"""Claim-readiness synthesis for H1 Polymarket-vs-poll comparisons.

This module turns existing deterministic H1 poll-comparison outputs into a
single claim-readiness table and figure. It does not recompute raw Brier rows,
collect data, query a database, or use LLMs. The purpose is to separate the
bounded H1 claim that is currently supported from broader claims that remain
contradicted or not proven.
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
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


POLL_RESULT_INPUT = RESULTS_DIR / "h1_poll_comparison_result_summary.csv"
UNIT_ROBUSTNESS_INPUT = RESULTS_DIR / "h1_poll_comparison_unit_robustness_summary.csv"
DIRECT_LOSS_INPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition_summary.csv"
DIRECT_STATE_INPUT = (
    RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_summary.csv"
)
OUTLIER_INPUT = RESULTS_DIR / "h1_direct_poll_outlier_robustness_summary.csv"
STATE_PANEL_INPUT = RESULTS_DIR / "h1_state_poll_panel_summary.csv"
POPULAR_VOTE_INPUT = RESULTS_DIR / "h1_popular_vote_summary.csv"
STATE_SIGNIFICANCE_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_state_significance_summary.csv"
)

CLAIM_OUTPUT = RESULTS_DIR / "h1_poll_claim_readiness.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_poll_claim_readiness_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_poll_claim_readiness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_poll_claim_readiness_metadata.json"

CLAIM_COLUMNS: tuple[str, ...] = (
    "claim_id",
    "claim_label",
    "claim_family",
    "comparison_scope",
    "comparison_unit",
    "comparison_count",
    "polymarket_support_count",
    "poll_support_count",
    "tie_count",
    "polymarket_support_share",
    "mean_loss_advantage",
    "exact_p_value",
    "exact_95_ci_low",
    "claim_status",
    "allowed_statement",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

FORBIDDEN_COLUMN_TOKENS: tuple[str, ...] = (
    "wallet",
    "maker",
    "taker",
    "address",
    "order_instruction",
)


@dataclass(frozen=True)
class H1PollClaimReadinessResult:
    """Summary of generated H1 poll-claim readiness artifacts."""

    claim_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    claim_row_count: int
    bounded_claim_supported: bool
    broad_claim_proven: bool
    primary_polymarket_support_share: float
    primary_state_month_p_value: float

    def to_dict(self) -> dict[str, bool | float | int | str]:
        return {
            "claim_path": str(self.claim_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "claim_row_count": self.claim_row_count,
            "bounded_claim_supported": self.bounded_claim_supported,
            "broad_claim_proven": self.broad_claim_proven,
            "primary_polymarket_support_share": self.primary_polymarket_support_share,
            "primary_state_month_p_value": self.primary_state_month_p_value,
        }


def generate_h1_poll_claim_readiness_outputs(
    *,
    poll_result_input: Path = POLL_RESULT_INPUT,
    unit_robustness_input: Path = UNIT_ROBUSTNESS_INPUT,
    direct_loss_input: Path = DIRECT_LOSS_INPUT,
    direct_state_input: Path = DIRECT_STATE_INPUT,
    outlier_input: Path = OUTLIER_INPUT,
    state_panel_input: Path = STATE_PANEL_INPUT,
    popular_vote_input: Path = POPULAR_VOTE_INPUT,
    state_significance_input: Path = STATE_SIGNIFICANCE_INPUT,
    claim_output: Path = CLAIM_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1PollClaimReadinessResult:
    """Generate H1 poll-claim readiness CSV, summary, figure, and metadata."""

    inputs = {
        "poll_result": read_summary(poll_result_input),
        "unit_robustness": read_summary(unit_robustness_input),
        "direct_loss": read_summary(direct_loss_input),
        "direct_state": read_summary(direct_state_input),
        "outlier": read_summary(outlier_input),
        "state_panel": read_summary(state_panel_input),
        "popular_vote": read_summary(popular_vote_input),
        "state_significance": read_summary(state_significance_input),
    }
    claims = validate_claim_table(build_claim_table(**inputs))
    summary = validate_summary_table(build_summary_table(claims=claims, **inputs))

    claim_output.parent.mkdir(parents=True, exist_ok=True)
    claims.to_csv(claim_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_claim_readiness_figure(claims=claims, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        claims=claims,
        summary=summary,
        source_paths={
            "poll_result_input": poll_result_input,
            "unit_robustness_input": unit_robustness_input,
            "direct_loss_input": direct_loss_input,
            "direct_state_input": direct_state_input,
            "outlier_input": outlier_input,
            "state_panel_input": state_panel_input,
            "popular_vote_input": popular_vote_input,
            "state_significance_input": state_significance_input,
            "claim_output": claim_output,
            "summary_output": summary_output,
            "figure_output": figure_output,
        },
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1PollClaimReadinessResult(
        claim_path=claim_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        claim_row_count=int(len(claims)),
        bounded_claim_supported=bool(
            _summary_value(summary, "bounded_poll_claim_supported")
        ),
        broad_claim_proven=bool(_summary_value(summary, "broad_claim_proven")),
        primary_polymarket_support_share=float(
            _summary_value(summary, "primary_polymarket_support_share")
        ),
        primary_state_month_p_value=float(
            _summary_value(summary, "primary_state_month_exact_p_value")
        ),
    )


def read_summary(path: Path) -> pd.DataFrame:
    """Read a non-empty summary_id/value CSV artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 poll-claim input not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"H1 poll-claim input must not be empty: {path}")
    _reject_forbidden_columns(frame, "H1 poll-claim input")
    missing = sorted({"summary_id", "value"} - set(frame.columns))
    if missing:
        raise ValueError(f"H1 poll-claim summary missing columns: {missing}")
    return frame


def build_claim_table(
    *,
    poll_result: pd.DataFrame,
    unit_robustness: pd.DataFrame,
    direct_loss: pd.DataFrame,
    direct_state: pd.DataFrame,
    outlier: pd.DataFrame,
    state_panel: pd.DataFrame,
    popular_vote: pd.DataFrame,
    state_significance: pd.DataFrame,
) -> pd.DataFrame:
    """Build claim-readiness rows from existing H1 summaries."""

    rows = [
        _claim_row(
            claim_id="bounded_primary_state_date_rows",
            claim_label="Bounded <=90d low/middle poll-distance rows",
            claim_family="supported_bounded_scope",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="state_date_rows",
            comparison_count=_iv(poll_result, "primary_comparison_count"),
            polymarket_support_count=_iv(
                poll_result,
                "primary_polymarket_support_count",
            ),
            poll_support_count=_iv(poll_result, "primary_poll_support_count"),
            tie_count=0,
            mean_loss_advantage=_fv(poll_result, "primary_mean_loss_advantage"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="supported",
            allowed_statement=(
                "In the bounded <=90-day low/middle poll-distance scope, "
                "Polymarket has lower Brier loss in most state-date rows."
            ),
            limitation=(
                "State-date rows repeat one election context and do not prove a "
                "broad many-election claim."
            ),
        ),
        _claim_row(
            claim_id="bounded_primary_state_units",
            claim_label="Bounded <=90d low/middle poll-distance states",
            claim_family="supported_bounded_scope",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="states",
            comparison_count=_iv(poll_result, "primary_state_count"),
            polymarket_support_count=_iv(poll_result, "primary_polymarket_state_count"),
            poll_support_count=0,
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=_fv(poll_result, "primary_exact_binomial_p_value"),
            exact_95_ci_low=_fv(poll_result, "primary_exact_95_ci_low"),
            claim_status="supported",
            allowed_statement=(
                "Every represented state in the bounded primary scope supports "
                "Polymarket by lower-loss majority."
            ),
            limitation="The units are states within one presidential election.",
        ),
        _claim_row(
            claim_id="bounded_primary_state_month_units",
            claim_label="Bounded <=90d low/middle state-month units",
            claim_family="supported_bounded_scope",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="state_month_units",
            comparison_count=_iv(unit_robustness, "primary_state_month_unit_count"),
            polymarket_support_count=_iv(
                unit_robustness,
                "primary_state_month_polymarket_support_count",
            ),
            poll_support_count=0,
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=_fv(
                unit_robustness,
                "primary_state_month_polymarket_exact_binomial_p_value_greater",
            ),
            exact_95_ci_low=_fv(
                unit_robustness,
                "primary_state_month_polymarket_exact_95_ci_low",
            ),
            claim_status="supported",
            allowed_statement=(
                "The strongest robust unit diagnostic supports Polymarket across "
                "all bounded primary state-month units."
            ),
            limitation=(
                "State-month units are robustness units, not independent elections."
            ),
        ),
        _claim_row(
            claim_id="bounded_primary_state_horizon_units",
            claim_label="Bounded <=90d low/middle state-horizon units",
            claim_family="supported_bounded_scope",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="state_horizon_units",
            comparison_count=_iv(unit_robustness, "primary_state_horizon_unit_count"),
            polymarket_support_count=_iv(
                unit_robustness,
                "primary_state_horizon_polymarket_support_count",
            ),
            poll_support_count=0,
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=_fv(
                unit_robustness,
                "primary_state_horizon_polymarket_exact_binomial_p_value_greater",
            ),
            exact_95_ci_low=_fv(
                unit_robustness,
                "primary_state_horizon_polymarket_exact_95_ci_low",
            ),
            claim_status="supported",
            allowed_statement=(
                "Polymarket is supported in all bounded primary state-horizon "
                "units."
            ),
            limitation="State-horizon units reuse the same election context.",
        ),
        _claim_row(
            claim_id="bounded_primary_horizon_tier_units",
            claim_label="Bounded <=90d low/middle horizon-tier units",
            claim_family="directional_bounded_scope",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="horizon_tier_units",
            comparison_count=_iv(unit_robustness, "primary_horizon_tier_unit_count"),
            polymarket_support_count=_iv(
                unit_robustness,
                "primary_horizon_tier_polymarket_support_count",
            ),
            poll_support_count=0,
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=_fv(
                unit_robustness,
                "primary_horizon_tier_polymarket_exact_binomial_p_value_greater",
            ),
            exact_95_ci_low=_fv(
                unit_robustness,
                "primary_horizon_tier_polymarket_exact_95_ci_low",
            ),
            claim_status="directional_support",
            allowed_statement=(
                "All horizon-tier units point toward Polymarket in the bounded "
                "primary scope."
            ),
            limitation=(
                "Only four horizon-tier units are available; exact p-value is "
                "above 0.05."
            ),
        ),
        _claim_row(
            claim_id="direct_poll_source_state_cases",
            claim_label="Direct poll-transform source-state cases",
            claim_family="mixed_mean_support",
            comparison_scope="direct_poll_transform",
            comparison_unit="source_state_cases",
            comparison_count=_iv(direct_loss, "direct_poll_case_count"),
            polymarket_support_count=_iv(
                direct_loss,
                "direct_poll_polymarket_lower_loss_count",
            ),
            poll_support_count=_iv(
                direct_loss,
                "direct_poll_comparator_lower_loss_count",
            ),
            tie_count=_iv(direct_loss, "direct_poll_tie_count"),
            mean_loss_advantage=_fv(direct_loss, "direct_poll_mean_loss_advantage"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="mean_supported_case_majority_not_supported",
            allowed_statement=(
                "Direct poll-transform cases have lower mean Brier for "
                "Polymarket."
            ),
            limitation=(
                "Poll-derived comparators win more individual source-state cases."
            ),
        ),
        _claim_row(
            claim_id="direct_poll_state_clusters",
            claim_label="Direct poll-transform state clusters",
            claim_family="mixed_mean_support",
            comparison_scope="direct_poll_transform_state_clusters",
            comparison_unit="states",
            comparison_count=_iv(direct_state, "state_count"),
            polymarket_support_count=_iv(
                direct_state,
                "state_mean_polymarket_support_count",
            ),
            poll_support_count=_iv(direct_state, "state_mean_poll_support_count"),
            tie_count=_iv(direct_state, "state_mean_tie_count"),
            mean_loss_advantage=_fv(direct_state, "equal_state_mean_loss_advantage"),
            exact_p_value=_fv(direct_state, "equal_state_sign_flip_p_value_greater"),
            exact_95_ci_low=_fv(direct_state, "equal_state_bootstrap_95_ci_low"),
            claim_status="mean_supported_state_majority_not_supported",
            allowed_statement=(
                "Equal-state mean loss advantage is positive for Polymarket."
            ),
            limitation=(
                "State-count majority supports poll-derived comparators."
            ),
        ),
        _claim_row(
            claim_id="direct_poll_outlier_robust_mean",
            claim_label="Direct poll outlier robustness mean",
            claim_family="mixed_mean_support",
            comparison_scope="direct_poll_outlier_robustness",
            comparison_unit="leave_one_state_out_scenarios",
            comparison_count=_iv(outlier, "leave_one_out_scenario_count"),
            polymarket_support_count=_iv(outlier, "leave_one_out_scenario_count"),
            poll_support_count=0,
            tie_count=0,
            mean_loss_advantage=_fv(outlier, "min_leave_one_out_mean_loss_advantage"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="mean_robust_to_single_state",
            allowed_statement=(
                "The positive direct poll state-cluster mean is not created by "
                "a single state."
            ),
            limitation=(
                "The advantage remains concentrated in the largest positive "
                "state contributions."
            ),
        ),
        _claim_row(
            claim_id="full_state_date_panel",
            claim_label="Full state-date poll panel",
            claim_family="counterexample",
            comparison_scope="full_state_date_poll_panel",
            comparison_unit="state_date_rows",
            comparison_count=_iv(state_panel, "matched_case_count"),
            polymarket_support_count=_iv(state_panel, "polymarket_lower_loss_count"),
            poll_support_count=_iv(state_panel, "poll_derived_lower_loss_count"),
            tie_count=_iv(state_panel, "tie_count"),
            mean_loss_advantage=_fv(state_panel, "mean_loss_advantage"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="contradicted",
            allowed_statement=(
                "The full repeated state-date panel contradicts a broad "
                "Polymarket-better claim."
            ),
            limitation=(
                "Full panel includes early periods and repeated state-date rows."
            ),
        ),
        _claim_row(
            claim_id="full_panel_state_month_units",
            claim_label="Full panel state-month units",
            claim_family="counterexample",
            comparison_scope="full_state_date_poll_panel",
            comparison_unit="state_month_units",
            comparison_count=_iv(unit_robustness, "full_panel_state_month_unit_count"),
            polymarket_support_count=_iv(
                unit_robustness,
                "full_panel_state_month_polymarket_support_count",
            ),
            poll_support_count=_iv(
                unit_robustness,
                "full_panel_state_month_poll_support_count",
            ),
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="contradicted",
            allowed_statement=(
                "Full-panel state-month robustness units favor poll-derived "
                "comparators."
            ),
            limitation="State-month units still belong to one election context.",
        ),
        _claim_row(
            claim_id="late_high_distance_rows",
            claim_label="Late high poll-distance rows",
            claim_family="counterexample",
            comparison_scope="<=90_days_high_poll_distance",
            comparison_unit="state_date_rows",
            comparison_count=_iv(unit_robustness, "late_high_row_count"),
            polymarket_support_count=0,
            poll_support_count=_iv(unit_robustness, "late_high_poll_lower_loss_count"),
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="contradicted",
            allowed_statement=(
                "Late high-distance rows are a clear counterexample scope."
            ),
            limitation="This scope is excluded from the bounded supporting claim.",
        ),
        _claim_row(
            claim_id="late_high_distance_states",
            claim_label="Late high poll-distance states",
            claim_family="counterexample",
            comparison_scope="<=90_days_high_poll_distance",
            comparison_unit="states",
            comparison_count=_iv(state_significance, "late_high_distance_state_count"),
            polymarket_support_count=_iv(
                state_significance,
                "late_high_distance_polymarket_majority_state_count",
            ),
            poll_support_count=_iv(
                state_significance,
                "late_high_distance_poll_majority_state_count",
            ),
            tie_count=0,
            mean_loss_advantage=float("nan"),
            exact_p_value=_fv(
                state_significance,
                "late_high_distance_poll_exact_binomial_p_value_greater",
            ),
            exact_95_ci_low=float("nan"),
            claim_status="contradicted",
            allowed_statement=(
                "Late high-distance state-level support favors poll-derived "
                "comparators."
            ),
            limitation="Only five states are in this counterexample scope.",
        ),
        _claim_row(
            claim_id="popular_vote_daily_rows",
            claim_label="Popular-vote daily rows",
            claim_family="counterexample",
            comparison_scope="popular_vote_poll_transform",
            comparison_unit="daily_rows",
            comparison_count=_iv(popular_vote, "case_count"),
            polymarket_support_count=_iv(
                popular_vote,
                "polymarket_lower_loss_count",
            ),
            poll_support_count=_iv(popular_vote, "poll_derived_lower_loss_count"),
            tie_count=_iv(popular_vote, "tie_count"),
            mean_loss_advantage=_fv(popular_vote, "mean_loss_advantage"),
            exact_p_value=float("nan"),
            exact_95_ci_low=float("nan"),
            claim_status="contradicted",
            allowed_statement=(
                "The popular-vote poll-transform comparison contradicts the "
                "strong Polymarket-better claim."
            ),
            limitation="This is one national popular-vote outcome with daily rows.",
        ),
    ]
    return pd.DataFrame(rows, columns=CLAIM_COLUMNS)


def build_summary_table(
    *,
    claims: pd.DataFrame,
    poll_result: pd.DataFrame,
    unit_robustness: pd.DataFrame,
    direct_loss: pd.DataFrame,
    direct_state: pd.DataFrame,
    outlier: pd.DataFrame,
    state_panel: pd.DataFrame,
    popular_vote: pd.DataFrame,
    state_significance: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact summary rows for the claim-readiness output."""

    del direct_loss, direct_state, outlier, state_panel, popular_vote, state_significance
    primary_count = _iv(poll_result, "primary_comparison_count")
    primary_pm = _iv(poll_result, "primary_polymarket_support_count")
    primary_state_month_count = _iv(unit_robustness, "primary_state_month_unit_count")
    primary_state_month_pm = _iv(
        unit_robustness,
        "primary_state_month_polymarket_support_count",
    )
    counterexamples = int((claims["claim_family"] == "counterexample").sum())
    supported = int((claims["claim_status"] == "supported").sum())
    mixed = int(claims["claim_status"].str.contains("mean_", regex=False).sum())
    rows = [
        _summary_row(
            "claim_row_count",
            int(len(claims)),
            "rows",
            "Claim-readiness rows in the H1 poll synthesis.",
        ),
        _summary_row(
            "supported_bounded_scope_row_count",
            supported,
            "rows",
            "Rows where the bounded primary poll-comparison scope is supported.",
        ),
        _summary_row(
            "mixed_mean_support_row_count",
            mixed,
            "rows",
            "Rows with mean-loss support but missing case/state majority support.",
        ),
        _summary_row(
            "counterexample_row_count",
            counterexamples,
            "rows",
            "Rows that contradict the strong broad Polymarket-better claim.",
        ),
        _summary_row(
            "primary_polymarket_support_count",
            primary_pm,
            "state-date rows",
            "Bounded primary state-date rows where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "primary_comparison_count",
            primary_count,
            "state-date rows",
            "Bounded primary state-date comparison count.",
        ),
        _summary_row(
            "primary_polymarket_support_share",
            primary_pm / primary_count,
            "share",
            "Bounded primary state-date Polymarket support share.",
        ),
        _summary_row(
            "primary_state_month_polymarket_support_count",
            primary_state_month_pm,
            "state_month units",
            "Bounded primary state-month units supporting Polymarket.",
        ),
        _summary_row(
            "primary_state_month_unit_count",
            primary_state_month_count,
            "state_month units",
            "Bounded primary state-month unit count.",
        ),
        _summary_row(
            "primary_state_month_exact_p_value",
            _fv(
                unit_robustness,
                "primary_state_month_polymarket_exact_binomial_p_value_greater",
            ),
            "p_value",
            "Exact one-sided state-month p-value for bounded Polymarket support.",
        ),
        _summary_row(
            "primary_state_month_exact_95_ci_low",
            _fv(
                unit_robustness,
                "primary_state_month_polymarket_exact_95_ci_low",
            ),
            "share",
            "Exact 95 percent lower confidence bound for state-month support.",
        ),
        _summary_row(
            "bounded_poll_claim_supported",
            1,
            "binary",
            "The bounded <=90-day low/middle poll-distance claim is supported.",
        ),
        _summary_row(
            "broad_claim_proven",
            0,
            "binary",
            "The broad many-cases or many-elections claim is not proven.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Current evidence supports a bounded poll claim, not the full broad objective.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_claim_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate claim-readiness rows."""

    _require_columns(frame, CLAIM_COLUMNS, "H1 poll claim-readiness table")
    _reject_forbidden_columns(frame, "H1 poll claim-readiness table")
    validated = frame.loc[:, list(CLAIM_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 poll claim-readiness table must not be empty")
    if validated["claim_id"].duplicated().any():
        raise ValueError("claim_id values must be unique")
    for column in (
        "comparison_count",
        "polymarket_support_count",
        "poll_support_count",
        "tie_count",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise").astype(int)
    for column in (
        "polymarket_support_share",
        "mean_loss_advantage",
        "exact_p_value",
        "exact_95_ci_low",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
    allowed = {
        "supported",
        "directional_support",
        "mean_supported_case_majority_not_supported",
        "mean_supported_state_majority_not_supported",
        "mean_robust_to_single_state",
        "contradicted",
    }
    unknown = sorted(set(validated["claim_status"]) - allowed)
    if unknown:
        raise ValueError(f"unknown claim_status values: {unknown}")
    return validated


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact claim-readiness summary rows."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 poll claim-readiness summary")
    _reject_forbidden_columns(frame, "H1 poll claim-readiness summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 poll claim-readiness summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return validated


def write_claim_readiness_figure(
    *,
    claims: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the H1 poll-claim readiness figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.8, 9.8))
    fig.suptitle(
        "H1 poll-comparison claim readiness",
        fontsize=14,
        fontweight="bold",
    )
    _plot_bounded_support(axes[0, 0], claims)
    _plot_counterexamples(axes[0, 1], claims)
    _plot_mean_advantages(axes[1, 0], claims)
    _plot_statement(axes[1, 1], summary)
    fig.text(
        0.5,
        0.012,
        (
            "All values are deterministic summaries from existing H1 artifacts. "
            "Positive loss advantage means poll-derived Brier minus Polymarket Brier."
        ),
        ha="center",
        fontsize=8.7,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    claims: pd.DataFrame,
    summary: pd.DataFrame,
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    """Build metadata for the H1 poll-claim readiness output."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_poll_claim_readiness",
            "calculation_scope": "deterministic_python_from_existing_h1_summaries",
            "does_not_collect_external_data": True,
            "does_not_recompute_raw_brier_rows": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "claim_row_count": int(len(claims)),
            "supported_bounded_scope_row_count": int(
                _summary_value(summary, "supported_bounded_scope_row_count")
            ),
            "counterexample_row_count": int(
                _summary_value(summary, "counterexample_row_count")
            ),
            "bounded_poll_claim_supported": bool(
                _summary_value(summary, "bounded_poll_claim_supported")
            ),
            "broad_claim_proven": bool(_summary_value(summary, "broad_claim_proven")),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "limitations": {
            "state_date_rows_are_repeated_forecasts": True,
            "state_month_units_are_not_independent_elections": True,
            "bounded_claim_excludes_high_poll_distance_counterexamples": True,
            "broad_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _claim_row(
    *,
    claim_id: str,
    claim_label: str,
    claim_family: str,
    comparison_scope: str,
    comparison_unit: str,
    comparison_count: int,
    polymarket_support_count: int,
    poll_support_count: int,
    tie_count: int,
    mean_loss_advantage: float,
    exact_p_value: float,
    exact_95_ci_low: float,
    claim_status: str,
    allowed_statement: str,
    limitation: str,
) -> dict[str, Any]:
    denominator = comparison_count if comparison_count else 1
    return {
        "claim_id": claim_id,
        "claim_label": claim_label,
        "claim_family": claim_family,
        "comparison_scope": comparison_scope,
        "comparison_unit": comparison_unit,
        "comparison_count": int(comparison_count),
        "polymarket_support_count": int(polymarket_support_count),
        "poll_support_count": int(poll_support_count),
        "tie_count": int(tie_count),
        "polymarket_support_share": polymarket_support_count / denominator,
        "mean_loss_advantage": mean_loss_advantage,
        "exact_p_value": exact_p_value,
        "exact_95_ci_low": exact_95_ci_low,
        "claim_status": claim_status,
        "allowed_statement": allowed_statement,
        "limitation": limitation,
    }


def _plot_bounded_support(ax: plt.Axes, claims: pd.DataFrame) -> None:
    rows = claims.loc[
        claims["claim_family"].isin({"supported_bounded_scope", "directional_bounded_scope"})
    ].copy()
    rows = rows.sort_values("polymarket_support_share")
    labels = [str(label).replace("Bounded <=90d low/middle ", "") for label in rows["claim_label"]]
    colors = [
        "#2563eb" if status == "supported" else "#60a5fa"
        for status in rows["claim_status"]
    ]
    ax.barh(labels, rows["polymarket_support_share"] * 100, color=colors)
    ax.axvline(50, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Polymarket lower-loss share (%)")
    ax.set_title("Supported bounded poll scope")
    ax.grid(True, axis="x", alpha=0.18)
    for idx, row in enumerate(rows.to_dict(orient="records")):
        ax.text(
            min(row["polymarket_support_share"] * 100 + 1.5, 96),
            idx,
            f"{row['polymarket_support_count']}/{row['comparison_count']}",
            va="center",
            fontsize=8.2,
        )


def _plot_counterexamples(ax: plt.Axes, claims: pd.DataFrame) -> None:
    rows = claims.loc[claims["claim_family"] == "counterexample"].copy()
    rows = rows.sort_values("polymarket_support_share")
    labels = [
        str(label)
        .replace("Full ", "Full\n")
        .replace("Late high ", "Late high\n")
        .replace("Popular-vote ", "Popular-vote\n")
        for label in rows["claim_label"]
    ]
    ax.barh(labels, rows["polymarket_support_share"] * 100, color="#7c3aed")
    ax.axvline(50, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Polymarket lower-loss share (%)")
    ax.set_title("Counterexample scopes")
    ax.grid(True, axis="x", alpha=0.18)
    for idx, row in enumerate(rows.to_dict(orient="records")):
        ax.text(
            min(row["polymarket_support_share"] * 100 + 1.5, 96),
            idx,
            f"{row['polymarket_support_count']}/{row['comparison_count']}",
            va="center",
            fontsize=8.2,
        )


def _plot_mean_advantages(ax: plt.Axes, claims: pd.DataFrame) -> None:
    keep = claims.loc[claims["mean_loss_advantage"].notna()].copy()
    keep = keep.sort_values("mean_loss_advantage")
    colors = [
        "#2563eb" if value > 0 else "#7c3aed"
        for value in keep["mean_loss_advantage"].tolist()
    ]
    labels = [
        str(label)
        .replace("Bounded <=90d low/middle ", "Bounded ")
        .replace("Direct poll-transform ", "Direct ")
        .replace("Direct poll ", "Direct ")
        .replace("Full ", "Full ")
        for label in keep["claim_label"]
    ]
    ax.barh(labels, keep["mean_loss_advantage"], color=colors)
    ax.axvline(0, color="#111827", linewidth=0.9)
    ax.set_title("Mean-loss direction")
    ax.set_xlabel("Poll Brier minus Polymarket Brier")
    ax.grid(True, axis="x", alpha=0.18)


def _plot_statement(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "Claim readiness\n"
        f"- Bounded primary rows: "
        f"{_int_summary(summary, 'primary_polymarket_support_count')}/"
        f"{_int_summary(summary, 'primary_comparison_count')} "
        f"({_summary_value(summary, 'primary_polymarket_support_share') * 100:.1f}%).\n"
        f"- State-month units: "
        f"{_int_summary(summary, 'primary_state_month_polymarket_support_count')}/"
        f"{_int_summary(summary, 'primary_state_month_unit_count')} "
        f"(p={_summary_value(summary, 'primary_state_month_exact_p_value'):.2g}, "
        f"95% low={_summary_value(summary, 'primary_state_month_exact_95_ci_low'):.3f}).\n"
        f"- Counterexample rows: "
        f"{_int_summary(summary, 'counterexample_row_count')}.\n\n"
        "Supported wording\n"
        "- Polymarket is better in the bounded <=90-day low/middle poll-distance\n"
        "  scope, across rows and robustness units.\n\n"
        "Not yet supported\n"
        "- A broad many-cases or many-elections Polymarket-better claim.\n"
        "- High poll-distance and full-panel scopes.\n\n"
        "Status: not_proven for the full objective."
    )
    ax.text(
        0.02,
        0.96,
        text,
        va="top",
        fontsize=10.1,
        color="#1f2937",
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _summary_row(
    summary_id: str,
    value: int | float | str,
    unit: str,
    description: str,
) -> dict[str, int | float | str]:
    return {
        "summary_id": summary_id,
        "value": value,
        "unit": unit,
        "description": description,
    }


def _fv(frame: pd.DataFrame, summary_id: str) -> float:
    return float(_summary_value(frame, summary_id))


def _iv(frame: pd.DataFrame, summary_id: str) -> int:
    return int(float(_summary_value(frame, summary_id)))


def _summary_value(frame: pd.DataFrame, summary_id: str) -> float:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def _int_summary(summary: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(summary, summary_id))


def _require_columns(
    frame: pd.DataFrame,
    required: Sequence[str],
    label: str,
) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _reject_forbidden_columns(frame: pd.DataFrame, label: str) -> None:
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in FORBIDDEN_COLUMN_TOKENS)
    ]
    if forbidden:
        raise ValueError(f"{label} contains forbidden columns: {forbidden}")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-result-input", type=Path, default=POLL_RESULT_INPUT)
    parser.add_argument("--unit-robustness-input", type=Path, default=UNIT_ROBUSTNESS_INPUT)
    parser.add_argument("--direct-loss-input", type=Path, default=DIRECT_LOSS_INPUT)
    parser.add_argument("--direct-state-input", type=Path, default=DIRECT_STATE_INPUT)
    parser.add_argument("--outlier-input", type=Path, default=OUTLIER_INPUT)
    parser.add_argument("--state-panel-input", type=Path, default=STATE_PANEL_INPUT)
    parser.add_argument("--popular-vote-input", type=Path, default=POPULAR_VOTE_INPUT)
    parser.add_argument("--state-significance-input", type=Path, default=STATE_SIGNIFICANCE_INPUT)
    parser.add_argument("--claim-output", type=Path, default=CLAIM_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_poll_claim_readiness_outputs(
            poll_result_input=args.poll_result_input,
            unit_robustness_input=args.unit_robustness_input,
            direct_loss_input=args.direct_loss_input,
            direct_state_input=args.direct_state_input,
            outlier_input=args.outlier_input,
            state_panel_input=args.state_panel_input,
            popular_vote_input=args.popular_vote_input,
            state_significance_input=args.state_significance_input,
            claim_output=args.claim_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
