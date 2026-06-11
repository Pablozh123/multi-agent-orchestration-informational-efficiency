from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_poll_decision_matrix import (
    build_decision_table,
    build_summary_table,
    generate_h1_poll_decision_matrix_outputs,
    read_calibration_pairwise,
    read_frontier,
    read_summary,
    validate_decision_table,
    validate_summary_table,
)


def test_poll_decision_matrix_marks_bounded_yes_and_counterexamples() -> None:
    decision = validate_decision_table(
        build_decision_table(
            frontier=read_frontier(Path("data/results/h1_poll_scope_frontier.csv")),
            direct_poll_state_cluster=read_summary(
                Path("data/results/h1_direct_poll_state_cluster_diagnostic_summary.csv")
            ),
            two_seventy_poll_average=read_summary(
                Path("data/results/h1_270towin_poll_average_summary.csv")
            ),
            state_source_consensus=read_summary(
                Path("data/results/h1_state_source_consensus_summary.csv")
            ),
            calibration_pairwise=read_calibration_pairwise(
                Path("data/results/h1_calibration_diagnostic_pairwise.csv")
            ),
        )
    )
    summary = validate_summary_table(
        build_summary_table(
            decision=decision,
            frontier_summary=read_summary(
                Path("data/results/h1_poll_scope_frontier_summary.csv")
            ),
            calibration_pairwise=read_calibration_pairwise(
                Path("data/results/h1_calibration_diagnostic_pairwise.csv")
            ),
        )
    )

    largest = _decision(decision, "largest_robust_poll_scope")
    strongest = _decision(decision, "strongest_robust_poll_scope")
    full_panel = _decision(decision, "full_poll_panel_counterexample")
    direct_mean = _decision(decision, "direct_poll_equal_state_mean")
    two_seventy = _decision(decision, "two_seventy_poll_average_states")
    calibration = _decision(decision, "calibration_resolved_case_sets")

    assert len(decision) == 9
    assert largest["decision_status"] == "robust_bounded_yes"
    assert largest["case_count"] == 433
    assert largest["polymarket_support_count"] == 313
    assert largest["comparator_support_count"] == 120
    assert largest["polymarket_unit_support_count"] == 18
    assert largest["unit_count"] == 26
    assert largest["p_value"] == pytest.approx(0.03775934875011444)
    assert strongest["polymarket_support_count"] == 262
    assert strongest["case_count"] == 285
    assert strongest["p_value"] == pytest.approx(7.62939453125e-06)
    assert full_panel["decision_status"] == "counterexample"
    assert full_panel["comparator_support_count"] == 1360
    assert full_panel["case_count"] == 1720
    assert direct_mean["decision_status"] == "mixed_mean_only"
    assert direct_mean["mean_supports_polymarket"] is True
    assert direct_mean["case_majority_supports_polymarket"] is False
    assert two_seventy["polymarket_support_count"] == 14
    assert two_seventy["comparator_support_count"] == 29
    assert calibration["polymarket_support_count"] == 5
    assert calibration["polymarket_unit_support_count"] == 2
    assert _summary_value(summary, "bounded_poll_claim_ready") == "1"
    assert _summary_value(summary, "broad_claim_proven") == "0"


def test_generate_poll_decision_matrix_outputs_writes_nonblank_figure(tmp_path: Path) -> None:
    result = generate_h1_poll_decision_matrix_outputs(
        decision_output=tmp_path / "decision.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "decision.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "decision.png")

    assert result.decision_row_count == 9
    assert result.robust_bounded_yes_count == 2
    assert result.counterexample_count == 2
    assert result.broad_claim_proven is False
    assert metadata["outputs"]["bounded_poll_claim_ready"] is True
    assert metadata["outputs"]["broad_claim_proven"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["limitations"]["full_panel_still_contradicts_broad_claim"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_poll_decision_matrix_rejects_forbidden_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "decision_id": "bad",
                "decision_label": "Bad",
                "evidence_family": "test",
                "scope": "test",
                "comparison_unit": "rows",
                "case_count": 1,
                "polymarket_support_count": 1,
                "comparator_support_count": 0,
                "tie_count": 0,
                "polymarket_support_share": 1.0,
                "mean_loss_advantage": 0.1,
                "unit_count": 1,
                "polymarket_unit_support_count": 1,
                "comparator_unit_support_count": 0,
                "p_value": 0.5,
                "mean_supports_polymarket": True,
                "case_majority_supports_polymarket": True,
                "unit_supports_polymarket": True,
                "broad_claim_supported": False,
                "decision_status": "robust_bounded_yes",
                "allowed_claim": "test",
                "limitation": "test",
                "wallet_address": "0xabc",
            }
        ]
    )

    with pytest.raises(ValueError, match="forbidden columns"):
        validate_decision_table(frame)


def _decision(frame: pd.DataFrame, decision_id: str) -> dict[str, object]:
    rows = frame.loc[frame["decision_id"] == decision_id]
    assert len(rows) == 1
    return rows.iloc[0].to_dict()


def _summary_value(frame: pd.DataFrame, summary_id: str) -> str:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    assert len(rows) == 1
    return str(rows.iloc[0])
