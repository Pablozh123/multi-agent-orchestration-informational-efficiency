"""Decision matrix for H1 Polymarket-vs-poll forecast-quality evidence.

This module does not create new forecast comparisons. It reads existing
deterministic H1 artifacts and turns them into one thesis-facing decision
matrix: which poll-related scopes support a bounded Polymarket advantage,
which rows are only mean-loss support, and which rows contradict the broad
many-cases claim.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
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


FRONTIER_INPUT = RESULTS_DIR / "h1_poll_scope_frontier.csv"
FRONTIER_SUMMARY_INPUT = RESULTS_DIR / "h1_poll_scope_frontier_summary.csv"
DIRECT_POLL_STATE_CLUSTER_INPUT = (
    RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_summary.csv"
)
TWO_SEVENTY_POLL_AVERAGE_INPUT = (
    RESULTS_DIR / "h1_270towin_poll_average_summary.csv"
)
STATE_SOURCE_CONSENSUS_INPUT = (
    RESULTS_DIR / "h1_state_source_consensus_summary.csv"
)
CALIBRATION_PAIRWISE_INPUT = RESULTS_DIR / "h1_calibration_diagnostic_pairwise.csv"

DECISION_OUTPUT = RESULTS_DIR / "h1_poll_decision_matrix.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_poll_decision_matrix_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_poll_decision_matrix.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_poll_decision_matrix_metadata.json"

DECISION_COLUMNS: tuple[str, ...] = (
    "decision_id",
    "decision_label",
    "evidence_family",
    "scope",
    "comparison_unit",
    "case_count",
    "polymarket_support_count",
    "comparator_support_count",
    "tie_count",
    "polymarket_support_share",
    "mean_loss_advantage",
    "unit_count",
    "polymarket_unit_support_count",
    "comparator_unit_support_count",
    "p_value",
    "mean_supports_polymarket",
    "case_majority_supports_polymarket",
    "unit_supports_polymarket",
    "broad_claim_supported",
    "decision_status",
    "allowed_claim",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

ROBUST_STATUS = "robust_bounded_yes"
MIXED_STATUS = "mixed_mean_only"
COUNTER_STATUS = "counterexample"
CALIBRATION_STATUS = "calibration_context"
BOUNDARY_STATUS = "directional_not_robust"


@dataclass(frozen=True)
class H1PollDecisionMatrixResult:
    """Summary of generated H1 poll decision artifacts."""

    decision_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    decision_row_count: int
    robust_bounded_yes_count: int
    counterexample_count: int
    broad_claim_proven: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "decision_path": str(self.decision_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "decision_row_count": self.decision_row_count,
            "robust_bounded_yes_count": self.robust_bounded_yes_count,
            "counterexample_count": self.counterexample_count,
            "broad_claim_proven": self.broad_claim_proven,
        }


def generate_h1_poll_decision_matrix_outputs(
    *,
    frontier_input: Path = FRONTIER_INPUT,
    frontier_summary_input: Path = FRONTIER_SUMMARY_INPUT,
    direct_poll_state_cluster_input: Path = DIRECT_POLL_STATE_CLUSTER_INPUT,
    two_seventy_poll_average_input: Path = TWO_SEVENTY_POLL_AVERAGE_INPUT,
    state_source_consensus_input: Path = STATE_SOURCE_CONSENSUS_INPUT,
    calibration_pairwise_input: Path = CALIBRATION_PAIRWISE_INPUT,
    decision_output: Path = DECISION_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1PollDecisionMatrixResult:
    """Generate H1 poll decision matrix CSV, summary, figure, and metadata."""

    frontier = read_frontier(frontier_input)
    frontier_summary = read_summary(frontier_summary_input)
    direct_poll_state_cluster = read_summary(direct_poll_state_cluster_input)
    two_seventy_poll_average = read_summary(two_seventy_poll_average_input)
    state_source_consensus = read_summary(state_source_consensus_input)
    calibration_pairwise = read_calibration_pairwise(calibration_pairwise_input)

    decision = validate_decision_table(
        build_decision_table(
            frontier=frontier,
            direct_poll_state_cluster=direct_poll_state_cluster,
            two_seventy_poll_average=two_seventy_poll_average,
            state_source_consensus=state_source_consensus,
            calibration_pairwise=calibration_pairwise,
        )
    )
    summary = validate_summary_table(
        build_summary_table(
            decision=decision,
            frontier_summary=frontier_summary,
            calibration_pairwise=calibration_pairwise,
        )
    )

    decision_output.parent.mkdir(parents=True, exist_ok=True)
    decision.to_csv(decision_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_decision_figure(decision=decision, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        decision=decision,
        summary=summary,
        frontier_input=frontier_input,
        frontier_summary_input=frontier_summary_input,
        direct_poll_state_cluster_input=direct_poll_state_cluster_input,
        two_seventy_poll_average_input=two_seventy_poll_average_input,
        state_source_consensus_input=state_source_consensus_input,
        calibration_pairwise_input=calibration_pairwise_input,
        decision_output=decision_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1PollDecisionMatrixResult(
        decision_path=decision_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        decision_row_count=int(len(decision)),
        robust_bounded_yes_count=int(
            (decision["decision_status"] == ROBUST_STATUS).sum()
        ),
        counterexample_count=int((decision["decision_status"] == COUNTER_STATUS).sum()),
        broad_claim_proven=bool(_summary_value(summary, "broad_claim_proven")),
    )


def read_frontier(path: Path) -> pd.DataFrame:
    """Read the H1 poll-scope frontier table."""

    if not path.exists():
        raise FileNotFoundError(f"H1 poll frontier input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "scope_id",
        "row_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
        "polymarket_lower_loss_share",
        "mean_loss_advantage",
        "state_month_unit_count",
        "state_month_polymarket_support_count",
        "state_month_poll_support_count",
        "state_month_exact_p_value",
        "frontier_status",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 poll frontier input missing columns: {missing}")
    return frame


def read_summary(path: Path) -> pd.DataFrame:
    """Read a summary_id/value artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 summary input not found: {path}")
    frame = pd.read_csv(path)
    required = {"summary_id", "value"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 summary input missing columns: {missing}")
    return frame


def read_calibration_pairwise(path: Path) -> pd.DataFrame:
    """Read the resolved-case calibration pairwise rows."""

    if not path.exists():
        raise FileNotFoundError(f"H1 calibration pairwise input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "comparison_id",
        "aggregate_mean_supports_polymarket",
        "majority_cases_supports_polymarket",
        "broad_many_cases_claim_supported",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 calibration pairwise input missing columns: {missing}")
    return frame


def build_decision_table(
    *,
    frontier: pd.DataFrame,
    direct_poll_state_cluster: pd.DataFrame,
    two_seventy_poll_average: pd.DataFrame,
    state_source_consensus: pd.DataFrame,
    calibration_pairwise: pd.DataFrame,
) -> pd.DataFrame:
    """Build the H1 poll decision matrix from existing deterministic summaries."""

    largest = _frontier_scope(frontier, "lte_120_days_low_middle_distance")
    strongest = _frontier_scope(frontier, "lte_90_days_low_middle_distance")
    lte90_all = _frontier_scope(frontier, "lte_90_days_all_distances")
    full_panel = _frontier_scope(frontier, "full_panel_all_distances")
    calibration_count = int(len(calibration_pairwise))
    calibration_mean_support = _bool_count(
        calibration_pairwise,
        "aggregate_mean_supports_polymarket",
    )
    calibration_majority_support = _bool_count(
        calibration_pairwise,
        "majority_cases_supports_polymarket",
    )
    calibration_broad_support = _bool_count(
        calibration_pairwise,
        "broad_many_cases_claim_supported",
    )

    rows = [
        _frontier_decision_row(
            row=largest,
            decision_id="largest_robust_poll_scope",
            decision_label="Largest robust poll scope",
            status=ROBUST_STATUS,
            allowed_claim=(
                "Yes, bounded: Polymarket has lower Brier loss in the largest "
                "robust H1 poll scope."
            ),
        ),
        _frontier_decision_row(
            row=strongest,
            decision_id="strongest_robust_poll_scope",
            decision_label="Strongest robust poll scope",
            status=ROBUST_STATUS,
            allowed_claim=(
                "Yes, bounded: Polymarket dominates the strongest late "
                "low/middle poll-distance scope."
            ),
        ),
        _frontier_decision_row(
            row=lte90_all,
            decision_id="lte_90_all_distances_boundary",
            decision_label="<=90 days, all poll distances",
            status=BOUNDARY_STATUS,
            allowed_claim=(
                "Directional only: row majority supports Polymarket, but "
                "state-month evidence misses the 0.05 rule."
            ),
        ),
        _frontier_decision_row(
            row=full_panel,
            decision_id="full_poll_panel_counterexample",
            decision_label="Full state-date poll panel",
            status=COUNTER_STATUS,
            allowed_claim=(
                "Counterexample: the full state-date poll panel supports the "
                "poll-derived comparator, not the broad Polymarket claim."
            ),
        ),
        _summary_decision_row(
            decision_id="direct_poll_equal_state_mean",
            decision_label="Direct poll equal-state mean",
            evidence_family="direct_poll_state_clusters",
            scope="43 states with direct poll-transform source rows",
            comparison_unit="state_clusters",
            case_count=int(_summary_value(direct_poll_state_cluster, "state_count")),
            pm_support=int(
                _summary_value(
                    direct_poll_state_cluster,
                    "state_mean_polymarket_support_count",
                )
            ),
            comparator_support=int(
                _summary_value(
                    direct_poll_state_cluster,
                    "state_mean_poll_support_count",
                )
            ),
            ties=int(_summary_value(direct_poll_state_cluster, "state_mean_tie_count")),
            mean_loss_advantage=_summary_value(
                direct_poll_state_cluster,
                "equal_state_mean_loss_advantage",
            ),
            unit_count=int(_summary_value(direct_poll_state_cluster, "state_count")),
            pm_units=int(
                _summary_value(
                    direct_poll_state_cluster,
                    "state_mean_polymarket_support_count",
                )
            ),
            comparator_units=int(
                _summary_value(
                    direct_poll_state_cluster,
                    "state_mean_poll_support_count",
                )
            ),
            p_value=_summary_value(
                direct_poll_state_cluster,
                "equal_state_sign_flip_p_value_greater",
            ),
            status=MIXED_STATUS,
            allowed_claim=(
                "Mean-loss support only: equal-state mean supports Polymarket, "
                "but the state-count majority supports poll-derived comparators."
            ),
            limitation=(
                "Direct poll-transform states are one election context; "
                "state majority contradicts a broad Polymarket claim."
            ),
        ),
        _summary_decision_row(
            decision_id="two_seventy_poll_average_states",
            decision_label="270toWin poll-average states",
            evidence_family="direct_poll_transform",
            scope="43 270toWin polling-average state outcomes",
            comparison_unit="resolved_state_outcomes",
            case_count=int(_summary_value(two_seventy_poll_average, "case_count")),
            pm_support=int(
                _summary_value(
                    two_seventy_poll_average,
                    "polymarket_lower_loss_count",
                )
            ),
            comparator_support=int(
                _summary_value(
                    two_seventy_poll_average,
                    "poll_derived_lower_loss_count",
                )
            ),
            ties=int(_summary_value(two_seventy_poll_average, "tie_count")),
            mean_loss_advantage=_summary_value(
                two_seventy_poll_average,
                "mean_loss_advantage",
            ),
            unit_count=int(_summary_value(two_seventy_poll_average, "case_count")),
            pm_units=int(
                _summary_value(
                    two_seventy_poll_average,
                    "polymarket_lower_loss_count",
                )
            ),
            comparator_units=int(
                _summary_value(
                    two_seventy_poll_average,
                    "poll_derived_lower_loss_count",
                )
            ),
            p_value=float("nan"),
            status=MIXED_STATUS,
            allowed_claim=(
                "Mean-loss support only: Polymarket has lower mean Brier, "
                "but poll-derived probabilities win most state cases."
            ),
            limitation=(
                "Poll-average margins are transformed to probabilities; "
                "state cases share one election context."
            ),
        ),
        _summary_decision_row(
            decision_id="direct_poll_source_state_consensus",
            decision_label="Direct poll source-state consensus",
            evidence_family="direct_poll_consensus",
            scope="56 direct poll-transform source-state rows",
            comparison_unit="source_state_cases_and_states",
            case_count=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_source_state_case_count",
                )
            ),
            pm_support=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_polymarket_lower_loss_count",
                )
            ),
            comparator_support=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_comparator_lower_loss_count",
                )
            ),
            ties=0,
            mean_loss_advantage=float("nan"),
            unit_count=int(
                _summary_value(state_source_consensus, "direct_poll_state_count")
            ),
            pm_units=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_polymarket_majority_state_count",
                )
            ),
            comparator_units=int(
                _summary_value(
                    state_source_consensus,
                    "direct_poll_comparator_majority_state_count",
                )
            ),
            p_value=float("nan"),
            status=COUNTER_STATUS,
            allowed_claim=(
                "Counterexample to case majority: direct poll-derived rows and "
                "state consensus mostly favor the comparator."
            ),
            limitation=(
                "Consensus counts are source-state rows and state tallies, "
                "not independent elections."
            ),
        ),
        _summary_decision_row(
            decision_id="all_source_state_consensus",
            decision_label="All-source state consensus",
            evidence_family="state_source_consensus",
            scope="156 source-state rows across 4 traditional sources",
            comparison_unit="source_state_cases_and_states",
            case_count=int(
                _summary_value(state_source_consensus, "source_state_case_count")
            ),
            pm_support=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_polymarket_lower_loss_count",
                )
            ),
            comparator_support=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_comparator_lower_loss_count",
                )
            ),
            ties=int(
                _summary_value(state_source_consensus, "all_source_tie_count")
            ),
            mean_loss_advantage=_summary_value(
                state_source_consensus,
                "all_source_mean_loss_advantage",
            ),
            unit_count=int(_summary_value(state_source_consensus, "state_count")),
            pm_units=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_polymarket_majority_state_count",
                )
            ),
            comparator_units=int(
                _summary_value(
                    state_source_consensus,
                    "all_source_comparator_majority_state_count",
                )
            ),
            p_value=float("nan"),
            status=MIXED_STATUS,
            allowed_claim=(
                "Mixed: aggregate mean Brier supports Polymarket, but source-case "
                "and state consensus favor traditional comparators."
            ),
            limitation=(
                "All-source consensus mixes poll transforms and poll-based "
                "model forecasts from one election context."
            ),
        ),
        _summary_decision_row(
            decision_id="calibration_resolved_case_sets",
            decision_label="Resolved-case calibration context",
            evidence_family="calibration",
            scope="5 pairwise resolved-case calibration diagnostics",
            comparison_unit="pairwise_comparison_rows",
            case_count=calibration_count,
            pm_support=calibration_mean_support,
            comparator_support=calibration_count - calibration_mean_support,
            ties=0,
            mean_loss_advantage=float("nan"),
            unit_count=calibration_count,
            pm_units=calibration_majority_support,
            comparator_units=calibration_count - calibration_majority_support,
            p_value=float("nan"),
            status=CALIBRATION_STATUS,
            allowed_claim=(
                "Calibration context: all pairwise rows support lower mean "
                "Polymarket Brier, but only some support case majority."
            ),
            limitation=(
                "Calibration rows include poll and model comparators; they are "
                "not a standalone poll-only proof."
            ),
            broad_claim_supported=calibration_broad_support > 0,
        ),
    ]
    return pd.DataFrame(rows, columns=DECISION_COLUMNS)


def build_summary_table(
    *,
    decision: pd.DataFrame,
    frontier_summary: pd.DataFrame,
    calibration_pairwise: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact summary rows for reporting."""

    largest = _decision_row(decision, "largest_robust_poll_scope")
    strongest = _decision_row(decision, "strongest_robust_poll_scope")
    full_panel = _decision_row(decision, "full_poll_panel_counterexample")
    calibration_count = int(len(calibration_pairwise))
    calibration_mean_support = _bool_count(
        calibration_pairwise,
        "aggregate_mean_supports_polymarket",
    )
    calibration_majority_support = _bool_count(
        calibration_pairwise,
        "majority_cases_supports_polymarket",
    )
    return pd.DataFrame(
        [
            _summary_row(
                "decision_row_count",
                int(len(decision)),
                "rows",
                "Rows in the H1 poll decision matrix.",
            ),
            _summary_row(
                "robust_bounded_yes_count",
                int((decision["decision_status"] == ROBUST_STATUS).sum()),
                "rows",
                "Decision rows with robust bounded Polymarket support.",
            ),
            _summary_row(
                "directional_not_robust_count",
                int((decision["decision_status"] == BOUNDARY_STATUS).sum()),
                "rows",
                "Rows with directional Polymarket support that miss the robust rule.",
            ),
            _summary_row(
                "mixed_mean_only_count",
                int((decision["decision_status"] == MIXED_STATUS).sum()),
                "rows",
                "Rows where aggregate or mean support does not imply case/unit majority.",
            ),
            _summary_row(
                "counterexample_count",
                int((decision["decision_status"] == COUNTER_STATUS).sum()),
                "rows",
                "Rows that contradict the broad Polymarket-better claim.",
            ),
            _summary_row(
                "largest_robust_scope_id",
                "lte_120_days_low_middle_distance",
                "scope",
                "Largest robust poll-scope frontier row.",
            ),
            _summary_row(
                "largest_robust_row_count",
                int(largest["case_count"]),
                "state-date rows",
                "State-date rows in the largest robust decision row.",
            ),
            _summary_row(
                "largest_robust_polymarket_support_count",
                int(largest["polymarket_support_count"]),
                "state-date rows",
                "Rows where Polymarket has lower loss in the largest robust row.",
            ),
            _summary_row(
                "largest_robust_comparator_support_count",
                int(largest["comparator_support_count"]),
                "state-date rows",
                "Rows where poll-derived probabilities have lower loss in the largest robust row.",
            ),
            _summary_row(
                "largest_robust_polymarket_support_share",
                float(largest["polymarket_support_share"]),
                "share",
                "Polymarket lower-loss share in the largest robust decision row.",
            ),
            _summary_row(
                "largest_robust_state_month_polymarket_support_count",
                int(largest["polymarket_unit_support_count"]),
                "state_month units",
                "State-month units supporting Polymarket in the largest robust row.",
            ),
            _summary_row(
                "largest_robust_state_month_count",
                int(largest["unit_count"]),
                "state_month units",
                "State-month units in the largest robust row.",
            ),
            _summary_row(
                "largest_robust_p_value",
                float(largest["p_value"]),
                "p_value",
                "State-month exact p-value in the largest robust row.",
            ),
            _summary_row(
                "strongest_robust_scope_id",
                "lte_90_days_low_middle_distance",
                "scope",
                "Strongest robust poll-scope frontier row.",
            ),
            _summary_row(
                "strongest_robust_row_count",
                int(strongest["case_count"]),
                "state-date rows",
                "State-date rows in the strongest robust decision row.",
            ),
            _summary_row(
                "strongest_robust_polymarket_support_count",
                int(strongest["polymarket_support_count"]),
                "state-date rows",
                "Rows where Polymarket has lower loss in the strongest robust row.",
            ),
            _summary_row(
                "strongest_robust_p_value",
                float(strongest["p_value"]),
                "p_value",
                "State-month exact p-value in the strongest robust row.",
            ),
            _summary_row(
                "frontier_robust_scope_count",
                int(_summary_value(frontier_summary, "robust_scope_count")),
                "scopes",
                "Robust scopes in the full horizon x poll-distance frontier.",
            ),
            _summary_row(
                "full_panel_poll_support_count",
                int(full_panel["comparator_support_count"]),
                "state-date rows",
                "Full-panel rows where poll-derived probabilities have lower loss.",
            ),
            _summary_row(
                "full_panel_row_count",
                int(full_panel["case_count"]),
                "state-date rows",
                "Full-panel state-date rows.",
            ),
            _summary_row(
                "calibration_pairwise_count",
                calibration_count,
                "pairwise rows",
                "Resolved-case calibration pairwise diagnostics.",
            ),
            _summary_row(
                "calibration_aggregate_support_count",
                calibration_mean_support,
                "pairwise rows",
                "Calibration rows where mean Brier supports Polymarket.",
            ),
            _summary_row(
                "calibration_majority_support_count",
                calibration_majority_support,
                "pairwise rows",
                "Calibration rows where case majority also supports Polymarket.",
            ),
            _summary_row(
                "bounded_poll_claim_ready",
                1,
                "binary",
                "A bounded poll claim is supported for late low/middle poll-distance scopes.",
            ),
            _summary_row(
                "broad_claim_proven",
                0,
                "binary",
                "The broad many-cases or many-elections claim remains unproven.",
            ),
            _summary_row(
                "h1_goal_completion_status",
                "not_proven",
                "status",
                "The bounded poll claim is supported, but the broad thread objective remains incomplete.",
            ),
        ],
        columns=SUMMARY_COLUMNS,
    )


def validate_decision_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the decision matrix table contract."""

    missing = [column for column in DECISION_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 poll decision matrix missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"H1 poll decision matrix contains forbidden columns: {forbidden}")
    normalized = frame.loc[:, list(DECISION_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("H1 poll decision matrix must not be empty")
    if normalized["decision_id"].duplicated().any():
        raise ValueError("decision_id values must be unique")
    for column in (
        "case_count",
        "polymarket_support_count",
        "comparator_support_count",
        "tie_count",
        "unit_count",
        "polymarket_unit_support_count",
        "comparator_unit_support_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_support_share",
        "mean_loss_advantage",
        "p_value",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    if (normalized["case_count"] <= 0).any():
        raise ValueError("case_count values must be positive")
    if (
        normalized["polymarket_support_count"]
        + normalized["comparator_support_count"]
        + normalized["tie_count"]
        != normalized["case_count"]
    ).any():
        raise ValueError("support counts must add to case_count")
    if not normalized["polymarket_support_share"].between(0.0, 1.0).all():
        raise ValueError("support shares must be in [0, 1]")
    for column in (
        "mean_supports_polymarket",
        "case_majority_supports_polymarket",
        "unit_supports_polymarket",
        "broad_claim_supported",
    ):
        normalized[column] = normalized[column].astype(bool)
    allowed_status = {
        ROBUST_STATUS,
        MIXED_STATUS,
        COUNTER_STATUS,
        CALIBRATION_STATUS,
        BOUNDARY_STATUS,
    }
    unknown = sorted(set(normalized["decision_status"]) - allowed_status)
    if unknown:
        raise ValueError(f"unknown decision_status values: {unknown}")
    return normalized


def validate_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact summary rows."""

    missing = [column for column in SUMMARY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 poll decision summary missing columns: {missing}")
    normalized = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("H1 poll decision summary must not be empty")
    if normalized["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return normalized


def write_decision_figure(
    *,
    decision: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the H1 poll decision matrix figure."""

    fig, axes = plt.subplots(2, 2, figsize=(16.0, 10.2))
    fig.suptitle(
        "H1 Poll Decision Matrix: Forecast Quality Claim Boundary",
        fontsize=14.5,
        fontweight="bold",
    )
    _plot_status_matrix(axes[0, 0], decision)
    _plot_scope_counts(axes[0, 1], decision)
    _plot_support_scatter(axes[1, 0], decision)
    _plot_statement(axes[1, 1], summary)
    fig.text(
        0.5,
        0.012,
        (
            "All values come from deterministic H1 artifacts. Robust bounded yes "
            "does not imply a broad many-elections or all-scope Polymarket claim."
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
    decision: pd.DataFrame,
    summary: pd.DataFrame,
    frontier_input: Path,
    frontier_summary_input: Path,
    direct_poll_state_cluster_input: Path,
    two_seventy_poll_average_input: Path,
    state_source_consensus_input: Path,
    calibration_pairwise_input: Path,
    decision_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the H1 poll decision matrix."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_poll_decision_matrix",
            "calculation_scope": "deterministic_python_from_precomputed_h1_artifacts",
            "does_not_recompute_brier_from_raw_rows": True,
            "uses_raw_poll_shares_directly": False,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
        },
        "outputs": {
            "decision_row_count": int(len(decision)),
            "summary_row_count": int(len(summary)),
            "robust_bounded_yes_count": int(
                (decision["decision_status"] == ROBUST_STATUS).sum()
            ),
            "counterexample_count": int(
                (decision["decision_status"] == COUNTER_STATUS).sum()
            ),
            "bounded_poll_claim_ready": bool(
                _summary_value(summary, "bounded_poll_claim_ready")
            ),
            "broad_claim_proven": bool(_summary_value(summary, "broad_claim_proven")),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "frontier_input": str(frontier_input),
            "frontier_summary_input": str(frontier_summary_input),
            "direct_poll_state_cluster_input": str(direct_poll_state_cluster_input),
            "two_seventy_poll_average_input": str(two_seventy_poll_average_input),
            "state_source_consensus_input": str(state_source_consensus_input),
            "calibration_pairwise_input": str(calibration_pairwise_input),
            "decision": str(decision_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "rows_repeat_resolved_state_outcomes": True,
            "state_month_units_are_not_independent_elections": True,
            "direct_poll_probabilities_are_transformed_from_polling_margins": True,
            "calibration_row_is_not_poll_only": True,
            "full_panel_still_contradicts_broad_claim": True,
            "goal_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _frontier_decision_row(
    *,
    row: pd.Series,
    decision_id: str,
    decision_label: str,
    status: str,
    allowed_claim: str,
) -> dict[str, Any]:
    case_count = int(row["row_count"])
    pm_count = int(row["polymarket_lower_loss_count"])
    comparator_count = int(row["poll_derived_lower_loss_count"])
    tie_count = int(row["tie_count"])
    unit_count = int(row["state_month_unit_count"])
    pm_units = int(row["state_month_polymarket_support_count"])
    comparator_units = int(row["state_month_poll_support_count"])
    p_value = float(row["state_month_exact_p_value"])
    mean_loss_advantage = float(row["mean_loss_advantage"])
    mean_support = mean_loss_advantage > 0
    case_majority = pm_count > comparator_count and pm_count > case_count / 2
    unit_support = pm_units > comparator_units and pm_units > unit_count / 2
    return {
        "decision_id": decision_id,
        "decision_label": decision_label,
        "evidence_family": "poll_scope_frontier",
        "scope": str(row["scope_id"]),
        "comparison_unit": "state_date_rows_and_state_month_units",
        "case_count": case_count,
        "polymarket_support_count": pm_count,
        "comparator_support_count": comparator_count,
        "tie_count": tie_count,
        "polymarket_support_share": pm_count / case_count,
        "mean_loss_advantage": mean_loss_advantage,
        "unit_count": unit_count,
        "polymarket_unit_support_count": pm_units,
        "comparator_unit_support_count": comparator_units,
        "p_value": p_value,
        "mean_supports_polymarket": mean_support,
        "case_majority_supports_polymarket": case_majority,
        "unit_supports_polymarket": unit_support,
        "broad_claim_supported": False,
        "decision_status": status,
        "allowed_claim": allowed_claim,
        "limitation": (
            "Repeated state-date forecasts and state-month units from one "
            "election context, not independent many-election proof."
        ),
    }


def _summary_decision_row(
    *,
    decision_id: str,
    decision_label: str,
    evidence_family: str,
    scope: str,
    comparison_unit: str,
    case_count: int,
    pm_support: int,
    comparator_support: int,
    ties: int,
    mean_loss_advantage: float,
    unit_count: int,
    pm_units: int,
    comparator_units: int,
    p_value: float,
    status: str,
    allowed_claim: str,
    limitation: str,
    broad_claim_supported: bool = False,
) -> dict[str, Any]:
    mean_support = bool(pd.notna(mean_loss_advantage) and mean_loss_advantage > 0)
    case_majority = pm_support > comparator_support and pm_support > case_count / 2
    unit_support = pm_units > comparator_units and pm_units > unit_count / 2
    return {
        "decision_id": decision_id,
        "decision_label": decision_label,
        "evidence_family": evidence_family,
        "scope": scope,
        "comparison_unit": comparison_unit,
        "case_count": int(case_count),
        "polymarket_support_count": int(pm_support),
        "comparator_support_count": int(comparator_support),
        "tie_count": int(ties),
        "polymarket_support_share": pm_support / case_count,
        "mean_loss_advantage": mean_loss_advantage,
        "unit_count": int(unit_count),
        "polymarket_unit_support_count": int(pm_units),
        "comparator_unit_support_count": int(comparator_units),
        "p_value": p_value,
        "mean_supports_polymarket": mean_support,
        "case_majority_supports_polymarket": case_majority,
        "unit_supports_polymarket": unit_support,
        "broad_claim_supported": bool(broad_claim_supported),
        "decision_status": status,
        "allowed_claim": allowed_claim,
        "limitation": limitation,
    }


def _plot_status_matrix(ax: plt.Axes, decision: pd.DataFrame) -> None:
    plot_rows = decision.loc[
        decision["decision_id"]
        != "calibration_resolved_case_sets"
    ].reset_index(drop=True)
    columns = [
        "mean_supports_polymarket",
        "case_majority_supports_polymarket",
        "unit_supports_polymarket",
        "broad_claim_supported",
    ]
    matrix = plot_rows[columns].astype(int).to_numpy()
    ax.imshow(
        matrix,
        aspect="auto",
        cmap=ListedColormap(["#fee2e2", "#bbf7d0"]),
        vmin=0,
        vmax=1,
    )
    ax.set_title("Decision checks by poll evidence row")
    ax.set_yticks(
        range(len(plot_rows)),
        [_wrap_label(label, 26) for label in plot_rows["decision_label"]],
        fontsize=8,
    )
    ax.set_xticks(
        range(len(columns)),
        ["Mean\nsupports PM", "Case\nmajority", "Unit\nmajority", "Broad\nclaim"],
        fontsize=8,
    )
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            ax.text(
                col_idx,
                row_idx,
                "yes" if matrix[row_idx, col_idx] else "no",
                ha="center",
                va="center",
                fontsize=8,
                color="#111827",
            )


def _plot_scope_counts(ax: plt.Axes, decision: pd.DataFrame) -> None:
    selected_ids = [
        "largest_robust_poll_scope",
        "strongest_robust_poll_scope",
        "lte_90_all_distances_boundary",
        "full_poll_panel_counterexample",
    ]
    rows = (
        decision.set_index("decision_id")
        .loc[selected_ids]
        .reset_index(drop=False)
    )
    labels = [_wrap_label(label, 24) for label in rows["decision_label"]]
    y_positions = np.arange(len(rows))
    case_count = rows["case_count"].to_numpy()
    pm_count = rows["polymarket_support_count"].to_numpy()
    comparator_count = rows["comparator_support_count"].to_numpy()
    ax.barh(y_positions, pm_count, color="#2563eb", label="Polymarket lower")
    ax.barh(
        y_positions,
        comparator_count,
        left=pm_count,
        color="#7c3aed",
        alpha=0.78,
        label="Poll-derived lower",
    )
    ax.set_yticks(y_positions, labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("State-date rows")
    ax.set_title("Poll-scope lower-loss counts")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")
    for idx, row in rows.iterrows():
        ax.text(
            int(row["case_count"]) * 1.01,
            idx,
            (
                f"PM {int(row['polymarket_support_count'])}/"
                f"{int(row['case_count'])}"
            ),
            va="center",
            fontsize=8,
            color="#374151",
        )
    ax.set_xlim(0, max(case_count) * 1.22)


def _plot_support_scatter(ax: plt.Axes, decision: pd.DataFrame) -> None:
    plot_rows = decision.loc[
        decision["mean_loss_advantage"].notna()
        & (decision["decision_id"] != "calibration_resolved_case_sets")
    ].copy()
    status_colors = {
        ROBUST_STATUS: "#2563eb",
        BOUNDARY_STATUS: "#f59e0b",
        MIXED_STATUS: "#64748b",
        COUNTER_STATUS: "#dc2626",
    }
    for status, rows in plot_rows.groupby("decision_status", sort=False):
        ax.scatter(
            rows["polymarket_support_share"],
            rows["mean_loss_advantage"],
            s=np.sqrt(rows["case_count"]) * 48,
            color=status_colors.get(status, "#111827"),
            alpha=0.78,
            edgecolor="#111827",
            linewidth=0.45,
            label=status.replace("_", " "),
        )
    ax.axvline(0.5, color="#6b7280", linestyle="--", linewidth=1.0)
    ax.axhline(0, color="#6b7280", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Polymarket lower-loss share")
    ax.set_ylabel("Mean loss advantage")
    ax.set_title("Mean Brier support vs case support")
    ax.grid(True, alpha=0.25)
    x_min = max(0.12, float(plot_rows["polymarket_support_share"].min()) - 0.08)
    x_max = min(1.0, float(plot_rows["polymarket_support_share"].max()) + 0.08)
    y_min = float(plot_rows["mean_loss_advantage"].min())
    y_max = float(plot_rows["mean_loss_advantage"].max())
    y_margin = max(0.025, (y_max - y_min) * 0.28)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min - y_margin, y_max + y_margin)
    ax.legend(fontsize=7.5, loc="lower right")
    offsets = {
        "largest_robust_poll_scope": (12, -16, "left"),
        "strongest_robust_poll_scope": (8, 10, "left"),
        "lte_90_all_distances_boundary": (-8, 13, "right"),
        "full_poll_panel_counterexample": (8, 8, "left"),
        "direct_poll_equal_state_mean": (-12, 16, "right"),
        "two_seventy_poll_average_states": (8, 9, "left"),
        "all_source_state_consensus": (-12, -15, "right"),
    }
    for _, row in plot_rows.iterrows():
        xytext_x, xytext_y, ha = offsets.get(
            str(row["decision_id"]),
            (8, 8, "left"),
        )
        ax.annotate(
            _short_decision_label(str(row["decision_id"])),
            (row["polymarket_support_share"], row["mean_loss_advantage"]),
            xytext=(xytext_x, xytext_y),
            textcoords="offset points",
            ha=ha,
            fontsize=7.5,
        )


def _plot_statement(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "Decision result\n"
        f"- Robust bounded yes rows: {_int_summary(summary, 'robust_bounded_yes_count')}.\n"
        f"- Largest robust scope: PM "
        f"{_int_summary(summary, 'largest_robust_polymarket_support_count')}/"
        f"{_int_summary(summary, 'largest_robust_row_count')} rows "
        f"({_summary_value(summary, 'largest_robust_polymarket_support_share') * 100:.1f}%).\n"
        f"- State-month support: "
        f"{_int_summary(summary, 'largest_robust_state_month_polymarket_support_count')}/"
        f"{_int_summary(summary, 'largest_robust_state_month_count')}, "
        f"p={_summary_value(summary, 'largest_robust_p_value'):.4f}.\n"
        f"- Strongest robust scope: "
        f"{_int_summary(summary, 'strongest_robust_polymarket_support_count')}/"
        f"{_int_summary(summary, 'strongest_robust_row_count')} rows, "
        f"p={_summary_value(summary, 'strongest_robust_p_value'):.2g}.\n\n"
        "Calibration context\n"
        f"- Mean Brier supports PM in "
        f"{_int_summary(summary, 'calibration_aggregate_support_count')}/"
        f"{_int_summary(summary, 'calibration_pairwise_count')} pairwise rows.\n"
        f"- Case majority supports PM in "
        f"{_int_summary(summary, 'calibration_majority_support_count')}/"
        f"{_int_summary(summary, 'calibration_pairwise_count')} pairwise rows.\n\n"
        "Boundary\n"
        f"- Full panel poll-derived lower loss: "
        f"{_int_summary(summary, 'full_panel_poll_support_count')}/"
        f"{_int_summary(summary, 'full_panel_row_count')} rows.\n"
        "Status: bounded poll claim ready; broad claim not_proven."
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


def _frontier_scope(frontier: pd.DataFrame, scope_id: str) -> pd.Series:
    rows = frontier.loc[frontier["scope_id"] == scope_id]
    if len(rows) != 1:
        raise ValueError(f"frontier scope not found: {scope_id}")
    return rows.iloc[0]


def _decision_row(decision: pd.DataFrame, decision_id: str) -> pd.Series:
    rows = decision.loc[decision["decision_id"] == decision_id]
    if len(rows) != 1:
        raise ValueError(f"decision row not found: {decision_id}")
    return rows.iloc[0]


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


def _summary_value(frame: pd.DataFrame, summary_id: str) -> float:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def _int_summary(frame: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(frame, summary_id))


def _bool_count(frame: pd.DataFrame, column: str) -> int:
    return int(frame[column].astype(str).str.lower().isin({"true", "1"}).sum())


def _wrap_label(label: str, width: int) -> str:
    return "\n".join(textwrap.wrap(label, width=width, break_long_words=False))


def _short_decision_label(decision_id: str) -> str:
    labels = {
        "largest_robust_poll_scope": "largest robust",
        "strongest_robust_poll_scope": "strongest robust",
        "lte_90_all_distances_boundary": "<=90 all",
        "full_poll_panel_counterexample": "full panel",
        "direct_poll_equal_state_mean": "direct state mean",
        "two_seventy_poll_average_states": "270 poll",
        "all_source_state_consensus": "all-source",
    }
    return labels.get(decision_id, decision_id)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-input", type=Path, default=FRONTIER_INPUT)
    parser.add_argument(
        "--frontier-summary-input",
        type=Path,
        default=FRONTIER_SUMMARY_INPUT,
    )
    parser.add_argument(
        "--direct-poll-state-cluster-input",
        type=Path,
        default=DIRECT_POLL_STATE_CLUSTER_INPUT,
    )
    parser.add_argument(
        "--two-seventy-poll-average-input",
        type=Path,
        default=TWO_SEVENTY_POLL_AVERAGE_INPUT,
    )
    parser.add_argument(
        "--state-source-consensus-input",
        type=Path,
        default=STATE_SOURCE_CONSENSUS_INPUT,
    )
    parser.add_argument(
        "--calibration-pairwise-input",
        type=Path,
        default=CALIBRATION_PAIRWISE_INPUT,
    )
    parser.add_argument("--decision-output", type=Path, default=DECISION_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_poll_decision_matrix_outputs(
            frontier_input=args.frontier_input,
            frontier_summary_input=args.frontier_summary_input,
            direct_poll_state_cluster_input=args.direct_poll_state_cluster_input,
            two_seventy_poll_average_input=args.two_seventy_poll_average_input,
            state_source_consensus_input=args.state_source_consensus_input,
            calibration_pairwise_input=args.calibration_pairwise_input,
            decision_output=args.decision_output,
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
