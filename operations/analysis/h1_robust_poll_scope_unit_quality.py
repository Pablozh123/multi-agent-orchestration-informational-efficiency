"""Aggregated-unit quality view for robust H1 poll scopes.

The row-level robust-scope quality diagnostic shows where Polymarket has lower
forecast loss than poll-derived probabilities. This module reduces repeated-row
dependence by aggregating the same robust scopes to state, state-month,
state-horizon, and horizon-tier units before comparing mean Brier loss.
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
import numpy as np
import pandas as pd
from scipy.stats import binomtest

from operations.analysis.h1_poll_scope_frontier import prepare_scope_cases
from operations.analysis.h1_state_poll_panel_competitiveness_diagnostic import (
    TIER_LABELS,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import CASE_INPUT
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


UNIT_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_unit_quality_units.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_unit_quality_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_unit_quality.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_unit_quality_metadata.json"

LOW_MIDDLE_TIERS: tuple[str, ...] = (
    "low_distance_tercile",
    "middle_distance_tercile",
)
SCOPE_SPECS: tuple[tuple[str, str, int, tuple[str, ...]], ...] = (
    (
        "largest_robust_lte120_low_middle",
        "<=120 days + low/middle poll distance",
        120,
        LOW_MIDDLE_TIERS,
    ),
    (
        "strongest_robust_lte90_low_middle",
        "<=90 days + low/middle poll distance",
        90,
        LOW_MIDDLE_TIERS,
    ),
)
UNIT_SPECS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("state", ("state",), "State"),
    ("state_month", ("state", "forecast_month"), "State-month"),
    ("state_horizon", ("state", "horizon_bin"), "State-horizon"),
    ("horizon_tier", ("horizon_bin", "competitiveness_tier"), "Horizon-tier"),
)

UNIT_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "unit_type",
    "unit_label",
    "unit_id",
    "state",
    "forecast_month",
    "horizon_bin",
    "horizon_label",
    "competitiveness_tier",
    "competitiveness_label",
    "row_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "aggregate_mean_supports_poll_derived",
    "majority_rows_support_polymarket",
    "majority_rows_support_poll_derived",
    "row_unit",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "unit_type",
    "unit_label",
    "unit_count",
    "polymarket_support_count",
    "poll_derived_support_count",
    "tie_count",
    "polymarket_support_share",
    "exact_binomial_p_value_greater",
    "exact_95_ci_low",
    "mean_unit_loss_advantage",
    "median_unit_loss_advantage",
    "min_unit_loss_advantage",
    "max_unit_loss_advantage",
    "all_units_support_polymarket",
    "broad_claim_supported",
    "limitation",
)


@dataclass(frozen=True)
class H1RobustPollScopeUnitQualityResult:
    """Summary of generated robust-scope unit-quality artifacts."""

    unit_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    unit_row_count: int
    summary_row_count: int
    largest_state_month_unit_count: int
    largest_state_month_polymarket_support_count: int
    strongest_state_month_unit_count: int
    strongest_state_month_polymarket_support_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "unit_path": str(self.unit_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "unit_row_count": self.unit_row_count,
            "summary_row_count": self.summary_row_count,
            "largest_state_month_unit_count": self.largest_state_month_unit_count,
            "largest_state_month_polymarket_support_count": (
                self.largest_state_month_polymarket_support_count
            ),
            "strongest_state_month_unit_count": self.strongest_state_month_unit_count,
            "strongest_state_month_polymarket_support_count": (
                self.strongest_state_month_polymarket_support_count
            ),
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_robust_poll_scope_unit_quality_outputs(
    *,
    case_input: Path = CASE_INPUT,
    unit_output: Path = UNIT_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1RobustPollScopeUnitQualityResult:
    """Generate robust poll-scope unit-quality CSVs, figure, and metadata."""

    cases = prepare_scope_cases(read_panel_cases(case_input))
    units = validate_unit_table(build_unit_table(cases))
    summary = validate_summary_table(build_summary_table(units))

    unit_output.parent.mkdir(parents=True, exist_ok=True)
    units.to_csv(unit_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_unit_quality_figure(units=units, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        units=units,
        summary=summary,
        case_input=case_input,
        unit_output=unit_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    largest_sm = _summary_row(summary, "largest_robust_lte120_low_middle", "state_month")
    strongest_sm = _summary_row(
        summary,
        "strongest_robust_lte90_low_middle",
        "state_month",
    )
    return H1RobustPollScopeUnitQualityResult(
        unit_path=unit_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        unit_row_count=int(len(units)),
        summary_row_count=int(len(summary)),
        largest_state_month_unit_count=int(largest_sm["unit_count"]),
        largest_state_month_polymarket_support_count=int(
            largest_sm["polymarket_support_count"]
        ),
        strongest_state_month_unit_count=int(strongest_sm["unit_count"]),
        strongest_state_month_polymarket_support_count=int(
            strongest_sm["polymarket_support_count"]
        ),
        broad_claim_proven=bool(summary["broad_claim_supported"].any()),
    )


def build_unit_table(cases: pd.DataFrame) -> pd.DataFrame:
    """Aggregate robust scope rows into coarser deterministic units."""

    rows: list[dict[str, Any]] = []
    for scope_id, scope_label, cutoff_days, tiers in SCOPE_SPECS:
        scoped = _scope_cases(cases, cutoff_days=cutoff_days, tiers=tiers)
        if scoped.empty:
            raise ValueError(f"robust scope must not be empty: {scope_id}")
        for unit_type, columns, unit_label in UNIT_SPECS:
            for keys, group in scoped.groupby(list(columns), sort=True):
                key_tuple = keys if isinstance(keys, tuple) else (keys,)
                unit_values = dict(zip(columns, key_tuple))
                rows.append(
                    _unit_row(
                        group,
                        scope_id=scope_id,
                        scope_label=scope_label,
                        unit_type=unit_type,
                        unit_label=unit_label,
                        unit_values=unit_values,
                    )
                )
    return pd.DataFrame(rows, columns=UNIT_COLUMNS)


def build_summary_table(units: pd.DataFrame) -> pd.DataFrame:
    """Summarize support across aggregated unit types."""

    rows: list[dict[str, Any]] = []
    for (scope_id, scope_label, unit_type, unit_label), group in units.groupby(
        ["scope_id", "scope_label", "unit_type", "unit_label"],
        sort=True,
    ):
        pm_count = int(group["aggregate_mean_supports_polymarket"].sum())
        poll_count = int(group["aggregate_mean_supports_poll_derived"].sum())
        tie_count = int(len(group) - pm_count - poll_count)
        test = _sign_test(pm_count=pm_count, poll_count=poll_count)
        advantages = group["mean_loss_advantage"]
        rows.append(
            {
                "scope_id": scope_id,
                "scope_label": scope_label,
                "unit_type": unit_type,
                "unit_label": unit_label,
                "unit_count": int(len(group)),
                "polymarket_support_count": pm_count,
                "poll_derived_support_count": poll_count,
                "tie_count": tie_count,
                "polymarket_support_share": (
                    pm_count / (pm_count + poll_count)
                    if pm_count + poll_count > 0
                    else float("nan")
                ),
                "exact_binomial_p_value_greater": test["p_value_greater"],
                "exact_95_ci_low": test["ci_low"],
                "mean_unit_loss_advantage": float(advantages.mean()),
                "median_unit_loss_advantage": float(advantages.median()),
                "min_unit_loss_advantage": float(advantages.min()),
                "max_unit_loss_advantage": float(advantages.max()),
                "all_units_support_polymarket": bool(pm_count == len(group)),
                "broad_claim_supported": False,
                "limitation": (
                    "Aggregated units reduce repeated daily rows but remain one "
                    "election context, not independent elections."
                ),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_unit_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate robust-scope unit table."""

    missing = sorted(set(UNIT_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"unit table missing columns: {missing}")
    _reject_forbidden_columns(frame, "unit table")
    normalized = frame.loc[:, list(UNIT_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("unit table must not be empty")
    for column in (
        "row_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    counts = (
        normalized["polymarket_lower_loss_count"]
        + normalized["poll_derived_lower_loss_count"]
        + normalized["tie_count"]
    )
    if not counts.eq(normalized["row_count"]).all():
        raise ValueError("unit lower-loss counts must add to row_count")
    if not normalized["polymarket_lower_loss_share"].between(0.0, 1.0).all():
        raise ValueError("polymarket_lower_loss_share must be in [0, 1]")
    return normalized


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate robust-scope unit summary table."""

    missing = sorted(set(SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"summary table missing columns: {missing}")
    _reject_forbidden_columns(frame, "summary table")
    normalized = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("summary table must not be empty")
    for column in (
        "unit_count",
        "polymarket_support_count",
        "poll_derived_support_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_support_share",
        "exact_binomial_p_value_greater",
        "exact_95_ci_low",
        "mean_unit_loss_advantage",
        "median_unit_loss_advantage",
        "min_unit_loss_advantage",
        "max_unit_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    return normalized


def write_unit_quality_figure(
    *,
    units: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write robust poll-scope unit-quality figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.2, 9.6))
    fig.suptitle(
        "H1 Robust Poll-Scope Unit Quality: Less-Repeated Evidence",
        fontsize=14,
        fontweight="bold",
    )
    _plot_support_heatmap(axes[0, 0], summary)
    _plot_state_month_scatter(axes[0, 1], units)
    _plot_advantage_distribution(axes[1, 0], units)
    _plot_statement(axes[1, 1], summary)
    fig.text(
        0.5,
        0.018,
        (
            "Positive advantage means poll-derived mean Brier minus Polymarket "
            "mean Brier is above zero. Units reduce repeated-day dependence, "
            "but remain one election context."
        ),
        ha="center",
        fontsize=8.8,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.055, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    cases: pd.DataFrame,
    units: pd.DataFrame,
    summary: pd.DataFrame,
    case_input: Path,
    unit_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for robust poll-scope unit quality."""

    largest_sm = _summary_row(summary, "largest_robust_lte120_low_middle", "state_month")
    strongest_sm = _summary_row(
        summary,
        "strongest_robust_lte90_low_middle",
        "state_month",
    )
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_robust_poll_scope_unit_quality",
            "calculation_scope": "deterministic_python_from_h1_state_date_poll_panel_cases",
            "unit_types": [unit_type for unit_type, _, _ in UNIT_SPECS],
            "scope_specs": [
                {
                    "scope_id": scope_id,
                    "scope_label": scope_label,
                    "horizon_cutoff_days": cutoff_days,
                    "included_competitiveness_tiers": list(tiers),
                }
                for scope_id, scope_label, cutoff_days, tiers in SCOPE_SPECS
            ],
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
        },
        "outputs": {
            "input_row_count": int(len(cases)),
            "unit_row_count": int(len(units)),
            "summary_row_count": int(len(summary)),
            "largest_state_month_unit_count": int(largest_sm["unit_count"]),
            "largest_state_month_polymarket_support_count": int(
                largest_sm["polymarket_support_count"]
            ),
            "largest_state_month_exact_binomial_p_value": float(
                largest_sm["exact_binomial_p_value_greater"]
            ),
            "strongest_state_month_unit_count": int(strongest_sm["unit_count"]),
            "strongest_state_month_polymarket_support_count": int(
                strongest_sm["polymarket_support_count"]
            ),
            "strongest_state_month_exact_binomial_p_value": float(
                strongest_sm["exact_binomial_p_value_greater"]
            ),
            "broad_claim_proven": bool(summary["broad_claim_supported"].any()),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "case_input": str(case_input),
            "units": str(unit_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "unit_aggregation_reduces_repeated_row_dependence": True,
            "state_month_units_are_not_independent_elections": True,
            "state_horizon_units_are_not_independent_elections": True,
            "one_election_context_only": True,
            "bounded_scope_quality_not_broad_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _scope_cases(
    cases: pd.DataFrame,
    *,
    cutoff_days: int,
    tiers: Sequence[str],
) -> pd.DataFrame:
    scoped = cases.loc[
        (cases["days_to_election"] <= cutoff_days)
        & (cases["competitiveness_tier"].isin(tiers))
    ].copy()
    return scoped.sort_values(["forecast_date", "state"]).reset_index(drop=True)


def _unit_row(
    group: pd.DataFrame,
    *,
    scope_id: str,
    scope_label: str,
    unit_type: str,
    unit_label: str,
    unit_values: dict[str, Any],
) -> dict[str, Any]:
    pm_count = int((group["lower_loss_source"] == "polymarket").sum())
    poll_count = int((group["lower_loss_source"] == "poll_derived_forecast").sum())
    tie_count = int(len(group) - pm_count - poll_count)
    mean_pm = float(group["polymarket_brier"].mean())
    mean_poll = float(group["poll_derived_brier"].mean())
    state = str(unit_values.get("state", ""))
    forecast_month = str(unit_values.get("forecast_month", ""))
    horizon_bin = str(unit_values.get("horizon_bin", ""))
    tier = str(unit_values.get("competitiveness_tier", ""))
    unit_id = "|".join(
        part for part in (state, forecast_month, horizon_bin, tier) if part
    )
    return {
        "scope_id": scope_id,
        "scope_label": scope_label,
        "unit_type": unit_type,
        "unit_label": unit_label,
        "unit_id": unit_id,
        "state": state,
        "forecast_month": forecast_month,
        "horizon_bin": horizon_bin,
        "horizon_label": str(_first_or_blank(group, "horizon_label", horizon_bin)),
        "competitiveness_tier": tier,
        "competitiveness_label": str(
            TIER_LABELS.get(tier, _first_or_blank(group, "competitiveness_label", ""))
        ),
        "row_count": int(len(group)),
        "polymarket_lower_loss_count": pm_count,
        "poll_derived_lower_loss_count": poll_count,
        "tie_count": tie_count,
        "polymarket_lower_loss_share": pm_count / len(group),
        "mean_polymarket_brier": mean_pm,
        "mean_poll_derived_brier": mean_poll,
        "mean_loss_advantage": mean_poll - mean_pm,
        "aggregate_mean_supports_polymarket": bool(mean_pm < mean_poll),
        "aggregate_mean_supports_poll_derived": bool(mean_poll < mean_pm),
        "majority_rows_support_polymarket": bool(pm_count > poll_count),
        "majority_rows_support_poll_derived": bool(poll_count > pm_count),
        "row_unit": "aggregated_state_date_forecast_rows",
        "limitation": (
            "Aggregated unit reduces repeated daily rows but remains one "
            "election context, not an independent election."
        ),
    }


def _plot_support_heatmap(ax: plt.Axes, summary: pd.DataFrame) -> None:
    scope_order = [
        "largest_robust_lte120_low_middle",
        "strongest_robust_lte90_low_middle",
    ]
    unit_order = ["state", "state_month", "state_horizon", "horizon_tier"]
    values = np.zeros((len(scope_order), len(unit_order)))
    labels: list[list[str]] = []
    for row_idx, scope_id in enumerate(scope_order):
        label_row = []
        for col_idx, unit_type in enumerate(unit_order):
            row = _summary_row(summary, scope_id, unit_type)
            share = float(row["polymarket_support_share"])
            values[row_idx, col_idx] = share
            label_row.append(
                f"{int(row['polymarket_support_count'])}/{int(row['unit_count'])}\n"
                f"p={float(row['exact_binomial_p_value_greater']):.2g}"
            )
        labels.append(label_row)
    image = ax.imshow(values, cmap="Blues", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(unit_order)), ["State", "State-month", "State-horizon", "Horizon-tier"])
    ax.set_yticks(
        np.arange(len(scope_order)),
        ["<=120 low/mid", "<=90 low/mid"],
    )
    ax.set_title("Polymarket support by aggregated unit")
    for row_idx in range(len(scope_order)):
        for col_idx in range(len(unit_order)):
            ax.text(
                col_idx,
                row_idx,
                labels[row_idx][col_idx],
                ha="center",
                va="center",
                fontsize=8.3,
                color="#f8fafc" if values[row_idx, col_idx] >= 0.78 else "#111827",
            )
    plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="PM support share")


def _plot_state_month_scatter(ax: plt.Axes, units: pd.DataFrame) -> None:
    largest = units.loc[
        (units["scope_id"] == "largest_robust_lte120_low_middle")
        & (units["unit_type"] == "state_month")
    ]
    colors = np.where(
        largest["aggregate_mean_supports_polymarket"],
        "#2563eb",
        "#dc2626",
    )
    ax.scatter(
        largest["mean_poll_derived_brier"],
        largest["mean_polymarket_brier"],
        s=36 + largest["row_count"] * 2.0,
        c=colors,
        alpha=0.82,
        edgecolor="#111827",
        linewidth=0.35,
    )
    max_value = float(
        max(
            largest["mean_poll_derived_brier"].max(),
            largest["mean_polymarket_brier"].max(),
        )
    )
    ax.plot([0, max_value * 1.08], [0, max_value * 1.08], "--", color="#6b7280")
    ax.set_xlim(0, max_value * 1.08)
    ax.set_ylim(0, max_value * 1.08)
    ax.set_xlabel("Poll-derived mean Brier")
    ax.set_ylabel("Polymarket mean Brier")
    ax.set_title("Largest robust scope: state-month paired Brier")
    ax.grid(True, alpha=0.24)
    ax.text(
        0.03,
        0.97,
        "Blue below diagonal = Polymarket lower mean Brier",
        transform=ax.transAxes,
        va="top",
        fontsize=8.2,
        color="#374151",
    )


def _plot_advantage_distribution(ax: plt.Axes, units: pd.DataFrame) -> None:
    unit_order = ["state", "state_month", "state_horizon", "horizon_tier"]
    scope_order = [
        ("largest_robust_lte120_low_middle", "<=120"),
        ("strongest_robust_lte90_low_middle", "<=90"),
    ]
    offsets = [-0.16, 0.16]
    rng = np.random.default_rng(20260611)
    for scope_idx, (scope_id, label) in enumerate(scope_order):
        color = "#2563eb" if scope_idx == 0 else "#7c3aed"
        for unit_idx, unit_type in enumerate(unit_order):
            rows = units.loc[
                (units["scope_id"] == scope_id)
                & (units["unit_type"] == unit_type),
                "mean_loss_advantage",
            ].to_numpy(dtype=float)
            x = (
                np.full(len(rows), unit_idx + offsets[scope_idx])
                + rng.uniform(-0.035, 0.035, len(rows))
            )
            ax.scatter(x, rows, color=color, alpha=0.68, s=22, label=label if unit_idx == 0 else None)
            ax.plot(
                [unit_idx + offsets[scope_idx] - 0.08, unit_idx + offsets[scope_idx] + 0.08],
                [np.median(rows), np.median(rows)],
                color="#111827",
                linewidth=1.2,
            )
    ax.axhline(0, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_xticks(np.arange(len(unit_order)), ["State", "State-month", "State-horizon", "Horizon-tier"])
    ax.set_ylabel("Mean loss advantage")
    ax.set_title("Unit-level Brier advantage distribution")
    ax.grid(True, axis="y", alpha=0.24)
    ax.legend(fontsize=8)


def _plot_statement(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    largest_state = _summary_row(summary, "largest_robust_lte120_low_middle", "state")
    largest_sm = _summary_row(summary, "largest_robust_lte120_low_middle", "state_month")
    strongest_state = _summary_row(summary, "strongest_robust_lte90_low_middle", "state")
    strongest_sm = _summary_row(summary, "strongest_robust_lte90_low_middle", "state_month")
    text = (
        "Less-repeated unit evidence\n"
        f"- <=120 low/mid: states {int(largest_state['polymarket_support_count'])}/"
        f"{int(largest_state['unit_count'])}, state-months "
        f"{int(largest_sm['polymarket_support_count'])}/"
        f"{int(largest_sm['unit_count'])}, p="
        f"{float(largest_sm['exact_binomial_p_value_greater']):.4f}.\n"
        f"- <=90 low/mid: states {int(strongest_state['polymarket_support_count'])}/"
        f"{int(strongest_state['unit_count'])}, state-months "
        f"{int(strongest_sm['polymarket_support_count'])}/"
        f"{int(strongest_sm['unit_count'])}, p="
        f"{float(strongest_sm['exact_binomial_p_value_greater']):.2g}.\n"
        f"- Median unit advantage <=120 state-months: "
        f"{float(largest_sm['median_unit_loss_advantage']):.4f}.\n"
        f"- Median unit advantage <=90 state-months: "
        f"{float(strongest_sm['median_unit_loss_advantage']):.4f}.\n\n"
        "Status: stronger bounded evidence; broad claim not_proven."
    )
    ax.text(
        0.02,
        0.97,
        text,
        va="top",
        fontsize=10,
        color="#111827",
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _summary_row(summary: pd.DataFrame, scope_id: str, unit_type: str) -> pd.Series:
    rows = summary.loc[
        (summary["scope_id"] == scope_id) & (summary["unit_type"] == unit_type)
    ]
    if len(rows) != 1:
        raise ValueError(f"summary row not found: {scope_id} / {unit_type}")
    return rows.iloc[0]


def _sign_test(*, pm_count: int, poll_count: int) -> dict[str, float]:
    trials = pm_count + poll_count
    if trials <= 0:
        return {"p_value_greater": float("nan"), "ci_low": float("nan")}
    result = binomtest(pm_count, trials, 0.5, alternative="greater")
    ci = binomtest(pm_count, trials).proportion_ci(
        confidence_level=0.95,
        method="exact",
    )
    return {"p_value_greater": float(result.pvalue), "ci_low": float(ci.low)}


def _first_or_blank(group: pd.DataFrame, column: str, default: object = "") -> object:
    if column not in group.columns:
        return default
    values = group[column].dropna()
    if values.empty:
        return default
    return values.iloc[0]


def _reject_forbidden_columns(frame: pd.DataFrame, label: str) -> None:
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"{label} contains forbidden raw-trade columns: {forbidden}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--unit-output", type=Path, default=UNIT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_robust_poll_scope_unit_quality_outputs(
            case_input=args.case_input,
            unit_output=args.unit_output,
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
