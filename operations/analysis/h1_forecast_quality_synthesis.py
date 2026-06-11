"""Synthesize H1 forecast-quality evidence across deterministic extensions.

The H1 baseline now has several compatible forecast-quality comparisons:
daily Polymarket-vs-FiveThirtyEight rows, curated final-snapshot outcomes,
state poll-derived probabilities, a popular-vote poll-transform panel, and two
50-state model-forecast extensions. This module creates a single audited table
and figure so the thesis-facing claim boundary is visible: aggregate mean Brier
support is not the same as Polymarket winning most individual cases.
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


PAIRWISE_INPUT = RESULTS_DIR / "h1_forecast_quality_pairwise.csv"
FINAL_SNAPSHOT_INPUT = RESULTS_DIR / "h1_final_snapshot_summary.csv"
STATE_POLL_INPUT = RESULTS_DIR / "h1_state_poll_snapshot_summary.csv"
STATE_POLL_PANEL_INPUT = RESULTS_DIR / "h1_state_poll_panel_summary.csv"
POPULAR_VOTE_INPUT = RESULTS_DIR / "h1_popular_vote_summary.csv"
RIEKE_INPUT = RESULTS_DIR / "h1_rieke_state_forecast_summary.csv"
TWO_SEVENTY_INPUT = RESULTS_DIR / "h1_270towin_state_forecast_summary.csv"
TWO_SEVENTY_POLL_AVERAGE_INPUT = RESULTS_DIR / "h1_270towin_poll_average_summary.csv"

SYNTHESIS_OUTPUT = RESULTS_DIR / "h1_forecast_quality_synthesis.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_forecast_quality_synthesis.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_forecast_quality_synthesis_metadata.json"

SYNTHESIS_COLUMNS: tuple[str, ...] = (
    "evidence_id",
    "evidence_label",
    "comparator_label",
    "case_count",
    "case_unit",
    "polymarket_lower_loss_count",
    "comparator_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_cases_supports_polymarket",
    "broad_many_cases_claim_supported",
    "evidence_scope",
    "limitation",
)


@dataclass(frozen=True)
class H1ForecastQualitySynthesisResult:
    """Summary of generated H1 synthesis artifacts."""

    synthesis_path: Path
    figure_path: Path
    metadata_path: Path
    evidence_row_count: int
    aggregate_support_row_count: int
    majority_support_row_count: int
    broad_many_cases_support_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "synthesis_path": str(self.synthesis_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "evidence_row_count": self.evidence_row_count,
            "aggregate_support_row_count": self.aggregate_support_row_count,
            "majority_support_row_count": self.majority_support_row_count,
            "broad_many_cases_support_row_count": (
                self.broad_many_cases_support_row_count
            ),
        }


def generate_h1_forecast_quality_synthesis_outputs(
    *,
    pairwise_input: Path = PAIRWISE_INPUT,
    final_snapshot_input: Path = FINAL_SNAPSHOT_INPUT,
    state_poll_input: Path = STATE_POLL_INPUT,
    state_poll_panel_input: Path = STATE_POLL_PANEL_INPUT,
    popular_vote_input: Path = POPULAR_VOTE_INPUT,
    rieke_input: Path = RIEKE_INPUT,
    two_seventy_input: Path = TWO_SEVENTY_INPUT,
    two_seventy_poll_average_input: Path = TWO_SEVENTY_POLL_AVERAGE_INPUT,
    synthesis_output: Path = SYNTHESIS_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1ForecastQualitySynthesisResult:
    """Generate H1 synthesis CSV, figure, and metadata."""

    synthesis = build_synthesis_table(
        pairwise=read_pairwise(pairwise_input),
        final_snapshot=read_summary(final_snapshot_input),
        state_poll=read_summary(state_poll_input),
        state_poll_panel=read_summary(state_poll_panel_input),
        popular_vote=read_summary(popular_vote_input),
        rieke=read_summary(rieke_input),
        two_seventy=read_summary(two_seventy_input),
        two_seventy_poll_average=read_summary(two_seventy_poll_average_input),
    )
    synthesis = validate_synthesis_table(synthesis)
    synthesis_output.parent.mkdir(parents=True, exist_ok=True)
    synthesis.to_csv(synthesis_output, index=False)
    write_synthesis_figure(synthesis=synthesis, output_path=figure_output)
    metadata = build_metadata(
        synthesis=synthesis,
        pairwise_input=pairwise_input,
        final_snapshot_input=final_snapshot_input,
        state_poll_input=state_poll_input,
        state_poll_panel_input=state_poll_panel_input,
        popular_vote_input=popular_vote_input,
        rieke_input=rieke_input,
        two_seventy_input=two_seventy_input,
        two_seventy_poll_average_input=two_seventy_poll_average_input,
        synthesis_output=synthesis_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H1ForecastQualitySynthesisResult(
        synthesis_path=synthesis_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        evidence_row_count=int(len(synthesis)),
        aggregate_support_row_count=int(
            synthesis["aggregate_mean_supports_polymarket"].sum()
        ),
        majority_support_row_count=int(
            synthesis["majority_cases_supports_polymarket"].sum()
        ),
        broad_many_cases_support_row_count=int(
            synthesis["broad_many_cases_claim_supported"].sum()
        ),
    )


def read_pairwise(path: Path) -> pd.DataFrame:
    """Read the H1 pairwise daily summary."""

    if not path.exists():
        raise FileNotFoundError(f"H1 pairwise input not found: {path}")
    frame = pd.read_csv(path)
    required = {
        "comparator",
        "comparison_row_count",
        "polymarket_lower_loss_count",
        "comparator_lower_loss_count",
        "tie_count",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 pairwise input missing columns: {missing}")
    return frame


def read_summary(path: Path) -> pd.DataFrame:
    """Read a compact summary_id/value H1 artifact."""

    if not path.exists():
        raise FileNotFoundError(f"H1 summary input not found: {path}")
    frame = pd.read_csv(path)
    required = {"summary_id", "value"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 summary input missing columns: {missing}")
    return frame


def build_synthesis_table(
    *,
    pairwise: pd.DataFrame,
    final_snapshot: pd.DataFrame,
    state_poll: pd.DataFrame,
    state_poll_panel: pd.DataFrame,
    popular_vote: pd.DataFrame,
    rieke: pd.DataFrame,
    two_seventy: pd.DataFrame,
    two_seventy_poll_average: pd.DataFrame,
) -> pd.DataFrame:
    """Build one H1 evidence-row table from existing deterministic summaries."""

    fte = pairwise.loc[pairwise["comparator"] == "fivethirtyeight"]
    if len(fte) != 1:
        raise ValueError("pairwise summary must contain one fivethirtyeight row")
    fte_row = fte.iloc[0]
    rows = [
        _row(
            evidence_id="daily_fivethirtyeight",
            evidence_label="Daily 538 overlap",
            comparator_label="FiveThirtyEight",
            case_count=int(fte_row["comparison_row_count"]),
            case_unit="daily_forecast_rows",
            pm_lower=int(fte_row["polymarket_lower_loss_count"]),
            comp_lower=int(fte_row["comparator_lower_loss_count"]),
            ties=int(fte_row["tie_count"]),
            mean_pm=float(fte_row["mean_polymarket_brier"]),
            mean_comp=float(fte_row["mean_comparator_brier"]),
            scope="daily rows from one resolved election market",
            limitation="Repeated daily forecasts; not independent election outcomes.",
        ),
        _row(
            evidence_id="final_snapshot_538",
            evidence_label="Final 538 snapshots",
            comparator_label="FiveThirtyEight final forecast",
            case_count=int(_summary_value(final_snapshot, "case_count")),
            case_unit="resolved_outcomes",
            pm_lower=int(_summary_value(final_snapshot, "polymarket_lower_loss_count")),
            comp_lower=int(_summary_value(final_snapshot, "traditional_lower_loss_count")),
            ties=int(_summary_value(final_snapshot, "tie_count", default=0.0)),
            mean_pm=_summary_value(final_snapshot, "mean_polymarket_brier"),
            mean_comp=_summary_value(final_snapshot, "mean_traditional_brier"),
            scope="curated resolved final-snapshot outcomes",
            limitation="Small 2024 election-day extension, not broad market coverage.",
        ),
        _row(
            evidence_id="state_poll_538_transform",
            evidence_label="538 state poll transform",
            comparator_label="538 poll-derived probability",
            case_count=int(_summary_value(state_poll, "case_count")),
            case_unit="resolved_state_outcomes",
            pm_lower=int(_summary_value(state_poll, "polymarket_lower_loss_count")),
            comp_lower=int(_summary_value(state_poll, "poll_derived_lower_loss_count")),
            ties=int(_summary_value(state_poll, "tie_count", default=0.0)),
            mean_pm=_summary_value(state_poll, "mean_polymarket_brier"),
            mean_comp=_summary_value(state_poll, "mean_poll_derived_brier"),
            scope="13 states with compatible 538 REP/DEM snapshot rows",
            limitation="Documented probability transform; not official 538 state forecast.",
        ),
        _row(
            evidence_id="state_poll_panel_538_transform",
            evidence_label="538 state poll panel",
            comparator_label="538 poll-derived probability panel",
            case_count=int(_summary_value(state_poll_panel, "matched_case_count")),
            case_unit="state_date_forecast_rows",
            pm_lower=int(
                _summary_value(state_poll_panel, "polymarket_lower_loss_count")
            ),
            comp_lower=int(
                _summary_value(state_poll_panel, "poll_derived_lower_loss_count")
            ),
            ties=int(_summary_value(state_poll_panel, "tie_count", default=0.0)),
            mean_pm=_summary_value(state_poll_panel, "mean_polymarket_brier"),
            mean_comp=_summary_value(state_poll_panel, "mean_poll_derived_brier"),
            scope="repeated state-date rows from 15 resolved state outcomes",
            limitation=(
                "Large repeated forecast panel; not independent elections and "
                "it does not support the Polymarket advantage claim."
            ),
        ),
        _row(
            evidence_id="popular_vote_538_transform",
            evidence_label="538 national popular-vote transform",
            comparator_label="538 poll-derived popular-vote probability",
            case_count=int(_summary_value(popular_vote, "case_count")),
            case_unit="daily_forecast_rows",
            pm_lower=int(_summary_value(popular_vote, "polymarket_lower_loss_count")),
            comp_lower=int(_summary_value(popular_vote, "poll_derived_lower_loss_count")),
            ties=int(_summary_value(popular_vote, "tie_count", default=0.0)),
            mean_pm=_summary_value(popular_vote, "mean_polymarket_brier"),
            mean_comp=_summary_value(popular_vote, "mean_poll_derived_brier"),
            scope="national daily rows for one resolved popular-vote outcome",
            limitation=(
                "Documented poll-margin transform; contradicts the broad "
                "Polymarket advantage claim for this outcome."
            ),
        ),
        _row(
            evidence_id="rieke_50_state",
            evidence_label="Rieke 50-state model",
            comparator_label="Rieke poll-based model",
            case_count=int(_summary_value(rieke, "case_count")),
            case_unit="resolved_state_outcomes",
            pm_lower=int(_summary_value(rieke, "polymarket_lower_loss_count")),
            comp_lower=int(_summary_value(rieke, "rieke_lower_loss_count")),
            ties=int(_summary_value(rieke, "tie_count", default=0.0)),
            mean_pm=_summary_value(rieke, "mean_polymarket_brier"),
            mean_comp=_summary_value(rieke, "mean_rieke_brier"),
            scope="50 states from one presidential election context",
            limitation="Lower aggregate loss, but Rieke wins most state-level cases.",
        ),
        _row(
            evidence_id="two_seventy_poll_average_transform",
            evidence_label="270toWin state poll transform",
            comparator_label="270toWin poll-derived probability",
            case_count=int(_summary_value(two_seventy_poll_average, "case_count")),
            case_unit="resolved_state_outcomes",
            pm_lower=int(
                _summary_value(two_seventy_poll_average, "polymarket_lower_loss_count")
            ),
            comp_lower=int(
                _summary_value(two_seventy_poll_average, "poll_derived_lower_loss_count")
            ),
            ties=int(_summary_value(two_seventy_poll_average, "tie_count", default=0.0)),
            mean_pm=_summary_value(two_seventy_poll_average, "mean_polymarket_brier"),
            mean_comp=_summary_value(two_seventy_poll_average, "mean_poll_derived_brier"),
            scope="43 states with 270toWin final polling averages and Polymarket state markets",
            limitation=(
                "Direct polling-average margin transformed to probability; "
                "poll-derived wins most state-level cases."
            ),
        ),
        _row(
            evidence_id="two_seventy_50_state",
            evidence_label="270toWin/JHK 50-state model",
            comparator_label="270toWin/JHK",
            case_count=int(_summary_value(two_seventy, "case_count")),
            case_unit="resolved_state_outcomes",
            pm_lower=int(_summary_value(two_seventy, "polymarket_lower_loss_count")),
            comp_lower=int(_summary_value(two_seventy, "two_seventy_lower_loss_count")),
            ties=int(_summary_value(two_seventy, "tie_count", default=0.0)),
            mean_pm=_summary_value(two_seventy, "mean_polymarket_brier"),
            mean_comp=_summary_value(two_seventy, "mean_two_seventy_brier"),
            scope="50 states; 28 source probabilities are censored boundaries",
            limitation="Lower aggregate loss, but 270toWin/JHK wins most state cases.",
        ),
        _row(
            evidence_id="two_seventy_exact_22",
            evidence_label="270toWin/JHK exact-state subset",
            comparator_label="270toWin/JHK exact probabilities",
            case_count=int(_summary_value(two_seventy, "exact_probability_case_count")),
            case_unit="resolved_state_outcomes",
            pm_lower=int(
                _summary_value(
                    two_seventy,
                    "exact_probability_polymarket_lower_loss_count",
                )
            ),
            comp_lower=int(
                _summary_value(
                    two_seventy,
                    "exact_probability_two_seventy_lower_loss_count",
                )
            ),
            ties=int(_summary_value(two_seventy, "exact_probability_tie_count")),
            mean_pm=_summary_value(two_seventy, "exact_probability_mean_polymarket_brier"),
            mean_comp=_summary_value(
                two_seventy,
                "exact_probability_mean_two_seventy_brier",
            ),
            scope="22 states with exact 270toWin source percentages",
            limitation="Exact subset still belongs to one election context.",
        ),
    ]
    return pd.DataFrame(rows, columns=SYNTHESIS_COLUMNS)


def validate_synthesis_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the H1 synthesis table contract."""

    missing = [column for column in SYNTHESIS_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 synthesis table missing columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"H1 synthesis table must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(SYNTHESIS_COLUMNS)].copy()
    for column in (
        "case_count",
        "polymarket_lower_loss_count",
        "comparator_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (normalized["case_count"] <= 0).any():
        raise ValueError("H1 synthesis case counts must be positive")
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["comparator_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["case_count"]
    ).any():
        raise ValueError("H1 synthesis lower-loss counts must add to case_count")
    if not normalized["polymarket_lower_loss_share"].between(0.0, 1.0).all():
        raise ValueError("H1 synthesis shares must be in [0, 1]")
    for column in (
        "aggregate_mean_supports_polymarket",
        "majority_cases_supports_polymarket",
        "broad_many_cases_claim_supported",
    ):
        normalized[column] = normalized[column].astype(bool)
    return normalized


def write_synthesis_figure(*, synthesis: pd.DataFrame, output_path: Path) -> Path:
    """Write a compact H1 cross-source synthesis figure."""

    short_label_map = {
        "daily_fivethirtyeight": "Daily\n538",
        "final_snapshot_538": "Final\n538",
        "state_poll_538_transform": "State\n538",
        "state_poll_panel_538_transform": "State\npanel",
        "popular_vote_538_transform": "Popular\nvote",
        "rieke_50_state": "Rieke\n50",
        "two_seventy_poll_average_transform": "270 poll\n43",
        "two_seventy_50_state": "270/JHK\n50",
        "two_seventy_exact_22": "270/JHK\nexact",
    }
    short_labels = [
        short_label_map.get(str(row["evidence_id"]), str(row["evidence_label"]))
        for _, row in synthesis.iterrows()
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14.4, 8.8))
    fig.suptitle(
        "H1 Forecast-Quality Synthesis Across Traditional Comparators",
        fontsize=13.5,
        fontweight="bold",
    )

    advantage = synthesis["mean_loss_advantage"].to_numpy()
    colors = ["#2563eb" if value > 0 else "#7c3aed" for value in advantage]
    axes[0, 0].bar(short_labels, advantage, color=colors)
    axes[0, 0].axhline(0, color="#111827", linewidth=0.8)
    axes[0, 0].set_ylabel("Comparator Brier minus Polymarket Brier")
    axes[0, 0].set_title("Aggregate mean-loss advantage")
    axes[0, 0].grid(True, axis="y", alpha=0.25)
    for idx, value in enumerate(advantage):
        offset = 0.003 if value >= 0 else -0.006
        axes[0, 0].text(idx, value + offset, f"{value:.4f}", ha="center", fontsize=8)

    x = np.arange(len(synthesis))
    pm_share = synthesis["polymarket_lower_loss_count"] / synthesis["case_count"]
    comp_share = synthesis["comparator_lower_loss_count"] / synthesis["case_count"]
    tie_share = synthesis["tie_count"] / synthesis["case_count"]
    axes[0, 1].bar(x, pm_share, label="Polymarket lower loss", color="#2563eb")
    axes[0, 1].bar(x, comp_share, bottom=pm_share, label="Comparator lower loss", color="#7c3aed")
    axes[0, 1].bar(
        x,
        tie_share,
        bottom=pm_share + comp_share,
        label="Tie",
        color="#9ca3af",
    )
    axes[0, 1].set_xticks(x, short_labels)
    axes[0, 1].set_ylim(0, 1.08)
    axes[0, 1].set_ylabel("Share of compared rows/cases")
    axes[0, 1].set_title("Head-to-head lower-loss shares")
    axes[0, 1].legend(fontsize=8, loc="lower left")
    axes[0, 1].grid(True, axis="y", alpha=0.25)
    for idx, row in synthesis.iterrows():
        axes[0, 1].text(
            idx,
            1.015,
            f"{int(row['polymarket_lower_loss_count'])}/{int(row['case_count'])}",
            ha="center",
            fontsize=7.5,
        )

    checks = synthesis[
        [
            "aggregate_mean_supports_polymarket",
            "majority_cases_supports_polymarket",
            "broad_many_cases_claim_supported",
        ]
    ].astype(int)
    axes[1, 0].imshow(
        checks.to_numpy().T,
        aspect="auto",
        cmap=ListedColormap(["#f3f4f6", "#bbf7d0"]),
        vmin=0,
        vmax=1,
    )
    axes[1, 0].set_xticks(x, short_labels)
    axes[1, 0].set_yticks(
        [0, 1, 2],
        ["Mean Brier\nsupports PM", "Majority cases\nsupport PM", "Broad claim\nproven"],
    )
    axes[1, 0].set_title("Claim audit")
    for row_idx in range(checks.shape[0]):
        for col_idx in range(checks.shape[1]):
            value = checks.iloc[row_idx, col_idx]
            axes[1, 0].text(
                row_idx,
                col_idx,
                "yes" if value else "no",
                ha="center",
                va="center",
                color="#111827",
                fontsize=8,
            )

    sizes = np.sqrt(synthesis["case_count"].to_numpy()) * 32
    axes[1, 1].scatter(
        synthesis["polymarket_lower_loss_share"],
        synthesis["mean_loss_advantage"],
        s=sizes,
        color="#2563eb",
        alpha=0.72,
        edgecolor="#111827",
        linewidth=0.4,
    )
    axes[1, 1].axvline(0.5, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 1].axhline(0, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 1].set_xlabel("Polymarket lower-loss share")
    axes[1, 1].set_ylabel("Mean loss advantage")
    axes[1, 1].set_title("Aggregate support vs case-majority support")
    axes[1, 1].set_xlim(-0.03, 1.08)
    y_min = float(synthesis["mean_loss_advantage"].min())
    y_max = float(synthesis["mean_loss_advantage"].max())
    y_margin = max(0.015, (y_max - y_min) * 0.18)
    axes[1, 1].set_ylim(y_min - y_margin, y_max + y_margin)
    axes[1, 1].grid(True, alpha=0.25)
    for idx, label in enumerate(short_labels):
        x_value = synthesis["polymarket_lower_loss_share"].iloc[idx]
        evidence_id = str(synthesis["evidence_id"].iloc[idx])
        custom_offsets = {
            "rieke_50_state": (-58, -8, "right"),
            "two_seventy_poll_average_transform": (6, 11, "left"),
            "two_seventy_50_state": (-48, 8, "right"),
            "two_seventy_exact_22": (8, -13, "left"),
            "popular_vote_538_transform": (6, -12, "left"),
        }
        if evidence_id in custom_offsets:
            x_offset, y_offset, ha = custom_offsets[evidence_id]
            xytext = (x_offset, y_offset)
        else:
            xytext = (-52, 4) if x_value > 0.85 else (5, 4)
            ha = "right" if x_value > 0.85 else "left"
        axes[1, 1].annotate(
            label.replace("\n", " "),
            (
                x_value,
                synthesis["mean_loss_advantage"].iloc[idx],
            ),
            xytext=xytext,
            textcoords="offset points",
            ha=ha,
            fontsize=7.5,
        )

    fig.text(
        0.5,
        0.012,
        "The state-date poll panel and case-majority checks still block a broad Polymarket advantage claim.",
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
    synthesis: pd.DataFrame,
    pairwise_input: Path,
    final_snapshot_input: Path,
    state_poll_input: Path,
    state_poll_panel_input: Path,
    popular_vote_input: Path,
    rieke_input: Path,
    two_seventy_input: Path,
    two_seventy_poll_average_input: Path,
    synthesis_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the H1 synthesis output."""

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_forecast_quality_cross_source_synthesis",
            "calculation_scope": "deterministic_python_from_precomputed_h1_summaries",
            "does_not_recompute_brier_from_raw_rows": True,
            "uses_raw_poll_shares_directly": False,
            "rcp_included": False,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "outputs": {
            "evidence_row_count": int(len(synthesis)),
            "aggregate_support_row_count": int(
                synthesis["aggregate_mean_supports_polymarket"].sum()
            ),
            "majority_support_row_count": int(
                synthesis["majority_cases_supports_polymarket"].sum()
            ),
            "broad_many_cases_support_row_count": int(
                synthesis["broad_many_cases_claim_supported"].sum()
            ),
            "h1_goal_completion_status": "not_proven",
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "pairwise_input": str(pairwise_input),
            "final_snapshot_input": str(final_snapshot_input),
            "state_poll_input": str(state_poll_input),
            "state_poll_panel_input": str(state_poll_panel_input),
            "popular_vote_input": str(popular_vote_input),
            "rieke_input": str(rieke_input),
            "two_seventy_input": str(two_seventy_input),
            "two_seventy_poll_average_input": str(two_seventy_poll_average_input),
            "synthesis": str(synthesis_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "daily_rows_are_not_independent_outcomes": True,
            "state_rows_share_one_election_context": True,
            "poll_transform_rows_are_model_dependent": True,
            "state_poll_panel_rows_are_repeated_forecasts": True,
            "popular_vote_rows_are_repeated_forecasts": True,
            "popular_vote_poll_transform_is_model_dependent": True,
            "two_seventy_poll_average_transform_is_model_dependent": True,
            "two_seventy_safe_state_probabilities_are_censored": True,
            "aggregate_mean_loss_not_same_as_majority_of_cases": True,
            "goal_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _row(
    *,
    evidence_id: str,
    evidence_label: str,
    comparator_label: str,
    case_count: int,
    case_unit: str,
    pm_lower: int,
    comp_lower: int,
    ties: int,
    mean_pm: float,
    mean_comp: float,
    scope: str,
    limitation: str,
) -> dict[str, Any]:
    if case_count <= 0:
        raise ValueError("case_count must be positive")
    advantage = mean_comp - mean_pm
    aggregate_support = advantage > 0
    majority_support = pm_lower > comp_lower and pm_lower > (case_count / 2.0)
    broad_support = (
        aggregate_support
        and majority_support
        and case_count >= 30
        and case_unit != "daily_forecast_rows"
    )
    return {
        "evidence_id": evidence_id,
        "evidence_label": evidence_label,
        "comparator_label": comparator_label,
        "case_count": case_count,
        "case_unit": case_unit,
        "polymarket_lower_loss_count": pm_lower,
        "comparator_lower_loss_count": comp_lower,
        "tie_count": ties,
        "polymarket_lower_loss_share": pm_lower / case_count,
        "mean_polymarket_brier": mean_pm,
        "mean_comparator_brier": mean_comp,
        "mean_loss_advantage": advantage,
        "aggregate_mean_supports_polymarket": aggregate_support,
        "majority_cases_supports_polymarket": majority_support,
        "broad_many_cases_claim_supported": broad_support,
        "evidence_scope": scope,
        "limitation": limitation,
    }


def _summary_value(
    frame: pd.DataFrame,
    summary_id: str,
    *,
    default: float | None = None,
) -> float:
    rows = frame.loc[frame["summary_id"] == summary_id, "value"]
    if rows.empty:
        if default is not None:
            return default
        raise ValueError(f"summary_id not found: {summary_id}")
    return float(rows.iloc[0])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairwise-input", type=Path, default=PAIRWISE_INPUT)
    parser.add_argument("--final-snapshot-input", type=Path, default=FINAL_SNAPSHOT_INPUT)
    parser.add_argument("--state-poll-input", type=Path, default=STATE_POLL_INPUT)
    parser.add_argument(
        "--state-poll-panel-input",
        type=Path,
        default=STATE_POLL_PANEL_INPUT,
    )
    parser.add_argument("--rieke-input", type=Path, default=RIEKE_INPUT)
    parser.add_argument("--popular-vote-input", type=Path, default=POPULAR_VOTE_INPUT)
    parser.add_argument("--two-seventy-input", type=Path, default=TWO_SEVENTY_INPUT)
    parser.add_argument(
        "--two-seventy-poll-average-input",
        type=Path,
        default=TWO_SEVENTY_POLL_AVERAGE_INPUT,
    )
    parser.add_argument("--synthesis-output", type=Path, default=SYNTHESIS_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_forecast_quality_synthesis_outputs(
            pairwise_input=args.pairwise_input,
            final_snapshot_input=args.final_snapshot_input,
            state_poll_input=args.state_poll_input,
            state_poll_panel_input=args.state_poll_panel_input,
            popular_vote_input=args.popular_vote_input,
            rieke_input=args.rieke_input,
            two_seventy_input=args.two_seventy_input,
            two_seventy_poll_average_input=args.two_seventy_poll_average_input,
            synthesis_output=args.synthesis_output,
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
