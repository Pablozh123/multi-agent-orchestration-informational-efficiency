from __future__ import annotations

import json
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_claim_evidence_audit import (
    build_claim_audit_summary,
    build_claim_audit_table,
    generate_h1_claim_evidence_audit_outputs,
    validate_audit_table,
)


def test_build_claim_audit_table_marks_late_support_but_not_completion() -> None:
    audit = validate_audit_table(
        build_claim_audit_table(
            synthesis=_synthesis_frame(),
            horizon_claim=_horizon_claim_frame(),
            horizon_state=_summary_frame(_horizon_state_values()),
            near_quality=_near_quality_frame(),
            final_snapshot=_summary_frame(_final_snapshot_values()),
            state_poll=_summary_frame(_state_poll_values()),
            popular_vote=_summary_frame(_popular_vote_values()),
            rieke=_summary_frame(_rieke_values()),
            two_seventy=_summary_frame(_two_seventy_values()),
            two_seventy_poll_average=_summary_frame(_two_seventy_poll_average_values()),
            state_source_consensus=_summary_frame(_state_source_consensus_values()),
            competitive_state=_summary_frame(_competitive_state_values()),
            panel_competitiveness=_summary_frame(_panel_competitiveness_values()),
            state_significance=_summary_frame(_state_significance_values()),
        )
    )
    summary = build_claim_audit_summary(audit)

    full_panel = audit.loc[audit["audit_id"] == "full_state_date_poll_panel"].iloc[0]
    late_rows = audit.loc[audit["audit_id"] == "late_90_day_state_date_rows"].iloc[0]
    all_source = audit.loc[audit["audit_id"] == "all_source_state_consensus"].iloc[0]
    direct_two = audit.loc[
        audit["audit_id"] == "direct_poll_two_source_state_consensus"
    ].iloc[0]
    competitive_low = audit.loc[
        audit["audit_id"] == "low_distance_competitive_cases"
    ].iloc[0]
    direct_low = audit.loc[
        audit["audit_id"] == "direct_poll_low_distance_competitive_cases"
    ].iloc[0]
    safe_high = audit.loc[audit["audit_id"] == "high_distance_safe_cases"].iloc[0]
    late_non_safe = audit.loc[
        audit["audit_id"] == "late_non_safe_competitive_state_date_rows"
    ].iloc[0]
    state_sign = audit.loc[
        audit["audit_id"] == "late_non_safe_state_significance"
    ].iloc[0]
    late_high = audit.loc[
        audit["audit_id"] == "late_high_distance_state_date_rows"
    ].iloc[0]
    completion = audit.loc[audit["audit_id"] == "completion_audit"].iloc[0]

    assert len(audit) == 22
    assert int(audit["supports_polymarket"].sum()) == 16
    assert int(audit["contradicts_polymarket"].sum()) == 5
    assert int(audit["proves_broad_user_claim"].sum()) == 0
    assert bool(full_panel["contradicts_polymarket"]) is True
    assert full_panel["polymarket_support_count"] == 360
    assert full_panel["comparator_support_count"] == 1360
    assert bool(late_rows["supports_polymarket"]) is True
    assert late_rows["polymarket_support_count"] == 262
    assert late_rows["comparator_support_count"] == 95
    assert bool(all_source["contradicts_polymarket"]) is True
    assert all_source["polymarket_support_count"] == 9
    assert all_source["comparator_support_count"] == 37
    assert bool(direct_two["supports_polymarket"]) is True
    assert direct_two["polymarket_support_count"] == 8
    assert direct_two["comparator_support_count"] == 4
    assert bool(competitive_low["supports_polymarket"]) is True
    assert competitive_low["polymarket_support_count"] == 35
    assert competitive_low["comparator_support_count"] == 17
    assert bool(direct_low["supports_polymarket"]) is True
    assert direct_low["polymarket_support_count"] == 18
    assert direct_low["comparator_support_count"] == 1
    assert bool(safe_high["contradicts_polymarket"]) is True
    assert safe_high["polymarket_support_count"] == 0
    assert safe_high["comparator_support_count"] == 40
    assert bool(late_non_safe["supports_polymarket"]) is True
    assert late_non_safe["polymarket_support_count"] == 262
    assert late_non_safe["comparator_support_count"] == 23
    assert late_non_safe["polymarket_secondary_value"] == 9
    assert bool(state_sign["supports_polymarket"]) is True
    assert state_sign["polymarket_support_count"] == 9
    assert state_sign["comparator_support_count"] == 0
    assert state_sign["polymarket_secondary_value"] == 0.001953125
    assert bool(late_high["contradicts_polymarket"]) is True
    assert late_high["polymarket_support_count"] == 0
    assert late_high["comparator_support_count"] == 72
    assert bool(completion["supports_polymarket"]) is False
    assert _summary_value(summary, "broad_user_claim_proven") == "0"
    assert _summary_value(summary, "h1_goal_completion_status") == "not_proven"


def test_generate_h1_claim_evidence_audit_outputs(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_h1_claim_evidence_audit_outputs(
        synthesis_input=paths["synthesis"],
        horizon_claim_input=paths["horizon_claim"],
        horizon_state_input=paths["horizon_state"],
        near_quality_input=paths["near_quality"],
        final_snapshot_input=paths["final_snapshot"],
        state_poll_input=paths["state_poll"],
        popular_vote_input=paths["popular_vote"],
        rieke_input=paths["rieke"],
        two_seventy_input=paths["two_seventy"],
        two_seventy_poll_average_input=paths["two_seventy_poll_average"],
        state_source_consensus_input=paths["state_source_consensus"],
        competitive_state_input=paths["competitive_state"],
        panel_competitiveness_input=paths["panel_competitiveness"],
        state_significance_input=paths["state_significance"],
        audit_output=tmp_path / "audit.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(tmp_path / "summary.csv")
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.audit_row_count == 22
    assert result.support_row_count == 16
    assert result.contradiction_row_count == 5
    assert result.broad_user_claim_proven is False
    assert metadata["outputs"]["h1_goal_completion_status"] == "not_proven"
    assert metadata["outputs"]["broad_user_claim_proven"] is False
    assert metadata["limitations"]["full_state_date_panel_contradicts_strong_claim"] is True
    assert metadata["limitations"]["popular_vote_extension_contradicts_strong_claim"] is True
    assert _summary_value(summary, "late_window_polymarket_lower_loss_count") == "262"
    assert _summary_value(summary, "full_panel_poll_lower_loss_count") == "1360"
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_validate_audit_table_rejects_forbidden_columns() -> None:
    audit = build_claim_audit_table(
        synthesis=_synthesis_frame(),
        horizon_claim=_horizon_claim_frame(),
        horizon_state=_summary_frame(_horizon_state_values()),
        near_quality=_near_quality_frame(),
        final_snapshot=_summary_frame(_final_snapshot_values()),
        state_poll=_summary_frame(_state_poll_values()),
        popular_vote=_summary_frame(_popular_vote_values()),
        rieke=_summary_frame(_rieke_values()),
        two_seventy=_summary_frame(_two_seventy_values()),
        two_seventy_poll_average=_summary_frame(_two_seventy_poll_average_values()),
        state_source_consensus=_summary_frame(_state_source_consensus_values()),
        competitive_state=_summary_frame(_competitive_state_values()),
        panel_competitiveness=_summary_frame(_panel_competitiveness_values()),
        state_significance=_summary_frame(_state_significance_values()),
    )
    audit["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden columns"):
        validate_audit_table(audit)


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    frames = {
        "synthesis": _synthesis_frame(),
        "horizon_claim": _horizon_claim_frame(),
        "horizon_state": _summary_frame(_horizon_state_values()),
        "near_quality": _near_quality_frame(),
        "final_snapshot": _summary_frame(_final_snapshot_values()),
        "state_poll": _summary_frame(_state_poll_values()),
        "popular_vote": _summary_frame(_popular_vote_values()),
        "rieke": _summary_frame(_rieke_values()),
        "two_seventy": _summary_frame(_two_seventy_values()),
        "two_seventy_poll_average": _summary_frame(_two_seventy_poll_average_values()),
        "state_source_consensus": _summary_frame(_state_source_consensus_values()),
        "competitive_state": _summary_frame(_competitive_state_values()),
        "panel_competitiveness": _summary_frame(_panel_competitiveness_values()),
        "state_significance": _summary_frame(_state_significance_values()),
    }
    paths: dict[str, Path] = {}
    for key, frame in frames.items():
        path = tmp_path / f"{key}.csv"
        frame.to_csv(path, index=False)
        paths[key] = path
    return paths


def _synthesis_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "aggregate_mean_supports_polymarket": [
                True,
                True,
                True,
                False,
                False,
                True,
                True,
                True,
                True,
            ],
            "majority_cases_supports_polymarket": [
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "broad_many_cases_claim_supported": [False] * 9,
        }
    )


def _horizon_claim_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "audit_scope": "full_panel",
                "row_count": 1720,
                "state_count": 15,
                "polymarket_lower_loss_count": 360,
                "poll_derived_lower_loss_count": 1360,
                "tie_count": 0,
                "polymarket_better_share": 360 / 1720,
                "mean_polymarket_brier": 0.15947981976744185,
                "mean_poll_derived_brier": 0.10260026775705648,
                "mean_loss_advantage": -0.05687955201038537,
                "limitation": "Repeated forecast rows.",
            },
            {
                "audit_scope": "within_90_days_before_election",
                "row_count": 357,
                "state_count": 13,
                "polymarket_lower_loss_count": 262,
                "poll_derived_lower_loss_count": 95,
                "tie_count": 0,
                "polymarket_better_share": 262 / 357,
                "mean_polymarket_brier": 0.179920350140056,
                "mean_poll_derived_brier": 0.2520477705719791,
                "mean_loss_advantage": 0.0721274204319231,
                "limitation": "Late repeated forecast rows.",
            },
        ]
    )


def _near_quality_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_id": "poll_derived",
                "source_label": "538 poll-derived",
                "row_count": 357,
                "state_count": 13,
                "mean_brier_loss": 0.2520477705719791,
                "expected_calibration_error": 0.439123917401707,
                "probability_separation": 0.43658917375930917,
                "limitation": "Repeated forecast rows.",
            },
            {
                "source_id": "polymarket",
                "source_label": "Polymarket",
                "row_count": 357,
                "state_count": 13,
                "mean_brier_loss": 0.179920350140056,
                "expected_calibration_error": 0.37974509803921574,
                "probability_separation": 0.45598656441010266,
                "limitation": "Repeated forecast rows.",
            },
        ]
    )


def _horizon_state_values() -> dict[str, float | int]:
    return {
        "state_count": 13,
        "mean_polymarket_brier": 0.179920350140056,
        "mean_poll_derived_brier": 0.2520477705719791,
        "mean_loss_advantage": 0.0721274204319231,
        "polymarket_mean_support_state_count": 8,
        "polymarket_majority_support_state_count": 8,
        "poll_derived_or_no_polymarket_support_state_count": 5,
    }


def _final_snapshot_values() -> dict[str, float | int]:
    return {
        "case_count": 8,
        "polymarket_lower_loss_count": 5,
        "traditional_lower_loss_count": 3,
        "tie_count": 0,
        "mean_polymarket_brier": 0.07837715625,
        "mean_traditional_brier": 0.09327890625,
    }


def _state_poll_values() -> dict[str, float | int]:
    return {
        "case_count": 13,
        "polymarket_lower_loss_count": 8,
        "poll_derived_lower_loss_count": 5,
        "tie_count": 0,
        "mean_polymarket_brier": 0.13355132692307695,
        "mean_poll_derived_brier": 0.17635906875132107,
    }


def _popular_vote_values() -> dict[str, float | int]:
    return {
        "case_count": 51,
        "polymarket_lower_loss_count": 21,
        "poll_derived_lower_loss_count": 30,
        "tie_count": 0,
        "mean_polymarket_brier": 0.5178593137254902,
        "mean_poll_derived_brier": 0.48244035524337675,
    }


def _rieke_values() -> dict[str, float | int]:
    return {
        "case_count": 50,
        "polymarket_lower_loss_count": 12,
        "rieke_lower_loss_count": 38,
        "tie_count": 0,
        "mean_polymarket_brier": 0.026207745,
        "mean_rieke_brier": 0.0295807872,
    }


def _two_seventy_values() -> dict[str, float | int]:
    return {
        "case_count": 50,
        "polymarket_lower_loss_count": 9,
        "two_seventy_lower_loss_count": 40,
        "tie_count": 1,
        "mean_polymarket_brier": 0.026207745,
        "mean_two_seventy_brier": 0.03059892,
    }


def _two_seventy_poll_average_values() -> dict[str, float | int]:
    return {
        "case_count": 43,
        "polymarket_lower_loss_count": 14,
        "poll_derived_lower_loss_count": 29,
        "tie_count": 0,
        "mean_polymarket_brier": 0.03044131976744186,
        "mean_poll_derived_brier": 0.0415955678144349,
    }


def _state_source_consensus_values() -> dict[str, float | int]:
    return {
        "source_state_case_count": 156,
        "source_count": 4,
        "state_count": 50,
        "all_source_polymarket_lower_loss_count": 43,
        "all_source_comparator_lower_loss_count": 112,
        "all_source_tie_count": 1,
        "all_source_mean_polymarket_brier": 0.0416,
        "all_source_mean_comparator_brier": 0.0600,
        "all_source_mean_loss_advantage": 0.0184,
        "all_source_polymarket_majority_state_count": 9,
        "all_source_comparator_majority_state_count": 37,
        "all_source_tie_state_count": 4,
        "direct_poll_source_state_case_count": 56,
        "direct_poll_state_count": 43,
        "direct_poll_polymarket_lower_loss_count": 22,
        "direct_poll_comparator_lower_loss_count": 34,
        "direct_poll_polymarket_majority_state_count": 13,
        "direct_poll_comparator_majority_state_count": 29,
        "direct_poll_tie_state_count": 1,
        "direct_poll_two_source_state_count": 13,
        "direct_poll_two_source_polymarket_majority_state_count": 8,
        "direct_poll_two_source_comparator_majority_state_count": 4,
        "direct_poll_two_source_tie_state_count": 1,
        "broad_many_cases_claim_supported_now": 0,
    }


def _competitive_state_values() -> dict[str, float | int]:
    return {
        "case_count": 156,
        "state_count": 50,
        "all_low_distance_case_count": 52,
        "all_low_distance_polymarket_lower_loss_count": 35,
        "all_low_distance_comparator_lower_loss_count": 17,
        "all_low_distance_mean_loss_advantage": 0.028374,
        "all_high_distance_case_count": 40,
        "all_high_distance_polymarket_lower_loss_count": 0,
        "all_high_distance_comparator_lower_loss_count": 40,
        "direct_low_distance_case_count": 19,
        "direct_low_distance_polymarket_lower_loss_count": 18,
        "direct_low_distance_comparator_lower_loss_count": 1,
        "direct_low_distance_mean_loss_advantage": 0.056696,
        "direct_high_distance_case_count": 19,
        "direct_high_distance_polymarket_lower_loss_count": 0,
        "direct_high_distance_comparator_lower_loss_count": 19,
        "competitive_subset_supports_polymarket": 1,
        "safe_state_subset_contradicts_strong_claim": 1,
        "broad_many_cases_claim_supported_now": 0,
    }


def _panel_competitiveness_values() -> dict[str, float | int]:
    return {
        "panel_row_count": 1720,
        "panel_state_count": 15,
        "late_row_count": 357,
        "late_non_safe_row_count": 285,
        "late_non_safe_state_count": 9,
        "late_non_safe_polymarket_lower_loss_count": 262,
        "late_non_safe_poll_lower_loss_count": 23,
        "late_non_safe_mean_loss_advantage": 0.093272,
        "late_non_safe_mean_polymarket_brier": 0.191067,
        "late_non_safe_mean_poll_brier": 0.284338,
        "late_non_safe_polymarket_state_support_count": 9,
        "late_high_distance_row_count": 72,
        "late_high_distance_state_count": 5,
        "late_high_distance_polymarket_lower_loss_count": 0,
        "late_high_distance_poll_lower_loss_count": 72,
        "late_high_distance_mean_loss_advantage": -0.011568,
        "late_high_distance_mean_polymarket_brier": 0.015562,
        "late_high_distance_mean_poll_brier": 0.003994,
        "late_high_distance_polymarket_state_support_count": 0,
        "late_non_safe_supports_polymarket": 1,
        "late_high_distance_contradicts_strong_claim": 1,
        "broad_many_cases_claim_supported_now": 0,
    }


def _state_significance_values() -> dict[str, float | int]:
    return {
        "late_non_safe_state_count": 9,
        "late_non_safe_polymarket_majority_state_count": 9,
        "late_non_safe_polymarket_majority_share": 1.0,
        "late_non_safe_polymarket_exact_binomial_p_value_greater": 0.001953125,
        "late_non_safe_polymarket_exact_95_ci_low": 0.7168711644368863,
        "late_high_distance_state_count": 5,
        "late_high_distance_polymarket_majority_state_count": 0,
        "late_high_distance_poll_majority_state_count": 5,
        "late_high_distance_poll_exact_binomial_p_value_greater": 0.03125,
        "late_non_safe_state_level_supports_polymarket": 1,
        "late_high_distance_state_level_contradicts_strong_claim": 1,
        "broad_many_cases_claim_supported_now": 0,
    }


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
