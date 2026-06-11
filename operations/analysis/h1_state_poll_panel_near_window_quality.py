"""Score-quality diagnostic for the H1 <=90-day state-date panel window.

The horizon diagnostics show a late-window Polymarket advantage. This module
adds a compact score-quality view for that same <=90-day window: fixed
calibration bins, mean Brier, expected calibration error, and probability
separation between resolved Republican-win and Republican-loss state rows.
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

from operations.analysis.h1_state_poll_panel_horizon_diagnostic import (
    CASE_INPUT,
    NEAR_HORIZON_MAX_DAYS,
    add_horizon_columns,
)
from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


FORECAST_ROWS_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality_rows.csv"
BIN_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality_bins.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_near_window_quality_metadata.json"

BIN_COUNT = 5

FORECAST_ROW_COLUMNS: tuple[str, ...] = (
    "source_id",
    "source_label",
    "state",
    "forecast_date",
    "case_id",
    "days_to_election",
    "outcome_value",
    "forecast_probability",
    "brier_loss",
    "row_unit",
    "limitation",
)

BIN_COLUMNS: tuple[str, ...] = (
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


@dataclass(frozen=True)
class H1NearWindowQualityResult:
    """Summary of generated <=90-day score-quality artifacts."""

    forecast_rows_path: Path
    bins_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    row_count: int
    state_count: int
    polymarket_mean_brier: float
    poll_derived_mean_brier: float
    polymarket_expected_calibration_error: float
    poll_derived_expected_calibration_error: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "forecast_rows_path": str(self.forecast_rows_path),
            "bins_path": str(self.bins_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "state_count": self.state_count,
            "polymarket_mean_brier": self.polymarket_mean_brier,
            "poll_derived_mean_brier": self.poll_derived_mean_brier,
            "polymarket_expected_calibration_error": (
                self.polymarket_expected_calibration_error
            ),
            "poll_derived_expected_calibration_error": (
                self.poll_derived_expected_calibration_error
            ),
        }


def generate_h1_state_poll_panel_near_window_quality_outputs(
    *,
    case_input: Path = CASE_INPUT,
    forecast_rows_output: Path = FORECAST_ROWS_OUTPUT,
    bin_output: Path = BIN_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1NearWindowQualityResult:
    """Generate <=90-day score-quality rows, bins, summary, and figure."""

    cases = add_horizon_columns(read_panel_cases(case_input))
    near_cases = cases.loc[cases["days_to_election"] <= NEAR_HORIZON_MAX_DAYS].copy()
    if near_cases.empty:
        raise ValueError("<=90-day horizon window must not be empty")
    forecast_rows = validate_forecast_rows(build_forecast_rows(near_cases))
    bins = build_calibration_bins(forecast_rows)
    summary = build_quality_summary(forecast_rows, bins)

    forecast_rows_output.parent.mkdir(parents=True, exist_ok=True)
    forecast_rows.to_csv(forecast_rows_output, index=False)
    bins.to_csv(bin_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_quality_figure(
        forecast_rows=forecast_rows,
        bins=bins,
        summary=summary,
        output_path=figure_output,
    )
    metadata = build_metadata(
        forecast_rows=forecast_rows,
        bins=bins,
        summary=summary,
        case_input=case_input,
        forecast_rows_output=forecast_rows_output,
        bin_output=bin_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    by_source = summary.set_index("source_id")
    return H1NearWindowQualityResult(
        forecast_rows_path=forecast_rows_output,
        bins_path=bin_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        row_count=int(by_source.loc["polymarket", "row_count"]),
        state_count=int(by_source.loc["polymarket", "state_count"]),
        polymarket_mean_brier=float(by_source.loc["polymarket", "mean_brier_loss"]),
        poll_derived_mean_brier=float(
            by_source.loc["poll_derived", "mean_brier_loss"]
        ),
        polymarket_expected_calibration_error=float(
            by_source.loc["polymarket", "expected_calibration_error"]
        ),
        poll_derived_expected_calibration_error=float(
            by_source.loc["poll_derived", "expected_calibration_error"]
        ),
    )


def build_forecast_rows(near_cases: pd.DataFrame) -> pd.DataFrame:
    """Convert <=90-day panel cases to long forecast rows."""

    rows: list[dict[str, Any]] = []
    source_specs = [
        ("polymarket", "Polymarket", "polymarket_probability", "polymarket_brier"),
        (
            "poll_derived",
            "538 poll-derived",
            "poll_derived_probability",
            "poll_derived_brier",
        ),
    ]
    for _, case in near_cases.iterrows():
        for source_id, source_label, probability_col, brier_col in source_specs:
            rows.append(
                {
                    "source_id": source_id,
                    "source_label": source_label,
                    "state": str(case["state"]),
                    "forecast_date": pd.Timestamp(case["forecast_date"]).strftime("%Y-%m-%d"),
                    "case_id": str(case["case_id"]),
                    "days_to_election": int(case["days_to_election"]),
                    "outcome_value": float(case["outcome_value"]),
                    "forecast_probability": float(case[probability_col]),
                    "brier_loss": float(case[brier_col]),
                    "row_unit": "state_date_forecast_pair_within_90_days",
                    "limitation": (
                        "Rows are repeated forecasts inside one election context, "
                        "not independent elections."
                    ),
                }
            )
    return pd.DataFrame(rows, columns=FORECAST_ROW_COLUMNS)


def validate_forecast_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate long-form <=90-day forecast rows."""

    missing = sorted(set(FORECAST_ROW_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"forecast rows missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"forecast rows contain forbidden raw-trade columns: {forbidden}")
    normalized = frame.loc[:, list(FORECAST_ROW_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("forecast rows must not be empty")
    for column in ("days_to_election", "outcome_value", "forecast_probability", "brier_loss"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome values must be binary")
    if not normalized["forecast_probability"].between(0.0, 1.0).all():
        raise ValueError("forecast probabilities must be in [0, 1]")
    expected = (normalized["forecast_probability"] - normalized["outcome_value"]) ** 2
    if not normalized["brier_loss"].sub(expected).abs().le(1e-12).all():
        raise ValueError("brier_loss must equal squared forecast error")
    return normalized.sort_values(["source_id", "state", "forecast_date"]).reset_index(drop=True)


def build_calibration_bins(forecast_rows: pd.DataFrame) -> pd.DataFrame:
    """Build fixed 20-point calibration bins for each source."""

    rows: list[dict[str, Any]] = []
    for source_id, group in forecast_rows.groupby("source_id", sort=True):
        source_label = str(group["source_label"].iloc[0])
        for bin_index in range(BIN_COUNT):
            bin_start = bin_index / BIN_COUNT
            bin_end = (bin_index + 1) / BIN_COUNT
            if bin_index == 0:
                mask = group["forecast_probability"].between(bin_start, bin_end, inclusive="both")
            else:
                mask = (group["forecast_probability"] > bin_start) & (
                    group["forecast_probability"] <= bin_end
                )
            subset = group.loc[mask]
            if subset.empty:
                mean_probability = float("nan")
                observed_frequency = float("nan")
                mean_brier = float("nan")
                forecast_minus_observed = float("nan")
                absolute_gap = float("nan")
                positive_count = 0
            else:
                mean_probability = float(subset["forecast_probability"].mean())
                observed_frequency = float(subset["outcome_value"].mean())
                mean_brier = float(subset["brier_loss"].mean())
                forecast_minus_observed = mean_probability - observed_frequency
                absolute_gap = abs(forecast_minus_observed)
                positive_count = int(subset["outcome_value"].sum())
            rows.append(
                {
                    "source_id": source_id,
                    "source_label": source_label,
                    "bin_index": bin_index,
                    "bin_label": f"{bin_start:.1f}-{bin_end:.1f}",
                    "bin_start": bin_start,
                    "bin_end": bin_end,
                    "row_count": int(len(subset)),
                    "positive_count": positive_count,
                    "mean_forecast_probability": mean_probability,
                    "observed_frequency": observed_frequency,
                    "mean_brier_loss": mean_brier,
                    "forecast_minus_observed": forecast_minus_observed,
                    "absolute_calibration_gap": absolute_gap,
                }
            )
    return pd.DataFrame(rows, columns=BIN_COLUMNS)


def build_quality_summary(forecast_rows: pd.DataFrame, bins: pd.DataFrame) -> pd.DataFrame:
    """Build source-level <=90-day quality summary."""

    rows: list[dict[str, Any]] = []
    for source_id, group in forecast_rows.groupby("source_id", sort=True):
        source_label = str(group["source_label"].iloc[0])
        source_bins = bins.loc[(bins["source_id"] == source_id) & (bins["row_count"] > 0)]
        positive = group.loc[group["outcome_value"] == 1.0, "forecast_probability"]
        negative = group.loc[group["outcome_value"] == 0.0, "forecast_probability"]
        mean_positive = float(positive.mean())
        mean_negative = float(negative.mean())
        weights = source_bins["row_count"] / len(group)
        ece = float((weights * source_bins["absolute_calibration_gap"]).sum())
        rmse = float(((weights * source_bins["absolute_calibration_gap"] ** 2).sum()) ** 0.5)
        rows.append(
            {
                "source_id": source_id,
                "source_label": source_label,
                "row_count": int(len(group)),
                "state_count": int(group["state"].nunique()),
                "positive_rate": float(group["outcome_value"].mean()),
                "mean_forecast_probability": float(group["forecast_probability"].mean()),
                "mean_brier_loss": float(group["brier_loss"].mean()),
                "brier_skill_vs_50_percent": 1.0 - float(group["brier_loss"].mean()) / 0.25,
                "nonempty_bin_count": int(len(source_bins)),
                "expected_calibration_error": ece,
                "root_mean_square_calibration_error": rmse,
                "max_absolute_calibration_gap": float(source_bins["absolute_calibration_gap"].max()),
                "mean_probability_positive_outcomes": mean_positive,
                "mean_probability_negative_outcomes": mean_negative,
                "probability_separation": mean_positive - mean_negative,
                "calibration_scope": "fixed_20_point_bins_within_90_days",
                "limitation": (
                    "Calibration bins are repeated state-date forecasts inside "
                    "one election context."
                ),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_quality_figure(
    *,
    forecast_rows: pd.DataFrame,
    bins: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the <=90-day score-quality figure."""

    by_source = summary.set_index("source_id")
    fig, axes = plt.subplots(2, 2, figsize=(13.8, 8.6))
    fig.suptitle(
        "H1 <=90-Day Score Quality: Polymarket vs 538 Poll-Derived",
        fontsize=13.5,
        fontweight="bold",
    )

    labels = ["Polymarket", "538 poll-derived"]
    source_ids = ["polymarket", "poll_derived"]
    colors = ["#2563eb", "#7c3aed"]

    metric_names = ["mean_brier_loss", "expected_calibration_error", "probability_separation"]
    x_positions = range(len(metric_names))
    width = 0.36
    for idx, source_id in enumerate(source_ids):
        values = [float(by_source.loc[source_id, metric]) for metric in metric_names]
        axes[0, 0].bar(
            [position + (idx - 0.5) * width for position in x_positions],
            values,
            width=width,
            label=labels[idx],
            color=colors[idx],
        )
        for position, value in zip(x_positions, values):
            axes[0, 0].text(
                position + (idx - 0.5) * width,
                value + 0.01,
                f"{value:.3f}",
                ha="center",
                fontsize=8,
            )
    axes[0, 0].set_xticks(
        list(x_positions),
        ["Mean\nBrier", "ECE", "Probability\nseparation"],
    )
    axes[0, 0].set_title("Source-level score metrics")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, axis="y", alpha=0.25)

    for source_id, color, label in zip(source_ids, colors, labels):
        source_bins = bins.loc[(bins["source_id"] == source_id) & (bins["row_count"] > 0)]
        axes[0, 1].plot(
            source_bins["mean_forecast_probability"],
            source_bins["observed_frequency"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )
        for _, row in source_bins.iterrows():
            x_offset = 10 if source_id == "polymarket" else -10
            if row["observed_frequency"] >= 0.95:
                y_offset = -14
            elif row["observed_frequency"] <= 0.05:
                y_offset = 14
            else:
                y_offset = 12 if source_id == "polymarket" else -14
            axes[0, 1].annotate(
                f"n={int(row['row_count'])}",
                xy=(row["mean_forecast_probability"], row["observed_frequency"]),
                xytext=(x_offset, y_offset),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=7,
                color=color,
                bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "none", "alpha": 0.82},
                clip_on=False,
                zorder=5,
            )
    axes[0, 1].plot([0, 1], [0, 1], color="#6b7280", linestyle="--", linewidth=1)
    axes[0, 1].set_xlim(0, 1)
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].set_xlabel("Mean forecast probability")
    axes[0, 1].set_ylabel("Observed frequency")
    axes[0, 1].set_title("Fixed-bin calibration (n = row count)")
    axes[0, 1].legend(fontsize=8, loc="lower right")
    axes[0, 1].grid(True, alpha=0.25)

    box_data = []
    box_labels = []
    for source_id, label in zip(source_ids, labels):
        source_rows = forecast_rows.loc[forecast_rows["source_id"] == source_id]
        for outcome_value, outcome_label in [(0.0, "lost"), (1.0, "won")]:
            box_data.append(
                source_rows.loc[
                    source_rows["outcome_value"] == outcome_value,
                    "forecast_probability",
                ].to_numpy()
            )
            box_labels.append(f"{label}\n{outcome_label}")
    axes[1, 0].boxplot(box_data, tick_labels=box_labels, patch_artist=True)
    for patch, color in zip(axes[1, 0].artists, ["#93c5fd", "#93c5fd", "#c4b5fd", "#c4b5fd"]):
        patch.set_facecolor(color)
    axes[1, 0].set_ylim(0, 1)
    axes[1, 0].set_ylabel("Forecast probability")
    axes[1, 0].set_title("Probability separation by resolved outcome")
    axes[1, 0].grid(True, axis="y", alpha=0.25)

    pm = forecast_rows.loc[forecast_rows["source_id"] == "polymarket", ["case_id", "brier_loss"]]
    poll = forecast_rows.loc[forecast_rows["source_id"] == "poll_derived", ["case_id", "brier_loss"]]
    joined = pm.merge(poll, on="case_id", suffixes=("_pm", "_poll"))
    pm_lower = int((joined["brier_loss_pm"] < joined["brier_loss_poll"]).sum())
    poll_lower = int((joined["brier_loss_poll"] < joined["brier_loss_pm"]).sum())
    axes[1, 1].bar(
        ["PM lower", "Poll lower"],
        [pm_lower, poll_lower],
        color=["#2563eb", "#7c3aed"],
    )
    axes[1, 1].set_title("<=90-day lower-loss rows")
    axes[1, 1].set_ylabel("State-date rows")
    axes[1, 1].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate([pm_lower, poll_lower]):
        axes[1, 1].text(idx, value + 5, f"{value}", ha="center", fontsize=9)

    fig.text(
        0.5,
        0.012,
        (
            "Lower Brier and lower ECE are better; higher probability separation "
            "means better discrimination between won and lost state rows."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    forecast_rows: pd.DataFrame,
    bins: pd.DataFrame,
    summary: pd.DataFrame,
    case_input: Path,
    forecast_rows_output: Path,
    bin_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the <=90-day score-quality diagnostic."""

    by_source = summary.set_index("source_id")
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_near_window_score_quality",
            "calculation_scope": "deterministic_python_from_state_date_poll_panel_cases",
            "near_horizon_max_days": NEAR_HORIZON_MAX_DAYS,
            "bin_count": BIN_COUNT,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "forecast_row_count": int(len(forecast_rows)),
            "case_row_count": int(len(forecast_rows) / 2),
            "state_count": int(forecast_rows["state"].nunique()),
            "bin_row_count": int(len(bins)),
            "polymarket_mean_brier": float(by_source.loc["polymarket", "mean_brier_loss"]),
            "poll_derived_mean_brier": float(by_source.loc["poll_derived", "mean_brier_loss"]),
            "polymarket_expected_calibration_error": float(
                by_source.loc["polymarket", "expected_calibration_error"]
            ),
            "poll_derived_expected_calibration_error": float(
                by_source.loc["poll_derived", "expected_calibration_error"]
            ),
            "polymarket_probability_separation": float(
                by_source.loc["polymarket", "probability_separation"]
            ),
            "poll_derived_probability_separation": float(
                by_source.loc["poll_derived", "probability_separation"]
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "h1_goal_completion_status": "not_proven",
        },
        "source_paths": {
            "case_input": str(case_input),
            "forecast_rows": str(forecast_rows_output),
            "bins": str(bin_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "calibration_rows_are_repeated_forecasts": True,
            "state_rows_share_one_election_context": True,
            "does_not_prove_broad_independent_many_cases_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--forecast-rows-output", type=Path, default=FORECAST_ROWS_OUTPUT)
    parser.add_argument("--bin-output", type=Path, default=BIN_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_near_window_quality_outputs(
            case_input=args.case_input,
            forecast_rows_output=args.forecast_rows_output,
            bin_output=args.bin_output,
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
