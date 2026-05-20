"""Generate recorded monitor v2 input CSVs from existing local artifacts.

The adapter creates file-based inputs for the future monitor from the current
historical replay sources. It does not call external APIs, WebSockets, LLMs,
agents, MCP tools, order-execution paths, or write to the database.
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

import pandas as pd

from operations.analysis.h3_lead_time_histograms import load_tiered_activity
from operations.analysis.monitor_v2_historical_replay import REPLAY_MARKET_ID
from operations.analysis.monitor_v2_input_validation import (
    EVENT_CANDIDATE_COLUMNS,
    MARKET_SNAPSHOT_COLUMNS,
    MARKET_WATCH_COLUMNS,
    REPORT_OUTPUT,
    WALLET_TIER_SNAPSHOT_COLUMNS,
    validate_recorded_input_files,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR, SEED_PATH, load_curated_events
from operations.analysis.tiered_wallet_activity import ACTIVITY_OUTPUT
from operations.db.migrations import DB_PATH


WATCHLIST_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_watchlist.csv"
MARKET_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_market_snapshots.csv"
WALLET_TIER_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_wallet_tier_snapshots.csv"
EVENT_CANDIDATES_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_event_candidates.csv"
METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_inputs_metadata.json"


@dataclass(frozen=True)
class RecordedInputAdapterResult:
    """Summary of generated recorded monitor v2 input artifacts."""

    watchlist_path: Path
    market_snapshots_path: Path
    wallet_tier_snapshots_path: Path
    event_candidates_path: Path
    validation_report_path: Path
    metadata_path: Path
    watchlist_row_count: int
    market_snapshot_row_count: int
    wallet_tier_snapshot_row_count: int
    event_candidate_row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "watchlist_path": str(self.watchlist_path),
            "market_snapshots_path": str(self.market_snapshots_path),
            "wallet_tier_snapshots_path": str(self.wallet_tier_snapshots_path),
            "event_candidates_path": str(self.event_candidates_path),
            "validation_report_path": str(self.validation_report_path),
            "metadata_path": str(self.metadata_path),
            "watchlist_row_count": self.watchlist_row_count,
            "market_snapshot_row_count": self.market_snapshot_row_count,
            "wallet_tier_snapshot_row_count": self.wallet_tier_snapshot_row_count,
            "event_candidate_row_count": self.event_candidate_row_count,
        }


def generate_recorded_monitor_v2_inputs(
    *,
    db_path: Path = DB_PATH,
    events_csv_path: Path = SEED_PATH,
    activity_path: Path = ACTIVITY_OUTPUT,
    watchlist_path: Path = WATCHLIST_OUTPUT,
    market_snapshots_path: Path = MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = EVENT_CANDIDATES_OUTPUT,
    validation_report_path: Path = REPORT_OUTPUT,
    metadata_path: Path = METADATA_OUTPUT,
    market_id: str = REPLAY_MARKET_ID,
) -> RecordedInputAdapterResult:
    """Generate and validate recorded monitor v2 input CSV files."""

    events = load_curated_events(events_csv_path)
    activity = load_tiered_activity(activity_path)
    price_snapshots = load_recorded_price_snapshots(
        db_path,
        start_date=_activity_min_date(activity),
        end_date=_activity_max_date(activity),
        market_id=market_id,
    )
    watchlist = build_recorded_watchlist(price_snapshots, market_id=market_id)
    wallet_snapshots = build_wallet_tier_snapshots(activity, market_id=market_id)
    event_candidates = build_event_candidates(events, market_id=market_id)

    for path, frame in (
        (watchlist_path, watchlist),
        (market_snapshots_path, price_snapshots),
        (wallet_tier_snapshots_path, wallet_snapshots),
        (event_candidates_path, event_candidates),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    validation_report = validate_recorded_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        report_output_path=validation_report_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                db_path=db_path,
                events_csv_path=events_csv_path,
                activity_path=activity_path,
                watchlist=watchlist,
                price_snapshots=price_snapshots,
                wallet_snapshots=wallet_snapshots,
                event_candidates=event_candidates,
                validation_report=validation_report,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return RecordedInputAdapterResult(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
        metadata_path=metadata_path,
        watchlist_row_count=len(watchlist),
        market_snapshot_row_count=len(price_snapshots),
        wallet_tier_snapshot_row_count=len(wallet_snapshots),
        event_candidate_row_count=len(event_candidates),
    )


def build_recorded_watchlist(price_snapshots: pd.DataFrame, *, market_id: str) -> pd.DataFrame:
    """Return one replay watchlist item from recorded price snapshots."""

    if price_snapshots.empty:
        raise ValueError("Cannot build watchlist from empty price snapshots")
    token_ids = sorted(str(value) for value in price_snapshots["token_id"].dropna().unique())
    if not token_ids:
        raise ValueError("Cannot build watchlist without token ids")
    first_timestamp = str(price_snapshots["timestamp_utc"].min())
    last_timestamp = str(price_snapshots["timestamp_utc"].max())
    return pd.DataFrame(
        [
            {
                "watch_id": "watch_2024_us_presidential_replay",
                "market_id": market_id,
                "condition_id": "recorded_replay_condition",
                "token_ids": ",".join(token_ids),
                "question": "2024 US presidential election Polymarket replay",
                "category": "politics",
                "subcategory": "us_election",
                "status": "active",
                "source": "data/thesis.db:polymarket_prices",
                "created_at": first_timestamp,
                "updated_at": last_timestamp,
            }
        ],
        columns=MARKET_WATCH_COLUMNS,
    )


def load_recorded_price_snapshots(
    db_path: Path,
    *,
    start_date: date,
    end_date: date,
    market_id: str,
) -> pd.DataFrame:
    """Load daily recorded market snapshots from the local SQLite price table."""

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")
    sql = """
        SELECT price_timestamp, market_id, token_id, price, volume_24h, best_bid, best_ask
        FROM polymarket_prices
        WHERE substr(price_timestamp, 1, 10) BETWEEN ? AND ?
        ORDER BY price_timestamp
    """
    conn = sqlite3.connect(db_path)
    try:
        frame = pd.read_sql_query(
            sql,
            conn,
            params=[start_date.isoformat(), end_date.isoformat()],
        )
    finally:
        conn.close()
    if frame.empty:
        raise ValueError(f"No recorded prices found between {start_date} and {end_date}")

    frame["date"] = pd.to_datetime(frame["price_timestamp"], errors="raise", utc=True).dt.date
    frame = frame.sort_values(["date", "price_timestamp"]).drop_duplicates("date", keep="last")
    frame["timestamp_utc"] = pd.to_datetime(
        frame["price_timestamp"],
        errors="raise",
        utc=True,
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    frame["market_id"] = market_id
    frame["midpoint"] = pd.to_numeric(frame["price"], errors="raise")
    frame["best_bid"] = pd.to_numeric(frame["best_bid"], errors="coerce")
    frame["best_ask"] = pd.to_numeric(frame["best_ask"], errors="coerce")
    frame["spread"] = frame["best_ask"] - frame["best_bid"]
    frame.loc[frame["best_bid"].isna() | frame["best_ask"].isna(), "spread"] = pd.NA
    frame["volume"] = pd.to_numeric(frame["volume_24h"], errors="coerce")
    frame["open_interest"] = pd.NA
    frame["source"] = "data/thesis.db:polymarket_prices"
    return frame.loc[
        :,
        MARKET_SNAPSHOT_COLUMNS,
    ].reset_index(drop=True)


def build_wallet_tier_snapshots(activity: pd.DataFrame, *, market_id: str) -> pd.DataFrame:
    """Return aggregate wallet-tier snapshots from tiered daily activity."""

    frame = activity.copy()
    if "wallet_address" in frame.columns:
        raise ValueError("recorded wallet-tier adapter must not receive wallet_address")
    required = {
        "date",
        "tier",
        "trade_rows",
        "active_wallets",
        "total_amount_usd",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"tiered activity missing required columns: {missing}")
    frame["timestamp_utc"] = pd.to_datetime(frame["date"], errors="raise", utc=True).dt.strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    frame["market_id"] = market_id
    frame["bucket"] = "daily"
    frame["trade_count"] = pd.to_numeric(frame["trade_rows"], errors="raise").astype(int)
    frame["active_wallets"] = pd.to_numeric(frame["active_wallets"], errors="raise").astype(int)
    frame["total_observed_amount_usd"] = pd.to_numeric(
        frame["total_amount_usd"],
        errors="raise",
    )
    concentration = _concentration_by_date(frame)
    frame = frame.merge(concentration, on="date", how="left")
    frame["source"] = "data/results/h3_tiered_wallet_activity_daily.csv"
    frame["filter_metadata"] = "buy_side_observed_extract; source_filter_documented_in_h3_metadata"
    return frame.loc[:, WALLET_TIER_SNAPSHOT_COLUMNS].sort_values(
        ["timestamp_utc", "tier"]
    ).reset_index(drop=True)


def build_event_candidates(events: pd.DataFrame, *, market_id: str) -> pd.DataFrame:
    """Return reviewed event candidates from the curated event seed."""

    required = {
        "event_id",
        "event_date",
        "event_time_utc",
        "title",
        "event_type",
        "source_url",
        "expected_direction",
    }
    missing = sorted(required.difference(events.columns))
    if missing:
        raise ValueError(f"events missing required columns: {missing}")
    frame = events.copy()
    frame["published_at_utc"] = [
        _event_timestamp(row["event_date"], row["event_time_utc"])
        for row in frame.to_dict(orient="records")
    ]
    frame["detected_at_utc"] = frame["published_at_utc"]
    frame["event_candidate_id"] = frame["event_id"].astype(str)
    frame["related_market_ids"] = market_id
    frame["expected_effect"] = frame["expected_direction"].astype(str)
    frame["review_status"] = "accepted"
    frame["review_notes"] = "curated_seed_event_used_for_historical_replay"
    return frame.loc[:, EVENT_CANDIDATE_COLUMNS].sort_values(
        ["published_at_utc", "event_candidate_id"]
    ).reset_index(drop=True)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--activity", type=Path, default=ACTIVITY_OUTPUT)
    parser.add_argument("--watchlist-output", type=Path, default=WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots-output", type=Path, default=MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument("--wallet-tier-snapshots-output", type=Path, default=WALLET_TIER_SNAPSHOTS_OUTPUT)
    parser.add_argument("--event-candidates-output", type=Path, default=EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--validation-report-output", type=Path, default=REPORT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_recorded_monitor_v2_inputs(
            db_path=args.db,
            events_csv_path=args.events,
            activity_path=args.activity,
            watchlist_path=args.watchlist_output,
            market_snapshots_path=args.market_snapshots_output,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots_output,
            event_candidates_path=args.event_candidates_output,
            validation_report_path=args.validation_report_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _activity_min_date(activity: pd.DataFrame) -> date:
    return min(pd.to_datetime(activity["date"], errors="raise").dt.date)


def _activity_max_date(activity: pd.DataFrame) -> date:
    return max(pd.to_datetime(activity["date"], errors="raise").dt.date)


def _concentration_by_date(activity: pd.DataFrame) -> pd.DataFrame:
    totals = activity.groupby("date", as_index=False)["total_observed_amount_usd"].sum()
    totals = totals.rename(columns={"total_observed_amount_usd": "daily_total"})
    shares = activity.merge(totals, on="date", how="left")
    shares["share"] = 0.0
    positive = shares["daily_total"] > 0
    shares.loc[positive, "share"] = (
        shares.loc[positive, "total_observed_amount_usd"]
        / shares.loc[positive, "daily_total"]
    )
    top_share = (
        shares.loc[shares["tier"] == "tier_1_top_1pct", ["date", "share"]]
        .rename(columns={"share": "top_tier_share"})
    )
    hhi = shares.assign(square_share=shares["share"] ** 2).groupby(
        "date",
        as_index=False,
    )["square_share"].sum()
    hhi = hhi.rename(columns={"square_share": "hhi_concentration"})
    return top_share.merge(hhi, on="date", how="outer")


def _event_timestamp(event_date: Any, event_time_utc: Any) -> str:
    day = pd.to_datetime(event_date, errors="raise").date().isoformat()
    time_value = str(event_time_utc).strip()
    if not time_value:
        raise ValueError("event_time_utc must be non-empty")
    return f"{day}T{time_value}Z"


def _build_metadata(
    *,
    db_path: Path,
    events_csv_path: Path,
    activity_path: Path,
    watchlist: pd.DataFrame,
    price_snapshots: pd.DataFrame,
    wallet_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_recorded_input_adapter",
            "source_mode": "existing_local_artifacts_only",
            "market_id": REPLAY_MARKET_ID,
            "validates_outputs": True,
        },
        "inputs": {
            "db_path": str(db_path),
            "events_csv_path": str(events_csv_path),
            "activity_path": str(activity_path),
        },
        "outputs": {
            "watchlist_row_count": int(len(watchlist)),
            "market_snapshot_row_count": int(len(price_snapshots)),
            "wallet_tier_snapshot_row_count": int(len(wallet_snapshots)),
            "event_candidate_row_count": int(len(event_candidates)),
            "validation_status": validation_report["status"],
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "recorded_files_only": True,
            "uses_existing_curated_events": True,
            "uses_daily_price_snapshots": True,
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


if __name__ == "__main__":
    raise SystemExit(main())
