from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd

from operations.analysis.h1_margin_threshold_readiness import (
    MARGIN_THRESHOLD_SPECS,
    build_readiness_frame,
    build_state_poll_pair_coverage,
    generate_h1_margin_threshold_readiness_outputs,
    mock_history_by_slug,
    mock_margin_threshold_markets,
    mock_poll_average_rows,
)


def test_build_state_poll_pair_coverage_counts_only_rep_dem_pairs() -> None:
    rows = mock_poll_average_rows() + [
        {
            "date": "2024-09-12",
            "state": "Florida",
            "cycle": 2024,
            "party": "IND",
            "pct_estimate": 2.0,
        },
        {
            "date": "2024-09-12",
            "state": "Florida",
            "cycle": 2020,
            "party": "REP",
            "pct_estimate": 49.0,
        },
    ]

    coverage = build_state_poll_pair_coverage(rows)
    florida = coverage[coverage["state"] == "Florida"].iloc[0]

    assert int(florida["poll_pair_count"]) == 2
    assert str(florida["poll_first_date"]) == "2024-09-11"
    assert str(florida["poll_last_date"]) == "2024-09-12"
    assert "Iowa" not in set(coverage["state"])


def test_build_readiness_frame_blocks_threshold_markets_without_overlap() -> None:
    markets = mock_margin_threshold_markets()
    poll_pairs = build_state_poll_pair_coverage(mock_poll_average_rows())
    history_by_slug = mock_history_by_slug()

    readiness = build_readiness_frame(
        markets=markets,
        poll_pairs=poll_pairs,
        history_by_slug=history_by_slug,
    )

    assert len(readiness) == len(MARGIN_THRESHOLD_SPECS)
    assert int(readiness["compatible_for_h1_brier_now"].sum()) == 0

    florida = readiness[
        readiness["market_slug"] == "will-trump-win-florida-by-8-points"
    ].iloc[0]
    iowa = readiness[
        readiness["market_slug"] == "will-trump-win-iowa-by-12-points"
    ].iloc[0]

    assert bool(florida["has_538_state_poll_rows"]) is True
    assert bool(florida["has_clob_history_during_538_poll_window"]) is False
    assert str(florida["status"]) == "blocked_by_no_temporal_overlap"
    assert int(florida["late_clob_points"]) == 1
    assert bool(iowa["has_538_state_poll_rows"]) is False
    assert str(iowa["status"]) == "blocked_by_missing_538_state_poll_rows"


def test_generate_h1_margin_threshold_readiness_outputs(tmp_path: Path) -> None:
    result = generate_h1_margin_threshold_readiness_outputs(
        source="mock",
        readiness_output=tmp_path / "margin_threshold_readiness.csv",
        figure_output=tmp_path / "margin_threshold_readiness.png",
        metadata_output=tmp_path / "margin_threshold_readiness.json",
    )

    readiness = pd.read_csv(tmp_path / "margin_threshold_readiness.csv")
    metadata = json.loads(
        (tmp_path / "margin_threshold_readiness.json").read_text(encoding="utf-8")
    )
    image = mpimg.imread(tmp_path / "margin_threshold_readiness.png")

    assert result.candidate_count == len(MARGIN_THRESHOLD_SPECS)
    assert result.candidates_with_538_state_polls == 4
    assert result.candidates_with_clob_poll_window_history == 0
    assert result.compatible_candidate_count == 0
    assert len(readiness) == len(MARGIN_THRESHOLD_SPECS)
    assert metadata["outputs"]["brier_rows_added"] == 0
    assert metadata["outputs"]["compatible_candidate_count"] == 0
    assert metadata["limitations"]["no_new_brier_evidence_without_temporal_overlap"]
    assert image.size > 0
    assert float(image.std()) > 0.0

