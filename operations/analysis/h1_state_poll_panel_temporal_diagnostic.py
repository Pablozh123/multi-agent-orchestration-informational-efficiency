"""Diagnose temporal structure in the H1 state-date poll panel.

The state-date poll panel is large, but its rows repeat the same resolved
state outcomes across dates. This module keeps that limitation explicit while
showing whether Polymarket's forecast-quality advantage appears only in
specific months of the available 538 poll-average window.
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


CASE_INPUT = RESULTS_DIR / "h1_state_poll_panel_cases.csv"
TEMPORAL_SUMMARY_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_temporal_summary.csv"
STATE_MONTH_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_temporal_state_month.csv"
CLAIM_AUDIT_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_temporal_claim_audit.csv"
FIGURE_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_temporal_diagnostic.png"
METADATA_OUTPUT = RESULTS_DIR / "h1_state_poll_panel_temporal_diagnostic_metadata.json"

REQUIRED_CASE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "state",
    "forecast_date",
    "outcome_value",
    "polymarket_probability",
    "poll_derived_probability",
    "polymarket_brier",
    "poll_derived_brier",
    "loss_advantage",
    "lower_loss_source",
)

TEMPORAL_SUMMARY_COLUMNS: tuple[str, ...] = (
    "forecast_month",
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

STATE_MONTH_COLUMNS: tuple[str, ...] = (
    "state",
    "forecast_month",
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
    "included_months",
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
class H1StatePollPanelTemporalResult:
    """Summary of generated temporal diagnostic artifacts."""

    temporal_summary_path: Path
    state_month_path: Path
    claim_audit_path: Path
    figure_path: Path
    metadata_path: Path
    month_count: int
    row_count: int
    polymarket_supporting_month_count: int
    polymarket_supporting_row_count: int
    polymarket_supporting_pm_lower_loss_count: int
    polymarket_supporting_poll_lower_loss_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "temporal_summary_path": str(self.temporal_summary_path),
            "state_month_path": str(self.state_month_path),
            "claim_audit_path": str(self.claim_audit_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "month_count": self.month_count,
            "row_count": self.row_count,
            "polymarket_supporting_month_count": self.polymarket_supporting_month_count,
            "polymarket_supporting_row_count": self.polymarket_supporting_row_count,
            "polymarket_supporting_pm_lower_loss_count": (
                self.polymarket_supporting_pm_lower_loss_count
            ),
            "polymarket_supporting_poll_lower_loss_count": (
                self.polymarket_supporting_poll_lower_loss_count
            ),
        }


def generate_h1_state_poll_panel_temporal_outputs(
    *,
    case_input: Path = CASE_INPUT,
    temporal_summary_output: Path = TEMPORAL_SUMMARY_OUTPUT,
    state_month_output: Path = STATE_MONTH_OUTPUT,
    claim_audit_output: Path = CLAIM_AUDIT_OUTPUT,
    figure_output: Path = FIGURE_OUTPUT,
    metadata_output: Path = METADATA_OUTPUT,
) -> H1StatePollPanelTemporalResult:
    """Generate temporal summary, claim audit, figure, and metadata."""

    cases = read_panel_cases(case_input)
    temporal_summary = build_temporal_summary(cases)
    state_month = build_state_month_summary(cases)
    claim_audit = build_claim_audit(cases, temporal_summary)

    temporal_summary_output.parent.mkdir(parents=True, exist_ok=True)
    temporal_summary.to_csv(temporal_summary_output, index=False)
    state_month.to_csv(state_month_output, index=False)
    claim_audit.to_csv(claim_audit_output, index=False)
    write_temporal_figure(
        temporal_summary=temporal_summary,
        state_month=state_month,
        claim_audit=claim_audit,
        output_path=figure_output,
    )
    metadata = build_metadata(
        cases=cases,
        temporal_summary=temporal_summary,
        claim_audit=claim_audit,
        case_input=case_input,
        temporal_summary_output=temporal_summary_output,
        state_month_output=state_month_output,
        claim_audit_output=claim_audit_output,
        figure_output=figure_output,
    )
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    supporting = _claim_row(claim_audit, "polymarket_supporting_months")
    return H1StatePollPanelTemporalResult(
        temporal_summary_path=temporal_summary_output,
        state_month_path=state_month_output,
        claim_audit_path=claim_audit_output,
        figure_path=figure_output,
        metadata_path=metadata_output,
        month_count=int(len(temporal_summary)),
        row_count=int(len(cases)),
        polymarket_supporting_month_count=int(
            temporal_summary["aggregate_mean_supports_polymarket"].sum()
        ),
        polymarket_supporting_row_count=int(supporting["row_count"]),
        polymarket_supporting_pm_lower_loss_count=int(
            supporting["polymarket_lower_loss_count"]
        ),
        polymarket_supporting_poll_lower_loss_count=int(
            supporting["poll_derived_lower_loss_count"]
        ),
    )


def read_panel_cases(path: Path) -> pd.DataFrame:
    """Read and validate state-date poll panel case rows."""

    if not path.exists():
        raise FileNotFoundError(f"H1 state poll panel cases not found: {path}")
    frame = pd.read_csv(path)
    missing = sorted(set(REQUIRED_CASE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"panel cases missing columns: {missing}")
    forbidden = [
        column
        for column in frame.columns
        if any(token in column.lower() for token in ("wallet", "maker", "taker", "address"))
    ]
    if forbidden:
        raise ValueError(f"panel cases contain forbidden raw-trade columns: {forbidden}")
    normalized = frame.loc[:, list(REQUIRED_CASE_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("panel cases must not be empty")
    normalized["forecast_date"] = pd.to_datetime(
        normalized["forecast_date"],
        errors="raise",
    )
    for column in (
        "outcome_value",
        "polymarket_probability",
        "poll_derived_probability",
        "polymarket_brier",
        "poll_derived_brier",
        "loss_advantage",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if not normalized["outcome_value"].isin([0.0, 1.0]).all():
        raise ValueError("outcome values must be binary")
    for column in ("polymarket_probability", "poll_derived_probability"):
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be in [0, 1]")
    if normalized["case_id"].duplicated().any():
        raise ValueError("panel case IDs must be unique")
    expected_pm = (normalized["polymarket_probability"] - normalized["outcome_value"]) ** 2
    expected_poll = (normalized["poll_derived_probability"] - normalized["outcome_value"]) ** 2
    if not normalized["polymarket_brier"].sub(expected_pm).abs().le(1e-12).all():
        raise ValueError("polymarket_brier must equal squared forecast error")
    if not normalized["poll_derived_brier"].sub(expected_poll).abs().le(1e-12).all():
        raise ValueError("poll_derived_brier must equal squared forecast error")
    return normalized.sort_values(["forecast_date", "state"]).reset_index(drop=True)


def build_temporal_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build month-level state-date panel summary rows."""

    frame = _with_forecast_month(cases)
    rows = [
        _summary_for_group(
            group,
            extra={
                "forecast_month": month,
                "first_forecast_date": _format_date(group["forecast_date"].min()),
                "last_forecast_date": _format_date(group["forecast_date"].max()),
                "row_unit": "state_date_forecast_pair",
                "limitation": (
                    "Monthly rows are repeated forecasts for resolved state outcomes, "
                    "not independent elections."
                ),
            },
            columns=TEMPORAL_SUMMARY_COLUMNS,
        )
        for month, group in frame.groupby("forecast_month", sort=True)
    ]
    return pd.DataFrame(rows, columns=TEMPORAL_SUMMARY_COLUMNS)


def build_state_month_summary(cases: pd.DataFrame) -> pd.DataFrame:
    """Build state-by-month mean-loss diagnostics."""

    frame = _with_forecast_month(cases)
    rows = [
        _summary_for_group(
            group,
            extra={"state": state, "forecast_month": month},
            columns=STATE_MONTH_COLUMNS,
        )
        for (state, month), group in frame.groupby(["state", "forecast_month"], sort=True)
    ]
    return pd.DataFrame(rows, columns=STATE_MONTH_COLUMNS)


def build_claim_audit(cases: pd.DataFrame, temporal_summary: pd.DataFrame) -> pd.DataFrame:
    """Build a compact audit separating full-panel and supporting-month claims."""

    supporting_months = temporal_summary.loc[
        temporal_summary["aggregate_mean_supports_polymarket"]
        & temporal_summary["majority_rows_support_polymarket"],
        "forecast_month",
    ].astype(str)
    frame = _with_forecast_month(cases)
    support_cases = frame.loc[frame["forecast_month"].isin(set(supporting_months))]
    non_support_cases = frame.loc[~frame["forecast_month"].isin(set(supporting_months))]

    rows = [
        _claim_audit_row(
            "full_panel",
            frame,
            allowed_interpretation=(
                "Full repeated state-date panel; this is the main panel-level "
                "Polymarket-vs-poll-derived comparison."
            ),
            limitation=(
                "Rows repeat 15 resolved state outcomes and do not prove broad "
                "independent many-case support."
            ),
        ),
        _claim_audit_row(
            "polymarket_supporting_months",
            support_cases,
            allowed_interpretation=(
                "Subset of months where both aggregate mean Brier and the row "
                "majority favor Polymarket."
            ),
            limitation=(
                "Conditioned on observed monthly support; useful diagnostic, "
                "not standalone proof of the broad H1 claim."
            ),
        ),
        _claim_audit_row(
            "non_supporting_months",
            non_support_cases,
            allowed_interpretation=(
                "Complement of the Polymarket-supporting monthly windows."
            ),
            limitation=(
                "Shows why the full panel can contradict the late-window "
                "Polymarket advantage."
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=CLAIM_AUDIT_COLUMNS)


def write_temporal_figure(
    *,
    temporal_summary: pd.DataFrame,
    state_month: pd.DataFrame,
    claim_audit: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Write a temporal diagnostic figure for the state-date poll panel."""

    months = temporal_summary["forecast_month"].astype(str).tolist()
    x = range(len(months))
    fig, axes = plt.subplots(2, 2, figsize=(14.4, 9.2))
    fig.suptitle(
        "H1 State-Date Poll Panel Temporal Diagnostic",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].plot(
        x,
        temporal_summary["mean_polymarket_brier"],
        marker="o",
        linewidth=2,
        color="#2563eb",
        label="Polymarket",
    )
    axes[0, 0].plot(
        x,
        temporal_summary["mean_poll_derived_brier"],
        marker="o",
        linewidth=2,
        color="#7c3aed",
        label="538 poll-derived",
    )
    axes[0, 0].set_xticks(list(x), months, rotation=30, ha="right")
    axes[0, 0].set_ylabel("Mean Brier loss")
    axes[0, 0].set_title("Monthly mean loss")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, alpha=0.25)

    axes[0, 1].bar(
        months,
        temporal_summary["polymarket_lower_loss_count"],
        color="#2563eb",
        label="PM lower",
    )
    axes[0, 1].bar(
        months,
        temporal_summary["poll_derived_lower_loss_count"],
        bottom=temporal_summary["polymarket_lower_loss_count"],
        color="#7c3aed",
        label="Poll lower",
    )
    axes[0, 1].bar(
        months,
        temporal_summary["tie_count"],
        bottom=(
            temporal_summary["polymarket_lower_loss_count"]
            + temporal_summary["poll_derived_lower_loss_count"]
        ),
        color="#9ca3af",
        label="Tie",
    )
    axes[0, 1].tick_params(axis="x", rotation=30)
    axes[0, 1].set_title("Lower-loss row counts by month")
    axes[0, 1].set_ylabel("State-date rows")
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, axis="y", alpha=0.25)

    heatmap = state_month.pivot(
        index="state",
        columns="forecast_month",
        values="mean_loss_advantage",
    ).sort_index()
    vmax = max(abs(float(heatmap.min().min())), abs(float(heatmap.max().max())), 0.01)
    image = axes[1, 0].imshow(
        heatmap.to_numpy(),
        aspect="auto",
        cmap="RdBu",
        vmin=-vmax,
        vmax=vmax,
    )
    axes[1, 0].set_xticks(range(len(heatmap.columns)), heatmap.columns, rotation=30, ha="right")
    axes[1, 0].set_yticks(range(len(heatmap.index)), heatmap.index)
    axes[1, 0].set_title("State-month mean loss advantage")
    axes[1, 0].set_xlabel("Forecast month")
    fig.colorbar(image, ax=axes[1, 0], fraction=0.046, pad=0.04)

    audit = claim_audit.set_index("audit_scope")
    audit_labels = ["Full panel", "PM-support months", "Other months"]
    audit_keys = ["full_panel", "polymarket_supporting_months", "non_supporting_months"]
    pm_counts = [audit.loc[key, "polymarket_lower_loss_count"] for key in audit_keys]
    poll_counts = [audit.loc[key, "poll_derived_lower_loss_count"] for key in audit_keys]
    axes[1, 1].bar(audit_labels, pm_counts, color="#2563eb", label="PM lower")
    axes[1, 1].bar(audit_labels, poll_counts, bottom=pm_counts, color="#7c3aed", label="Poll lower")
    axes[1, 1].set_title("Claim-audit row counts")
    axes[1, 1].set_ylabel("State-date rows")
    axes[1, 1].tick_params(axis="x", rotation=18)
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
            "Positive loss advantage means lower Polymarket Brier. "
            "Supporting months are diagnostic subsets, not independent elections."
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
    temporal_summary: pd.DataFrame,
    claim_audit: pd.DataFrame,
    case_input: Path,
    temporal_summary_output: Path,
    state_month_output: Path,
    claim_audit_output: Path,
    figure_output: Path,
) -> dict[str, Any]:
    """Build metadata for the temporal diagnostic."""

    full_panel = _claim_row(claim_audit, "full_panel")
    supporting = _claim_row(claim_audit, "polymarket_supporting_months")
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "h1_state_poll_panel_temporal_diagnostic",
            "calculation_scope": "deterministic_python_from_state_date_poll_panel_cases",
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
            "month_count": int(len(temporal_summary)),
            "polymarket_supporting_month_count": int(
                temporal_summary["aggregate_mean_supports_polymarket"].sum()
            ),
            "polymarket_supporting_months": str(supporting["included_months"]),
            "polymarket_supporting_row_count": int(supporting["row_count"]),
            "polymarket_supporting_pm_lower_loss_count": int(
                supporting["polymarket_lower_loss_count"]
            ),
            "polymarket_supporting_poll_lower_loss_count": int(
                supporting["poll_derived_lower_loss_count"]
            ),
            "polymarket_supporting_mean_polymarket_brier": float(
                supporting["mean_polymarket_brier"]
            ),
            "polymarket_supporting_mean_poll_derived_brier": float(
                supporting["mean_poll_derived_brier"]
            ),
            "full_panel_mean_polymarket_brier": float(full_panel["mean_polymarket_brier"]),
            "full_panel_mean_poll_derived_brier": float(full_panel["mean_poll_derived_brier"]),
            "full_panel_polymarket_lower_loss_count": int(
                full_panel["polymarket_lower_loss_count"]
            ),
            "full_panel_poll_derived_lower_loss_count": int(
                full_panel["poll_derived_lower_loss_count"]
            ),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "h1_goal_completion_status": "not_proven",
        },
        "source_paths": {
            "case_input": str(case_input),
            "temporal_summary": str(temporal_summary_output),
            "state_month": str(state_month_output),
            "claim_audit": str(claim_audit_output),
            "figure": str(figure_output),
        },
        "limitations": {
            "panel_rows_are_repeated_forecasts": True,
            "supporting_months_are_conditioned_diagnostic_subset": True,
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
    if group.empty:
        row = {
            "audit_scope": audit_scope,
            "included_months": "",
            "row_count": 0,
            "state_count": 0,
            "polymarket_lower_loss_count": 0,
            "poll_derived_lower_loss_count": 0,
            "tie_count": 0,
            "polymarket_better_share": 0.0,
            "mean_polymarket_brier": float("nan"),
            "mean_poll_derived_brier": float("nan"),
            "mean_loss_advantage": float("nan"),
            "aggregate_mean_supports_polymarket": False,
            "majority_rows_support_polymarket": False,
            "allowed_interpretation": allowed_interpretation,
            "limitation": limitation,
        }
    else:
        base = _summary_for_group(
            group,
            extra={},
            columns=tuple(column for column in CLAIM_AUDIT_COLUMNS if column not in {
                "audit_scope",
                "included_months",
                "allowed_interpretation",
                "limitation",
            }),
        )
        months = sorted(group["forecast_month"].astype(str).unique())
        row = {
            "audit_scope": audit_scope,
            "included_months": ",".join(months),
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


def _with_forecast_month(cases: pd.DataFrame) -> pd.DataFrame:
    frame = cases.copy()
    frame["forecast_date"] = pd.to_datetime(frame["forecast_date"], errors="raise")
    frame["forecast_month"] = frame["forecast_date"].dt.to_period("M").astype(str)
    return frame


def _format_date(value: Any) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-input", type=Path, default=CASE_INPUT)
    parser.add_argument(
        "--temporal-summary-output",
        type=Path,
        default=TEMPORAL_SUMMARY_OUTPUT,
    )
    parser.add_argument("--state-month-output", type=Path, default=STATE_MONTH_OUTPUT)
    parser.add_argument("--claim-audit-output", type=Path, default=CLAIM_AUDIT_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = generate_h1_state_poll_panel_temporal_outputs(
            case_input=args.case_input,
            temporal_summary_output=args.temporal_summary_output,
            state_month_output=args.state_month_output,
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
