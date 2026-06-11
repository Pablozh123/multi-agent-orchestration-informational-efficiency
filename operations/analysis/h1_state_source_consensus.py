"""Build an H1 cross-source state consensus diagnostic.

This module re-aggregates existing deterministic H1 state-level case artifacts.
It does not fetch live data and does not recompute from raw tables. The purpose
is diagnostic: show whether Polymarket's state-level lower-loss advantage is
stable across traditional poll-derived and poll-model sources, and separate
direct poll-transform evidence from model-forecast evidence.
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
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


STATE_POLL_INPUT = RESULTS_DIR / "h1_state_poll_snapshot_cases.csv"
TWO_SEVENTY_POLL_AVERAGE_INPUT = RESULTS_DIR / "h1_270towin_poll_average_cases.csv"
RIEKE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_cases.csv"
TWO_SEVENTY_INPUT = RESULTS_DIR / "h1_270towin_state_forecast_cases.csv"

CASES_OUTPUT = RESULTS_DIR / "h1_state_source_consensus_cases.csv"
STATE_SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_source_consensus_state_summary.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_source_consensus_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_source_consensus.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_source_consensus_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "source_id",
    "source_label",
    "source_family",
    "source_artifact",
    "case_id",
    "state",
    "outcome_value",
    "polymarket_probability",
    "comparator_probability",
    "polymarket_brier",
    "comparator_brier",
    "loss_advantage",
    "lower_loss_source",
    "allowed_interpretation",
    "limitation",
)

STATE_SUMMARY_COLUMNS: tuple[str, ...] = (
    "state",
    "source_count",
    "direct_poll_source_count",
    "polymarket_lower_loss_source_count",
    "comparator_lower_loss_source_count",
    "tie_source_count",
    "polymarket_lower_loss_share",
    "state_consensus_winner",
    "direct_poll_polymarket_lower_loss_count",
    "direct_poll_comparator_lower_loss_count",
    "direct_poll_tie_count",
    "direct_poll_consensus_winner",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "source_ids",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

DIRECT_POLL_FAMILY = "direct_poll_transform"


@dataclass(frozen=True)
class SourceSpec:
    """Input contract for one existing state-level H1 artifact."""

    source_id: str
    source_label: str
    source_family: str
    source_artifact: str
    probability_column: str
    brier_column: str


@dataclass(frozen=True)
class H1StateSourceConsensusResult:
    """Summary of generated cross-source state consensus artifacts."""

    cases_path: Path
    state_summary_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    source_state_case_count: int
    state_count: int
    all_source_polymarket_majority_state_count: int
    all_source_comparator_majority_state_count: int
    direct_poll_two_source_polymarket_majority_state_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "cases_path": str(self.cases_path),
            "state_summary_path": str(self.state_summary_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "source_state_case_count": self.source_state_case_count,
            "state_count": self.state_count,
            "all_source_polymarket_majority_state_count": (
                self.all_source_polymarket_majority_state_count
            ),
            "all_source_comparator_majority_state_count": (
                self.all_source_comparator_majority_state_count
            ),
            "direct_poll_two_source_polymarket_majority_state_count": (
                self.direct_poll_two_source_polymarket_majority_state_count
            ),
        }


SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        source_id="five_thirty_eight_poll_snapshot",
        source_label="538 poll snapshot",
        source_family=DIRECT_POLL_FAMILY,
        source_artifact="h1_state_poll_snapshot_cases.csv",
        probability_column="poll_derived_probability",
        brier_column="poll_derived_brier",
    ),
    SourceSpec(
        source_id="two_seventy_poll_average",
        source_label="270toWin poll average",
        source_family=DIRECT_POLL_FAMILY,
        source_artifact="h1_270towin_poll_average_cases.csv",
        probability_column="poll_derived_probability",
        brier_column="poll_derived_brier",
    ),
    SourceSpec(
        source_id="rieke_poll_model",
        source_label="Rieke poll model",
        source_family="poll_model_forecast",
        source_artifact="h1_rieke_state_forecast_cases.csv",
        probability_column="rieke_republican_win_probability",
        brier_column="rieke_brier",
    ),
    SourceSpec(
        source_id="two_seventy_jhk_model",
        source_label="270toWin/JHK model",
        source_family="poll_model_forecast",
        source_artifact="h1_270towin_state_forecast_cases.csv",
        probability_column="two_seventy_trump_win_probability",
        brier_column="two_seventy_brier",
    ),
)


def generate_h1_state_source_consensus_outputs(
    *,
    state_poll_input: Path = STATE_POLL_INPUT,
    two_seventy_poll_average_input: Path = TWO_SEVENTY_POLL_AVERAGE_INPUT,
    rieke_input: Path = RIEKE_INPUT,
    two_seventy_input: Path = TWO_SEVENTY_INPUT,
    cases_output: Path = CASES_OUTPUT,
    state_summary_output: Path = STATE_SUMMARY_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StateSourceConsensusResult:
    """Generate consensus case, state-summary, summary, figure, and metadata files."""

    source_paths = {
        "five_thirty_eight_poll_snapshot": state_poll_input,
        "two_seventy_poll_average": two_seventy_poll_average_input,
        "rieke_poll_model": rieke_input,
        "two_seventy_jhk_model": two_seventy_input,
    }
    cases = validate_consensus_cases(
        build_consensus_cases(
            {
                spec.source_id: read_source_cases(
                    source_paths[spec.source_id],
                    spec=spec,
                )
                for spec in SOURCE_SPECS
            }
        )
    )
    state_summary = validate_state_summary(build_state_summary(cases))
    summary = build_summary(cases=cases, state_summary=state_summary)

    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    state_summary.to_csv(state_summary_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_consensus_figure(
        cases=cases,
        state_summary=state_summary,
        output_path=figure_output,
    )
    metadata = build_metadata(
        cases=cases,
        state_summary=state_summary,
        summary=summary,
        source_paths=source_paths,
        cases_output=cases_output,
        state_summary_output=state_summary_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1StateSourceConsensusResult(
        cases_path=cases_output,
        state_summary_path=state_summary_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        source_state_case_count=int(values["source_state_case_count"]),
        state_count=int(values["state_count"]),
        all_source_polymarket_majority_state_count=int(
            values["all_source_polymarket_majority_state_count"]
        ),
        all_source_comparator_majority_state_count=int(
            values["all_source_comparator_majority_state_count"]
        ),
        direct_poll_two_source_polymarket_majority_state_count=int(
            values["direct_poll_two_source_polymarket_majority_state_count"]
        ),
    )


def read_source_cases(path: Path, *, spec: SourceSpec) -> pd.DataFrame:
    """Read and normalize one existing H1 state-level source artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 state source input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "case_id",
        "state",
        "outcome_value",
        "polymarket_probability",
        "polymarket_brier",
        spec.probability_column,
        spec.brier_column,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{spec.source_artifact} missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker"))
    ]
    if forbidden:
        raise ValueError(f"{spec.source_artifact} contains forbidden columns: {forbidden}")

    normalized = frame.copy()
    for column in (
        "outcome_value",
        "polymarket_probability",
        "polymarket_brier",
        spec.probability_column,
        spec.brier_column,
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in (
        "outcome_value",
        "polymarket_probability",
        spec.probability_column,
    ):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{spec.source_artifact} {column} values must be in [0, 1]")
    if (normalized["polymarket_brier"] < 0).any() or (
        normalized[spec.brier_column] < 0
    ).any():
        raise ValueError(f"{spec.source_artifact} Brier values must be non-negative")

    rows: list[dict[str, Any]] = []
    for item in normalized.itertuples(index=False):
        row = item._asdict()
        pm_brier = float(row["polymarket_brier"])
        comparator_brier = float(row[spec.brier_column])
        if pm_brier < comparator_brier:
            lower_loss_source = "polymarket"
        elif comparator_brier < pm_brier:
            lower_loss_source = "comparator"
        else:
            lower_loss_source = "tie"
        rows.append(
            {
                "source_id": spec.source_id,
                "source_label": spec.source_label,
                "source_family": spec.source_family,
                "source_artifact": spec.source_artifact,
                "case_id": str(row["case_id"]),
                "state": str(row["state"]),
                "outcome_value": float(row["outcome_value"]),
                "polymarket_probability": float(row["polymarket_probability"]),
                "comparator_probability": float(row[spec.probability_column]),
                "polymarket_brier": pm_brier,
                "comparator_brier": comparator_brier,
                "loss_advantage": comparator_brier - pm_brier,
                "lower_loss_source": lower_loss_source,
                "allowed_interpretation": (
                    "Cross-source state-level lower-loss diagnostic for existing "
                    "H1 Polymarket-vs-traditional comparison artifacts."
                ),
                "limitation": (
                    "Rows reuse one 2024 presidential election context and "
                    "source outputs are not independent elections."
                ),
            }
        )
    if not rows:
        raise ValueError(f"{spec.source_artifact} contains no state rows")
    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def build_consensus_cases(source_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine normalized state-source cases."""

    missing_sources = sorted({spec.source_id for spec in SOURCE_SPECS} - set(source_frames))
    if missing_sources:
        raise ValueError(f"Missing source frames: {missing_sources}")
    combined = pd.concat(
        [source_frames[spec.source_id] for spec in SOURCE_SPECS],
        ignore_index=True,
    )
    return combined.loc[:, list(CASE_COLUMNS)].sort_values(
        ["source_id", "state"]
    ).reset_index(drop=True)


def validate_consensus_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the long source-state case table."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 state-source consensus cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker"))
    ]
    if forbidden:
        raise ValueError(
            f"H1 state-source consensus cases contain forbidden columns: {forbidden}"
        )
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in ("outcome_value", "polymarket_probability", "comparator_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if (normalized["polymarket_brier"] < 0).any() or (
        normalized["comparator_brier"] < 0
    ).any():
        raise ValueError("Brier values must be non-negative")
    valid_winners = {"polymarket", "comparator", "tie"}
    if not set(normalized["lower_loss_source"]).issubset(valid_winners):
        raise ValueError("lower_loss_source contains unknown values")
    if normalized.duplicated(["source_id", "state"]).any():
        raise ValueError("Each source_id/state pair must appear at most once")
    return normalized.sort_values(["source_id", "state"]).reset_index(drop=True)


def build_state_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Aggregate long source-state cases to one row per state."""

    rows: list[dict[str, Any]] = []
    for state, group in cases.groupby("state", sort=True):
        direct = group.loc[group["source_family"] == DIRECT_POLL_FAMILY]
        pm_count = int((group["lower_loss_source"] == "polymarket").sum())
        comp_count = int((group["lower_loss_source"] == "comparator").sum())
        tie_count = int((group["lower_loss_source"] == "tie").sum())
        direct_pm = int((direct["lower_loss_source"] == "polymarket").sum())
        direct_comp = int((direct["lower_loss_source"] == "comparator").sum())
        direct_tie = int((direct["lower_loss_source"] == "tie").sum())
        rows.append(
            {
                "state": str(state),
                "source_count": int(len(group)),
                "direct_poll_source_count": int(len(direct)),
                "polymarket_lower_loss_source_count": pm_count,
                "comparator_lower_loss_source_count": comp_count,
                "tie_source_count": tie_count,
                "polymarket_lower_loss_share": pm_count / len(group),
                "state_consensus_winner": _winner(pm_count, comp_count, tie_count),
                "direct_poll_polymarket_lower_loss_count": direct_pm,
                "direct_poll_comparator_lower_loss_count": direct_comp,
                "direct_poll_tie_count": direct_tie,
                "direct_poll_consensus_winner": _winner(
                    direct_pm,
                    direct_comp,
                    direct_tie,
                )
                if len(direct)
                else "no_direct_poll_source",
                "mean_polymarket_brier": float(group["polymarket_brier"].mean()),
                "mean_comparator_brier": float(group["comparator_brier"].mean()),
                "mean_loss_advantage": float(group["loss_advantage"].mean()),
                "source_ids": ";".join(group["source_id"].astype(str).tolist()),
                "allowed_interpretation": (
                    "State-level consensus over existing H1 source comparisons."
                ),
                "limitation": (
                    "Consensus counts compare source outputs for the same state "
                    "outcome; they are not independent election outcomes."
                ),
            }
        )
    return pd.DataFrame(rows, columns=STATE_SUMMARY_COLUMNS)


def validate_state_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate one-row-per-state consensus summary."""

    missing = [column for column in STATE_SUMMARY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 state-source state summary missing columns: {missing}")
    normalized = frame.loc[:, list(STATE_SUMMARY_COLUMNS)].copy()
    for column in (
        "source_count",
        "direct_poll_source_count",
        "polymarket_lower_loss_source_count",
        "comparator_lower_loss_source_count",
        "tie_source_count",
        "direct_poll_polymarket_lower_loss_count",
        "direct_poll_comparator_lower_loss_count",
        "direct_poll_tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (normalized["source_count"] <= 0).any():
        raise ValueError("source_count must be positive")
    if (
        normalized["polymarket_lower_loss_source_count"]
        + normalized["comparator_lower_loss_source_count"]
        + normalized["tie_source_count"]
        != normalized["source_count"]
    ).any():
        raise ValueError("state summary lower-loss counts must add to source_count")
    if not normalized["polymarket_lower_loss_share"].between(0.0, 1.0).all():
        raise ValueError("polymarket_lower_loss_share values must be in [0, 1]")
    return normalized.sort_values("state").reset_index(drop=True)


def build_summary(*, cases: pd.DataFrame, state_summary: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the state-source consensus diagnostic."""

    direct_cases = cases.loc[cases["source_family"] == DIRECT_POLL_FAMILY]
    direct_states = state_summary.loc[state_summary["direct_poll_source_count"] > 0]
    direct_two_source_states = state_summary.loc[
        state_summary["direct_poll_source_count"] >= 2
    ]
    rows = [
        _summary_row(
            "source_state_case_count",
            len(cases),
            "source-state cases",
            "Total long rows across all included H1 state source artifacts.",
        ),
        _summary_row(
            "source_count",
            cases["source_id"].nunique(),
            "sources",
            "Included state-level traditional comparator sources.",
        ),
        _summary_row(
            "state_count",
            state_summary["state"].nunique(),
            "states",
            "Distinct resolved state outcomes covered by at least one source.",
        ),
        _summary_row(
            "all_source_polymarket_lower_loss_count",
            int((cases["lower_loss_source"] == "polymarket").sum()),
            "source-state cases",
            "Cases where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "all_source_comparator_lower_loss_count",
            int((cases["lower_loss_source"] == "comparator").sum()),
            "source-state cases",
            "Cases where the traditional comparator has lower Brier loss.",
        ),
        _summary_row(
            "all_source_tie_count",
            int((cases["lower_loss_source"] == "tie").sum()),
            "source-state cases",
            "Cases with equal Brier loss.",
        ),
        _summary_row(
            "all_source_mean_polymarket_brier",
            float(cases["polymarket_brier"].mean()),
            "brier_score",
            "Mean Polymarket Brier across source-state cases.",
        ),
        _summary_row(
            "all_source_mean_comparator_brier",
            float(cases["comparator_brier"].mean()),
            "brier_score",
            "Mean comparator Brier across source-state cases.",
        ),
        _summary_row(
            "all_source_mean_loss_advantage",
            float(cases["loss_advantage"].mean()),
            "brier_score",
            "Positive values mean lower mean Polymarket loss across source-state cases.",
        ),
        _summary_row(
            "all_source_polymarket_majority_state_count",
            _state_winner_count(state_summary, "state_consensus_winner", "polymarket"),
            "states",
            "States where Polymarket has the most lower-loss source comparisons.",
        ),
        _summary_row(
            "all_source_comparator_majority_state_count",
            _state_winner_count(state_summary, "state_consensus_winner", "comparator"),
            "states",
            "States where comparators have the most lower-loss source comparisons.",
        ),
        _summary_row(
            "all_source_tie_state_count",
            _state_winner_count(state_summary, "state_consensus_winner", "tie"),
            "states",
            "States tied by source lower-loss consensus.",
        ),
        _summary_row(
            "direct_poll_source_state_case_count",
            len(direct_cases),
            "source-state cases",
            "Long rows from direct poll-transform sources only.",
        ),
        _summary_row(
            "direct_poll_state_count",
            len(direct_states),
            "states",
            "States with at least one direct poll-transform source.",
        ),
        _summary_row(
            "direct_poll_polymarket_lower_loss_count",
            int((direct_cases["lower_loss_source"] == "polymarket").sum()),
            "source-state cases",
            "Direct poll-transform cases where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "direct_poll_comparator_lower_loss_count",
            int((direct_cases["lower_loss_source"] == "comparator").sum()),
            "source-state cases",
            "Direct poll-transform cases where the poll-derived comparator has lower loss.",
        ),
        _summary_row(
            "direct_poll_polymarket_majority_state_count",
            _state_winner_count(
                direct_states,
                "direct_poll_consensus_winner",
                "polymarket",
            ),
            "states",
            "Direct-poll states where Polymarket has the most lower-loss source rows.",
        ),
        _summary_row(
            "direct_poll_comparator_majority_state_count",
            _state_winner_count(
                direct_states,
                "direct_poll_consensus_winner",
                "comparator",
            ),
            "states",
            "Direct-poll states where poll-derived comparators have the most lower-loss source rows.",
        ),
        _summary_row(
            "direct_poll_tie_state_count",
            _state_winner_count(direct_states, "direct_poll_consensus_winner", "tie"),
            "states",
            "Direct-poll states tied by source lower-loss consensus.",
        ),
        _summary_row(
            "direct_poll_two_source_state_count",
            len(direct_two_source_states),
            "states",
            "States covered by at least two direct poll-transform sources.",
        ),
        _summary_row(
            "direct_poll_two_source_polymarket_majority_state_count",
            _state_winner_count(
                direct_two_source_states,
                "direct_poll_consensus_winner",
                "polymarket",
            ),
            "states",
            "Two-direct-source states where Polymarket has more lower-loss source rows.",
        ),
        _summary_row(
            "direct_poll_two_source_comparator_majority_state_count",
            _state_winner_count(
                direct_two_source_states,
                "direct_poll_consensus_winner",
                "comparator",
            ),
            "states",
            "Two-direct-source states where poll-derived comparators have more lower-loss source rows.",
        ),
        _summary_row(
            "direct_poll_two_source_tie_state_count",
            _state_winner_count(
                direct_two_source_states,
                "direct_poll_consensus_winner",
                "tie",
            ),
            "states",
            "Two-direct-source states tied by source lower-loss consensus.",
        ),
        _summary_row(
            "broad_many_cases_claim_supported_now",
            0,
            "binary",
            "This diagnostic does not prove the requested broad many-cases claim.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_consensus_figure(
    *,
    cases: pd.DataFrame,
    state_summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a readable consensus figure."""

    source_order = [spec.source_id for spec in SOURCE_SPECS]
    source_labels = [spec.source_label for spec in SOURCE_SPECS]
    states = sorted(state_summary["state"].astype(str).tolist())
    value_map = {"comparator": 0, "tie": 1, "polymarket": 2}
    matrix = np.full((len(source_order), len(states)), -1)
    for source_idx, source_id in enumerate(source_order):
        rows = cases.loc[cases["source_id"] == source_id].set_index("state")
        for state_idx, state in enumerate(states):
            if state in rows.index:
                matrix[source_idx, state_idx] = value_map[
                    str(rows.loc[state, "lower_loss_source"])
                ]

    source_counts = cases.groupby(["source_label", "lower_loss_source"]).size().unstack(
        fill_value=0
    )
    source_counts = source_counts.reindex(source_labels, fill_value=0)
    consensus_counts = state_summary["state_consensus_winner"].value_counts()
    direct_two = state_summary.loc[state_summary["direct_poll_source_count"] >= 2]
    direct_two_counts = direct_two["direct_poll_consensus_winner"].value_counts()

    fig, axes = plt.subplots(2, 2, figsize=(17.4, 10.2))
    fig.suptitle(
        "H1 State-Source Consensus Diagnostic",
        fontsize=14,
        fontweight="bold",
    )

    x = np.arange(len(source_labels))
    pm_values = [
        int(source_counts.loc[label].get("polymarket", 0)) for label in source_labels
    ]
    comp_values = [
        int(source_counts.loc[label].get("comparator", 0)) for label in source_labels
    ]
    tie_values = [int(source_counts.loc[label].get("tie", 0)) for label in source_labels]
    width = 0.34
    axes[0, 0].bar(x - width / 2, pm_values, width=width, color="#2563eb", label="PM")
    axes[0, 0].bar(
        x + width / 2,
        comp_values,
        width=width,
        color="#7c3aed",
        label="Comparator",
    )
    if any(tie_values):
        axes[0, 0].bar(x + width * 1.45, tie_values, width=width * 0.65, color="#9ca3af", label="Tie")
    axes[0, 0].set_xticks(x, ["538\npoll", "270\npoll", "Rieke\nmodel", "270/JHK\nmodel"])
    axes[0, 0].set_ylabel("State cases")
    axes[0, 0].set_title("Lower-loss counts by source")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(pm_values):
        axes[0, 0].text(idx - width / 2, value + 0.5, str(value), ha="center", fontsize=8)
    for idx, value in enumerate(comp_values):
        axes[0, 0].text(idx + width / 2, value + 0.5, str(value), ha="center", fontsize=8)

    all_labels = ["Polymarket", "Comparator", "Tie"]
    all_values = [
        int(consensus_counts.get("polymarket", 0)),
        int(consensus_counts.get("comparator", 0)),
        int(consensus_counts.get("tie", 0)),
    ]
    axes[0, 1].bar(all_labels, all_values, color=["#2563eb", "#7c3aed", "#9ca3af"])
    axes[0, 1].set_ylabel("States")
    axes[0, 1].set_title("All-source state consensus")
    axes[0, 1].set_ylim(0, max(all_values) + 5)
    axes[0, 1].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(all_values):
        axes[0, 1].text(idx, value + 0.7, str(value), ha="center", fontsize=9)

    two_labels = ["Polymarket", "Comparator", "Tie"]
    two_values = [
        int(direct_two_counts.get("polymarket", 0)),
        int(direct_two_counts.get("comparator", 0)),
        int(direct_two_counts.get("tie", 0)),
    ]
    axes[1, 0].bar(two_labels, two_values, color=["#2563eb", "#7c3aed", "#9ca3af"])
    axes[1, 0].set_ylabel("States")
    axes[1, 0].set_title("States with two direct poll-transform sources")
    axes[1, 0].set_ylim(0, max(two_values) + 3)
    axes[1, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(two_values):
        axes[1, 0].text(idx, value + 0.35, str(value), ha="center", fontsize=9)

    cmap = ListedColormap(["#ffffff", "#7c3aed", "#9ca3af", "#2563eb"])
    axes[1, 1].imshow(matrix + 1, aspect="auto", cmap=cmap, vmin=0, vmax=3)
    axes[1, 1].set_yticks(range(len(source_labels)), ["538 poll", "270 poll", "Rieke", "270/JHK"])
    axes[1, 1].set_xticks(range(len(states)), states, rotation=90, fontsize=5.8)
    axes[1, 1].set_title("Per-state lower-loss winner by source")
    axes[1, 1].tick_params(axis="y", labelsize=8)
    axes[1, 1].set_xlabel("State")

    fig.text(
        0.5,
        0.012,
        (
            "Blue = Polymarket lower loss, purple = comparator lower loss, grey = tie. "
            "The diagnostic reuses state artifacts and is not a new independent-elections sample."
        ),
        ha="center",
        fontsize=9,
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
    state_summary: pd.DataFrame,
    summary: pd.DataFrame,
    source_paths: dict[str, Path],
    cases_output: Path,
    state_summary_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the consensus diagnostic."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_source_consensus",
            "calculation_scope": "deterministic_python_from_existing_h1_state_case_artifacts",
            "does_not_collect_external_data": True,
            "does_not_recompute_from_raw_database": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
        },
        "outputs": {
            "source_state_case_count": int(values["source_state_case_count"]),
            "state_count": int(values["state_count"]),
            "source_count": int(values["source_count"]),
            "all_source_polymarket_lower_loss_count": int(
                values["all_source_polymarket_lower_loss_count"]
            ),
            "all_source_comparator_lower_loss_count": int(
                values["all_source_comparator_lower_loss_count"]
            ),
            "all_source_tie_count": int(values["all_source_tie_count"]),
            "all_source_polymarket_majority_state_count": int(
                values["all_source_polymarket_majority_state_count"]
            ),
            "all_source_comparator_majority_state_count": int(
                values["all_source_comparator_majority_state_count"]
            ),
            "all_source_tie_state_count": int(values["all_source_tie_state_count"]),
            "direct_poll_two_source_state_count": int(
                values["direct_poll_two_source_state_count"]
            ),
            "direct_poll_two_source_polymarket_majority_state_count": int(
                values["direct_poll_two_source_polymarket_majority_state_count"]
            ),
            "direct_poll_two_source_comparator_majority_state_count": int(
                values["direct_poll_two_source_comparator_majority_state_count"]
            ),
            "direct_poll_two_source_tie_state_count": int(
                values["direct_poll_two_source_tie_state_count"]
            ),
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            **{key: str(path) for key, path in source_paths.items()},
            "cases": str(cases_output),
            "state_summary": str(state_summary_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "source_ids": sorted(cases["source_id"].unique().tolist()),
        "states": state_summary["state"].tolist(),
        "limitations": {
            "reuses_existing_h1_state_case_artifacts": True,
            "state_sources_are_not_independent_elections": True,
            "poll_models_and_poll_transforms_are_not_raw_poll_shares": True,
            "source_outputs_may_share_poll_information": True,
            "all_rows_share_one_presidential_election_context": True,
            "no_causal_or_tradeability_claim": True,
            "goal_many_cases_claim_not_yet_proven": True,
        },
    }


def _winner(pm_count: int, comparator_count: int, tie_count: int) -> str:
    if pm_count > comparator_count and pm_count > tie_count:
        return "polymarket"
    if comparator_count > pm_count and comparator_count > tie_count:
        return "comparator"
    return "tie"


def _state_winner_count(frame: pd.DataFrame, column: str, value: str) -> int:
    return int(frame[column].astype(str).eq(value).sum())


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
    parser.add_argument("--state-poll-input", type=Path, default=STATE_POLL_INPUT)
    parser.add_argument(
        "--two-seventy-poll-average-input",
        type=Path,
        default=TWO_SEVENTY_POLL_AVERAGE_INPUT,
    )
    parser.add_argument("--rieke-input", type=Path, default=RIEKE_INPUT)
    parser.add_argument("--two-seventy-input", type=Path, default=TWO_SEVENTY_INPUT)
    parser.add_argument("--cases-output", type=Path, default=CASES_OUTPUT)
    parser.add_argument("--state-summary-output", type=Path, default=STATE_SUMMARY_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_source_consensus_outputs(
            state_poll_input=args.state_poll_input,
            two_seventy_poll_average_input=args.two_seventy_poll_average_input,
            rieke_input=args.rieke_input,
            two_seventy_input=args.two_seventy_input,
            cases_output=args.cases_output,
            state_summary_output=args.state_summary_output,
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
