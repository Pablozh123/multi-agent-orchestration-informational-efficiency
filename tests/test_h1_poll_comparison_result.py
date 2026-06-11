from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_comparison_result import (
    build_result_table,
    build_summary_table,
    generate_h1_poll_comparison_result_outputs,
    validate_result_table,
)


def test_build_h1_poll_comparison_result_is_bounded_not_broad() -> None:
    result = validate_result_table(
        build_result_table(
            claim_audit=_claim_audit_frame(),
            claim_summary=_claim_summary_frame(),
            panel_competitiveness=_panel_competitiveness_frame(),
            state_significance=_state_significance_frame(),
        )
    )
    summary = build_summary_table(result, _claim_summary_frame())

    primary = result.loc[
        result["result_id"] == "bounded_late_competitive_poll_rows"
    ].iloc[0]
    state_sign = result.loc[
        result["result_id"] == "bounded_late_competitive_state_sign_test"
    ].iloc[0]
    full_panel = result.loc[
        result["result_id"] == "full_poll_panel_counterexample"
    ].iloc[0]
    high_distance = result.loc[
        result["result_id"] == "late_high_distance_counterexample"
    ].iloc[0]

    assert len(result) == 6
    assert int(primary["polymarket_support_count"]) == 262
    assert int(primary["poll_support_count"]) == 23
    assert int(primary["comparison_count"]) == 285
    assert float(primary["polymarket_support_share"]) == pytest.approx(262 / 285)
    assert bool(primary["supports_bounded_polymarket_statement"]) is True
    assert int(state_sign["polymarket_support_count"]) == 9
    assert int(state_sign["poll_support_count"]) == 0
    assert float(state_sign["exact_p_value"]) == pytest.approx(0.001953125)
    assert bool(full_panel["contradicts_broad_polymarket_statement"]) is True
    assert int(full_panel["poll_support_count"]) == 1360
    assert bool(high_distance["contradicts_broad_polymarket_statement"]) is True
    assert int(high_distance["poll_support_count"]) == 72
    assert _summary_value(summary, "bounded_polymarket_statement_supported") == "1"
    assert _summary_value(summary, "broad_claim_proven") == "0"
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"


def test_generate_h1_poll_comparison_result_outputs(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    generated = generate_h1_poll_comparison_result_outputs(
        claim_audit_input=paths["claim_audit"],
        claim_audit_summary_input=paths["claim_summary"],
        panel_competitiveness_input=paths["panel_competitiveness"],
        state_significance_input=paths["state_significance"],
        result_output=tmp_path / "result.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    result = pd.read_csv(tmp_path / "result.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert generated.result_row_count == 6
    assert generated.primary_polymarket_support_count == 262
    assert generated.primary_poll_support_count == 23
    assert generated.primary_state_count == 9
    assert generated.broad_claim_proven is False
    assert len(result) == 6
    assert _summary_value(summary, "primary_polymarket_support_count") == "262"
    assert _summary_value(summary, "primary_polymarket_state_count") == "9"
    assert metadata["outputs"]["bounded_polymarket_statement_supported"] is True
    assert metadata["outputs"]["broad_claim_proven"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["full_state_date_panel_contradicts_broad_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_validate_result_table_rejects_forbidden_columns() -> None:
    result = build_result_table(
        claim_audit=_claim_audit_frame(),
        claim_summary=_claim_summary_frame(),
        panel_competitiveness=_panel_competitiveness_frame(),
        state_significance=_state_significance_frame(),
    )
    result["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden columns"):
        validate_result_table(result)


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    frames = {
        "claim_audit": _claim_audit_frame(),
        "claim_summary": _claim_summary_frame(),
        "panel_competitiveness": _panel_competitiveness_frame(),
        "state_significance": _state_significance_frame(),
    }
    paths: dict[str, Path] = {}
    for key, frame in frames.items():
        path = tmp_path / f"{key}.csv"
        frame.to_csv(path, index=False)
        paths[key] = path
    return paths


def _claim_audit_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "audit_id": "full_state_date_poll_panel",
                "comparison_unit": "state_date_rows",
                "comparison_count": 1720,
                "state_count": 15,
                "polymarket_support_count": 360,
                "comparator_support_count": 1360,
                "tie_count": 0,
                "polymarket_support_share": 360 / 1720,
                "mean_polymarket_brier": 0.1594798197674418,
                "mean_comparator_brier": 0.1026002677570564,
                "mean_loss_advantage": -0.0568795520103854,
                "limitation": "Rows repeat resolved states.",
                "source_artifact": "h1_state_poll_panel_horizon_claim_audit.csv",
            },
            {
                "audit_id": "late_90_day_state_date_rows",
                "comparison_unit": "state_date_rows",
                "comparison_count": 357,
                "state_count": 13,
                "polymarket_support_count": 262,
                "comparator_support_count": 95,
                "tie_count": 0,
                "polymarket_support_share": 262 / 357,
                "mean_polymarket_brier": 0.179920350140056,
                "mean_comparator_brier": 0.2520477705719791,
                "mean_loss_advantage": 0.0721274204319231,
                "limitation": "Late rows repeat resolved states.",
                "source_artifact": "h1_state_poll_panel_horizon_claim_audit.csv",
            },
        ]
    )


def _claim_summary_frame() -> pd.DataFrame:
    return _summary_frame(
        {
            "direct_poll_audit_row_count": 15,
            "direct_poll_support_row_count": 12,
            "direct_poll_contradiction_row_count": 3,
            "broad_user_claim_proven": 0,
        }
    )


def _panel_competitiveness_frame() -> pd.DataFrame:
    return _summary_frame(
        {
            "late_non_safe_row_count": 285,
            "late_non_safe_state_count": 9,
            "late_non_safe_polymarket_lower_loss_count": 262,
            "late_non_safe_poll_lower_loss_count": 23,
            "late_non_safe_mean_loss_advantage": 0.09327158775169828,
            "late_non_safe_mean_polymarket_brier": 0.2214428070175438,
            "late_non_safe_mean_poll_brier": 0.3147143947692421,
            "late_high_distance_row_count": 72,
            "late_high_distance_state_count": 5,
            "late_high_distance_polymarket_lower_loss_count": 0,
            "late_high_distance_poll_lower_loss_count": 72,
            "late_high_distance_mean_loss_advantage": -0.01156824187552041,
            "late_high_distance_mean_polymarket_brier": 0.015560624999999988,
            "late_high_distance_mean_poll_brier": 0.0039923831244795,
        }
    )


def _state_significance_frame() -> pd.DataFrame:
    return _summary_frame(
        {
            "late_non_safe_state_count": 9,
            "late_non_safe_polymarket_majority_state_count": 9,
            "late_non_safe_polymarket_exact_binomial_p_value_greater": 0.001953125,
            "late_non_safe_polymarket_exact_95_ci_low": 0.7168711644368863,
            "late_high_distance_state_count": 5,
            "late_high_distance_poll_majority_state_count": 5,
            "late_high_distance_poll_exact_binomial_p_value_greater": 0.03125,
        }
    )


def _summary_frame(values: dict[str, float | int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"summary_id": key, "value": value, "unit": "", "description": ""}
            for key, value in values.items()
        ]
    )


def _summary_value(summary: pd.DataFrame, summary_id: str) -> str:
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return str(row.iloc[0])
