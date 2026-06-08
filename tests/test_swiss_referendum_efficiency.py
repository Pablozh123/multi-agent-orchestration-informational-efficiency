from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.swiss_referendum_efficiency import (
    POLL_INPUT,
    build_comparison_rows,
    build_latest_source_comparison_rows,
    build_poll_impact_rows,
    build_poll_reaction_window_rows,
    build_source_audit_rows,
    generate_swiss_referendum_efficiency_outputs,
    main,
    read_poll_catalog,
    verify_dashboard_artifact,
)


def test_read_poll_catalog_validates_curated_poll_rows(tmp_path: Path) -> None:
    poll_path = _poll_path(tmp_path)

    polls = read_poll_catalog(poll_path)

    assert len(polls) == 2
    assert polls.iloc[0]["poll_id"] == "poll_001"
    assert float(polls.iloc[1]["yes_share"]) == 0.45


def test_project_poll_catalog_includes_current_yougov_rows() -> None:
    polls = read_poll_catalog(POLL_INPUT)
    audit = build_source_audit_rows(polls)

    assert len(polls) == 7
    assert "yougov_2026_w2_final" in set(polls["poll_id"])
    yougov = polls[polls["poll_id"] == "yougov_2026_w2_final"].iloc[0]
    assert yougov["source_name"] == "YouGov Schweiz"
    assert float(yougov["yes_share"]) == 0.38
    assert float(yougov["no_share"]) == 0.55
    assert float(yougov["undecided_share"]) == 0.07
    assert set(audit[audit["source_name"] == "YouGov Schweiz"]["source_role"]) == {
        "voting_intention_poll"
    }
    bfs = audit[audit["source_id"] == "bfs_population_scenarios_2025_2055"].iloc[0]
    assert bool(bfs["included_in_poll_catalog"]) is False


def test_read_poll_catalog_rejects_invalid_share_sum(tmp_path: Path) -> None:
    poll_path = _poll_path(tmp_path)
    polls = pd.read_csv(poll_path)
    polls.loc[0, "undecided_share"] = 0.30
    polls.to_csv(poll_path, index=False)

    with pytest.raises(ValueError, match="sum to approximately 1"):
        read_poll_catalog(poll_path)


def test_build_comparison_rows_matches_latest_prior_poll(tmp_path: Path) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path))
    snapshots = pd.read_csv(_snapshots_path(tmp_path))

    comparisons = build_comparison_rows(snapshots=snapshots, polls=polls)

    latest = comparisons.iloc[-1]
    assert len(comparisons) == 3
    assert latest["poll_id"] == "poll_002"
    assert latest["comparison_status"] == "matched_latest_prior_poll"
    assert latest["divergence_label"] == "polymarket_below_poll_yes_share"
    assert latest["poll_proxy_valuation_label"] == "below_poll_proxy"
    assert latest["valuation_scope"] == (
        "descriptive_poll_proxy_not_true_mispricing_or_trade_signal"
    )
    assert round(float(latest["raw_yes_gap"]), 3) == -0.200
    assert round(float(latest["poll_yes_decided_share"]), 3) == 0.464


def test_build_latest_source_comparison_rows_compares_each_poll_source(
    tmp_path: Path,
) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path))
    snapshots = pd.read_csv(_snapshots_path(tmp_path))

    rows = build_latest_source_comparison_rows(snapshots=snapshots, polls=polls)

    assert len(rows) == 1
    row = rows.iloc[0]
    assert row["source_name"] == "SRG/gfs.bern"
    assert row["poll_id"] == "poll_002"
    assert round(float(row["raw_yes_gap"]), 3) == -0.200
    assert row["poll_proxy_valuation_label"] == "below_poll_proxy"
    assert row["valuation_scope"] == (
        "descriptive_latest_source_poll_proxy_not_true_mispricing_or_trade_signal"
    )


def test_build_poll_impact_rows_reports_pre_post_changes(tmp_path: Path) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path))
    snapshots = pd.read_csv(_snapshots_path(tmp_path))

    impacts = build_poll_impact_rows(snapshots=snapshots, polls=polls)

    assert len(impacts) == 2
    assert list(impacts["impact_status"]) == ["observed_pre_post", "observed_pre_post"]
    assert round(float(impacts.iloc[1]["yes_probability_change"]), 3) == -0.240
    assert "yes_probability_change_24h" in impacts.columns


def test_build_poll_impact_rows_reports_reaction_windows(tmp_path: Path) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path)).tail(1)
    snapshots = pd.DataFrame(
        [
            {
                "observed_at_utc": "2026-06-03T03:00:00Z",
                "yes_probability": 0.50,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-03T04:00:00Z",
                "yes_probability": 0.49,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-03T09:00:00Z",
                "yes_probability": 0.47,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-04T03:55:00Z",
                "yes_probability": 0.44,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-05T03:55:00Z",
                "yes_probability": 0.43,
                "source_url": "https://polymarket.com/de/event/example",
            },
        ]
    )

    impacts = build_poll_impact_rows(snapshots=snapshots, polls=polls)

    row = impacts.iloc[0]
    assert round(float(row["yes_probability_change_1h"]), 3) == -0.010
    assert round(float(row["yes_probability_change_6h"]), 3) == -0.030
    assert round(float(row["yes_probability_change_24h"]), 3) == -0.060
    assert round(float(row["yes_probability_change_48h"]), 3) == -0.070


def test_build_poll_reaction_window_rows_returns_tidy_windows(tmp_path: Path) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path)).tail(1)
    snapshots = pd.DataFrame(
        [
            {
                "observed_at_utc": "2026-06-03T03:00:00Z",
                "yes_probability": 0.50,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-03T04:00:00Z",
                "yes_probability": 0.49,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "observed_at_utc": "2026-06-03T09:00:00Z",
                "yes_probability": 0.47,
                "source_url": "https://polymarket.com/de/event/example",
            },
        ]
    )
    impacts = build_poll_impact_rows(snapshots=snapshots, polls=polls)

    windows = build_poll_reaction_window_rows(impacts)

    assert len(windows) == 4
    assert list(windows["window_hours"]) == [1, 6, 24, 48]
    assert set(windows["interpretation_scope"]) == {
        "descriptive_pre_post_window_no_causality_or_trade_signal"
    }
    one_hour = windows[windows["window_hours"] == 1].iloc[0]
    assert one_hour["reaction_status"] == "observed_window_change"
    assert round(float(one_hour["yes_probability_change"]), 3) == -0.010


def test_build_source_audit_rows_marks_bfs_as_context_only(tmp_path: Path) -> None:
    polls = read_poll_catalog(_poll_path(tmp_path))

    audit = build_source_audit_rows(polls)

    bfs = audit[audit["source_id"] == "bfs_population_scenarios_2025_2055"].iloc[0]
    poll_sources = audit[audit["source_role"] == "voting_intention_poll"]
    assert len(audit) == 4
    assert bool(bfs["has_voting_intention_values"]) is False
    assert bool(bfs["included_in_poll_catalog"]) is False
    assert set(poll_sources["included_in_poll_catalog"]) == {True}


def test_generate_outputs_writes_dashboard_metadata_and_figure(tmp_path: Path) -> None:
    paths = _output_paths(tmp_path)

    result = generate_swiss_referendum_efficiency_outputs(
        poll_input_path=_poll_path(tmp_path),
        polymarket_snapshots_path=_snapshots_path(tmp_path),
        polymarket_history_path=None,
        **paths,
    )

    dashboard = paths["dashboard_path"].read_text(encoding="utf-8")
    summary = paths["summary_path"].read_text(encoding="utf-8")
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    comparison = pd.read_csv(paths["comparison_path"])
    latest_source = pd.read_csv(paths["latest_source_comparison_path"])
    impacts = pd.read_csv(paths["poll_impact_path"])
    reaction_windows = pd.read_csv(paths["poll_reaction_windows_path"])
    source_audit = pd.read_csv(paths["source_audit_path"])
    assert result.comparison_row_count == 3
    assert result.poll_impact_row_count == 2
    assert result.source_audit_path == paths["source_audit_path"]
    assert result.latest_divergence_label == "polymarket_below_poll_yes_share"
    assert "Swiss 10-Million Referendum Efficiency View" in dashboard
    assert "BFS/admin.ch is used as official referendum" in dashboard
    assert "Source Boundary Audit" in dashboard
    assert "Poll proxy relation" in dashboard
    assert "Latest local snapshot" in dashboard
    assert "Latest matched poll" in dashboard
    assert "manual bounded refresh" in dashboard
    assert "Latest Poll-Source Comparison" in dashboard
    assert "cross-source poll-proxy view" in dashboard
    assert "Poll Release Timing Summary" in dashboard
    assert "first post observation after" in dashboard
    assert "below_poll_proxy" in dashboard
    assert "Swiss 10-Million Referendum Latest Summary" in summary
    assert "## Latest Poll-Source Comparison" in summary
    assert "## Poll Release Timing Summary" in summary
    assert "descriptive no-causality scope" in summary
    assert "Poll reaction-window rows" in summary
    assert "Poll reaction windows" in summary
    assert "## Key Numerical Result" in summary
    assert "## Bounded Interpretation" in summary
    assert "## Main Limitation" in summary
    assert "below_poll_proxy" in summary
    assert "![Swiss referendum comparison figure](figure.png)" in summary
    assert "![Swiss referendum reaction-window figure](reaction_figure.png)" in summary
    assert paths["figure_path"].exists()
    assert paths["reaction_figure_path"].exists()
    assert len(comparison) == 3
    assert len(latest_source) == 1
    assert len(impacts) == 2
    assert len(reaction_windows) == 8
    assert len(source_audit) == 4
    assert metadata["method"]["poll_probability_transform"] == "none"
    assert metadata["limitations"]["bfs_is_context_not_poll_source"] is True
    assert metadata["limitations"]["source_audit_confirms_bfs_context_only"] is True
    assert metadata["outputs"]["poll_reaction_window_row_count"] == 8
    assert metadata["outputs"]["latest_source_comparison_row_count"] == 1
    assert metadata["outputs"]["source_audit_row_count"] == 4
    assert metadata["outputs"]["latest_poll_proxy_valuation_label"] == "below_poll_proxy"
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["dashboard_verification"]["figure_nonblank"] is True
    assert metadata["dashboard_verification"]["checked_figure_count"] == 2
    assert metadata["dashboard_verification"]["table_count"] >= 4


def test_verify_dashboard_artifact_checks_html_and_figure(tmp_path: Path) -> None:
    paths = _output_paths(tmp_path)
    generate_swiss_referendum_efficiency_outputs(
        poll_input_path=_poll_path(tmp_path),
        polymarket_snapshots_path=_snapshots_path(tmp_path),
        polymarket_history_path=None,
        **paths,
    )

    verification = verify_dashboard_artifact(
        dashboard_path=paths["dashboard_path"],
        figure_path=paths["figure_path"],
        extra_figure_paths=(paths["reaction_figure_path"],),
        required_text=("below_poll_proxy", "Source Boundary Audit"),
    )

    assert verification.title == "Swiss 10-Million Referendum Efficiency View"
    assert verification.h1 == "Swiss 10-Million Referendum Efficiency View"
    assert verification.table_count >= 4
    assert verification.image_count == 2
    assert verification.checked_figure_count == 2
    assert verification.figure_nonblank is True
    assert verification.required_text_present is True


def test_verify_dashboard_artifact_rejects_missing_required_text(tmp_path: Path) -> None:
    paths = _output_paths(tmp_path)
    generate_swiss_referendum_efficiency_outputs(
        poll_input_path=_poll_path(tmp_path),
        polymarket_snapshots_path=_snapshots_path(tmp_path),
        polymarket_history_path=None,
        **paths,
    )

    with pytest.raises(ValueError, match="missing required text"):
        verify_dashboard_artifact(
            dashboard_path=paths["dashboard_path"],
            figure_path=paths["figure_path"],
            required_text=("not-present-in-dashboard",),
        )


def test_cli_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _output_paths(tmp_path)

    exit_code = main(
        [
            "--poll-input",
            str(_poll_path(tmp_path)),
            "--polymarket-snapshots",
            str(_snapshots_path(tmp_path)),
            "--polymarket-history",
            str(tmp_path / "missing_history.csv"),
            "--comparison-output",
            str(paths["comparison_path"]),
            "--latest-source-comparison-output",
            str(paths["latest_source_comparison_path"]),
            "--poll-impact-output",
            str(paths["poll_impact_path"]),
            "--poll-reaction-windows-output",
            str(paths["poll_reaction_windows_path"]),
            "--source-audit-output",
            str(paths["source_audit_path"]),
            "--figure-output",
            str(paths["figure_path"]),
            "--reaction-figure-output",
            str(paths["reaction_figure_path"]),
            "--dashboard-output",
            str(paths["dashboard_path"]),
            "--summary-output",
            str(paths["summary_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "latest_divergence_label" in captured.out
    assert paths["dashboard_path"].exists()


def _poll_path(root: Path) -> Path:
    path = root / "polls.csv"
    pd.DataFrame(
        [
            {
                "poll_id": "poll_001",
                "referendum_id": "swiss_2026_06_14_10mio",
                "source_name": "SRG/gfs.bern",
                "source_type": "poll",
                "fieldwork_start": "2026-04-20",
                "fieldwork_end": "2026-05-03",
                "published_at_utc": "2026-05-08T03:56:00Z",
                "published_time_precision": "minute",
                "yes_share": 0.47,
                "no_share": 0.47,
                "undecided_share": 0.06,
                "sample_size": 19728,
                "margin_error": 0.028,
                "source_url": "https://www.srf.ch/news/schweiz/1-srg-umfrage-pattsituation-bei-keine-10-mio-schweiz-initiative",
                "notes": "fixture",
            },
            {
                "poll_id": "poll_002",
                "referendum_id": "swiss_2026_06_14_10mio",
                "source_name": "SRG/gfs.bern",
                "source_type": "poll",
                "fieldwork_start": "2026-05-19",
                "fieldwork_end": "2026-05-27",
                "published_at_utc": "2026-06-03T03:55:00Z",
                "published_time_precision": "minute",
                "yes_share": 0.45,
                "no_share": 0.52,
                "undecided_share": 0.03,
                "sample_size": 19400,
                "margin_error": 0.028,
                "source_url": "https://www.srf.ch/news/schweiz/2-srg-umfrage-keine-10-mio-schweiz-kippt-ins-nein-52-prozent-dagegen",
                "notes": "fixture",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _snapshots_path(root: Path) -> Path:
    path = root / "snapshots.csv"
    pd.DataFrame(
        [
            {
                "collected_at_utc": "2026-05-07T12:00:00Z",
                "yes_probability": 0.50,
                "no_probability": 0.50,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "collected_at_utc": "2026-05-09T12:00:00Z",
                "yes_probability": 0.49,
                "no_probability": 0.51,
                "source_url": "https://polymarket.com/de/event/example",
            },
            {
                "collected_at_utc": "2026-06-04T12:00:00Z",
                "yes_probability": 0.25,
                "no_probability": 0.75,
                "source_url": "https://polymarket.com/de/event/example",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _output_paths(root: Path) -> dict[str, Path]:
    return {
        "comparison_path": root / "comparison.csv",
        "latest_source_comparison_path": root / "latest_source_comparison.csv",
        "poll_impact_path": root / "impacts.csv",
        "poll_reaction_windows_path": root / "reaction_windows.csv",
        "source_audit_path": root / "source_audit.csv",
        "figure_path": root / "figure.png",
        "reaction_figure_path": root / "reaction_figure.png",
        "dashboard_path": root / "dashboard.html",
        "summary_path": root / "latest_summary.md",
        "metadata_path": root / "metadata.json",
    }
