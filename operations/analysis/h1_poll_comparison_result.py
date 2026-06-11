"""Create a thesis-facing H1 poll-comparison result scorecard.

The broader H1 claim audit mixes poll transforms, poll-based model forecasts,
daily rows, and counterexamples. This module isolates the direct poll-comparison
question into one bounded result artifact. It reads existing deterministic H1
outputs only; it does not collect data or recompute raw Brier rows.
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


CLAIM_AUDIT_INPUT = RESULTS_DIR / "h1_claim_evidence_audit.csv"
CLAIM_AUDIT_SUMMARY_INPUT = RESULTS_DIR / "h1_claim_evidence_audit_summary.csv"
PANEL_COMPETITIVENESS_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_competitiveness_summary.csv"
)
STATE_SIGNIFICANCE_INPUT = (
    RESULTS_DIR / "h1_state_poll_panel_state_significance_summary.csv"
)

RESULT_OUTPUT = RESULTS_DIR / "h1_poll_comparison_result.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_poll_comparison_result_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_poll_comparison_result.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_poll_comparison_result_metadata.json"

RESULT_COLUMNS: tuple[str, ...] = (
    "result_id",
    "result_label",
    "result_role",
    "comparison_scope",
    "comparison_unit",
    "comparison_count",
    "state_count",
    "polymarket_support_count",
    "poll_support_count",
    "tie_count",
    "polymarket_support_share",
    "mean_polymarket_brier",
    "mean_poll_brier",
    "mean_loss_advantage",
    "exact_p_value",
    "exact_95_ci_low",
    "supports_bounded_polymarket_statement",
    "contradicts_broad_polymarket_statement",
    "allowed_statement",
    "limitation",
    "source_artifacts",
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
class H1PollComparisonResult:
    """Summary of generated H1 poll-comparison result artifacts."""

    result_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    result_row_count: int
    primary_polymarket_support_count: int
    primary_poll_support_count: int
    primary_state_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "result_path": str(self.result_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "result_row_count": self.result_row_count,
            "primary_polymarket_support_count": self.primary_polymarket_support_count,
            "primary_poll_support_count": self.primary_poll_support_count,
            "primary_state_count": self.primary_state_count,
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_poll_comparison_result_outputs(
    *,
    claim_audit_input: Path = CLAIM_AUDIT_INPUT,
    claim_audit_summary_input: Path = CLAIM_AUDIT_SUMMARY_INPUT,
    panel_competitiveness_input: Path = PANEL_COMPETITIVENESS_INPUT,
    state_significance_input: Path = STATE_SIGNIFICANCE_INPUT,
    result_output: Path = RESULT_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1PollComparisonResult:
    """Generate result CSV, compact summary, figure, and metadata."""

    claim_audit = read_csv(claim_audit_input)
    claim_summary = read_summary(claim_audit_summary_input)
    panel_competitiveness = read_summary(panel_competitiveness_input)
    state_significance = read_summary(state_significance_input)

    result = validate_result_table(
        build_result_table(
            claim_audit=claim_audit,
            claim_summary=claim_summary,
            panel_competitiveness=panel_competitiveness,
            state_significance=state_significance,
        )
    )
    summary = validate_summary_table(build_summary_table(result, claim_summary))

    result_output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(result_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_result_figure(result=result, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        result=result,
        summary=summary,
        source_paths={
            "claim_audit_input": claim_audit_input,
            "claim_audit_summary_input": claim_audit_summary_input,
            "panel_competitiveness_input": panel_competitiveness_input,
            "state_significance_input": state_significance_input,
            "result_output": result_output,
            "summary_output": summary_output,
            "figure_output": figure_output,
        },
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    primary = _result_row(result, "bounded_late_competitive_poll_rows")
    return H1PollComparisonResult(
        result_path=result_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        result_row_count=int(len(result)),
        primary_polymarket_support_count=int(primary["polymarket_support_count"]),
        primary_poll_support_count=int(primary["poll_support_count"]),
        primary_state_count=int(primary["state_count"]),
        broad_claim_proven=bool(_summary_value(summary, "broad_claim_proven")),
    )


def read_csv(path: Path) -> pd.DataFrame:
    """Read a non-empty local CSV artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 poll-comparison input not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"H1 poll-comparison input must not be empty: {path}")
    return frame


def read_summary(path: Path) -> pd.DataFrame:
    """Read a summary_id/value CSV artifact."""

    frame = read_csv(path)
    missing = sorted({"summary_id", "value"} - set(frame.columns))
    if missing:
        raise ValueError(f"H1 poll-comparison summary missing columns: {missing}")
    return frame


def build_result_table(
    *,
    claim_audit: pd.DataFrame,
    claim_summary: pd.DataFrame,
    panel_competitiveness: pd.DataFrame,
    state_significance: pd.DataFrame,
) -> pd.DataFrame:
    """Build a bounded H1 poll-comparison result table."""

    full_panel = _audit_row(claim_audit, "full_state_date_poll_panel")
    late_panel = _audit_row(claim_audit, "late_90_day_state_date_rows")
    primary_row_count = int(
        _summary_value(panel_competitiveness, "late_non_safe_row_count")
    )
    primary_state_count = int(
        _summary_value(panel_competitiveness, "late_non_safe_state_count")
    )
    primary_pm_count = int(
        _summary_value(
            panel_competitiveness,
            "late_non_safe_polymarket_lower_loss_count",
        )
    )
    primary_poll_count = int(
        _summary_value(panel_competitiveness, "late_non_safe_poll_lower_loss_count")
    )
    high_row_count = int(
        _summary_value(panel_competitiveness, "late_high_distance_row_count")
    )
    high_state_count = int(
        _summary_value(panel_competitiveness, "late_high_distance_state_count")
    )
    high_pm_count = int(
        _summary_value(
            panel_competitiveness,
            "late_high_distance_polymarket_lower_loss_count",
        )
    )
    high_poll_count = int(
        _summary_value(panel_competitiveness, "late_high_distance_poll_lower_loss_count")
    )
    sign_state_count = int(
        _summary_value(state_significance, "late_non_safe_state_count")
    )
    sign_pm_count = int(
        _summary_value(
            state_significance,
            "late_non_safe_polymarket_majority_state_count",
        )
    )
    sign_high_state_count = int(
        _summary_value(state_significance, "late_high_distance_state_count")
    )
    sign_high_poll_count = int(
        _summary_value(state_significance, "late_high_distance_poll_majority_state_count")
    )

    rows = [
        _row(
            result_id="bounded_late_competitive_poll_rows",
            result_label="Bounded late low/middle poll-distance rows",
            result_role="primary_bounded_support",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="state_date_forecast_rows",
            comparison_count=primary_row_count,
            state_count=primary_state_count,
            pm_count=primary_pm_count,
            poll_count=primary_poll_count,
            ties=0,
            mean_pm=_summary_value(
                panel_competitiveness,
                "late_non_safe_mean_polymarket_brier",
            ),
            mean_poll=_summary_value(panel_competitiveness, "late_non_safe_mean_poll_brier"),
            advantage=_summary_value(
                panel_competitiveness,
                "late_non_safe_mean_loss_advantage",
            ),
            exact_p=_summary_value(
                state_significance,
                "late_non_safe_polymarket_exact_binomial_p_value_greater",
            ),
            ci_low=_summary_value(
                state_significance,
                "late_non_safe_polymarket_exact_95_ci_low",
            ),
            supports=True,
            contradicts=False,
            allowed_statement=(
                "Bounded statement supported: in the <=90-day low/middle "
                "poll-distance state-date panel, Polymarket has lower loss in "
                f"{primary_pm_count} of {primary_row_count} rows."
            ),
            limitation=(
                "Rows repeat resolved states from one election context and "
                "poll-derived probabilities are transformed from polling margins."
            ),
            artifacts=(
                "h1_state_poll_panel_competitiveness_summary.csv; "
                "h1_state_poll_panel_state_significance_summary.csv"
            ),
        ),
        _row(
            result_id="bounded_late_competitive_state_sign_test",
            result_label="State-as-unit confirmation",
            result_role="state_level_confirmation",
            comparison_scope="<=90_days_low_middle_poll_distance",
            comparison_unit="states",
            comparison_count=sign_state_count,
            state_count=sign_state_count,
            pm_count=sign_pm_count,
            poll_count=sign_state_count - sign_pm_count,
            ties=0,
            mean_pm=None,
            mean_poll=None,
            advantage=None,
            exact_p=_summary_value(
                state_significance,
                "late_non_safe_polymarket_exact_binomial_p_value_greater",
            ),
            ci_low=_summary_value(
                state_significance,
                "late_non_safe_polymarket_exact_95_ci_low",
            ),
            supports=True,
            contradicts=False,
            allowed_statement=(
                "The state-as-unit sign test supports Polymarket in "
                f"{sign_pm_count} of {sign_state_count} states."
            ),
            limitation=(
                "The exact binomial test is a bounded diagnostic; states are "
                "not independent elections."
            ),
            artifacts="h1_state_poll_panel_state_significance_summary.csv",
        ),
        _row_from_audit(
            result_id="wider_late_poll_window",
            result_label="Wider <=90-day state-date poll panel",
            result_role="secondary_bounded_support",
            source=late_panel,
            supports=True,
            contradicts=False,
            allowed_statement=(
                "In the full <=90-day window, Polymarket has lower loss in "
                f"{int(late_panel['polymarket_support_count'])} of "
                f"{int(late_panel['comparison_count'])} rows."
            ),
        ),
        _row_from_audit(
            result_id="full_poll_panel_counterexample",
            result_label="Full state-date poll panel",
            result_role="broad_claim_counterexample",
            source=full_panel,
            supports=False,
            contradicts=True,
            allowed_statement=(
                "The full state-date poll panel contradicts the broad claim: "
                f"poll-derived probabilities have lower loss in "
                f"{int(full_panel['comparator_support_count'])} of "
                f"{int(full_panel['comparison_count'])} rows."
            ),
        ),
        _row(
            result_id="late_high_distance_counterexample",
            result_label="Late high poll-distance rows",
            result_role="scope_counterexample",
            comparison_scope="<=90_days_high_poll_distance",
            comparison_unit="state_date_forecast_rows",
            comparison_count=high_row_count,
            state_count=high_state_count,
            pm_count=high_pm_count,
            poll_count=high_poll_count,
            ties=0,
            mean_pm=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_polymarket_brier",
            ),
            mean_poll=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_poll_brier",
            ),
            advantage=_summary_value(
                panel_competitiveness,
                "late_high_distance_mean_loss_advantage",
            ),
            exact_p=_summary_value(
                state_significance,
                "late_high_distance_poll_exact_binomial_p_value_greater",
            ),
            ci_low=None,
            supports=False,
            contradicts=True,
            allowed_statement=(
                "In the late high-distance subset, poll-derived probabilities "
                f"have lower loss in {high_poll_count} of {high_row_count} rows "
                f"and {sign_high_poll_count} of {sign_high_state_count} states."
            ),
            limitation=(
                "This safer-state subset blocks a broad Polymarket-better "
                "claim even though the late low/middle-distance subset supports it."
            ),
            artifacts=(
                "h1_state_poll_panel_competitiveness_summary.csv; "
                "h1_state_poll_panel_state_significance_summary.csv"
            ),
        ),
        _row(
            result_id="direct_poll_audit_ledger",
            result_label="Direct poll-related audit ledger",
            result_role="claim_ledger_context",
            comparison_scope="direct_poll_related_audit_rows",
            comparison_unit="audit_rows",
            comparison_count=int(
                _summary_value(claim_summary, "direct_poll_audit_row_count")
            ),
            state_count=0,
            pm_count=int(_summary_value(claim_summary, "direct_poll_support_row_count")),
            poll_count=int(
                _summary_value(claim_summary, "direct_poll_contradiction_row_count")
            ),
            ties=0,
            mean_pm=None,
            mean_poll=None,
            advantage=None,
            exact_p=None,
            ci_low=None,
            supports=True,
            contradicts=False,
            allowed_statement=(
                "Across direct poll-related audit rows, the current evidence is "
                "mostly supportive but still bounded."
            ),
            limitation=(
                "Audit rows are evidence scopes, not independent election outcomes."
            ),
            artifacts="h1_claim_evidence_audit_summary.csv",
        ),
    ]
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def build_summary_table(
    result: pd.DataFrame,
    claim_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact summary rows for reporting."""

    primary = _result_row(result, "bounded_late_competitive_poll_rows")
    sign = _result_row(result, "bounded_late_competitive_state_sign_test")
    full = _result_row(result, "full_poll_panel_counterexample")
    high = _result_row(result, "late_high_distance_counterexample")
    direct = _result_row(result, "direct_poll_audit_ledger")
    broad_claim_proven = int(_summary_value(claim_summary, "broad_user_claim_proven"))
    rows = [
        _summary_row(
            "primary_scope",
            str(primary["comparison_scope"]),
            "scope",
            "Scope of the main bounded Polymarket-supporting poll comparison.",
        ),
        _summary_row(
            "primary_polymarket_support_count",
            int(primary["polymarket_support_count"]),
            "state-date rows",
            "Rows in the primary bounded scope where Polymarket has lower loss.",
        ),
        _summary_row(
            "primary_poll_support_count",
            int(primary["poll_support_count"]),
            "state-date rows",
            "Rows in the primary bounded scope where poll-derived probability has lower loss.",
        ),
        _summary_row(
            "primary_comparison_count",
            int(primary["comparison_count"]),
            "state-date rows",
            "Rows in the primary bounded scope.",
        ),
        _summary_row(
            "primary_polymarket_support_share",
            float(primary["polymarket_support_share"]),
            "share",
            "Polymarket lower-loss share in the primary bounded scope.",
        ),
        _summary_row(
            "primary_mean_loss_advantage",
            float(primary["mean_loss_advantage"]),
            "brier_score",
            "Positive values mean lower Polymarket mean Brier in the primary scope.",
        ),
        _summary_row(
            "primary_state_count",
            int(sign["state_count"]),
            "states",
            "State count for the primary bounded sign-test scope.",
        ),
        _summary_row(
            "primary_polymarket_state_count",
            int(sign["polymarket_support_count"]),
            "states",
            "States where Polymarket has lower-loss majority in the primary bounded scope.",
        ),
        _summary_row(
            "primary_exact_binomial_p_value",
            float(sign["exact_p_value"]),
            "p_value",
            "One-sided exact binomial p-value for the primary state-as-unit diagnostic.",
        ),
        _summary_row(
            "primary_exact_95_ci_low",
            float(sign["exact_95_ci_low"]),
            "share",
            "Exact 95 percent lower confidence bound for the primary state support share.",
        ),
        _summary_row(
            "direct_poll_audit_support_count",
            int(direct["polymarket_support_count"]),
            "audit rows",
            "Direct poll-related audit rows supporting bounded Polymarket evidence.",
        ),
        _summary_row(
            "direct_poll_audit_row_count",
            int(direct["comparison_count"]),
            "audit rows",
            "Direct poll-related audit rows.",
        ),
        _summary_row(
            "full_panel_polymarket_support_count",
            int(full["polymarket_support_count"]),
            "state-date rows",
            "Full-panel rows where Polymarket has lower loss.",
        ),
        _summary_row(
            "full_panel_poll_support_count",
            int(full["poll_support_count"]),
            "state-date rows",
            "Full-panel rows where poll-derived probability has lower loss.",
        ),
        _summary_row(
            "late_high_distance_poll_support_count",
            int(high["poll_support_count"]),
            "state-date rows",
            "Late high-distance rows where poll-derived probability has lower loss.",
        ),
        _summary_row(
            "bounded_polymarket_statement_supported",
            1,
            "binary",
            "The primary bounded late low/middle-distance poll statement is supported.",
        ),
        _summary_row(
            "broad_claim_proven",
            broad_claim_proven,
            "binary",
            "The broad many-cases Polymarket-better claim remains unproven.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Current evidence supports a bounded poll statement, not the full broad objective.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_result_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate result table schema and numeric consistency."""

    _require_columns(frame, RESULT_COLUMNS, "H1 poll result table")
    _reject_forbidden_columns(frame, "H1 poll result table")
    validated = frame.loc[:, list(RESULT_COLUMNS)].copy()
    numeric_columns = [
        "comparison_count",
        "state_count",
        "polymarket_support_count",
        "poll_support_count",
        "tie_count",
        "polymarket_support_share",
    ]
    for column in numeric_columns:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    for column in (
        "mean_polymarket_brier",
        "mean_poll_brier",
        "mean_loss_advantage",
        "exact_p_value",
        "exact_95_ci_low",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
    if validated.empty:
        raise ValueError("H1 poll result table must not be empty")
    count_sum = (
        validated["polymarket_support_count"]
        + validated["poll_support_count"]
        + validated["tie_count"]
    )
    if not (count_sum == validated["comparison_count"]).all():
        raise ValueError("support counts must add to comparison_count")
    expected_share = validated["polymarket_support_count"] / validated["comparison_count"]
    if not (validated["polymarket_support_share"].round(12) == expected_share.round(12)).all():
        raise ValueError("polymarket_support_share must match support counts")
    return validated


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate summary table schema."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 poll result summary")
    _reject_forbidden_columns(frame, "H1 poll result summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 poll result summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("H1 poll result summary_id values must be unique")
    return validated


def write_result_figure(
    *,
    result: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a focused H1 poll-comparison result figure."""

    primary = _result_row(result, "bounded_late_competitive_poll_rows")
    sign = _result_row(result, "bounded_late_competitive_state_sign_test")
    full = _result_row(result, "full_poll_panel_counterexample")
    high = _result_row(result, "late_high_distance_counterexample")
    direct = _result_row(result, "direct_poll_audit_ledger")
    late = _result_row(result, "wider_late_poll_window")

    fig, axes = plt.subplots(2, 2, figsize=(14.4, 9.2))
    fig.suptitle(
        "H1 poll-comparison result: bounded Polymarket support with counterexamples",
        fontsize=14,
        fontweight="bold",
    )

    _plot_primary_counts(axes[0, 0], primary, sign)
    _plot_scope_support(axes[0, 1], [primary, late, full, high])
    _plot_mean_brier(axes[1, 0], [primary, late, full, high])
    _plot_statement_box(axes[1, 1], primary, sign, full, high, direct, summary)

    fig.text(
        0.5,
        0.012,
        (
            "All values are deterministic outputs from existing H1 artifacts. "
            "The supported statement is bounded to the late low/middle "
            "poll-distance scope; the full panel and high-distance subset remain "
            "counterexamples."
        ),
        ha="center",
        fontsize=8.5,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    result: pd.DataFrame,
    summary: pd.DataFrame,
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    """Build metadata for the focused poll-comparison scorecard."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_poll_comparison_result_scorecard",
            "calculation_scope": "deterministic_python_from_precomputed_h1_artifacts",
            "does_not_recompute_raw_brier_rows": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
        },
        "outputs": {
            "result_row_count": int(len(result)),
            "bounded_polymarket_statement_supported": bool(
                _summary_value(summary, "bounded_polymarket_statement_supported")
            ),
            "broad_claim_proven": bool(_summary_value(summary, "broad_claim_proven")),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "limitations": {
            "bounded_statement_is_late_low_middle_poll_distance_only": True,
            "full_state_date_panel_contradicts_broad_claim": True,
            "late_high_distance_subset_contradicts_broad_claim": True,
            "rows_repeat_states_from_one_election_context": True,
            "poll_probabilities_are_transformed_from_polling_margins": True,
            "not_independent_many_elections_proof": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _plot_primary_counts(
    ax: plt.Axes,
    primary: pd.Series,
    sign: pd.Series,
) -> None:
    labels = ["State-date rows", "States"]
    pm_counts = [
        int(primary["polymarket_support_count"]),
        int(sign["polymarket_support_count"]),
    ]
    poll_counts = [int(primary["poll_support_count"]), int(sign["poll_support_count"])]
    totals = [int(primary["comparison_count"]), int(sign["comparison_count"])]
    y_positions = range(len(labels))
    ax.barh(y_positions, pm_counts, color="#2563eb", label="Polymarket lower")
    ax.barh(
        y_positions,
        poll_counts,
        left=pm_counts,
        color="#dc2626",
        alpha=0.78,
        label="Poll-derived lower",
    )
    for y, pm_count, poll_count, total in zip(y_positions, pm_counts, poll_counts, totals):
        ax.text(
            total + max(totals) * 0.015,
            y,
            f"PM {pm_count} / poll {poll_count}",
            va="center",
            fontsize=9,
            color="#374151",
        )
    ax.set_yticks(list(y_positions), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max(totals) * 1.32)
    ax.set_title("Primary bounded result")
    ax.set_xlabel("Count")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", alpha=0.25)


def _plot_scope_support(ax: plt.Axes, rows: Sequence[pd.Series]) -> None:
    labels = [
        "Late low/mid\npoll distance",
        "<=90d\nall rows",
        "Full\npanel",
        "Late high\npoll distance",
    ]
    shares = [float(row["polymarket_support_share"]) for row in rows]
    colors = ["#2563eb" if share > 0.5 else "#dc2626" for share in shares]
    ax.bar(labels, shares, color=colors, alpha=0.84)
    ax.axhline(0.5, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_ylim(0, 1.08)
    ax.set_title("Polymarket lower-loss share by scope")
    ax.set_ylabel("Support share")
    ax.grid(axis="y", alpha=0.25)
    for idx, row in enumerate(rows):
        ax.text(
            idx,
            float(row["polymarket_support_share"]) + 0.035,
            (
                f"{int(row['polymarket_support_count'])}/"
                f"{int(row['comparison_count'])}"
            ),
            ha="center",
            fontsize=8,
        )


def _plot_mean_brier(ax: plt.Axes, rows: Sequence[pd.Series]) -> None:
    labels = [
        "Late low/mid",
        "<=90d all",
        "Full panel",
        "Late high",
    ]
    positions = list(range(len(rows)))
    width = 0.35
    pm_values = [float(row["mean_polymarket_brier"]) for row in rows]
    poll_values = [float(row["mean_poll_brier"]) for row in rows]
    ax.bar(
        [pos - width / 2 for pos in positions],
        pm_values,
        width=width,
        color="#2563eb",
        label="Polymarket",
    )
    ax.bar(
        [pos + width / 2 for pos in positions],
        poll_values,
        width=width,
        color="#7c3aed",
        label="Poll-derived",
    )
    ax.set_xticks(positions, labels)
    ax.set_title("Mean Brier by scope")
    ax.set_ylabel("Mean Brier loss")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)


def _plot_statement_box(
    ax: plt.Axes,
    primary: pd.Series,
    sign: pd.Series,
    full: pd.Series,
    high: pd.Series,
    direct: pd.Series,
    summary: pd.DataFrame,
) -> None:
    ax.axis("off")
    text = (
        "Allowed bounded statement\n"
        f"- Polymarket lower loss: {int(primary['polymarket_support_count'])} "
        f"of {int(primary['comparison_count'])} late low/middle-distance rows "
        f"({float(primary['polymarket_support_share']) * 100:.1f}%).\n"
        f"- State-as-unit check: {int(sign['polymarket_support_count'])} "
        f"of {int(sign['comparison_count'])} states; exact p="
        f"{float(sign['exact_p_value']):.4f}, 95% lower bound "
        f"{float(sign['exact_95_ci_low']):.3f}.\n"
        f"- Direct poll audit rows supporting PM: "
        f"{int(direct['polymarket_support_count'])} of "
        f"{int(direct['comparison_count'])}.\n\n"
        "Boundary\n"
        f"- Full panel: poll-derived lower loss in "
        f"{int(full['poll_support_count'])} of {int(full['comparison_count'])} rows.\n"
        f"- Late high-distance subset: poll-derived lower loss in "
        f"{int(high['poll_support_count'])} of {int(high['comparison_count'])} rows.\n"
        f"- Broad many-cases claim proven: "
        f"{int(_summary_value(summary, 'broad_claim_proven'))}."
    )
    ax.text(
        0.02,
        0.98,
        text,
        va="top",
        ha="left",
        fontsize=10,
        color="#111827",
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _row_from_audit(
    *,
    result_id: str,
    result_label: str,
    result_role: str,
    source: pd.Series,
    supports: bool,
    contradicts: bool,
    allowed_statement: str,
) -> dict[str, Any]:
    return _row(
        result_id=result_id,
        result_label=result_label,
        result_role=result_role,
        comparison_scope=str(source["audit_id"]),
        comparison_unit=str(source["comparison_unit"]),
        comparison_count=int(source["comparison_count"]),
        state_count=int(source["state_count"]),
        pm_count=int(source["polymarket_support_count"]),
        poll_count=int(source["comparator_support_count"]),
        ties=int(source["tie_count"]),
        mean_pm=float(source["mean_polymarket_brier"]),
        mean_poll=float(source["mean_comparator_brier"]),
        advantage=float(source["mean_loss_advantage"]),
        exact_p=None,
        ci_low=None,
        supports=supports,
        contradicts=contradicts,
        allowed_statement=allowed_statement,
        limitation=str(source["limitation"]),
        artifacts=str(source["source_artifact"]),
    )


def _row(
    *,
    result_id: str,
    result_label: str,
    result_role: str,
    comparison_scope: str,
    comparison_unit: str,
    comparison_count: int,
    state_count: int,
    pm_count: int,
    poll_count: int,
    ties: int,
    mean_pm: float | None,
    mean_poll: float | None,
    advantage: float | None,
    exact_p: float | None,
    ci_low: float | None,
    supports: bool,
    contradicts: bool,
    allowed_statement: str,
    limitation: str,
    artifacts: str,
) -> dict[str, Any]:
    if comparison_count <= 0:
        raise ValueError("comparison_count must be positive")
    if pm_count + poll_count + ties != comparison_count:
        raise ValueError("support counts must add to comparison_count")
    return {
        "result_id": result_id,
        "result_label": result_label,
        "result_role": result_role,
        "comparison_scope": comparison_scope,
        "comparison_unit": comparison_unit,
        "comparison_count": comparison_count,
        "state_count": state_count,
        "polymarket_support_count": pm_count,
        "poll_support_count": poll_count,
        "tie_count": ties,
        "polymarket_support_share": pm_count / comparison_count,
        "mean_polymarket_brier": mean_pm,
        "mean_poll_brier": mean_poll,
        "mean_loss_advantage": advantage,
        "exact_p_value": exact_p,
        "exact_95_ci_low": ci_low,
        "supports_bounded_polymarket_statement": supports,
        "contradicts_broad_polymarket_statement": contradicts,
        "allowed_statement": allowed_statement,
        "limitation": limitation,
        "source_artifacts": artifacts,
    }


def _audit_row(frame: pd.DataFrame, audit_id: str) -> pd.Series:
    rows = frame.loc[frame["audit_id"] == audit_id]
    if len(rows) != 1:
        raise ValueError(f"H1 claim audit must contain one {audit_id!r} row")
    return rows.iloc[0]


def _result_row(frame: pd.DataFrame, result_id: str) -> pd.Series:
    rows = frame.loc[frame["result_id"] == result_id]
    if len(rows) != 1:
        raise ValueError(f"H1 poll result must contain one {result_id!r} row")
    return rows.iloc[0]


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


def _summary_value(frame: pd.DataFrame, summary_id: str) -> float:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    value = rows.iloc[0]
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _reject_forbidden_columns(frame: pd.DataFrame, label: str) -> None:
    lower_columns = [column.lower() for column in frame.columns]
    matches = [
        column
        for column in lower_columns
        if any(token in column for token in FORBIDDEN_COLUMN_TOKENS)
    ]
    if matches:
        raise ValueError(f"{label} contains forbidden columns: {matches}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-audit-input", type=Path, default=CLAIM_AUDIT_INPUT)
    parser.add_argument(
        "--claim-audit-summary-input",
        type=Path,
        default=CLAIM_AUDIT_SUMMARY_INPUT,
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
    parser.add_argument("--result-output", type=Path, default=RESULT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_poll_comparison_result_outputs(
            claim_audit_input=args.claim_audit_input,
            claim_audit_summary_input=args.claim_audit_summary_input,
            panel_competitiveness_input=args.panel_competitiveness_input,
            state_significance_input=args.state_significance_input,
            result_output=args.result_output,
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
