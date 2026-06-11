from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_panel_horizon_diagnostic import add_horizon_columns
from operations.analysis.h1_state_poll_panel_near_window_quality import (
    build_calibration_bins,
    build_forecast_rows,
    build_quality_summary,
    generate_h1_state_poll_panel_near_window_quality_outputs,
    validate_forecast_rows,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_near_window_quality_compares_score_calibration_and_separation() -> None:
    cases = add_horizon_columns(_toy_cases())
    near = cases.loc[cases["days_to_election"] <= 90]
    forecast_rows = validate_forecast_rows(build_forecast_rows(near))
    bins = build_calibration_bins(forecast_rows)
    summary = build_quality_summary(forecast_rows, bins).set_index("source_id")

    assert len(forecast_rows) == 12
    assert set(summary.index) == {"polymarket", "poll_derived"}
    assert int(summary.loc["polymarket", "row_count"]) == 6
    assert int(summary.loc["polymarket", "state_count"]) == 3
    assert summary.loc["polymarket", "mean_brier_loss"] < summary.loc[
        "poll_derived",
        "mean_brier_loss",
    ]
    assert summary.loc["polymarket", "expected_calibration_error"] < summary.loc[
        "poll_derived",
        "expected_calibration_error",
    ]
    assert summary.loc["polymarket", "probability_separation"] > summary.loc[
        "poll_derived",
        "probability_separation",
    ]
    assert bins["row_count"].sum() == len(forecast_rows)


def test_generate_near_window_quality_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_state_poll_panel_near_window_quality_outputs(
        case_input=case_path,
        forecast_rows_output=tmp_path / "forecast_rows.csv",
        bin_output=tmp_path / "bins.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    forecast_rows = pd.read_csv(tmp_path / "forecast_rows.csv")
    bins = pd.read_csv(tmp_path / "bins.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.row_count == 6
    assert result.state_count == 3
    assert result.polymarket_mean_brier < result.poll_derived_mean_brier
    assert result.polymarket_expected_calibration_error < (
        result.poll_derived_expected_calibration_error
    )
    assert len(forecast_rows) == 12
    assert len(bins) == 10
    assert set(summary["source_id"]) == {"polymarket", "poll_derived"}
    assert metadata["outputs"]["forecast_row_count"] == 12
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["limitations"]["calibration_rows_are_repeated_forecasts"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_near_window_quality_rejects_raw_trade_columns(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    cases = _toy_cases()
    cases["maker_address"] = "0xabc"
    cases.to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        read_panel_cases(path)


def _toy_cases() -> pd.DataFrame:
    rows = []
    specs = [
        ("case-1", "Arizona", "2024-08-20", 1.0, 0.90, 0.60),
        ("case-2", "Arizona", "2024-09-10", 1.0, 0.88, 0.58),
        ("case-3", "Michigan", "2024-08-20", 1.0, 0.91, 0.55),
        ("case-4", "Michigan", "2024-09-10", 1.0, 0.89, 0.59),
        ("case-5", "Texas", "2024-08-20", 0.0, 0.10, 0.35),
        ("case-6", "Texas", "2024-09-10", 0.0, 0.12, 0.38),
        ("case-7", "Arizona", "2024-05-01", 1.0, 0.20, 0.80),
    ]
    for case_id, state, date, outcome, pm_probability, poll_probability in specs:
        pm_brier = (pm_probability - outcome) ** 2
        poll_brier = (poll_probability - outcome) ** 2
        rows.append(
            {
                "case_id": case_id,
                "state": state,
                "forecast_date": date,
                "outcome_value": outcome,
                "polymarket_probability": pm_probability,
                "poll_derived_probability": poll_probability,
                "polymarket_brier": pm_brier,
                "poll_derived_brier": poll_brier,
                "loss_advantage": poll_brier - pm_brier,
                "lower_loss_source": (
                    "polymarket"
                    if pm_brier < poll_brier
                    else "poll_derived_forecast"
                ),
            }
        )
    return pd.DataFrame(rows)
