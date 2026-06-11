"""Audit whether the current H1 baseline can be expanded responsibly.

The current H1 result is strong within one paired daily forecast window. This
module makes the expansion bottleneck explicit: local Polymarket prices extend
beyond the current H1 end date, but compatible local traditional probability
forecasts do not. The output is an audit artifact, not a new forecast metric.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.brier_score import load_poll_forecasts_daily, load_polymarket_daily
from operations.analysis.run_h2_event_windows import RESULTS_DIR


DB_PATH = Path("data/thesis.db")
BRIER_INPUT = RESULTS_DIR / "h1_brier_scores.csv"
SWISS_POLL_INPUT = Path("data/swiss_referendum_10mio_polls.csv")
READINESS_OUTPUT = RESULTS_DIR / "h1_expansion_readiness.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_expansion_readiness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_expansion_readiness_metadata.json"

FIVETHIRTYEIGHT_POLL_README_URL = (
    "https://github.com/fivethirtyeight/data/blob/master/polls/README.md"
)
FIVETHIRTYEIGHT_2024_AVERAGES_URL = (
    "https://github.com/fivethirtyeight/data/tree/master/polls/2024-averages"
)
FIVETHIRTYEIGHT_FINAL_FORECAST_URL = (
    "https://abcnews.com/538/538s-final-forecasts-2024-election/story?id=115511051"
)

READINESS_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "candidate_label",
    "candidate_type",
    "local_available_rows",
    "current_overlap_rows",
    "additional_pair_rows_now",
    "independent_resolved_outcomes_now",
    "compatible_for_h1_brier_now",
    "broad_many_cases_support_now",
    "status",
    "main_blocker",
    "required_next_step",
    "source_url",
)


@dataclass(frozen=True)
class H1ExpansionReadinessResult:
    """Summary of generated H1 expansion-readiness artifacts."""

    readiness_path: Path
    figure_path: Path
    metadata_path: Path
    readiness_row_count: int
    current_h1_pair_rows: int
    polymarket_extra_daily_rows: int
    fivethirtyeight_extra_probability_rows: int
    additional_pair_rows_now: int
    eligible_independent_outcome_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "readiness_path": str(self.readiness_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "readiness_row_count": self.readiness_row_count,
            "current_h1_pair_rows": self.current_h1_pair_rows,
            "polymarket_extra_daily_rows": self.polymarket_extra_daily_rows,
            "fivethirtyeight_extra_probability_rows": (
                self.fivethirtyeight_extra_probability_rows
            ),
            "additional_pair_rows_now": self.additional_pair_rows_now,
            "eligible_independent_outcome_count": self.eligible_independent_outcome_count,
        }


def generate_h1_expansion_readiness_outputs(
    *,
    db_path: Path = DB_PATH,
    brier_input: Path = BRIER_INPUT,
    swiss_poll_input: Path = SWISS_POLL_INPUT,
    readiness_output: Path = READINESS_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1ExpansionReadinessResult:
    """Generate H1 expansion-readiness CSV, figure, and metadata."""

    brier = read_h1_brier_input(brier_input)
    coverage = inspect_local_coverage(
        db_path=db_path,
        current_h1_end_date=str(brier["date"].max()),
    )
    swiss_poll_rows = _count_csv_rows(swiss_poll_input)
    readiness = build_readiness_rows(
        brier=brier,
        coverage=coverage,
        swiss_poll_rows=swiss_poll_rows,
    )

    readiness_output.parent.mkdir(parents=True, exist_ok=True)
    readiness.to_csv(readiness_output, index=False)
    write_readiness_figure(
        readiness=readiness,
        coverage=coverage,
        output_path=figure_output,
    )
    metadata = build_metadata(
        db_path=db_path,
        brier_input=brier_input,
        swiss_poll_input=swiss_poll_input,
        readiness_output=readiness_output,
        figure_output=figure_output,
        readiness=readiness,
        brier=brier,
        coverage=coverage,
        swiss_poll_rows=swiss_poll_rows,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1ExpansionReadinessResult(
        readiness_path=readiness_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        readiness_row_count=int(len(readiness)),
        current_h1_pair_rows=int(len(brier)),
        polymarket_extra_daily_rows=int(coverage["polymarket_extra_daily_rows"]),
        fivethirtyeight_extra_probability_rows=int(
            coverage["fivethirtyeight_extra_probability_rows"]
        ),
        additional_pair_rows_now=int(readiness["additional_pair_rows_now"].sum()),
        eligible_independent_outcome_count=int(
            readiness["independent_resolved_outcomes_now"].sum()
        ),
    )


def read_h1_brier_input(path: Path) -> pd.DataFrame:
    """Read the current H1 Brier artifact and validate the date column."""

    if not path.exists():
        raise FileNotFoundError(f"H1 Brier input not found: {path}")
    frame = pd.read_csv(path)
    if "date" not in frame.columns:
        raise ValueError("H1 Brier input must contain a date column")
    if frame.empty:
        raise ValueError("H1 Brier input must not be empty")
    normalized = frame.copy()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="raise").dt.date.astype(str)
    return normalized.sort_values("date").reset_index(drop=True)


def inspect_local_coverage(*, db_path: Path, current_h1_end_date: str) -> dict[str, Any]:
    """Inspect local Polymarket and FiveThirtyEight coverage in SQLite."""

    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    end_date = pd.Timestamp(current_h1_end_date).date().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        polymarket_daily = load_polymarket_daily(conn)
        fte_daily = load_poll_forecasts_daily(conn, "fivethirtyeight")
    finally:
        conn.close()

    if polymarket_daily.empty:
        raise ValueError("polymarket_prices contains no daily local prices")
    if fte_daily.empty:
        raise ValueError("poll_forecasts contains no FiveThirtyEight Trump probabilities")

    pm_after = polymarket_daily[polymarket_daily["date"] > end_date]
    fte_after = fte_daily[fte_daily["date"] > end_date]
    return {
        "current_h1_end_date": end_date,
        "polymarket_daily_rows": int(len(polymarket_daily)),
        "polymarket_min_date": str(polymarket_daily["date"].min()),
        "polymarket_max_date": str(polymarket_daily["date"].max()),
        "fivethirtyeight_probability_rows": int(len(fte_daily)),
        "fivethirtyeight_min_date": str(fte_daily["date"].min()),
        "fivethirtyeight_max_date": str(fte_daily["date"].max()),
        "polymarket_extra_daily_rows": int(len(pm_after)),
        "fivethirtyeight_extra_probability_rows": int(len(fte_after)),
    }


def build_readiness_rows(
    *,
    brier: pd.DataFrame,
    coverage: dict[str, Any],
    swiss_poll_rows: int,
) -> pd.DataFrame:
    """Build compact rows describing H1 expansion candidates."""

    current_rows = int(len(brier))
    pm_extra = int(coverage["polymarket_extra_daily_rows"])
    fte_extra = int(coverage["fivethirtyeight_extra_probability_rows"])
    additional_pairs = min(pm_extra, fte_extra)
    rows: list[dict[str, Any]] = [
        {
            "candidate_id": "current_us_2024_h1_overlap",
            "candidate_label": "Current US 2024 H1 paired daily baseline",
            "candidate_type": "existing_probability_forecast_overlap",
            "local_available_rows": current_rows,
            "current_overlap_rows": current_rows,
            "additional_pair_rows_now": 0,
            "independent_resolved_outcomes_now": 1,
            "compatible_for_h1_brier_now": True,
            "broad_many_cases_support_now": False,
            "status": "usable_but_single_independent_outcome",
            "main_blocker": (
                "Daily rows are repeated forecasts for one resolved election outcome."
            ),
            "required_next_step": (
                "Add additional resolved markets with compatible probability forecasts."
            ),
            "source_url": "",
        },
        {
            "candidate_id": "local_polymarket_tail_after_h1_end",
            "candidate_label": "Local Polymarket prices after current H1 end date",
            "candidate_type": "local_prediction_market_tail_without_comparator",
            "local_available_rows": pm_extra,
            "current_overlap_rows": 0,
            "additional_pair_rows_now": additional_pairs,
            "independent_resolved_outcomes_now": 0,
            "compatible_for_h1_brier_now": False,
            "broad_many_cases_support_now": False,
            "status": "blocked_by_missing_probability_comparator",
            "main_blocker": (
                "Polymarket has extra daily prices, but local FiveThirtyEight "
                "probability rows after the current H1 end date are unavailable."
            ),
            "required_next_step": (
                "Load a compatible traditional probability forecast time series "
                "or keep these Polymarket rows out of H1 Brier comparisons."
            ),
            "source_url": "",
        },
        {
            "candidate_id": "local_fivethirtyeight_after_h1_end",
            "candidate_label": "Local FiveThirtyEight probability rows after H1 end",
            "candidate_type": "local_traditional_probability_forecast_tail",
            "local_available_rows": fte_extra,
            "current_overlap_rows": 0,
            "additional_pair_rows_now": additional_pairs,
            "independent_resolved_outcomes_now": 0,
            "compatible_for_h1_brier_now": fte_extra > 0 and pm_extra > 0,
            "broad_many_cases_support_now": False,
            "status": "not_available_locally",
            "main_blocker": (
                "The local poll_forecasts table ends at the current H1 boundary "
                "for FiveThirtyEight Trump probabilities."
            ),
            "required_next_step": (
                "Find an official machine-readable probability forecast source "
                "with dates beyond the current H1 end date."
            ),
            "source_url": FIVETHIRTYEIGHT_POLL_README_URL,
        },
        {
            "candidate_id": "official_538_polling_averages_2024",
            "candidate_label": "Official FiveThirtyEight 2024 polling averages",
            "candidate_type": "external_polling_average_not_win_probability",
            "local_available_rows": 0,
            "current_overlap_rows": 0,
            "additional_pair_rows_now": 0,
            "independent_resolved_outcomes_now": 0,
            "compatible_for_h1_brier_now": False,
            "broad_many_cases_support_now": False,
            "status": "blocked_until_probability_transform_documented",
            "main_blocker": (
                "Polling averages and raw polls are vote-share estimates, not "
                "model-implied win probabilities."
            ),
            "required_next_step": (
                "Document and test a poll-share-to-probability transformation "
                "before using these rows in Brier scoring."
            ),
            "source_url": FIVETHIRTYEIGHT_2024_AVERAGES_URL,
        },
        {
            "candidate_id": "official_538_final_forecast_article",
            "candidate_label": "Official 538 final presidential forecast article",
            "candidate_type": "external_single_final_probability_snapshot",
            "local_available_rows": 0,
            "current_overlap_rows": 0,
            "additional_pair_rows_now": 0,
            "independent_resolved_outcomes_now": 0,
            "compatible_for_h1_brier_now": False,
            "broad_many_cases_support_now": False,
            "status": "possible_curated_one_row_check_not_many_cases",
            "main_blocker": (
                "The article gives one final national probability snapshot, not "
                "a machine-readable daily series or additional independent cases."
            ),
            "required_next_step": (
                "Use only as a separately curated final-snapshot check if a "
                "timestamp-aligned Polymarket price is documented."
            ),
            "source_url": FIVETHIRTYEIGHT_FINAL_FORECAST_URL,
        },
        {
            "candidate_id": "swiss_referendum_poll_track",
            "candidate_label": "Swiss referendum poll-share comparison track",
            "candidate_type": "local_poll_share_descriptive_track",
            "local_available_rows": swiss_poll_rows,
            "current_overlap_rows": 0,
            "additional_pair_rows_now": 0,
            "independent_resolved_outcomes_now": 0,
            "compatible_for_h1_brier_now": False,
            "broad_many_cases_support_now": False,
            "status": "unresolved_and_poll_shares_not_probabilities",
            "main_blocker": (
                "The referendum outcome is not resolved locally, and poll shares "
                "are not model-implied win probabilities."
            ),
            "required_next_step": (
                "After resolution, keep as a poll-share gap study or document a "
                "probability transformation before Brier scoring."
            ),
            "source_url": "data/swiss_referendum_10mio_polls.csv",
        },
    ]
    return pd.DataFrame(rows, columns=READINESS_COLUMNS)


def write_readiness_figure(
    *,
    readiness: pd.DataFrame,
    coverage: dict[str, Any],
    output_path: Path,
) -> Path:
    """Write a figure showing why H1 cannot yet be broadly expanded."""

    current_h1 = readiness.loc[
        readiness["candidate_id"] == "current_us_2024_h1_overlap"
    ].iloc[0]
    pm_tail = readiness.loc[
        readiness["candidate_id"] == "local_polymarket_tail_after_h1_end"
    ].iloc[0]
    fte_tail = readiness.loc[
        readiness["candidate_id"] == "local_fivethirtyeight_after_h1_end"
    ].iloc[0]

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8))
    fig.suptitle("H1 Expansion Readiness Audit", fontsize=14, fontweight="bold")

    left_labels = [
        "Current paired\nH1 days",
        "PM-only days\nafter H1 end",
        "Compatible 538\nprobability days",
    ]
    left_values = [
        int(current_h1["current_overlap_rows"]),
        int(pm_tail["local_available_rows"]),
        int(fte_tail["local_available_rows"]),
    ]
    axes[0].bar(left_labels, left_values, color=["#2563eb", "#f59e0b", "#dc2626"])
    axes[0].set_title("Coverage after current H1 boundary")
    axes[0].set_ylabel("Daily rows")
    axes[0].text(
        0.5,
        -0.26,
        f"Current H1 ends {coverage['current_h1_end_date']}; "
        "PM tail alone is not a paired Brier comparison.",
        ha="center",
        transform=axes[0].transAxes,
        fontsize=8.8,
        color="#374151",
    )
    for idx, value in enumerate(left_values):
        axes[0].text(idx, value + max(left_values) * 0.025, str(value), ha="center")

    right_labels = [
        "Eligible independent\nH1 outcomes",
        "Additional independent\noutcomes found locally",
    ]
    right_values = [
        int(current_h1["independent_resolved_outcomes_now"]),
        int(readiness["independent_resolved_outcomes_now"].sum())
        - int(current_h1["independent_resolved_outcomes_now"]),
    ]
    axes[1].bar(right_labels, right_values, color=["#2563eb", "#9ca3af"])
    axes[1].set_title("Broad many-cases claim readiness")
    axes[1].set_ylabel("Independent resolved outcomes")
    axes[1].set_ylim(0, max(1.3, max(right_values) + 0.4))
    axes[1].text(
        0.5,
        -0.26,
        "The audit adds 0 new Brier-computable independent cases.",
        ha="center",
        transform=axes[1].transAxes,
        fontsize=8.8,
        color="#374151",
    )
    for idx, value in enumerate(right_values):
        axes[1].text(idx, value + 0.04, str(value), ha="center")

    for ax in axes:
        ax.grid(True, axis="y", alpha=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.08, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    db_path: Path,
    brier_input: Path,
    swiss_poll_input: Path,
    readiness_output: Path,
    figure_output: Path,
    readiness: pd.DataFrame,
    brier: pd.DataFrame,
    coverage: dict[str, Any],
    swiss_poll_rows: int,
) -> dict[str, Any]:
    """Build metadata for the H1 expansion-readiness audit."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_expansion_readiness_audit",
            "calculation_scope": "deterministic_python_from_local_artifacts",
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "raw_poll_average_probability_transform_used": False,
            "rcp_included": False,
        },
        "outputs": {
            "readiness_rows": int(len(readiness)),
            "current_h1_pair_rows": int(len(brier)),
            "current_h1_start_date": str(brier["date"].min()),
            "current_h1_end_date": str(brier["date"].max()),
            "polymarket_daily_rows_total": int(coverage["polymarket_daily_rows"]),
            "polymarket_daily_rows_after_current_h1_end": int(
                coverage["polymarket_extra_daily_rows"]
            ),
            "fivethirtyeight_probability_rows_total": int(
                coverage["fivethirtyeight_probability_rows"]
            ),
            "fivethirtyeight_probability_rows_after_current_h1_end": int(
                coverage["fivethirtyeight_extra_probability_rows"]
            ),
            "compatible_additional_h1_pair_rows_now": int(
                readiness["additional_pair_rows_now"].sum()
            ),
            "eligible_independent_resolved_outcome_count": int(
                readiness["independent_resolved_outcomes_now"].sum()
            ),
            "swiss_poll_rows": int(swiss_poll_rows),
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "db_path": str(db_path),
            "brier_input": str(brier_input),
            "swiss_poll_input": str(swiss_poll_input),
            "readiness_output": str(readiness_output),
            "figure_output": str(figure_output),
        },
        "reviewed_external_source_urls": {
            "fivethirtyeight_polls_readme": FIVETHIRTYEIGHT_POLL_README_URL,
            "fivethirtyeight_2024_averages_directory": FIVETHIRTYEIGHT_2024_AVERAGES_URL,
            "fivethirtyeight_final_forecast_article": FIVETHIRTYEIGHT_FINAL_FORECAST_URL,
        },
        "limitations": {
            "polymarket_tail_lacks_compatible_traditional_probability_forecast": True,
            "raw_poll_shares_require_documented_probability_transform": True,
            "single_final_forecast_article_is_not_many_cases": True,
            "current_brier_evidence_has_one_independent_resolved_outcome": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return int(len(pd.read_csv(path)))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--brier-input", type=Path, default=BRIER_INPUT)
    parser.add_argument("--swiss-poll-input", type=Path, default=SWISS_POLL_INPUT)
    parser.add_argument("--readiness-output", type=Path, default=READINESS_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_expansion_readiness_outputs(
            db_path=args.db_path,
            brier_input=args.brier_input,
            swiss_poll_input=args.swiss_poll_input,
            readiness_output=args.readiness_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, KeyError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
