"""Audit the evidentiary scope of the current H1 forecast-quality baseline.

The H1 Brier result is strong for the available paired daily forecast rows, but
those rows belong to one resolved election outcome. This module writes compact
deterministic artifacts that separate row count from independent outcome count.
It also records which nearby project data can and cannot be reused for H1.
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

from operations.analysis.h1_forecast_quality import PAIRWISE_OUTPUT
from operations.analysis.run_h2_event_windows import RESULTS_DIR


BRIER_INPUT = RESULTS_DIR / "h1_brier_scores.csv"
SWISS_POLL_INPUT = Path("data/swiss_referendum_10mio_polls.csv")
EVENT_INPUT = Path("data/events_timeline_seed.csv")
SCOPE_OUTPUT = RESULTS_DIR / "h1_evidence_scope.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_evidence_scope.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_evidence_scope_metadata.json"

SCOPE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "case_label",
    "status",
    "evidence_role",
    "independent_resolved_outcome_count",
    "local_row_count",
    "comparator_type",
    "brier_computable_now",
    "current_h1_eligible",
    "polymarket_better_count",
    "comparison_count",
    "polymarket_better_share",
    "main_limitation",
    "required_next_data",
)


@dataclass(frozen=True)
class H1EvidenceScopeResult:
    """Summary of generated H1 evidence-scope artifacts."""

    scope_path: Path
    figure_path: Path
    metadata_path: Path
    scope_row_count: int
    eligible_independent_outcome_count: int
    eligible_daily_row_count: int
    polymarket_better_vs_fivethirtyeight_count: int
    fivethirtyeight_comparison_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "scope_path": str(self.scope_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "scope_row_count": self.scope_row_count,
            "eligible_independent_outcome_count": self.eligible_independent_outcome_count,
            "eligible_daily_row_count": self.eligible_daily_row_count,
            "polymarket_better_vs_fivethirtyeight_count": (
                self.polymarket_better_vs_fivethirtyeight_count
            ),
            "fivethirtyeight_comparison_count": self.fivethirtyeight_comparison_count,
        }


def generate_h1_evidence_scope_outputs(
    *,
    brier_input: Path = BRIER_INPUT,
    pairwise_input: Path = PAIRWISE_OUTPUT,
    swiss_poll_input: Path = SWISS_POLL_INPUT,
    event_input: Path = EVENT_INPUT,
    scope_output: Path = SCOPE_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1EvidenceScopeResult:
    """Generate H1 evidence-scope CSV, figure, and metadata."""

    brier = _read_csv_if_exists(brier_input)
    pairwise = _read_csv_if_exists(pairwise_input)
    swiss_polls = _read_csv_if_exists(swiss_poll_input)
    events = _read_csv_if_exists(event_input)
    scope = build_scope_rows(
        brier=brier,
        pairwise=pairwise,
        swiss_polls=swiss_polls,
        events=events,
    )

    scope_output.parent.mkdir(parents=True, exist_ok=True)
    scope.to_csv(scope_output, index=False)
    write_scope_figure(scope=scope, output_path=figure_output)
    metadata = build_metadata(
        brier_input=brier_input,
        pairwise_input=pairwise_input,
        swiss_poll_input=swiss_poll_input,
        event_input=event_input,
        scope_output=scope_output,
        figure_output=figure_output,
        scope=scope,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    eligible = scope[scope["current_h1_eligible"]]
    fte = scope.loc[scope["case_id"] == "us_2024_presidential_h1"].iloc[0]
    return H1EvidenceScopeResult(
        scope_path=scope_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        scope_row_count=int(len(scope)),
        eligible_independent_outcome_count=int(
            eligible["independent_resolved_outcome_count"].sum()
        ),
        eligible_daily_row_count=int(eligible["local_row_count"].sum()),
        polymarket_better_vs_fivethirtyeight_count=int(
            fte["polymarket_better_count"]
        ),
        fivethirtyeight_comparison_count=int(fte["comparison_count"]),
    )


def build_scope_rows(
    *,
    brier: pd.DataFrame,
    pairwise: pd.DataFrame,
    swiss_polls: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Build one row per candidate evidence source for H1."""

    required_pairwise = {"comparator", "polymarket_lower_loss_count", "comparison_row_count"}
    if pairwise.empty or not required_pairwise.issubset(pairwise.columns):
        raise ValueError("H1 pairwise input is missing required comparison columns")
    fte = pairwise.loc[pairwise["comparator"] == "fivethirtyeight"]
    if fte.empty:
        raise ValueError("H1 pairwise input has no FiveThirtyEight comparison row")
    fte_row = fte.iloc[0]
    comparison_count = int(fte_row["comparison_row_count"])
    pm_better = int(fte_row["polymarket_lower_loss_count"])
    rows: list[dict[str, Any]] = [
        {
            "case_id": "us_2024_presidential_h1",
            "case_label": "2024 US presidential election",
            "status": "resolved",
            "evidence_role": "h1_brier_forecast_quality_case",
            "independent_resolved_outcome_count": 1,
            "local_row_count": int(len(brier)),
            "comparator_type": "FiveThirtyEight poll-based probability forecast",
            "brier_computable_now": True,
            "current_h1_eligible": True,
            "polymarket_better_count": pm_better,
            "comparison_count": comparison_count,
            "polymarket_better_share": (
                pm_better / comparison_count if comparison_count else 0.0
            ),
            "main_limitation": (
                "Daily rows are repeated forecasts for one resolved election, "
                "not independent election outcomes."
            ),
            "required_next_data": (
                "Add additional resolved markets with Polymarket probability "
                "history and comparable probability forecasts."
            ),
        },
        {
            "case_id": "swiss_2026_10mio_referendum",
            "case_label": "Swiss 10-million referendum",
            "status": "unresolved_as_of_2026_06_10",
            "evidence_role": "poll_proxy_descriptive_current_goal",
            "independent_resolved_outcome_count": 0,
            "local_row_count": int(len(swiss_polls)),
            "comparator_type": "curated poll shares and decided-voter shares",
            "brier_computable_now": False,
            "current_h1_eligible": False,
            "polymarket_better_count": 0,
            "comparison_count": 0,
            "polymarket_better_share": 0.0,
            "main_limitation": (
                "The vote outcome is not yet resolved locally, and poll shares "
                "are not model-implied win probabilities."
            ),
            "required_next_data": (
                "After the official result, decide whether this remains a "
                "poll-share gap study or document a probability transformation "
                "before Brier scoring polls."
            ),
        },
        {
            "case_id": "h2_curated_us_events",
            "case_label": "Curated US-election event windows",
            "status": "event_window_context_not_outcome_set",
            "evidence_role": "h2_reaction_context_only",
            "independent_resolved_outcome_count": 0,
            "local_row_count": int(len(events)),
            "comparator_type": "event labels, not forecast sources",
            "brier_computable_now": False,
            "current_h1_eligible": False,
            "polymarket_better_count": 0,
            "comparison_count": 0,
            "polymarket_better_share": 0.0,
            "main_limitation": (
                "Events explain timing around one presidential market; they "
                "are not separate forecast outcomes."
            ),
            "required_next_data": (
                "Do not count H2 events as H1 cases unless each has its own "
                "resolved probability market and compatible benchmark forecast."
            ),
        },
    ]
    return pd.DataFrame(rows, columns=SCOPE_COLUMNS)


def write_scope_figure(*, scope: pd.DataFrame, output_path: Path) -> Path:
    """Write a compact visual audit of current H1 evidence scope."""

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8))
    fig.suptitle("H1 Evidence Scope Audit", fontsize=14, fontweight="bold")

    labels = scope["case_label"].str.replace(" ", "\n", n=2)
    colors = [
        "#2563eb" if eligible else "#9ca3af"
        for eligible in scope["current_h1_eligible"].tolist()
    ]
    axes[0].bar(labels, scope["independent_resolved_outcome_count"], color=colors)
    axes[0].set_title("Independent resolved H1 outcomes")
    axes[0].set_ylabel("Brier-computable outcome count")
    axes[0].tick_params(axis="x", labelsize=8)
    for idx, value in enumerate(scope["independent_resolved_outcome_count"]):
        axes[0].text(idx, float(value) + 0.03, str(int(value)), ha="center")

    h1_row = scope.loc[scope["case_id"] == "us_2024_presidential_h1"].iloc[0]
    axes[1].bar(
        ["Polymarket\nlower loss", "FiveThirtyEight\nlower loss"],
        [
            int(h1_row["polymarket_better_count"]),
            int(h1_row["comparison_count"]) - int(h1_row["polymarket_better_count"]),
        ],
        color=["#2563eb", "#dc2626"],
    )
    axes[1].set_title("Daily paired rows inside the eligible case")
    axes[1].set_ylabel("Daily forecast rows")
    axes[1].text(
        0.5,
        -0.24,
        "Daily rows support the one eligible case; they are not independent cases.",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=9,
        color="#374151",
    )
    for ax in axes:
        ax.grid(True, axis="y", alpha=0.25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    brier_input: Path,
    pairwise_input: Path,
    swiss_poll_input: Path,
    event_input: Path,
    scope_output: Path,
    figure_output: Path,
    scope: pd.DataFrame,
) -> dict[str, Any]:
    """Build metadata for the H1 evidence-scope audit."""

    eligible = scope[scope["current_h1_eligible"]]
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_evidence_scope_audit",
            "calculation_scope": "deterministic_python_from_local_artifacts",
            "separates_daily_rows_from_independent_outcomes": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "scope_rows": int(len(scope)),
            "eligible_brier_case_rows": int(len(eligible)),
            "eligible_independent_resolved_outcome_count": int(
                eligible["independent_resolved_outcome_count"].sum()
            ),
            "eligible_daily_row_count": int(eligible["local_row_count"].sum()),
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "brier_input": str(brier_input),
            "pairwise_input": str(pairwise_input),
            "swiss_poll_input": str(swiss_poll_input),
            "event_input": str(event_input),
            "scope_output": str(scope_output),
            "figure_output": str(figure_output),
        },
        "limitations": {
            "current_brier_evidence_has_one_independent_resolved_outcome": True,
            "swiss_referendum_unresolved_as_of_2026_06_10": True,
            "h2_events_are_not_independent_h1_outcomes": True,
            "raw_poll_shares_require_documented_probability_transform": True,
        },
    }


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brier-input", type=Path, default=BRIER_INPUT)
    parser.add_argument("--pairwise-input", type=Path, default=PAIRWISE_OUTPUT)
    parser.add_argument("--swiss-poll-input", type=Path, default=SWISS_POLL_INPUT)
    parser.add_argument("--event-input", type=Path, default=EVENT_INPUT)
    parser.add_argument("--scope-output", type=Path, default=SCOPE_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_evidence_scope_outputs(
            brier_input=args.brier_input,
            pairwise_input=args.pairwise_input,
            swiss_poll_input=args.swiss_poll_input,
            event_input=args.event_input,
            scope_output=args.scope_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except (ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
