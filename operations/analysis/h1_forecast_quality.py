"""Build clearer H1 forecast-quality outputs from deterministic Brier rows.

The existing reliability diagram is weak evidence for calibration because the
baseline contains repeated daily forecasts for one resolved binary election
outcome. This module keeps the valid H1 object narrower: paired daily forecast
losses, mean Brier Scores, head-to-head lower-loss counts, and a readable
figure. It does not use raw polls, RCP, LLMs, agents, MCP, ML, or database
writes.
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR


BRIER_INPUT = RESULTS_DIR / "h1_brier_scores.csv"
DM_INPUT = RESULTS_DIR / "h1_diebold_mariano.json"
SOURCE_SUMMARY_OUTPUT = RESULTS_DIR / "h1_forecast_quality_sources.csv"
PAIRWISE_OUTPUT = RESULTS_DIR / "h1_forecast_quality_pairwise.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_forecast_quality.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_forecast_quality_metadata.json"

SOURCE_COLUMNS: tuple[str, ...] = (
    "source",
    "source_label",
    "source_role",
    "row_count",
    "mean_brier_score",
    "median_brier_score",
    "mean_forecast",
    "min_forecast",
    "max_forecast",
)

PAIRWISE_COLUMNS: tuple[str, ...] = (
    "comparison_id",
    "comparator",
    "comparator_label",
    "comparator_role",
    "comparison_row_count",
    "polymarket_lower_loss_count",
    "comparator_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "comparator_better_share",
    "tie_share",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "relative_loss_reduction",
    "sign_test_p_value",
    "dm_p_value",
    "allowed_interpretation",
    "limitation",
)

SOURCE_SPECS: dict[str, dict[str, str]] = {
    "polymarket": {
        "label": "Polymarket",
        "role": "decentralized_prediction_market_probability",
        "forecast_col": "forecast_polymarket",
        "brier_col": "bs_polymarket",
    },
    "fivethirtyeight": {
        "label": "FiveThirtyEight",
        "role": "traditional_poll_based_probability_forecast",
        "forecast_col": "forecast_fivethirtyeight",
        "brier_col": "bs_fivethirtyeight",
    },
    "always_50": {
        "label": "Always 50%",
        "role": "uninformative_probability_baseline",
        "forecast_col": "forecast_always_50",
        "brier_col": "bs_always_50",
    },
    "prior_day_polymarket": {
        "label": "Prior-day Polymarket",
        "role": "persistence_baseline",
        "forecast_col": "forecast_prior_day",
        "brier_col": "bs_prior_day",
    },
}


@dataclass(frozen=True)
class H1ForecastQualityResult:
    """Summary of generated H1 forecast-quality artifacts."""

    source_summary_path: Path
    pairwise_path: Path
    figure_path: Path
    metadata_path: Path
    source_row_count: int
    pairwise_row_count: int
    fivethirtyeight_polymarket_better_count: int
    fivethirtyeight_comparison_count: int
    fivethirtyeight_polymarket_better_share: float
    fivethirtyeight_mean_loss_advantage: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "source_summary_path": str(self.source_summary_path),
            "pairwise_path": str(self.pairwise_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "source_row_count": self.source_row_count,
            "pairwise_row_count": self.pairwise_row_count,
            "fivethirtyeight_polymarket_better_count": (
                self.fivethirtyeight_polymarket_better_count
            ),
            "fivethirtyeight_comparison_count": (
                self.fivethirtyeight_comparison_count
            ),
            "fivethirtyeight_polymarket_better_share": (
                self.fivethirtyeight_polymarket_better_share
            ),
            "fivethirtyeight_mean_loss_advantage": (
                self.fivethirtyeight_mean_loss_advantage
            ),
        }


def generate_h1_forecast_quality_outputs(
    *,
    brier_input: Path = BRIER_INPUT,
    dm_input: Path = DM_INPUT,
    source_summary_output: Path = SOURCE_SUMMARY_OUTPUT,
    pairwise_output: Path = PAIRWISE_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1ForecastQualityResult:
    """Generate H1 source summary, pairwise comparison, figure, and metadata."""

    brier = read_h1_brier_rows(brier_input)
    dm_results = read_dm_results(dm_input)
    source_summary = build_source_summary(brier)
    pairwise = build_pairwise_summary(brier, dm_results=dm_results)

    source_summary_output.parent.mkdir(parents=True, exist_ok=True)
    pairwise_output.parent.mkdir(parents=True, exist_ok=True)
    source_summary.to_csv(source_summary_output, index=False)
    pairwise.to_csv(pairwise_output, index=False)
    write_forecast_quality_figure(
        brier=brier,
        source_summary=source_summary,
        pairwise=pairwise,
        output_path=figure_output,
    )
    metadata = build_metadata(
        brier_input=brier_input,
        dm_input=dm_input,
        source_summary_output=source_summary_output,
        pairwise_output=pairwise_output,
        figure_output=figure_output,
        source_summary=source_summary,
        pairwise=pairwise,
        brier=brier,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fte = pairwise.loc[pairwise["comparator"] == "fivethirtyeight"].iloc[0]
    return H1ForecastQualityResult(
        source_summary_path=source_summary_output,
        pairwise_path=pairwise_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        source_row_count=int(len(source_summary)),
        pairwise_row_count=int(len(pairwise)),
        fivethirtyeight_polymarket_better_count=int(
            fte["polymarket_lower_loss_count"]
        ),
        fivethirtyeight_comparison_count=int(fte["comparison_row_count"]),
        fivethirtyeight_polymarket_better_share=float(
            fte["polymarket_better_share"]
        ),
        fivethirtyeight_mean_loss_advantage=float(
            fte["mean_loss_advantage"]
        ),
    )


def read_h1_brier_rows(path: Path) -> pd.DataFrame:
    """Read and validate the deterministic H1 Brier row artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 Brier input not found: {path}")
    frame = pd.read_csv(path)
    required = ["date"]
    for spec in SOURCE_SPECS.values():
        required.extend([spec["forecast_col"], spec["brier_col"]])
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 Brier input missing columns: {missing}")
    normalized = frame.loc[:, required].copy()
    normalized["date"] = normalized["date"].astype(str)
    for column in required:
        if column == "date":
            continue
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for spec in SOURCE_SPECS.values():
        forecast_col = spec["forecast_col"]
        brier_col = spec["brier_col"]
        if not normalized[forecast_col].between(0.0, 1.0).all():
            raise ValueError(f"{forecast_col} values must be probabilities in [0, 1]")
        if (normalized[brier_col] < 0.0).any():
            raise ValueError(f"{brier_col} values must be non-negative")
    return normalized.sort_values("date").reset_index(drop=True)


def read_dm_results(path: Path) -> dict[tuple[str, str], float]:
    """Read Diebold-Mariano p-values keyed by normalized source labels."""

    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("DM input must contain a list of result objects")
    results: dict[tuple[str, str], float] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        source_1 = _normalize_dm_label(str(item.get("source_1", "")))
        source_2 = _normalize_dm_label(str(item.get("source_2", "")))
        try:
            p_value = float(item["p_value"])
        except (KeyError, TypeError, ValueError):
            continue
        results[(source_1, source_2)] = p_value
        results[(source_2, source_1)] = p_value
    return results


def build_source_summary(brier: pd.DataFrame) -> pd.DataFrame:
    """Build source-level Brier and forecast summaries."""

    rows: list[dict[str, Any]] = []
    for source, spec in SOURCE_SPECS.items():
        forecast = brier[spec["forecast_col"]]
        losses = brier[spec["brier_col"]]
        rows.append(
            {
                "source": source,
                "source_label": spec["label"],
                "source_role": spec["role"],
                "row_count": int(losses.notna().sum()),
                "mean_brier_score": float(losses.mean()),
                "median_brier_score": float(losses.median()),
                "mean_forecast": float(forecast.mean()),
                "min_forecast": float(forecast.min()),
                "max_forecast": float(forecast.max()),
            }
        )
    return pd.DataFrame(rows, columns=SOURCE_COLUMNS)


def build_pairwise_summary(
    brier: pd.DataFrame,
    *,
    dm_results: dict[tuple[str, str], float],
) -> pd.DataFrame:
    """Build pairwise Polymarket-vs-comparator lower-loss counts."""

    rows: list[dict[str, Any]] = []
    pm_loss = brier[SOURCE_SPECS["polymarket"]["brier_col"]]
    for comparator in ("fivethirtyeight", "always_50", "prior_day_polymarket"):
        spec = SOURCE_SPECS[comparator]
        comp_loss = brier[spec["brier_col"]]
        work = pd.DataFrame({"pm": pm_loss, "comparator": comp_loss}).dropna()
        pm_better = int((work["pm"] < work["comparator"]).sum())
        comp_better = int((work["pm"] > work["comparator"]).sum())
        ties = int((work["pm"] == work["comparator"]).sum())
        non_ties = pm_better + comp_better
        sign_p = (
            float(binomtest(pm_better, non_ties, p=0.5).pvalue)
            if non_ties > 0
            else float("nan")
        )
        mean_pm = float(work["pm"].mean())
        mean_comp = float(work["comparator"].mean())
        advantage = mean_comp - mean_pm
        rows.append(
            {
                "comparison_id": f"polymarket_vs_{comparator}",
                "comparator": comparator,
                "comparator_label": spec["label"],
                "comparator_role": spec["role"],
                "comparison_row_count": int(len(work)),
                "polymarket_lower_loss_count": pm_better,
                "comparator_lower_loss_count": comp_better,
                "tie_count": ties,
                "polymarket_better_share": pm_better / len(work) if len(work) else 0.0,
                "comparator_better_share": comp_better / len(work) if len(work) else 0.0,
                "tie_share": ties / len(work) if len(work) else 0.0,
                "mean_polymarket_brier": mean_pm,
                "mean_comparator_brier": mean_comp,
                "mean_loss_advantage": advantage,
                "relative_loss_reduction": advantage / mean_comp if mean_comp else float("nan"),
                "sign_test_p_value": sign_p,
                "dm_p_value": dm_results.get(("polymarket", comparator), float("nan")),
                "allowed_interpretation": (
                    "Polymarket had lower daily Brier loss than the comparator "
                    "on the counted paired forecast days."
                ),
                "limitation": (
                    "Rows are paired daily forecasts for one resolved election "
                    "market, not independent election outcomes. FiveThirtyEight "
                    "is a poll-based probability forecast, not a raw poll share."
                ),
            }
        )
    return pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)


def write_forecast_quality_figure(
    *,
    brier: pd.DataFrame,
    source_summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a clearer H1 forecast-quality figure."""

    labels = source_summary["source_label"].tolist()
    means = source_summary["mean_brier_score"].tolist()
    colors = ["#2563eb", "#dc2626", "#9ca3af", "#f59e0b"]
    fte = pairwise.loc[pairwise["comparator"] == "fivethirtyeight"].iloc[0]

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.4))
    fig.suptitle(
        "H1 Forecast Quality: Polymarket vs poll-based probability forecasts",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].bar(labels, means, color=colors)
    axes[0, 0].set_title("Mean Brier Score (lower is better)")
    axes[0, 0].set_ylabel("Mean Brier Score")
    axes[0, 0].tick_params(axis="x", rotation=18)
    for idx, value in enumerate(means):
        axes[0, 0].text(idx, value + 0.005, f"{value:.3f}", ha="center", fontsize=9)

    count_labels = pairwise["comparator_label"].tolist()
    pm_counts = pairwise["polymarket_lower_loss_count"].tolist()
    comp_counts = pairwise["comparator_lower_loss_count"].tolist()
    tie_counts = pairwise["tie_count"].tolist()
    x = range(len(count_labels))
    axes[0, 1].bar(x, pm_counts, label="Polymarket lower loss", color="#2563eb")
    axes[0, 1].bar(
        x,
        comp_counts,
        bottom=pm_counts,
        label="Comparator lower loss",
        color="#dc2626",
    )
    axes[0, 1].bar(
        x,
        tie_counts,
        bottom=[a + b for a, b in zip(pm_counts, comp_counts, strict=True)],
        label="Tie",
        color="#9ca3af",
    )
    axes[0, 1].set_xticks(list(x), count_labels, rotation=18)
    axes[0, 1].set_title("Head-to-head daily lower-loss counts")
    axes[0, 1].set_ylabel("Paired forecast days")
    axes[0, 1].legend(fontsize=8, loc="upper right")

    dates = pd.to_datetime(brier["date"])
    daily_advantage = brier["bs_fivethirtyeight"] - brier["bs_polymarket"]
    axes[1, 0].plot(dates, daily_advantage.cumsum(), color="#2563eb", lw=2)
    axes[1, 0].axhline(0, color="#111111", lw=0.8)
    axes[1, 0].set_title("Cumulative loss advantage vs FiveThirtyEight")
    axes[1, 0].set_ylabel("Cumulative Brier loss difference")
    axes[1, 0].set_xlabel("Date")
    axes[1, 0].tick_params(axis="x", rotation=20)

    axes[1, 1].plot(
        dates,
        brier["forecast_polymarket"],
        color="#2563eb",
        lw=2,
        label="Polymarket",
    )
    axes[1, 1].plot(
        dates,
        brier["forecast_fivethirtyeight"],
        color="#dc2626",
        lw=2,
        label="FiveThirtyEight",
    )
    axes[1, 1].axhline(0.5, color="#6b7280", lw=1.0, ls="--", label="50% baseline")
    axes[1, 1].set_ylim(0.35, 0.75)
    axes[1, 1].set_title("Forecast probabilities for the winning outcome")
    axes[1, 1].set_ylabel("Trump win probability")
    axes[1, 1].set_xlabel("Date")
    axes[1, 1].tick_params(axis="x", rotation=20)
    axes[1, 1].legend(fontsize=8, loc="upper left")

    subtitle = (
        f"Polymarket lower loss than FiveThirtyEight on "
        f"{int(fte['polymarket_lower_loss_count'])}/"
        f"{int(fte['comparison_row_count'])} paired days; "
        f"mean loss advantage {float(fte['mean_loss_advantage']):.3f}."
    )
    fig.text(
        0.5,
        0.012,
        subtitle
        + " Daily rows are repeated forecasts for one resolved election market.",
        ha="center",
        fontsize=9.5,
        color="#374151",
    )
    for ax in axes.ravel():
        ax.grid(True, alpha=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    brier_input: Path,
    dm_input: Path,
    source_summary_output: Path,
    pairwise_output: Path,
    figure_output: Path,
    source_summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    brier: pd.DataFrame,
) -> dict[str, Any]:
    """Build metadata describing the H1 forecast-quality outputs."""

    fte = pairwise.loc[pairwise["comparator"] == "fivethirtyeight"].iloc[0]
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_forecast_quality_pairwise_brier_summary",
            "calculation_scope": "deterministic_python_from_precomputed_h1_brier_rows",
            "outcome": "Trump won the 2024 US presidential election",
            "primary_comparator": "FiveThirtyEight poll-based probability forecast",
            "raw_poll_average_probability_transform_used": False,
            "rcp_included": False,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
        },
        "outputs": {
            "source_summary_rows": int(len(source_summary)),
            "pairwise_rows": int(len(pairwise)),
            "h1_daily_rows": int(len(brier)),
            "start_date": str(brier["date"].min()),
            "end_date": str(brier["date"].max()),
            "polymarket_better_than_fivethirtyeight_count": int(
                fte["polymarket_lower_loss_count"]
            ),
            "fivethirtyeight_comparison_count": int(fte["comparison_row_count"]),
            "polymarket_better_than_fivethirtyeight_share": float(
                fte["polymarket_better_share"]
            ),
            "mean_loss_advantage_vs_fivethirtyeight": float(
                fte["mean_loss_advantage"]
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "brier_input": str(brier_input),
            "dm_input": str(dm_input),
            "source_summary": str(source_summary_output),
            "pairwise": str(pairwise_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "daily_rows_are_not_independent_election_outcomes": True,
            "single_resolved_event_limits_true_calibration_curve": True,
            "fivethirtyeight_is_poll_based_probability_not_raw_poll_share": True,
            "raw_polls_require_documented_probability_transform_before_brier_use": True,
            "no_reaction_speed_claim_from_h1": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _normalize_dm_label(value: str) -> str:
    lowered = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "fivethirtyeight": "fivethirtyeight",
        "polymarket": "polymarket",
        "immer_50%": "always_50",
        "always_50": "always_50",
        "vortag_polymarket": "prior_day_polymarket",
        "prior_day_polymarket": "prior_day_polymarket",
    }
    return aliases.get(lowered, lowered)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brier-input", type=Path, default=BRIER_INPUT)
    parser.add_argument("--dm-input", type=Path, default=DM_INPUT)
    parser.add_argument("--source-summary-output", type=Path, default=SOURCE_SUMMARY_OUTPUT)
    parser.add_argument("--pairwise-output", type=Path, default=PAIRWISE_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_forecast_quality_outputs(
            brier_input=args.brier_input,
            dm_input=args.dm_input,
            source_summary_output=args.source_summary_output,
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
