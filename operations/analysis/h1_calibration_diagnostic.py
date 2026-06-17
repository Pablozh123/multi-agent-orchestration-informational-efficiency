"""Build H1 calibration diagnostics from deterministic case artifacts.

The original daily H1 reliability curve repeats forecasts for one resolved
national election outcome. This module therefore builds the thesis-facing
calibration view from resolved case sets with multiple binary outcomes:
50-state final forecasts, the 13-state poll-derived snapshot, and the curated
8-case final-snapshot extension.
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


RIEKE_CASE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_cases.csv"
TWO_SEVENTY_CASE_INPUT = RESULTS_DIR / "h1_270towin_state_forecast_cases.csv"
STATE_POLL_CASE_INPUT = RESULTS_DIR / "h1_state_poll_snapshot_cases.csv"
FINAL_SNAPSHOT_CASE_INPUT = RESULTS_DIR / "h1_final_snapshot_cases.csv"

FORECAST_CASE_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic_cases.csv"
BIN_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic_bins.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic_summary.csv"
PAIRWISE_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic_pairwise.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_calibration_diagnostic_metadata.json"

BIN_COUNT = 5
FIGURE_SIZE_INCHES: tuple[float, float] = (14.4, 9.6)

CASE_COLUMNS: tuple[str, ...] = (
    "case_set_id",
    "case_unit",
    "forecast_source_id",
    "forecast_source_label",
    "source_family",
    "canonical_case_id",
    "case_label",
    "outcome_value",
    "forecast_probability",
    "brier_loss",
    "is_polymarket",
    "probability_note",
    "source_artifact",
    "limitation",
)

BIN_COLUMNS: tuple[str, ...] = (
    "forecast_source_id",
    "forecast_source_label",
    "case_set_id",
    "source_family",
    "bin_index",
    "bin_label",
    "bin_start",
    "bin_end",
    "case_count",
    "positive_count",
    "mean_forecast_probability",
    "observed_frequency",
    "mean_brier_loss",
    "forecast_minus_observed",
    "absolute_calibration_gap",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "forecast_source_id",
    "forecast_source_label",
    "case_set_id",
    "source_family",
    "case_count",
    "positive_count",
    "positive_rate",
    "mean_forecast_probability",
    "mean_brier_loss",
    "brier_skill_vs_50_percent",
    "nonempty_bin_count",
    "expected_calibration_error",
    "root_mean_square_calibration_error",
    "max_absolute_calibration_gap",
    "mean_forecast_minus_observed",
    "calibration_scope",
    "limitation",
)

PAIRWISE_COLUMNS: tuple[str, ...] = (
    "comparison_id",
    "case_set_label",
    "comparator_label",
    "case_count",
    "polymarket_lower_loss_count",
    "comparator_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_cases_supports_polymarket",
    "broad_many_cases_claim_supported",
    "limitation",
)

FORBIDDEN_COLUMN_TOKENS: tuple[str, ...] = (
    "wallet",
    "maker",
    "taker",
    "address",
    "order_instruction",
)


@dataclass(frozen=True)
class H1CalibrationDiagnosticResult:
    """Summary of generated H1 calibration diagnostic artifacts."""

    forecast_cases_path: Path
    bins_path: Path
    summary_path: Path
    pairwise_path: Path
    figure_path: Path
    metadata_path: Path
    forecast_case_row_count: int
    forecast_source_count: int
    calibration_bin_row_count: int
    pairwise_comparison_count: int
    aggregate_support_row_count: int
    majority_support_row_count: int
    broad_many_cases_support_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "forecast_cases_path": str(self.forecast_cases_path),
            "bins_path": str(self.bins_path),
            "summary_path": str(self.summary_path),
            "pairwise_path": str(self.pairwise_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "forecast_case_row_count": self.forecast_case_row_count,
            "forecast_source_count": self.forecast_source_count,
            "calibration_bin_row_count": self.calibration_bin_row_count,
            "pairwise_comparison_count": self.pairwise_comparison_count,
            "aggregate_support_row_count": self.aggregate_support_row_count,
            "majority_support_row_count": self.majority_support_row_count,
            "broad_many_cases_support_row_count": (
                self.broad_many_cases_support_row_count
            ),
        }


def generate_h1_calibration_diagnostic_outputs(
    *,
    rieke_case_input: Path = RIEKE_CASE_INPUT,
    two_seventy_case_input: Path = TWO_SEVENTY_CASE_INPUT,
    state_poll_case_input: Path = STATE_POLL_CASE_INPUT,
    final_snapshot_case_input: Path = FINAL_SNAPSHOT_CASE_INPUT,
    forecast_case_output: Path = FORECAST_CASE_OUTPUT,
    bin_output: Path = BIN_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    pairwise_output: Path = PAIRWISE_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1CalibrationDiagnosticResult:
    """Generate H1 calibration diagnostic CSVs, figure, and metadata."""

    rieke_cases = read_case_artifact(
        rieke_case_input,
        required_columns={
            "state",
            "outcome_value",
            "rieke_republican_win_probability",
            "polymarket_probability",
        },
    )
    two_seventy_cases = read_case_artifact(
        two_seventy_case_input,
        required_columns={
            "state",
            "outcome_value",
            "two_seventy_trump_win_probability",
            "two_seventy_probability_precision",
            "polymarket_probability",
        },
    )
    state_poll_cases = read_case_artifact(
        state_poll_case_input,
        required_columns={
            "state",
            "outcome_value",
            "poll_derived_probability",
            "polymarket_probability",
        },
    )
    final_snapshot_cases = read_case_artifact(
        final_snapshot_case_input,
        required_columns={
            "case_id",
            "case_label",
            "outcome_value",
            "traditional_probability",
            "polymarket_probability",
        },
    )

    forecast_cases = validate_forecast_cases(
        build_forecast_cases(
            rieke_cases=rieke_cases,
            two_seventy_cases=two_seventy_cases,
            state_poll_cases=state_poll_cases,
            final_snapshot_cases=final_snapshot_cases,
        )
    )
    calibration_bins = validate_calibration_bins(
        build_calibration_bins(forecast_cases, bin_count=BIN_COUNT)
    )
    summary = validate_calibration_summary(
        build_calibration_summary(forecast_cases, calibration_bins)
    )
    pairwise = validate_pairwise_summary(
        build_pairwise_summary(
            rieke_cases=rieke_cases,
            two_seventy_cases=two_seventy_cases,
            state_poll_cases=state_poll_cases,
            final_snapshot_cases=final_snapshot_cases,
        )
    )

    forecast_case_output.parent.mkdir(parents=True, exist_ok=True)
    forecast_cases.to_csv(forecast_case_output, index=False)
    calibration_bins.to_csv(bin_output, index=False)
    summary.to_csv(summary_output, index=False)
    pairwise.to_csv(pairwise_output, index=False)
    write_calibration_figure(
        calibration_bins=calibration_bins,
        summary=summary,
        pairwise=pairwise,
        output_path=figure_output,
    )
    metadata = build_metadata(
        forecast_cases=forecast_cases,
        calibration_bins=calibration_bins,
        summary=summary,
        pairwise=pairwise,
        rieke_case_input=rieke_case_input,
        two_seventy_case_input=two_seventy_case_input,
        state_poll_case_input=state_poll_case_input,
        final_snapshot_case_input=final_snapshot_case_input,
        forecast_case_output=forecast_case_output,
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

    return H1CalibrationDiagnosticResult(
        forecast_cases_path=forecast_case_output,
        bins_path=bin_output,
        summary_path=summary_output,
        pairwise_path=pairwise_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        forecast_case_row_count=int(len(forecast_cases)),
        forecast_source_count=int(forecast_cases["forecast_source_id"].nunique()),
        calibration_bin_row_count=int(len(calibration_bins)),
        pairwise_comparison_count=int(len(pairwise)),
        aggregate_support_row_count=int(
            pairwise["aggregate_mean_supports_polymarket"].sum()
        ),
        majority_support_row_count=int(
            pairwise["majority_cases_supports_polymarket"].sum()
        ),
        broad_many_cases_support_row_count=int(
            pairwise["broad_many_cases_claim_supported"].sum()
        ),
    )


def read_case_artifact(path: Path, *, required_columns: set[str]) -> pd.DataFrame:
    """Read a local H1 case artifact and validate required columns."""

    if not path.exists():
        raise FileNotFoundError(f"H1 calibration input not found: {path}")
    frame = pd.read_csv(path)
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise ValueError(f"H1 calibration input missing columns: {missing}")
    return frame


def build_forecast_cases(
    *,
    rieke_cases: pd.DataFrame,
    two_seventy_cases: pd.DataFrame,
    state_poll_cases: pd.DataFrame,
    final_snapshot_cases: pd.DataFrame,
) -> pd.DataFrame:
    """Create a long forecast-case table for calibration diagnostics."""

    rows: list[dict[str, Any]] = []
    rows.extend(
        _source_rows(
            frame=rieke_cases,
            case_set_id="state_final_50",
            case_unit="resolved_state_outcomes",
            forecast_source_id="polymarket_state_final_50",
            forecast_source_label="Polymarket state final",
            source_family="polymarket",
            probability_column="polymarket_probability",
            label_column="state",
            probability_note="Polymarket market probability nearest forecast time.",
            source_artifact="h1_rieke_state_forecast_cases.csv",
            limitation=(
                "State outcomes share one election context; this is a "
                "calibration diagnostic, not independent national elections."
            ),
        )
    )
    rows.extend(
        _source_rows(
            frame=rieke_cases,
            case_set_id="state_final_50",
            case_unit="resolved_state_outcomes",
            forecast_source_id="rieke_state_final_50",
            forecast_source_label="Rieke poll-model state forecast",
            source_family="traditional_forecast",
            probability_column="rieke_republican_win_probability",
            label_column="state",
            probability_note="Complement of Rieke Harris state-win probability.",
            source_artifact="h1_rieke_state_forecast_cases.csv",
            limitation=(
                "Rieke is an independent poll-based model, not raw polls and "
                "not an official FiveThirtyEight state forecast."
            ),
        )
    )
    rows.extend(
        _source_rows(
            frame=two_seventy_cases,
            case_set_id="state_final_50",
            case_unit="resolved_state_outcomes",
            forecast_source_id="two_seventy_state_final_50",
            forecast_source_label="270toWin/JHK state forecast",
            source_family="traditional_forecast",
            probability_column="two_seventy_trump_win_probability",
            label_column="state",
            probability_note="Exact percentages plus documented censored boundaries.",
            source_artifact="h1_270towin_state_forecast_cases.csv",
            limitation=(
                "Includes 28 censored safe-state boundary probabilities; exact "
                "probabilities are separated in pairwise diagnostics."
            ),
        )
    )
    rows.extend(
        _source_rows(
            frame=state_poll_cases,
            case_set_id="state_poll_snapshot_13",
            case_unit="resolved_state_outcomes",
            forecast_source_id="polymarket_state_poll_13",
            forecast_source_label="Polymarket state poll snapshot",
            source_family="polymarket",
            probability_column="polymarket_probability",
            label_column="state",
            probability_note="Polymarket market probability nearest poll snapshot time.",
            source_artifact="h1_state_poll_snapshot_cases.csv",
            limitation=(
                "Only states with compatible FiveThirtyEight polling-average "
                "rows are included."
            ),
        )
    )
    rows.extend(
        _source_rows(
            frame=state_poll_cases,
            case_set_id="state_poll_snapshot_13",
            case_unit="resolved_state_outcomes",
            forecast_source_id="poll_derived_state_13",
            forecast_source_label="538 poll-derived state probability",
            source_family="traditional_poll_transform",
            probability_column="poll_derived_probability",
            label_column="state",
            probability_note="Documented normal-error transform of poll margins.",
            source_artifact="h1_state_poll_snapshot_cases.csv",
            limitation=(
                "A transformed polling-average margin, not a raw poll share and "
                "not an official FiveThirtyEight state win forecast."
            ),
        )
    )
    rows.extend(
        _source_rows(
            frame=final_snapshot_cases,
            case_set_id="final_snapshot_8",
            case_unit="resolved_outcomes",
            forecast_source_id="polymarket_final_snapshot_8",
            forecast_source_label="Polymarket final snapshot",
            source_family="polymarket",
            probability_column="polymarket_probability",
            label_column="case_label",
            probability_note="Polymarket market probability nearest final forecast time.",
            source_artifact="h1_final_snapshot_cases.csv",
            limitation="Small curated final-snapshot extension.",
        )
    )
    rows.extend(
        _source_rows(
            frame=final_snapshot_cases,
            case_set_id="final_snapshot_8",
            case_unit="resolved_outcomes",
            forecast_source_id="fivethirtyeight_final_snapshot_8",
            forecast_source_label="FiveThirtyEight final snapshot",
            source_family="traditional_forecast",
            probability_column="traditional_probability",
            label_column="case_label",
            probability_note="Curated FiveThirtyEight final probability forecast.",
            source_artifact="h1_final_snapshot_cases.csv",
            limitation="Small curated final-snapshot extension.",
        )
    )
    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def build_calibration_bins(
    forecast_cases: pd.DataFrame, *, bin_count: int = BIN_COUNT
) -> pd.DataFrame:
    """Aggregate forecast cases into fixed-width reliability bins."""

    if bin_count < 2:
        raise ValueError("bin_count must be at least 2")
    frame = forecast_cases.copy()
    probabilities = pd.to_numeric(frame["forecast_probability"], errors="raise")
    frame["bin_index"] = (probabilities * bin_count).astype(int).clip(0, bin_count - 1)
    frame["bin_start"] = frame["bin_index"] / bin_count
    frame["bin_end"] = (frame["bin_index"] + 1) / bin_count
    frame["bin_label"] = frame.apply(
        lambda row: f"{row['bin_start']:.1f}-{row['bin_end']:.1f}",
        axis=1,
    )

    grouped = (
        frame.groupby(
            [
                "forecast_source_id",
                "forecast_source_label",
                "case_set_id",
                "source_family",
                "bin_index",
                "bin_label",
                "bin_start",
                "bin_end",
            ],
            as_index=False,
            sort=True,
        )
        .agg(
            case_count=("forecast_probability", "size"),
            positive_count=("outcome_value", "sum"),
            mean_forecast_probability=("forecast_probability", "mean"),
            observed_frequency=("outcome_value", "mean"),
            mean_brier_loss=("brier_loss", "mean"),
        )
        .loc[:, BIN_COLUMNS[:-2]]
    )
    grouped["forecast_minus_observed"] = (
        grouped["mean_forecast_probability"] - grouped["observed_frequency"]
    )
    grouped["absolute_calibration_gap"] = grouped[
        "forecast_minus_observed"
    ].abs()
    return grouped.loc[:, BIN_COLUMNS]


def build_calibration_summary(
    forecast_cases: pd.DataFrame, calibration_bins: pd.DataFrame
) -> pd.DataFrame:
    """Summarize Brier and fixed-bin calibration error by forecast source."""

    rows: list[dict[str, Any]] = []
    for source_id, source_cases in forecast_cases.groupby(
        "forecast_source_id", sort=True
    ):
        source_bins = calibration_bins.loc[
            calibration_bins["forecast_source_id"] == source_id
        ].copy()
        count = int(len(source_cases))
        weights = source_bins["case_count"] / count
        ece = float((weights * source_bins["absolute_calibration_gap"]).sum())
        rmsce = float(
            ((weights * source_bins["absolute_calibration_gap"] ** 2).sum()) ** 0.5
        )
        positive_rate = float(source_cases["outcome_value"].mean())
        mean_forecast = float(source_cases["forecast_probability"].mean())
        mean_brier = float(source_cases["brier_loss"].mean())
        rows.append(
            {
                "forecast_source_id": source_id,
                "forecast_source_label": str(
                    source_cases["forecast_source_label"].iloc[0]
                ),
                "case_set_id": str(source_cases["case_set_id"].iloc[0]),
                "source_family": str(source_cases["source_family"].iloc[0]),
                "case_count": count,
                "positive_count": int(source_cases["outcome_value"].sum()),
                "positive_rate": positive_rate,
                "mean_forecast_probability": mean_forecast,
                "mean_brier_loss": mean_brier,
                "brier_skill_vs_50_percent": 1.0 - (mean_brier / 0.25),
                "nonempty_bin_count": int(len(source_bins)),
                "expected_calibration_error": ece,
                "root_mean_square_calibration_error": rmsce,
                "max_absolute_calibration_gap": float(
                    source_bins["absolute_calibration_gap"].max()
                ),
                "mean_forecast_minus_observed": mean_forecast - positive_rate,
                "calibration_scope": (
                    "state_case_diagnostic" if count >= 30 else "limited_case_check"
                ),
                "limitation": str(source_cases["limitation"].iloc[0]),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_pairwise_summary(
    *,
    rieke_cases: pd.DataFrame,
    two_seventy_cases: pd.DataFrame,
    state_poll_cases: pd.DataFrame,
    final_snapshot_cases: pd.DataFrame,
) -> pd.DataFrame:
    """Build pairwise Polymarket-vs-comparator loss diagnostics."""

    exact_two_seventy = two_seventy_cases.loc[
        two_seventy_cases["two_seventy_probability_precision"] == "exact_percent"
    ].copy()
    rows = [
        _pairwise_row(
            frame=rieke_cases,
            comparison_id="state_final_pm_vs_rieke",
            case_set_label="50 state outcomes",
            comparator_label="Rieke poll-model forecast",
            comparator_probability_column="rieke_republican_win_probability",
            limitation=(
                "State outcomes share one election context; Rieke is an "
                "independent poll-based forecast model."
            ),
        ),
        _pairwise_row(
            frame=two_seventy_cases,
            comparison_id="state_final_pm_vs_270towin",
            case_set_label="50 state outcomes",
            comparator_label="270toWin/JHK forecast",
            comparator_probability_column="two_seventy_trump_win_probability",
            limitation=(
                "Includes censored safe-state boundary probabilities from the "
                "source."
            ),
        ),
        _pairwise_row(
            frame=exact_two_seventy,
            comparison_id="state_exact_pm_vs_270towin",
            case_set_label="22 exact-probability state outcomes",
            comparator_label="270toWin/JHK exact probabilities",
            comparator_probability_column="two_seventy_trump_win_probability",
            limitation=(
                "Only the 270toWin/JHK states with exact displayed "
                "probabilities are included."
            ),
        ),
        _pairwise_row(
            frame=state_poll_cases,
            comparison_id="state_poll_pm_vs_538_transform",
            case_set_label="13 state outcomes",
            comparator_label="538 poll-derived probability",
            comparator_probability_column="poll_derived_probability",
            limitation=(
                "Poll-derived probabilities are a documented transformation "
                "of polling-average margins, not raw poll shares."
            ),
        ),
        _pairwise_row(
            frame=final_snapshot_cases,
            comparison_id="final_snapshot_pm_vs_538",
            case_set_label="8 final-snapshot outcomes",
            comparator_label="FiveThirtyEight final forecast",
            comparator_probability_column="traditional_probability",
            limitation="Small curated final-snapshot extension.",
        ),
    ]
    return pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)


def validate_forecast_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the long forecast-case table."""

    _require_columns(frame, CASE_COLUMNS, "forecast cases")
    _reject_forbidden_columns(frame, "forecast cases")
    validated = frame.copy()
    validated["forecast_probability"] = pd.to_numeric(
        validated["forecast_probability"], errors="raise"
    )
    validated["outcome_value"] = pd.to_numeric(
        validated["outcome_value"], errors="raise"
    )
    validated["brier_loss"] = pd.to_numeric(validated["brier_loss"], errors="raise")
    if validated.empty:
        raise ValueError("forecast cases must not be empty")
    if not validated["forecast_probability"].between(0.0, 1.0).all():
        raise ValueError("forecast probabilities must be in [0, 1]")
    if not validated["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome values must be binary 0/1")
    expected = (validated["forecast_probability"] - validated["outcome_value"]) ** 2
    if not (validated["brier_loss"].sub(expected).abs() <= 1e-12).all():
        raise ValueError("brier_loss must equal squared forecast error")
    if validated["forecast_source_id"].nunique() < 2:
        raise ValueError("at least two forecast sources are required")
    return validated


def validate_calibration_bins(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate calibration-bin output."""

    _require_columns(frame, BIN_COLUMNS, "calibration bins")
    _reject_forbidden_columns(frame, "calibration bins")
    validated = frame.copy()
    numeric_columns = [
        "bin_index",
        "bin_start",
        "bin_end",
        "case_count",
        "positive_count",
        "mean_forecast_probability",
        "observed_frequency",
        "mean_brier_loss",
        "forecast_minus_observed",
        "absolute_calibration_gap",
    ]
    for column in numeric_columns:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    if validated.empty:
        raise ValueError("calibration bins must not be empty")
    if not validated["mean_forecast_probability"].between(0.0, 1.0).all():
        raise ValueError("bin mean forecast probabilities must be in [0, 1]")
    if not validated["observed_frequency"].between(0.0, 1.0).all():
        raise ValueError("bin observed frequencies must be in [0, 1]")
    if (validated["case_count"] <= 0).any():
        raise ValueError("calibration bin case_count must be positive")
    return validated


def validate_calibration_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate source-level calibration summary."""

    _require_columns(frame, SUMMARY_COLUMNS, "calibration summary")
    _reject_forbidden_columns(frame, "calibration summary")
    validated = frame.copy()
    numeric_columns = [
        "case_count",
        "positive_count",
        "positive_rate",
        "mean_forecast_probability",
        "mean_brier_loss",
        "brier_skill_vs_50_percent",
        "nonempty_bin_count",
        "expected_calibration_error",
        "root_mean_square_calibration_error",
        "max_absolute_calibration_gap",
        "mean_forecast_minus_observed",
    ]
    for column in numeric_columns:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    if validated.empty:
        raise ValueError("calibration summary must not be empty")
    if (validated["case_count"] <= 0).any():
        raise ValueError("summary case_count must be positive")
    if not validated["positive_rate"].between(0.0, 1.0).all():
        raise ValueError("summary positive_rate must be in [0, 1]")
    if not validated["mean_forecast_probability"].between(0.0, 1.0).all():
        raise ValueError("summary mean forecast probabilities must be in [0, 1]")
    return validated


def validate_pairwise_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate pairwise Polymarket-vs-comparator diagnostics."""

    _require_columns(frame, PAIRWISE_COLUMNS, "pairwise summary")
    _reject_forbidden_columns(frame, "pairwise summary")
    validated = frame.copy()
    numeric_columns = [
        "case_count",
        "polymarket_lower_loss_count",
        "comparator_lower_loss_count",
        "tie_count",
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
    ]
    for column in numeric_columns:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    if validated.empty:
        raise ValueError("pairwise summary must not be empty")
    count_sum = (
        validated["polymarket_lower_loss_count"]
        + validated["comparator_lower_loss_count"]
        + validated["tie_count"]
    )
    if not (count_sum == validated["case_count"]).all():
        raise ValueError("pairwise lower-loss counts must add to case_count")
    return validated


def write_calibration_figure(
    *,
    calibration_bins: pd.DataFrame,
    summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a compact calibration and forecast-quality diagnostic figure."""

    colors = {
        "polymarket_state_final_50": "#2563eb",
        "rieke_state_final_50": "#059669",
        "two_seventy_state_final_50": "#d97706",
        "polymarket_state_poll_13": "#60a5fa",
        "poll_derived_state_13": "#7c3aed",
        "polymarket_final_snapshot_8": "#1d4ed8",
        "fivethirtyeight_final_snapshot_8": "#dc2626",
    }
    fig, axes = plt.subplots(2, 2, figsize=FIGURE_SIZE_INCHES)
    fig.suptitle(
        "H1 forecast-quality scorecard and sparse-bin calibration",
        fontsize=15,
        fontweight="bold",
    )

    _plot_loss_advantage_panel(axes[0, 0], pairwise)
    _plot_pairwise_panel(axes[0, 1], pairwise)
    _plot_reliability_panel(
        ax=axes[1, 0],
        calibration_bins=calibration_bins,
        summary=summary,
        source_ids=[
            "polymarket_state_final_50",
            "rieke_state_final_50",
            "two_seventy_state_final_50",
        ],
        colors=colors,
        title="Sparse reliability bins for n>=30 sources",
    )
    _plot_brier_ece_panel(axes[1, 1], summary, colors)

    fig.text(
        0.5,
        0.012,
        (
            "Positive loss advantage means lower Polymarket mean Brier. "
            "Reliability points are not connected because fixed 20-point bins "
            "are sparse; n<30 sources are excluded from the reliability panel "
            "but retained in the scorecards."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    forecast_cases: pd.DataFrame,
    calibration_bins: pd.DataFrame,
    summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    rieke_case_input: Path,
    two_seventy_case_input: Path,
    state_poll_case_input: Path,
    final_snapshot_case_input: Path,
    forecast_case_output: Path,
    bin_output: Path,
    summary_output: Path,
    pairwise_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the H1 calibration diagnostic."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_fixed_bin_calibration_diagnostic",
            "calculation_scope": "deterministic_python_from_precomputed_h1_cases",
            "fixed_bin_count": BIN_COUNT,
            "fixed_bin_width_probability_points": 1.0 / BIN_COUNT,
            "daily_national_reliability_curve_excluded": True,
            "sparse_reliability_points_not_connected": True,
            "reliability_panel_min_case_count": 30,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "forecast_case_row_count": int(len(forecast_cases)),
            "forecast_source_count": int(forecast_cases["forecast_source_id"].nunique()),
            "calibration_bin_row_count": int(len(calibration_bins)),
            "summary_row_count": int(len(summary)),
            "pairwise_comparison_count": int(len(pairwise)),
            "aggregate_support_row_count": int(
                pairwise["aggregate_mean_supports_polymarket"].sum()
            ),
            "majority_support_row_count": int(
                pairwise["majority_cases_supports_polymarket"].sum()
            ),
            "broad_many_cases_support_row_count": int(
                pairwise["broad_many_cases_claim_supported"].sum()
            ),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "figure_width_inches": FIGURE_SIZE_INCHES[0],
            "figure_height_inches": FIGURE_SIZE_INCHES[1],
            "figure_aspect_ratio": FIGURE_SIZE_INCHES[0] / FIGURE_SIZE_INCHES[1],
            "reliability_panel_x_limits": [0.0, 1.0],
            "reliability_panel_y_limits": [0.0, 1.0],
            "reliability_panel_aspect": "equal",
        },
        "source_paths": {
            "rieke_case_input": str(rieke_case_input),
            "two_seventy_case_input": str(two_seventy_case_input),
            "state_poll_case_input": str(state_poll_case_input),
            "final_snapshot_case_input": str(final_snapshot_case_input),
            "forecast_cases": str(forecast_case_output),
            "calibration_bins": str(bin_output),
            "summary": str(summary_output),
            "pairwise": str(pairwise_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "state_rows_share_one_election_context": True,
            "limited_case_sets_have_low_bin_counts": True,
            "poll_transform_rows_are_model_dependent": True,
            "two_seventy_safe_state_probabilities_are_censored": True,
            "calibration_bins_are_descriptive_not_significance_tests": True,
            "goal_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _source_rows(
    *,
    frame: pd.DataFrame,
    case_set_id: str,
    case_unit: str,
    forecast_source_id: str,
    forecast_source_label: str,
    source_family: str,
    probability_column: str,
    label_column: str,
    probability_note: str,
    source_artifact: str,
    limitation: str,
) -> list[dict[str, Any]]:
    probabilities = pd.to_numeric(frame[probability_column], errors="raise")
    outcomes = pd.to_numeric(frame["outcome_value"], errors="raise")
    rows: list[dict[str, Any]] = []
    for idx, (_, row) in enumerate(frame.iterrows()):
        probability = float(probabilities.iloc[idx])
        outcome = float(outcomes.iloc[idx])
        label = str(row[label_column])
        rows.append(
            {
                "case_set_id": case_set_id,
                "case_unit": case_unit,
                "forecast_source_id": forecast_source_id,
                "forecast_source_label": forecast_source_label,
                "source_family": source_family,
                "canonical_case_id": _canonical_case_id(case_set_id, row, label),
                "case_label": label,
                "outcome_value": outcome,
                "forecast_probability": probability,
                "brier_loss": (probability - outcome) ** 2,
                "is_polymarket": forecast_source_id.startswith("polymarket"),
                "probability_note": probability_note,
                "source_artifact": source_artifact,
                "limitation": limitation,
            }
        )
    return rows


def _pairwise_row(
    *,
    frame: pd.DataFrame,
    comparison_id: str,
    case_set_label: str,
    comparator_label: str,
    comparator_probability_column: str,
    limitation: str,
) -> dict[str, Any]:
    if frame.empty:
        raise ValueError(f"pairwise frame is empty: {comparison_id}")
    outcome = pd.to_numeric(frame["outcome_value"], errors="raise")
    pm_probability = pd.to_numeric(frame["polymarket_probability"], errors="raise")
    comparator_probability = pd.to_numeric(
        frame[comparator_probability_column], errors="raise"
    )
    pm_brier = (pm_probability - outcome) ** 2
    comparator_brier = (comparator_probability - outcome) ** 2
    advantage = comparator_brier - pm_brier
    tolerance = 1e-12
    pm_lower = int((advantage > tolerance).sum())
    comparator_lower = int((advantage < -tolerance).sum())
    ties = int((advantage.abs() <= tolerance).sum())
    case_count = int(len(frame))
    mean_pm = float(pm_brier.mean())
    mean_comparator = float(comparator_brier.mean())
    mean_advantage = mean_comparator - mean_pm
    aggregate_support = mean_advantage > 0.0
    majority_support = pm_lower > comparator_lower and pm_lower > (case_count / 2.0)
    broad_support = aggregate_support and majority_support and case_count >= 30
    return {
        "comparison_id": comparison_id,
        "case_set_label": case_set_label,
        "comparator_label": comparator_label,
        "case_count": case_count,
        "polymarket_lower_loss_count": pm_lower,
        "comparator_lower_loss_count": comparator_lower,
        "tie_count": ties,
        "polymarket_lower_loss_share": pm_lower / case_count,
        "mean_polymarket_brier": mean_pm,
        "mean_comparator_brier": mean_comparator,
        "mean_loss_advantage": mean_advantage,
        "aggregate_mean_supports_polymarket": aggregate_support,
        "majority_cases_supports_polymarket": majority_support,
        "broad_many_cases_claim_supported": broad_support,
        "limitation": limitation,
    }


def _plot_reliability_panel(
    *,
    ax: plt.Axes,
    calibration_bins: pd.DataFrame,
    summary: pd.DataFrame,
    source_ids: Sequence[str],
    colors: dict[str, str],
    title: str,
) -> None:
    ax.plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1.0)
    for source_id in source_ids:
        rows = calibration_bins.loc[
            calibration_bins["forecast_source_id"] == source_id
        ].sort_values("mean_forecast_probability")
        if rows.empty:
            continue
        label = str(rows["forecast_source_label"].iloc[0])
        summary_row = summary.loc[summary["forecast_source_id"] == source_id].iloc[0]
        case_count = int(summary_row["case_count"])
        ece = float(summary_row["expected_calibration_error"])
        mean_brier = float(summary_row["mean_brier_loss"])
        sizes = 42 + rows["case_count"] * 11
        ax.scatter(
            rows["mean_forecast_probability"],
            rows["observed_frequency"],
            s=sizes,
            color=colors.get(source_id, "#111827"),
            alpha=0.78,
            edgecolor="#111827",
            linewidth=0.45,
            label=(
                f"{label} (n={case_count}, "
                f"Brier={mean_brier:.3f}, ECE={ece:.3f})"
            ),
        )
    ax.set_title(title)
    ax.set_xlabel("Mean forecast probability in bin")
    ax.set_ylabel("Observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=7.0, loc="upper left")
    ax.text(
        0.03,
        0.08,
        "Point size = bin case count",
        transform=ax.transAxes,
        fontsize=8,
        color="#374151",
    )


def _plot_loss_advantage_panel(ax: plt.Axes, pairwise: pd.DataFrame) -> None:
    ordered = pairwise.sort_values("mean_loss_advantage", ascending=True)
    labels = [_short_comparison_label(value) for value in ordered["comparison_id"]]
    y_positions = list(range(len(ordered)))
    max_abs = max(0.01, float(ordered["mean_loss_advantage"].abs().max()))
    colors = [
        "#2563eb" if float(value) > 0 else "#dc2626"
        for value in ordered["mean_loss_advantage"]
    ]
    ax.set_xlim(-max_abs * 0.25, max_abs * 2.05)
    ax.barh(
        y_positions,
        ordered["mean_loss_advantage"],
        color=colors,
        alpha=0.84,
    )
    ax.axvline(0, color="#111827", linewidth=0.9)
    for y, (_, row) in zip(y_positions, ordered.iterrows()):
        advantage = float(row["mean_loss_advantage"])
        pm_lower = int(row["polymarket_lower_loss_count"])
        comparator_lower = int(row["comparator_lower_loss_count"])
        case_count = int(row["case_count"])
        majority = (
            "PM majority"
            if bool(row["majority_cases_supports_polymarket"])
            else "no PM majority"
        )
        ax.text(
            max_abs * 1.08,
            y,
            (
                f"{advantage:+.3f} | PM {pm_lower}, "
                f"comp {comparator_lower}, tie {int(row['tie_count'])} | {majority}"
            ),
            va="center",
            ha="left",
            fontsize=7.3,
            color="#374151",
        )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Mean loss advantage: comparator Brier - PM Brier")
    ax.set_title("Aggregate Brier advantage by comparison")
    ax.grid(axis="x", alpha=0.25)


def _plot_brier_ece_panel(
    ax: plt.Axes, summary: pd.DataFrame, colors: dict[str, str]
) -> None:
    ordered = summary.sort_values(["case_count", "mean_brier_loss"], ascending=[False, True])
    labels = [_short_source_label(value) for value in ordered["forecast_source_id"]]
    y_positions = range(len(ordered))
    bar_colors = [
        colors.get(source_id, "#64748b") for source_id in ordered["forecast_source_id"]
    ]
    ax.barh(
        [y - 0.18 for y in y_positions],
        ordered["mean_brier_loss"],
        height=0.34,
        color=bar_colors,
        alpha=0.82,
        label="Mean Brier",
    )
    ax.barh(
        [y + 0.18 for y in y_positions],
        ordered["expected_calibration_error"],
        height=0.34,
        color="#94a3b8",
        alpha=0.72,
        label="Fixed-bin ECE",
    )
    for y, (_, row) in zip(y_positions, ordered.iterrows()):
        ax.text(
            max(float(row["mean_brier_loss"]), float(row["expected_calibration_error"]))
            + 0.006,
            y,
            f"n={int(row['case_count'])}",
            va="center",
            fontsize=7.5,
            color="#374151",
        )
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Score")
    ax.set_title("Mean Brier and fixed-bin calibration error")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")


def _plot_pairwise_panel(ax: plt.Axes, pairwise: pd.DataFrame) -> None:
    ordered = pairwise.sort_values("case_count", ascending=False)
    labels = [_short_comparison_label(value) for value in ordered["comparison_id"]]
    y_positions = range(len(ordered))
    pm_share = ordered["polymarket_lower_loss_count"] / ordered["case_count"]
    comparator_share = ordered["comparator_lower_loss_count"] / ordered["case_count"]
    tie_share = ordered["tie_count"] / ordered["case_count"]
    ax.barh(y_positions, pm_share, color="#2563eb", alpha=0.82, label="PM lower")
    ax.barh(
        y_positions,
        comparator_share,
        left=pm_share,
        color="#dc2626",
        alpha=0.75,
        label="Comparator lower",
    )
    ax.barh(
        y_positions,
        tie_share,
        left=pm_share + comparator_share,
        color="#9ca3af",
        alpha=0.75,
        label="Tie",
    )
    for y, (_, row) in zip(y_positions, ordered.iterrows()):
        ax.text(
            1.01,
            y,
            (
                f"{int(row['polymarket_lower_loss_count'])}/"
                f"{int(row['comparator_lower_loss_count'])}/"
                f"{int(row['tie_count'])}"
            ),
            va="center",
            fontsize=7.5,
            color="#374151",
        )
    ax.axvline(0.5, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_xlim(0, 1.22)
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Share of cases")
    ax.set_title("Individual lower-loss counts (PM / comparator / tie)")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")


def _canonical_case_id(case_set_id: str, row: pd.Series, label: str) -> str:
    if "case_id" in row and pd.notna(row["case_id"]):
        return str(row["case_id"])
    normalized = (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("__", "_")
    )
    return f"{case_set_id}_{normalized}"


def _short_source_label(source_id: str) -> str:
    labels = {
        "polymarket_state_final_50": "PM 50-state",
        "rieke_state_final_50": "Rieke 50-state",
        "two_seventy_state_final_50": "270/JHK 50-state",
        "polymarket_state_poll_13": "PM 13-state",
        "poll_derived_state_13": "538 poll transform",
        "polymarket_final_snapshot_8": "PM final 8",
        "fivethirtyeight_final_snapshot_8": "538 final 8",
    }
    return labels.get(source_id, source_id)


def _short_comparison_label(comparison_id: str) -> str:
    labels = {
        "state_final_pm_vs_rieke": "PM vs Rieke",
        "state_final_pm_vs_270towin": "PM vs 270/JHK",
        "state_exact_pm_vs_270towin": "PM vs 270 exact",
        "state_poll_pm_vs_538_transform": "PM vs poll transform",
        "final_snapshot_pm_vs_538": "PM vs 538 final",
    }
    return labels.get(comparison_id, comparison_id)


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
        raise ValueError(f"{label} contains forbidden raw-trade columns: {matches}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rieke-case-input", type=Path, default=RIEKE_CASE_INPUT)
    parser.add_argument(
        "--two-seventy-case-input", type=Path, default=TWO_SEVENTY_CASE_INPUT
    )
    parser.add_argument(
        "--state-poll-case-input", type=Path, default=STATE_POLL_CASE_INPUT
    )
    parser.add_argument(
        "--final-snapshot-case-input", type=Path, default=FINAL_SNAPSHOT_CASE_INPUT
    )
    parser.add_argument(
        "--forecast-case-output", type=Path, default=FORECAST_CASE_OUTPUT
    )
    parser.add_argument("--bin-output", type=Path, default=BIN_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--pairwise-output", type=Path, default=PAIRWISE_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_calibration_diagnostic_outputs(
            rieke_case_input=args.rieke_case_input,
            two_seventy_case_input=args.two_seventy_case_input,
            state_poll_case_input=args.state_poll_case_input,
            final_snapshot_case_input=args.final_snapshot_case_input,
            forecast_case_output=args.forecast_case_output,
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
