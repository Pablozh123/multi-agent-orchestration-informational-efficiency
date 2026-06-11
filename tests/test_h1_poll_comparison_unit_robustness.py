from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_comparison_unit_robustness import (
    build_summary_table,
    build_unit_table,
    generate_h1_poll_comparison_unit_robustness_outputs,
    prepare_cases,
    validate_unit_table,
)


def test_unit_robustness_aggregates_primary_scope() -> None:
    cases = prepare_cases(_toy_cases())
    units = validate_unit_table(build_unit_table(cases))
    summary = build_summary_table(cases, units)

    assert int(_summary_value(summary, "primary_row_count")) == 4
    assert int(_summary_value(summary, "primary_polymarket_lower_loss_count")) == 4
    assert int(_summary_value(summary, "primary_state_unit_count")) == 2
    assert int(_summary_value(summary, "primary_state_polymarket_support_count")) == 2
    assert int(_summary_value(summary, "primary_state_month_unit_count")) == 4
    assert int(_summary_value(summary, "primary_state_month_polymarket_support_count")) == 4
    assert float(
        _summary_value(
            summary,
            "primary_state_month_polymarket_exact_binomial_p_value_greater",
        )
    ) == pytest.approx(0.0625)
    assert float(
        _summary_value(
            summary,
            "primary_state_month_polymarket_exact_95_ci_low",
        )
    ) == pytest.approx(0.4728708045015879)
    assert int(_summary_value(summary, "primary_state_horizon_unit_count")) == 4
    assert int(_summary_value(summary, "primary_state_horizon_polymarket_support_count")) == 4
    assert int(_summary_value(summary, "primary_horizon_tier_unit_count")) == 4
    assert int(_summary_value(summary, "primary_horizon_tier_polymarket_support_count")) == 4
    assert int(_summary_value(summary, "late_high_state_month_unit_count")) == 2
    assert int(_summary_value(summary, "late_high_state_month_poll_support_count")) == 2
    assert int(_summary_value(summary, "primary_scope_supported_across_all_units")) == 1
    assert int(_summary_value(summary, "broad_claim_proven")) == 0


def test_generate_unit_robustness_outputs(tmp_path: Path) -> None:
    case_path = tmp_path / "cases.csv"
    _toy_cases().to_csv(case_path, index=False)

    result = generate_h1_poll_comparison_unit_robustness_outputs(
        case_input=case_path,
        unit_output=tmp_path / "units.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    units = pd.read_csv(tmp_path / "units.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.unit_row_count == len(units)
    assert result.primary_state_month_unit_count == 4
    assert result.primary_state_month_polymarket_support_count == 4
    assert result.broad_claim_proven is False
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"
    assert metadata["method"]["uses_quantile_derived_competitiveness_tiers"] is True
    assert metadata["method"]["uses_fixed_competitiveness_thresholds"] is False
    assert metadata["outputs"]["primary_state_month_exact_binomial_p_value"] == pytest.approx(
        0.0625
    )
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["state_month_units_are_not_independent_elections"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_unit_robustness_rejects_forbidden_columns() -> None:
    cases = prepare_cases(_toy_cases())
    units = build_unit_table(cases)
    units["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden columns"):
        validate_unit_table(units)


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


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
