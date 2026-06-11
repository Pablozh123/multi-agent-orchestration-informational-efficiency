from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_calibration_diagnostic import (
    build_calibration_bins,
    build_calibration_summary,
    build_forecast_cases,
    build_pairwise_summary,
    generate_h1_calibration_diagnostic_outputs,
    validate_forecast_cases,
)


def test_build_h1_calibration_diagnostic_keeps_scope_limited() -> None:
    forecast_cases = validate_forecast_cases(
        build_forecast_cases(
            rieke_cases=_rieke_cases(),
            two_seventy_cases=_two_seventy_cases(),
            state_poll_cases=_state_poll_cases(),
            final_snapshot_cases=_final_snapshot_cases(),
        )
    )
    bins = build_calibration_bins(forecast_cases, bin_count=5)
    summary = build_calibration_summary(forecast_cases, bins)
    pairwise = build_pairwise_summary(
        rieke_cases=_rieke_cases(),
        two_seventy_cases=_two_seventy_cases(),
        state_poll_cases=_state_poll_cases(),
        final_snapshot_cases=_final_snapshot_cases(),
    )

    assert len(forecast_cases) == 22
    assert forecast_cases["forecast_source_id"].nunique() == 7
    assert "wallet" not in " ".join(forecast_cases.columns).lower()
    assert "maker" not in " ".join(forecast_cases.columns).lower()
    assert set(summary["calibration_scope"]) == {"limited_case_check"}
    assert len(pairwise) == 5
    assert int(pairwise["aggregate_mean_supports_polymarket"].sum()) >= 1
    assert int(pairwise["broad_many_cases_claim_supported"].sum()) == 0


def test_generate_h1_calibration_diagnostic_outputs(tmp_path: Path) -> None:
    rieke_path = tmp_path / "rieke.csv"
    two_seventy_path = tmp_path / "two_seventy.csv"
    state_poll_path = tmp_path / "state_poll.csv"
    final_path = tmp_path / "final.csv"
    _rieke_cases().to_csv(rieke_path, index=False)
    _two_seventy_cases().to_csv(two_seventy_path, index=False)
    _state_poll_cases().to_csv(state_poll_path, index=False)
    _final_snapshot_cases().to_csv(final_path, index=False)

    result = generate_h1_calibration_diagnostic_outputs(
        rieke_case_input=rieke_path,
        two_seventy_case_input=two_seventy_path,
        state_poll_case_input=state_poll_path,
        final_snapshot_case_input=final_path,
        forecast_case_output=tmp_path / "cases.csv",
        bin_output=tmp_path / "bins.csv",
        summary_output=tmp_path / "summary.csv",
        pairwise_output=tmp_path / "pairwise.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    cases = pd.read_csv(tmp_path / "cases.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    pairwise = pd.read_csv(tmp_path / "pairwise.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.forecast_case_row_count == 22
    assert result.forecast_source_count == 7
    assert result.pairwise_comparison_count == 5
    assert metadata["method"]["daily_national_reliability_curve_excluded"] is True
    assert metadata["method"]["sparse_reliability_points_not_connected"] is True
    assert metadata["method"]["reliability_panel_min_case_count"] == 30
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert len(cases) == 22
    assert len(summary) == 7
    assert len(pairwise) == 5
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_validate_forecast_cases_rejects_forbidden_raw_trade_columns() -> None:
    cases = build_forecast_cases(
        rieke_cases=_rieke_cases(),
        two_seventy_cases=_two_seventy_cases(),
        state_poll_cases=_state_poll_cases(),
        final_snapshot_cases=_final_snapshot_cases(),
    )
    cases["maker_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        validate_forecast_cases(cases)


def _rieke_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "state": "Alpha",
                "outcome_value": 1.0,
                "rieke_republican_win_probability": 0.75,
                "polymarket_probability": 0.80,
            },
            {
                "state": "Beta",
                "outcome_value": 0.0,
                "rieke_republican_win_probability": 0.30,
                "polymarket_probability": 0.20,
            },
            {
                "state": "Gamma",
                "outcome_value": 1.0,
                "rieke_republican_win_probability": 0.55,
                "polymarket_probability": 0.60,
            },
            {
                "state": "Delta",
                "outcome_value": 0.0,
                "rieke_republican_win_probability": 0.40,
                "polymarket_probability": 0.45,
            },
        ]
    )


def _two_seventy_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "state": "Alpha",
                "outcome_value": 1.0,
                "two_seventy_trump_win_probability": 0.78,
                "two_seventy_probability_precision": "exact_percent",
                "polymarket_probability": 0.80,
            },
            {
                "state": "Beta",
                "outcome_value": 0.0,
                "two_seventy_trump_win_probability": 0.22,
                "two_seventy_probability_precision": "exact_percent",
                "polymarket_probability": 0.20,
            },
            {
                "state": "Gamma",
                "outcome_value": 1.0,
                "two_seventy_trump_win_probability": 0.52,
                "two_seventy_probability_precision": "exact_percent",
                "polymarket_probability": 0.60,
            },
            {
                "state": "Delta",
                "outcome_value": 0.0,
                "two_seventy_trump_win_probability": 0.42,
                "two_seventy_probability_precision": "censored_boundary_>99.9",
                "polymarket_probability": 0.45,
            },
        ]
    )


def _state_poll_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "state": "Alpha",
                "outcome_value": 1.0,
                "poll_derived_probability": 0.58,
                "polymarket_probability": 0.65,
            },
            {
                "state": "Beta",
                "outcome_value": 0.0,
                "poll_derived_probability": 0.35,
                "polymarket_probability": 0.30,
            },
            {
                "state": "Gamma",
                "outcome_value": 1.0,
                "poll_derived_probability": 0.52,
                "polymarket_probability": 0.55,
            },
        ]
    )


def _final_snapshot_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "case_alpha",
                "case_label": "Final Alpha",
                "outcome_value": 1.0,
                "traditional_probability": 0.54,
                "polymarket_probability": 0.62,
            },
            {
                "case_id": "case_beta",
                "case_label": "Final Beta",
                "outcome_value": 0.0,
                "traditional_probability": 0.47,
                "polymarket_probability": 0.40,
            },
        ]
    )
