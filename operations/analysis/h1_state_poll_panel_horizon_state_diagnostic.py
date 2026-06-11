"""State-level support diagnostic for the H1 <=90-day horizon panel.

The horizon diagnostic shows that Polymarket has lower loss in most repeated
forecast rows within 90 days of election day. This module aggregates that same
window by state, making clear how many resolved state outcomes support the
late-window Polymarket result.
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


STATE_SUPPORT_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_state_support.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_state_support_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_state_support.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_state_support_metadata.json"

STATE_SUPPORT_COLUMNS: tuple[str, ...] = (
    "state",
    "row_count",
    "first_forecast_date",
    "last_forecast_date",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
    "support_label",
    "row_unit",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)


@dataclass(frozen=True)
class H1StatePollPanelHorizonStateResult:
    """Summary of generated state-level horizon diagnostic artifacts."""

    state_support_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    state_count: int
    polymarket_mean_support_state_count: int
    polymarket_majority_support_state_count: int
    row_count: int
    polymarket_lower_loss_count: int
    poll_derived_lower_loss_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "state_support_path": str(self.state_support_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "state_count": self.state_count,
            "polymarket_mean_support_state_count": self.polymarket_mean_support_state_count,
            "polymarket_majority_support_state_count": (
                self.polymarket_majority_support_state_count
            ),
            "row_count": self.row_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "poll_derived_lower_loss_count": self.poll_derived_lower_loss_count,
        }


def generate_h1_state_poll_panel_horizon_state_outputs(
    *,
    case_input: Path = CASE_INPUT,
    state_support_output: Path = STATE_SUPPORT_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StatePollPanelHorizonStateResult:
    """Generate state-level support outputs for the <=90-day horizon window."""

    cases = add_horizon_columns(read_panel_cases(case_input))
    near_cases = cases.loc[cases["days_to_election"] <= NEAR_HORIZON_MAX_DAYS].copy()
    if near_cases.empty:
        raise ValueError("<=90-day horizon window must not be empty")
    state_support = build_state_support(near_cases)
    summary = build_summary(state_support, near_cases)

    state_support_output.parent.mkdir(parents=True, exist_ok=True)
    state_support.to_csv(state_support_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_state_support_figure(
        state_support=state_support,
        summary=summary,
        output_path=figure_output,
    )
    metadata = build_metadata(
        state_support=state_support,
        summary=summary,
        near_cases=near_cases,
        case_input=case_input,
        state_support_output=state_support_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1StatePollPanelHorizonStateResult(
        state_support_path=state_support_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        state_count=int(values["state_count"]),
        polymarket_mean_support_state_count=int(
            values["polymarket_mean_support_state_count"]
        ),
        polymarket_majority_support_state_count=int(
            values["polymarket_majority_support_state_count"]
        ),
        row_count=int(values["row_count"]),
        polymarket_lower_loss_count=int(values["polymarket_lower_loss_count"]),
        poll_derived_lower_loss_count=int(values["poll_derived_lower_loss_count"]),
    )


def build_state_support(near_cases: pd.DataFrame) -> pd.DataFrame:
    """Build one <=90-day support row per state."""

    rows: list[dict[str, Any]] = []
    for state, group in near_cases.groupby("state", sort=True):
        counts = group["lower_loss_source"].value_counts()
        row_count = int(len(group))
        pm_lower = int(counts.get("polymarket", 0))
        poll_lower = int(counts.get("poll_derived_forecast", 0))
        ties = int(counts.get("tie", 0))
        mean_pm = float(group["polymarket_brier"].mean())
        mean_poll = float(group["poll_derived_brier"].mean())
        mean_support = mean_pm < mean_poll
        majority_support = pm_lower > poll_lower and pm_lower > row_count / 2.0
        if mean_support and majority_support:
            support_label = "polymarket_mean_and_majority"
        elif mean_support:
            support_label = "polymarket_mean_only"
        elif majority_support:
            support_label = "polymarket_majority_only"
        else:
            support_label = "poll_derived_or_no_polymarket_support"
        rows.append(
            {
                "state": str(state),
                "row_count": row_count,
                "first_forecast_date": _format_date(group["forecast_date"].min()),
                "last_forecast_date": _format_date(group["forecast_date"].max()),
                "polymarket_lower_loss_count": pm_lower,
                "poll_derived_lower_loss_count": poll_lower,
                "tie_count": ties,
                "polymarket_better_share": pm_lower / row_count,
                "mean_polymarket_brier": mean_pm,
                "mean_poll_derived_brier": mean_poll,
                "mean_loss_advantage": mean_poll - mean_pm,
                "aggregate_mean_supports_polymarket": mean_support,
                "majority_rows_support_polymarket": majority_support,
                "support_label": support_label,
                "row_unit": "state_date_forecast_pair_within_90_days",
                "limitation": (
                    "State rows aggregate repeated forecast rows inside one "
                    "election context; they are not independent elections."
                ),
            }
        )
    return pd.DataFrame(rows, columns=STATE_SUPPORT_COLUMNS).sort_values(
        "mean_loss_advantage"
    ).reset_index(drop=True)


def build_summary(state_support: pd.DataFrame, near_cases: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the state-level horizon diagnostic."""

    counts = near_cases["lower_loss_source"].value_counts()
    pm_lower = int(counts.get("polymarket", 0))
    poll_lower = int(counts.get("poll_derived_forecast", 0))
    ties = int(counts.get("tie", 0))
    mean_pm = float(near_cases["polymarket_brier"].mean())
    mean_poll = float(near_cases["poll_derived_brier"].mean())
    rows = [
        _summary_row("state_count", int(len(state_support)), "states", "States represented in the <=90-day window."),
        _summary_row("row_count", int(len(near_cases)), "state-date rows", "Repeated forecast rows in the <=90-day window."),
        _summary_row("polymarket_lower_loss_count", pm_lower, "state-date rows", "Rows where Polymarket has lower Brier loss."),
        _summary_row("poll_derived_lower_loss_count", poll_lower, "state-date rows", "Rows where the poll-derived probability has lower Brier loss."),
        _summary_row("tie_count", ties, "state-date rows", "Rows with equal Brier loss."),
        _summary_row("polymarket_better_share", pm_lower / len(near_cases), "share", "Share of <=90-day rows where Polymarket has lower loss."),
        _summary_row("mean_polymarket_brier", mean_pm, "brier", "Mean Polymarket Brier in the <=90-day window."),
        _summary_row("mean_poll_derived_brier", mean_poll, "brier", "Mean poll-derived Brier in the <=90-day window."),
        _summary_row("mean_loss_advantage", mean_poll - mean_pm, "brier", "Positive means lower Polymarket mean Brier."),
        _summary_row(
            "polymarket_mean_support_state_count",
            int(state_support["aggregate_mean_supports_polymarket"].sum()),
            "states",
            "States where mean Brier is lower for Polymarket.",
        ),
        _summary_row(
            "polymarket_majority_support_state_count",
            int(state_support["majority_rows_support_polymarket"].sum()),
            "states",
            "States where Polymarket has a majority of lower-loss rows.",
        ),
        _summary_row(
            "poll_derived_or_no_polymarket_support_state_count",
            int((~state_support["aggregate_mean_supports_polymarket"]).sum()),
            "states",
            "States where mean Brier is not lower for Polymarket.",
        ),
        _summary_row("broad_many_cases_claim_supported", 0.0, "binary", "Still one election context; broad claim is not proven."),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_state_support_figure(
    *,
    state_support: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the state-level <=90-day support figure."""

    values = _summary_values(summary)
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 6.2))
    fig.suptitle(
        "H1 <=90-Day State-Level Support: Polymarket vs 538 Poll-Derived",
        fontsize=13.5,
        fontweight="bold",
    )

    ordered = state_support.sort_values("mean_loss_advantage")
    colors = [
        "#2563eb" if bool(value) else "#7c3aed"
        for value in ordered["aggregate_mean_supports_polymarket"]
    ]
    axes[0].barh(ordered["state"], ordered["mean_loss_advantage"], color=colors)
    axes[0].axvline(0, color="#111827", linewidth=0.9)
    axes[0].set_title("State mean-loss advantage")
    axes[0].set_xlabel("Poll-derived Brier - PM Brier")
    axes[0].grid(True, axis="x", alpha=0.25)

    share_ordered = state_support.sort_values("polymarket_better_share")
    axes[1].barh(
        share_ordered["state"],
        share_ordered["polymarket_better_share"],
        color=[
            "#2563eb" if value >= 0.5 else "#7c3aed"
            for value in share_ordered["polymarket_better_share"]
        ],
    )
    axes[1].axvline(0.5, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1].set_xlim(0, 1.05)
    axes[1].set_title("State lower-loss share")
    axes[1].set_xlabel("PM lower-loss share")
    axes[1].grid(True, axis="x", alpha=0.25)

    labels = ["States", "Mean PM win", "Majority PM win"]
    counts = [
        values["state_count"],
        values["polymarket_mean_support_state_count"],
        values["polymarket_majority_support_state_count"],
    ]
    axes[2].bar(labels, counts, color=["#475569", "#2563eb", "#2563eb"])
    axes[2].set_ylim(0, max(counts) + 2)
    axes[2].set_title("State support count")
    axes[2].set_ylabel("States")
    axes[2].grid(True, axis="y", alpha=0.25)
    for idx, count in enumerate(counts):
        axes[2].text(idx, count + 0.3, f"{int(count)}", ha="center", fontsize=9)

    fig.text(
        0.5,
        0.012,
        (
            "Within 90 days, Polymarket supports 8 of 13 states by mean Brier "
            "and row majority; rows still repeat one election context."
        ),
        ha="center",
        fontsize=9,
        color="#374151",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    state_support: pd.DataFrame,
    summary: pd.DataFrame,
    near_cases: pd.DataFrame,
    case_input: Path,
    state_support_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the state-level horizon support diagnostic."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_horizon_state_support",
            "calculation_scope": "deterministic_python_from_state_date_poll_panel_cases",
            "near_horizon_max_days": NEAR_HORIZON_MAX_DAYS,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "state_count": int(values["state_count"]),
            "row_count": int(values["row_count"]),
            "polymarket_lower_loss_count": int(values["polymarket_lower_loss_count"]),
            "poll_derived_lower_loss_count": int(values["poll_derived_lower_loss_count"]),
            "polymarket_better_share": float(values["polymarket_better_share"]),
            "mean_polymarket_brier": float(values["mean_polymarket_brier"]),
            "mean_poll_derived_brier": float(values["mean_poll_derived_brier"]),
            "polymarket_mean_support_state_count": int(
                values["polymarket_mean_support_state_count"]
            ),
            "polymarket_majority_support_state_count": int(
                values["polymarket_majority_support_state_count"]
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "h1_goal_completion_status": "not_proven",
        },
        "source_paths": {
            "case_input": str(case_input),
            "state_support": str(state_support_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "state_rows_share_one_election_context": True,
            "panel_rows_are_repeated_forecasts": True,
            "does_not_prove_broad_independent_many_cases_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _summary_row(
    summary_id: str,
    value: float | int,
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
    return {
        str(row["summary_id"]): float(row["value"])
        for _, row in summary.iterrows()
    }


def _format_date(value: Any) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--state-support-output", type=Path, default=STATE_SUPPORT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_horizon_state_outputs(
            case_input=args.case_input,
            state_support_output=args.state_support_output,
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
