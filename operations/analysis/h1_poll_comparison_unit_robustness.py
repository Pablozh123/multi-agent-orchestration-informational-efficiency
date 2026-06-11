"""Aggregate the H1 poll comparison into less repeated diagnostic units.

The focused H1 poll-comparison result shows strong support in state-date rows.
This module checks whether that result survives coarser deterministic units
such as state, state-month, state-horizon, and horizon-tier. It reads the
existing H1 state-date poll panel only and keeps the full-panel/high-distance
counterexamples visible.
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
from scipy.stats import binomtest

from operations.analysis.h1_state_poll_panel_competitiveness_diagnostic import (
    TIER_LABELS,
    add_competitiveness_columns,
)
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    add_horizon_columns,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import (
    read_panel_cases,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


CASE_INPUT = RESULTS_DIR / "h1_state_poll_panel_cases.csv"
UNIT_OUTPUT = RESULTS_DIR / "h1_poll_comparison_unit_robustness_units.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_poll_comparison_unit_robustness_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_poll_comparison_unit_robustness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_poll_comparison_unit_robustness_metadata.json"

PRIMARY_SCOPE_ID = "late_low_middle_poll_distance"
FULL_PANEL_SCOPE_ID = "full_state_date_poll_panel"
HIGH_DISTANCE_SCOPE_ID = "late_high_poll_distance"
PRIMARY_TIERS = ("low_distance_tercile", "middle_distance_tercile")

UNIT_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "unit_type",
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
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
    "aggregate_mean_supports_poll_derived",
    "majority_rows_support_poll_derived",
    "row_unit",
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
class H1PollComparisonUnitRobustnessResult:
    """Summary of generated H1 unit-robustness artifacts."""

    unit_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    unit_row_count: int
    primary_state_month_unit_count: int
    primary_state_month_polymarket_support_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "unit_path": str(self.unit_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "unit_row_count": self.unit_row_count,
            "primary_state_month_unit_count": self.primary_state_month_unit_count,
            "primary_state_month_polymarket_support_count": (
                self.primary_state_month_polymarket_support_count
            ),
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_poll_comparison_unit_robustness_outputs(
    *,
    case_input: Path = CASE_INPUT,
    unit_output: Path = UNIT_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1PollComparisonUnitRobustnessResult:
    """Generate unit table, compact summary, figure, and metadata."""

    cases = prepare_cases(read_panel_cases(case_input))
    units = validate_unit_table(build_unit_table(cases))
    summary = validate_summary_table(build_summary_table(cases, units))

    unit_output.parent.mkdir(parents=True, exist_ok=True)
    units.to_csv(unit_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_unit_robustness_figure(units=units, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        units=units,
        summary=summary,
        source_paths={
            "case_input": case_input,
            "unit_output": unit_output,
            "summary_output": summary_output,
            "figure_output": figure_output,
        },
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1PollComparisonUnitRobustnessResult(
        unit_path=unit_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        unit_row_count=int(len(units)),
        primary_state_month_unit_count=int(
            _summary_value(summary, "primary_state_month_unit_count")
        ),
        primary_state_month_polymarket_support_count=int(
            _summary_value(summary, "primary_state_month_polymarket_support_count")
        ),
        broad_claim_proven=bool(_summary_value(summary, "broad_claim_proven")),
    )


def prepare_cases(cases: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic scope and aggregation fields to validated panel rows."""

    frame = add_competitiveness_columns(add_horizon_columns(cases)).copy()
    _reject_forbidden_columns(frame, "H1 poll comparison robustness cases")
    frame["forecast_month"] = frame["forecast_date"].dt.to_period("M").astype(str)
    frame["scope_primary"] = (
        (frame["days_to_election"] <= 90)
        & frame["competitiveness_tier"].isin(PRIMARY_TIERS)
    )
    frame["scope_late_high_distance"] = (
        (frame["days_to_election"] <= 90)
        & (frame["competitiveness_tier"] == "high_distance_tercile")
    )
    return frame


def build_unit_table(cases: pd.DataFrame) -> pd.DataFrame:
    """Build unit-level support rows for primary and counterexample scopes."""

    scopes = {
        PRIMARY_SCOPE_ID: cases.loc[cases["scope_primary"]],
        FULL_PANEL_SCOPE_ID: cases,
        HIGH_DISTANCE_SCOPE_ID: cases.loc[cases["scope_late_high_distance"]],
    }
    unit_specs: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("state", ("state",)),
        ("state_month", ("state", "forecast_month")),
        ("state_horizon", ("state", "horizon_bin")),
        ("horizon_tier", ("horizon_bin", "competitiveness_tier")),
    )
    rows: list[dict[str, Any]] = []
    for scope_id, scope in scopes.items():
        if scope.empty:
            continue
        for unit_type, columns in unit_specs:
            for keys, group in scope.groupby(list(columns), sort=True):
                key_tuple = keys if isinstance(keys, tuple) else (keys,)
                values = dict(zip(columns, key_tuple))
                rows.append(
                    _unit_summary(
                        group,
                        scope_id=scope_id,
                        unit_type=unit_type,
                        unit_values=values,
                    )
                )
    return pd.DataFrame(rows, columns=UNIT_COLUMNS)


def build_summary_table(cases: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """Build compact rows for report integration."""

    primary_cases = cases.loc[cases["scope_primary"]]
    high_cases = cases.loc[cases["scope_late_high_distance"]]
    rows = [
        _summary_row(
            "input_row_count",
            len(cases),
            "state-date rows",
            "Input state-date poll panel rows.",
        ),
        _summary_row(
            "primary_row_count",
            len(primary_cases),
            "state-date rows",
            "Rows in the primary <=90-day low/middle poll-distance scope.",
        ),
        _summary_row(
            "primary_polymarket_lower_loss_count",
            int((primary_cases["lower_loss_source"] == "polymarket").sum()),
            "state-date rows",
            "Primary rows where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "primary_poll_lower_loss_count",
            int(
                (primary_cases["lower_loss_source"] == "poll_derived_forecast").sum()
            ),
            "state-date rows",
            "Primary rows where poll-derived probability has lower Brier loss.",
        ),
    ]
    for unit_type in ("state", "state_month", "state_horizon", "horizon_tier"):
        primary_units = _scope_units(units, PRIMARY_SCOPE_ID, unit_type)
        full_units = _scope_units(units, FULL_PANEL_SCOPE_ID, unit_type)
        high_units = _scope_units(units, HIGH_DISTANCE_SCOPE_ID, unit_type)
        rows.extend(
            [
                _summary_row(
                    f"primary_{unit_type}_unit_count",
                    len(primary_units),
                    f"{unit_type} units",
                    f"Primary scope {unit_type} units.",
                ),
                _summary_row(
                    f"primary_{unit_type}_polymarket_support_count",
                    _support_count(primary_units, "aggregate_mean_supports_polymarket"),
                    f"{unit_type} units",
                    f"Primary {unit_type} units where Polymarket has lower mean Brier.",
                ),
                _summary_row(
                    f"primary_{unit_type}_majority_support_count",
                    _support_count(primary_units, "majority_rows_support_polymarket"),
                    f"{unit_type} units",
                    f"Primary {unit_type} units where Polymarket has lower loss in a row majority.",
                ),
                _summary_row(
                    f"primary_{unit_type}_polymarket_exact_binomial_p_value_greater",
                    _sign_test(primary_units, "aggregate_mean_supports_polymarket")[
                        "p_value_greater"
                    ],
                    "p_value",
                    f"One-sided exact binomial p-value for Polymarket support across primary {unit_type} units.",
                ),
                _summary_row(
                    f"primary_{unit_type}_polymarket_exact_95_ci_low",
                    _sign_test(primary_units, "aggregate_mean_supports_polymarket")[
                        "ci_low"
                    ],
                    "share",
                    f"Exact 95 percent lower confidence bound for Polymarket support across primary {unit_type} units.",
                ),
                _summary_row(
                    f"full_panel_{unit_type}_unit_count",
                    len(full_units),
                    f"{unit_type} units",
                    f"Full panel {unit_type} units.",
                ),
                _summary_row(
                    f"full_panel_{unit_type}_polymarket_support_count",
                    _support_count(full_units, "aggregate_mean_supports_polymarket"),
                    f"{unit_type} units",
                    f"Full-panel {unit_type} units where Polymarket has lower mean Brier.",
                ),
                _summary_row(
                    f"full_panel_{unit_type}_poll_support_count",
                    _support_count(full_units, "aggregate_mean_supports_poll_derived"),
                    f"{unit_type} units",
                    f"Full-panel {unit_type} units where poll-derived probability has lower mean Brier.",
                ),
                _summary_row(
                    f"late_high_{unit_type}_unit_count",
                    len(high_units),
                    f"{unit_type} units",
                    f"Late high-distance {unit_type} units.",
                ),
                _summary_row(
                    f"late_high_{unit_type}_poll_support_count",
                    _support_count(high_units, "aggregate_mean_supports_poll_derived"),
                    f"{unit_type} units",
                    f"Late high-distance {unit_type} units where poll-derived probability has lower mean Brier.",
                ),
                _summary_row(
                    f"late_high_{unit_type}_poll_exact_binomial_p_value_greater",
                    _sign_test(high_units, "aggregate_mean_supports_poll_derived")[
                        "p_value_greater"
                    ],
                    "p_value",
                    f"One-sided exact binomial p-value for poll-derived support across late high-distance {unit_type} units.",
                ),
            ]
        )
    rows.extend(
        [
            _summary_row(
                "late_high_row_count",
                len(high_cases),
                "state-date rows",
                "Rows in the <=90-day high poll-distance counterexample scope.",
            ),
            _summary_row(
                "late_high_poll_lower_loss_count",
                int(
                    (high_cases["lower_loss_source"] == "poll_derived_forecast").sum()
                ),
                "state-date rows",
                "Late high-distance rows where poll-derived probability has lower Brier loss.",
            ),
            _summary_row(
                "primary_scope_supported_across_all_units",
                int(
                    all(
                        _support_count(
                            _scope_units(units, PRIMARY_SCOPE_ID, unit_type),
                            "aggregate_mean_supports_polymarket",
                        )
                        == len(_scope_units(units, PRIMARY_SCOPE_ID, unit_type))
                        for unit_type in (
                            "state",
                            "state_month",
                            "state_horizon",
                            "horizon_tier",
                        )
                    )
                ),
                "binary",
                "Primary scope has Polymarket lower mean Brier in every reported aggregation unit.",
            ),
            _summary_row(
                "broad_claim_proven",
                0,
                "binary",
                "The broad Polymarket-better claim remains unproven.",
            ),
            _summary_row(
                "h1_goal_completion_status",
                "not_proven",
                "status",
                "The robust aggregation supports a bounded poll statement, not the full broad objective.",
            ),
        ]
    )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_unit_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate unit-level output schema and counts."""

    _require_columns(frame, UNIT_COLUMNS, "H1 poll unit robustness table")
    _reject_forbidden_columns(frame, "H1 poll unit robustness table")
    validated = frame.loc[:, list(UNIT_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 poll unit robustness table must not be empty")
    for column in (
        "row_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise").astype(int)
    for column in (
        "polymarket_better_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    total = (
        validated["polymarket_lower_loss_count"]
        + validated["poll_derived_lower_loss_count"]
        + validated["tie_count"]
    )
    if not (total == validated["row_count"]).all():
        raise ValueError("unit lower-loss counts must add to row_count")
    if not validated["polymarket_better_share"].between(0.0, 1.0).all():
        raise ValueError("polymarket_better_share must be in [0, 1]")
    return validated


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact summary table."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 poll unit robustness summary")
    _reject_forbidden_columns(frame, "H1 poll unit robustness summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 poll unit robustness summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return validated


def write_unit_robustness_figure(
    *,
    units: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a robustness scorecard figure."""

    fig, axes = plt.subplots(2, 2, figsize=(14.6, 9.3))
    fig.suptitle(
        "H1 poll-comparison robustness: row result survives coarser units",
        fontsize=14,
        fontweight="bold",
    )

    _plot_primary_unit_support(axes[0, 0], summary)
    _plot_counterexample_units(axes[0, 1], summary)
    _plot_unit_mean_advantages(axes[1, 0], units)
    _plot_statement_box(axes[1, 1], summary)

    fig.text(
        0.5,
        0.012,
        (
            "Unit aggregations reduce repeated-row dependence but remain one "
            "election context. State-month and state-horizon units are "
            "diagnostic, not independent elections."
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
    cases: pd.DataFrame,
    units: pd.DataFrame,
    summary: pd.DataFrame,
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    """Build metadata for the unit-robustness scorecard."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_poll_comparison_unit_robustness",
            "calculation_scope": "deterministic_python_from_existing_h1_panel_rows",
            "uses_existing_horizon_bins": True,
            "uses_quantile_derived_competitiveness_tiers": True,
            "uses_fixed_competitiveness_thresholds": False,
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
            "primary_scope_supported_across_all_units": bool(
                _summary_value(summary, "primary_scope_supported_across_all_units")
            ),
            "primary_state_month_exact_binomial_p_value": float(
                _summary_value(
                    summary,
                    "primary_state_month_polymarket_exact_binomial_p_value_greater",
                )
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
            "unit_aggregation_reduces_repeated_row_dependence": True,
            "state_month_units_are_not_independent_elections": True,
            "state_horizon_units_are_not_independent_elections": True,
            "one_election_context_only": True,
            "full_panel_remains_counterexample": True,
            "late_high_distance_subset_remains_counterexample": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _unit_summary(
    group: pd.DataFrame,
    *,
    scope_id: str,
    unit_type: str,
    unit_values: dict[str, Any],
) -> dict[str, Any]:
    pm_count = int((group["lower_loss_source"] == "polymarket").sum())
    poll_count = int((group["lower_loss_source"] == "poll_derived_forecast").sum())
    tie_count = int(len(group) - pm_count - poll_count)
    mean_pm = float(group["polymarket_brier"].mean())
    mean_poll = float(group["poll_derived_brier"].mean())
    state = str(unit_values.get("state", ""))
    month = str(unit_values.get("forecast_month", ""))
    horizon = str(unit_values.get("horizon_bin", ""))
    tier = str(unit_values.get("competitiveness_tier", ""))
    parts = [value for value in (state, month, horizon, tier) if value]
    return {
        "scope_id": scope_id,
        "unit_type": unit_type,
        "unit_id": "|".join(parts),
        "state": state,
        "forecast_month": month,
        "horizon_bin": horizon,
        "horizon_label": str(_first_or_blank(group, "horizon_label", horizon)),
        "competitiveness_tier": tier,
        "competitiveness_label": str(
            TIER_LABELS.get(tier, _first_or_blank(group, "competitiveness_label", ""))
        ),
        "row_count": int(len(group)),
        "polymarket_lower_loss_count": pm_count,
        "poll_derived_lower_loss_count": poll_count,
        "tie_count": tie_count,
        "polymarket_better_share": pm_count / len(group),
        "mean_polymarket_brier": mean_pm,
        "mean_poll_derived_brier": mean_poll,
        "mean_loss_advantage": mean_poll - mean_pm,
        "aggregate_mean_supports_polymarket": bool(mean_pm < mean_poll),
        "majority_rows_support_polymarket": bool(pm_count > poll_count),
        "aggregate_mean_supports_poll_derived": bool(mean_poll < mean_pm),
        "majority_rows_support_poll_derived": bool(poll_count > pm_count),
        "row_unit": "aggregated_state_date_forecast_rows",
        "limitation": (
            "Aggregated units reduce repeated daily rows but remain one "
            "election context, not independent elections."
        ),
    }


def _plot_primary_unit_support(ax: plt.Axes, summary: pd.DataFrame) -> None:
    labels = ["Rows", "States", "State-months", "State-horizons", "Horizon-tiers"]
    pm_counts = [
        int(_summary_value(summary, "primary_polymarket_lower_loss_count")),
        int(_summary_value(summary, "primary_state_polymarket_support_count")),
        int(_summary_value(summary, "primary_state_month_polymarket_support_count")),
        int(_summary_value(summary, "primary_state_horizon_polymarket_support_count")),
        int(_summary_value(summary, "primary_horizon_tier_polymarket_support_count")),
    ]
    totals = [
        int(_summary_value(summary, "primary_row_count")),
        int(_summary_value(summary, "primary_state_unit_count")),
        int(_summary_value(summary, "primary_state_month_unit_count")),
        int(_summary_value(summary, "primary_state_horizon_unit_count")),
        int(_summary_value(summary, "primary_horizon_tier_unit_count")),
    ]
    shares = [pm / total for pm, total in zip(pm_counts, totals)]
    colors = ["#2563eb" if share >= 0.5 else "#dc2626" for share in shares]
    bars = ax.bar(labels, shares, color=colors, alpha=0.84)
    ax.axhline(0.5, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Polymarket support share")
    ax.set_title("Primary scope survives coarser units")
    for bar, pm, total in zip(bars, pm_counts, totals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.025,
            f"{pm}/{total}",
            ha="center",
            fontsize=8.5,
        )
    ax.tick_params(axis="x", rotation=18)
    ax.grid(axis="y", alpha=0.24)


def _plot_counterexample_units(ax: plt.Axes, summary: pd.DataFrame) -> None:
    labels = ["Full panel\nstate-months", "Late high\nstate-months"]
    poll_counts = [
        int(_summary_value(summary, "full_panel_state_month_poll_support_count")),
        int(_summary_value(summary, "late_high_state_month_poll_support_count")),
    ]
    totals = [
        int(_summary_value(summary, "full_panel_state_month_unit_count")),
        int(_summary_value(summary, "late_high_state_month_unit_count")),
    ]
    shares = [count / total for count, total in zip(poll_counts, totals)]
    bars = ax.bar(labels, shares, color="#dc2626", alpha=0.82)
    ax.axhline(0.5, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Poll-derived support share")
    ax.set_title("Boundaries remain visible")
    for bar, count, total in zip(bars, poll_counts, totals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.025,
            f"{count}/{total}",
            ha="center",
            fontsize=9,
        )
    ax.grid(axis="y", alpha=0.24)


def _plot_unit_mean_advantages(ax: plt.Axes, units: pd.DataFrame) -> None:
    primary = units.loc[units["scope_id"] == PRIMARY_SCOPE_ID]
    unit_order = ["state", "state_month", "state_horizon", "horizon_tier"]
    data = [
        primary.loc[primary["unit_type"] == unit_type, "mean_loss_advantage"].to_numpy()
        for unit_type in unit_order
    ]
    ax.boxplot(
        data,
        tick_labels=["State", "State-month", "State-horizon", "Horizon-tier"],
        patch_artist=True,
        boxprops={"facecolor": "#93c5fd", "color": "#2563eb", "alpha": 0.86},
        medianprops={"color": "#111827", "linewidth": 1.2},
        whiskerprops={"color": "#2563eb"},
        capprops={"color": "#2563eb"},
    )
    ax.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_title("Mean Brier advantage across primary units")
    ax.set_ylabel("Poll Brier minus Polymarket Brier")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.24)


def _plot_statement_box(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "Robust bounded statement\n"
        f"- Row-level: PM {_int_summary(summary, 'primary_polymarket_lower_loss_count')} "
        f"of {_int_summary(summary, 'primary_row_count')}.\n"
        f"- State units: PM {_int_summary(summary, 'primary_state_polymarket_support_count')} "
        f"of {_int_summary(summary, 'primary_state_unit_count')}.\n"
        f"- State-month units: PM {_int_summary(summary, 'primary_state_month_polymarket_support_count')} "
        f"of {_int_summary(summary, 'primary_state_month_unit_count')}; exact p="
        f"{_summary_value(summary, 'primary_state_month_polymarket_exact_binomial_p_value_greater'):.2g}, "
        f"95% lower bound "
        f"{_summary_value(summary, 'primary_state_month_polymarket_exact_95_ci_low'):.3f}.\n"
        f"- State-horizon units: PM {_int_summary(summary, 'primary_state_horizon_polymarket_support_count')} "
        f"of {_int_summary(summary, 'primary_state_horizon_unit_count')}.\n\n"
        "Boundary\n"
        f"- Full panel state-month units: poll-derived "
        f"{_int_summary(summary, 'full_panel_state_month_poll_support_count')} "
        f"of {_int_summary(summary, 'full_panel_state_month_unit_count')}.\n"
        f"- Late high-distance state-month units: poll-derived "
        f"{_int_summary(summary, 'late_high_state_month_poll_support_count')} "
        f"of {_int_summary(summary, 'late_high_state_month_unit_count')}.\n"
        f"- Broad claim proven: {_int_summary(summary, 'broad_claim_proven')}."
    )
    ax.text(
        0.02,
        0.96,
        text,
        va="top",
        fontsize=10.6,
        color="#1f2937",
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _scope_units(units: pd.DataFrame, scope_id: str, unit_type: str) -> pd.DataFrame:
    return units.loc[(units["scope_id"] == scope_id) & (units["unit_type"] == unit_type)]


def _support_count(units: pd.DataFrame, column: str) -> int:
    if column not in units.columns:
        raise ValueError(f"support column not found: {column}")
    return int(units[column].astype(str).str.lower().eq("true").sum())


def _sign_test(units: pd.DataFrame, support_column: str) -> dict[str, float]:
    if units.empty:
        return {"p_value_greater": float("nan"), "ci_low": float("nan")}
    successes = _support_count(units, support_column)
    test_n = len(units)
    result = binomtest(successes, test_n, p=0.5, alternative="greater")
    ci = result.proportion_ci(confidence_level=0.95, method="exact")
    return {"p_value_greater": float(result.pvalue), "ci_low": float(ci.low)}


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


def _summary_value(summary: pd.DataFrame, summary_id: str) -> float:
    rows = summary.loc[summary["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def _int_summary(summary: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(summary, summary_id))


def _first_or_blank(group: pd.DataFrame, column: str, fallback: str) -> str:
    if column not in group.columns:
        return fallback
    values = group[column].dropna().astype(str)
    return str(values.iloc[0]) if not values.empty else fallback


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
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--unit-output", type=Path, default=UNIT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_poll_comparison_unit_robustness_outputs(
            case_input=args.case_input,
            unit_output=args.unit_output,
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
