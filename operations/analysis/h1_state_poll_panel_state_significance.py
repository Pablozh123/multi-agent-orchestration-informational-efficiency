"""State-level significance check for H1 late competitive poll-panel support.

This module reads the state-level output of the H1 state-date competitiveness
diagnostic and applies exact binomial tests to state-majority support counts.
The calculation is deterministic and deliberately bounded: it treats states as
the unit for a diagnostic sign test, while documenting that all states still
come from one election context.
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


STATE_INPUT = RESULTS_DIR / "h1_state_poll_panel_competitiveness_state.csv"
SIGNIFICANCE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_state_significance.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_state_significance_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_state_significance.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_state_significance_metadata.json"

STATE_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "state",
    "row_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
)

SIGNIFICANCE_COLUMNS: tuple[str, ...] = (
    "scope_id",
    "scope_label",
    "state_count",
    "polymarket_majority_state_count",
    "poll_derived_majority_state_count",
    "tie_state_count",
    "polymarket_majority_share",
    "poll_derived_majority_share",
    "polymarket_exact_binomial_p_value_greater",
    "polymarket_exact_binomial_p_value_two_sided",
    "polymarket_exact_95_ci_low",
    "polymarket_exact_95_ci_high",
    "poll_derived_exact_binomial_p_value_greater",
    "mean_state_loss_advantage",
    "median_state_loss_advantage",
    "min_state_loss_advantage",
    "max_state_loss_advantage",
    "supports_polymarket_state_level",
    "contradicts_strong_claim",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)

SCOPE_LABELS: dict[str, str] = {
    "late_non_safe_distance": "<=90d low/middle poll-distance states",
    "late_high_distance": "<=90d high poll-distance states",
}


@dataclass(frozen=True)
class H1StatePollPanelStateSignificanceResult:
    """Summary of generated state-level significance artifacts."""

    significance_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    late_non_safe_state_count: int
    late_non_safe_polymarket_majority_state_count: int
    late_non_safe_p_value: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "significance_path": str(self.significance_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "late_non_safe_state_count": self.late_non_safe_state_count,
            "late_non_safe_polymarket_majority_state_count": (
                self.late_non_safe_polymarket_majority_state_count
            ),
            "late_non_safe_p_value": self.late_non_safe_p_value,
        }


def generate_h1_state_poll_panel_state_significance_outputs(
    *,
    state_input: Path = STATE_INPUT,
    significance_output: Path = SIGNIFICANCE_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StatePollPanelStateSignificanceResult:
    """Generate state-level significance outputs."""

    state = read_state_summary(state_input)
    significance = validate_significance(build_significance_summary(state))
    summary = build_summary(significance)

    significance_output.parent.mkdir(parents=True, exist_ok=True)
    significance.to_csv(significance_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_significance_figure(
        state=state,
        significance=significance,
        output_path=figure_output,
    )
    metadata = build_metadata(
        state=state,
        significance=significance,
        summary=summary,
        state_input=state_input,
        significance_output=significance_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1StatePollPanelStateSignificanceResult(
        significance_path=significance_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        late_non_safe_state_count=int(values["late_non_safe_state_count"]),
        late_non_safe_polymarket_majority_state_count=int(
            values["late_non_safe_polymarket_majority_state_count"]
        ),
        late_non_safe_p_value=float(
            values["late_non_safe_polymarket_exact_binomial_p_value_greater"]
        ),
    )


def read_state_summary(path: Path) -> pd.DataFrame:
    """Read and validate state-level competitiveness rows."""

    if not path.exists():
        raise FileNotFoundError(f"H1 state competitiveness input not found: {path}")
    frame = pd.read_csv(path)
    missing = sorted(set(STATE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"H1 state competitiveness input missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"H1 state competitiveness input contains forbidden columns: {forbidden}")
    normalized = frame.loc[:, list(STATE_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("H1 state competitiveness input must not be empty")
    for column in (
        "row_count",
        "polymarket_lower_loss_count",
        "poll_derived_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_better_share",
        "mean_polymarket_brier",
        "mean_poll_derived_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in (
        "aggregate_mean_supports_polymarket",
        "majority_rows_support_polymarket",
    ):
        normalized[column] = _coerce_bool(normalized[column])
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["poll_derived_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["row_count"]
    ).any():
        raise ValueError("state lower-loss counts must add to row_count")
    if normalized["state"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("state names must not be blank")
    return normalized


def build_significance_summary(state: pd.DataFrame) -> pd.DataFrame:
    """Build exact sign-test rows for each diagnostic scope."""

    rows: list[dict[str, Any]] = []
    for scope_id, group in state.groupby("scope_id", sort=True):
        pm_majority = int(group["majority_rows_support_polymarket"].sum())
        poll_majority = int(
            (
                group["poll_derived_lower_loss_count"]
                > group["polymarket_lower_loss_count"]
            ).sum()
        )
        ties = int(len(group) - pm_majority - poll_majority)
        test_n = pm_majority + poll_majority
        if test_n <= 0:
            raise ValueError(f"scope {scope_id} has no non-tie state-majority rows")
        pm_test = binomtest(pm_majority, test_n, p=0.5, alternative="greater")
        pm_two_sided = binomtest(pm_majority, test_n, p=0.5, alternative="two-sided")
        pm_ci = pm_test.proportion_ci(confidence_level=0.95, method="exact")
        poll_test = binomtest(poll_majority, test_n, p=0.5, alternative="greater")
        rows.append(
            {
                "scope_id": scope_id,
                "scope_label": SCOPE_LABELS.get(str(scope_id), str(scope_id)),
                "state_count": int(len(group)),
                "polymarket_majority_state_count": pm_majority,
                "poll_derived_majority_state_count": poll_majority,
                "tie_state_count": ties,
                "polymarket_majority_share": pm_majority / test_n,
                "poll_derived_majority_share": poll_majority / test_n,
                "polymarket_exact_binomial_p_value_greater": float(pm_test.pvalue),
                "polymarket_exact_binomial_p_value_two_sided": float(pm_two_sided.pvalue),
                "polymarket_exact_95_ci_low": float(pm_ci.low),
                "polymarket_exact_95_ci_high": float(pm_ci.high),
                "poll_derived_exact_binomial_p_value_greater": float(poll_test.pvalue),
                "mean_state_loss_advantage": float(group["mean_loss_advantage"].mean()),
                "median_state_loss_advantage": float(group["mean_loss_advantage"].median()),
                "min_state_loss_advantage": float(group["mean_loss_advantage"].min()),
                "max_state_loss_advantage": float(group["mean_loss_advantage"].max()),
                "supports_polymarket_state_level": bool(
                    pm_majority > poll_majority and pm_test.pvalue < 0.05
                ),
                "contradicts_strong_claim": bool(poll_majority > pm_majority),
                "allowed_interpretation": (
                    "Exact binomial sign test over state-majority lower-loss "
                    "directions within the bounded diagnostic scope."
                ),
                "limitation": (
                    "States are treated as diagnostic units, but all states come "
                    "from one election context and are not independent elections."
                ),
            }
        )
    return pd.DataFrame(rows, columns=SIGNIFICANCE_COLUMNS)


def validate_significance(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate exact sign-test rows."""

    missing = [column for column in SIGNIFICANCE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 state significance output missing columns: {missing}")
    normalized = frame.loc[:, list(SIGNIFICANCE_COLUMNS)].copy()
    for column in (
        "state_count",
        "polymarket_majority_state_count",
        "poll_derived_majority_state_count",
        "tie_state_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_majority_share",
        "poll_derived_majority_share",
        "polymarket_exact_binomial_p_value_greater",
        "polymarket_exact_binomial_p_value_two_sided",
        "polymarket_exact_95_ci_low",
        "polymarket_exact_95_ci_high",
        "poll_derived_exact_binomial_p_value_greater",
        "mean_state_loss_advantage",
        "median_state_loss_advantage",
        "min_state_loss_advantage",
        "max_state_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (
        normalized["polymarket_majority_state_count"]
        + normalized["poll_derived_majority_state_count"]
        + normalized["tie_state_count"]
        != normalized["state_count"]
    ).any():
        raise ValueError("state-majority counts must add to state_count")
    for column in (
        "polymarket_majority_share",
        "poll_derived_majority_share",
        "polymarket_exact_binomial_p_value_greater",
        "polymarket_exact_binomial_p_value_two_sided",
        "polymarket_exact_95_ci_low",
        "polymarket_exact_95_ci_high",
        "poll_derived_exact_binomial_p_value_greater",
    ):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    for column in ("supports_polymarket_state_level", "contradicts_strong_claim"):
        normalized[column] = _coerce_bool(normalized[column])
    return normalized


def build_summary(significance: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for report and audit integration."""

    late_non_safe = _scope(significance, "late_non_safe_distance")
    late_high = _scope(significance, "late_high_distance")
    rows = [
        _summary_row(
            "late_non_safe_state_count",
            int(late_non_safe["state_count"]),
            "states",
            "Late low/middle-distance state count.",
        ),
        _summary_row(
            "late_non_safe_polymarket_majority_state_count",
            int(late_non_safe["polymarket_majority_state_count"]),
            "states",
            "Late low/middle-distance states with Polymarket lower-loss majority.",
        ),
        _summary_row(
            "late_non_safe_polymarket_majority_share",
            float(late_non_safe["polymarket_majority_share"]),
            "share",
            "Late low/middle-distance Polymarket state-majority share.",
        ),
        _summary_row(
            "late_non_safe_polymarket_exact_binomial_p_value_greater",
            float(late_non_safe["polymarket_exact_binomial_p_value_greater"]),
            "p_value",
            "One-sided exact binomial p-value for Polymarket state-majority support.",
        ),
        _summary_row(
            "late_non_safe_polymarket_exact_95_ci_low",
            float(late_non_safe["polymarket_exact_95_ci_low"]),
            "share",
            "Lower exact 95 percent confidence bound for Polymarket state-majority share.",
        ),
        _summary_row(
            "late_high_distance_state_count",
            int(late_high["state_count"]),
            "states",
            "Late high-distance state count.",
        ),
        _summary_row(
            "late_high_distance_polymarket_majority_state_count",
            int(late_high["polymarket_majority_state_count"]),
            "states",
            "Late high-distance states with Polymarket lower-loss majority.",
        ),
        _summary_row(
            "late_high_distance_poll_majority_state_count",
            int(late_high["poll_derived_majority_state_count"]),
            "states",
            "Late high-distance states with poll-derived lower-loss majority.",
        ),
        _summary_row(
            "late_high_distance_poll_exact_binomial_p_value_greater",
            float(late_high["poll_derived_exact_binomial_p_value_greater"]),
            "p_value",
            "One-sided exact binomial p-value for poll-derived state-majority support.",
        ),
        _summary_row(
            "late_non_safe_state_level_supports_polymarket",
            int(bool(late_non_safe["supports_polymarket_state_level"])),
            "binary",
            "The late low/middle-distance state-level sign test supports Polymarket.",
        ),
        _summary_row(
            "late_high_distance_state_level_contradicts_strong_claim",
            int(bool(late_high["contradicts_strong_claim"])),
            "binary",
            "The late high-distance state-level result contradicts the strong claim.",
        ),
        _summary_row(
            "broad_many_cases_claim_supported_now",
            0,
            "binary",
            "This diagnostic does not prove the requested broad many-cases claim.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_significance_figure(
    *,
    state: pd.DataFrame,
    significance: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write state-level significance figure."""

    non_safe = state.loc[state["scope_id"] == "late_non_safe_distance"].sort_values(
        "mean_loss_advantage"
    )
    high = state.loc[state["scope_id"] == "late_high_distance"].sort_values(
        "mean_loss_advantage"
    )
    fig, axes = plt.subplots(2, 2, figsize=(15.8, 9.8))
    fig.suptitle(
        "H1 State-Level Significance: Late Competitive Poll Panel",
        fontsize=14,
        fontweight="bold",
    )
    _plot_state_advantage(
        axes[0, 0],
        non_safe,
        "<=90d low/middle poll-distance states",
    )
    _plot_state_advantage(
        axes[0, 1],
        high,
        "<=90d high poll-distance states",
    )

    sig = significance.set_index("scope_id")
    scope_labels = ["Low/middle\npoll distance", "High\npoll distance"]
    pm_counts = [
        int(sig.loc["late_non_safe_distance", "polymarket_majority_state_count"]),
        int(sig.loc["late_high_distance", "polymarket_majority_state_count"]),
    ]
    poll_counts = [
        int(sig.loc["late_non_safe_distance", "poll_derived_majority_state_count"]),
        int(sig.loc["late_high_distance", "poll_derived_majority_state_count"]),
    ]
    x = np.arange(len(scope_labels))
    width = 0.36
    axes[1, 0].bar(
        x - width / 2,
        pm_counts,
        width=width,
        color="#2563eb",
        label="Polymarket",
    )
    axes[1, 0].bar(
        x + width / 2,
        poll_counts,
        width=width,
        color="#7c3aed",
        label="Poll-derived",
    )
    axes[1, 0].set_xticks(x, scope_labels)
    axes[1, 0].set_ylabel("States with lower-loss majority")
    axes[1, 0].set_title("State-majority counts")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(pm_counts):
        axes[1, 0].text(idx - width / 2, value + 0.08, str(value), ha="center", fontsize=9)
    for idx, value in enumerate(poll_counts):
        axes[1, 0].text(idx + width / 2, value + 0.08, str(value), ha="center", fontsize=9)

    axes[1, 1].axis("off")
    p_value = float(
        sig.loc[
            "late_non_safe_distance",
            "polymarket_exact_binomial_p_value_greater",
        ]
    )
    ci_low = float(sig.loc["late_non_safe_distance", "polymarket_exact_95_ci_low"])
    high_poll_p = float(
        sig.loc[
            "late_high_distance",
            "poll_derived_exact_binomial_p_value_greater",
        ]
    )
    axes[1, 1].text(
        0.02,
        0.82,
        "Exact state-level sign test",
        fontsize=12,
        fontweight="bold",
        transform=axes[1, 1].transAxes,
    )
    axes[1, 1].text(
        0.02,
        0.60,
        (
            "Late low/middle distance:\n"
            f"Polymarket states 9/9, one-sided exact p = {p_value:.4f};\n"
            f"exact 95% lower bound for support share = {ci_low:.3f}."
        ),
        fontsize=10,
        transform=axes[1, 1].transAxes,
    )
    axes[1, 1].text(
        0.02,
        0.33,
        (
            "Late high distance:\n"
            "poll-derived states 5/5, "
            f"one-sided exact p = {high_poll_p:.4f}."
        ),
        fontsize=10,
        transform=axes[1, 1].transAxes,
    )
    axes[1, 1].text(
        0.02,
        0.10,
        (
            "Scope: diagnostic state-as-unit sign test. "
            "All states still come from one election context."
        ),
        fontsize=9,
        color="#374151",
        transform=axes[1, 1].transAxes,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return output_path


def build_metadata(
    *,
    state: pd.DataFrame,
    significance: pd.DataFrame,
    summary: pd.DataFrame,
    state_input: Path,
    significance_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the state-level significance diagnostic."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_state_significance",
            "calculation_scope": "deterministic_python_from_h1_state_poll_panel_competitiveness_state",
            "test": "exact_binomial_sign_test_over_state_majority_directions",
            "state_unit": "resolved_state_within_bounded_scope",
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "late_non_safe_state_count": int(values["late_non_safe_state_count"]),
            "late_non_safe_polymarket_majority_state_count": int(
                values["late_non_safe_polymarket_majority_state_count"]
            ),
            "late_non_safe_polymarket_exact_binomial_p_value_greater": float(
                values["late_non_safe_polymarket_exact_binomial_p_value_greater"]
            ),
            "late_high_distance_state_count": int(values["late_high_distance_state_count"]),
            "late_high_distance_poll_majority_state_count": int(
                values["late_high_distance_poll_majority_state_count"]
            ),
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "state_input": str(state_input),
            "significance": str(significance_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "summary": {str(row["summary_id"]): row["value"] for _, row in summary.iterrows()},
        "significance_rows": significance.to_dict(orient="records"),
        "state_rows": state.to_dict(orient="records"),
        "limitations": {
            "states_are_diagnostic_units_not_independent_elections": True,
            "one_election_context": True,
            "poll_probabilities_are_model_transformed": True,
            "state_sign_test_is_bounded_not_broad_proof": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _plot_state_advantage(axis, frame: pd.DataFrame, title: str) -> None:
    colors = ["#2563eb" if value > 0 else "#7c3aed" for value in frame["mean_loss_advantage"]]
    axis.barh(frame["state"], frame["mean_loss_advantage"], color=colors)
    axis.axvline(0, color="#6b7280", linestyle="--", linewidth=1.0)
    axis.set_xlabel("Mean poll-derived Brier minus Polymarket Brier")
    axis.set_title(title)
    axis.grid(True, axis="x", alpha=0.25)


def _coerce_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    normalized = series.astype(str).str.strip().str.lower()
    valid = {"true": True, "false": False, "1": True, "0": False}
    unknown = sorted(set(normalized) - set(valid))
    if unknown:
        raise ValueError(f"cannot coerce boolean values: {unknown}")
    return normalized.map(valid).astype(bool)


def _scope(frame: pd.DataFrame, scope_id: str) -> pd.Series:
    rows = frame.loc[frame["scope_id"] == scope_id]
    if len(rows) != 1:
        raise ValueError(f"expected one {scope_id!r} row, found {len(rows)}")
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


def _summary_values(summary: pd.DataFrame) -> dict[str, float]:
    return {str(row["summary_id"]): float(row["value"]) for _, row in summary.iterrows()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-input", type=Path, default=STATE_INPUT)
    parser.add_argument("--significance-output", type=Path, default=SIGNIFICANCE_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_state_significance_outputs(
            state_input=args.state_input,
            significance_output=args.significance_output,
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
