from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_scope_frontier import (
    build_frontier_table,
    build_summary_table,
    generate_h1_poll_scope_frontier_outputs,
    prepare_scope_cases,
    validate_frontier_table,
    validate_summary_table,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import CASE_INPUT
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_scope_frontier_identifies_largest_and_strongest_supported_scopes() -> None:
    cases = prepare_scope_cases(read_panel_cases(CASE_INPUT))

    frontier = validate_frontier_table(build_frontier_table(cases))
    summary = validate_summary_table(build_summary_table(frontier))

    largest = _scope(frontier, "lte_120_days_low_middle_distance")
    strongest = _scope(frontier, "lte_90_days_low_middle_distance")
    full_panel = _scope(frontier, "full_panel_all_distances")

    assert len(frontier) == 30
    assert largest["frontier_status"] == "robust_support"
    assert largest["row_count"] == 433
    assert largest["polymarket_lower_loss_count"] == 313
    assert largest["poll_derived_lower_loss_count"] == 120
    assert largest["state_count"] == 11
    assert largest["state_month_polymarket_support_count"] == 18
    assert largest["state_month_unit_count"] == 26
    assert largest["state_month_exact_p_value"] == pytest.approx(0.03775934875011444)
    assert strongest["state_month_exact_p_value"] == pytest.approx(7.62939453125e-06)
    assert full_panel["frontier_status"] == "contradicted_or_unsupported"
    assert full_panel["polymarket_lower_loss_count"] == 360
    assert full_panel["poll_derived_lower_loss_count"] == 1360
    assert _summary_value(summary, "largest_robust_scope_id") == (
        "lte_120_days_low_middle_distance"
    )
    assert float(_summary_value(summary, "largest_robust_polymarket_support_share")) == pytest.approx(
        313 / 433
    )
    assert _summary_value(summary, "strongest_robust_scope_id") == (
        "lte_90_days_low_middle_distance"
    )
    assert int(float(_summary_value(summary, "broad_claim_proven"))) == 0


def test_generate_scope_frontier_outputs_writes_nonblank_figure(tmp_path: Path) -> None:
    result = generate_h1_poll_scope_frontier_outputs(
        case_input=CASE_INPUT,
        frontier_output=tmp_path / "frontier.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "frontier.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "frontier.png")

    assert result.frontier_row_count == 30
    assert result.robust_scope_count == 8
    assert result.largest_robust_scope_id == "lte_120_days_low_middle_distance"
    assert result.largest_robust_row_count == 433
    assert result.broad_claim_proven is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["full_panel_still_contradicts_broad_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_scope_frontier_rejects_forbidden_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "state": "A",
                "forecast_date": "2024-09-01",
                "poll_derived_probability": 0.52,
                "polymarket_brier": 0.1,
                "poll_derived_brier": 0.2,
                "loss_advantage": 0.1,
                "lower_loss_source": "polymarket",
                "wallet_address": "0xabc",
            }
        ]
    )

    with pytest.raises(ValueError, match="forbidden columns"):
        prepare_scope_cases(frame)


def _scope(frontier: pd.DataFrame, scope_id: str) -> dict[str, object]:
    rows = frontier.loc[frontier["scope_id"] == scope_id]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()


def _summary_value(summary: pd.DataFrame, summary_id: str):
    rows = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(rows) == 1
    return rows.iloc[0]
