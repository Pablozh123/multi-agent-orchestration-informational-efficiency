"""Build a state-cluster diagnostic for direct H1 poll comparisons.

The direct poll loss decomposition shows lower aggregate mean Brier for
Polymarket, but not a Polymarket majority by source-state cases. This module
checks the same direct poll-transform rows after aggregating to states and
adds deterministic state-cluster uncertainty diagnostics. It is intentionally
diagnostic: state clusters still belong to one 2024 election context.
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
import numpy as np
import pandas as pd
from scipy.stats import binomtest

from operations.analysis.run_h2_event_windows import RESULTS_DIR


CASES_INPUT = RESULTS_DIR / "h1_direct_poll_loss_decomposition_cases.csv"
STATE_OUTPUT = RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_states.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_direct_poll_state_cluster_diagnostic_metadata.json"

DEFAULT_BOOTSTRAP_ITERATIONS = 20_000
DEFAULT_RANDOM_SEED = 20240611

STATE_COLUMNS: tuple[str, ...] = (
    "state",
    "source_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "total_loss_advantage",
    "state_mean_winner",
    "case_majority_winner",
    "source_labels",
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
class H1DirectPollStateClusterDiagnosticResult:
    """Summary of generated state-cluster diagnostic artifacts."""

    state_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    state_count: int
    state_mean_polymarket_support_count: int
    state_mean_poll_support_count: int
    equal_state_mean_loss_advantage: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "state_path": str(self.state_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "state_count": self.state_count,
            "state_mean_polymarket_support_count": (
                self.state_mean_polymarket_support_count
            ),
            "state_mean_poll_support_count": self.state_mean_poll_support_count,
            "equal_state_mean_loss_advantage": self.equal_state_mean_loss_advantage,
            "bootstrap_ci_low": self.bootstrap_ci_low,
            "bootstrap_ci_high": self.bootstrap_ci_high,
        }


def generate_h1_direct_poll_state_cluster_diagnostic_outputs(
    *,
    cases_input: Path = CASES_INPUT,
    state_output: Path = STATE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
    bootstrap_iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> H1DirectPollStateClusterDiagnosticResult:
    """Generate state rows, summary, figure, and metadata."""

    cases = read_cases(cases_input)
    states = validate_state_table(build_state_table(cases))
    summary = validate_summary(
        build_summary(
            cases=cases,
            states=states,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed,
        )
    )

    state_output.parent.mkdir(parents=True, exist_ok=True)
    states.to_csv(state_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_state_cluster_figure(states=states, summary=summary, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        states=states,
        summary=summary,
        cases_input=cases_input,
        state_output=state_output,
        summary_output=summary_output,
        figure_output=figure_output,
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1DirectPollStateClusterDiagnosticResult(
        state_path=state_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        state_count=int(_summary_value(summary, "state_count")),
        state_mean_polymarket_support_count=int(
            _summary_value(summary, "state_mean_polymarket_support_count")
        ),
        state_mean_poll_support_count=int(
            _summary_value(summary, "state_mean_poll_support_count")
        ),
        equal_state_mean_loss_advantage=float(
            _summary_value(summary, "equal_state_mean_loss_advantage")
        ),
        bootstrap_ci_low=float(
            _summary_value(summary, "equal_state_bootstrap_95_ci_low")
        ),
        bootstrap_ci_high=float(
            _summary_value(summary, "equal_state_bootstrap_95_ci_high")
        ),
    )


def read_cases(path: Path) -> pd.DataFrame:
    """Read direct poll loss-decomposition cases."""

    if not path.exists():
        raise FileNotFoundError(f"H1 direct poll loss cases not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "source_id",
        "source_label",
        "state",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
        "lower_loss_source",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 direct poll loss cases missing columns: {missing}")
    _reject_forbidden_columns(frame, "H1 direct poll state-cluster input")
    normalized = frame.copy()
    for column in ("polymarket_brier", "comparator_brier", "loss_advantage"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (normalized["polymarket_brier"] < 0).any() or (
        normalized["comparator_brier"] < 0
    ).any():
        raise ValueError("Brier values must be non-negative")
    return normalized


def build_state_table(cases: pd.DataFrame) -> pd.DataFrame:
    """Aggregate direct poll cases to one row per state."""

    rows: list[dict[str, Any]] = []
    for state, group in cases.groupby("state", sort=True):
        pm_count = int((group["lower_loss_source"] == "polymarket").sum())
        poll_count = int((group["lower_loss_source"] == "comparator").sum())
        tie_count = int((group["lower_loss_source"] == "tie").sum())
        mean_pm = float(group["polymarket_brier"].mean())
        mean_poll = float(group["comparator_brier"].mean())
        mean_advantage = mean_poll - mean_pm
        rows.append(
            {
                "state": str(state),
                "source_count": int(len(group)),
                "polymarket_lower_loss_count": pm_count,
                "poll_derived_lower_loss_count": poll_count,
                "tie_count": tie_count,
                "mean_polymarket_brier": mean_pm,
                "mean_poll_derived_brier": mean_poll,
                "mean_loss_advantage": mean_advantage,
                "total_loss_advantage": float(group["loss_advantage"].sum()),
                "state_mean_winner": _winner_from_values(mean_advantage, 0.0),
                "case_majority_winner": _winner_from_counts(pm_count, poll_count, tie_count),
                "source_labels": ";".join(group["source_label"].astype(str).tolist()),
                "allowed_interpretation": (
                    "State-cluster diagnostic for direct H1 poll-transform comparisons."
                ),
                "limitation": (
                    "States are coarser diagnostic units but still share one "
                    "2024 presidential election context."
                ),
            }
        )
    return pd.DataFrame(rows, columns=STATE_COLUMNS)


def build_summary(
    *,
    cases: pd.DataFrame,
    states: pd.DataFrame,
    bootstrap_iterations: int,
    random_seed: int,
) -> pd.DataFrame:
    """Build compact state-cluster summary rows."""

    if bootstrap_iterations < 100:
        raise ValueError("bootstrap_iterations must be at least 100")
    state_values = states["mean_loss_advantage"].to_numpy(dtype=float)
    bootstrap = bootstrap_state_mean(
        state_values,
        iterations=bootstrap_iterations,
        random_seed=random_seed,
    )
    sign_flip_p = sign_flip_p_value(
        state_values,
        iterations=bootstrap_iterations,
        random_seed=random_seed + 1,
    )
    pm_states = int((states["state_mean_winner"] == "polymarket").sum())
    poll_states = int((states["state_mean_winner"] == "poll_derived").sum())
    tie_states = int((states["state_mean_winner"] == "tie").sum())
    poll_sign_test = binomtest(poll_states, len(states), p=0.5, alternative="greater")
    pm_sign_test = binomtest(pm_states, len(states), p=0.5, alternative="greater")
    rows = [
        _summary_row(
            "source_state_case_count",
            int(len(cases)),
            "source-state cases",
            "Input direct poll-transform source-state cases.",
        ),
        _summary_row(
            "state_count",
            int(len(states)),
            "states",
            "State clusters with at least one direct poll-transform source.",
        ),
        _summary_row(
            "state_mean_polymarket_support_count",
            pm_states,
            "states",
            "States where mean direct poll-transform Brier is lower for Polymarket.",
        ),
        _summary_row(
            "state_mean_poll_support_count",
            poll_states,
            "states",
            "States where mean direct poll-transform Brier is lower for poll-derived comparators.",
        ),
        _summary_row(
            "state_mean_tie_count",
            tie_states,
            "states",
            "States tied by mean direct poll-transform Brier.",
        ),
        _summary_row(
            "equal_state_mean_loss_advantage",
            float(state_values.mean()),
            "brier_score",
            "Equal-state mean of poll-derived Brier minus Polymarket Brier.",
        ),
        _summary_row(
            "equal_state_median_loss_advantage",
            float(np.median(state_values)),
            "brier_score",
            "Equal-state median of poll-derived Brier minus Polymarket Brier.",
        ),
        _summary_row(
            "equal_state_bootstrap_95_ci_low",
            float(np.quantile(bootstrap, 0.025)),
            "brier_score",
            "Deterministic state-cluster bootstrap 2.5 percent quantile.",
        ),
        _summary_row(
            "equal_state_bootstrap_95_ci_high",
            float(np.quantile(bootstrap, 0.975)),
            "brier_score",
            "Deterministic state-cluster bootstrap 97.5 percent quantile.",
        ),
        _summary_row(
            "equal_state_bootstrap_positive_share",
            float((bootstrap > 0.0).mean()),
            "share",
            "Share of deterministic bootstrap means above zero.",
        ),
        _summary_row(
            "equal_state_sign_flip_p_value_greater",
            float(sign_flip_p),
            "p_value",
            "Deterministic Monte Carlo sign-flip p-value for positive equal-state mean.",
        ),
        _summary_row(
            "state_mean_polymarket_exact_binomial_p_value_greater",
            float(pm_sign_test.pvalue),
            "p_value",
            "One-sided exact binomial p-value for Polymarket state-count support.",
        ),
        _summary_row(
            "state_mean_poll_exact_binomial_p_value_greater",
            float(poll_sign_test.pvalue),
            "p_value",
            "One-sided exact binomial p-value for poll-derived state-count support.",
        ),
        _summary_row(
            "state_cluster_mean_supports_polymarket",
            int(state_values.mean() > 0.0),
            "binary",
            "Whether equal-state mean loss advantage is positive for Polymarket.",
        ),
        _summary_row(
            "state_count_majority_supports_polymarket",
            int(pm_states > poll_states),
            "binary",
            "Whether Polymarket wins more state clusters by mean Brier.",
        ),
        _summary_row(
            "broad_many_cases_claim_proven",
            0,
            "binary",
            "This state-cluster diagnostic does not prove the broad many-cases claim.",
        ),
        _summary_row(
            "h1_goal_completion_status",
            "not_proven",
            "status",
            "Equal-state mean supports Polymarket, but state-count majority and broad-scope proof remain incomplete.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def bootstrap_state_mean(
    values: np.ndarray,
    *,
    iterations: int,
    random_seed: int,
) -> np.ndarray:
    """Return deterministic state-cluster bootstrap means."""

    if values.size == 0:
        raise ValueError("values must not be empty")
    rng = np.random.default_rng(random_seed)
    draws = rng.choice(values, size=(iterations, values.size), replace=True)
    return draws.mean(axis=1)


def sign_flip_p_value(
    values: np.ndarray,
    *,
    iterations: int,
    random_seed: int,
) -> float:
    """Return deterministic Monte Carlo sign-flip p-value for positive mean."""

    observed = float(values.mean())
    rng = np.random.default_rng(random_seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(iterations, values.size))
    null_means = (signs * values).mean(axis=1)
    return float((np.count_nonzero(null_means >= observed) + 1) / (iterations + 1))


def validate_state_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate state-cluster table."""

    _require_columns(frame, STATE_COLUMNS, "H1 direct poll state-cluster table")
    _reject_forbidden_columns(frame, "H1 direct poll state-cluster table")
    validated = frame.loc[:, list(STATE_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll state-cluster table must not be empty")
    for column in (
        "source_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise").astype(int)
    for column in (
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
        "total_loss_advantage",
    ):
        validated[column] = pd.to_numeric(validated[column], errors="raise")
    total = (
        validated["polymarket_lower_loss_count"]
        + validated["poll_derived_lower_loss_count"]
        + validated["tie_count"]
    )
    if not (total == validated["source_count"]).all():
        raise ValueError("state lower-loss counts must add to source_count")
    return validated.sort_values("state").reset_index(drop=True)


def validate_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate state-cluster summary table."""

    _require_columns(frame, SUMMARY_COLUMNS, "H1 direct poll state-cluster summary")
    _reject_forbidden_columns(frame, "H1 direct poll state-cluster summary")
    validated = frame.loc[:, list(SUMMARY_COLUMNS)].copy()
    if validated.empty:
        raise ValueError("H1 direct poll state-cluster summary must not be empty")
    if validated["summary_id"].duplicated().any():
        raise ValueError("summary_id values must be unique")
    return validated


def write_state_cluster_figure(
    *,
    states: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the state-cluster diagnostic figure."""

    fig, axes = plt.subplots(2, 2, figsize=(15.6, 9.8))
    fig.suptitle(
        "H1 direct poll comparison: state-cluster diagnostic",
        fontsize=14,
        fontweight="bold",
    )

    _plot_state_support_counts(axes[0, 0], summary)
    _plot_state_advantage_distribution(axes[0, 1], states, summary)
    _plot_largest_state_margins(axes[1, 0], states)
    _plot_statement_box(axes[1, 1], summary)

    fig.text(
        0.5,
        0.012,
        (
            "States are equal-weight diagnostic clusters from direct poll-transform "
            "artifacts. Positive loss advantage means poll-derived Brier minus "
            "Polymarket Brier."
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
    states: pd.DataFrame,
    summary: pd.DataFrame,
    cases_input: Path,
    state_output: Path,
    summary_output: Path,
    figure_output: Path,
    bootstrap_iterations: int,
    random_seed: int,
) -> dict[str, Any]:
    """Build metadata for the state-cluster diagnostic."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_direct_poll_state_cluster_diagnostic",
            "calculation_scope": "deterministic_python_from_existing_h1_direct_poll_artifact",
            "state_clusters_equal_weighted": True,
            "bootstrap_iterations": bootstrap_iterations,
            "random_seed": random_seed,
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
            "source_state_case_count": int(len(cases)),
            "state_count": int(len(states)),
            "state_mean_polymarket_support_count": int(
                _summary_value(summary, "state_mean_polymarket_support_count")
            ),
            "state_mean_poll_support_count": int(
                _summary_value(summary, "state_mean_poll_support_count")
            ),
            "equal_state_mean_loss_advantage": float(
                _summary_value(summary, "equal_state_mean_loss_advantage")
            ),
            "state_cluster_mean_supports_polymarket": bool(
                _summary_value(summary, "state_cluster_mean_supports_polymarket")
            ),
            "state_count_majority_supports_polymarket": bool(
                _summary_value(summary, "state_count_majority_supports_polymarket")
            ),
            "broad_many_cases_claim_proven": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "summary": {
            str(row["summary_id"]): row["value"] for _, row in summary.iterrows()
        },
        "source_paths": {
            "cases_input": str(cases_input),
            "states": str(state_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "states_are_not_independent_elections": True,
            "all_rows_share_one_presidential_election_context": True,
            "cluster_bootstrap_is_diagnostic_not_new_data": True,
            "state_count_majority_does_not_support_polymarket": bool(
                not _summary_value(summary, "state_count_majority_supports_polymarket")
            ),
            "no_causal_or_tradeability_claim": True,
            "goal_many_cases_claim_not_yet_proven": True,
        },
    }


def _plot_state_support_counts(ax: plt.Axes, summary: pd.DataFrame) -> None:
    labels = ["Polymarket", "Poll-derived", "Tie"]
    values = [
        int(_summary_value(summary, "state_mean_polymarket_support_count")),
        int(_summary_value(summary, "state_mean_poll_support_count")),
        int(_summary_value(summary, "state_mean_tie_count")),
    ]
    total = int(_summary_value(summary, "state_count"))
    bars = ax.bar(labels, values, color=["#2563eb", "#7c3aed", "#9ca3af"], alpha=0.84)
    ax.set_title("State-count winner by mean Brier")
    ax.set_ylabel("States")
    ax.set_ylim(0, max(values) + 5)
    ax.grid(True, axis="y", alpha=0.24)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.6,
            f"{value}/{total}",
            ha="center",
            fontsize=9,
        )


def _plot_state_advantage_distribution(
    ax: plt.Axes,
    states: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    values = states["mean_loss_advantage"].to_numpy(dtype=float)
    ax.hist(values, bins=16, color="#93c5fd", edgecolor="#2563eb", alpha=0.86)
    ax.axvline(0.0, color="#111827", linestyle="--", linewidth=0.9)
    ax.axvline(
        _summary_value(summary, "equal_state_mean_loss_advantage"),
        color="#2563eb",
        linewidth=1.5,
        label="Equal-state mean",
    )
    ax.axvline(
        _summary_value(summary, "equal_state_median_loss_advantage"),
        color="#7c3aed",
        linewidth=1.5,
        label="Median",
    )
    ax.set_title("Distribution of state-level loss advantages")
    ax.set_xlabel("Poll Brier minus PM Brier")
    ax.set_ylabel("States")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.22)


def _plot_largest_state_margins(ax: plt.Axes, states: pd.DataFrame) -> None:
    extremes = pd.concat(
        [
            states.nsmallest(7, "mean_loss_advantage"),
            states.nlargest(9, "mean_loss_advantage"),
        ],
        ignore_index=True,
    ).sort_values("mean_loss_advantage")
    colors = [
        "#2563eb" if value > 0 else "#7c3aed"
        for value in extremes["mean_loss_advantage"].tolist()
    ]
    ax.barh(extremes["state"], extremes["mean_loss_advantage"], color=colors, alpha=0.84)
    ax.axvline(0.0, color="#111827", linewidth=0.9)
    ax.set_title("Largest state-level margins")
    ax.set_xlabel("Mean poll Brier minus PM Brier")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, axis="x", alpha=0.22)


def _plot_statement_box(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.axis("off")
    text = (
        "State-cluster diagnostic\n"
        f"- Source-state cases: {_int_summary(summary, 'source_state_case_count')}.\n"
        f"- States: {_int_summary(summary, 'state_count')}.\n"
        f"- Mean winner count: PM "
        f"{_int_summary(summary, 'state_mean_polymarket_support_count')} vs "
        f"poll-derived {_int_summary(summary, 'state_mean_poll_support_count')}.\n"
        f"- Equal-state mean advantage: "
        f"{_summary_value(summary, 'equal_state_mean_loss_advantage'):.4f}.\n"
        f"- Bootstrap 95% interval: "
        f"[{_summary_value(summary, 'equal_state_bootstrap_95_ci_low'):.4f}, "
        f"{_summary_value(summary, 'equal_state_bootstrap_95_ci_high'):.4f}].\n"
        f"- Sign-flip p-value: "
        f"{_summary_value(summary, 'equal_state_sign_flip_p_value_greater'):.4f}.\n\n"
        "Boundary\n"
        f"- PM state-count p-value: "
        f"{_summary_value(summary, 'state_mean_polymarket_exact_binomial_p_value_greater'):.4f}.\n"
        f"- Poll-derived state-count p-value: "
        f"{_summary_value(summary, 'state_mean_poll_exact_binomial_p_value_greater'):.4f}.\n"
        "- Mean supports PM; state-count majority supports poll-derived.\n"
        "- Broad many-cases claim remains not_proven."
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


def _winner_from_values(value: float, reference: float) -> str:
    if value > reference:
        return "polymarket"
    if value < reference:
        return "poll_derived"
    return "tie"


def _winner_from_counts(pm_count: int, poll_count: int, tie_count: int) -> str:
    if pm_count > poll_count and pm_count > tie_count:
        return "polymarket"
    if poll_count > pm_count and poll_count > tie_count:
        return "poll_derived"
    return "tie"


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
    parser.add_argument("--cases-input", type=Path, default=CASES_INPUT)
    parser.add_argument("--state-output", type=Path, default=STATE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=DEFAULT_BOOTSTRAP_ITERATIONS,
    )
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_direct_poll_state_cluster_diagnostic_outputs(
            cases_input=args.cases_input,
            state_output=args.state_output,
            summary_output=args.summary_output,
            figure_output=args.figure_output,
            metadata_output=args.metadata_output,
            bootstrap_iterations=args.bootstrap_iterations,
            random_seed=args.random_seed,
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
