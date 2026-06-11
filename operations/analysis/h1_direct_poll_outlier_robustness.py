"""Outlier robustness for direct H1 poll state-cluster advantages.

This module tests whether the positive equal-state mean loss advantage from
the direct poll state-cluster diagnostic is driven by one or a few large
states. It uses only the existing state-cluster artifact and produces
deterministic leave-one-state-out and top-k exclusion diagnostics.
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


STATE_INPUT = RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_states.csv"
SCENARIO_OUTPUT = RESULTS_DIR / "h1_direct_poll_outlier_robustness_scenarios.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_direct_poll_outlier_robustness_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_direct_poll_outlier_robustness.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_direct_poll_outlier_robustness_metadata.json"

SCENARIO_COLUMNS: tuple[str, ...] = (
    "scenario_type",
    "scenario_id",
    "removed_state_count",
    "removed_states",
    "remaining_state_count",
    "mean_loss_advantage",
    "supports_polymarket_mean",
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
class H1DirectPollOutlierRobustnessResult:
    """Summary of generated outlier robustness artifacts."""

    scenario_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    state_count: int
    full_mean_loss_advantage: float
    min_leave_one_out_mean_loss_advantage: float
    max_top_positive_exclusion_k_with_positive_mean: int

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "scenario_path": str(self.scenario_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "state_count": self.state_count,
            "full_mean_loss_advantage": self.full_mean_loss_advantage,
            "min_leave_one_out_mean_loss_advantage": (
                self.min_leave_one_out_mean_loss_advantage
            ),
            "max_top_positive_exclusion_k_with_positive_mean": (
                self.max_top_positive_exclusion_k_with_positive_mean
            ),
        }


def generate_h1_direct_poll_outlier_robustness_outputs(
    *,
    state_input: Path = STATE_INPUT,
    scenario_output: Path = SCENARIO_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1DirectPollOutlierRobustnessResult:
    """Generate outlier robustness scenarios, summary, figure, and metadata."""

    states = read_state_clusters(state_input)
    scenarios = validate_scenarios(build_scenarios(states))
    summary = validate_summary(build_summary(states=states, scenarios=scenarios))

    scenario_output.parent.mkdir(parents=True, exist_ok=True)
    scenarios.to_csv(scenario_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_outlier_figure(states=states, scenarios=scenarios, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        states=states,
        scenarios=scenarios,
        summary=summary,
        state_input=state_input,
        scenario_output=scenario_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1DirectPollOutlierRobustnessResult(
        scenario_path=scenario_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        state_count=int(_summary_value(summary, "state_count")),
        full_mean_loss_advantage=float(
            _summary_value(summary, "full_mean_loss_advantage")
        ),
        min_leave_one_out_mean_loss_advantage=float(
            _summary_value(summary, "min_leave_one_out_mean_loss_advantage")
        ),
        max_top_positive_exclusion_k_with_positive_mean=int(
            _summary_value(summary, "max_top_positive_exclusion_k_with_positive_mean")
        ),
    )


def read_state_clusters(path: Path) -> pd.DataFrame:
    """Read direct poll state-cluster rows."""

    if not path.exists():
        raise FileNotFoundError(f"H1 direct poll state-cluster input not found: {path}")
    frame = pd.read_csv(path)
    required = {"state", "mean_loss_advantage"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 direct poll state-cluster input missing columns: {missing}")
    _reject_forbidden_columns(frame, "H1 direct poll outlier input")
    normalized = frame.copy()
    normalized["mean_loss_advantage"] = pd.to_numeric(
        normalized["mean_loss_advantage"],
        errors="raise",
    )
    if normalized["state"].astype(str).str.strip().eq("").any():
        raise ValueError("state values must not be blank")
    return normalized.sort_values("state").reset_index(drop=True)


def build_scenarios(states: pd.DataFrame) -> pd.DataFrame:
    """Build full, leave-one-out, and top-k exclusion scenarios."""

    if states.empty:
        raise ValueError("state cluster table must not be empty")
    rows: list[dict[str, Any]] = []
    rows.append(_scenario_row(states, scenario_type="full", scenario_id="all_states"))

    for state in states["state"].astype(str).tolist():
        remaining = states.loc[states["state"].astype(str) != state]
        rows.append(
            _scenario_row(
                remaining,
                scenario_type="leave_one_state_out",
                scenario_id=f"without_{_slug(state)}",
                removed_states=state,
            )
        )

    ordered_positive = states.loc[states["mean_loss_advantage"] > 0].sort_values(
        "mean_loss_advantage",
        ascending=False,
    )
    removed: list[str] = []
    for state in ordered_positive["state"].astype(str).tolist():
        removed.append(state)
        remaining = states.loc[~states["state"].astype(str).isin(removed)]
        rows.append(
            _scenario_row(
                remaining,
                scenario_type="drop_top_positive_states",
                scenario_id=f"drop_top_{len(removed)}",
                removed_states=";".join(removed),
            )
        )

    return pd.DataFrame(rows, columns=SCENARIO_COLUMNS)


def build_summary(
    *,
    states: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> pd.DataFrame:
    """Build compact outlier robustness summary."""

    full_mean = float(states["mean_loss_advantage"].mean())
    leave_one = scenarios.loc[scenarios["scenario_type"] == "leave_one_state_out"]
    top_drop = scenarios.loc[scenarios["scenario_type"] == "drop_top_positive_states"]
    positive_top = top_drop.loc[top_drop["supports_polymarket_mean"]]
    first_nonpositive = top_drop.loc[~top_drop["supports_polymarket_mean"]].head(1)
    strongest = states.sort_values("mean_loss_advantage", ascending=False).iloc[0]
    rows = [
        _summary_row(
            "state_count",
            int(len(states)),
            "states",
            "Direct poll state clusters included in the outlier diagnostic.",
        ),
        _summary_row(
            "full_mean_loss_advantage",
            full_mean,
            "brier_score",
            "Equal-state mean loss advantage across all direct poll state clusters.",
        ),
        _summary_row(
            "leave_one_out_scenario_count",
            int(len(leave_one)),
            "scenarios",
            "Number of leave-one-state-out scenarios.",
        ),
        _summary_row(
            "min_leave_one_out_mean_loss_advantage",
            float(leave_one["mean_loss_advantage"].min()),
            "brier_score",
            "Smallest equal-state mean after removing one state.",
        ),
        _summary_row(
            "leave_one_out_all_positive",
            int(bool(leave_one["supports_polymarket_mean"].all())),
            "binary",
            "Whether every leave-one-state-out mean remains positive.",
        ),
        _summary_row(
            "most_influential_removed_state",
            str(
                leave_one.sort_values("mean_loss_advantage").iloc[0]["removed_states"]
            ),
            "state",
            "Single removed state that yields the smallest remaining mean.",
        ),
        _summary_row(
            "max_top_positive_exclusion_k_with_positive_mean",
            int(positive_top["removed_state_count"].max()) if not positive_top.empty else 0,
            "states",
            "Largest number of top positive states removable while mean remains positive.",
        ),
        _summary_row(
            "first_nonpositive_top_positive_exclusion_k",
            int(first_nonpositive.iloc[0]["removed_state_count"])
            if not first_nonpositive.empty
            else 0,
            "states",
            "Smallest top-positive-state removal count where mean is not positive.",
        ),
        _summary_row(
            "first_nonpositive_top_positive_exclusion_mean",
            float(first_nonpositive.iloc[0]["mean_loss_advantage"])
            if not first_nonpositive.empty
            else float("nan"),
            "brier_score",
            "Mean after the first top-positive-state exclusion that is not positive.",
        ),
        _summary_row(
            "largest_positive_state",
            str(strongest["state"]),
            "state",
            "State with the largest positive Polymarket loss advantage.",
        ),
        _summary_row(
            "largest_positive_state_loss_advantage",
            float(strongest["mean_loss_advantage"]),
            "brier_score",
            "Largest state-level positive loss advantage.",
        ),
        _summary_row(
            "outlier_robustness_supports_polymarket_mean",
            int(full_mean > 0 and bool(leave_one["supports_polymarket_mean"].all())),
            "binary",
            "Whether the positive mean survives all one-state exclusions.",
        ),
        _summary_row(
            "broad_many_cases_claim_proven",
            0,
            "binary",
            "This outlier diagnostic does not prove the broad many-cases claim.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Mean advantage survives single-state exclusions, but the result is still concentrated in top positive states.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def validate_scenarios(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate scenario output."""

    _require_columns(frame, SCENARIO_COLUMNS, "H1 direct poll outlier scenarios")
    _reject_forbidden_columns(frame, "H1 direct poll outlier scenarios")
    validated = frame.loc[:, list(SCENARIO_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll outlier scenarios must not be empty")
    for column in ("removed_state_count", "remaining_state_count"):
        validated[column] = pd.to_numeric(validated[column], errors="raise").astype(int)
    validated["mean_loss_advantage"] = pd.to_numeric(
        validated["mean_loss_advantage"],
        errors="raise",
    )
    return validated


def validate_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate compact summary table."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 direct poll outlier summary")
    _reject_forbidden_columns(frame, "H1 direct poll outlier summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll outlier summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return validated


def write_outlier_figure(
    *,
    states: pd.DataFrame,
    scenarios: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write an outlier robustness figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.6, 9.6))
    fig.suptitle(
        "H1 direct poll comparison: outlier robustness",
        fontsize=14,
        fontweight="bold",
    )

    _plot_leave_one_out(axes[0, 0], scenarios, summary)
    _plot_top_k_exclusion(axes[0, 1], scenarios, summary)
    _plot_state_contributions(axes[1, 0], states)
    _plot_statement_box(axes[1, 1], summary)

    fig.text(
        0.5,
        0.012,
        (
            "Outlier checks use equal-weight direct poll state clusters. Positive "
            "loss advantage means poll-derived Brier minus Polymarket Brier."
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
    states: pd.DataFrame,
    scenarios: pd.DataFrame,
    summary: pd.DataFrame,
    state_input: Path,
    scenario_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for outlier robustness artifacts."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_direct_poll_outlier_robustness",
            "calculation_scope": "deterministic_python_from_h1_direct_poll_state_clusters",
            "state_clusters_equal_weighted": True,
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
            "state_count": int(_summary_value(summary, "state_count")),
            "scenario_count": int(len(scenarios)),
            "full_mean_loss_advantage": float(
                _summary_value(summary, "full_mean_loss_advantage")
            ),
            "min_leave_one_out_mean_loss_advantage": float(
                _summary_value(summary, "min_leave_one_out_mean_loss_advantage")
            ),
            "max_top_positive_exclusion_k_with_positive_mean": int(
                _summary_value(
                    summary,
                    "max_top_positive_exclusion_k_with_positive_mean",
                )
            ),
            "outlier_robustness_supports_polymarket_mean": bool(
                _summary_value(
                    summary,
                    "outlier_robustness_supports_polymarket_mean",
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
            "state_input": str(state_input),
            "scenarios": str(scenario_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "states_are_not_independent_elections": True,
            "all_rows_share_one_presidential_election_context": True,
            "single_state_outlier_check_is_not_new_data": True,
            "top_positive_exclusion_shows_concentration": True,
            "no_causal_or_tradeability_claim": True,
            "goal_many_cases_claim_not_yet_proven": True,
        },
    }


def _scenario_row(
    remaining: pd.DataFrame,
    *,
    scenario_type: str,
    scenario_id: str,
    removed_states: str = "",
) -> dict[str, Any]:
    removed_count = 0 if not removed_states else len(removed_states.split(";"))
    mean = float(remaining["mean_loss_advantage"].mean())
    return {
        "scenario_type": scenario_type,
        "scenario_id": scenario_id,
        "removed_state_count": removed_count,
        "removed_states": removed_states,
        "remaining_state_count": int(len(remaining)),
        "mean_loss_advantage": mean,
        "supports_polymarket_mean": bool(mean > 0.0),
        "allowed_interpretation": (
            "Outlier robustness diagnostic for equal-weight direct poll state clusters."
        ),
        "limitation": (
            "Scenario rows reuse the same 2024 election context and are not new independent outcomes."
        ),
    }


def _plot_leave_one_out(
    ax: plt.Axes,
    scenarios: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    leave_one = scenarios.loc[scenarios["scenario_type"] == "leave_one_state_out"].copy()
    leave_one = leave_one.sort_values("mean_loss_advantage")
    ax.plot(
        range(len(leave_one)),
        leave_one["mean_loss_advantage"],
        marker="o",
        markersize=3,
        linewidth=1.2,
        color="#2563eb",
    )
    ax.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    ax.axhline(
        _summary_value(summary, "full_mean_loss_advantage"),
        color="#7c3aed",
        linewidth=1.2,
        label="Full mean",
    )
    ax.set_title("Leave-one-state-out means")
    ax.set_ylabel("Mean loss advantage")
    ax.set_xlabel("Leave-one scenarios, sorted")
    ax.grid(True, axis="y", alpha=0.24)
    ax.legend(fontsize=8)
    min_row = leave_one.iloc[0]
    ax.annotate(
        f"min without {min_row['removed_states']}\n{float(min_row['mean_loss_advantage']):.4f}",
        xy=(0, float(min_row["mean_loss_advantage"])),
        xytext=(2, float(min_row["mean_loss_advantage"]) + 0.003),
        arrowprops={"arrowstyle": "->", "color": "#374151", "lw": 0.8},
        fontsize=8.3,
    )


def _plot_top_k_exclusion(
    ax: plt.Axes,
    scenarios: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    top_drop = scenarios.loc[scenarios["scenario_type"] == "drop_top_positive_states"].copy()
    ax.plot(
        top_drop["removed_state_count"],
        top_drop["mean_loss_advantage"],
        marker="o",
        color="#2563eb",
        linewidth=1.4,
    )
    ax.axhline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    ax.set_title("Drop largest positive state margins")
    ax.set_xlabel("Top positive states removed")
    ax.set_ylabel("Remaining mean loss advantage")
    ax.grid(True, axis="y", alpha=0.24)
    flip_k = int(_summary_value(summary, "first_nonpositive_top_positive_exclusion_k"))
    if flip_k:
        row = top_drop.loc[top_drop["removed_state_count"] == flip_k].iloc[0]
        ax.annotate(
            f"first non-positive: k={flip_k}\n{float(row['mean_loss_advantage']):.4f}",
            xy=(flip_k, float(row["mean_loss_advantage"])),
            xytext=(flip_k + 0.5, float(row["mean_loss_advantage"]) + 0.006),
            arrowprops={"arrowstyle": "->", "color": "#374151", "lw": 0.8},
            fontsize=8.3,
        )


def _plot_state_contributions(ax: plt.Axes, states: pd.DataFrame) -> None:
    ordered = states.sort_values("mean_loss_advantage")
    colors = [
        "#2563eb" if value > 0 else "#7c3aed"
        for value in ordered["mean_loss_advantage"].tolist()
    ]
    ax.barh(ordered["state"], ordered["mean_loss_advantage"], color=colors, alpha=0.82)
    ax.axvline(0.0, color="#111827", linewidth=0.9)
    ax.set_title("All state-cluster contributions")
    ax.set_xlabel("Mean poll Brier minus PM Brier")
    ax.tick_params(axis="y", labelsize=5.9)
    ax.grid(True, axis="x", alpha=0.18)


def _plot_statement_box(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "Outlier robustness\n"
        f"- States: {_int_summary(summary, 'state_count')}.\n"
        f"- Full equal-state mean: "
        f"{_summary_value(summary, 'full_mean_loss_advantage'):.4f}.\n"
        f"- Minimum leave-one-out mean: "
        f"{_summary_value(summary, 'min_leave_one_out_mean_loss_advantage'):.4f}.\n"
        f"- All leave-one-out means positive: "
        f"{_int_summary(summary, 'leave_one_out_all_positive')}.\n"
        f"- Most influential state: "
        f"{_summary_text(summary, 'most_influential_removed_state')}.\n\n"
        "Concentration boundary\n"
        f"- Largest positive state: "
        f"{_summary_text(summary, 'largest_positive_state')} "
        f"({_summary_value(summary, 'largest_positive_state_loss_advantage'):.4f}).\n"
        f"- Positive mean survives removing top "
        f"{_int_summary(summary, 'max_top_positive_exclusion_k_with_positive_mean')} "
        "positive states.\n"
        f"- First non-positive top-k removal: "
        f"{_int_summary(summary, 'first_nonpositive_top_positive_exclusion_k')} "
        f"states, mean "
        f"{_summary_value(summary, 'first_nonpositive_top_positive_exclusion_mean'):.4f}.\n\n"
        "Interpretation\n"
        "- Not driven by any single state.\n"
        "- Still concentrated in top positive states.\n"
        "- Broad many-cases claim remains not_proven."
    )
    ax.text(
        0.02,
        0.96,
        text,
        va="top",
        fontsize=10.2,
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


def _summary_text(summary: pd.DataFrame, summary_id: str) -> str:
    rows = summary.loc[summary["summary_id"] == summary_id, "value"]
    if rows.empty:
        raise ValueError(f"summary_id not found: {summary_id}")
    return str(rows.iloc[0])


def _int_summary(summary: pd.DataFrame, summary_id: str) -> int:
    return int(_summary_value(summary, summary_id))


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_")


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
    parser.add_argument("--state-input", type=Path, default=STATE_INPUT)
    parser.add_argument("--scenario-output", type=Path, default=SCENARIO_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_direct_poll_outlier_robustness_outputs(
            state_input=args.state_input,
            scenario_output=args.scenario_output,
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
