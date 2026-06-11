"""Calibration and score-quality view for robust H1 poll scopes.

The poll-scope frontier identifies bounded scopes where Polymarket has robust
support against poll-derived probabilities. This module adds a focused
forecast-quality diagnostic for those scopes: lower-loss counts, mean Brier,
fixed-bin calibration error, and probability separation.
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

from operations.analysis.h1_poll_scope_frontier import prepare_scope_cases
from operations.analysis.h1_state_poll_panel_horizon_diagnostic import CASE_INPUT
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


FORECAST_ROWS_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality_rows.csv"
BIN_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality_bins.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality_summary.csv"
PAIRWISE_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality_pairwise.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_robust_poll_scope_quality_metadata.json"

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

BIN_COUNT = 5

FORECAST_ROW_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "source_id",
    "source_label",
    "state",
    "forecast_date",
    "forecast_month",
    "case_id",
    "days_to_election",
    "competitiveness_tier",
    "outcome_value",
    "forecast_probability",
    "brier_loss",
    "row_unit",
    "limitation",
)

BIN_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "source_id",
    "source_label",
    "bin_index",
    "bin_label",
    "bin_start",
    "bin_end",
    "row_count",
    "positive_count",
    "mean_forecast_probability",
    "observed_frequency",
    "mean_brier_loss",
    "forecast_minus_observed",
    "absolute_calibration_gap",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "source_id",
    "source_label",
    "row_count",
    "state_count",
    "positive_rate",
    "mean_forecast_probability",
    "mean_brier_loss",
    "brier_skill_vs_50_percent",
    "nonempty_bin_count",
    "expected_calibration_error",
    "root_mean_square_calibration_error",
    "max_absolute_calibration_gap",
    "mean_probability_positive_outcomes",
    "mean_probability_negative_outcomes",
    "probability_separation",
    "calibration_scope",
    "limitation",
)

PAIRWISE_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "case_count",
    "state_count",
    "state_month_unit_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "polymarket_expected_calibration_error",
    "poll_derived_expected_calibration_error",
    "ece_advantage",
    "polymarket_probability_separation",
    "poll_derived_probability_separation",
    "probability_separation_advantage",
    "state_month_polymarket_support_count",
    "state_month_poll_support_count",
    "state_month_tie_count",
    "bounded_poll_claim_supported",
    "broad_claim_supported",
    "limitation",
)


@dataclass(frozen=True)
class H1RobustPollScopeQualityResult:
    """Summary of generated robust poll-scope quality artifacts."""

    forecast_rows_path: Path
    bins_path: Path
    summary_path: Path
    pairwise_path: Path
    figure_path: Path
    metadata_path: Path
    scope_count: int
    strongest_case_count: int
    strongest_polymarket_lower_loss_count: int
    largest_case_count: int
    largest_polymarket_lower_loss_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "forecast_rows_path": str(self.forecast_rows_path),
            "bins_path": str(self.bins_path),
            "summary_path": str(self.summary_path),
            "pairwise_path": str(self.pairwise_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "scope_count": self.scope_count,
            "strongest_case_count": self.strongest_case_count,
            "strongest_polymarket_lower_loss_count": (
                self.strongest_polymarket_lower_loss_count
            ),
            "largest_case_count": self.largest_case_count,
            "largest_polymarket_lower_loss_count": (
                self.largest_polymarket_lower_loss_count
            ),
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_robust_poll_scope_quality_outputs(
    *,
    case_input: Path = CASE_INPUT,
    forecast_rows_output: Path = FORECAST_ROWS_OUTPUT,
    bin_output: Path = BIN_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    pairwise_output: Path = PAIRWISE_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1RobustPollScopeQualityResult:
    """Generate robust poll-scope quality CSVs, figure, and metadata."""

    cases = prepare_scope_cases(read_panel_cases(case_input))
    forecast_rows = validate_forecast_rows(build_forecast_rows(cases))
    bins = validate_bins(build_calibration_bins(forecast_rows))
    summary = validate_summary(build_quality_summary(forecast_rows, bins))
    pairwise = validate_pairwise(build_pairwise_summary(cases, summary))

    forecast_rows_output.parent.mkdir(parents=True, exist_ok=True)
    forecast_rows.to_csv(forecast_rows_output, index=False)
    bins.to_csv(bin_output, index=False)
    summary.to_csv(summary_output, index=False)
    pairwise.to_csv(pairwise_output, index=False)
    write_quality_figure(pairwise=pairwise, bins=bins, output_path=figure_output)
    metadata = build_metadata(
        forecast_rows=forecast_rows,
        bins=bins,
        summary=summary,
        pairwise=pairwise,
        case_input=case_input,
        forecast_rows_output=forecast_rows_output,
        bin_output=bin_output,
        summary_output=summary_output,
        pairwise_output=pairwise_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    largest = _pairwise_scope(pairwise, "largest_robust_lte120_low_middle")
    strongest = _pairwise_scope(pairwise, "strongest_robust_lte90_low_middle")
    return H1RobustPollScopeQualityResult(
        forecast_rows_path=forecast_rows_output,
        bins_path=bin_output,
        summary_path=summary_output,
        pairwise_path=pairwise_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        scope_count=int(len(pairwise)),
        strongest_case_count=int(strongest["case_count"]),
        strongest_polymarket_lower_loss_count=int(
            strongest["polymarket_lower_loss_count"]
        ),
        largest_case_count=int(largest["case_count"]),
        largest_polymarket_lower_loss_count=int(
            largest["polymarket_lower_loss_count"]
        ),
        broad_claim_proven=bool(pairwise["broad_claim_supported"].any()),
    )


def build_forecast_rows(cases: pd.DataFrame) -> pd.DataFrame:
    """Create long forecast rows for selected robust poll scopes."""

    rows: list[dict[str, Any]] = []
    sources = [
        ("polymarket", "Polymarket", "polymarket_probability", "polymarket_brier"),
        (
            "poll_derived",
            "538 poll-derived",
            "poll_derived_probability",
            "poll_derived_brier",
        ),
    ]
    for scope_id, scope_label, cutoff_days, tiers in SCOPE_SPECS:
        scope_cases = _scope_cases(cases, cutoff_days=cutoff_days, tiers=tiers)
        if scope_cases.empty:
            raise ValueError(f"robust poll scope must not be empty: {scope_id}")
        for _, case in scope_cases.iterrows():
            for source_id, source_label, probability_col, brier_col in sources:
                rows.append(
                    {
                        "scope_id": scope_id,
                        "scope_label": scope_label,
                        "source_id": source_id,
                        "source_label": source_label,
                        "state": str(case["state"]),
                        "forecast_date": pd.Timestamp(case["forecast_date"]).strftime(
                            "%Y-%m-%d"
                        ),
                        "forecast_month": str(case["forecast_month"]),
                        "case_id": str(case["case_id"]),
                        "days_to_election": int(case["days_to_election"]),
                        "competitiveness_tier": str(case["competitiveness_tier"]),
                        "outcome_value": float(case["outcome_value"]),
                        "forecast_probability": float(case[probability_col]),
                        "brier_loss": float(case[brier_col]),
                        "row_unit": "state_date_forecast_row_in_robust_poll_scope",
                        "limitation": (
                            "Rows are repeated state-date forecasts inside one "
                            "election context; scope is bounded to low/middle "
                            "poll-distance rows."
                        ),
                    }
                )
    return pd.DataFrame(rows, columns=FORECAST_ROW_COLUMNS)


def build_calibration_bins(forecast_rows: pd.DataFrame) -> pd.DataFrame:
    """Build fixed 20-point calibration bins for each robust scope and source."""

    rows: list[dict[str, Any]] = []
    group_cols = ["scope_id", "scope_label", "source_id", "source_label"]
    for keys, group in forecast_rows.groupby(group_cols, sort=True):
        scope_id, scope_label, source_id, source_label = keys
        for bin_index in range(BIN_COUNT):
            bin_start = bin_index / BIN_COUNT
            bin_end = (bin_index + 1) / BIN_COUNT
            if bin_index == 0:
                mask = group["forecast_probability"].between(
                    bin_start,
                    bin_end,
                    inclusive="both",
                )
            else:
                mask = (group["forecast_probability"] > bin_start) & (
                    group["forecast_probability"] <= bin_end
                )
            subset = group.loc[mask]
            if subset.empty:
                row_count = 0
                positive_count = 0
                mean_probability = float("nan")
                observed_frequency = float("nan")
                mean_brier = float("nan")
                forecast_minus_observed = float("nan")
                absolute_gap = float("nan")
            else:
                row_count = int(len(subset))
                positive_count = int(subset["outcome_value"].sum())
                mean_probability = float(subset["forecast_probability"].mean())
                observed_frequency = float(subset["outcome_value"].mean())
                mean_brier = float(subset["brier_loss"].mean())
                forecast_minus_observed = mean_probability - observed_frequency
                absolute_gap = abs(forecast_minus_observed)
            rows.append(
                {
                    "scope_id": scope_id,
                    "scope_label": scope_label,
                    "source_id": source_id,
                    "source_label": source_label,
                    "bin_index": bin_index,
                    "bin_label": f"{bin_start:.1f}-{bin_end:.1f}",
                    "bin_start": bin_start,
                    "bin_end": bin_end,
                    "row_count": row_count,
                    "positive_count": positive_count,
                    "mean_forecast_probability": mean_probability,
                    "observed_frequency": observed_frequency,
                    "mean_brier_loss": mean_brier,
                    "forecast_minus_observed": forecast_minus_observed,
                    "absolute_calibration_gap": absolute_gap,
                }
            )
    return pd.DataFrame(rows, columns=BIN_COLUMNS)


def build_quality_summary(
    forecast_rows: pd.DataFrame,
    bins: pd.DataFrame,
) -> pd.DataFrame:
    """Build source-level score-quality summaries for selected robust scopes."""

    rows: list[dict[str, Any]] = []
    group_cols = ["scope_id", "scope_label", "source_id", "source_label"]
    for keys, group in forecast_rows.groupby(group_cols, sort=True):
        scope_id, scope_label, source_id, source_label = keys
        source_bins = bins.loc[
            (bins["scope_id"] == scope_id)
            & (bins["source_id"] == source_id)
            & (bins["row_count"] > 0)
        ]
        weights = source_bins["row_count"] / len(group)
        ece = float((weights * source_bins["absolute_calibration_gap"]).sum())
        rmsce = float(
            ((weights * source_bins["absolute_calibration_gap"] ** 2).sum()) ** 0.5
        )
        positive = group.loc[group["outcome_value"] == 1.0, "forecast_probability"]
        negative = group.loc[group["outcome_value"] == 0.0, "forecast_probability"]
        mean_positive = float(positive.mean())
        mean_negative = float(negative.mean())
        mean_brier = float(group["brier_loss"].mean())
        rows.append(
            {
                "scope_id": scope_id,
                "scope_label": scope_label,
                "source_id": source_id,
                "source_label": source_label,
                "row_count": int(len(group)),
                "state_count": int(group["state"].nunique()),
                "positive_rate": float(group["outcome_value"].mean()),
                "mean_forecast_probability": float(
                    group["forecast_probability"].mean()
                ),
                "mean_brier_loss": mean_brier,
                "brier_skill_vs_50_percent": 1.0 - mean_brier / 0.25,
                "nonempty_bin_count": int(len(source_bins)),
                "expected_calibration_error": ece,
                "root_mean_square_calibration_error": rmsce,
                "max_absolute_calibration_gap": float(
                    source_bins["absolute_calibration_gap"].max()
                ),
                "mean_probability_positive_outcomes": mean_positive,
                "mean_probability_negative_outcomes": mean_negative,
                "probability_separation": mean_positive - mean_negative,
                "calibration_scope": "fixed_20_point_bins_in_robust_poll_scope",
                "limitation": (
                    "Calibration bins are repeated state-date forecasts inside "
                    "one election context."
                ),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_pairwise_summary(
    cases: pd.DataFrame,
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build robust poll-scope pairwise score-quality summaries."""

    rows: list[dict[str, Any]] = []
    summary_by_key = summary.set_index(["scope_id", "source_id"])
    for scope_id, scope_label, cutoff_days, tiers in SCOPE_SPECS:
        scope_cases = _scope_cases(cases, cutoff_days=cutoff_days, tiers=tiers)
        state_month = _state_month_units(scope_cases)
        unit_counts = state_month["support_source"].value_counts()
        pm_summary = summary_by_key.loc[(scope_id, "polymarket")]
        poll_summary = summary_by_key.loc[(scope_id, "poll_derived")]
        pm_lower = int((scope_cases["lower_loss_source"] == "polymarket").sum())
        poll_lower = int(
            (scope_cases["lower_loss_source"] == "poll_derived_forecast").sum()
        )
        tie_count = int((scope_cases["lower_loss_source"] == "tie").sum())
        case_count = int(len(scope_cases))
        rows.append(
            {
                "scope_id": scope_id,
                "scope_label": scope_label,
                "case_count": case_count,
                "state_count": int(scope_cases["state"].nunique()),
                "state_month_unit_count": int(len(state_month)),
                "polymarket_lower_loss_count": pm_lower,
                "poll_derived_lower_loss_count": poll_lower,
                "tie_count": tie_count,
                "polymarket_lower_loss_share": pm_lower / case_count,
                "mean_polymarket_brier": float(pm_summary["mean_brier_loss"]),
                "mean_poll_derived_brier": float(poll_summary["mean_brier_loss"]),
                "mean_loss_advantage": float(
                    poll_summary["mean_brier_loss"] - pm_summary["mean_brier_loss"]
                ),
                "polymarket_expected_calibration_error": float(
                    pm_summary["expected_calibration_error"]
                ),
                "poll_derived_expected_calibration_error": float(
                    poll_summary["expected_calibration_error"]
                ),
                "ece_advantage": float(
                    poll_summary["expected_calibration_error"]
                    - pm_summary["expected_calibration_error"]
                ),
                "polymarket_probability_separation": float(
                    pm_summary["probability_separation"]
                ),
                "poll_derived_probability_separation": float(
                    poll_summary["probability_separation"]
                ),
                "probability_separation_advantage": float(
                    pm_summary["probability_separation"]
                    - poll_summary["probability_separation"]
                ),
                "state_month_polymarket_support_count": int(
                    unit_counts.get("polymarket", 0)
                ),
                "state_month_poll_support_count": int(
                    unit_counts.get("poll_derived_forecast", 0)
                ),
                "state_month_tie_count": int(unit_counts.get("tie", 0)),
                "bounded_poll_claim_supported": True,
                "broad_claim_supported": False,
                "limitation": (
                    "Robust scope is bounded to late low/middle poll-distance "
                    "state-date rows from one election context."
                ),
            }
        )
    return pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)


def validate_forecast_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate long-form robust-scope forecast rows."""

    missing = sorted(set(FORECAST_ROW_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"forecast rows missing columns: {missing}")
    _reject_forbidden_columns(frame, "forecast rows")
    normalized = frame.loc[:, list(FORECAST_ROW_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("forecast rows must not be empty")
    for column in (
        "days_to_election",
        "outcome_value",
        "forecast_probability",
        "brier_loss",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome values must be binary")
    if not normalized["forecast_probability"].between(0.0, 1.0).all():
        raise ValueError("forecast probabilities must be in [0, 1]")
    expected = (normalized["forecast_probability"] - normalized["outcome_value"]) ** 2
    if not normalized["brier_loss"].sub(expected).abs().le(1e-12).all():
        raise ValueError("brier_loss must equal squared forecast error")
    return normalized.sort_values(
        ["scope_id", "source_id", "state", "forecast_date"]
    ).reset_index(drop=True)


def validate_bins(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate robust-scope calibration bins."""

    missing = sorted(set(BIN_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"calibration bins missing columns: {missing}")
    _reject_forbidden_columns(frame, "calibration bins")
    return frame.loc[:, list(BIN_COLUMNS)].copy()


def validate_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate robust-scope quality summary."""

    missing = sorted(set(SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"quality summary missing columns: {missing}")
    _reject_forbidden_columns(frame, "quality summary")
    normalized = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("quality summary must not be empty")
    for column in (
        "row_count",
        "state_count",
        "mean_brier_loss",
        "expected_calibration_error",
        "probability_separation",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    return normalized


def validate_pairwise(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate robust-scope pairwise summary."""

    missing = sorted(set(PAIRWISE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"pairwise summary missing columns: {missing}")
    _reject_forbidden_columns(frame, "pairwise summary")
    normalized = frame.loc[:, list(PAIRWISE_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("pairwise summary must not be empty")
    numeric_columns = [
        "case_count",
        "state_count",
        "state_month_unit_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
        "polymarket_expected_calibration_error",
        "poll_derived_expected_calibration_error",
        "ece_advantage",
        "polymarket_probability_separation",
        "poll_derived_probability_separation",
        "probability_separation_advantage",
        "state_month_polymarket_support_count",
        "state_month_poll_support_count",
        "state_month_tie_count",
    ]
    for column in numeric_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["poll_derived_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["case_count"]
    ).any():
        raise ValueError("pairwise lower-loss counts must add to case_count")
    return normalized


def write_quality_figure(
    *,
    pairwise: pd.DataFrame,
    bins: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the robust poll-scope quality figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.0, 9.4))
    fig.suptitle(
        "H1 Robust Poll-Scope Quality: Calibration and Brier Evidence",
        fontsize=14,
        fontweight="bold",
    )
    _plot_brier_ece(axes[0, 0], pairwise)
    _plot_reliability(axes[0, 1], bins, "largest_robust_lte120_low_middle")
    _plot_lower_loss_counts(axes[1, 0], pairwise)
    _plot_statement(axes[1, 1], pairwise)
    fig.text(
        0.5,
        0.016,
        (
            "Lower Brier/ECE are better; reliability uses the largest robust "
            "scope because the strongest scope has only positive outcomes.\n"
            "Bounded robust scopes only; not independent many-election proof."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.065, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    forecast_rows: pd.DataFrame,
    bins: pd.DataFrame,
    summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    case_input: Path,
    forecast_rows_output: Path,
    bin_output: Path,
    summary_output: Path,
    pairwise_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the robust poll-scope quality output."""

    largest = _pairwise_scope(pairwise, "largest_robust_lte120_low_middle")
    strongest = _pairwise_scope(pairwise, "strongest_robust_lte90_low_middle")
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_robust_poll_scope_quality",
            "calculation_scope": "deterministic_python_from_h1_state_date_poll_panel_cases",
            "scope_specs": [
                {
                    "scope_id": scope_id,
                    "scope_label": scope_label,
                    "horizon_cutoff_days": cutoff_days,
                    "included_competitiveness_tiers": list(tiers),
                }
                for scope_id, scope_label, cutoff_days, tiers in SCOPE_SPECS
            ],
            "bin_count": BIN_COUNT,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "forecast_row_count": int(len(forecast_rows)),
            "case_row_count": int(len(forecast_rows) / 2),
            "bin_row_count": int(len(bins)),
            "summary_row_count": int(len(summary)),
            "pairwise_row_count": int(len(pairwise)),
            "largest_case_count": int(largest["case_count"]),
            "largest_polymarket_lower_loss_count": int(
                largest["polymarket_lower_loss_count"]
            ),
            "strongest_case_count": int(strongest["case_count"]),
            "strongest_polymarket_lower_loss_count": int(
                strongest["polymarket_lower_loss_count"]
            ),
            "strongest_scope_all_positive_outcomes": bool(
                summary.loc[
                    (summary["scope_id"] == "strongest_robust_lte90_low_middle")
                    & (summary["source_id"] == "polymarket"),
                    "positive_rate",
                ].iloc[0]
                == 1.0
            ),
            "bounded_poll_claim_supported": bool(
                pairwise["bounded_poll_claim_supported"].all()
            ),
            "broad_claim_proven": bool(pairwise["broad_claim_supported"].any()),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "case_input": str(case_input),
            "forecast_rows": str(forecast_rows_output),
            "bins": str(bin_output),
            "summary": str(summary_output),
            "pairwise": str(pairwise_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "rows_repeat_resolved_state_outcomes": True,
            "state_month_units_are_not_independent_elections": True,
            "low_middle_scope_excludes_high_distance_counterexamples": True,
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


def _state_month_units(group: pd.DataFrame) -> pd.DataFrame:
    units = (
        group.groupby(["state", "forecast_month"], as_index=False)
        .agg(
            row_count=("lower_loss_source", "size"),
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


def _plot_brier_ece(ax: plt.Axes, pairwise: pd.DataFrame) -> None:
    labels = ["<=120\nlow/mid", "<=90\nlow/mid"]
    x = np.arange(len(labels))
    width = 0.18
    metric_specs = [
        ("mean_polymarket_brier", "PM Brier", "#2563eb", -1.5),
        ("mean_poll_derived_brier", "Poll Brier", "#7c3aed", -0.5),
        ("polymarket_expected_calibration_error", "PM ECE", "#60a5fa", 0.5),
        ("poll_derived_expected_calibration_error", "Poll ECE", "#c4b5fd", 1.5),
    ]
    ordered = pairwise.set_index("scope_id").loc[
        ["largest_robust_lte120_low_middle", "strongest_robust_lte90_low_middle"]
    ]
    for column, label, color, offset in metric_specs:
        values = ordered[column].to_numpy(dtype=float)
        ax.bar(x + offset * width, values, width=width, label=label, color=color)
        for xpos, value in zip(x + offset * width, values):
            ax.text(xpos, value + 0.006, f"{value:.3f}", ha="center", fontsize=7.5)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Score")
    ax.set_title("Brier and fixed-bin ECE by robust scope")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(fontsize=7.5, ncol=2)


def _plot_reliability(ax: plt.Axes, bins: pd.DataFrame, scope_id: str) -> None:
    colors = {"polymarket": "#2563eb", "poll_derived": "#7c3aed"}
    labels = {"polymarket": "Polymarket", "poll_derived": "538 poll-derived"}
    markers = {"polymarket": "o", "poll_derived": "s"}
    scope_bins = bins.loc[(bins["scope_id"] == scope_id) & (bins["row_count"] > 0)]
    for source_id, rows in scope_bins.groupby("source_id", sort=True):
        rows = rows.sort_values("mean_forecast_probability")
        sizes = 34 + rows["row_count"] * 1.2
        ax.plot(
            rows["mean_forecast_probability"],
            rows["observed_frequency"],
            color=colors[source_id],
            alpha=0.55,
            linewidth=1.2,
        )
        ax.scatter(
            rows["mean_forecast_probability"],
            rows["observed_frequency"],
            s=sizes,
            color=colors[source_id],
            marker=markers[source_id],
            alpha=0.78,
            edgecolor="#111827",
            linewidth=0.4,
            label=labels[source_id],
        )
        for row_index, (_, row) in enumerate(rows.iterrows()):
            if row["observed_frequency"] >= 0.95:
                x_offset = -16 if source_id == "poll_derived" else 16
                y_offset = -12 if source_id == "poll_derived" else -28
            else:
                x_offset = -12 if row_index % 2 == 0 else 12
                y_offset = 12 if source_id == "poll_derived" else -16
            ax.annotate(
                f"n={int(row['row_count'])}",
                (row["mean_forecast_probability"], row["observed_frequency"]),
                xytext=(x_offset, y_offset),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                color=colors[source_id],
            )
    ax.plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Mean forecast probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title("Calibration bins for largest robust scope")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")


def _plot_lower_loss_counts(ax: plt.Axes, pairwise: pd.DataFrame) -> None:
    ordered = pairwise.set_index("scope_id").loc[
        ["largest_robust_lte120_low_middle", "strongest_robust_lte90_low_middle"]
    ]
    labels = ["<=120 low/mid", "<=90 low/mid"]
    y = np.arange(len(ordered))
    pm = ordered["polymarket_lower_loss_count"].to_numpy(dtype=int)
    poll = ordered["poll_derived_lower_loss_count"].to_numpy(dtype=int)
    ax.barh(y, pm, color="#2563eb", label="Polymarket lower")
    ax.barh(y, poll, left=pm, color="#7c3aed", alpha=0.78, label="Poll-derived lower")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("State-date rows")
    ax.set_title("Lower-loss counts in robust scopes")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, axis="x", alpha=0.25)
    for idx, row in enumerate(ordered.itertuples()):
        ax.text(
            row.case_count + 8,
            idx,
            f"PM {row.polymarket_lower_loss_count}/{row.case_count}",
            va="center",
            fontsize=8,
        )
    ax.set_xlim(0, int(ordered["case_count"].max()) * 1.25)


def _plot_statement(ax: plt.Axes, pairwise: pd.DataFrame) -> None:
    ax.axis("off")
    largest = _pairwise_scope(pairwise, "largest_robust_lte120_low_middle")
    strongest = _pairwise_scope(pairwise, "strongest_robust_lte90_low_middle")
    text = (
        "Robust-scope quality\n"
        f"- Largest robust scope: PM "
        f"{int(largest['polymarket_lower_loss_count'])}/"
        f"{int(largest['case_count'])} rows "
        f"({largest['polymarket_lower_loss_share'] * 100:.1f}%).\n"
        f"- Mean Brier: PM {largest['mean_polymarket_brier']:.4f}, "
        f"poll {largest['mean_poll_derived_brier']:.4f}.\n"
        f"- ECE: PM {largest['polymarket_expected_calibration_error']:.4f}, "
        f"poll {largest['poll_derived_expected_calibration_error']:.4f}.\n\n"
        f"- Strongest robust scope: PM "
        f"{int(strongest['polymarket_lower_loss_count'])}/"
        f"{int(strongest['case_count'])} rows "
        f"({strongest['polymarket_lower_loss_share'] * 100:.1f}%).\n"
        f"- Mean Brier: PM {strongest['mean_polymarket_brier']:.4f}, "
        f"poll {strongest['mean_poll_derived_brier']:.4f}.\n"
        f"- ECE: PM {strongest['polymarket_expected_calibration_error']:.4f}, "
        f"poll {strongest['poll_derived_expected_calibration_error']:.4f}.\n\n"
        "- Strongest scope has only positive outcomes; separation is undefined.\n\n"
        "Status: bounded forecast-quality support; broad claim not_proven."
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


def _pairwise_scope(pairwise: pd.DataFrame, scope_id: str) -> pd.Series:
    rows = pairwise.loc[pairwise["scope_id"] == scope_id]
    if len(rows) != 1:
        raise ValueError(f"pairwise scope not found: {scope_id}")
    return rows.iloc[0]


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
    parser.add_argument(
        "--forecast-rows-output",
        type=Path,
        default=FORECAST_ROWS_OUTPUT,
    )
    parser.add_argument("--bin-output", type=Path, default=BIN_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--pairwise-output", type=Path, default=PAIRWISE_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_robust_poll_scope_quality_outputs(
            case_input=args.case_input,
            forecast_rows_output=args.forecast_rows_output,
            bin_output=args.bin_output,
            summary_output=args.summary_output,
            pairwise_output=args.pairwise_output,
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
