from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_evidence_scope import (
    build_scope_rows,
    generate_h1_evidence_scope_outputs,
)


def _write_inputs(base: Path) -> dict[str, Path]:
    paths = {
        "brier": base / "h1_brier_scores.csv",
        "pairwise": base / "h1_forecast_quality_pairwise.csv",
        "polls": base / "swiss_polls.csv",
        "events": base / "events.csv",
    }
    pd.DataFrame(
        [
            {"date": "2024-01-01", "bs_polymarket": 0.1},
            {"date": "2024-01-02", "bs_polymarket": 0.2},
        ]
    ).to_csv(paths["brier"], index=False)
    pd.DataFrame(
        [
            {
                "comparator": "fivethirtyeight",
                "polymarket_lower_loss_count": 2,
                "comparison_row_count": 2,
            }
        ]
    ).to_csv(paths["pairwise"], index=False)
    pd.DataFrame(
        [
            {"poll_id": "poll_a", "yes_share": 0.45},
            {"poll_id": "poll_b", "yes_share": 0.40},
        ]
    ).to_csv(paths["polls"], index=False)
    pd.DataFrame(
        [
            {"event_id": "evt_a"},
            {"event_id": "evt_b"},
            {"event_id": "evt_c"},
        ]
    ).to_csv(paths["events"], index=False)
    return paths


def test_build_scope_rows_separates_daily_rows_from_independent_outcomes(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)
    scope = build_scope_rows(
        brier=pd.read_csv(paths["brier"]),
        pairwise=pd.read_csv(paths["pairwise"]),
        swiss_polls=pd.read_csv(paths["polls"]),
        events=pd.read_csv(paths["events"]),
    )

    us_row = scope[scope["case_id"] == "us_2024_presidential_h1"].iloc[0]
    swiss_row = scope[scope["case_id"] == "swiss_2026_10mio_referendum"].iloc[0]
    h2_row = scope[scope["case_id"] == "h2_curated_us_events"].iloc[0]

    assert bool(us_row["current_h1_eligible"]) is True
    assert int(us_row["independent_resolved_outcome_count"]) == 1
    assert int(us_row["local_row_count"]) == 2
    assert int(us_row["polymarket_better_count"]) == 2

    assert bool(swiss_row["current_h1_eligible"]) is False
    assert bool(swiss_row["brier_computable_now"]) is False
    assert int(swiss_row["local_row_count"]) == 2

    assert bool(h2_row["current_h1_eligible"]) is False
    assert int(h2_row["local_row_count"]) == 3


def test_generate_h1_evidence_scope_outputs(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)
    result = generate_h1_evidence_scope_outputs(
        brier_input=paths["brier"],
        pairwise_input=paths["pairwise"],
        swiss_poll_input=paths["polls"],
        event_input=paths["events"],
        scope_output=tmp_path / "scope.csv",
        figure_output=tmp_path / "scope.png",
        metadata_output=tmp_path / "scope.json",
    )

    assert result.scope_row_count == 3
    assert result.eligible_independent_outcome_count == 1
    assert result.eligible_daily_row_count == 2
    assert result.polymarket_better_vs_fivethirtyeight_count == 2
    assert result.fivethirtyeight_comparison_count == 2

    metadata = json.loads((tmp_path / "scope.json").read_text(encoding="utf-8"))
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["limitations"]["current_brier_evidence_has_one_independent_resolved_outcome"]
    assert metadata["limitations"]["h2_events_are_not_independent_h1_outcomes"]

    image = mpimg.imread(tmp_path / "scope.png")
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_build_scope_rows_requires_fivethirtyeight_pairwise_row() -> None:
    with pytest.raises(ValueError, match="FiveThirtyEight"):
        build_scope_rows(
            brier=pd.DataFrame(),
            pairwise=pd.DataFrame(
                [
                    {
                        "comparator": "always_50",
                        "polymarket_lower_loss_count": 1,
                        "comparison_row_count": 1,
                    }
                ]
            ),
            swiss_polls=pd.DataFrame(),
            events=pd.DataFrame(),
        )
