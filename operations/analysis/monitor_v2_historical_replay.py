"""Build historical monitor v2 replay snapshots from deterministic artifacts.

The replay converts existing daily price, event, and aggregate wallet-tier
artifacts into the monitor v2 snapshot contract, then scores the snapshots with
the deterministic monitor v2 alert logic. It does not collect live data, write
to the database, call LLMs, activate agents, use MCP tools, or send orders.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from operations.analysis.event_study import compute_daily_price_changes
from operations.analysis.h3_lead_time_histograms import load_tiered_activity
from operations.analysis.monitor_v2_snapshot import (
    ALERT_ROW_COLUMNS,
    ALERT_SUMMARY_COLUMNS,
    DEFAULT_BASELINE_OBSERVATIONS,
    DEFAULT_MIN_BASELINE_OBSERVATIONS,
    SNAPSHOT_COLUMNS,
    build_monitor_v2_alert_rows,
    summarize_monitor_v2_alerts,
)
from operations.analysis.run_h2_event_windows import (
    RESULTS_DIR,
    SEED_PATH,
    load_curated_events,
    load_daily_polymarket_prices,
)
from operations.analysis.tiered_wallet_activity import ACTIVITY_COLUMNS, ACTIVITY_OUTPUT
from operations.analysis.wallet_distribution_inventory import TIER_ORDER
from operations.db.migrations import DB_PATH


REPLAY_MARKET_ID = "polymarket_2024_us_presidential_replay"
SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_historical_replay_snapshots.csv"
ALERT_ROWS_OUTPUT = RESULTS_DIR / "monitor_v2_historical_replay_alert_rows.csv"
ALERT_SUMMARY_OUTPUT = RESULTS_DIR / "monitor_v2_historical_replay_alert_summary.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_historical_replay_metadata.json"

EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "event_type",
    "source_url",
)


@dataclass(frozen=True)
class MonitorV2HistoricalReplayResult:
    """Summary of generated historical replay artifacts."""

    snapshots_path: Path
    rows_path: Path
    summary_path: Path
    metadata_path: Path
    snapshot_count: int
    alert_row_count: int
    alert_count: int
    summary_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "snapshots_path": str(self.snapshots_path),
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "snapshot_count": self.snapshot_count,
            "alert_row_count": self.alert_row_count,
            "alert_count": self.alert_count,
            "summary_row_count": self.summary_row_count,
        }


def build_historical_replay_snapshots(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    activity: pd.DataFrame,
    *,
    market_id: str = REPLAY_MARKET_ID,
) -> pd.DataFrame:
    """Return monitor v2 snapshots from existing historical artifacts."""

    event_frame = _validate_events(events)
    price_changes = compute_daily_price_changes(prices)
    price_changes["date"] = pd.to_datetime(price_changes["date"], errors="raise").dt.date
    activity_frame = _validate_activity(activity)
    replay_dates = _replay_dates(price_changes, activity_frame)
    event_lookup = _event_lookup(event_frame)

    rows: list[dict[str, object]] = []
    for replay_date in replay_dates:
        event = event_lookup.get(replay_date)
        context = _event_context(event)
        price_value = _price_change_for_date(price_changes, replay_date)
        rows.append(
            {
                "timestamp_utc": _timestamp(replay_date),
                "market_id": market_id,
                "tier": "market",
                "anomaly_family": "market_move",
                "metric_name": "absolute_price_change",
                "observed_value": abs(price_value),
                **context,
                "evidence_ref": "data/thesis.db:polymarket_prices",
                "limitation": "daily price replay; no intraday market movement",
                "review_status": "candidate",
            }
        )

        day_activity = activity_frame[activity_frame["date"] == replay_date]
        for tier in TIER_ORDER:
            tier_row = _activity_row(day_activity, tier)
            total_amount = float(tier_row["total_amount_usd"])
            active_wallets = float(tier_row["active_wallets"])
            rows.extend(
                [
                    {
                        "timestamp_utc": _timestamp(replay_date),
                        "market_id": market_id,
                        "tier": tier,
                        "anomaly_family": "wallet_tier_activity",
                        "metric_name": "log1p_total_observed_amount_usd",
                        "observed_value": float(np.log1p(total_amount)),
                        **context,
                        "evidence_ref": "data/results/h3_tiered_wallet_activity_daily.csv",
                        "limitation": "aggregate BUY-side tier activity replay; no wallet addresses",
                        "review_status": "candidate",
                    },
                    {
                        "timestamp_utc": _timestamp(replay_date),
                        "market_id": market_id,
                        "tier": tier,
                        "anomaly_family": "active_wallet_activity",
                        "metric_name": "active_wallets",
                        "observed_value": active_wallets,
                        **context,
                        "evidence_ref": "data/results/h3_tiered_wallet_activity_daily.csv",
                        "limitation": "aggregate active-wallet tier count replay; no wallet addresses",
                        "review_status": "candidate",
                    },
                ]
            )

        rows.append(
            {
                "timestamp_utc": _timestamp(replay_date),
                "market_id": market_id,
                "tier": "all_tiers",
                "anomaly_family": "concentration",
                "metric_name": "tier_1_total_amount_share",
                "observed_value": _top_tier_share(day_activity),
                **context,
                "evidence_ref": "data/results/h3_tiered_wallet_activity_daily.csv",
                "limitation": "aggregate tier concentration replay; no wallet performance claim",
                "review_status": "candidate",
            }
        )

    return pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS)


def generate_monitor_v2_historical_replay(
    *,
    db_path: Path = DB_PATH,
    events_csv_path: Path = SEED_PATH,
    activity_path: Path = ACTIVITY_OUTPUT,
    snapshots_path: Path = SNAPSHOTS_OUTPUT,
    rows_path: Path = ALERT_ROWS_OUTPUT,
    summary_path: Path = ALERT_SUMMARY_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    baseline_observations: int = DEFAULT_BASELINE_OBSERVATIONS,
    min_baseline_observations: int = DEFAULT_MIN_BASELINE_OBSERVATIONS,
    market_id: str = REPLAY_MARKET_ID,
) -> MonitorV2HistoricalReplayResult:
    """Generate replay snapshots, alert rows, summaries, and metadata."""

    events = load_curated_events(events_csv_path)
    activity = load_tiered_activity(activity_path)
    start_date, end_date = _price_query_bounds(activity)
    prices = load_daily_polymarket_prices(
        db_path,
        start_date=start_date,
        end_date=end_date,
    )
    snapshots = build_historical_replay_snapshots(
        events,
        prices,
        activity,
        market_id=market_id,
    )
    alert_rows = build_monitor_v2_alert_rows(
        snapshots,
        baseline_observations=baseline_observations,
        min_baseline_observations=min_baseline_observations,
    )
    alert_summary = summarize_monitor_v2_alerts(alert_rows)

    snapshots_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    snapshots.to_csv(snapshots_path, index=False)
    alert_rows.to_csv(rows_path, index=False)
    alert_summary.to_csv(summary_path, index=False)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                events=events,
                activity=activity,
                prices=prices,
                snapshots=snapshots,
                alert_rows=alert_rows,
                alert_summary=alert_summary,
                db_path=db_path,
                events_csv_path=events_csv_path,
                activity_path=activity_path,
                baseline_observations=baseline_observations,
                min_baseline_observations=min_baseline_observations,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return MonitorV2HistoricalReplayResult(
        snapshots_path=snapshots_path,
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
        snapshot_count=len(snapshots),
        alert_row_count=len(alert_rows),
        alert_count=int((alert_rows["severity"] != "none").sum()),
        summary_row_count=len(alert_summary),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--activity", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--snapshots-output", type=Path, default=SNAPSHOTS_OUTPUT)
    parser.add_argument("--rows-output", type=Path, default=ALERT_ROWS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=ALERT_SUMMARY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--baseline-observations", type=int, default=DEFAULT_BASELINE_OBSERVATIONS)
    parser.add_argument("--min-baseline-observations", type=int, default=DEFAULT_MIN_BASELINE_OBSERVATIONS)
    args = parser.parse_args(argv)

    try:
        result = generate_monitor_v2_historical_replay(
            db_path=args.db,
            events_csv_path=args.events,
            activity_path=args.activity,
            snapshots_path=args.snapshots_output,
            rows_path=args.rows_output,
            summary_path=args.summary_output,
            metadata_path=args.metadata_output,
            baseline_observations=args.baseline_observations,
            min_baseline_observations=args.min_baseline_observations,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_events(events: pd.DataFrame) -> pd.DataFrame:
    _require_columns(events, EVENT_COLUMNS, "events")
    frame = events.loc[:, EVENT_COLUMNS].copy()
    for column in ("event_id", "title", "event_type", "source_url"):
        if frame[column].isna().any() or (
            frame[column].astype(str).str.strip() == ""
        ).any():
            raise ValueError(f"events contain blank values in {column}")
        frame[column] = frame[column].astype(str).str.strip()
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise").dt.date
    if frame["event_id"].duplicated().any():
        duplicates = sorted(frame.loc[frame["event_id"].duplicated(), "event_id"].unique())
        raise ValueError(f"events contain duplicate event_id values: {duplicates}")
    return frame.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def _validate_activity(activity: pd.DataFrame) -> pd.DataFrame:
    _require_columns(activity, ACTIVITY_COLUMNS, "tiered activity")
    frame = activity.copy()
    if "wallet_address" in frame.columns:
        raise ValueError("historical replay activity must not contain wallet_address")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
    return frame.sort_values(["date", "tier"]).reset_index(drop=True)


def _event_lookup(events: pd.DataFrame) -> dict[date, dict[str, object]]:
    lookup: dict[date, dict[str, object]] = {}
    for row in events.to_dict(orient="records"):
        lookup[row["event_date"]] = row
    return lookup


def _event_context(event: dict[str, object] | None) -> dict[str, str]:
    if event is None:
        return {
            "event_candidate_id": "",
            "event_review_status": "",
        }
    return {
        "event_candidate_id": str(event["event_id"]),
        "event_review_status": "accepted",
    }


def _replay_dates(price_changes: pd.DataFrame, activity: pd.DataFrame) -> list[date]:
    price_dates = set(price_changes["date"])
    activity_dates = set(activity["date"])
    replay_dates = sorted(price_dates.intersection(activity_dates))
    if not replay_dates:
        raise ValueError("No overlapping replay dates between prices and tier activity")
    return replay_dates


def _price_change_for_date(price_changes: pd.DataFrame, replay_date: date) -> float:
    rows = price_changes.loc[price_changes["date"] == replay_date, "price_change"]
    if rows.empty:
        raise ValueError(f"Missing price change for replay date {replay_date}")
    return float(rows.iloc[-1])


def _activity_row(day_activity: pd.DataFrame, tier: str) -> pd.Series:
    rows = day_activity[day_activity["tier"] == tier]
    if rows.empty:
        raise ValueError(f"Missing tier activity for {tier}")
    return rows.iloc[-1]


def _top_tier_share(day_activity: pd.DataFrame) -> float:
    total = float(day_activity["total_amount_usd"].sum())
    if total <= 0:
        return 0.0
    top = float(
        day_activity.loc[
            day_activity["tier"] == "tier_1_top_1pct",
            "total_amount_usd",
        ].sum()
    )
    return top / total


def _price_query_bounds(activity: pd.DataFrame) -> tuple[date, date]:
    dates = pd.to_datetime(activity["date"], errors="raise").dt.date
    return min(dates), max(dates)


def _timestamp(replay_date: date) -> str:
    return f"{replay_date.isoformat()}T00:00:00Z"


def _build_metadata(
    *,
    events: pd.DataFrame,
    activity: pd.DataFrame,
    prices: pd.DataFrame,
    snapshots: pd.DataFrame,
    alert_rows: pd.DataFrame,
    alert_summary: pd.DataFrame,
    db_path: Path,
    events_csv_path: Path,
    activity_path: Path,
    baseline_observations: int,
    min_baseline_observations: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_historical_replay_snapshots",
            "replay_frequency": "daily",
            "source_mode": "existing_local_artifacts_only",
            "baseline_observations": baseline_observations,
            "min_baseline_observations": min_baseline_observations,
            "alert_rule": "Rule C combined-family confirmation from monitor_v2_snapshot",
            "uses_completed_prior_observations": True,
        },
        "inputs": {
            "db_path": str(db_path),
            "events_csv_path": str(events_csv_path),
            "activity_path": str(activity_path),
            "event_count": int(events["event_id"].nunique()),
            "price_row_count": int(len(prices)),
            "activity_row_count": int(len(activity)),
            "date_range_start": str(min(snapshots["timestamp_utc"]).split("T")[0]),
            "date_range_end": str(max(snapshots["timestamp_utc"]).split("T")[0]),
        },
        "outputs": {
            "snapshot_count": int(len(snapshots)),
            "alert_row_count": int(len(alert_rows)),
            "alert_count": int((alert_rows["severity"] != "none").sum()),
            "summary_row_count": int(len(alert_summary)),
            "snapshot_columns": list(SNAPSHOT_COLUMNS),
            "alert_row_columns": list(ALERT_ROW_COLUMNS),
            "summary_columns": list(ALERT_SUMMARY_COLUMNS),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "severity_counts": _severity_counts(alert_rows),
        },
        "limitations": {
            "daily_replay_only": True,
            "uses_existing_curated_events": True,
            "uses_aggregate_wallet_tier_activity": True,
            "uses_observed_buy_side_activity_extract": True,
            "no_live_websocket_or_api_collection": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


def _severity_counts(alert_rows: pd.DataFrame) -> dict[str, int]:
    counts = alert_rows["severity"].value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


if __name__ == "__main__":
    raise SystemExit(main())
