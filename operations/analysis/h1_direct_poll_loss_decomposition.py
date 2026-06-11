"""Decompose direct H1 poll-transform loss advantages.

The H1 state-source consensus shows a subtle result: direct poll-transform
comparators win more state-source cases, but Polymarket has lower aggregate
mean Brier because its winning cases carry larger loss advantages. This module
turns that into an explicit deterministic artifact and keeps the late
poll-panel support visible as a bounded statement.
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

from operations.analysis.h1_state_source_consensus import DIRECT_POLL_FAMILY
from operations.analysis.run_h2_event_windows import RESULTS_DIR


CONSENSUS_INPUT = RESULTS_DIR / "h1_state_source_consensus_cases.csv"
UNIT_ROBUSTNESS_SUMMARY_INPUT = (
    RESULTS_DIR / "h1_poll_comparison_unit_robustness_summary.csv"
)
CASES_OUTPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition_cases.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition_metadata.json"

CASE_COLUMNS: tuple[str, ...] = (
    "source_id",
    "source_label",
    "state",
    "case_id",
    "outcome_value",
    "polymarket_probability",
    "comparator_probability",
    "polymarket_brier",
    "comparator_brier",
    "loss_advantage",
    "absolute_loss_advantage",
    "lower_loss_source",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

FORBIDDEN_COLUMN_TOKENS: tuple[str, ...] = (
    "wallet",
    "maker",
    "taker",
    "address",
    "order_instruction",
)


@dataclass(frozen=True)
class H1DirectPollLossDecompositionResult:
    """Summary of generated direct poll loss-decomposition artifacts."""

    cases_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    direct_poll_case_count: int
    polymarket_lower_loss_count: int
    comparator_lower_loss_count: int
    aggregate_mean_supports_polymarket: bool
    case_majority_supports_polymarket: bool

    def to_dict(self) -> dict[str, bool | int | str]:
        return {
            "cases_path": str(self.cases_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "direct_poll_case_count": self.direct_poll_case_count,
            "polymarket_lower_loss_count": self.polymarket_lower_loss_count,
            "comparator_lower_loss_count": self.comparator_lower_loss_count,
            "aggregate_mean_supports_polymarket": (
                self.aggregate_mean_supports_polymarket
            ),
            "case_majority_supports_polymarket": (
                self.case_majority_supports_polymarket
            ),
        }


def generate_h1_direct_poll_loss_decomposition_outputs(
    *,
    consensus_input: Path = CONSENSUS_INPUT,
    unit_robustness_summary_input: Path = UNIT_ROBUSTNESS_SUMMARY_INPUT,
    cases_output: Path = CASES_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1DirectPollLossDecompositionResult:
    """Generate direct-poll loss decomposition CSVs, figure, and metadata."""

    cases = validate_direct_poll_cases(read_direct_poll_cases(consensus_input))
    unit_summary = read_optional_unit_summary(unit_robustness_summary_input)
    summary = validate_summary(build_summary(cases, unit_summary))

    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_loss_decomposition_figure(
        cases=cases,
        summary=summary,
        output_path=figure_output,
    )
    metadata = build_metadata(
        cases=cases,
        summary=summary,
        consensus_input=consensus_input,
        unit_robustness_summary_input=unit_robustness_summary_input,
        cases_output=cases_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1DirectPollLossDecompositionResult(
        cases_path=cases_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        direct_poll_case_count=int(_summary_value(summary, "direct_poll_case_count")),
        polymarket_lower_loss_count=int(
            _summary_value(summary, "direct_poll_polymarket_lower_loss_count")
        ),
        comparator_lower_loss_count=int(
            _summary_value(summary, "direct_poll_comparator_lower_loss_count")
        ),
        aggregate_mean_supports_polymarket=bool(
            _summary_value(summary, "direct_poll_aggregate_mean_supports_polymarket")
        ),
        case_majority_supports_polymarket=bool(
            _summary_value(summary, "direct_poll_case_majority_supports_polymarket")
        ),
    )


def read_direct_poll_cases(path: Path) -> pd.DataFrame:
    """Read direct poll-transform rows from the state-source consensus cases."""

    if not path.exists():
        raise FileNotFoundError(f"H1 state-source consensus cases not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "source_id",
        "source_label",
        "source_family",
        "state",
        "case_id",
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
        "lower_loss_source",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 state-source consensus cases missing columns: {missing}")
    _reject_forbidden_columns(frame, "H1 direct poll consensus input")

    direct = frame.loc[frame["source_family"] == DIRECT_POLL_FAMILY].copy()
    if direct.empty:
        raise ValueError("H1 state-source consensus cases contain no direct poll rows")
    for column in (
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
    ):
        direct[column] = pd.to_numeric(direct[column], errors="raise")
    direct["absolute_loss_advantage"] = direct["loss_advantage"].abs()
    direct["allowed_interpretation"] = (
        "Direct poll-transform loss-decomposition diagnostic for H1 forecast quality."
    )
    direct["limitation"] = (
        "Rows reuse 2024 US presidential state outcomes and direct poll "
        "transform artifacts; they are not independent elections."
    )
    return direct.loc[:, list(CASE_COLUMNS)].sort_values(
        ["source_id", "state"]
    ).reset_index(drop=True)


def read_optional_unit_summary(path: Path) -> pd.DataFrame:
    """Read unit robustness summary when available for bounded-scope context."""

    if not path.exists():
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    frame = pd.read_csv(path)
    missing = [column for column in SUMMARY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"unit robustness summary missing columns: {missing}")
    return frame.loc[:, list(SUMMARY_COLUMNS)].copy()


def validate_direct_poll_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate direct poll-transform case rows."""

    _require_columns(frame, CASE_COLUMNS, "H1 direct poll loss cases")
    _reject_forbidden_columns(frame, "H1 direct poll loss cases")
    validated = frame.loc[:, list(CASE_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll loss cases must not be empty")
    for column in (
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
        "absolute_loss_advantage",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    for column in ("outcome_value", "polymarket_probability", "comparator_probability"):
        if not validated[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if (validated["polymarket_brier"] < 0).any() or (
        validated["comparator_brier"] < 0
    ).any():
        raise ValueError("Brier values must be non-negative")
    if not set(validated["lower_loss_source"]).issubset({"polymarket", "comparator", "tie"}):
        raise ValueError("lower_loss_source contains unknown values")
    if validated.duplicated(["source_id", "state"]).any():
        raise ValueError("Each direct source/state pair must appear at most once")
    return validated.sort_values(["source_id", "state"]).reset_index(drop=True)


def build_summary(
    cases: pd.DataFrame,
    unit_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact decomposition summary rows."""

    pm_wins = cases.loc[cases["lower_loss_source"] == "polymarket"]
    comparator_wins = cases.loc[cases["lower_loss_source"] == "comparator"]
    ties = cases.loc[cases["lower_loss_source"] == "tie"]
    pm_win_total = float(pm_wins["loss_advantage"].sum())
    comparator_win_total_abs = float(-comparator_wins["loss_advantage"].sum())
    advantage_ratio = (
        pm_win_total / comparator_win_total_abs
        if comparator_win_total_abs > 0
        else float("inf")
    )
    pm_lower = int(len(pm_wins))
    comparator_lower = int(len(comparator_wins))
    rows = [
        _summary_row(
            "direct_poll_case_count",
            int(len(cases)),
            "source-state cases",
            "Direct poll-transform source-state cases.",
        ),
        _summary_row(
            "direct_poll_polymarket_lower_loss_count",
            pm_lower,
            "source-state cases",
            "Direct poll-transform cases where Polymarket has lower Brier loss.",
        ),
        _summary_row(
            "direct_poll_comparator_lower_loss_count",
            comparator_lower,
            "source-state cases",
            "Direct poll-transform cases where the poll-derived comparator has lower Brier loss.",
        ),
        _summary_row(
            "direct_poll_tie_count",
            int(len(ties)),
            "source-state cases",
            "Direct poll-transform cases with equal Brier loss.",
        ),
        _summary_row(
            "direct_poll_polymarket_lower_loss_share",
            pm_lower / len(cases),
            "share",
            "Share of direct poll-transform cases won by Polymarket.",
        ),
        _summary_row(
            "direct_poll_mean_polymarket_brier",
            float(cases["polymarket_brier"].mean()),
            "brier_score",
            "Mean Polymarket Brier across direct poll-transform cases.",
        ),
        _summary_row(
            "direct_poll_mean_poll_derived_brier",
            float(cases["comparator_brier"].mean()),
            "brier_score",
            "Mean poll-derived comparator Brier across direct poll-transform cases.",
        ),
        _summary_row(
            "direct_poll_mean_loss_advantage",
            float(cases["loss_advantage"].mean()),
            "brier_score",
            "Mean comparator Brier minus Polymarket Brier; positive supports Polymarket.",
        ),
        _summary_row(
            "polymarket_win_total_loss_advantage",
            pm_win_total,
            "brier_score_sum",
            "Total positive loss advantage from cases won by Polymarket.",
        ),
        _summary_row(
            "comparator_win_total_loss_advantage_abs",
            comparator_win_total_abs,
            "brier_score_sum",
            "Total absolute negative loss advantage from cases won by poll-derived comparators.",
        ),
        _summary_row(
            "polymarket_win_mean_loss_advantage",
            float(pm_wins["loss_advantage"].mean()) if not pm_wins.empty else 0.0,
            "brier_score",
            "Mean positive loss advantage in Polymarket-winning direct poll cases.",
        ),
        _summary_row(
            "comparator_win_mean_loss_advantage_abs",
            float(-comparator_wins["loss_advantage"].mean())
            if not comparator_wins.empty
            else 0.0,
            "brier_score",
            "Mean absolute loss advantage in comparator-winning direct poll cases.",
        ),
        _summary_row(
            "polymarket_win_total_to_comparator_win_abs_ratio",
            advantage_ratio,
            "ratio",
            "Ratio of total Polymarket-winning advantage to total comparator-winning advantage.",
        ),
        _summary_row(
            "direct_poll_aggregate_mean_supports_polymarket",
            int(cases["polymarket_brier"].mean() < cases["comparator_brier"].mean()),
            "binary",
            "Whether aggregate mean Brier is lower for Polymarket.",
        ),
        _summary_row(
            "direct_poll_case_majority_supports_polymarket",
            int(pm_lower > comparator_lower),
            "binary",
            "Whether Polymarket wins a majority of direct poll-transform cases.",
        ),
        _summary_row(
            "broad_many_cases_claim_proven",
            0,
            "binary",
            "This decomposition does not prove the requested broad many-cases claim.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Direct poll aggregate loss supports Polymarket, but case-majority and broad-scope proof remain incomplete.",
        ),
    ]
    rows.extend(_bounded_unit_rows(unit_summary))
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact decomposition summary."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 direct poll loss summary")
    _reject_forbidden_columns(frame, "H1 direct poll loss summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll loss summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return validated


def write_loss_decomposition_figure(
    *,
    cases: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a thesis-facing direct poll loss decomposition figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.4, 9.8))
    fig.suptitle(
        "H1 direct poll comparison: aggregate loss vs case-count majority",
        fontsize=14,
        fontweight="bold",
    )

    _plot_mean_brier_and_counts(axes[0, 0], summary)
    _plot_loss_mass_decomposition(axes[0, 1], summary)
    _plot_largest_case_margins(axes[1, 0], cases)
    _plot_statement_box(axes[1, 1], summary)

    fig.text(
        0.5,
        0.012,
        (
            "Direct poll-transform rows come from existing deterministic H1 state artifacts. "
            "Positive loss advantage means poll-derived Brier minus Polymarket Brier."
        ),
        ha="center",
        fontsize=8.7,
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
    summary: pd.DataFrame,
    consensus_input: Path,
    unit_robustness_summary_input: Path,
    cases_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for direct poll loss decomposition."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_direct_poll_loss_decomposition",
            "calculation_scope": "deterministic_python_from_existing_h1_artifacts",
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
            "direct_poll_case_count": int(
                _summary_value(summary, "direct_poll_case_count")
            ),
            "direct_poll_polymarket_lower_loss_count": int(
                _summary_value(summary, "direct_poll_polymarket_lower_loss_count")
            ),
            "direct_poll_comparator_lower_loss_count": int(
                _summary_value(summary, "direct_poll_comparator_lower_loss_count")
            ),
            "direct_poll_aggregate_mean_supports_polymarket": bool(
                _summary_value(
                    summary,
                    "direct_poll_aggregate_mean_supports_polymarket",
                )
            ),
            "direct_poll_case_majority_supports_polymarket": bool(
                _summary_value(
                    summary,
                    "direct_poll_case_majority_supports_polymarket",
                )
            ),
            "broad_many_cases_claim_proven": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {
            "consensus_input": str(consensus_input),
            "unit_robustness_summary_input": str(unit_robustness_summary_input),
            "cases": str(cases_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "source_ids": sorted(cases["source_id"].unique().tolist()),
        "limitations": {
            "uses_existing_h1_state_source_consensus": True,
            "direct_poll_rows_are_not_independent_elections": True,
            "all_rows_share_one_presidential_election_context": True,
            "case_majority_does_not_support_polymarket": bool(
                not _summary_value(
                    summary,
                    "direct_poll_case_majority_supports_polymarket",
                )
            ),
            "no_causal_or_tradeability_claim": True,
            "goal_many_cases_claim_not_yet_proven": True,
        },
    }


def _bounded_unit_rows(unit_summary: pd.DataFrame) -> list[dict[str, Any]]:
    if unit_summary.empty:
        return []
    wanted = {
        "primary_row_count": "Bounded <=90-day low/middle poll-distance row count.",
        "primary_polymarket_lower_loss_count": "Bounded rows won by Polymarket.",
        "primary_state_month_unit_count": "Bounded state-month diagnostic unit count.",
        "primary_state_month_polymarket_support_count": (
            "Bounded state-month units supporting Polymarket."
        ),
        "primary_state_month_polymarket_exact_binomial_p_value_greater": (
            "One-sided exact p-value for bounded state-month Polymarket support."
        ),
        "primary_state_month_polymarket_exact_95_ci_low": (
            "Exact 95 percent lower confidence bound for bounded state-month support."
        ),
    }
    rows: list[dict[str, Any]] = []
    for summary_id, description in wanted.items():
        value = _optional_summary_value(unit_summary, summary_id)
        if value is None:
            continue
        unit = str(
            unit_summary.loc[unit_summary["summary_id"] == summary_id, "unit"].iloc[0]
        )
        rows.append(_summary_row(f"bounded_{summary_id}", value, unit, description))
    return rows


def _plot_mean_brier_and_counts(ax: plt.Axes, summary: pd.DataFrame) -> None:
    mean_pm = _summary_value(summary, "direct_poll_mean_polymarket_brier")
    mean_poll = _summary_value(summary, "direct_poll_mean_poll_derived_brier")
    pm_count = int(_summary_value(summary, "direct_poll_polymarket_lower_loss_count"))
    poll_count = int(_summary_value(summary, "direct_poll_comparator_lower_loss_count"))
    total = int(_summary_value(summary, "direct_poll_case_count"))
    x = [0, 1, 3, 4]
    values = [mean_pm, mean_poll, pm_count / total, poll_count / total]
    labels = ["PM\nmean Brier", "Poll\nmean Brier", "PM\ncase share", "Poll\ncase share"]
    colors = ["#2563eb", "#7c3aed", "#2563eb", "#7c3aed"]
    bars = ax.bar(x, values, color=colors, alpha=0.84)
    ax.set_title("Mean loss supports PM; case majority does not")
    ax.set_ylim(0, max(values) * 1.32)
    ax.set_xticks(x, labels)
    ax.grid(True, axis="y", alpha=0.24)
    for idx, bar in enumerate(bars):
        if idx < 2:
            text = f"{bar.get_height():.4f}"
        else:
            count = pm_count if idx == 2 else poll_count
            text = f"{count}/{total}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.035,
            text,
            ha="center",
            fontsize=9,
        )


def _plot_loss_mass_decomposition(ax: plt.Axes, summary: pd.DataFrame) -> None:
    pm_total = _summary_value(summary, "polymarket_win_total_loss_advantage")
    poll_total = _summary_value(summary, "comparator_win_total_loss_advantage_abs")
    pm_mean = _summary_value(summary, "polymarket_win_mean_loss_advantage")
    poll_mean = _summary_value(summary, "comparator_win_mean_loss_advantage_abs")
    labels = ["Total PM\nwinning margin", "Total poll\nwinning margin"]
    values = [pm_total, poll_total]
    bars = ax.bar(labels, values, color=["#2563eb", "#7c3aed"], alpha=0.84)
    ax.set_ylabel("Absolute summed Brier advantage")
    ax.set_title("Why aggregate Brier still favours PM")
    ax.grid(True, axis="y", alpha=0.24)
    ax.set_ylim(0, max(values) * 1.22)
    for bar, value, mean_value in zip(bars, values, (pm_mean, poll_mean)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + max(values) * 0.035,
            f"sum {value:.3f}\navg {mean_value:.4f}",
            ha="center",
            fontsize=9,
        )


def _plot_largest_case_margins(ax: plt.Axes, cases: pd.DataFrame) -> None:
    extremes = pd.concat(
        [
            cases.nsmallest(5, "loss_advantage"),
            cases.nlargest(7, "loss_advantage"),
        ],
        ignore_index=True,
    ).sort_values("loss_advantage")
    labels = [
        f"{row.state[:13]} ({row.source_label.split()[0]})"
        for row in extremes.itertuples(index=False)
    ]
    colors = [
        "#2563eb" if value > 0 else "#7c3aed"
        for value in extremes["loss_advantage"].tolist()
    ]
    ax.barh(labels, extremes["loss_advantage"], color=colors, alpha=0.84)
    ax.axvline(0.0, color="#111827", linewidth=0.9)
    ax.set_title("Largest direct poll loss-advantage cases")
    ax.set_xlabel("Poll Brier minus PM Brier")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, axis="x", alpha=0.22)


def _plot_statement_box(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    summary_ids = set(summary["summary_id"].astype(str))
    if "bounded_primary_row_count" in summary_ids:
        bounded_text = (
            "Bounded late poll-panel context\n"
            f"- PM rows: {_int_summary(summary, 'bounded_primary_polymarket_lower_loss_count')} "
            f"of {_int_summary(summary, 'bounded_primary_row_count')}.\n"
            f"- State-month units: "
            f"{_int_summary(summary, 'bounded_primary_state_month_polymarket_support_count')} "
            f"of {_int_summary(summary, 'bounded_primary_state_month_unit_count')}; "
            f"p={_summary_value(summary, 'bounded_primary_state_month_polymarket_exact_binomial_p_value_greater'):.2g}.\n\n"
        )
    else:
        bounded_text = "Bounded late poll-panel context\n- Unit summary not available.\n\n"
    text = (
        "Direct poll-transform result\n"
        f"- Mean Brier: PM {_summary_value(summary, 'direct_poll_mean_polymarket_brier'):.4f} "
        f"vs poll-derived {_summary_value(summary, 'direct_poll_mean_poll_derived_brier'):.4f}.\n"
        f"- Lower-loss cases: PM {_int_summary(summary, 'direct_poll_polymarket_lower_loss_count')} "
        f"of {_int_summary(summary, 'direct_poll_case_count')}; poll-derived "
        f"{_int_summary(summary, 'direct_poll_comparator_lower_loss_count')}.\n"
        f"- PM-winning mean advantage: "
        f"{_summary_value(summary, 'polymarket_win_mean_loss_advantage'):.4f}; "
        f"poll-winning mean advantage: "
        f"{_summary_value(summary, 'comparator_win_mean_loss_advantage_abs'):.4f}.\n"
        f"- Total margin ratio PM/poll: "
        f"{_summary_value(summary, 'polymarket_win_total_to_comparator_win_abs_ratio'):.1f}.\n\n"
        f"{bounded_text}"
        "Boundary\n"
        "- Aggregate loss supports PM in direct poll rows.\n"
        "- Direct case majority and broad many-cases claim remain unproven."
    )
    ax.text(
        0.02,
        0.96,
        text,
        va="top",
        fontsize=10.4,
        color="#1f2937",
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#f8fafc",
            "edgecolor": "#cbd5e1",
        },
    )


def _summary_row(
    summary_id: str,
    value: int | float | str,
    unit: str,
    description: str,
) -> dict[str, int | float | str]:
    return {
        "summary_id": summary_id,
        "value": value,
        "unit": unit,
        "description": description,
    }


def _summary_value(summary: pd.DataFrame, summary_id: str) -> float:
    rows = summary.loc[summary["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def _optional_summary_value(summary: pd.DataFrame, summary_id: str) -> str | None:
    rows = summary.loc[summary["summary_id"] == summary_id, "value"]
    if rows.empty:
        return None
    return str(rows.iloc[0])


def _int_summary(summary: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(summary, summary_id))


def _require_columns(
    frame: pd.DataFrame,
    required: Sequence[str],
    label: str,
) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _reject_forbidden_columns(frame: pd.DataFrame, label: str) -> None:
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in FORBIDDEN_COLUMN_TOKENS)
    ]
    if forbidden:
        raise ValueError(f"{label} contains forbidden columns: {forbidden}")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consensus-input", type=Path, default=CONSENSUS_INPUT)
    parser.add_argument(
        "--unit-robustness-summary-input",
        type=Path,
        default=UNIT_ROBUSTNESS_SUMMARY_INPUT,
    )
    parser.add_argument("--cases-output", type=Path, default=CASES_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_direct_poll_loss_decomposition_outputs(
            consensus_input=args.consensus_input,
            unit_robustness_summary_input=args.unit_robustness_summary_input,
            cases_output=args.cases_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
