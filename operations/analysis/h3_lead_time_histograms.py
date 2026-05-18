"""Compute descriptive H3 lead-time histograms from tiered wallet activity.

The module aligns the deterministic daily tier activity series to the curated
H2 event catalog. It produces descriptive timing outputs only; it does not run
lead-lag regressions, Granger tests, agents, MCP tools, or LLM calls.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR, SEED_PATH, load_curated_events
from operations.analysis.tiered_wallet_activity import ACTIVITY_COLUMNS, ACTIVITY_OUTPUT
from operations.analysis.wallet_distribution_inventory import TIER_ORDER


DEFAULT_LEAD_WINDOW = (-14, 0)
LEAD_WINDOW_LABEL = "lead_minus_14d_to_0d"
EVENT_ROWS_OUTPUT = RESULTS_DIR / "h3_lead_time_event_rows.csv"
HISTOGRAM_OUTPUT = RESULTS_DIR / "h3_lead_time_histograms.csv"
METADATA_OUTPUT = RESULTS_DIR / "h3_lead_time_histograms_metadata.json"

EVENT_ROW_COLUMNS: tuple[str, ...] = (
    "window_label",
    "event_id",
    "event_date",
    "date",
    "relative_day",
    "tier",
    "activity_date_available",
    "has_activity",
    "trade_rows",
    "active_wallets",
    "total_amount_usd",
    "buy_amount_usd",
    "sell_amount_usd",
    "net_amount_usd",
)

HISTOGRAM_COLUMNS: tuple[str, ...] = (
    "window_label",
    "tier",
    "relative_day",
    "event_count",
    "available_event_days",
    "active_event_days",
    "active_event_share",
    "total_trade_rows",
    "total_active_wallet_observations",
    "total_amount_usd",
    "buy_amount_usd",
    "sell_amount_usd",
    "net_amount_usd",
    "avg_trade_rows_per_event",
    "avg_total_amount_usd_per_event",
)


@dataclass(frozen=True)
class H3LeadTimeResult:
    """Summary of generated H3 lead-time artifacts."""

    event_rows_path: Path
    histogram_path: Path
    metadata_path: Path
    event_count: int
    event_row_count: int
    histogram_row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "event_rows_path": str(self.event_rows_path),
            "histogram_path": str(self.histogram_path),
            "metadata_path": str(self.metadata_path),
            "event_count": self.event_count,
            "event_row_count": self.event_row_count,
            "histogram_row_count": self.histogram_row_count,
        }


def load_tiered_activity(activity_path: Path = ACTIVITY_OUTPUT) -> pd.DataFrame:
    """Load the deterministic daily tier activity CSV."""

    if not activity_path.exists():
        raise FileNotFoundError(f"Tiered wallet activity not found: {activity_path}")
    return validate_tiered_activity(pd.read_csv(activity_path))


def validate_tiered_activity(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a daily tier activity DataFrame."""

    missing = [column for column in ACTIVITY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"tiered activity missing columns: {missing}")
    if "wallet_address" in frame.columns:
        raise ValueError("tiered activity must be aggregated and must not contain wallet_address")

    normalized = frame.loc[:, ACTIVITY_COLUMNS].copy()
    normalized["date"] = pd.to_datetime(
        normalized["date"],
        errors="raise",
    ).dt.date.astype(str)
    normalized["tier"] = normalized["tier"].astype(str).str.strip()

    invalid_tiers = sorted(set(normalized["tier"]).difference(TIER_ORDER))
    if invalid_tiers:
        raise ValueError(f"tiered activity has invalid tiers: {invalid_tiers}")

    duplicate_rows = normalized.duplicated(subset=["date", "tier"])
    if duplicate_rows.any():
        duplicates = normalized.loc[duplicate_rows, ["date", "tier"]].to_dict(
            orient="records"
        )
        raise ValueError(f"tiered activity has duplicate date-tier rows: {duplicates}")

    integer_columns = ("trade_rows", "active_wallets")
    amount_columns = (
        "total_amount_usd",
        "buy_amount_usd",
        "sell_amount_usd",
        "net_amount_usd",
    )
    for column in integer_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not (normalized[column] >= 0).all():
            raise ValueError(f"{column} must be non-negative")
        normalized[column] = normalized[column].astype(int)
    for column in amount_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")

    return normalized.sort_values(["date", "tier"]).reset_index(drop=True)


def build_lead_time_event_rows(
    events: pd.DataFrame,
    activity: pd.DataFrame,
    *,
    lead_window_days: tuple[int, int] = DEFAULT_LEAD_WINDOW,
    window_label: str = LEAD_WINDOW_LABEL,
) -> pd.DataFrame:
    """Align tiered activity to curated events over a pre-event daily window."""

    _validate_lead_window(lead_window_days)
    event_frame = _validate_events(events)
    activity_frame = validate_tiered_activity(activity)

    activity_lookup = {
        (row["date"], row["tier"]): row
        for row in activity_frame.to_dict(orient="records")
    }
    rows: list[dict[str, object]] = []
    for event in event_frame.to_dict(orient="records"):
        event_date = event["event_date"]
        for offset in range(lead_window_days[0], lead_window_days[1] + 1):
            target_date = event_date + timedelta(days=offset)
            date_key = target_date.isoformat()
            for tier in TIER_ORDER:
                activity_row = activity_lookup.get((date_key, tier))
                metrics = _activity_metrics(activity_row)
                rows.append(
                    {
                        "window_label": window_label,
                        "event_id": event["event_id"],
                        "event_date": event_date.isoformat(),
                        "date": date_key,
                        "relative_day": offset,
                        "tier": tier,
                        **metrics,
                    }
                )

    return pd.DataFrame(rows, columns=EVENT_ROW_COLUMNS)


def summarize_lead_time_histograms(event_rows: pd.DataFrame) -> pd.DataFrame:
    """Aggregate aligned event rows into tier-by-relative-day histograms."""

    _require_columns(event_rows, EVENT_ROW_COLUMNS, "event_rows")
    if event_rows.empty:
        return pd.DataFrame(columns=HISTOGRAM_COLUMNS)

    frame = event_rows.loc[:, EVENT_ROW_COLUMNS].copy()
    frame["tier"] = pd.Categorical(frame["tier"], categories=TIER_ORDER, ordered=True)
    grouped = (
        frame.groupby(
            ["window_label", "tier", "relative_day"],
            as_index=False,
            observed=True,
        )
        .agg(
            event_count=("event_id", "nunique"),
            available_event_days=("activity_date_available", "sum"),
            active_event_days=("has_activity", "sum"),
            total_trade_rows=("trade_rows", "sum"),
            total_active_wallet_observations=("active_wallets", "sum"),
            total_amount_usd=("total_amount_usd", "sum"),
            buy_amount_usd=("buy_amount_usd", "sum"),
            sell_amount_usd=("sell_amount_usd", "sum"),
            net_amount_usd=("net_amount_usd", "sum"),
        )
        .sort_values(["window_label", "tier", "relative_day"])
        .reset_index(drop=True)
    )
    grouped["active_event_share"] = (
        grouped["active_event_days"] / grouped["event_count"]
    )
    grouped["avg_trade_rows_per_event"] = (
        grouped["total_trade_rows"] / grouped["event_count"]
    )
    grouped["avg_total_amount_usd_per_event"] = (
        grouped["total_amount_usd"] / grouped["event_count"]
    )

    for column in ("event_count", "available_event_days", "active_event_days"):
        grouped[column] = grouped[column].astype(int)
    grouped["total_trade_rows"] = grouped["total_trade_rows"].astype(int)
    grouped["total_active_wallet_observations"] = grouped[
        "total_active_wallet_observations"
    ].astype(int)
    grouped["tier"] = grouped["tier"].astype(str)
    return grouped.loc[:, HISTOGRAM_COLUMNS]


def generate_h3_lead_time_histograms(
    *,
    events_csv_path: Path = SEED_PATH,
    activity_path: Path = ACTIVITY_OUTPUT,
    event_rows_path: Path = EVENT_ROWS_OUTPUT,
    histogram_path: Path = HISTOGRAM_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    lead_window_days: tuple[int, int] = DEFAULT_LEAD_WINDOW,
) -> H3LeadTimeResult:
    """Generate deterministic H3 lead-time event rows, histograms, and metadata."""

    events = load_curated_events(events_csv_path)
    activity = load_tiered_activity(activity_path)
    event_rows = build_lead_time_event_rows(
        events,
        activity,
        lead_window_days=lead_window_days,
    )
    histograms = summarize_lead_time_histograms(event_rows)

    event_rows_path.parent.mkdir(parents=True, exist_ok=True)
    histogram_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    event_rows.to_csv(event_rows_path, index=False)
    histograms.to_csv(histogram_path, index=False)

    metadata = _build_metadata(
        events=events,
        activity=activity,
        event_rows=event_rows,
        histograms=histograms,
        events_csv_path=events_csv_path,
        activity_path=activity_path,
        lead_window_days=lead_window_days,
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return H3LeadTimeResult(
        event_rows_path=event_rows_path,
        histogram_path=histogram_path,
        metadata_path=metadata_path,
        event_count=len(events),
        event_row_count=len(event_rows),
        histogram_row_count=len(histograms),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--activity", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--event-rows-output", type=Path, default=EVENT_ROWS_OUTPUT)
    parser.add_argument("--histogram-output", type=Path, default=HISTOGRAM_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--start-day", type=int, default=DEFAULT_LEAD_WINDOW[0])
    parser.add_argument("--end-day", type=int, default=DEFAULT_LEAD_WINDOW[1])
    args = parser.parse_args(argv)

    try:
        result = generate_h3_lead_time_histograms(
            events_csv_path=args.events,
            activity_path=args.activity,
            event_rows_path=args.event_rows_output,
            histogram_path=args.histogram_output,
            metadata_path=args.metadata_output,
            lead_window_days=(args.start_day, args.end_day),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_events(events: pd.DataFrame) -> pd.DataFrame:
    _require_columns(events, ("event_id", "event_date"), "events")
    frame = events.loc[:, ["event_id", "event_date"]].copy()
    if frame["event_id"].isna().any() or (
        frame["event_id"].astype(str).str.strip() == ""
    ).any():
        raise ValueError("events contain blank event_id values")
    frame["event_id"] = frame["event_id"].astype(str).str.strip()
    if frame["event_id"].duplicated().any():
        duplicates = sorted(frame.loc[frame["event_id"].duplicated(), "event_id"].unique())
        raise ValueError(f"events contain duplicate event_id values: {duplicates}")
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise").dt.date
    return frame.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def _activity_metrics(activity_row: dict[str, object] | None) -> dict[str, object]:
    if activity_row is None:
        return {
            "activity_date_available": False,
            "has_activity": False,
            "trade_rows": 0,
            "active_wallets": 0,
            "total_amount_usd": 0.0,
            "buy_amount_usd": 0.0,
            "sell_amount_usd": 0.0,
            "net_amount_usd": 0.0,
        }

    trade_rows = int(activity_row["trade_rows"])
    total_amount = float(activity_row["total_amount_usd"])
    return {
        "activity_date_available": True,
        "has_activity": bool(trade_rows > 0 or total_amount != 0.0),
        "trade_rows": trade_rows,
        "active_wallets": int(activity_row["active_wallets"]),
        "total_amount_usd": total_amount,
        "buy_amount_usd": float(activity_row["buy_amount_usd"]),
        "sell_amount_usd": float(activity_row["sell_amount_usd"]),
        "net_amount_usd": float(activity_row["net_amount_usd"]),
    }


def _build_metadata(
    *,
    events: pd.DataFrame,
    activity: pd.DataFrame,
    event_rows: pd.DataFrame,
    histograms: pd.DataFrame,
    events_csv_path: Path,
    activity_path: Path,
    lead_window_days: tuple[int, int],
) -> dict[str, Any]:
    return {
        "method": {
            "name": "descriptive_h3_lead_time_histograms",
            "lead_window_days": {
                "start": lead_window_days[0],
                "end": lead_window_days[1],
                "label": LEAD_WINDOW_LABEL,
            },
            "alignment": "calendar_day_relative_to_curated_event_date",
            "statistics": "descriptive_aggregates_only",
        },
        "input": {
            "events_csv_path": str(events_csv_path),
            "activity_path": str(activity_path),
            "event_count": int(events["event_id"].nunique()),
            "activity_row_count": int(len(activity)),
            "activity_date_range_start": str(activity["date"].min()),
            "activity_date_range_end": str(activity["date"].max()),
            "tiers": list(TIER_ORDER),
        },
        "output": {
            "event_row_count": int(len(event_rows)),
            "histogram_row_count": int(len(histograms)),
            "event_row_columns": list(EVENT_ROW_COLUMNS),
            "histogram_columns": list(HISTOGRAM_COLUMNS),
            "contains_wallet_addresses": False,
            "claim_scope": "descriptive_timing_patterns_only",
        },
        "limitations": {
            "daily_alignment_only": True,
            "uses_curated_h2_events": True,
            "does_not_establish_causality": True,
            "granger_tests_included": False,
        },
    }


def _validate_lead_window(lead_window_days: tuple[int, int]) -> None:
    start_day, end_day = lead_window_days
    if start_day > end_day:
        raise ValueError("lead_window_days start must be <= end")
    if end_day > 0:
        raise ValueError("lead-time window end must be <= 0")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
