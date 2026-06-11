"""Audit the current H1 Polymarket-vs-polls forecast-quality claim.

This module turns the existing deterministic H1 outputs into one claim ledger.
It does not recompute raw Brier rows. Instead it reads precomputed H1 summary
artifacts and makes the boundary explicit: where the current evidence supports
Polymarket, where it contradicts the strong claim, and whether the requested
many-cases conclusion is proven.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


SYNTHESIS_INPUT = RESULTS_DIR / "h1_forecast_quality_synthesis.csv"
HORIZON_CLAIM_INPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_claim_audit.csv"
HORIZON_STATE_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_horizon_state_support_summary.csv"
)
NEAR_QUALITY_INPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality_summary.csv"
FINAL_SNAPSHOT_INPUT = RESULTS_DIR / "h1_final_snapshot_summary.csv"
STATE_POLL_INPUT = RESULTS_DIR / "h1_state_poll_snapshot_summary.csv"
POPULAR_VOTE_INPUT = RESULTS_DIR / "h1_popular_vote_summary.csv"
RIEKE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_summary.csv"
TWO_SEVENTY_INPUT = RESULTS_DIR / "h1_270towin_state_forecast_summary.csv"
TWO_SEVENTY_POLL_AVERAGE_INPUT = RESULTS_DIR / "h1_270towin_poll_average_summary.csv"
STATE_SOURCE_CONSENSUS_INPUT = RESULTS_DIR / "h1_state_source_consensus_summary.csv"
COMPETITIVE_STATE_INPUT = RESULTS_DIR / "h1_competitive_state_diagnostic_summary.csv"
PANEL_COMPETITIVENESS_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_competitiveness_summary.csv"
)
STATE_SIGNIFICANCE_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_state_significance_summary.csv"
)

AUDIT_OUTPUT = RESULTS_DIR / "h1_claim_evidence_audit.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_claim_evidence_audit_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_claim_evidence_audit.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_claim_evidence_audit_metadata.json"

AUDIT_COLUMNS: tuple[str, ...] = (
    "audit_id",
    "audit_label",
    "source_artifact",
    "comparison_family",
    "comparison_unit",
    "comparison_count",
    "state_count",
    "polymarket_support_count",
    "comparator_support_count",
    "tie_count",
    "polymarket_support_share",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "secondary_metric_label",
    "polymarket_secondary_value",
    "comparator_secondary_value",
    "supports_polymarket",
    "contradicts_polymarket",
    "proves_broad_user_claim",
    "evidence_grade",
    "allowed_statement",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

PRIMARY_POLL_AUDIT_IDS: tuple[str, ...] = (
    "full_state_date_poll_panel",
    "late_90_day_state_date_rows",
    "late_90_day_state_level",
    "late_90_day_mean_brier",
    "late_90_day_fixed_bin_ece",
    "late_90_day_probability_separation",
    "final_538_snapshot_outcomes",
    "state_poll_snapshot_outcomes",
    "two_seventy_poll_average_state_outcomes",
    "direct_poll_two_source_state_consensus",
    "direct_poll_low_distance_competitive_cases",
    "late_non_safe_competitive_state_date_rows",
    "late_non_safe_state_significance",
    "late_high_distance_state_date_rows",
    "popular_vote_daily_rows",
)


@dataclass(frozen=True)
class H1ClaimEvidenceAuditResult:
    """Summary of generated H1 claim-audit artifacts."""

    audit_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    audit_row_count: int
    support_row_count: int
    contradiction_row_count: int
    broad_user_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "audit_path": str(self.audit_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "audit_row_count": self.audit_row_count,
            "support_row_count": self.support_row_count,
            "contradiction_row_count": self.contradiction_row_count,
            "broad_user_claim_proven": self.broad_user_claim_proven,
        }


def generate_h1_claim_evidence_audit_outputs(
    *,
    synthesis_input: Path = SYNTHESIS_INPUT,
    horizon_claim_input: Path = HORIZON_CLAIM_INPUT,
    horizon_state_input: Path = HORIZON_STATE_INPUT,
    near_quality_input: Path = NEAR_QUALITY_INPUT,
    final_snapshot_input: Path = FINAL_SNAPSHOT_INPUT,
    state_poll_input: Path = STATE_POLL_INPUT,
    popular_vote_input: Path = POPULAR_VOTE_INPUT,
    rieke_input: Path = RIEKE_INPUT,
    two_seventy_input: Path = TWO_SEVENTY_INPUT,
    two_seventy_poll_average_input: Path = TWO_SEVENTY_POLL_AVERAGE_INPUT,
    state_source_consensus_input: Path = STATE_SOURCE_CONSENSUS_INPUT,
    competitive_state_input: Path = COMPETITIVE_STATE_INPUT,
    panel_competitiveness_input: Path = PANEL_COMPETITIVENESS_INPUT,
    state_significance_input: Path = STATE_SIGNIFICANCE_INPUT,
    audit_output: Path = AUDIT_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1ClaimEvidenceAuditResult:
    """Generate H1 claim-audit CSV, summary, figure, and metadata."""

    inputs = {
        "synthesis": read_csv(synthesis_input),
        "horizon_claim": read_csv(horizon_claim_input),
        "horizon_state": read_summary(horizon_state_input),
        "near_quality": read_csv(near_quality_input),
        "final_snapshot": read_summary(final_snapshot_input),
        "state_poll": read_summary(state_poll_input),
        "popular_vote": read_summary(popular_vote_input),
        "rieke": read_summary(rieke_input),
        "two_seventy": read_summary(two_seventy_input),
        "two_seventy_poll_average": read_summary(two_seventy_poll_average_input),
        "state_source_consensus": read_summary(state_source_consensus_input),
        "competitive_state": read_summary(competitive_state_input),
        "panel_competitiveness": read_summary(panel_competitiveness_input),
        "state_significance": read_summary(state_significance_input),
    }
    audit = validate_audit_table(build_claim_audit_table(**inputs))
    summary = build_claim_audit_summary(audit)

    audit_output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(audit_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_claim_audit_figure(audit=audit, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        audit=audit,
        summary=summary,
        source_paths={
            "synthesis_input": synthesis_input,
            "horizon_claim_input": horizon_claim_input,
            "horizon_state_input": horizon_state_input,
            "near_quality_input": near_quality_input,
            "final_snapshot_input": final_snapshot_input,
            "state_poll_input": state_poll_input,
            "popular_vote_input": popular_vote_input,
            "rieke_input": rieke_input,
            "two_seventy_input": two_seventy_input,
            "two_seventy_poll_average_input": two_seventy_poll_average_input,
            "state_source_consensus_input": state_source_consensus_input,
            "competitive_state_input": competitive_state_input,
            "panel_competitiveness_input": panel_competitiveness_input,
            "state_significance_input": state_significance_input,
            "audit_output": audit_output,
            "summary_output": summary_output,
            "figure_output": figure_output,
        },
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1ClaimEvidenceAuditResult(
        audit_path=audit_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        audit_row_count=int(len(audit)),
        support_row_count=int(audit["supports_polymarket"].sum()),
        contradiction_row_count=int(audit["contradicts_polymarket"].sum()),
        broad_user_claim_proven=bool(audit["proves_broad_user_claim"].all()),
    )


def read_csv(path: Path) -> pd.DataFrame:
    """Read a required CSV artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 claim-audit input not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"H1 claim-audit input must not be empty: {path}")
    return frame


def read_summary(path: Path) -> pd.DataFrame:
    """Read a summary_id/value CSV artifact."""

    frame = read_csv(path)
    required = {"summary_id", "value"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 summary input missing columns: {missing}")
    return frame


def build_claim_audit_table(
    *,
    synthesis: pd.DataFrame,
    horizon_claim: pd.DataFrame,
    horizon_state: pd.DataFrame,
    near_quality: pd.DataFrame,
    final_snapshot: pd.DataFrame,
    state_poll: pd.DataFrame,
    popular_vote: pd.DataFrame,
    rieke: pd.DataFrame,
    two_seventy: pd.DataFrame,
    two_seventy_poll_average: pd.DataFrame,
    state_source_consensus: pd.DataFrame,
    competitive_state: pd.DataFrame,
    panel_competitiveness: pd.DataFrame,
    state_significance: pd.DataFrame,
) -> pd.DataFrame:
    """Build the H1 claim-audit table from deterministic H1 artifacts."""

    synthesis_rows = int(len(synthesis))
    aggregate_support = int(synthesis["aggregate_mean_supports_polymarket"].sum())
    majority_support = int(synthesis["majority_cases_supports_polymarket"].sum())
    broad_support = int(synthesis["broad_many_cases_claim_supported"].sum())
    full_panel = _audit_row(horizon_claim, "full_panel")
    late_panel = _audit_row(horizon_claim, "within_90_days_before_election")
    near = near_quality.set_index("source_id")
    pm_near = near.loc["polymarket"]
    poll_near = near.loc["poll_derived"]

    rows = [
        _row(
            audit_id="synthesis_aggregate_rows",
            audit_label="All H1 comparator rows by aggregate mean Brier",
            source_artifact="h1_forecast_quality_synthesis.csv",
            comparison_family="cross_source_summary",
            comparison_unit="evidence_rows",
            comparison_count=synthesis_rows,
            state_count=0,
            pm_count=aggregate_support,
            comp_count=synthesis_rows - aggregate_support,
            ties=0,
            mean_pm=_summary_value(
                panel_competitiveness,
                "late_non_safe_mean_polymarket_brier",
            ),
            mean_comp=_summary_value(
                panel_competitiveness,
                "late_non_safe_mean_poll_brier",
            ),
            advantage=None,
            secondary_label="majority-support evidence rows",
            pm_secondary=majority_support,
            comp_secondary=synthesis_rows - majority_support,
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="aggregate_support_but_not_broad_proof",
            allowed_statement=(
                "Most current H1 evidence rows support Polymarket by mean Brier, "
                "but the broad claim remains unproven."
            ),
            limitation=(
                f"Only {broad_support} of {synthesis_rows} evidence rows support "
                "the broad many-cases criterion."
            ),
        ),
        _panel_row(
            audit_id="full_state_date_poll_panel",
            audit_label="Full state-date poll panel",
            artifact="h1_state_poll_panel_horizon_claim_audit.csv",
            row=full_panel,
            supports=False,
            contradicts=True,
            evidence_grade="contradicts_strong_polymarket_claim",
            allowed_statement=(
                "The largest poll-derived panel contradicts a broad Polymarket "
                "advantage claim."
            ),
        ),
        _panel_row(
            audit_id="late_90_day_state_date_rows",
            audit_label="<=90-day state-date poll panel",
            artifact="h1_state_poll_panel_horizon_claim_audit.csv",
            row=late_panel,
            supports=True,
            contradicts=False,
            evidence_grade="supports_polymarket_late_window",
            allowed_statement=(
                "In the final 90 days, Polymarket has lower loss in most "
                "state-date rows and lower mean Brier."
            ),
        ),
        _row(
            audit_id="late_90_day_state_level",
            audit_label="<=90-day state-level support",
            source_artifact="h1_state_poll_panel_horizon_state_support_summary.csv",
            comparison_family="poll_transform_late_window",
            comparison_unit="states",
            comparison_count=int(_summary_value(horizon_state, "state_count")),
            state_count=int(_summary_value(horizon_state, "state_count")),
            pm_count=int(
                _summary_value(horizon_state, "polymarket_mean_support_state_count")
            ),
            comp_count=int(
                _summary_value(
                    horizon_state,
                    "poll_derived_or_no_polymarket_support_state_count",
                )
            ),
            ties=0,
            mean_pm=_summary_value(horizon_state, "mean_polymarket_brier"),
            mean_comp=_summary_value(horizon_state, "mean_poll_derived_brier"),
            advantage=_summary_value(horizon_state, "mean_loss_advantage"),
            secondary_label="state row-majority support count",
            pm_secondary=_summary_value(
                horizon_state,
                "polymarket_majority_support_state_count",
            ),
            comp_secondary=_summary_value(
                horizon_state,
                "poll_derived_or_no_polymarket_support_state_count",
            ),
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="supports_polymarket_late_window_state_level",
            allowed_statement=(
                "The <=90-day diagnostic supports Polymarket in 8 of 13 states."
            ),
            limitation="All states still belong to one presidential election context.",
        ),
        _quality_row(
            audit_id="late_90_day_mean_brier",
            audit_label="<=90-day score quality: mean Brier",
            metric="mean_brier_loss",
            pm=pm_near,
            comp=poll_near,
            lower_is_better=True,
            evidence_grade="supports_polymarket_late_window_score_quality",
            allowed_statement="Polymarket has lower mean Brier in the <=90-day window.",
        ),
        _quality_row(
            audit_id="late_90_day_fixed_bin_ece",
            audit_label="<=90-day score quality: fixed-bin ECE",
            metric="expected_calibration_error",
            pm=pm_near,
            comp=poll_near,
            lower_is_better=True,
            evidence_grade="supports_polymarket_late_window_score_quality",
            allowed_statement="Polymarket has lower fixed-bin ECE in the <=90-day window.",
        ),
        _quality_row(
            audit_id="late_90_day_probability_separation",
            audit_label="<=90-day score quality: probability separation",
            metric="probability_separation",
            pm=pm_near,
            comp=poll_near,
            lower_is_better=False,
            evidence_grade="supports_polymarket_late_window_score_quality",
            allowed_statement=(
                "Polymarket has slightly higher probability separation in the "
                "<=90-day window."
            ),
        ),
        _summary_comparison_row(
            audit_id="final_538_snapshot_outcomes",
            audit_label="Final 538 snapshot outcomes",
            artifact="h1_final_snapshot_summary.csv",
            comparison_family="traditional_probability_snapshot",
            unit="resolved_outcomes",
            summary=final_snapshot,
            pm_key="polymarket_lower_loss_count",
            comp_key="traditional_lower_loss_count",
            mean_comp_key="mean_traditional_brier",
            supports=True,
            contradicts=False,
            evidence_grade="small_outcome_set_support",
            allowed_statement="Polymarket is lower-loss in 5 of 8 final 538 outcomes.",
            limitation="Small same-election final-snapshot extension.",
        ),
        _summary_comparison_row(
            audit_id="state_poll_snapshot_outcomes",
            audit_label="State poll snapshot outcomes",
            artifact="h1_state_poll_snapshot_summary.csv",
            comparison_family="poll_transform_snapshot",
            unit="resolved_state_outcomes",
            summary=state_poll,
            pm_key="polymarket_lower_loss_count",
            comp_key="poll_derived_lower_loss_count",
            mean_comp_key="mean_poll_derived_brier",
            supports=True,
            contradicts=False,
            evidence_grade="small_state_snapshot_support",
            allowed_statement=(
                "Polymarket is lower-loss in 8 of 13 transformed state-poll "
                "snapshot cases."
            ),
            limitation=(
                "Transformed polling-average margin, not raw poll shares or an "
                "official 538 state win forecast."
            ),
        ),
        _summary_comparison_row(
            audit_id="popular_vote_daily_rows",
            audit_label="Popular-vote daily poll transform",
            artifact="h1_popular_vote_summary.csv",
            comparison_family="poll_transform_popular_vote",
            unit="daily_forecast_rows",
            summary=popular_vote,
            pm_key="polymarket_lower_loss_count",
            comp_key="poll_derived_lower_loss_count",
            mean_comp_key="mean_poll_derived_brier",
            supports=False,
            contradicts=True,
            evidence_grade="popular_vote_counterexample",
            allowed_statement=(
                "For the 2024 popular-vote outcome, the transformed 538 poll "
                "margin has lower mean Brier and more lower-loss daily rows."
            ),
            limitation=(
                "Repeated daily rows for one resolved popular-vote outcome; "
                "poll-margin transform is model-dependent."
            ),
        ),
        _summary_comparison_row(
            audit_id="two_seventy_poll_average_state_outcomes",
            audit_label="270toWin state polling-average transform",
            artifact="h1_270towin_poll_average_summary.csv",
            comparison_family="poll_transform_state_snapshot",
            unit="resolved_state_outcomes",
            summary=two_seventy_poll_average,
            pm_key="polymarket_lower_loss_count",
            comp_key="poll_derived_lower_loss_count",
            mean_comp_key="mean_poll_derived_brier",
            supports=True,
            contradicts=False,
            evidence_grade="aggregate_support_case_majority_negative",
            allowed_statement=(
                "Polymarket has lower aggregate mean Brier, but the transformed "
                "270toWin polling average wins most state-level cases."
            ),
            limitation=(
                "Transformed 270toWin polling-average margin, not raw poll "
                "shares or an official win forecast; poll-derived wins 29 of "
                "43 state cases."
            ),
        ),
        _summary_comparison_row(
            audit_id="rieke_50_state_mean_brier",
            audit_label="Rieke 50-state model: mean Brier",
            artifact="h1_rieke_state_forecast_summary.csv",
            comparison_family="poll_model_state_forecast",
            unit="resolved_state_outcomes",
            summary=rieke,
            pm_key="polymarket_lower_loss_count",
            comp_key="rieke_lower_loss_count",
            mean_comp_key="mean_rieke_brier",
            supports=True,
            contradicts=False,
            evidence_grade="aggregate_support_case_majority_negative",
            allowed_statement=(
                "Polymarket has lower aggregate mean Brier, but Rieke wins most "
                "state-level cases."
            ),
            limitation="Rieke is a model forecast and wins 38 of 50 state cases.",
        ),
        _summary_comparison_row(
            audit_id="two_seventy_50_state_mean_brier",
            audit_label="270toWin/JHK 50-state model: mean Brier",
            artifact="h1_270towin_state_forecast_summary.csv",
            comparison_family="poll_model_state_forecast",
            unit="resolved_state_outcomes",
            summary=two_seventy,
            pm_key="polymarket_lower_loss_count",
            comp_key="two_seventy_lower_loss_count",
            mean_comp_key="mean_two_seventy_brier",
            supports=True,
            contradicts=False,
            evidence_grade="aggregate_support_case_majority_negative",
            allowed_statement=(
                "Polymarket has lower aggregate mean Brier, but 270toWin/JHK "
                "wins most state-level cases."
            ),
            limitation=(
                "Includes censored safe-state boundary probabilities and 40 of "
                "50 lower-loss cases for 270toWin/JHK."
            ),
        ),
        _row(
            audit_id="all_source_state_consensus",
            audit_label="All-source state consensus",
            source_artifact="h1_state_source_consensus_summary.csv",
            comparison_family="cross_source_state_consensus",
            comparison_unit="states",
            comparison_count=int(_summary_value(state_source_consensus, "state_count")),
            state_count=int(_summary_value(state_source_consensus, "state_count")),
            pm_count=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_polymarket_majority_state_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_comparator_majority_state_count",
                )
            ),
            ties=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_tie_state_count",
                )
            ),
            mean_pm=_summary_value(
                state_source_consensus,
                "all_source_mean_polymarket_brier",
            ),
            mean_comp=_summary_value(
                state_source_consensus,
                "all_source_mean_comparator_brier",
            ),
            advantage=_summary_value(
                state_source_consensus,
                "all_source_mean_loss_advantage",
            ),
            secondary_label="source-state lower-loss rows",
            pm_secondary=_summary_value(
                state_source_consensus,
                "all_source_polymarket_lower_loss_count",
            ),
            comp_secondary=_summary_value(
                state_source_consensus,
                "all_source_comparator_lower_loss_count",
            ),
            supports=False,
            contradicts=True,
            broad=False,
            evidence_grade="cross_source_state_consensus_counterexample",
            allowed_statement=(
                "Across four state-level source comparisons, the state-level "
                "majority consensus favours comparators in most states."
            ),
            limitation=(
                "This reuses existing state artifacts; source outputs are not "
                "independent elections and may share polling information."
            ),
        ),
        _row(
            audit_id="direct_poll_two_source_state_consensus",
            audit_label="Two direct poll-transform source consensus",
            source_artifact="h1_state_source_consensus_summary.csv",
            comparison_family="direct_poll_transform_state_consensus",
            comparison_unit="states",
            comparison_count=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_two_source_state_count",
                )
            ),
            state_count=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_two_source_state_count",
                )
            ),
            pm_count=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_two_source_polymarket_majority_state_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_two_source_comparator_majority_state_count",
                )
            ),
            ties=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_two_source_tie_state_count",
                )
            ),
            mean_pm=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_polymarket_brier",
            ),
            mean_comp=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_poll_brier",
            ),
            advantage=None,
            secondary_label="source-state lower-loss rows",
            pm_secondary=_summary_value(
                state_source_consensus,
                "direct_poll_polymarket_lower_loss_count",
            ),
            comp_secondary=_summary_value(
                state_source_consensus,
                "direct_poll_comparator_lower_loss_count",
            ),
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="direct_poll_consensus_support_bounded",
            allowed_statement=(
                "Among states covered by both direct poll-transform sources, "
                "Polymarket has the state-level consensus in 8 of 13 states."
            ),
            limitation=(
                "The two direct poll-transform sources cover one election and "
                "both require documented margin-to-probability assumptions."
            ),
        ),
        _row(
            audit_id="low_distance_competitive_cases",
            audit_label="Lowest-distance competitive state-source cases",
            source_artifact="h1_competitive_state_diagnostic_summary.csv",
            comparison_family="competitive_state_source_diagnostic",
            comparison_unit="source_state_cases",
            comparison_count=int(
                _summary_value(competitive_state, "all_low_distance_case_count")
            ),
            state_count=0,
            pm_count=int(
                _summary_value(
                    competitive_state,
                    "all_low_distance_polymarket_lower_loss_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    competitive_state,
                    "all_low_distance_comparator_lower_loss_count",
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=_summary_value(
                competitive_state,
                "all_low_distance_mean_loss_advantage",
            ),
            secondary_label="quantile-derived competitiveness subset",
            pm_secondary=_summary_value(
                competitive_state,
                "all_low_distance_polymarket_lower_loss_count",
            ),
            comp_secondary=_summary_value(
                competitive_state,
                "all_low_distance_comparator_lower_loss_count",
            ),
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="competitive_subset_support_bounded",
            allowed_statement=(
                "In the lowest comparator-distance tercile, Polymarket has "
                "lower loss in most source-state cases."
            ),
            limitation=(
                "Competitiveness tiers are diagnostic quantiles from one "
                "election context, not independent elections."
            ),
        ),
        _row(
            audit_id="direct_poll_low_distance_competitive_cases",
            audit_label="Direct-poll lowest-distance competitive cases",
            source_artifact="h1_competitive_state_diagnostic_summary.csv",
            comparison_family="direct_poll_competitive_state_diagnostic",
            comparison_unit="source_state_cases",
            comparison_count=int(
                _summary_value(competitive_state, "direct_low_distance_case_count")
            ),
            state_count=0,
            pm_count=int(
                _summary_value(
                    competitive_state,
                    "direct_low_distance_polymarket_lower_loss_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    competitive_state,
                    "direct_low_distance_comparator_lower_loss_count",
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=_summary_value(
                competitive_state,
                "direct_low_distance_mean_loss_advantage",
            ),
            secondary_label="direct poll-transform competitive subset",
            pm_secondary=_summary_value(
                competitive_state,
                "direct_low_distance_polymarket_lower_loss_count",
            ),
            comp_secondary=_summary_value(
                competitive_state,
                "direct_low_distance_comparator_lower_loss_count",
            ),
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="direct_poll_competitive_subset_support_bounded",
            allowed_statement=(
                "In direct poll-transform cases closest to 0.5, Polymarket has "
                "lower loss in 18 of 19 source-state cases."
            ),
            limitation=(
                "This is a quantile subset of transformed polling margins and "
                "does not establish a broad all-state claim."
            ),
        ),
        _row(
            audit_id="high_distance_safe_cases",
            audit_label="Highest-distance safer state-source cases",
            source_artifact="h1_competitive_state_diagnostic_summary.csv",
            comparison_family="competitive_state_source_diagnostic",
            comparison_unit="source_state_cases",
            comparison_count=int(
                _summary_value(competitive_state, "all_high_distance_case_count")
            ),
            state_count=0,
            pm_count=int(
                _summary_value(
                    competitive_state,
                    "all_high_distance_polymarket_lower_loss_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    competitive_state,
                    "all_high_distance_comparator_lower_loss_count",
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=None,
            secondary_label="quantile-derived safer-state subset",
            pm_secondary=_summary_value(
                competitive_state,
                "all_high_distance_polymarket_lower_loss_count",
            ),
            comp_secondary=_summary_value(
                competitive_state,
                "all_high_distance_comparator_lower_loss_count",
            ),
            supports=False,
            contradicts=True,
            broad=False,
            evidence_grade="safe_state_subset_counterexample",
            allowed_statement=(
                "In the highest comparator-distance tercile, traditional "
                "comparators have lower loss in all source-state cases."
            ),
            limitation=(
                "Safe-state Brier differences are often very small in absolute "
                "terms, but they block a broad all-state majority claim."
            ),
        ),
        _row(
            audit_id="late_non_safe_competitive_state_date_rows",
            audit_label="Late low/middle-distance state-date rows",
            source_artifact="h1_state_poll_panel_competitiveness_summary.csv",
            comparison_family="state_date_horizon_competitiveness",
            comparison_unit="state_date_forecast_rows",
            comparison_count=int(
                _summary_value(panel_competitiveness, "late_non_safe_row_count")
            ),
            state_count=int(
                _summary_value(panel_competitiveness, "late_non_safe_state_count")
            ),
            pm_count=int(
                _summary_value(
                    panel_competitiveness,
                    "late_non_safe_polymarket_lower_loss_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    panel_competitiveness,
                    "late_non_safe_poll_lower_loss_count",
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=_summary_value(
                panel_competitiveness,
                "late_non_safe_mean_loss_advantage",
            ),
            secondary_label="state majority support",
            pm_secondary=_summary_value(
                panel_competitiveness,
                "late_non_safe_polymarket_state_support_count",
            ),
            comp_secondary=(
                _summary_value(panel_competitiveness, "late_non_safe_state_count")
                - _summary_value(
                    panel_competitiveness,
                    "late_non_safe_polymarket_state_support_count",
                )
            ),
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="late_competitive_panel_support_bounded",
            allowed_statement=(
                "In the <=90-day low/middle poll-distance panel subset, "
                "Polymarket has lower loss in 262 of 285 state-date rows."
            ),
            limitation=(
                "Rows repeat resolved state outcomes and poll-derived probabilities "
                "are transformed from polling-average margins."
            ),
        ),
        _row(
            audit_id="late_non_safe_state_significance",
            audit_label="Late low/middle-distance state sign test",
            source_artifact="h1_state_poll_panel_state_significance_summary.csv",
            comparison_family="state_date_horizon_competitiveness",
            comparison_unit="states",
            comparison_count=int(
                _summary_value(state_significance, "late_non_safe_state_count")
            ),
            state_count=int(
                _summary_value(state_significance, "late_non_safe_state_count")
            ),
            pm_count=int(
                _summary_value(
                    state_significance,
                    "late_non_safe_polymarket_majority_state_count",
                )
            ),
            comp_count=(
                int(_summary_value(state_significance, "late_non_safe_state_count"))
                - int(
                    _summary_value(
                        state_significance,
                        "late_non_safe_polymarket_majority_state_count",
                    )
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=None,
            secondary_label="one-sided exact binomial p-value",
            pm_secondary=_summary_value(
                state_significance,
                "late_non_safe_polymarket_exact_binomial_p_value_greater",
            ),
            comp_secondary=None,
            supports=True,
            contradicts=False,
            broad=False,
            evidence_grade="late_competitive_state_sign_test_support",
            allowed_statement=(
                "Under a state-as-unit sign test, Polymarket has a lower-loss "
                "majority in 9 of 9 late low/middle-distance states."
            ),
            limitation=(
                "The exact binomial test is a bounded diagnostic; all states "
                "still come from one election context and are not independent "
                "elections."
            ),
        ),
        _row(
            audit_id="late_high_distance_state_date_rows",
            audit_label="Late high-distance state-date rows",
            source_artifact="h1_state_poll_panel_competitiveness_summary.csv",
            comparison_family="state_date_horizon_competitiveness",
            comparison_unit="state_date_forecast_rows",
            comparison_count=int(
                _summary_value(panel_competitiveness, "late_high_distance_row_count")
            ),
            state_count=int(
                _summary_value(panel_competitiveness, "late_high_distance_state_count")
            ),
            pm_count=int(
                _summary_value(
                    panel_competitiveness,
                    "late_high_distance_polymarket_lower_loss_count",
                )
            ),
            comp_count=int(
                _summary_value(
                    panel_competitiveness,
                    "late_high_distance_poll_lower_loss_count",
                )
            ),
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_loss_advantage",
            ),
            secondary_label="state majority support",
            pm_secondary=_summary_value(
                panel_competitiveness,
                "late_high_distance_polymarket_state_support_count",
            ),
            comp_secondary=(
                _summary_value(panel_competitiveness, "late_high_distance_state_count")
                - _summary_value(
                    panel_competitiveness,
                    "late_high_distance_polymarket_state_support_count",
                )
            ),
            supports=False,
            contradicts=True,
            broad=False,
            evidence_grade="late_high_distance_panel_counterexample",
            allowed_statement=(
                "In the <=90-day high poll-distance panel subset, poll-derived "
                "probabilities have lower loss in all 72 rows."
            ),
            limitation=(
                "This safer-state subset blocks a broad claim even though the "
                "late low/middle-distance subset supports Polymarket."
            ),
        ),
        _row(
            audit_id="completion_audit",
            audit_label="Completion audit for broad user claim",
            source_artifact="h1_claim_evidence_audit.csv",
            comparison_family="claim_boundary",
            comparison_unit="audit_rows",
            comparison_count=1,
            state_count=0,
            pm_count=0,
            comp_count=1,
            ties=0,
            mean_pm=None,
            mean_comp=None,
            advantage=None,
            secondary_label="broad claim proven flag",
            pm_secondary=0,
            comp_secondary=1,
            supports=False,
            contradicts=False,
            broad=False,
            evidence_grade="not_complete",
            allowed_statement=(
                "Current H1 evidence permits a bounded late-window support claim, "
                "not the requested broad many-cases conclusion."
            ),
            limitation=(
                "The largest poll-derived panel contradicts the strong claim and "
                "the positive windows still share one election context."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def validate_audit_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the claim-audit output contract."""

    missing = [column for column in AUDIT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 claim-audit table missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"H1 claim-audit table contains forbidden columns: {forbidden}")
    normalized = frame.loc[:, list(AUDIT_COLUMNS)].copy()
    for column in (
        "comparison_count",
        "state_count",
        "polymarket_support_count",
        "comparator_support_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_support_share",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
        "polymarket_secondary_value",
        "comparator_secondary_value",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    if (normalized["comparison_count"] <= 0).any():
        raise ValueError("H1 claim-audit comparison counts must be positive")
    if not normalized["polymarket_support_share"].between(0.0, 1.0).all():
        raise ValueError("H1 claim-audit support shares must be in [0, 1]")
    for column in (
        "supports_polymarket",
        "contradicts_polymarket",
        "proves_broad_user_claim",
    ):
        normalized[column] = normalized[column].astype(bool)
    broad_count = int(normalized["proves_broad_user_claim"].sum())
    if broad_count != 0:
        raise ValueError("Current H1 audit must not mark the broad user claim proven")
    return normalized


def build_claim_audit_summary(audit: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the H1 claim audit."""

    direct = audit.loc[audit["audit_id"].isin(PRIMARY_POLL_AUDIT_IDS)]
    rows: list[dict[str, Any]] = [
        _summary_row("audit_row_count", len(audit), "rows", "Total claim-audit rows."),
        _summary_row(
            "support_row_count",
            int(audit["supports_polymarket"].sum()),
            "rows",
            "Audit rows that support a bounded Polymarket advantage.",
        ),
        _summary_row(
            "contradiction_row_count",
            int(audit["contradicts_polymarket"].sum()),
            "rows",
            "Audit rows that contradict the strong Polymarket advantage claim.",
        ),
        _summary_row(
            "direct_poll_audit_row_count",
            len(direct),
            "rows",
            "Rows directly tied to polls, poll-derived probabilities, or 538 snapshots.",
        ),
        _summary_row(
            "direct_poll_support_row_count",
            int(direct["supports_polymarket"].sum()),
            "rows",
            "Direct poll-related audit rows that support Polymarket.",
        ),
        _summary_row(
            "direct_poll_contradiction_row_count",
            int(direct["contradicts_polymarket"].sum()),
            "rows",
            "Direct poll-related audit rows that contradict the strong claim.",
        ),
        _summary_row(
            "late_window_state_date_row_count",
            _audit_int(audit, "late_90_day_state_date_rows", "comparison_count"),
            "state-date rows",
            "State-date rows in the <=90-day poll-derived window.",
        ),
        _summary_row(
            "late_window_polymarket_lower_loss_count",
            _audit_int(
                audit,
                "late_90_day_state_date_rows",
                "polymarket_support_count",
            ),
            "state-date rows",
            "Rows in the <=90-day window where Polymarket has lower loss.",
        ),
        _summary_row(
            "late_window_poll_lower_loss_count",
            _audit_int(
                audit,
                "late_90_day_state_date_rows",
                "comparator_support_count",
            ),
            "state-date rows",
            "Rows in the <=90-day window where poll-derived probability has lower loss.",
        ),
        _summary_row(
            "full_panel_polymarket_lower_loss_count",
            _audit_int(audit, "full_state_date_poll_panel", "polymarket_support_count"),
            "state-date rows",
            "Rows in the full state-date panel where Polymarket has lower loss.",
        ),
        _summary_row(
            "full_panel_poll_lower_loss_count",
            _audit_int(audit, "full_state_date_poll_panel", "comparator_support_count"),
            "state-date rows",
            "Rows in the full state-date panel where poll-derived probability has lower loss.",
        ),
        _summary_row(
            "broad_user_claim_proven",
            0,
            "binary",
            "The requested broad many-cases conclusion is not proven.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Bounded late-window support exists, but the broad claim remains open.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_claim_audit_figure(
    *,
    audit: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a figure for the H1 claim audit."""

    plot_rows = audit.loc[
        audit["audit_id"].isin(
            [
                "full_state_date_poll_panel",
                "late_90_day_state_date_rows",
                "late_non_safe_competitive_state_date_rows",
                "late_non_safe_state_significance",
                "late_high_distance_state_date_rows",
                "late_90_day_state_level",
                "late_90_day_mean_brier",
                "late_90_day_fixed_bin_ece",
                "late_90_day_probability_separation",
                "final_538_snapshot_outcomes",
                "state_poll_snapshot_outcomes",
                "popular_vote_daily_rows",
                "rieke_50_state_mean_brier",
                "two_seventy_poll_average_state_outcomes",
                "two_seventy_50_state_mean_brier",
                "all_source_state_consensus",
                "direct_poll_two_source_state_consensus",
                "low_distance_competitive_cases",
                "direct_poll_low_distance_competitive_cases",
                "high_distance_safe_cases",
                "completion_audit",
            ]
        )
    ].copy()
    short_labels = [
        "Full\npanel",
        "<=90d\nrows",
        "<=90d\ncomp.",
        "<=90d\nsign",
        "<=90d\nsafe",
        "<=90d\nstates",
        "<=90d\nBrier",
        "<=90d\nECE",
        "<=90d\nsep.",
        "Final\n538",
        "State\npoll",
        "Popular\nvote",
        "Rieke\n50",
        "270 poll\n43",
        "270\nJHK",
        "All-src\nstates",
        "2 poll\nstates",
        "Comp.\nlow",
        "Poll\nlow",
        "Safe\nhigh",
        "Done\naudit",
    ]

    fig, axes = plt.subplots(2, 2, figsize=(19.2, 9.6))
    fig.suptitle(
        "H1 Claim Evidence Audit: Polymarket vs Poll-Based Comparators",
        fontsize=14,
        fontweight="bold",
    )

    x = range(len(plot_rows))
    colors = [
        "#2563eb" if value else "#9ca3af"
        for value in plot_rows["supports_polymarket"]
    ]
    colors = [
        "#dc2626" if contradicts else color
        for color, contradicts in zip(colors, plot_rows["contradicts_polymarket"])
    ]
    axes[0, 0].bar(short_labels, plot_rows["polymarket_support_share"], color=colors)
    axes[0, 0].axhline(0.5, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[0, 0].set_ylim(0, 1.08)
    axes[0, 0].set_title("Polymarket support share by audit scope")
    axes[0, 0].set_ylabel("Support share")
    axes[0, 0].tick_params(axis="x", labelsize=7.4)
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, row in enumerate(plot_rows.itertuples(index=False)):
        axes[0, 0].text(
            idx,
            float(row.polymarket_support_share) + 0.035,
            f"{int(row.polymarket_support_count)}/{int(row.comparison_count)}",
            ha="center",
            fontsize=7.3,
        )

    brier_rows = audit.loc[
        audit["audit_id"].isin(
            [
                "full_state_date_poll_panel",
                "late_90_day_state_date_rows",
                "late_non_safe_competitive_state_date_rows",
                "late_90_day_state_level",
                "final_538_snapshot_outcomes",
                "state_poll_snapshot_outcomes",
                "popular_vote_daily_rows",
                "rieke_50_state_mean_brier",
                "two_seventy_poll_average_state_outcomes",
                "two_seventy_50_state_mean_brier",
                "all_source_state_consensus",
                "low_distance_competitive_cases",
            ]
        )
    ].copy()
    brier_labels = [
        "Full\npanel",
        "<=90d\nrows",
        "<=90d\ncomp.",
        "<=90d\nstates",
        "Final\n538",
        "State\npoll",
        "Popular\nvote",
        "Rieke\n50",
        "270 poll\n43",
        "270\nJHK",
        "All-src\nstates",
        "Comp.\nlow",
    ]
    width = 0.36
    positions = list(range(len(brier_rows)))
    axes[0, 1].bar(
        [pos - width / 2 for pos in positions],
        brier_rows["mean_polymarket_brier"],
        width=width,
        color="#2563eb",
        label="Polymarket",
    )
    axes[0, 1].bar(
        [pos + width / 2 for pos in positions],
        brier_rows["mean_comparator_brier"],
        width=width,
        color="#7c3aed",
        label="Comparator",
    )
    axes[0, 1].set_xticks(positions, brier_labels)
    axes[0, 1].set_title("Mean Brier by comparable scope")
    axes[0, 1].set_ylabel("Mean Brier loss")
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, axis="y", alpha=0.25)

    status_values = plot_rows[
        ["supports_polymarket", "contradicts_polymarket", "proves_broad_user_claim"]
    ].astype(int)
    axes[1, 0].imshow(
        status_values.to_numpy().T,
        aspect="auto",
        cmap=ListedColormap(["#f3f4f6", "#bbf7d0"]),
        vmin=0,
        vmax=1,
    )
    axes[1, 0].set_xticks(list(x), short_labels)
    axes[1, 0].set_yticks(
        [0, 1, 2],
        ["Supports PM", "Contradicts\nstrong claim", "Broad claim\nproven"],
    )
    axes[1, 0].set_title("Claim-status ledger")
    axes[1, 0].tick_params(axis="x", labelsize=7.2)
    for col_idx in range(status_values.shape[0]):
        for row_idx in range(status_values.shape[1]):
            value = status_values.iloc[col_idx, row_idx]
            axes[1, 0].text(
                col_idx,
                row_idx,
                "yes" if value else "no",
                ha="center",
                va="center",
                fontsize=7.2,
            )

    support = int(_summary_value(summary, "support_row_count"))
    contradiction = int(_summary_value(summary, "contradiction_row_count"))
    remaining = int(_summary_value(summary, "audit_row_count")) - support - contradiction
    axes[1, 1].bar(
        ["Supports\nPM", "Contradicts\nstrong claim", "Limited /\ncompletion"],
        [support, contradiction, remaining],
        color=["#2563eb", "#dc2626", "#9ca3af"],
    )
    axes[1, 1].set_title("Audit-row count summary")
    axes[1, 1].set_ylabel("Rows")
    axes[1, 1].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate([support, contradiction, remaining]):
        axes[1, 1].text(idx, value + 0.12, str(value), ha="center", fontsize=9)

    fig.text(
        0.5,
        0.018,
        (
            "Current evidence supports Polymarket in the late <=90-day window, "
            "but the full state-date panel, popular-vote extension, and completion "
            "audit block a broad many-cases conclusion.\n"
            "All-source state consensus also favours traditional comparators in "
            "most states. The competitive "
            "lowest-distance subset is a bounded Polymarket-supporting exception."
        ),
        ha="center",
        fontsize=8.4,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    audit: pd.DataFrame,
    summary: pd.DataFrame,
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    """Build metadata for the H1 claim audit."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_claim_evidence_audit",
            "calculation_scope": "deterministic_python_from_precomputed_h1_artifacts",
            "does_not_recompute_raw_brier_rows": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "audit_row_count": int(len(audit)),
            "support_row_count": int(audit["supports_polymarket"].sum()),
            "contradiction_row_count": int(audit["contradicts_polymarket"].sum()),
            "broad_user_claim_proven": False,
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "limitations": {
            "full_state_date_panel_contradicts_strong_claim": True,
            "popular_vote_extension_contradicts_strong_claim": True,
            "late_window_support_is_repeated_forecast_rows": True,
            "state_rows_share_one_election_context": True,
            "model_forecasts_are_not_raw_polls": True,
            "two_seventy_poll_average_is_poll_transform": True,
            "competitive_subset_supports_polymarket_bounded": True,
            "safe_state_subset_contradicts_strong_claim": True,
            "late_non_safe_state_date_supports_polymarket_bounded": True,
            "late_non_safe_state_sign_test_supports_polymarket": True,
            "late_high_distance_state_date_contradicts_strong_claim": True,
            "broad_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _panel_row(
    *,
    audit_id: str,
    audit_label: str,
    artifact: str,
    row: pd.Series,
    supports: bool,
    contradicts: bool,
    evidence_grade: str,
    allowed_statement: str,
) -> dict[str, Any]:
    return _row(
        audit_id=audit_id,
        audit_label=audit_label,
        source_artifact=artifact,
        comparison_family="poll_transform_state_date_panel",
        comparison_unit="state_date_rows",
        comparison_count=int(row["row_count"]),
        state_count=int(row["state_count"]),
        pm_count=int(row["polymarket_lower_loss_count"]),
        comp_count=int(row["poll_derived_lower_loss_count"]),
        ties=int(row["tie_count"]),
        mean_pm=float(row["mean_polymarket_brier"]),
        mean_comp=float(row["mean_poll_derived_brier"]),
        advantage=float(row["mean_loss_advantage"]),
        secondary_label="polymarket lower-loss share",
        pm_secondary=float(row["polymarket_better_share"]),
        comp_secondary=1.0 - float(row["polymarket_better_share"]),
        supports=supports,
        contradicts=contradicts,
        broad=False,
        evidence_grade=evidence_grade,
        allowed_statement=allowed_statement,
        limitation=str(row["limitation"]),
    )


def _quality_row(
    *,
    audit_id: str,
    audit_label: str,
    metric: str,
    pm: pd.Series,
    comp: pd.Series,
    lower_is_better: bool,
    evidence_grade: str,
    allowed_statement: str,
) -> dict[str, Any]:
    pm_value = float(pm[metric])
    comp_value = float(comp[metric])
    supports = pm_value < comp_value if lower_is_better else pm_value > comp_value
    return _row(
        audit_id=audit_id,
        audit_label=audit_label,
        source_artifact="h1_state_poll_panel_near_window_quality_summary.csv",
        comparison_family="poll_transform_late_window_score_quality",
        comparison_unit="forecast_source_metric",
        comparison_count=1,
        state_count=int(pm["state_count"]),
        pm_count=1 if supports else 0,
        comp_count=0 if supports else 1,
        ties=0,
        mean_pm=None,
        mean_comp=None,
        advantage=None,
        secondary_label=metric,
        pm_secondary=pm_value,
        comp_secondary=comp_value,
        supports=supports,
        contradicts=not supports,
        broad=False,
        evidence_grade=evidence_grade if supports else "score_quality_contradiction",
        allowed_statement=allowed_statement,
        limitation=str(pm["limitation"]),
    )


def _summary_comparison_row(
    *,
    audit_id: str,
    audit_label: str,
    artifact: str,
    comparison_family: str,
    unit: str,
    summary: pd.DataFrame,
    pm_key: str,
    comp_key: str,
    mean_comp_key: str,
    supports: bool,
    contradicts: bool,
    evidence_grade: str,
    allowed_statement: str,
    limitation: str,
) -> dict[str, Any]:
    case_count = int(_summary_value(summary, "case_count"))
    pm_count = int(_summary_value(summary, pm_key))
    comp_count = int(_summary_value(summary, comp_key))
    ties = int(_summary_value(summary, "tie_count", default=0.0))
    mean_pm = _summary_value(summary, "mean_polymarket_brier")
    mean_comp = _summary_value(summary, mean_comp_key)
    return _row(
        audit_id=audit_id,
        audit_label=audit_label,
        source_artifact=artifact,
        comparison_family=comparison_family,
        comparison_unit=unit,
        comparison_count=case_count,
        state_count=case_count if "state" in unit else 0,
        pm_count=pm_count,
        comp_count=comp_count,
        ties=ties,
        mean_pm=mean_pm,
        mean_comp=mean_comp,
        advantage=mean_comp - mean_pm,
        secondary_label="case lower-loss counts",
        pm_secondary=pm_count,
        comp_secondary=comp_count,
        supports=supports,
        contradicts=contradicts,
        broad=False,
        evidence_grade=evidence_grade,
        allowed_statement=allowed_statement,
        limitation=limitation,
    )


def _row(
    *,
    audit_id: str,
    audit_label: str,
    source_artifact: str,
    comparison_family: str,
    comparison_unit: str,
    comparison_count: int,
    state_count: int,
    pm_count: int,
    comp_count: int,
    ties: int,
    mean_pm: float | None,
    mean_comp: float | None,
    advantage: float | None,
    secondary_label: str,
    pm_secondary: float | int | None,
    comp_secondary: float | int | None,
    supports: bool,
    contradicts: bool,
    broad: bool,
    evidence_grade: str,
    allowed_statement: str,
    limitation: str,
) -> dict[str, Any]:
    if comparison_count <= 0:
        raise ValueError("comparison_count must be positive")
    return {
        "audit_id": audit_id,
        "audit_label": audit_label,
        "source_artifact": source_artifact,
        "comparison_family": comparison_family,
        "comparison_unit": comparison_unit,
        "comparison_count": comparison_count,
        "state_count": state_count,
        "polymarket_support_count": pm_count,
        "comparator_support_count": comp_count,
        "tie_count": ties,
        "polymarket_support_share": pm_count / comparison_count,
        "mean_polymarket_brier": mean_pm,
        "mean_comparator_brier": mean_comp,
        "mean_loss_advantage": advantage,
        "secondary_metric_label": secondary_label,
        "polymarket_secondary_value": pm_secondary,
        "comparator_secondary_value": comp_secondary,
        "supports_polymarket": supports,
        "contradicts_polymarket": contradicts,
        "proves_broad_user_claim": broad,
        "evidence_grade": evidence_grade,
        "allowed_statement": allowed_statement,
        "limitation": limitation,
    }


def _audit_row(frame: pd.DataFrame, audit_scope: str) -> pd.Series:
    rows = frame.loc[frame["audit_scope"] == audit_scope]
    if len(rows) != 1:
        raise ValueError(f"H1 horizon audit must contain one {audit_scope!r} row")
    return rows.iloc[0]


def _audit_int(audit: pd.DataFrame, audit_id: str, column: str) -> int:
    rows = audit.loc[audit["audit_id"] == audit_id, column]
    if len(rows) != 1:
        raise ValueError(f"H1 claim audit must contain one {audit_id!r} row")
    return int(rows.iloc[0])


def _summary_row(
    summary_id: str,
    value: int | float | str,
    unit: str,
    description: str,
) -> dict[str, Any]:
    return {
        "summary_id": summary_id,
        "value": value,
        "unit": unit,
        "description": description,
    }


def _summary_value(
    frame: pd.DataFrame,
    summary_id: str,
    *,
    default: float | None = None,
) -> float:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        if default is not None:
            return default
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesis-input", type=Path, default=SYNTHESIS_INPUT)
    parser.add_argument("--horizon-claim-input", type=Path, default=HORIZON_CLAIM_INPUT)
    parser.add_argument("--horizon-state-input", type=Path, default=HORIZON_STATE_INPUT)
    parser.add_argument("--near-quality-input", type=Path, default=NEAR_QUALITY_INPUT)
    parser.add_argument("--final-snapshot-input", type=Path, default=FINAL_SNAPSHOT_INPUT)
    parser.add_argument("--state-poll-input", type=Path, default=STATE_POLL_INPUT)
    parser.add_argument("--popular-vote-input", type=Path, default=POPULAR_VOTE_INPUT)
    parser.add_argument("--rieke-input", type=Path, default=RIEKE_INPUT)
    parser.add_argument("--two-seventy-input", type=Path, default=TWO_SEVENTY_INPUT)
    parser.add_argument(
        "--two-seventy-poll-average-input",
        type=Path,
        default=TWO_SEVENTY_POLL_AVERAGE_INPUT,
    )
    parser.add_argument(
        "--state-source-consensus-input",
        type=Path,
        default=STATE_SOURCE_CONSENSUS_INPUT,
    )
    parser.add_argument(
        "--competitive-state-input",
        type=Path,
        default=COMPETITIVE_STATE_INPUT,
    )
    parser.add_argument(
        "--panel-competitiveness-input",
        type=Path,
        default=PANEL_COMPETITIVENESS_INPUT,
    )
    parser.add_argument(
        "--state-significance-input",
        type=Path,
        default=STATE_SIGNIFICANCE_INPUT,
    )
    parser.add_argument("--audit-output", type=Path, default=AUDIT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_claim_evidence_audit_outputs(
            synthesis_input=args.synthesis_input,
            horizon_claim_input=args.horizon_claim_input,
            horizon_state_input=args.horizon_state_input,
            near_quality_input=args.near_quality_input,
            final_snapshot_input=args.final_snapshot_input,
            state_poll_input=args.state_poll_input,
            popular_vote_input=args.popular_vote_input,
            rieke_input=args.rieke_input,
            two_seventy_input=args.two_seventy_input,
            two_seventy_poll_average_input=args.two_seventy_poll_average_input,
            state_source_consensus_input=args.state_source_consensus_input,
            competitive_state_input=args.competitive_state_input,
            panel_competitiveness_input=args.panel_competitiveness_input,
            state_significance_input=args.state_significance_input,
            audit_output=args.audit_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
