from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_claim_readiness import (
    build_claim_table,
    build_summary_table,
    generate_h1_poll_claim_readiness_outputs,
    read_summary,
    validate_claim_table,
    validate_summary_table,
)


def test_claim_readiness_table_separates_bounded_support_and_counterexamples() -> None:
    inputs = _input_frames()

    claims = validate_claim_table(build_claim_table(**inputs))
    summary = validate_summary_table(build_summary_table(claims=claims, **inputs))

    primary = _claim(claims, "bounded_primary_state_date_rows")
    full_panel = _claim(claims, "full_state_date_panel")

    assert len(claims) == 13
    assert primary["claim_status"] == "supported"
    assert primary["polymarket_support_count"] == 8
    assert primary["comparison_count"] == 10
    assert primary["polymarket_support_share"] == pytest.approx(0.8)
    assert full_panel["claim_status"] == "contradicted"
    assert full_panel["polymarket_support_count"] == 5
    assert full_panel["poll_support_count"] == 15
    assert int(_summary_value(summary, "supported_bounded_scope_row_count")) == 4
    assert int(_summary_value(summary, "counterexample_row_count")) == 5
    assert int(_summary_value(summary, "bounded_poll_claim_supported")) == 1
    assert int(_summary_value(summary, "broad_claim_proven")) == 0
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"


def test_generate_claim_readiness_outputs_writes_nonblank_figure(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_h1_poll_claim_readiness_outputs(
        poll_result_input=paths["poll_result"],
        unit_robustness_input=paths["unit_robustness"],
        direct_loss_input=paths["direct_loss"],
        direct_state_input=paths["direct_state"],
        outlier_input=paths["outlier"],
        state_panel_input=paths["state_panel"],
        popular_vote_input=paths["popular_vote"],
        state_significance_input=paths["state_significance"],
        claim_output=tmp_path / "claims.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.claim_row_count == 13
    assert result.bounded_claim_supported is True
    assert result.broad_claim_proven is False
    assert result.primary_polymarket_support_share == pytest.approx(0.8)
    assert result.primary_state_month_p_value == pytest.approx(0.0625)
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["bounded_poll_claim_supported"] is True
    assert metadata["limitations"]["broad_many_cases_claim_not_yet_proven"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_claim_readiness_rejects_forbidden_summary_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    _summary_frame({"primary_comparison_count": 10}).assign(
        wallet_address="0xabc"
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="forbidden columns"):
        read_summary(path)


def _input_frames() -> dict[str, pd.DataFrame]:
    return {
        "poll_result": _summary_frame(
            {
                "primary_comparison_count": 10,
                "primary_polymarket_support_count": 8,
                "primary_poll_support_count": 2,
                "primary_mean_loss_advantage": 0.1,
                "primary_state_count": 3,
                "primary_polymarket_state_count": 3,
                "primary_exact_binomial_p_value": 0.125,
                "primary_exact_95_ci_low": 0.3,
            }
        ),
        "unit_robustness": _summary_frame(
            {
                "primary_state_month_unit_count": 4,
                "primary_state_month_polymarket_support_count": 4,
                "primary_state_month_polymarket_exact_binomial_p_value_greater": 0.0625,
                "primary_state_month_polymarket_exact_95_ci_low": 0.4729,
                "primary_state_horizon_unit_count": 4,
                "primary_state_horizon_polymarket_support_count": 4,
                "primary_state_horizon_polymarket_exact_binomial_p_value_greater": 0.0625,
                "primary_state_horizon_polymarket_exact_95_ci_low": 0.4729,
                "primary_horizon_tier_unit_count": 2,
                "primary_horizon_tier_polymarket_support_count": 2,
                "primary_horizon_tier_polymarket_exact_binomial_p_value_greater": 0.25,
                "primary_horizon_tier_polymarket_exact_95_ci_low": 0.158,
                "full_panel_state_month_unit_count": 5,
                "full_panel_state_month_polymarket_support_count": 1,
                "full_panel_state_month_poll_support_count": 4,
                "late_high_row_count": 6,
                "late_high_poll_lower_loss_count": 6,
            }
        ),
        "direct_loss": _summary_frame(
            {
                "direct_poll_case_count": 5,
                "direct_poll_polymarket_lower_loss_count": 2,
                "direct_poll_comparator_lower_loss_count": 3,
                "direct_poll_tie_count": 0,
                "direct_poll_mean_loss_advantage": 0.02,
            }
        ),
        "direct_state": _summary_frame(
            {
                "state_count": 4,
                "state_mean_polymarket_support_count": 1,
                "state_mean_poll_support_count": 3,
                "state_mean_tie_count": 0,
                "equal_state_mean_loss_advantage": 0.01,
                "equal_state_sign_flip_p_value_greater": 0.03,
                "equal_state_bootstrap_95_ci_low": 0.001,
            }
        ),
        "outlier": _summary_frame(
            {
                "leave_one_out_scenario_count": 4,
                "min_leave_one_out_mean_loss_advantage": 0.005,
            }
        ),
        "state_panel": _summary_frame(
            {
                "matched_case_count": 20,
                "polymarket_lower_loss_count": 5,
                "poll_derived_lower_loss_count": 15,
                "tie_count": 0,
                "mean_loss_advantage": -0.04,
            }
        ),
        "popular_vote": _summary_frame(
            {
                "case_count": 10,
                "polymarket_lower_loss_count": 4,
                "poll_derived_lower_loss_count": 6,
                "tie_count": 0,
                "mean_loss_advantage": -0.03,
            }
        ),
        "state_significance": _summary_frame(
            {
                "late_high_distance_state_count": 2,
                "late_high_distance_polymarket_majority_state_count": 0,
                "late_high_distance_poll_majority_state_count": 2,
                "late_high_distance_poll_exact_binomial_p_value_greater": 0.25,
            }
        ),
    }


def _write_inputs(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, frame in _input_frames().items():
        path = root / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


def _summary_frame(values: dict[str, float | int | str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "summary_id": key,
                "value": value,
                "unit": "unit",
                "description": key,
            }
            for key, value in values.items()
        ]
    )


def _claim(frame: pd.DataFrame, claim_id: str) -> dict[str, object]:
    rows = frame.loc[frame["claim_id"] == claim_id]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()


def _summary_value(summary: pd.DataFrame, summary_id: str):
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return row.iloc[0]
