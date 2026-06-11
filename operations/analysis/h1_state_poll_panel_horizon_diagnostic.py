"""Diagnose H1 state-date poll panel quality by forecast horizon.

This module derives time-to-election bins from the existing state-date poll
panel. It keeps the full-panel result visible while testing whether Polymarket
performs better closer to the resolved election date.
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

from operations.analysis.h1_state_poll_panel_temporal_diagnostic import read_panel_cases
from operations.analysis.run_h2_event_windows import RESULTS_DIR


CASE_INPUT = RESULTS_DIR / "h1_state_poll_panel_cases.csv"
HORIZON_SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_summary.csv"
STATE_HORIZON_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_state_summary.csv"
CLAIM_AUDIT_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_claim_audit.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_diagnostic.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_horizon_diagnostic_metadata.json"

ELECTION_DATE = "2024-11-05"
NEAR_HORIZON_MAX_DAYS = 90

HORIZON_BINS: tuple[tuple[int, int, str, str], ...] = (
    (181, 10_000, "181_plus_days", "181+ days"),
    (151, 180, "151_180_days", "151-180 days"),
    (121, 150, "121_150_days", "121-150 days"),
    (91, 120, "91_120_days", "91-120 days"),
    (61, 90, "61_90_days", "61-90 days"),
    (0, 60, "0_60_days", "0-60 days"),
)

HORIZON_SUMMARY_COLUMNS: tuple[str, ...] = (
    "horizon_bin",
    "horizon_label",
    "min_days_to_election",
    "max_days_to_election",
    "first_forecast_date",
    "last_forecast_date",
    "row_count",
    "state_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
    "row_unit",
    "limitation",
)

STATE_HORIZON_COLUMNS: tuple[str, ...] = (
    "state",
    "horizon_bin",
    "horizon_label",
    "row_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
)

CLAIM_AUDIT_COLUMNS: tuple[str, ...] = (
    "audit_scope",
    "included_horizon_bins",
    "row_count",
    "state_count",
    "polymarket_lower_loss_count",
    "poll_derived_lower_loss_count",
    "tie_count",
    "polymarket_better_share",
    "mean_polymarket_brier",
    "mean_poll_derived_brier",
    "mean_loss_advantage",
    "aggregate_mean_supports_polymarket",
    "majority_rows_support_polymarket",
    "allowed_interpretation",
    "limitation",
)


@dataclass(frozen=True)
class H1StatePollPanelHorizonResult:
    """Summary of generated horizon diagnostic artifacts."""

    horizon_summary_path: Path
    state_horizon_path: Path
    claim_audit_path: Path
    figure_path: Path
    metadata_path: Path
    horizon_bin_count: int
    row_count: int
    within_90_row_count: int
    within_90_pm_lower_loss_count: int
    within_90_poll_lower_loss_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "horizon_summary_path": str(self.horizon_summary_path),
            "state_horizon_path": str(self.state_horizon_path),
            "claim_audit_path": str(self.claim_audit_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "horizon_bin_count": self.horizon_bin_count,
            "row_count": self.row_count,
            "within_90_row_count": self.within_90_row_count,
            "within_90_pm_lower_loss_count": self.within_90_pm_lower_loss_count,
            "within_90_poll_lower_loss_count": self.within_90_poll_lower_loss_count,
        }


def generate_h1_state_poll_panel_horizon_outputs(
    *,
    case_input: Path = CASE_INPUT,
    horizon_summary_output: Path = HORIZON_SUMMARY_OUTPUT,
    state_horizon_output: Path = STATE_HORIZON_OUTPUT,
    claim_audit_output: Path = CLAIM_AUDIT_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StatePollPanelHorizonResult:
    """Generate horizon summary, claim audit, figure, and metadata."""

    cases = add_horizon_columns(read_panel_cases(case_input))
    horizon_summary = build_horizon_summary(cases)
    state_horizon = build_state_horizon_summary(cases)
    claim_audit = build_claim_audit(cases)

    horizon_summary_output.parent.mkdir(parents=True, exist_ok=True)
    horizon_summary.to_csv(horizon_summary_output, index=False)
    state_horizon.to_csv(state_horizon_output, index=False)
    claim_audit.to_csv(claim_audit_output, index=False)
    write_horizon_figure(
        horizon_summary=horizon_summary,
        claim_audit=claim_audit,
        output_path=figure_output,
    )
    metadata = build_metadata(
        cases=cases,
        horizon_summary=horizon_summary,
        claim_audit=claim_audit,
        case_input=case_input,
        horizon_summary_output=horizon_summary_output,
        state_horizon_output=state_horizon_output,
        claim_audit_output=claim_audit_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    within_90 = _claim_row(claim_audit, "within_90_days_before_election")
    return H1StatePollPanelHorizonResult(
        horizon_summary_path=horizon_summary_output,
        state_horizon_path=state_horizon_output,
        claim_audit_path=claim_audit_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        horizon_bin_count=int(len(horizon_summary)),
        row_count=int(len(cases)),
        within_90_row_count=int(within_90["row_count"]),
        within_90_pm_lower_loss_count=int(within_90["polymarket_lower_loss_count"]),
        within_90_poll_lower_loss_count=int(within_90["poll_derived_lower_loss_count"]),
    )


def add_horizon_columns(cases: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic election-horizon columns to validated case rows."""

    frame = cases.copy()
    frame["forecast_date"] = pd.to_datetime(frame["forecast_date"], errors="raise")
    election_date = pd.Timestamp(ELECTION_DATE)
    frame["days_to_election"] = (election_date - frame["forecast_date"]).dt.days
    if (frame["days_to_election"] < 0).any():
        raise ValueError("forecast_date must not be after election date")
    labels = frame["days_to_election"].map(_horizon_for_days)
    frame["horizon_bin"] = labels.map(lambda item: item[0])
    frame["horizon_label"] = labels.map(lambda item: item[1])
    return frame


def build_horizon_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build forecast-horizon summary rows."""

    rows: list[dict[str, Any]] = []
    for lower, upper, horizon_bin, label in HORIZON_BINS:
        group = cases.loc[cases["horizon_bin"] == horizon_bin]
        if group.empty:
            continue
        rows.append(
            _summary_for_group(
                group,
                extra={
                    "horizon_bin": horizon_bin,
                    "horizon_label": label,
                    "min_days_to_election": lower,
                    "max_days_to_election": upper if upper < 10_000 else "",
                    "first_forecast_date": _format_date(group["forecast_date"].min()),
                    "last_forecast_date": _format_date(group["forecast_date"].max()),
                    "row_unit": "state_date_forecast_pair",
                    "limitation": (
                        "Horizon rows repeat resolved state outcomes; they are "
                        "forecast rows, not independent elections."
                    ),
                },
                columns=HORIZON_SUMMARY_COLUMNS,
            )
        )
    return pd.DataFrame(rows, columns=HORIZON_SUMMARY_COLUMNS)


def build_state_horizon_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build state-by-horizon diagnostics."""

    rows = [
        _summary_for_group(
            group,
            extra={
                "state": state,
                "horizon_bin": horizon_bin,
                "horizon_label": str(group["horizon_label"].iloc[0]),
            },
            columns=STATE_HORIZON_COLUMNS,
        )
        for (state, horizon_bin), group in cases.groupby(["state", "horizon_bin"], sort=True)
    ]
    return pd.DataFrame(rows, columns=STATE_HORIZON_COLUMNS)


def build_claim_audit(cases: pd.DataFrame) -> pd.DataFrame:
    """Build full-panel versus forecast-horizon claim rows."""

    near = cases.loc[cases["days_to_election"] <= NEAR_HORIZON_MAX_DAYS]
    far = cases.loc[cases["days_to_election"] > NEAR_HORIZON_MAX_DAYS]
    rows = [
        _claim_audit_row(
            "full_panel",
            cases,
            allowed_interpretation=(
                "Main repeated state-date panel across all available horizons."
            ),
            limitation=(
                "Rows repeat resolved state outcomes and do not prove a broad "
                "independent many-cases claim."
            ),
        ),
        _claim_audit_row(
            "within_90_days_before_election",
            near,
            allowed_interpretation=(
                "Forecast rows from the final 90 days available in the preserved "
                "538 average file."
            ),
            limitation=(
                "A predeclared horizon diagnostic, but still repeated rows from "
                "one election context."
            ),
        ),
        _claim_audit_row(
            "more_than_90_days_before_election",
            far,
            allowed_interpretation=(
                "Forecast rows more than 90 days before election day."
            ),
            limitation=(
                "Shows the early-horizon counterweight to the late Polymarket "
                "advantage."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=CLAIM_AUDIT_COLUMNS)


def write_horizon_figure(
    *,
    horizon_summary: pd.DataFrame,
    claim_audit: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write the horizon diagnostic figure."""

    labels = horizon_summary["horizon_label"].astype(str).tolist()
    x = range(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=(14.4, 9.0))
    fig.suptitle(
        "H1 State-Date Poll Panel Forecast-Horizon Diagnostic",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].plot(
        x,
        horizon_summary["mean_polymarket_brier"],
        marker="o",
        linewidth=2,
        color="#2563eb",
        label="Polymarket",
    )
    axes[0, 0].plot(
        x,
        horizon_summary["mean_poll_derived_brier"],
        marker="o",
        linewidth=2,
        color="#7c3aed",
        label="538 poll-derived",
    )
    axes[0, 0].set_xticks(list(x), labels, rotation=25, ha="right")
    axes[0, 0].set_ylabel("Mean Brier loss")
    axes[0, 0].set_title("Mean loss by days before election")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, alpha=0.25)

    axes[0, 1].bar(
        labels,
        horizon_summary["polymarket_lower_loss_count"],
        color="#2563eb",
        label="PM lower",
    )
    axes[0, 1].bar(
        labels,
        horizon_summary["poll_derived_lower_loss_count"],
        bottom=horizon_summary["polymarket_lower_loss_count"],
        color="#7c3aed",
        label="Poll lower",
    )
    axes[0, 1].set_title("Lower-loss row counts by horizon")
    axes[0, 1].set_ylabel("State-date rows")
    axes[0, 1].tick_params(axis="x", rotation=25)
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, axis="y", alpha=0.25)

    axes[1, 0].plot(
        x,
        horizon_summary["polymarket_better_share"],
        marker="o",
        linewidth=2,
        color="#0f766e",
    )
    axes[1, 0].axhline(0.5, color="#6b7280", linestyle="--", linewidth=1.0)
    axes[1, 0].set_xticks(list(x), labels, rotation=25, ha="right")
    axes[1, 0].set_ylim(0, 1.02)
    axes[1, 0].set_ylabel("PM lower-loss share")
    axes[1, 0].set_title("Polymarket row-majority threshold")
    axes[1, 0].grid(True, alpha=0.25)
    for idx, value in enumerate(horizon_summary["polymarket_better_share"]):
        axes[1, 0].text(idx, value + 0.035, f"{value:.2f}", ha="center", fontsize=8)

    audit = claim_audit.set_index("audit_scope")
    audit_keys = [
        "full_panel",
        "within_90_days_before_election",
        "more_than_90_days_before_election",
    ]
    audit_labels = ["Full panel", "<=90 days", ">90 days"]
    pm_counts = [audit.loc[key, "polymarket_lower_loss_count"] for key in audit_keys]
    poll_counts = [audit.loc[key, "poll_derived_lower_loss_count"] for key in audit_keys]
    axes[1, 1].bar(audit_labels, pm_counts, color="#2563eb", label="PM lower")
    axes[1, 1].bar(audit_labels, poll_counts, bottom=pm_counts, color="#7c3aed", label="Poll lower")
    axes[1, 1].set_title("Claim-audit row counts")
    axes[1, 1].set_ylabel("State-date rows")
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, axis="y", alpha=0.25)
    for idx, key in enumerate(audit_keys):
        row = audit.loc[key]
        axes[1, 1].text(
            idx,
            row["row_count"] + max(audit["row_count"]) * 0.018,
            f"{int(row['polymarket_lower_loss_count'])}/{int(row['row_count'])}",
            ha="center",
            fontsize=8,
        )

    fig.text(
        0.5,
        0.012,
        (
            "Horizon bins are repeated forecast rows. The <=90-day window "
            "supports Polymarket, while the full panel does not."
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
    horizon_summary: pd.DataFrame,
    claim_audit: pd.DataFrame,
    case_input: Path,
    horizon_summary_output: Path,
    state_horizon_output: Path,
    claim_audit_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the horizon diagnostic."""

    full_panel = _claim_row(claim_audit, "full_panel")
    within_90 = _claim_row(claim_audit, "within_90_days_before_election")
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_horizon_diagnostic",
            "calculation_scope": "deterministic_python_from_state_date_poll_panel_cases",
            "election_date": ELECTION_DATE,
            "near_horizon_max_days": NEAR_HORIZON_MAX_DAYS,
            "horizon_bins": [
                {
                    "min_days_to_election": lower,
                    "max_days_to_election": upper,
                    "horizon_bin": horizon_bin,
                    "horizon_label": label,
                }
                for lower, upper, horizon_bin, label in HORIZON_BINS
            ],
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "rcp_included": False,
            "uses_raw_poll_shares_directly": False,
        },
        "outputs": {
            "row_count": int(len(cases)),
            "state_count": int(cases["state"].nunique()),
            "horizon_bin_count": int(len(horizon_summary)),
            "full_panel_polymarket_lower_loss_count": int(
                full_panel["polymarket_lower_loss_count"]
            ),
            "full_panel_poll_derived_lower_loss_count": int(
                full_panel["poll_derived_lower_loss_count"]
            ),
            "full_panel_mean_polymarket_brier": float(full_panel["mean_polymarket_brier"]),
            "full_panel_mean_poll_derived_brier": float(full_panel["mean_poll_derived_brier"]),
            "within_90_row_count": int(within_90["row_count"]),
            "within_90_state_count": int(within_90["state_count"]),
            "within_90_polymarket_lower_loss_count": int(
                within_90["polymarket_lower_loss_count"]
            ),
            "within_90_poll_derived_lower_loss_count": int(
                within_90["poll_derived_lower_loss_count"]
            ),
            "within_90_mean_polymarket_brier": float(within_90["mean_polymarket_brier"]),
            "within_90_mean_poll_derived_brier": float(within_90["mean_poll_derived_brier"]),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "h1_goal_completion_status": "not_proven",
        },
        "source_paths": {
            "case_input": str(case_input),
            "horizon_summary": str(horizon_summary_output),
            "state_horizon": str(state_horizon_output),
            "claim_audit": str(claim_audit_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "panel_rows_are_repeated_forecasts": True,
            "within_90_days_is_horizon_diagnostic_subset": True,
            "does_not_prove_broad_independent_many_cases_claim": True,
            "no_causal_or_tradeability_claim": True,
        },
    }


def _summary_for_group(
    group: pd.DataFrame,
    *,
    extra: dict[str, Any],
    columns: tuple[str, ...],
) -> dict[str, Any]:
    counts = group["lower_loss_source"].value_counts()
    pm_lower = int(counts.get("polymarket", 0))
    poll_lower = int(counts.get("poll_derived_forecast", 0))
    ties = int(counts.get("tie", 0))
    row_count = int(len(group))
    mean_pm = float(group["polymarket_brier"].mean())
    mean_poll = float(group["poll_derived_brier"].mean())
    row = {
        **extra,
        "row_count": row_count,
        "state_count": int(group["state"].nunique()),
        "polymarket_lower_loss_count": pm_lower,
        "poll_derived_lower_loss_count": poll_lower,
        "tie_count": ties,
        "polymarket_better_share": pm_lower / row_count if row_count else 0.0,
        "mean_polymarket_brier": mean_pm,
        "mean_poll_derived_brier": mean_poll,
        "mean_loss_advantage": mean_poll - mean_pm,
        "aggregate_mean_supports_polymarket": bool(mean_pm < mean_poll),
        "majority_rows_support_polymarket": bool(
            pm_lower > poll_lower and pm_lower > row_count / 2.0
        ),
    }
    return {column: row.get(column, "") for column in columns}


def _claim_audit_row(
    audit_scope: str,
    group: pd.DataFrame,
    *,
    allowed_interpretation: str,
    limitation: str,
) -> dict[str, Any]:
    base = _summary_for_group(
        group,
        extra={},
        columns=tuple(
            column
            for column in CLAIM_AUDIT_COLUMNS
            if column
            not in {
                "audit_scope",
                "included_horizon_bins",
                "allowed_interpretation",
                "limitation",
            }
        ),
    )
    horizons = sorted(
        group["horizon_bin"].astype(str).unique(),
        key=_horizon_sort_key,
    )
    row = {
        "audit_scope": audit_scope,
        "included_horizon_bins": ",".join(horizons),
        **base,
        "allowed_interpretation": allowed_interpretation,
        "limitation": limitation,
    }
    return {column: row.get(column, "") for column in CLAIM_AUDIT_COLUMNS}


def _claim_row(claim_audit: pd.DataFrame, audit_scope: str) -> pd.Series:
    rows = claim_audit.loc[claim_audit["audit_scope"] == audit_scope]
    if len(rows) != 1:
        raise ValueError(f"claim audit must contain one {audit_scope!r} row")
    return rows.iloc[0]


def _horizon_for_days(days_to_election: int) -> tuple[str, str]:
    for lower, upper, horizon_bin, label in HORIZON_BINS:
        if lower <= int(days_to_election) <= upper:
            return horizon_bin, label
    raise ValueError(f"days_to_election out of supported range: {days_to_election}")


def _horizon_sort_key(horizon_bin: str) -> int:
    order = {item[2]: index for index, item in enumerate(HORIZON_BINS)}
    return order[horizon_bin]


def _format_date(value: Any) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument("--horizon-summary-output", type=Path, default=HORIZON_SUMMARY_OUTPUT)
    parser.add_argument("--state-horizon-output", type=Path, default=STATE_HORIZON_OUTPUT)
    parser.add_argument("--claim-audit-output", type=Path, default=CLAIM_AUDIT_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_horizon_outputs(
            case_input=args.case_input,
            horizon_summary_output=args.horizon_summary_output,
            state_horizon_output=args.state_horizon_output,
            claim_audit_output=args.claim_audit_output,
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
