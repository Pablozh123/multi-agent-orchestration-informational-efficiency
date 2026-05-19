"""Generate compact thesis-facing summaries from deterministic H1-H3 outputs."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


H1_OUTPUT = "thesis_h1_summary.csv"
H2_OUTPUT = "thesis_h2_summary.csv"
H3_OUTPUT = "thesis_h3_summary.csv"
METADATA_OUTPUT = "thesis_result_summary_metadata.json"

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "hypothesis",
    "summary_type",
    "label",
    "metric",
    "value",
    "source_artifact",
    "allowed_interpretation",
    "limitation",
    "thesis_readiness",
)


@dataclass(frozen=True)
class ThesisSummaryResult:
    """Summary of generated thesis-facing artifacts."""

    h1_path: Path
    h2_path: Path
    h3_path: Path
    metadata_path: Path
    h1_rows: int
    h2_rows: int
    h3_rows: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "h1_path": str(self.h1_path),
            "h2_path": str(self.h2_path),
            "h3_path": str(self.h3_path),
            "metadata_path": str(self.metadata_path),
            "h1_rows": self.h1_rows,
            "h2_rows": self.h2_rows,
            "h3_rows": self.h3_rows,
        }


def build_h1_summary(results_dir: Path = RESULTS_DIR) -> pd.DataFrame:
    """Build a compact H1 summary from precomputed Brier artifacts."""

    brier_path = _required_path(results_dir / "h1_brier_scores.csv")
    dm_path = _required_path(results_dir / "h1_diebold_mariano.json")
    brier = pd.read_csv(brier_path)
    _require_columns(
        brier,
        (
            "date",
            "bs_polymarket",
            "bs_fivethirtyeight",
            "bs_always_50",
            "bs_prior_day",
        ),
        str(brier_path),
    )
    dm_results = json.loads(dm_path.read_text(encoding="utf-8"))

    rows: list[dict[str, object]] = [
        _summary_row(
            summary_id="h1_observation_count",
            hypothesis="H1",
            summary_type="coverage",
            label=f"{brier['date'].min()} to {brier['date'].max()}",
            metric="daily_observations",
            value=len(brier),
            source_artifact=brier_path,
            allowed_interpretation="H1 baseline covers the overlapping daily forecast window.",
            limitation="Coverage is limited to dates where Polymarket and FiveThirtyEight overlap.",
        )
    ]
    brier_sources = (
        ("polymarket", "bs_polymarket"),
        ("fivethirtyeight", "bs_fivethirtyeight"),
        ("always_50", "bs_always_50"),
        ("prior_day_polymarket", "bs_prior_day"),
    )
    for label, column in brier_sources:
        rows.append(
            _summary_row(
                summary_id=f"h1_mean_brier_{label}",
                hypothesis="H1",
                summary_type="mean_brier",
                label=label,
                metric="mean_brier_score",
                value=float(pd.to_numeric(brier[column], errors="raise").mean()),
                source_artifact=brier_path,
                allowed_interpretation="Lower mean Brier Score indicates lower squared forecast error in the tested window.",
                limitation="This is forecast-quality evidence, not a reaction-speed test.",
            )
        )

    for item in dm_results:
        source_1 = str(item["source_1"]).lower().replace(" ", "_")
        source_2 = str(item["source_2"]).lower().replace(" ", "_")
        if "rcp" in {source_1, source_2}:
            continue
        rows.append(
            _summary_row(
                summary_id=f"h1_dm_{source_1}_vs_{source_2}",
                hypothesis="H1",
                summary_type="diebold_mariano",
                label=f"{item['source_1']} vs {item['source_2']}",
                metric="dm_p_value",
                value=float(item["p_value"]),
                source_artifact=dm_path,
                allowed_interpretation="Diebold-Mariano output compares precomputed Brier loss series.",
                limitation="Significance does not identify the mechanism behind forecast differences.",
            )
        )
    return _frame(rows)


def build_h2_summary(results_dir: Path = RESULTS_DIR) -> pd.DataFrame:
    """Build a compact H2 event-window summary."""

    source_path = _required_path(results_dir / "h2_event_window_summary.csv")
    summary = pd.read_csv(source_path)
    _require_columns(
        summary,
        (
            "event_id",
            "title",
            "window_label",
            "observed_days",
            "final_cumulative_abnormal_change",
            "estimation_observations",
        ),
        str(source_path),
    )
    rows: list[dict[str, object]] = [
        _summary_row(
            summary_id="h2_curated_event_count",
            hypothesis="H2",
            summary_type="coverage",
            label="curated_event_seed",
            metric="event_count",
            value=int(summary["event_id"].nunique()),
            source_artifact=source_path,
            allowed_interpretation="H2 uses a pre-curated event set for the initial daily baseline.",
            limitation="Events are fixed for the baseline; later additions require documented review.",
        )
    ]
    for row in summary.sort_values(["event_id", "window_label"]).to_dict(orient="records"):
        rows.append(
            _summary_row(
                summary_id=f"h2_{row['event_id']}_{row['window_label']}",
                hypothesis="H2",
                summary_type="event_window",
                label=f"{row['event_id']} | {row['window_label']}",
                metric="final_cumulative_abnormal_change",
                value=float(row["final_cumulative_abnormal_change"]),
                source_artifact=source_path,
                allowed_interpretation=(
                    "Daily event-window movement describes Polymarket price response "
                    "around a pre-curated public event."
                ),
                limitation="Daily data cannot support intraday reaction-speed claims.",
            )
        )
    return _frame(rows)


def build_h3_summary(results_dir: Path = RESULTS_DIR) -> pd.DataFrame:
    """Build a compact H3 timing and wallet-tier summary."""

    inventory_path = _required_path(results_dir / "h3_wallet_distribution_inventory.json")
    correlations_path = _required_path(results_dir / "h3_lead_lag_correlations.csv")
    granger_path = _required_path(results_dir / "h3_granger_results.csv")
    granger_metadata_path = _required_path(results_dir / "h3_granger_metadata.json")

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    correlations = pd.read_csv(correlations_path)
    granger = pd.read_csv(granger_path)
    metadata = json.loads(granger_metadata_path.read_text(encoding="utf-8"))
    _require_columns(correlations, ("tier", "lag_days", "correlation", "status"), str(correlations_path))
    _require_columns(granger, ("tier", "lag_days", "p_value", "status"), str(granger_path))

    rows: list[dict[str, object]] = [
        _summary_row(
            summary_id="h3_model_row_count",
            hypothesis="H3",
            summary_type="coverage",
            label="daily_tier_activity_and_price_changes",
            metric="aligned_model_rows",
            value=int(metadata["input"]["model_row_count"]),
            source_artifact=granger_metadata_path,
            allowed_interpretation="H3 timing baseline uses aligned daily tier activity and Polymarket price changes.",
            limitation="Daily alignment and BUY-only observed activity limit timing claims.",
        )
    ]

    for tier, count in inventory["tier_counts"].items():
        rows.append(
            _summary_row(
                summary_id=f"h3_wallet_count_{tier}",
                hypothesis="H3",
                summary_type="wallet_tier",
                label=tier,
                metric="wallet_count",
                value=int(count),
                source_artifact=inventory_path,
                allowed_interpretation="Wallet tiers are dataset-relative and distribution-derived.",
                limitation="Tier counts reflect the current observed and filtered wallet dataset.",
            )
        )

    for tier, group in correlations.groupby("tier", sort=True):
        ok_group = group[group["status"] == "ok"].copy()
        if ok_group.empty:
            continue
        selected = ok_group.assign(abs_correlation=ok_group["correlation"].abs()).sort_values(
            ["abs_correlation", "lag_days"],
            ascending=[False, True],
        ).iloc[0]
        rows.append(
            _summary_row(
                summary_id=f"h3_top_abs_correlation_{tier}",
                hypothesis="H3",
                summary_type="lead_lag_correlation",
                label=f"{tier} lag {int(selected['lag_days'])}",
                metric="top_absolute_correlation",
                value=float(selected["correlation"]),
                source_artifact=correlations_path,
                allowed_interpretation="Lead-lag correlations describe timing association between tier activity and price changes.",
                limitation="Correlation does not establish true causality or strategy profitability.",
            )
        )

    for tier, group in granger.groupby("tier", sort=True):
        ok_group = group[group["status"] == "ok"].copy()
        if ok_group.empty:
            continue
        selected = ok_group.sort_values(["p_value", "lag_days"], ascending=[True, True]).iloc[0]
        rows.append(
            _summary_row(
                summary_id=f"h3_min_granger_p_value_{tier}",
                hypothesis="H3",
                summary_type="granger",
                label=f"{tier} lag {int(selected['lag_days'])}",
                metric="minimum_granger_p_value",
                value=float(selected["p_value"]),
                source_artifact=granger_path,
                allowed_interpretation="Granger output is a predictive timing diagnostic under model assumptions.",
                limitation="Multiple testing, BUY-only data, and daily alignment limit thesis conclusions.",
            )
        )
    return _frame(rows)


def generate_thesis_result_summaries(
    *,
    results_dir: Path = RESULTS_DIR,
    output_dir: Path = RESULTS_DIR,
) -> ThesisSummaryResult:
    """Write compact H1-H3 thesis-facing summary artifacts."""

    h1 = build_h1_summary(results_dir)
    h2 = build_h2_summary(results_dir)
    h3 = build_h3_summary(results_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    h1_path = output_dir / H1_OUTPUT
    h2_path = output_dir / H2_OUTPUT
    h3_path = output_dir / H3_OUTPUT
    metadata_path = output_dir / METADATA_OUTPUT
    h1.to_csv(h1_path, index=False)
    h2.to_csv(h2_path, index=False)
    h3.to_csv(h3_path, index=False)

    metadata = {
        "method": {
            "name": "thesis_facing_h1_h2_h3_summary_aggregation",
            "calculation_scope": "aggregation_of_existing_deterministic_outputs",
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
        },
        "outputs": {
            "h1_rows": int(len(h1)),
            "h2_rows": int(len(h2)),
            "h3_rows": int(len(h3)),
            "columns": list(SUMMARY_COLUMNS),
        },
        "source_artifacts": sorted(
            set(h1["source_artifact"]).union(h2["source_artifact"]).union(h3["source_artifact"])
        ),
        "limitations": {
            "rcp_probability_transform_missing": True,
            "daily_h2_and_h3_alignment_only": True,
            "h3_buy_only_source_extract": True,
            "no_profitability_claim": True,
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return ThesisSummaryResult(
        h1_path=h1_path,
        h2_path=h2_path,
        h3_path=h3_path,
        metadata_path=metadata_path,
        h1_rows=len(h1),
        h2_rows=len(h2),
        h3_rows=len(h3),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_result_summaries(
            results_dir=args.results_dir,
            output_dir=args.output_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _summary_row(
    *,
    summary_id: str,
    hypothesis: str,
    summary_type: str,
    label: str,
    metric: str,
    value: object,
    source_artifact: Path,
    allowed_interpretation: str,
    limitation: str,
    thesis_readiness: str = "baseline_ready_with_limitations",
) -> dict[str, object]:
    return {
        "summary_id": summary_id,
        "hypothesis": hypothesis,
        "summary_type": summary_type,
        "label": label,
        "metric": metric,
        "value": value,
        "source_artifact": str(source_artifact),
        "allowed_interpretation": allowed_interpretation,
        "limitation": limitation,
        "thesis_readiness": thesis_readiness,
    }


def _frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _required_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis summary source artifact not found: {path}")
    return path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
