"""Scope frontier for the H1 Polymarket-vs-poll panel.

This module scans transparent horizon and poll-distance scopes in the existing
H1 state-date poll panel. It does not add new markets or recompute the source
panel. The goal is to show how far the Polymarket-supporting poll comparison
can be widened before counterexamples dominate.
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

from operations.analysis.h1_state_poll_panel_competitiveness_diagnostic import (
    TIER_ORDER,
    add_competitiveness_columns,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    CASE_INPUT,
    add_horizon_columns,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


FRONTIER_OUTPUT = RESULTS_DIR / "h1_poll_scope_frontier.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_poll_scope_frontier_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_poll_scope_frontier.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_poll_scope_frontier_metadata.json"

HORIZON_CUTOFFS: tuple[tuple[int, str, str], ...] = (
    (60, "lte_60_days", "<=60 days"),
    (90, "lte_90_days", "<=90 days"),
    (120, "lte_120_days", "<=120 days"),
    (150, "lte_150_days", "<=150 days"),
    (180, "lte_180_days", "<=180 days"),
    (10_000, "full_panel", "Full panel"),
)

TIER_SCOPES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("all_distances", TIER_ORDER, "All distances"),
    (
        "low_middle_distance",
        ("low_distance_tercile", "middle_distance_tercile"),
        "Low/middle distance",
    ),
    ("low_distance", ("low_distance_tercile",), "Low distance"),
    ("middle_distance", ("middle_distance_tercile",), "Middle distance"),
    ("high_distance", ("high_distance_tercile",), "High distance"),
)

FRONTIER_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "horizon_cutoff_days",
    "horizon_scope",
    "horizon_label",
    "tier_scope",
    "tier_label",
    "included_tiers",
    "row_count",
    "state_count",
    "state_month_unit_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "state_month_polymarket_support_count",
    "state_month_poll_support_count",
    "state_month_tie_count",
    "state_month_polymarket_support_share",
    "state_month_exact_p_value",
    "state_month_exact_95_ci_low",
    "row_majority_supports_polymarket",
    "mean_supports_polymarket",
    "state_month_supports_polymarket",
    "frontier_status",
    "allowed_statement",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

MIN_STATE_MONTH_UNITS_FOR_ROBUST_STATUS = 5
ROBUST_P_VALUE_THRESHOLD = 0.05


@dataclass(frozen=True)
class H1PollScopeFrontierResult:
    """Summary of generated H1 scope-frontier artifacts."""

    frontier_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    frontier_row_count: int
    robust_scope_count: int
    largest_robust_scope_id: str
    largest_robust_row_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "frontier_path": str(self.frontier_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "frontier_row_count": self.frontier_row_count,
            "robust_scope_count": self.robust_scope_count,
            "largest_robust_scope_id": self.largest_robust_scope_id,
            "largest_robust_row_count": self.largest_robust_row_count,
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_poll_scope_frontier_outputs(
    *,
    case_input: Path = CASE_INPUT,
    frontier_output: Path = FRONTIER_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1PollScopeFrontierResult:
    """Generate H1 poll-scope frontier CSV, summary, figure, and metadata."""

    cases = prepare_scope_cases(read_panel_cases(case_input))
    frontier = validate_frontier_table(build_frontier_table(cases))
    summary = validate_summary_table(build_summary_table(frontier))

    frontier_output.parent.mkdir(parents=True, exist_ok=True)
    frontier.to_csv(frontier_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_frontier_figure(frontier=frontier, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        frontier=frontier,
        summary=summary,
        case_input=case_input,
        frontier_output=frontier_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1PollScopeFrontierResult(
        frontier_path=frontier_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        frontier_row_count=int(len(frontier)),
        robust_scope_count=int(_summary_value(summary, "robust_scope_count")),
        largest_robust_scope_id=_summary_text(summary, "largest_robust_scope_id"),
        largest_robust_row_count=int(
            _summary_value(summary, "largest_robust_row_count")
        ),
        broad_claim_proven=bool(_summary_value(summary, "broad_claim_proven")),
    )


def prepare_scope_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and augment minimal H1 panel case columns."""

    required = {
        "state",
        "forecast_date",
        "poll_derived_probability",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
        "lower_loss_source",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 scope-frontier cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"H1 scope-frontier cases contain forbidden columns: {forbidden}")
    normalized = frame.copy()
    for column in (
        "poll_derived_probability",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if not normalized["poll_derived_probability"].between(0.0, 1.0).all():
        raise ValueError("poll_derived_probability must be in [0, 1]")
    allowed_sources = {"polymarket", "poll_derived_forecast", "tie"}
    unknown = sorted(set(normalized["lower_loss_source"].astype(str)) - allowed_sources)
    if unknown:
        raise ValueError(f"unknown lower_loss_source values: {unknown}")
    normalized = add_competitiveness_columns(add_horizon_columns(normalized))
    normalized["forecast_month"] = (
        pd.to_datetime(normalized["forecast_date"], errors="raise")
        .dt.to_period("M")
        .astype(str)
    )
    return normalized


def build_frontier_table(cases: pd.DataFrame) -> pd.DataFrame:
    """Build a horizon-cutoff x poll-distance scope frontier table."""

    rows: list[dict[str, Any]] = []
    for cutoff_days, horizon_scope, horizon_label in HORIZON_CUTOFFS:
        horizon_cases = cases.loc[cases["days_to_election"] <= cutoff_days]
        if horizon_cases.empty:
            continue
        for tier_scope, tiers, tier_label in TIER_SCOPES:
            group = horizon_cases.loc[horizon_cases["competitiveness_tier"].isin(tiers)]
            if group.empty:
                continue
            rows.append(
                _frontier_row(
                    group=group,
                    cutoff_days=cutoff_days,
                    horizon_scope=horizon_scope,
                    horizon_label=horizon_label,
                    tier_scope=tier_scope,
                    tiers=tiers,
                    tier_label=tier_label,
                )
            )
    return pd.DataFrame(rows, columns=FRONTIER_COLUMNS)


def build_summary_table(frontier: pd.DataFrame) -> pd.DataFrame:
    """Build compact reporting rows for the scope frontier."""

    robust = frontier.loc[frontier["frontier_status"] == "robust_support"].copy()
    if robust.empty:
        largest = None
        strongest = None
    else:
        largest = robust.sort_values(
            ["row_count", "state_month_exact_p_value"],
            ascending=[False, True],
        ).iloc[0]
        strongest = robust.sort_values(
            ["state_month_exact_p_value", "row_count"],
            ascending=[True, False],
        ).iloc[0]
    lte_90_all = _frontier_row_by_scope(frontier, "lte_90_days", "all_distances")
    lte_90_low_mid = _frontier_row_by_scope(
        frontier,
        "lte_90_days",
        "low_middle_distance",
    )
    full_panel = _frontier_row_by_scope(frontier, "full_panel", "all_distances")
    rows = [
        _summary_row(
            "frontier_row_count",
            int(len(frontier)),
            "rows",
            "Horizon-cutoff x poll-distance scope rows in the frontier table.",
        ),
        _summary_row(
            "robust_scope_count",
            int(len(robust)),
            "scopes",
            (
                "Scopes with row majority, positive mean loss advantage, and "
                "state-month exact p < 0.05."
            ),
        ),
        *_largest_scope_rows(largest),
        *_strongest_scope_rows(strongest),
        _summary_row(
            "lte_90_all_row_count",
            int(lte_90_all["row_count"]),
            "state-date rows",
            "Rows in the <=90-day all-distance scope.",
        ),
        _summary_row(
            "lte_90_all_polymarket_support_count",
            int(lte_90_all["polymarket_lower_loss_count"]),
            "state-date rows",
            "Rows where Polymarket has lower loss in the <=90-day all-distance scope.",
        ),
        _summary_row(
            "lte_90_all_polymarket_support_share",
            float(lte_90_all["polymarket_lower_loss_share"]),
            "share",
            "Polymarket lower-loss share in the <=90-day all-distance scope.",
        ),
        _summary_row(
            "lte_90_all_state_month_p_value",
            float(lte_90_all["state_month_exact_p_value"]),
            "p_value",
            "State-month exact p-value in the <=90-day all-distance scope.",
        ),
        _summary_row(
            "lte_90_low_middle_row_count",
            int(lte_90_low_mid["row_count"]),
            "state-date rows",
            "Rows in the <=90-day low/middle-distance scope.",
        ),
        _summary_row(
            "lte_90_low_middle_polymarket_support_count",
            int(lte_90_low_mid["polymarket_lower_loss_count"]),
            "state-date rows",
            (
                "Rows where Polymarket has lower loss in the <=90-day "
                "low/middle-distance scope."
            ),
        ),
        _summary_row(
            "lte_90_low_middle_state_month_support_count",
            int(lte_90_low_mid["state_month_polymarket_support_count"]),
            "state_month units",
            "State-month units supporting Polymarket in the <=90-day low/middle scope.",
        ),
        _summary_row(
            "lte_90_low_middle_state_month_count",
            int(lte_90_low_mid["state_month_unit_count"]),
            "state_month units",
            "State-month units in the <=90-day low/middle scope.",
        ),
        _summary_row(
            "lte_90_low_middle_state_month_p_value",
            float(lte_90_low_mid["state_month_exact_p_value"]),
            "p_value",
            "State-month exact p-value in the <=90-day low/middle scope.",
        ),
        _summary_row(
            "full_panel_row_count",
            int(full_panel["row_count"]),
            "state-date rows",
            "Rows in the full all-distance panel.",
        ),
        _summary_row(
            "full_panel_polymarket_support_count",
            int(full_panel["polymarket_lower_loss_count"]),
            "state-date rows",
            "Rows where Polymarket has lower loss in the full all-distance panel.",
        ),
        _summary_row(
            "full_panel_poll_support_count",
            int(full_panel["poll_derived_lower_loss_count"]),
            "state-date rows",
            "Rows where poll-derived probability has lower loss in the full panel.",
        ),
        _summary_row(
            "broad_claim_proven",
            0,
            "binary",
            "The broad many-cases or many-elections claim remains unproven.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            (
                "Current frontier supports bounded poll statements and shows "
                "where they stop."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_frontier_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the generated scope-frontier table."""

    missing = [column for column in FRONTIER_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 scope frontier missing columns: {missing}")
    normalized = frame.loc[:, list(FRONTIER_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("H1 scope frontier must not be empty")
    if normalized["scope_id"].duplicated().any():
        raise ValueError("scope_id values must be unique")
    for column in (
        "horizon_cutoff_days",
        "row_count",
        "state_count",
        "state_month_unit_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
        "state_month_polymarket_support_count",
        "state_month_poll_support_count",
        "state_month_tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
        "state_month_polymarket_support_share",
        "state_month_exact_p_value",
        "state_month_exact_95_ci_low",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["poll_derived_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["row_count"]
    ).any():
        raise ValueError("row lower-loss counts must add to row_count")
    if (
        normalized["state_month_polymarket_support_count"]
        + normalized["state_month_poll_support_count"]
        + normalized["state_month_tie_count"]
        != normalized["state_month_unit_count"]
    ).any():
        raise ValueError("state-month support counts must add to state_month_unit_count")
    allowed = {
        "robust_support",
        "directional_support",
        "mixed_support",
        "contradicted_or_unsupported",
    }
    unknown = sorted(set(normalized["frontier_status"]) - allowed)
    if unknown:
        raise ValueError(f"unknown frontier_status values: {unknown}")
    return normalized.sort_values(["horizon_cutoff_days", "tier_scope"]).reset_index(drop=True)


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact summary rows."""

    missing = [column for column in SUMMARY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 scope frontier summary missing columns: {missing}")
    normalized = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("H1 scope frontier summary must not be empty")
    if normalized["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return normalized


def write_frontier_figure(
    *,
    frontier: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a scope-frontier figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.8, 9.8))
    fig.suptitle(
        "H1 poll-scope frontier: where the Polymarket advantage holds",
        fontsize=14,
        fontweight="bold",
    )
    _plot_row_share_heatmap(axes[0, 0], frontier)
    _plot_state_month_heatmap(axes[0, 1], frontier)
    _plot_robust_scopes(axes[1, 0], frontier)
    _plot_statement(axes[1, 1], summary)
    fig.text(
        0.5,
        0.012,
        (
            "Robust support = row majority + positive mean loss advantage + "
            "state-month exact p < 0.05. Units are repeated forecasts inside "
            "one election context, not independent elections."
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
    cases: pd.DataFrame,
    frontier: pd.DataFrame,
    summary: pd.DataFrame,
    case_input: Path,
    frontier_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the scope-frontier output."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_poll_scope_frontier",
            "calculation_scope": "deterministic_python_from_h1_state_date_poll_panel_cases",
            "horizon_cutoffs": [
                {
                    "horizon_cutoff_days": cutoff,
                    "horizon_scope": scope,
                    "horizon_label": label,
                }
                for cutoff, scope, label in HORIZON_CUTOFFS
            ],
            "tier_scopes": [
                {
                    "tier_scope": scope,
                    "included_tiers": list(tiers),
                    "tier_label": label,
                }
                for scope, tiers, label in TIER_SCOPES
            ],
            "competitiveness_distance": "abs(poll_derived_probability - 0.5)",
            "tier_method": "uses_existing quantile-derived poll-distance terciles",
            "robust_support_rule": (
                "row majority and positive mean loss advantage and state-month "
                "exact one-sided binomial p-value < 0.05"
            ),
            "minimum_state_month_units_for_robust_status": (
                MIN_STATE_MONTH_UNITS_FOR_ROBUST_STATUS
            ),
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "input_row_count": int(len(cases)),
            "frontier_row_count": int(len(frontier)),
            "robust_scope_count": int(_summary_value(summary, "robust_scope_count")),
            "largest_robust_scope_id": _summary_text(summary, "largest_robust_scope_id"),
            "largest_robust_row_count": int(
                _summary_value(summary, "largest_robust_row_count")
            ),
            "broad_claim_proven": bool(_summary_value(summary, "broad_claim_proven")),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {
            "case_input": str(case_input),
            "frontier": str(frontier_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "rows_repeat_resolved_state_outcomes": True,
            "state_month_units_are_not_independent_elections": True,
            "frontier_is_scope_sensitivity_not_new_data": True,
            "low_middle_scope_excludes_high_distance_counterexamples": True,
            "full_panel_still_contradicts_broad_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _frontier_row(
    *,
    group: pd.DataFrame,
    cutoff_days: int,
    horizon_scope: str,
    horizon_label: str,
    tier_scope: str,
    tiers: Sequence[str],
    tier_label: str,
) -> dict[str, Any]:
    pm_lower = _lower_loss_count(group, "polymarket")
    poll_lower = _lower_loss_count(group, "poll_derived_forecast")
    tie_count = _lower_loss_count(group, "tie")
    row_count = int(len(group))
    units = _state_month_units(group)
    unit_counts = units["support_source"].value_counts()
    pm_units = int(unit_counts.get("polymarket", 0))
    poll_units = int(unit_counts.get("poll_derived_forecast", 0))
    tie_units = int(unit_counts.get("tie", 0))
    unit_count = int(len(units))
    exact = binomtest(pm_units, unit_count, 0.5, alternative="greater")
    ci_low = exact.proportion_ci(confidence_level=0.95, method="exact").low
    row_majority = pm_lower > poll_lower and pm_lower > row_count / 2.0
    mean_advantage = float(group["loss_advantage"].mean())
    mean_support = mean_advantage > 0.0
    state_month_support = (
        pm_units > poll_units
        and pm_units > unit_count / 2.0
        and unit_count >= MIN_STATE_MONTH_UNITS_FOR_ROBUST_STATUS
    )
    status = _frontier_status(
        row_majority=row_majority,
        mean_support=mean_support,
        state_month_support=state_month_support,
        state_month_p_value=float(exact.pvalue),
    )
    scope_id = f"{horizon_scope}_{tier_scope}"
    return {
        "scope_id": scope_id,
        "horizon_cutoff_days": int(cutoff_days),
        "horizon_scope": horizon_scope,
        "horizon_label": horizon_label,
        "tier_scope": tier_scope,
        "tier_label": tier_label,
        "included_tiers": ",".join(tiers),
        "row_count": row_count,
        "state_count": int(group["state"].nunique()),
        "state_month_unit_count": unit_count,
        "polymarket_lower_loss_count": pm_lower,
        "poll_derived_lower_loss_count": poll_lower,
        "tie_count": tie_count,
        "polymarket_lower_loss_share": pm_lower / row_count,
        "mean_polymarket_brier": float(group["polymarket_brier"].mean()),
        "mean_poll_derived_brier": float(group["poll_derived_brier"].mean()),
        "mean_loss_advantage": mean_advantage,
        "state_month_polymarket_support_count": pm_units,
        "state_month_poll_support_count": poll_units,
        "state_month_tie_count": tie_units,
        "state_month_polymarket_support_share": pm_units / unit_count,
        "state_month_exact_p_value": float(exact.pvalue),
        "state_month_exact_95_ci_low": float(ci_low),
        "row_majority_supports_polymarket": bool(row_majority),
        "mean_supports_polymarket": bool(mean_support),
        "state_month_supports_polymarket": bool(state_month_support),
        "frontier_status": status,
        "allowed_statement": _allowed_statement(
            status=status,
            horizon_label=horizon_label,
            tier_label=tier_label,
            pm_lower=pm_lower,
            poll_lower=poll_lower,
            row_count=row_count,
            pm_units=pm_units,
            unit_count=unit_count,
            p_value=float(exact.pvalue),
        ),
        "limitation": (
            "Rows are repeated state-date forecasts from one election context; "
            "frontier rows test scope sensitivity, not independent many-election proof."
        ),
    }


def _state_month_units(group: pd.DataFrame) -> pd.DataFrame:
    units = (
        group.groupby(["state", "forecast_month"], as_index=False)
        .agg(
            row_count=("lower_loss_source", "size"),
            polymarket_lower_loss_count=(
                "lower_loss_source",
                lambda values: int((values == "polymarket").sum()),
            ),
            poll_derived_lower_loss_count=(
                "lower_loss_source",
                lambda values: int((values == "poll_derived_forecast").sum()),
            ),
            mean_polymarket_brier=("polymarket_brier", "mean"),
            mean_poll_derived_brier=("poll_derived_brier", "mean"),
        )
        .reset_index(drop=True)
    )
    conditions = [
        units["mean_polymarket_brier"] < units["mean_poll_derived_brier"],
        units["mean_poll_derived_brier"] < units["mean_polymarket_brier"],
    ]
    units["support_source"] = np.select(
        conditions,
        ["polymarket", "poll_derived_forecast"],
        default="tie",
    )
    return units


def _frontier_status(
    *,
    row_majority: bool,
    mean_support: bool,
    state_month_support: bool,
    state_month_p_value: float,
) -> str:
    if (
        row_majority
        and mean_support
        and state_month_support
        and state_month_p_value < ROBUST_P_VALUE_THRESHOLD
    ):
        return "robust_support"
    if row_majority and mean_support:
        return "directional_support"
    if row_majority or mean_support or state_month_support:
        return "mixed_support"
    return "contradicted_or_unsupported"


def _allowed_statement(
    *,
    status: str,
    horizon_label: str,
    tier_label: str,
    pm_lower: int,
    poll_lower: int,
    row_count: int,
    pm_units: int,
    unit_count: int,
    p_value: float,
) -> str:
    if status == "robust_support":
        return (
            f"Robust bounded support in {horizon_label}, {tier_label}: "
            f"Polymarket lower loss in {pm_lower} of {row_count} rows and "
            f"{pm_units} of {unit_count} state-month units (p={p_value:.3g})."
        )
    if status == "directional_support":
        return (
            f"Directional support in {horizon_label}, {tier_label}: "
            f"Polymarket lower loss in {pm_lower} of {row_count} rows, but "
            "state-month evidence is not significant at 0.05."
        )
    return (
        f"No robust Polymarket support in {horizon_label}, {tier_label}: "
        f"Polymarket lower loss in {pm_lower} rows and poll-derived lower loss "
        f"in {poll_lower} rows."
    )


def _largest_scope_rows(row: pd.Series | None) -> list[dict[str, Any]]:
    if row is None:
        return [
            _summary_row("largest_robust_scope_id", "", "scope", "No robust scope found."),
            _summary_row("largest_robust_row_count", 0, "state-date rows", "No robust scope found."),
        ]
    return [
        _summary_row(
            "largest_robust_scope_id",
            str(row["scope_id"]),
            "scope",
            "Largest robust frontier scope by state-date row count.",
        ),
        _summary_row(
            "largest_robust_horizon_label",
            str(row["horizon_label"]),
            "scope",
            "Horizon label for the largest robust frontier scope.",
        ),
        _summary_row(
            "largest_robust_tier_label",
            str(row["tier_label"]),
            "scope",
            "Poll-distance tier label for the largest robust frontier scope.",
        ),
        _summary_row(
            "largest_robust_row_count",
            int(row["row_count"]),
            "state-date rows",
            "State-date rows in the largest robust frontier scope.",
        ),
        _summary_row(
            "largest_robust_polymarket_support_count",
            int(row["polymarket_lower_loss_count"]),
            "state-date rows",
            "Rows where Polymarket has lower loss in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_poll_support_count",
            int(row["poll_derived_lower_loss_count"]),
            "state-date rows",
            "Rows where poll-derived probability has lower loss in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_polymarket_support_share",
            float(row["polymarket_lower_loss_share"]),
            "share",
            "Polymarket lower-loss share in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_state_count",
            int(row["state_count"]),
            "states",
            "States in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_state_month_polymarket_support_count",
            int(row["state_month_polymarket_support_count"]),
            "state_month units",
            "State-month units supporting Polymarket in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_state_month_count",
            int(row["state_month_unit_count"]),
            "state_month units",
            "State-month units in the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_state_month_p_value",
            float(row["state_month_exact_p_value"]),
            "p_value",
            "State-month exact p-value for the largest robust scope.",
        ),
        _summary_row(
            "largest_robust_mean_loss_advantage",
            float(row["mean_loss_advantage"]),
            "brier_score",
            "Mean poll-derived minus Polymarket Brier in the largest robust scope.",
        ),
    ]


def _strongest_scope_rows(row: pd.Series | None) -> list[dict[str, Any]]:
    if row is None:
        return []
    return [
        _summary_row(
            "strongest_robust_scope_id",
            str(row["scope_id"]),
            "scope",
            "Robust scope with the lowest state-month exact p-value.",
        ),
        _summary_row(
            "strongest_robust_row_count",
            int(row["row_count"]),
            "state-date rows",
            "Rows in the strongest robust frontier scope.",
        ),
        _summary_row(
            "strongest_robust_state_month_p_value",
            float(row["state_month_exact_p_value"]),
            "p_value",
            "Lowest state-month exact p-value among robust scopes.",
        ),
    ]


def _plot_row_share_heatmap(ax: plt.Axes, frontier: pd.DataFrame) -> None:
    matrix = _frontier_matrix(frontier, "polymarket_lower_loss_share")
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_title("Polymarket lower-loss share")
    _format_frontier_axis(ax)
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            if np.isnan(value):
                continue
            ax.text(col_idx, row_idx, f"{value:.0%}", ha="center", va="center", fontsize=7.8)
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)


def _plot_state_month_heatmap(ax: plt.Axes, frontier: pd.DataFrame) -> None:
    matrix = _frontier_matrix(frontier, "state_month_polymarket_support_share")
    p_values = _frontier_matrix(frontier, "state_month_exact_p_value")
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_title("State-month support share")
    _format_frontier_axis(ax)
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            if np.isnan(value):
                continue
            star = "*" if p_values[row_idx, col_idx] < ROBUST_P_VALUE_THRESHOLD else ""
            ax.text(
                col_idx,
                row_idx,
                f"{value:.0%}{star}",
                ha="center",
                va="center",
                fontsize=7.8,
            )
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)


def _plot_robust_scopes(ax: plt.Axes, frontier: pd.DataFrame) -> None:
    robust = frontier.loc[frontier["frontier_status"] == "robust_support"].copy()
    if robust.empty:
        ax.axis("off")
        ax.text(0.05, 0.8, "No robust scopes found.", fontsize=11)
        return
    robust = robust.sort_values("row_count", ascending=True).tail(8)
    labels = [
        f"{row.horizon_label}\n{row.tier_label.replace(' distance', '')}"
        for row in robust.itertuples()
    ]
    ax.barh(labels, robust["row_count"], color="#2563eb")
    ax.set_title("Robust scopes by row coverage")
    ax.set_xlabel("State-date rows")
    ax.grid(True, axis="x", alpha=0.22)
    for idx, row in enumerate(robust.itertuples()):
        ax.text(
            row.row_count + robust["row_count"].max() * 0.015,
            idx,
            f"{row.polymarket_lower_loss_count}/{row.row_count}",
            va="center",
            fontsize=8,
        )


def _plot_statement(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "Frontier result\n"
        f"- Largest robust scope: {_summary_text(summary, 'largest_robust_horizon_label')}, "
        f"{_summary_text(summary, 'largest_robust_tier_label')}.\n"
        f"- PM lower loss: {_int_summary(summary, 'largest_robust_polymarket_support_count')}/"
        f"{_int_summary(summary, 'largest_robust_row_count')} rows "
        f"({_summary_value(summary, 'largest_robust_polymarket_support_share') * 100:.1f}%).\n"
        f"- State-month: "
        f"{_int_summary(summary, 'largest_robust_state_month_polymarket_support_count')}/"
        f"{_int_summary(summary, 'largest_robust_state_month_count')} "
        f"(p={_summary_value(summary, 'largest_robust_state_month_p_value'):.3g}).\n\n"
        "Strongest bounded scope\n"
        f"- {_summary_text(summary, 'strongest_robust_scope_id')}: "
        f"{_int_summary(summary, 'strongest_robust_row_count')} rows, "
        f"p={_summary_value(summary, 'strongest_robust_state_month_p_value'):.2g}.\n\n"
        "Boundary\n"
        f"- <=90 all distances: "
        f"{_int_summary(summary, 'lte_90_all_polymarket_support_count')}/"
        f"{_int_summary(summary, 'lte_90_all_row_count')} rows, "
        f"state-month p={_summary_value(summary, 'lte_90_all_state_month_p_value'):.3g}.\n"
        f"- Full panel: PM "
        f"{_int_summary(summary, 'full_panel_polymarket_support_count')}/"
        f"{_int_summary(summary, 'full_panel_row_count')}, poll-derived "
        f"{_int_summary(summary, 'full_panel_poll_support_count')}/"
        f"{_int_summary(summary, 'full_panel_row_count')}.\n\n"
        "Status: broad claim still not_proven."
    )
    ax.text(
        0.02,
        0.97,
        text,
        va="top",
        fontsize=10,
        color="#111827",
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _frontier_matrix(frontier: pd.DataFrame, value_column: str) -> np.ndarray:
    pivot = frontier.pivot(
        index="horizon_scope",
        columns="tier_scope",
        values=value_column,
    ).reindex(
        index=[scope for _, scope, _ in HORIZON_CUTOFFS],
        columns=[scope for scope, _, _ in TIER_SCOPES],
    )
    return pivot.to_numpy(dtype=float)


def _format_frontier_axis(ax: plt.Axes) -> None:
    ax.set_xticks(
        range(len(TIER_SCOPES)),
        [
            "All\ndist.",
            "Low/middle\ndist.",
            "Low\ndist.",
            "Middle\ndist.",
            "High\ndist.",
        ],
        rotation=0,
    )
    ax.set_yticks(
        range(len(HORIZON_CUTOFFS)),
        [label for _, _, label in HORIZON_CUTOFFS],
    )


def _frontier_row_by_scope(
    frontier: pd.DataFrame,
    horizon_scope: str,
    tier_scope: str,
) -> pd.Series:
    rows = frontier.loc[
        (frontier["horizon_scope"] == horizon_scope)
        & (frontier["tier_scope"] == tier_scope)
    ]
    if len(rows) != 1:
        raise ValueError(f"frontier scope not found: {horizon_scope}/{tier_scope}")
    return rows.iloc[0]


def _lower_loss_count(frame: pd.DataFrame, source: str) -> int:
    return int((frame["lower_loss_source"] == source).sum())


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
    return float(rows.iloc[0])


def _summary_text(frame: pd.DataFrame, summary_id: str) -> str:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return str(rows.iloc[0])


def _int_summary(frame: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(frame, summary_id))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--frontier-output", type=Path, default=FRONTIER_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_poll_scope_frontier_outputs(
            case_input=args.case_input,
            frontier_output=args.frontier_output,
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
