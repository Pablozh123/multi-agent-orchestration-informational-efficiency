from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_scope_frontier import prepare_scope_cases
from operations.analysis.h1_robust_poll_scope_quality import (
    build_calibration_bins,
    build_forecast_rows,
    build_pairwise_summary,
    build_quality_summary,
    generate_h1_robust_poll_scope_quality_outputs,
    validate_bins,
    validate_forecast_rows,
    validate_pairwise,
    validate_summary,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import CASE_INPUT
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_robust_poll_scope_quality_quantifies_bounded_forecast_support() -> None:
    cases = prepare_scope_cases(read_panel_cases(CASE_INPUT))

    forecast_rows = validate_forecast_rows(build_forecast_rows(cases))
    bins = validate_bins(build_calibration_bins(forecast_rows))
    summary = validate_summary(build_quality_summary(forecast_rows, bins))
    pairwise = validate_pairwise(build_pairwise_summary(cases, summary))

    largest = _scope(pairwise, "largest_robust_lte120_low_middle")
    strongest = _scope(pairwise, "strongest_robust_lte90_low_middle")
    largest_pm = _summary(summary, "largest_robust_lte120_low_middle", "polymarket")
    largest_poll = _summary(summary, "largest_robust_lte120_low_middle", "poll_derived")
    strongest_pm = _summary(summary, "strongest_robust_lte90_low_middle", "polymarket")

    assert len(pairwise) == 2
    assert len(forecast_rows) == 1436
    assert bins["row_count"].sum() == len(forecast_rows)

    assert largest["case_count"] == 433
    assert largest["polymarket_lower_loss_count"] == 313
    assert largest["poll_derived_lower_loss_count"] == 120
    assert largest["state_month_polymarket_support_count"] == 18
    assert largest["state_month_unit_count"] == 26
    assert largest["polymarket_lower_loss_share"] == pytest.approx(313 / 433)
    assert largest["mean_polymarket_brier"] == pytest.approx(0.19824693995381062)
    assert largest["mean_poll_derived_brier"] == pytest.approx(0.25545961757137536)
    assert largest["mean_loss_advantage"] > 0.0
    assert largest["ece_advantage"] > 0.0
    assert largest["probability_separation_advantage"] > 0.0

    assert largest_pm["expected_calibration_error"] < largest_poll[
        "expected_calibration_error"
    ]
    assert largest_pm["probability_separation"] > largest_poll[
        "probability_separation"
    ]

    assert strongest["case_count"] == 285
    assert strongest["polymarket_lower_loss_count"] == 262
    assert strongest["poll_derived_lower_loss_count"] == 23
    assert strongest["state_month_polymarket_support_count"] == 17
    assert strongest["state_month_poll_support_count"] == 0
    assert strongest["polymarket_lower_loss_share"] == pytest.approx(262 / 285)
    assert strongest["mean_loss_advantage"] > largest["mean_loss_advantage"]
    assert strongest_pm["positive_rate"] == 1.0
    assert pd.isna(strongest["polymarket_probability_separation"])
    assert bool(strongest["bounded_poll_claim_supported"]) is True
    assert bool(strongest["broad_claim_supported"]) is False


def test_generate_robust_poll_scope_quality_outputs(tmp_path: Path) -> None:
    result = generate_h1_robust_poll_scope_quality_outputs(
        case_input=CASE_INPUT,
        forecast_rows_output=tmp_path / "rows.csv",
        bin_output=tmp_path / "bins.csv",
        summary_output=tmp_path / "summary.csv",
        pairwise_output=tmp_path / "pairwise.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    rows = pd.read_csv(tmp_path / "rows.csv")
    bins = pd.read_csv(tmp_path / "bins.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    pairwise = pd.read_csv(tmp_path / "pairwise.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.scope_count == 2
    assert result.largest_case_count == 433
    assert result.largest_polymarket_lower_loss_count == 313
    assert result.strongest_case_count == 285
    assert result.strongest_polymarket_lower_loss_count == 262
    assert result.broad_claim_proven is False

    assert len(rows) == 1436
    assert len(bins) == 20
    assert len(summary) == 4
    assert len(pairwise) == 2
    assert metadata["outputs"]["forecast_row_count"] == 1436
    assert metadata["outputs"]["case_row_count"] == 718
    assert metadata["outputs"]["bounded_poll_claim_supported"] is True
    assert metadata["outputs"]["broad_claim_proven"] is False
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["outputs"]["strongest_scope_all_positive_outcomes"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["bounded_scope_quality_not_broad_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_robust_poll_scope_quality_rejects_forbidden_raw_trade_columns() -> None:
    cases = prepare_scope_cases(read_panel_cases(CASE_INPUT))
    forecast_rows = build_forecast_rows(cases)
    forecast_rows["maker_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        validate_forecast_rows(forecast_rows)


def _scope(pairwise: pd.DataFrame, scope_id: str) -> dict[str, object]:
    rows = pairwise.loc[pairwise["scope_id"] == scope_id]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()


def _summary(
    summary: pd.DataFrame,
    scope_id: str,
    source_id: str,
) -> dict[str, object]:
    rows = summary.loc[
        (summary["scope_id"] == scope_id) & (summary["source_id"] == source_id)
    ]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()
