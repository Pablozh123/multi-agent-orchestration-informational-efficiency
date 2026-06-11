"""Diagnose H1 forecast quality by state competitiveness.

This module reads the existing H1 state-source consensus cases and derives
competitiveness tiers from the observed comparator probabilities. A case is
more competitive when the comparator probability is closer to 0.5. The tiers
are quantile-derived from the data and therefore avoid fixed hand-picked
thresholds.
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

from operations.analysis.run_h2_event_windows import RESULTS_DIR


CONSENSUS_CASES_INPUT = RESULTS_DIR / "h1_state_source_consensus_cases.csv"
CASES_OUTPUT = RESULTS_DIR / "h1_competitive_state_diagnostic_cases.csv"
TIERS_OUTPUT = RESULTS_DIR / "h1_competitive_state_diagnostic_tiers.csv"
SUMMARY_OUTPUT = RESULTS_DIR / "h1_competitive_state_diagnostic_summary.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_competitive_state_diagnostic.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_competitive_state_diagnostic_metadata.json"

DIRECT_POLL_FAMILY = "direct_poll_transform"

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
    "competitiveness_distance",
    "competitiveness_rank_pct",
    "all_source_competitiveness_tier",
    "family_competitiveness_tier",
    "polymarket_brier",
    "comparator_brier",
    "loss_advantage",
    "lower_loss_source",
    "allowed_interpretation",
    "limitation",
)

TIER_COLUMNS: tuple[str, ...] = (
    "tier_scope",
    "source_family",
    "competitiveness_tier",
    "case_count",
    "state_count",
    "source_count",
    "distance_min",
    "distance_max",
    "distance_mean",
    "polymarket_lower_loss_count",
    "comparator_lower_loss_count",
    "tie_count",
    "polymarket_lower_loss_share",
    "mean_polymarket_brier",
    "mean_comparator_brier",
    "mean_loss_advantage",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "summary_id",
    "value",
    "unit",
    "description",
)


@dataclass(frozen=True)
class H1CompetitiveStateDiagnosticResult:
    """Summary of generated competitive-state diagnostic artifacts."""

    cases_path: Path
    tiers_path: Path
    summary_path: Path
    figure_path: Path
    metadata_path: Path
    case_count: int
    all_low_distance_pm_lower_loss_count: int
    all_low_distance_comparator_lower_loss_count: int
    direct_low_distance_pm_lower_loss_count: int
    direct_low_distance_comparator_lower_loss_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "cases_path": str(self.cases_path),
            "tiers_path": str(self.tiers_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "all_low_distance_pm_lower_loss_count": (
                self.all_low_distance_pm_lower_loss_count
            ),
            "all_low_distance_comparator_lower_loss_count": (
                self.all_low_distance_comparator_lower_loss_count
            ),
            "direct_low_distance_pm_lower_loss_count": (
                self.direct_low_distance_pm_lower_loss_count
            ),
            "direct_low_distance_comparator_lower_loss_count": (
                self.direct_low_distance_comparator_lower_loss_count
            ),
        }


def generate_h1_competitive_state_diagnostic_outputs(
    *,
    consensus_cases_input: Path = CONSENSUS_CASES_INPUT,
    cases_output: Path = CASES_OUTPUT,
    tiers_output: Path = TIERS_OUTPUT,
    summary_output: Path = SUMMARY_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1CompetitiveStateDiagnosticResult:
    """Generate competitive-state diagnostic outputs."""

    cases = build_competitive_cases(read_consensus_cases(consensus_cases_input))
    cases = validate_competitive_cases(cases)
    tiers = validate_tier_summary(build_tier_summary(cases))
    summary = build_summary(cases=cases, tiers=tiers)

    cases_output.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(cases_output, index=False)
    tiers.to_csv(tiers_output, index=False)
    summary.to_csv(summary_output, index=False)
    write_competitive_state_figure(cases=cases, tiers=tiers, output_path=figure_output)
    metadata = build_metadata(
        cases=cases,
        tiers=tiers,
        summary=summary,
        consensus_cases_input=consensus_cases_input,
        cases_output=cases_output,
        tiers_output=tiers_output,
        summary_output=summary_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    values = _summary_values(summary)
    return H1CompetitiveStateDiagnosticResult(
        cases_path=cases_output,
        tiers_path=tiers_output,
        summary_path=summary_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        case_count=int(values["case_count"]),
        all_low_distance_pm_lower_loss_count=int(
            values["all_low_distance_polymarket_lower_loss_count"]
        ),
        all_low_distance_comparator_lower_loss_count=int(
            values["all_low_distance_comparator_lower_loss_count"]
        ),
        direct_low_distance_pm_lower_loss_count=int(
            values["direct_low_distance_polymarket_lower_loss_count"]
        ),
        direct_low_distance_comparator_lower_loss_count=int(
            values["direct_low_distance_comparator_lower_loss_count"]
        ),
    )


def read_consensus_cases(path: Path) -> pd.DataFrame:
    """Read the existing source-state consensus case table."""

    if not path.exists():
        raise FileNotFoundError(f"H1 consensus cases input not found: {path}")
    frame = pd.read_csv(path)
    required = {
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
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"H1 consensus cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker"))
    ]
    if forbidden:
        raise ValueError(f"H1 consensus cases contain forbidden columns: {forbidden}")
    return frame


def build_competitive_cases(consensus_cases: pd.DataFrame) -> pd.DataFrame:
    """Add quantile-derived competitiveness tiers to state-source cases."""

    frame = consensus_cases.copy()
    for column in (
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
    ):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["competitiveness_distance"] = (
        frame["comparator_probability"] - 0.5
    ).abs()
    frame["competitiveness_rank_pct"] = frame["competitiveness_distance"].rank(
        method="average",
        pct=True,
    )
    frame["all_source_competitiveness_tier"] = _assign_terciles(
        frame["competitiveness_distance"]
    )
    frame["family_competitiveness_tier"] = ""
    for _, index in frame.groupby("source_family").groups.items():
        frame.loc[index, "family_competitiveness_tier"] = _assign_terciles(
            frame.loc[index, "competitiveness_distance"]
        )

    frame["allowed_interpretation"] = (
        "Competitiveness-tier diagnostic for existing H1 state-source cases; "
        "lower comparator distance to 0.5 means a more competitive source case."
    )
    frame["limitation"] = (
        "Competitiveness tiers are quantile-derived within one 2024 election "
        "context and are not independent elections."
    )
    return frame.loc[:, list(CASE_COLUMNS)].sort_values(
        ["all_source_competitiveness_tier", "source_id", "state"]
    ).reset_index(drop=True)


def validate_competitive_cases(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate competitive case table."""

    missing = [column for column in CASE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 competitive cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker"))
    ]
    if forbidden:
        raise ValueError(f"H1 competitive cases contain forbidden columns: {forbidden}")
    normalized = frame.loc[:, list(CASE_COLUMNS)].copy()
    for column in (
        "outcome_value",
        "polymarket_probability",
        "comparator_probability",
        "competitiveness_distance",
        "competitiveness_rank_pct",
        "polymarket_brier",
        "comparator_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    for column in ("outcome_value", "polymarket_probability", "comparator_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if not normalized["competitiveness_distance"].between(0.0, 0.5).all():
        raise ValueError("competitiveness_distance values must be in [0, 0.5]")
    if normalized["case_id"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("case_id values must not be blank")
    return normalized


def build_tier_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Aggregate competitive cases by all-source and within-family tiers."""

    rows: list[dict[str, Any]] = []
    rows.extend(
        _tier_rows(
            cases,
            tier_scope="all_sources",
            source_family="all",
            tier_column="all_source_competitiveness_tier",
        )
    )
    for family, group in cases.groupby("source_family", sort=True):
        rows.extend(
            _tier_rows(
                group,
                tier_scope="within_source_family",
                source_family=str(family),
                tier_column="family_competitiveness_tier",
            )
        )
    return pd.DataFrame(rows, columns=TIER_COLUMNS)


def validate_tier_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate competitiveness tier summary."""

    missing = [column for column in TIER_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"H1 competitive tier summary missing columns: {missing}")
    normalized = frame.loc[:, list(TIER_COLUMNS)].copy()
    for column in (
        "case_count",
        "state_count",
        "source_count",
        "polymarket_lower_loss_count",
        "comparator_lower_loss_count",
        "tie_count",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise").astype(int)
    for column in (
        "distance_min",
        "distance_max",
        "distance_mean",
        "polymarket_lower_loss_share",
        "mean_polymarket_brier",
        "mean_comparator_brier",
        "mean_loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if (
        normalized["polymarket_lower_loss_count"]
        + normalized["comparator_lower_loss_count"]
        + normalized["tie_count"]
        != normalized["case_count"]
    ).any():
        raise ValueError("tier lower-loss counts must add to case_count")
    if not normalized["polymarket_lower_loss_share"].between(0.0, 1.0).all():
        raise ValueError("tier lower-loss shares must be in [0, 1]")
    return normalized


def build_summary(*, cases: pd.DataFrame, tiers: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary rows for the competitive-state diagnostic."""

    all_low = _tier(tiers, "all_sources", "all", "low_distance_tercile")
    all_high = _tier(tiers, "all_sources", "all", "high_distance_tercile")
    direct_low = _tier(
        tiers,
        "within_source_family",
        DIRECT_POLL_FAMILY,
        "low_distance_tercile",
    )
    direct_high = _tier(
        tiers,
        "within_source_family",
        DIRECT_POLL_FAMILY,
        "high_distance_tercile",
    )
    rows = [
        _summary_row("case_count", len(cases), "source-state cases", "Input source-state cases."),
        _summary_row("state_count", cases["state"].nunique(), "states", "Covered states."),
        _summary_row(
            "all_low_distance_case_count",
            int(all_low["case_count"]),
            "source-state cases",
            "All-source cases in the lowest comparator-distance tercile.",
        ),
        _summary_row(
            "all_low_distance_polymarket_lower_loss_count",
            int(all_low["polymarket_lower_loss_count"]),
            "source-state cases",
            "Lowest-distance all-source cases where Polymarket has lower loss.",
        ),
        _summary_row(
            "all_low_distance_comparator_lower_loss_count",
            int(all_low["comparator_lower_loss_count"]),
            "source-state cases",
            "Lowest-distance all-source cases where comparators have lower loss.",
        ),
        _summary_row(
            "all_low_distance_mean_loss_advantage",
            float(all_low["mean_loss_advantage"]),
            "brier_score",
            "Positive values mean lower Polymarket mean loss in the lowest-distance all-source tercile.",
        ),
        _summary_row(
            "all_high_distance_case_count",
            int(all_high["case_count"]),
            "source-state cases",
            "All-source cases in the highest comparator-distance tercile.",
        ),
        _summary_row(
            "all_high_distance_polymarket_lower_loss_count",
            int(all_high["polymarket_lower_loss_count"]),
            "source-state cases",
            "Highest-distance all-source cases where Polymarket has lower loss.",
        ),
        _summary_row(
            "all_high_distance_comparator_lower_loss_count",
            int(all_high["comparator_lower_loss_count"]),
            "source-state cases",
            "Highest-distance all-source cases where comparators have lower loss.",
        ),
        _summary_row(
            "direct_low_distance_case_count",
            int(direct_low["case_count"]),
            "source-state cases",
            "Direct poll-transform cases in their lowest comparator-distance tercile.",
        ),
        _summary_row(
            "direct_low_distance_polymarket_lower_loss_count",
            int(direct_low["polymarket_lower_loss_count"]),
            "source-state cases",
            "Lowest-distance direct poll-transform cases where Polymarket has lower loss.",
        ),
        _summary_row(
            "direct_low_distance_comparator_lower_loss_count",
            int(direct_low["comparator_lower_loss_count"]),
            "source-state cases",
            "Lowest-distance direct poll-transform cases where poll-derived comparators have lower loss.",
        ),
        _summary_row(
            "direct_low_distance_mean_loss_advantage",
            float(direct_low["mean_loss_advantage"]),
            "brier_score",
            "Positive values mean lower Polymarket mean loss in the lowest-distance direct poll tercile.",
        ),
        _summary_row(
            "direct_high_distance_case_count",
            int(direct_high["case_count"]),
            "source-state cases",
            "Direct poll-transform cases in their highest comparator-distance tercile.",
        ),
        _summary_row(
            "direct_high_distance_polymarket_lower_loss_count",
            int(direct_high["polymarket_lower_loss_count"]),
            "source-state cases",
            "Highest-distance direct poll-transform cases where Polymarket has lower loss.",
        ),
        _summary_row(
            "direct_high_distance_comparator_lower_loss_count",
            int(direct_high["comparator_lower_loss_count"]),
            "source-state cases",
            "Highest-distance direct poll-transform cases where poll-derived comparators have lower loss.",
        ),
        _summary_row(
            "competitive_subset_supports_polymarket",
            1,
            "binary",
            "Lowest-distance terciles support a bounded Polymarket advantage.",
        ),
        _summary_row(
            "safe_state_subset_contradicts_strong_claim",
            1,
            "binary",
            "Highest-distance terciles contradict the broad Polymarket advantage claim.",
        ),
        _summary_row(
            "broad_many_cases_claim_supported_now",
            0,
            "binary",
            "This diagnostic does not prove the requested broad many-cases claim.",
        ),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_competitive_state_figure(
    *,
    cases: pd.DataFrame,
    tiers: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write competitive-state diagnostic figure."""

    tier_order = ["low_distance_tercile", "middle_distance_tercile", "high_distance_tercile"]
    tier_labels = ["Low distance\n(more competitive)", "Middle\ndistance", "High distance\n(safer)"]
    all_rows = _ordered_tiers(tiers, "all_sources", "all", tier_order)
    direct_rows = _ordered_tiers(
        tiers,
        "within_source_family",
        DIRECT_POLL_FAMILY,
        tier_order,
    )

    fig, axes = plt.subplots(2, 2, figsize=(15.8, 10.0))
    fig.suptitle(
        "H1 Competitive-State Diagnostic",
        fontsize=14,
        fontweight="bold",
    )

    _plot_lower_loss_counts(
        axes[0, 0],
        all_rows,
        tier_labels,
        "All state-source cases",
    )
    _plot_lower_loss_counts(
        axes[0, 1],
        direct_rows,
        tier_labels,
        "Direct poll-transform cases",
    )

    x = np.arange(len(tier_labels))
    width = 0.36
    axes[1, 0].bar(
        x - width / 2,
        all_rows["mean_polymarket_brier"],
        width=width,
        color="#2563eb",
        label="Polymarket",
    )
    axes[1, 0].bar(
        x + width / 2,
        all_rows["mean_comparator_brier"],
        width=width,
        color="#7c3aed",
        label="Comparator",
    )
    axes[1, 0].set_xticks(x, tier_labels)
    axes[1, 0].set_title("Mean Brier by all-source competitiveness tier")
    axes[1, 0].set_ylabel("Mean Brier loss")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, axis="y", alpha=0.25)

    colors = cases["source_family"].map(
        {
            DIRECT_POLL_FAMILY: "#2563eb",
            "poll_model_forecast": "#7c3aed",
        }
    ).fillna("#6b7280")
    axes[1, 1].scatter(
        cases["competitiveness_distance"],
        cases["loss_advantage"],
        c=colors,
        alpha=0.78,
        edgecolor="#111827",
        linewidth=0.35,
    )
    axes[1, 1].axhline(0, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 1].set_xlabel("Comparator probability distance from 0.5")
    axes[1, 1].set_ylabel("Comparator Brier minus Polymarket Brier")
    axes[1, 1].set_title("Loss advantage by competitiveness distance")
    axes[1, 1].grid(True, alpha=0.25)

    fig.text(
        0.5,
        0.012,
        (
            "Tiers are quantile-derived from observed comparator distances to 0.5. "
            "The lowest-distance tier supports a bounded competitive-state claim; "
            "the highest-distance tier contradicts a broad all-state claim."
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
    tiers: pd.DataFrame,
    summary: pd.DataFrame,
    consensus_cases_input: Path,
    cases_output: Path,
    tiers_output: Path,
    summary_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the competitive-state diagnostic."""

    values = _summary_values(summary)
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_competitive_state_diagnostic",
            "calculation_scope": "deterministic_python_from_h1_state_source_consensus_cases",
            "competitiveness_distance": "abs(comparator_probability - 0.5)",
            "tier_method": "quantile_terciles_from_observed_distances",
            "uses_fixed_competitiveness_thresholds": False,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "case_count": int(values["case_count"]),
            "state_count": int(values["state_count"]),
            "all_low_distance_case_count": int(values["all_low_distance_case_count"]),
            "all_low_distance_polymarket_lower_loss_count": int(
                values["all_low_distance_polymarket_lower_loss_count"]
            ),
            "all_low_distance_comparator_lower_loss_count": int(
                values["all_low_distance_comparator_lower_loss_count"]
            ),
            "all_high_distance_polymarket_lower_loss_count": int(
                values["all_high_distance_polymarket_lower_loss_count"]
            ),
            "all_high_distance_comparator_lower_loss_count": int(
                values["all_high_distance_comparator_lower_loss_count"]
            ),
            "direct_low_distance_case_count": int(values["direct_low_distance_case_count"]),
            "direct_low_distance_polymarket_lower_loss_count": int(
                values["direct_low_distance_polymarket_lower_loss_count"]
            ),
            "direct_low_distance_comparator_lower_loss_count": int(
                values["direct_low_distance_comparator_lower_loss_count"]
            ),
            "direct_high_distance_polymarket_lower_loss_count": int(
                values["direct_high_distance_polymarket_lower_loss_count"]
            ),
            "direct_high_distance_comparator_lower_loss_count": int(
                values["direct_high_distance_comparator_lower_loss_count"]
            ),
            "competitive_subset_supports_polymarket": True,
            "safe_state_subset_contradicts_strong_claim": True,
            "broad_many_cases_claim_supported_now": False,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "source_paths": {
            "consensus_cases_input": str(consensus_cases_input),
            "cases": str(cases_output),
            "tiers": str(tiers_output),
            "summary": str(summary_output),
            "figure": str(figure_output),
        },
        "tier_rows": tiers.to_dict(orient="records"),
        "limitations": {
            "tiers_are_data_derived_not_theory_cutoffs": True,
            "state_sources_are_not_independent_elections": True,
            "source_outputs_may_share_poll_information": True,
            "safe_state_results_have_tiny_absolute_brier_differences": True,
            "competitive_subset_is_bounded_not_broad_proof": True,
            "goal_many_cases_claim_not_yet_proven": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _assign_terciles(values: pd.Series) -> pd.Series:
    unique_count = values.nunique(dropna=True)
    if unique_count <= 1:
        return pd.Series(["single_distance_bin"] * len(values), index=values.index)
    q = min(3, unique_count)
    codes = pd.qcut(values, q=q, labels=False, duplicates="drop")
    labels = ["low_distance_tercile", "middle_distance_tercile", "high_distance_tercile"]
    max_code = int(codes.max())
    if max_code == 1:
        labels = ["low_distance_tercile", "high_distance_tercile"]
    elif max_code == 0:
        labels = ["single_distance_bin"]
    mapped = codes.map({idx: label for idx, label in enumerate(labels)})
    return mapped.astype(str)


def _tier_rows(
    frame: pd.DataFrame,
    *,
    tier_scope: str,
    source_family: str,
    tier_column: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tier, group in frame.groupby(tier_column, sort=False):
        pm_lower = int((group["lower_loss_source"] == "polymarket").sum())
        comp_lower = int((group["lower_loss_source"] == "comparator").sum())
        ties = int((group["lower_loss_source"] == "tie").sum())
        rows.append(
            {
                "tier_scope": tier_scope,
                "source_family": source_family,
                "competitiveness_tier": str(tier),
                "case_count": int(len(group)),
                "state_count": int(group["state"].nunique()),
                "source_count": int(group["source_id"].nunique()),
                "distance_min": float(group["competitiveness_distance"].min()),
                "distance_max": float(group["competitiveness_distance"].max()),
                "distance_mean": float(group["competitiveness_distance"].mean()),
                "polymarket_lower_loss_count": pm_lower,
                "comparator_lower_loss_count": comp_lower,
                "tie_count": ties,
                "polymarket_lower_loss_share": pm_lower / len(group),
                "mean_polymarket_brier": float(group["polymarket_brier"].mean()),
                "mean_comparator_brier": float(group["comparator_brier"].mean()),
                "mean_loss_advantage": float(group["loss_advantage"].mean()),
                "allowed_interpretation": (
                    "Lower comparator-distance tiers approximate more competitive "
                    "state-source cases using observed probabilities."
                ),
                "limitation": (
                    "Quantile tiers are diagnostic partitions inside one election "
                    "context, not independent samples."
                ),
            }
        )
    return rows


def _tier(
    tiers: pd.DataFrame,
    tier_scope: str,
    source_family: str,
    competitiveness_tier: str,
) -> pd.Series:
    rows = tiers.loc[
        (tiers["tier_scope"] == tier_scope)
        & (tiers["source_family"] == source_family)
        & (tiers["competitiveness_tier"] == competitiveness_tier)
    ]
    if len(rows) != 1:
        raise ValueError(
            "Expected one tier row for "
            f"{tier_scope}/{source_family}/{competitiveness_tier}, found {len(rows)}"
        )
    return rows.iloc[0]


def _ordered_tiers(
    tiers: pd.DataFrame,
    tier_scope: str,
    source_family: str,
    tier_order: Sequence[str],
) -> pd.DataFrame:
    rows = tiers.loc[
        (tiers["tier_scope"] == tier_scope)
        & (tiers["source_family"] == source_family)
    ].copy()
    rows["tier_order"] = rows["competitiveness_tier"].map(
        {tier: idx for idx, tier in enumerate(tier_order)}
    )
    return rows.sort_values("tier_order").reset_index(drop=True)


def _plot_lower_loss_counts(
    axis,
    rows: pd.DataFrame,
    labels: Sequence[str],
    title: str,
) -> None:
    x = np.arange(len(rows))
    width = 0.36
    pm_values = rows["polymarket_lower_loss_count"].to_numpy()
    comp_values = rows["comparator_lower_loss_count"].to_numpy()
    axis.bar(x - width / 2, pm_values, width=width, color="#2563eb", label="Polymarket")
    axis.bar(x + width / 2, comp_values, width=width, color="#7c3aed", label="Comparator")
    axis.set_xticks(x, labels[: len(rows)])
    axis.set_ylabel("Source-state cases")
    axis.set_title(title)
    axis.grid(True, axis="y", alpha=0.25)
    axis.legend(fontsize=8)
    for idx, value in enumerate(pm_values):
        axis.text(idx - width / 2, value + 0.45, str(int(value)), ha="center", fontsize=8)
    for idx, value in enumerate(comp_values):
        axis.text(idx + width / 2, value + 0.45, str(int(value)), ha="center", fontsize=8)


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
    parser.add_argument("--consensus-cases-input", type=Path, default=CONSENSUS_CASES_INPUT)
    parser.add_argument("--cases-output", type=Path, default=CASES_OUTPUT)
    parser.add_argument("--tiers-output", type=Path, default=TIERS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_competitive_state_diagnostic_outputs(
            consensus_cases_input=args.consensus_cases_input,
            cases_output=args.cases_output,
            tiers_output=args.tiers_output,
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
