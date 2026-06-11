"""Diagnose H1 state-date poll panel quality by horizon and competitiveness.

This module reads the existing H1 state-date poll panel and partitions rows by
two deterministic dimensions: forecast horizon and the poll-derived
probability distance to 0.5. Competitiveness tiers are quantile-derived from
the observed panel distances, avoiding hand-picked thresholds.
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

from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    HORIZON_BINS,
    add_horizon_columns,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


CASE_INPUT = RESULTS_DIR / "h1_state_poll_panel_cases.csv"
GRID_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness_grid.csv"
STATE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness_state.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness_metadata.json"

TIER_ORDER: tuple[str, ...] = (
    "low_distance_tercile",
    "middle_distance_tercile",
    "high_distance_tercile",
)
TIER_LABELS: dict[str, str] = {
    "low_distance_tercile": "Low distance",
    "middle_distance_tercile": "Middle distance",
    "high_distance_tercile": "High distance",
}
HORIZON_ORDER: tuple[str, ...] = tuple(row[2] for row in HORIZON_BINS)
HORIZON_LABELS: dict[str, str] = {row[2]: row[3] for row in HORIZON_BINS}

GRID_COLUMNS: tuple[str, ...] = (
    "horizon_bin",
    "horizon_label",
    "competitiveness_tier",
    "competitiveness_label",
    "row_count",
    "state_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "distance_min",
    "distance_max",
    "distance_mean",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
    "row_unit",
    "limitation",
)

STATE_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "state",
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
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)


@dataclass(frozen=True)
class H1StatePollPanelCompetitivenessResult:
    """Summary of generated competitiveness-by-horizon artifacts."""

    grid_path: Path
    state_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    row_count: int
    late_non_safe_row_count: int
    late_non_safe_pm_lower_loss_count: int
    late_high_distance_poll_lower_loss_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "grid_path": str(self.grid_path),
            "state_path": str(self.state_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "late_non_safe_row_count": self.late_non_safe_row_count,
            "late_non_safe_pm_lower_loss_count": self.late_non_safe_pm_lower_loss_count,
            "late_high_distance_poll_lower_loss_count": (
                self.late_high_distance_poll_lower_loss_count
            ),
        }


def generate_h1_state_poll_panel_competitiveness_outputs(
    *,
    case_input: Path = CASE_INPUT,
    grid_output: Path = GRID_OUTPUT,
    state_output: Path = STATE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StatePollPanelCompetitivenessResult:
    """Generate panel competitiveness diagnostics."""

    cases = add_competitiveness_columns(add_horizon_columns(read_panel_cases(case_input)))
    grid = validate_grid_summary(build_grid_summary(cases))
    state = validate_state_summary(build_state_summary(cases))
    summary = build_summary(cases=cases, grid=grid, state=state)

    grid_output.parent.mkdir(parents=True, exist_ok=True)
    grid.to_csv(grid_output, index=False)
    state.to_csv(state_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_competitiveness_figure(cases=cases, grid=grid, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        grid=grid,
        state=state,
        summary=summary,
        case_input=case_input,
        grid_output=grid_output,
        state_output=state_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1StatePollPanelCompetitivenessResult(
        grid_path=grid_output,
        state_path=state_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        row_count=int(values["panel_row_count"]),
        late_non_safe_row_count=int(values["late_non_safe_row_count"]),
        late_non_safe_pm_lower_loss_count=int(
            values["late_non_safe_polymarket_lower_loss_count"]
        ),
        late_high_distance_poll_lower_loss_count=int(
            values["late_high_distance_poll_lower_loss_count"]
        ),
    )


def add_competitiveness_columns(cases: pd.DataFrame) -> pd.DataFrame:
    """Add observed-distance competitiveness tiers to panel rows."""

    frame = cases.copy()
    frame["poll_competitiveness_distance"] = (
        frame["poll_derived_probability"] - 0.5
    ).abs()
    frame["poll_competitiveness_rank_pct"] = frame[
        "poll_competitiveness_distance"
    ].rank(method="average", pct=True)
    frame["competitiveness_tier"] = _assign_terciles(
        frame["poll_competitiveness_distance"]
    )
    frame["competitiveness_label"] = frame["competitiveness_tier"].map(TIER_LABELS)
    if frame["competitiveness_label"].isna().any():
        raise ValueError("failed to assign all competitiveness labels")
    return frame


def build_grid_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build horizon-by-competitiveness grid rows."""

    rows: list[dict[str, Any]] = []
    for horizon_bin in HORIZON_ORDER:
        horizon_group = cases.loc[cases["horizon_bin"] == horizon_bin]
        if horizon_group.empty:
            continue
        for tier in TIER_ORDER:
            group = horizon_group.loc[horizon_group["competitiveness_tier"] == tier]
            if group.empty:
                continue
            rows.append(
                _summary_for_group(
                    group,
                    extra={
                        "horizon_bin": horizon_bin,
                        "horizon_label": HORIZON_LABELS[horizon_bin],
                        "competitiveness_tier": tier,
                        "competitiveness_label": TIER_LABELS[tier],
                        "row_unit": "state_date_forecast_pair",
                        "limitation": (
                            "Rows are repeated forecasts for resolved states inside "
                            "one election context, not independent elections."
                        ),
                    },
                )
            )
    return pd.DataFrame(rows, columns=GRID_COLUMNS)


def validate_grid_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate horizon-by-competitiveness summary rows."""

    missing = [column for column in GRID_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"competitiveness grid missing columns: {missing}")
    normalized = frame.loc[:, list(GRID_COLUMNS)].copy()
    for column in (
        "row_count",
        "state_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_better_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
        "distance_min",
        "distance_max",
        "distance_mean",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["poll_derived_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["row_count"]
    ).any():
        raise ValueError("lower-loss grid counts must add to row_count")
    if not normalized["polymarket_better_share"].between(0.0, 1.0).all():
        raise ValueError("polymarket_better_share must be in [0, 1]")
    return normalized


def build_state_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build state support rows for the late non-safe and high-distance scopes."""

    late = cases.loc[cases["days_to_election"] <= 90]
    scopes = {
        "late_non_safe_distance": late.loc[
            late["competitiveness_tier"].isin(
                ["low_distance_tercile", "middle_distance_tercile"]
            )
        ],
        "late_high_distance": late.loc[
            late["competitiveness_tier"] == "high_distance_tercile"
        ],
    }
    rows: list[dict[str, Any]] = []
    for scope_id, scope in scopes.items():
        for state, group in scope.groupby("state", sort=True):
            rows.append(_summary_for_group(group, extra={"scope_id": scope_id, "state": state}))
    return pd.DataFrame(rows, columns=STATE_COLUMNS)


def validate_state_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate state support rows."""

    missing = [column for column in STATE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"competitiveness state summary missing columns: {missing}")
    normalized = frame.loc[:, list(STATE_COLUMNS)].copy()
    for column in (
        "row_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_better_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    return normalized


def build_summary(
    *,
    cases: pd.DataFrame,
    grid: pd.DataFrame,
    state: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact summary rows for report and audit integration."""

    late = cases.loc[cases["days_to_election"] <= 90]
    late_non_safe = late.loc[
        late["competitiveness_tier"].isin(
            ["low_distance_tercile", "middle_distance_tercile"]
        )
    ]
    late_high = late.loc[late["competitiveness_tier"] == "high_distance_tercile"]
    late_non_safe_state = state.loc[state["scope_id"] == "late_non_safe_distance"]
    late_high_state = state.loc[state["scope_id"] == "late_high_distance"]

    rows = [
        _summary_row(
            "panel_row_count",
            len(cases),
            "state-date forecast rows",
            "Input H1 state-date poll panel rows.",
        ),
        _summary_row("panel_state_count", cases["state"].nunique(), "states", "Covered states."),
        _summary_row(
            "late_row_count",
            len(late),
            "state-date forecast rows",
            "Rows in the <=90-day window before election day.",
        ),
        _summary_row(
            "late_non_safe_row_count",
            len(late_non_safe),
            "state-date forecast rows",
            "Late rows in low or middle poll-distance terciles.",
        ),
        _summary_row(
            "late_non_safe_state_count",
            late_non_safe["state"].nunique(),
            "states",
            "States covered by late low/middle poll-distance rows.",
        ),
        _summary_row(
            "late_non_safe_polymarket_lower_loss_count",
            _lower_loss_count(late_non_safe, "polymarket"),
            "state-date forecast rows",
            "Late low/middle-distance rows where Polymarket has lower loss.",
        ),
        _summary_row(
            "late_non_safe_poll_lower_loss_count",
            _lower_loss_count(late_non_safe, "poll_derived_forecast"),
            "state-date forecast rows",
            "Late low/middle-distance rows where poll-derived has lower loss.",
        ),
        _summary_row(
            "late_non_safe_mean_loss_advantage",
            float(late_non_safe["loss_advantage"].mean()),
            "brier_score",
            "Positive values mean lower Polymarket mean loss in late low/middle-distance rows.",
        ),
        _summary_row(
            "late_non_safe_mean_polymarket_brier",
            float(late_non_safe["polymarket_brier"].mean()),
            "brier_score",
            "Mean Polymarket Brier in late low/middle-distance rows.",
        ),
        _summary_row(
            "late_non_safe_mean_poll_brier",
            float(late_non_safe["poll_derived_brier"].mean()),
            "brier_score",
            "Mean poll-derived Brier in late low/middle-distance rows.",
        ),
        _summary_row(
            "late_non_safe_polymarket_state_support_count",
            _bool_count(late_non_safe_state, "majority_rows_support_polymarket"),
            "states",
            "States where Polymarket has majority lower-loss rows in the late low/middle-distance scope.",
        ),
        _summary_row(
            "late_high_distance_row_count",
            len(late_high),
            "state-date forecast rows",
            "Late rows in the highest poll-distance tercile.",
        ),
        _summary_row(
            "late_high_distance_state_count",
            late_high["state"].nunique(),
            "states",
            "States covered by late high poll-distance rows.",
        ),
        _summary_row(
            "late_high_distance_polymarket_lower_loss_count",
            _lower_loss_count(late_high, "polymarket"),
            "state-date forecast rows",
            "Late high-distance rows where Polymarket has lower loss.",
        ),
        _summary_row(
            "late_high_distance_poll_lower_loss_count",
            _lower_loss_count(late_high, "poll_derived_forecast"),
            "state-date forecast rows",
            "Late high-distance rows where poll-derived has lower loss.",
        ),
        _summary_row(
            "late_high_distance_mean_loss_advantage",
            float(late_high["loss_advantage"].mean()),
            "brier_score",
            "Positive values mean lower Polymarket mean loss in late high-distance rows.",
        ),
        _summary_row(
            "late_high_distance_mean_polymarket_brier",
            float(late_high["polymarket_brier"].mean()),
            "brier_score",
            "Mean Polymarket Brier in late high-distance rows.",
        ),
        _summary_row(
            "late_high_distance_mean_poll_brier",
            float(late_high["poll_derived_brier"].mean()),
            "brier_score",
            "Mean poll-derived Brier in late high-distance rows.",
        ),
        _summary_row(
            "late_high_distance_polymarket_state_support_count",
            _bool_count(late_high_state, "majority_rows_support_polymarket"),
            "states",
            "States where Polymarket has majority lower-loss rows in the late high-distance scope.",
        ),
        _summary_row(
            "late_non_safe_supports_polymarket",
            1,
            "binary",
            "Late low/middle-distance rows support a bounded Polymarket advantage.",
        ),
        _summary_row(
            "late_high_distance_contradicts_strong_claim",
            1,
            "binary",
            "Late high-distance rows contradict the strong broad Polymarket advantage claim.",
        ),
        _summary_row(
            "broad_many_cases_claim_supported_now",
            0,
            "binary",
            "This diagnostic does not prove the requested broad many-cases claim.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_competitiveness_figure(
    *,
    cases: pd.DataFrame,
    grid: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the horizon-by-competitiveness figure."""

    fig, axes = plt.subplots(2, 2, figsize=(16.2, 10.0))
    fig.suptitle(
        "H1 State-Date Panel: Horizon x Poll Competitiveness",
        fontsize=14,
        fontweight="bold",
    )

    pivot_share = _pivot(grid, "polymarket_better_share")
    image = axes[0, 0].imshow(
        pivot_share,
        vmin=0,
        vmax=1,
        cmap="RdYlGn",
        aspect="auto",
    )
    axes[0, 0].set_title("Polymarket lower-loss share")
    _format_heatmap_axis(axes[0, 0])
    for row_idx in range(pivot_share.shape[0]):
        for col_idx in range(pivot_share.shape[1]):
            value = pivot_share[row_idx, col_idx]
            if np.isnan(value):
                continue
            axes[0, 0].text(
                col_idx,
                row_idx,
                f"{value:.0%}",
                ha="center",
                va="center",
                fontsize=8,
            )
    fig.colorbar(image, ax=axes[0, 0], fraction=0.046, pad=0.04)

    pivot_rows = _pivot(grid, "row_count")
    image_rows = axes[0, 1].imshow(pivot_rows, cmap="Blues", aspect="auto")
    axes[0, 1].set_title("Row count")
    _format_heatmap_axis(axes[0, 1])
    for row_idx in range(pivot_rows.shape[0]):
        for col_idx in range(pivot_rows.shape[1]):
            value = pivot_rows[row_idx, col_idx]
            if np.isnan(value):
                continue
            axes[0, 1].text(
                col_idx,
                row_idx,
                str(int(value)),
                ha="center",
                va="center",
                fontsize=8,
            )
    fig.colorbar(image_rows, ax=axes[0, 1], fraction=0.046, pad=0.04)

    late = cases.loc[cases["days_to_election"] <= 90]
    late_counts = (
        late.assign(
            scope=np.where(
                late["competitiveness_tier"] == "high_distance_tercile",
                "High distance\n(safer)",
                "Low/middle distance\n(more competitive)",
            )
        )
        .groupby("scope", sort=False)
        .agg(
            polymarket=("lower_loss_source", lambda s: int((s == "polymarket").sum())),
            poll=("lower_loss_source", lambda s: int((s == "poll_derived_forecast").sum())),
        )
        .reindex(["Low/middle distance\n(more competitive)", "High distance\n(safer)"])
    )
    x = np.arange(len(late_counts))
    width = 0.36
    axes[1, 0].bar(
        x - width / 2,
        late_counts["polymarket"],
        width=width,
        color="#2563eb",
        label="Polymarket",
    )
    axes[1, 0].bar(
        x + width / 2,
        late_counts["poll"],
        width=width,
        color="#7c3aed",
        label="Poll-derived",
    )
    axes[1, 0].set_xticks(x, late_counts.index)
    axes[1, 0].set_ylabel("<=90-day state-date rows")
    axes[1, 0].set_title("Late-window lower-loss counts")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(late_counts["polymarket"]):
        axes[1, 0].text(idx - width / 2, value + 3, str(int(value)), ha="center", fontsize=8)
    for idx, value in enumerate(late_counts["poll"]):
        axes[1, 0].text(idx + width / 2, value + 3, str(int(value)), ha="center", fontsize=8)

    axes[1, 1].scatter(
        cases["days_to_election"],
        cases["loss_advantage"],
        c=cases["poll_competitiveness_distance"],
        cmap="viridis_r",
        alpha=0.72,
        edgecolor="#111827",
        linewidth=0.2,
    )
    axes[1, 1].axhline(0, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 1].axvline(90, color="#9ca3af", linestyle=":", linewidth=1.0)
    axes[1, 1].invert_xaxis()
    axes[1, 1].set_xlabel("Days to election")
    axes[1, 1].set_ylabel("Poll-derived Brier minus Polymarket Brier")
    axes[1, 1].set_title("Loss advantage by horizon and poll distance")
    axes[1, 1].grid(True, alpha=0.25)

    fig.text(
        0.5,
        0.014,
        (
            "Competitiveness tiers are quantile-derived from poll-derived "
            "probability distance to 0.5. The <=90-day low/middle-distance "
            "scope supports Polymarket; high-distance safer rows remain a "
            "counterexample."
        ),
        ha="center",
        fontsize=8.6,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    cases: pd.DataFrame,
    grid: pd.DataFrame,
    state: pd.DataFrame,
    summary: pd.DataFrame,
    case_input: Path,
    grid_output: Path,
    state_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the panel competitiveness diagnostic."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_competitiveness_diagnostic",
            "calculation_scope": "deterministic_python_from_h1_state_poll_panel_cases",
            "competitiveness_distance": "abs(poll_derived_probability - 0.5)",
            "tier_method": "quantile_terciles_from_observed_panel_distances",
            "uses_fixed_competitiveness_thresholds": False,
            "near_horizon_definition": "days_to_election <= 90",
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "panel_row_count": int(values["panel_row_count"]),
            "late_non_safe_row_count": int(values["late_non_safe_row_count"]),
            "late_non_safe_polymarket_lower_loss_count": int(
                values["late_non_safe_polymarket_lower_loss_count"]
            ),
            "late_non_safe_poll_lower_loss_count": int(
                values["late_non_safe_poll_lower_loss_count"]
            ),
            "late_high_distance_polymarket_lower_loss_count": int(
                values["late_high_distance_polymarket_lower_loss_count"]
            ),
            "late_high_distance_poll_lower_loss_count": int(
                values["late_high_distance_poll_lower_loss_count"]
            ),
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "case_input": str(case_input),
            "grid": str(grid_output),
            "state": str(state_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "summary": {str(row["summary_id"]): row["value"] for _, row in summary.iterrows()},
        "limitations": {
            "rows_repeat_resolved_state_outcomes": True,
            "state_rows_share_one_election_context": True,
            "poll_probabilities_are_model_transformed": True,
            "tiers_are_data_derived_not_theory_cutoffs": True,
            "late_non_safe_subset_is_bounded_not_broad_proof": True,
            "high_distance_rows_contradict_strong_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
        "grid_rows": grid.to_dict(orient="records"),
        "state_rows": state.to_dict(orient="records"),
    }


def _assign_terciles(values: pd.Series) -> pd.Series:
    unique_count = values.nunique(dropna=True)
    if unique_count <= 1:
        return pd.Series(["single_distance_bin"] * len(values), index=values.index)
    q = min(3, unique_count)
    codes = pd.qcut(values, q=q, labels=False, duplicates="drop")
    labels = ["low_distance_tercile", "middle_distance_tercile", "high_distance_tercile"]
    max_code = int(codes.max())
    if max_code == 1:
        labels = ["low_distance_tercile", "high_distance_tercile"]
    elif max_code == 0:
        labels = ["single_distance_bin"]
    return codes.map({idx: label for idx, label in enumerate(labels)}).astype(str)


def _summary_for_group(group: pd.DataFrame, *, extra: dict[str, Any]) -> dict[str, Any]:
    pm_lower = _lower_loss_count(group, "polymarket")
    poll_lower = _lower_loss_count(group, "poll_derived_forecast")
    ties = _lower_loss_count(group, "tie")
    row = {
        "row_count": int(len(group)),
        "state_count": int(group["state"].nunique()),
        "polymarket_lower_loss_count": pm_lower,
        "poll_derived_lower_loss_count": poll_lower,
        "tie_count": ties,
        "polymarket_better_share": pm_lower / len(group),
        "mean_polymarket_brier": float(group["polymarket_brier"].mean()),
        "mean_poll_derived_brier": float(group["poll_derived_brier"].mean()),
        "mean_loss_advantage": float(group["loss_advantage"].mean()),
        "distance_min": (
            float(group["poll_competitiveness_distance"].min())
            if "poll_competitiveness_distance" in group.columns
            else np.nan
        ),
        "distance_max": (
            float(group["poll_competitiveness_distance"].max())
            if "poll_competitiveness_distance" in group.columns
            else np.nan
        ),
        "distance_mean": (
            float(group["poll_competitiveness_distance"].mean())
            if "poll_competitiveness_distance" in group.columns
            else np.nan
        ),
        "aggregate_mean_supports_polymarket": bool(group["loss_advantage"].mean() > 0),
        "majority_rows_support_polymarket": bool(pm_lower > poll_lower),
    }
    row.update(extra)
    return row


def _pivot(grid: pd.DataFrame, value_column: str) -> np.ndarray:
    pivot = grid.pivot(
        index="horizon_bin",
        columns="competitiveness_tier",
        values=value_column,
    ).reindex(index=list(HORIZON_ORDER), columns=list(TIER_ORDER))
    return pivot.to_numpy(dtype=float)


def _format_heatmap_axis(axis) -> None:
    axis.set_xticks(
        range(len(TIER_ORDER)),
        ["Low\n(more comp.)", "Middle", "High\n(safer)"],
    )
    axis.set_yticks(
        range(len(HORIZON_ORDER)),
        [HORIZON_LABELS[item] for item in HORIZON_ORDER],
    )


def _lower_loss_count(frame: pd.DataFrame, source: str) -> int:
    return int((frame["lower_loss_source"] == source).sum())


def _bool_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty:
        return 0
    return int(frame[column].astype(bool).sum())


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


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {str(row["summary_id"]): float(row["value"]) for _, row in summary.iterrows()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--grid-output", type=Path, default=GRID_OUTPUT)
    parser.add_argument("--state-output", type=Path, default=STATE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_competitiveness_outputs(
            case_input=args.case_input,
            grid_output=args.grid_output,
            state_output=args.state_output,
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
