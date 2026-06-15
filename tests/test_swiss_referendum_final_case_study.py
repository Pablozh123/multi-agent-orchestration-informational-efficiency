from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.swiss_referendum_final_case_study import (
    build_history_accuracy_rows,
    build_live_accuracy_rows,
    build_poll_accuracy_rows,
    generate_swiss_referendum_final_case_study_outputs,
    read_official_result,
)


def test_read_official_result_validates_single_curated_row(tmp_path: Path) -> None:
    result_path = _official_result_path(tmp_path)

    result = read_official_result(result_path)

    assert result["referendum_id"] == "swiss_2026_06_14_10mio"
    assert result["outcome"] == "rejected"
    assert result["official_yes_share"] == 0.4521
    assert result["official_dashboard_url"].startswith("https://abstimmungen.admin.ch/")


def test_read_official_result_rejects_invalid_share_sum(tmp_path: Path) -> None:
    result_path = _official_result_path(tmp_path)
    frame = pd.read_csv(result_path)
    frame.loc[0, "official_no_share"] = 0.60
    frame.to_csv(result_path, index=False)

    with pytest.raises(ValueError, match="sum to 1"):
        read_official_result(result_path)


def test_accuracy_rows_keep_vote_share_and_binary_modes_separate(tmp_path: Path) -> None:
    official = read_official_result(_official_result_path(tmp_path))
    polls = pd.read_csv(_polls_path(tmp_path))
    comparisons = pd.read_csv(_comparisons_path(tmp_path))
    history = pd.read_csv(_history_path(tmp_path))

    poll_accuracy = build_poll_accuracy_rows(polls=polls, official=official)
    live_accuracy = build_live_accuracy_rows(
        comparisons=comparisons,
        official=official,
    )
    history_accuracy = build_history_accuracy_rows(
        history=history,
        polls=polls,
        official=official,
    )

    assert len(poll_accuracy) == 2
    assert int(poll_accuracy["final_poll_for_source"].sum()) == 1
    assert len(live_accuracy) == 2
    assert len(history_accuracy) == 2

    first = live_accuracy[live_accuracy["observation_id"] == "cmp_001"].iloc[0]
    latest = live_accuracy[live_accuracy["observation_id"] == "cmp_002"].iloc[0]
    assert bool(first["polymarket_beats_poll_raw_vote_share"]) is True
    assert bool(latest["polymarket_beats_poll_raw_vote_share"]) is False
    assert bool(latest["polymarket_beats_poll_raw_binary_proxy"]) is True
    assert latest["interpretation_scope"] == (
        "post_result_bounded_poll_proxy_not_true_mispricing_or_trade_signal"
    )


def test_generate_final_case_study_outputs_writes_bounded_artifacts(
    tmp_path: Path,
) -> None:
    output_paths = _output_paths(tmp_path)

    result = generate_swiss_referendum_final_case_study_outputs(
        official_result_path=_official_result_path(tmp_path),
        poll_input_path=_polls_path(tmp_path),
        comparison_path=_comparisons_path(tmp_path),
        latest_source_comparison_path=_latest_source_path(tmp_path),
        price_history_path=_history_path(tmp_path),
        **output_paths,
    )

    final_case = pd.read_csv(output_paths["final_case_study_path"]).iloc[0]
    metadata = json.loads(output_paths["metadata_path"].read_text(encoding="utf-8"))
    doc = output_paths["docs_path"].read_text(encoding="utf-8")

    assert result.live_observation_rows == 2
    assert result.history_observation_rows == 2
    assert result.live_vote_share_better_count == 1
    assert int(final_case["live_polymarket_beats_raw_vote_share_count"]) == 1
    assert int(final_case["live_polymarket_beats_raw_binary_proxy_count"]) == 2
    assert final_case["official_outcome"] == "rejected"
    assert metadata["method"]["official_result_mapped"] is True
    assert metadata["limitations"]["binary_poll_brier_is_proxy_only"] is True
    assert "Live vote-share comparison" in doc
    assert "Live binary outcome proxy" in doc
    assert "kein Effizienzbeweis" in doc
    assert chr(223) not in doc
    assert output_paths["figure_path"].exists()


def _official_result_path(root: Path) -> Path:
    path = root / "official.csv"
    pd.DataFrame(
        [
            {
                "referendum_id": "swiss_2026_06_14_10mio",
                "proposal_id": "6860",
                "vote_number": "686",
                "vote_date": "2026-06-14",
                "official_title": "Volksinitiative Keine 10-Millionen-Schweiz",
                "outcome": "rejected",
                "official_yes_share": 0.4521,
                "official_no_share": 0.5479,
                "no_share_derivation": "derived_as_1_minus_official_yes_share",
                "yes_cantonal_votes": 10.0,
                "no_cantonal_votes": 13.0,
                "turnout": 0.5886,
                "official_dashboard_url": "https://abstimmungen.admin.ch/details/2026-06-14?proposalId=6860",
                "result_reference_url": "https://swissvotes.ch/vote/686.00",
                "source_note": "fixture",
            }
        ]
    ).to_csv(path, index=False)
    return path


def _polls_path(root: Path) -> Path:
    path = root / "polls.csv"
    pd.DataFrame(
        [
            {
                "poll_id": "poll_001",
                "referendum_id": "swiss_2026_06_14_10mio",
                "source_name": "Example Poll",
                "source_type": "poll",
                "fieldwork_start": "2026-05-01",
                "fieldwork_end": "2026-05-02",
                "published_at_utc": "2026-05-03T00:00:00Z",
                "published_time_precision": "date",
                "yes_share": 0.50,
                "no_share": 0.45,
                "undecided_share": 0.05,
                "sample_size": 1000,
                "margin_error": 0.02,
                "source_url": "https://example.test/poll-001",
                "notes": "fixture",
            },
            {
                "poll_id": "poll_002",
                "referendum_id": "swiss_2026_06_14_10mio",
                "source_name": "Example Poll",
                "source_type": "poll",
                "fieldwork_start": "2026-06-01",
                "fieldwork_end": "2026-06-02",
                "published_at_utc": "2026-06-03T00:00:00Z",
                "published_time_precision": "date",
                "yes_share": 0.45,
                "no_share": 0.52,
                "undecided_share": 0.03,
                "sample_size": 1000,
                "margin_error": 0.02,
                "source_url": "https://example.test/poll-002",
                "notes": "fixture",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _comparisons_path(root: Path) -> Path:
    path = root / "comparisons.csv"
    pd.DataFrame(
        [
            {
                "comparison_id": "cmp_001",
                "collected_at_utc": "2026-05-04T00:00:00Z",
                "polymarket_yes_probability": 0.445,
                "polymarket_no_probability": 0.555,
                "poll_id": "poll_001",
                "poll_source": "Example Poll",
                "poll_published_at_utc": "2026-05-03T00:00:00Z",
                "poll_age_hours": 24.0,
                "poll_yes_share": 0.50,
                "poll_no_share": 0.45,
                "poll_undecided_share": 0.05,
                "poll_yes_decided_share": 0.50 / 0.95,
                "raw_yes_gap": -0.055,
                "decided_yes_gap": -0.0813,
                "divergence_label": "near_poll_yes_share",
                "poll_proxy_valuation_label": "near_poll_proxy",
                "valuation_scope": "fixture",
            },
            {
                "comparison_id": "cmp_002",
                "collected_at_utc": "2026-06-14T00:04:17Z",
                "polymarket_yes_probability": 0.215,
                "polymarket_no_probability": 0.785,
                "poll_id": "poll_002",
                "poll_source": "Example Poll",
                "poll_published_at_utc": "2026-06-03T00:00:00Z",
                "poll_age_hours": 260.0,
                "poll_yes_share": 0.45,
                "poll_no_share": 0.52,
                "poll_undecided_share": 0.03,
                "poll_yes_decided_share": 0.45 / 0.97,
                "raw_yes_gap": -0.235,
                "decided_yes_gap": -0.2489,
                "divergence_label": "polymarket_below_poll_yes_share",
                "poll_proxy_valuation_label": "below_poll_proxy",
                "valuation_scope": "fixture",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _history_path(root: Path) -> Path:
    path = root / "history.csv"
    pd.DataFrame(
        [
            {
                "observed_at_utc": "2026-05-04T00:00:00Z",
                "poll_id": "poll_001",
                "poll_published_at_utc": "2026-05-03T00:00:00Z",
                "yes_probability": 0.445,
                "source_name": "polymarket_clob_prices_history",
            },
            {
                "observed_at_utc": "2026-06-04T00:00:00Z",
                "poll_id": "poll_002",
                "poll_published_at_utc": "2026-06-03T00:00:00Z",
                "yes_probability": 0.285,
                "source_name": "polymarket_clob_prices_history",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _latest_source_path(root: Path) -> Path:
    path = root / "latest_source.csv"
    pd.DataFrame(
        [
            {
                "source_name": "Example Poll",
                "poll_id": "poll_002",
                "polymarket_snapshot_at_utc": "2026-06-14T00:04:17Z",
            }
        ]
    ).to_csv(path, index=False)
    return path


def _output_paths(root: Path) -> dict[str, Path]:
    return {
        "final_case_study_path": root / "final_case.csv",
        "poll_accuracy_path": root / "poll_accuracy.csv",
        "live_accuracy_path": root / "live_accuracy.csv",
        "history_accuracy_path": root / "history_accuracy.csv",
        "figure_path": root / "figure.png",
        "metadata_path": root / "metadata.json",
        "docs_path": root / "case_study.md",
    }
