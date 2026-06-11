from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd

from operations.analysis.h1_state_poll_panel_competitiveness_diagnostic import (
    add_competitiveness_columns,
    build_grid_summary,
    build_state_summary,
    build_summary,
    generate_h1_state_poll_panel_competitiveness_outputs,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    add_horizon_columns,
)


def test_competitiveness_grid_preserves_late_support_and_safe_counterexample() -> None:
    cases = add_competitiveness_columns(add_horizon_columns(_toy_cases()))
    grid = build_grid_summary(cases)
    state = build_state_summary(cases)
    summary = build_summary(cases=cases, grid=grid, state=state)

    late_low = _grid_row(grid, "61_90_days", "low_distance_tercile")
    late_middle = _grid_row(grid, "61_90_days", "middle_distance_tercile")
    late_high = _grid_row(grid, "61_90_days", "high_distance_tercile")

    assert int(late_low["polymarket_lower_loss_count"]) == 1
    assert int(late_middle["polymarket_lower_loss_count"]) == 1
    assert int(late_high["poll_derived_lower_loss_count"]) == 1
    assert int(_summary_value(summary, "late_non_safe_row_count")) == 4
    assert int(_summary_value(summary, "late_non_safe_polymarket_lower_loss_count")) == 4
    assert int(_summary_value(summary, "late_high_distance_row_count")) == 2
    assert int(_summary_value(summary, "late_high_distance_poll_lower_loss_count")) == 2
    assert int(_summary_value(summary, "broad_many_cases_claim_supported_now")) == 0


def test_generate_competitiveness_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_state_poll_panel_competitiveness_outputs(
        case_input=case_path,
        grid_output=tmp_path / "grid.csv",
        state_output=tmp_path / "state.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    grid = pd.read_csv(tmp_path / "grid.csv")
    state = pd.read_csv(tmp_path / "state.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.row_count == 9
    assert result.late_non_safe_row_count == 4
    assert result.late_non_safe_pm_lower_loss_count == 4
    assert result.late_high_distance_poll_lower_loss_count == 2
    assert len(grid) == 9
    assert set(state["scope_id"]) == {"late_non_safe_distance", "late_high_distance"}
    assert int(_summary_value(summary, "late_non_safe_polymarket_state_support_count")) == 2
    assert metadata["method"]["uses_fixed_competitiveness_thresholds"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["high_distance_rows_contradict_strong_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def _toy_cases() -> pd.DataFrame:
    rows = []
    specs = [
        ("far-low", "Arizona", "2024-05-01", 1.0, 0.55, 0.52),
        ("far-mid", "Georgia", "2024-05-01", 1.0, 0.55, 0.68),
        ("far-high", "Ohio", "2024-05-01", 1.0, 0.55, 0.92),
        ("late-low-a", "Arizona", "2024-08-20", 1.0, 0.80, 0.53),
        ("late-mid-a", "Georgia", "2024-08-20", 1.0, 0.90, 0.69),
        ("late-high-a", "Ohio", "2024-08-20", 1.0, 0.80, 0.93),
        ("late-low-b", "Arizona", "2024-09-10", 1.0, 0.82, 0.54),
        ("late-mid-b", "Georgia", "2024-09-10", 1.0, 0.91, 0.70),
        ("late-high-b", "Ohio", "2024-09-10", 1.0, 0.80, 0.94),
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


def _grid_row(
    grid: pd.DataFrame,
    horizon_bin: str,
    competitiveness_tier: str,
) -> pd.Series:
    rows = grid.loc[
        (grid["horizon_bin"] == horizon_bin)
        & (grid["competitiveness_tier"] == competitiveness_tier)
    ]
    assert len(rows) == 1
    return rows.iloc[0]


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
