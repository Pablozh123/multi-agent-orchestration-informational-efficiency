from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_scope_frontier import prepare_scope_cases
from operations.analysis.h1_robust_poll_scope_unit_quality import (
    build_summary_table,
    build_unit_table,
    generate_h1_robust_poll_scope_unit_quality_outputs,
    validate_summary_table,
    validate_unit_table,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import CASE_INPUT
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases


def test_robust_poll_scope_unit_quality_reduces_repeated_row_dependence() -> None:
    cases = prepare_scope_cases(read_panel_cases(CASE_INPUT))

    units = validate_unit_table(build_unit_table(cases))
    summary = validate_summary_table(build_summary_table(units))

    largest_state = _summary(summary, "largest_robust_lte120_low_middle", "state")
    largest_state_month = _summary(
        summary,
        "largest_robust_lte120_low_middle",
        "state_month",
    )
    largest_state_horizon = _summary(
        summary,
        "largest_robust_lte120_low_middle",
        "state_horizon",
    )
    strongest_state = _summary(summary, "strongest_robust_lte90_low_middle", "state")
    strongest_state_month = _summary(
        summary,
        "strongest_robust_lte90_low_middle",
        "state_month",
    )
    strongest_state_horizon = _summary(
        summary,
        "strongest_robust_lte90_low_middle",
        "state_horizon",
    )

    assert len(units) == 116
    assert len(summary) == 8

    assert largest_state["unit_count"] == 11
    assert largest_state["polymarket_support_count"] == 10
    assert largest_state["poll_derived_support_count"] == 1
    assert largest_state["exact_binomial_p_value_greater"] == pytest.approx(
        0.005859375
    )
    assert largest_state_month["unit_count"] == 26
    assert largest_state_month["polymarket_support_count"] == 18
    assert largest_state_month["poll_derived_support_count"] == 8
    assert largest_state_month["exact_binomial_p_value_greater"] == pytest.approx(
        0.03775934875011444
    )
    assert largest_state_month["median_unit_loss_advantage"] == pytest.approx(
        0.04838463316283399
    )
    assert largest_state_horizon["polymarket_support_count"] == 20
    assert largest_state_horizon["unit_count"] == 26

    assert strongest_state["unit_count"] == 9
    assert strongest_state["polymarket_support_count"] == 9
    assert strongest_state["poll_derived_support_count"] == 0
    assert strongest_state["exact_binomial_p_value_greater"] == pytest.approx(
        0.001953125
    )
    assert strongest_state_month["unit_count"] == 17
    assert strongest_state_month["polymarket_support_count"] == 17
    assert strongest_state_month["poll_derived_support_count"] == 0
    assert strongest_state_month["exact_binomial_p_value_greater"] == pytest.approx(
        7.62939453125e-06
    )
    assert strongest_state_month["median_unit_loss_advantage"] == pytest.approx(
        0.0723122744230541
    )
    assert strongest_state_horizon["polymarket_support_count"] == 17
    assert strongest_state_horizon["unit_count"] == 17
    assert bool(strongest_state_horizon["all_units_support_polymarket"]) is True
    assert bool(strongest_state_horizon["broad_claim_supported"]) is False


def test_generate_robust_poll_scope_unit_quality_outputs(tmp_path: Path) -> None:
    result = generate_h1_robust_poll_scope_unit_quality_outputs(
        case_input=CASE_INPUT,
        unit_output=tmp_path / "units.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    units = pd.read_csv(tmp_path / "units.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.unit_row_count == 116
    assert result.summary_row_count == 8
    assert result.largest_state_month_unit_count == 26
    assert result.largest_state_month_polymarket_support_count == 18
    assert result.strongest_state_month_unit_count == 17
    assert result.strongest_state_month_polymarket_support_count == 17
    assert result.broad_claim_proven is False

    assert len(units) == 116
    assert len(summary) == 8
    assert metadata["outputs"]["unit_row_count"] == 116
    assert metadata["outputs"]["summary_row_count"] == 8
    assert metadata["outputs"]["largest_state_month_exact_binomial_p_value"] == pytest.approx(
        0.03775934875011444
    )
    assert metadata["outputs"]["strongest_state_month_exact_binomial_p_value"] == pytest.approx(
        7.62939453125e-06
    )
    assert metadata["outputs"]["broad_claim_proven"] is False
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["unit_aggregation_reduces_repeated_row_dependence"] is True
    assert metadata["limitations"]["bounded_scope_quality_not_broad_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_robust_poll_scope_unit_quality_rejects_forbidden_columns() -> None:
    cases = prepare_scope_cases(read_panel_cases(CASE_INPUT))
    units = build_unit_table(cases)
    units["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden raw-trade"):
        validate_unit_table(units)


def _summary(
    summary: pd.DataFrame,
    scope_id: str,
    unit_type: str,
) -> dict[str, object]:
    rows = summary.loc[
        (summary["scope_id"] == scope_id) & (summary["unit_type"] == unit_type)
    ]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()
