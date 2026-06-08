from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.collectors.swiss_referendum_refresh import (
    build_running_status,
    main,
    refresh_swiss_referendum_comparison,
)


def test_refresh_swiss_referendum_comparison_writes_all_outputs(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    result = refresh_swiss_referendum_comparison(
        source="mock",
        collected_at_utc="2026-06-08T12:00:00Z",
        **paths,
    )

    snapshots = pd.read_csv(paths["snapshots_path"])
    comparison = pd.read_csv(paths["comparison_path"])
    metadata = json.loads(paths["refresh_metadata_path"].read_text(encoding="utf-8"))
    assert result.snapshot_row_count == 1
    assert result.history_row_count == 8
    assert result.comparison_row_count == 1
    assert result.poll_impact_row_count == 2
    assert result.latest_yes_probability == 0.225
    assert result.latest_divergence_label == "polymarket_below_poll_yes_share"
    assert len(snapshots) == 1
    assert len(comparison) == 1
    assert paths["history_path"].exists()
    assert paths["latest_source_comparison_path"].exists()
    assert paths["dashboard_path"].exists()
    assert paths["figure_path"].exists()
    assert paths["reaction_figure_path"].exists()
    assert paths["poll_reaction_windows_path"].exists()
    assert paths["information_response_path"].exists()
    assert paths["information_response_figure_path"].exists()
    assert paths["source_audit_path"].exists()
    assert paths["summary_path"].exists()
    assert paths["running_status_path"].exists()
    assert result.summary_path == paths["summary_path"]
    assert result.running_status_path == paths["running_status_path"]
    assert result.source_audit_path == paths["source_audit_path"]
    assert result.latest_source_comparison_path == paths["latest_source_comparison_path"]
    assert result.information_response_path == paths["information_response_path"]
    assert result.information_response_figure_path == paths[
        "information_response_figure_path"
    ]
    assert metadata["method"]["bounded_single_snapshot_refresh"] is True
    assert metadata["method"]["collects_bounded_price_history"] is True
    assert metadata["method"]["does_not_use_order_endpoints"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["running_status"]["status"]["all_outputs_exist"] is True


def test_refresh_append_keeps_multiple_snapshot_times(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    refresh_swiss_referendum_comparison(
        source="mock",
        collected_at_utc="2026-06-08T12:00:00Z",
        **paths,
    )
    result = refresh_swiss_referendum_comparison(
        source="mock",
        collected_at_utc="2026-06-08T12:05:00Z",
        **paths,
    )

    snapshots = pd.read_csv(paths["snapshots_path"])
    assert result.snapshot_row_count == 2
    assert result.history_row_count == 8
    assert result.comparison_row_count == 2
    assert len(snapshots) == 2


def test_build_running_status_reports_snapshot_recency(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    refresh_swiss_referendum_comparison(
        source="mock",
        collected_at_utc="2026-06-08T12:00:00Z",
        fresh_snapshot_minutes=120,
        **paths,
    )

    status = build_running_status(
        snapshots_path=paths["snapshots_path"],
        history_path=paths["history_path"],
        comparison_path=paths["comparison_path"],
        latest_source_comparison_path=paths["latest_source_comparison_path"],
        poll_impact_path=paths["poll_impact_path"],
        poll_reaction_windows_path=paths["poll_reaction_windows_path"],
        information_response_path=paths["information_response_path"],
        source_audit_path=paths["source_audit_path"],
        figure_path=paths["figure_path"],
        reaction_figure_path=paths["reaction_figure_path"],
        information_response_figure_path=paths["information_response_figure_path"],
        dashboard_path=paths["dashboard_path"],
        summary_path=paths["summary_path"],
        efficiency_metadata_path=paths["efficiency_metadata_path"],
        fresh_snapshot_minutes=120,
        generated_at_utc=pd.Timestamp("2026-06-08T13:00:00Z").to_pydatetime(),
    )

    assert status["status"]["latest_snapshot_at_utc"] == "2026-06-08T12:00:00Z"
    assert status["status"]["snapshot_age_minutes"] == 60.0
    assert status["status"]["snapshot_recency_status"] == "fresh"
    assert status["status"]["ready_for_running_view"] is True
    assert status["method"]["does_not_use_order_endpoints"] is True


def test_refresh_cli_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--collected-at-utc",
            "2026-06-08T12:00:00Z",
            "--poll-input",
            str(paths["poll_input_path"]),
            "--snapshots-output",
            str(paths["snapshots_path"]),
            "--snapshot-metadata-output",
            str(paths["snapshot_metadata_path"]),
            "--history-output",
            str(paths["history_path"]),
            "--history-metadata-output",
            str(paths["history_metadata_path"]),
            "--comparison-output",
            str(paths["comparison_path"]),
            "--latest-source-comparison-output",
            str(paths["latest_source_comparison_path"]),
            "--poll-impact-output",
            str(paths["poll_impact_path"]),
            "--poll-reaction-windows-output",
            str(paths["poll_reaction_windows_path"]),
            "--information-response-output",
            str(paths["information_response_path"]),
            "--source-audit-output",
            str(paths["source_audit_path"]),
            "--figure-output",
            str(paths["figure_path"]),
            "--reaction-figure-output",
            str(paths["reaction_figure_path"]),
            "--information-response-figure-output",
            str(paths["information_response_figure_path"]),
            "--dashboard-output",
            str(paths["dashboard_path"]),
            "--summary-output",
            str(paths["summary_path"]),
            "--efficiency-metadata-output",
            str(paths["efficiency_metadata_path"]),
            "--refresh-metadata-output",
            str(paths["refresh_metadata_path"]),
            "--running-status-output",
            str(paths["running_status_path"]),
            "--fresh-snapshot-minutes",
            "1000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "latest_divergence_label" in captured.out
    assert paths["refresh_metadata_path"].exists()
    assert paths["running_status_path"].exists()


def _paths(root: Path) -> dict[str, Path]:
    poll_input_path = root / "polls.csv"
    pd.DataFrame(
        [
            {
                "poll_id": "poll_001",
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
            {
                "poll_id": "poll_002",
                "referendum_id": "swiss_2026_06_14_10mio",
                "source_name": "Independent poll fixture",
                "source_type": "poll",
                "fieldwork_start": "2026-06-01",
                "fieldwork_end": "2026-06-01",
                "published_at_utc": "2026-06-07T00:00:00Z",
                "published_time_precision": "date",
                "yes_share": 0.44,
                "no_share": 0.53,
                "undecided_share": 0.03,
                "sample_size": 1000,
                "margin_error": 0.03,
                "source_url": "https://example.invalid/poll",
                "notes": "fixture",
            },
        ]
    ).to_csv(poll_input_path, index=False)
    return {
        "poll_input_path": poll_input_path,
        "snapshots_path": root / "snapshots.csv",
        "snapshot_metadata_path": root / "snapshot_metadata.json",
        "history_path": root / "history.csv",
        "history_metadata_path": root / "history_metadata.json",
        "comparison_path": root / "comparison.csv",
        "latest_source_comparison_path": root / "latest_source_comparison.csv",
        "poll_impact_path": root / "impacts.csv",
        "poll_reaction_windows_path": root / "reaction_windows.csv",
        "information_response_path": root / "information_response.csv",
        "source_audit_path": root / "source_audit.csv",
        "figure_path": root / "figure.png",
        "reaction_figure_path": root / "reaction_figure.png",
        "information_response_figure_path": root / "information_response_figure.png",
        "dashboard_path": root / "dashboard.html",
        "summary_path": root / "latest_summary.md",
        "efficiency_metadata_path": root / "efficiency_metadata.json",
        "refresh_metadata_path": root / "refresh_metadata.json",
        "running_status_path": root / "running_status.json",
    }
