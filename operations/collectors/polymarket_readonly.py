"""Collect read-only Polymarket monitor v2 input files.

The collector writes validated monitor-facing CSV artifacts from public
Polymarket endpoints or deterministic mock payloads. It never uses
authenticated user channels, credentials, agents, MCP tools, ML systems, or
order endpoints.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import httpx
import pandas as pd
from pydantic import ValidationError

from operations.analysis.monitor_v2_live_input_validation import (
    EVENT_CANDIDATE_LIVE_COLUMNS,
    MARKET_SNAPSHOT_LIVE_COLUMNS,
    MARKET_WATCH_LIVE_COLUMNS,
    WALLET_TIER_SNAPSHOT_LIVE_COLUMNS,
    validate_live_event_candidates,
    validate_live_input_files,
    validate_live_market_snapshots,
    validate_live_market_watch_items,
    validate_live_wallet_tier_snapshots,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_watchlist import (
    read_curated_watchlist,
    validate_curated_watchlist,
)


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"
DATA_API_BASE_URL = "https://data-api.polymarket.com"

DEFAULT_BUCKET_MINUTES = 5
DEFAULT_MAX_MARKETS = 5
DEFAULT_TRADE_LIMIT = 500
DEFAULT_TERMS: tuple[str, ...] = (
    "election",
    "president",
    "congress",
    "senate",
    "war",
    "china",
    "taiwan",
    "invade",
    "invasion",
    "sanction",
    "iran",
    "israel",
    "ukraine",
    "russia",
    "venezuela",
    "maduro",
    "trump",
)
DEFAULT_EXCLUDED_TERMS: tuple[str, ...] = (
    "fifa",
    "world cup",
    "nba",
    "nhl",
    "nfl",
    "stanley cup",
    "hockey",
    "soccer",
    "football",
    "super bowl",
    "champions league",
    "gta vi",
    "album",
    "rihanna",
    "playboi",
    "carti",
    "jesus christ",
    "harvey",
    "weinstein",
    "sentenced",
    "prison",
)
DEFAULT_HARD_EXCLUDED_TERMS: tuple[str, ...] = (
    "fifa",
    "world cup",
    "nba",
    "nhl",
    "nfl",
    "stanley cup",
    "hockey",
    "soccer",
    "football",
    "super bowl",
    "champions league",
    "album",
    "rihanna",
    "playboi",
    "carti",
    "jesus christ",
    "harvey",
    "weinstein",
)

LIVE_WATCHLIST_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_live_watchlist.csv"
LIVE_MARKET_SNAPSHOTS_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_live_market_snapshots.csv"
)
LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_live_wallet_tier_snapshots.csv"
)
LIVE_EVENT_CANDIDATES_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_live_event_candidates.csv"
LIVE_VALIDATION_REPORT_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_live_input_validation_report.json"
)
LIVE_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_live_collection_metadata.json"


@dataclass(frozen=True)
class ReadOnlyCollectionResult:
    """Summary of generated read-only Polymarket monitor input artifacts."""

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
        """Return a JSON-friendly summary."""

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


def collect_readonly_polymarket_inputs(
    *,
    source: str = "mock",
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = LIVE_EVENT_CANDIDATES_OUTPUT,
    validation_report_path: Path = LIVE_VALIDATION_REPORT_OUTPUT,
    metadata_path: Path = LIVE_METADATA_OUTPUT,
    bucket_minutes: int = DEFAULT_BUCKET_MINUTES,
    max_markets: int = DEFAULT_MAX_MARKETS,
    trade_limit: int = DEFAULT_TRADE_LIMIT,
    collected_at_utc: str | None = None,
    curated_watchlist_path: Path | None = None,
    append: bool = False,
    client: httpx.Client | None = None,
) -> ReadOnlyCollectionResult:
    """Collect, validate, and write read-only monitor v2 input artifacts."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    if bucket_minutes < 1:
        raise ValueError("bucket_minutes must be >= 1")
    if max_markets < 1:
        raise ValueError("max_markets must be >= 1")
    collected_at = _parse_collected_at(collected_at_utc)
    own_client = client is None
    http_client = client or httpx.Client(timeout=20.0)
    try:
        if curated_watchlist_path is None:
            gamma_markets = (
                mock_gamma_markets()
                if source == "mock"
                else fetch_gamma_markets(http_client, limit=max(250, max_markets * 50))
            )
            watchlist = build_watchlist_from_gamma_markets(
                gamma_markets,
                collected_at=collected_at,
                bucket_minutes=bucket_minutes,
                max_markets=max_markets,
            )
        else:
            watchlist = build_watchlist_from_curated_watchlist(
                curated_watchlist_path,
                collected_at=collected_at,
                bucket_minutes=bucket_minutes,
                max_markets=max_markets,
            )
        if watchlist.empty:
            raise ValueError("No active politics/geopolitics Polymarket markets found")

        midpoint_by_token = (
            mock_midpoints_for_watchlist(watchlist)
            if source == "mock"
            else fetch_midpoints_for_watchlist(http_client, watchlist)
        )
        trades = (
            mock_trade_rows(watchlist, collected_at=collected_at)
            if source == "mock"
            else fetch_trade_rows_for_watchlist(
                http_client,
                watchlist,
                limit=trade_limit,
            )
        )
    finally:
        if own_client:
            http_client.close()

    market_snapshots = build_market_snapshot_rows(
        watchlist,
        midpoint_by_token,
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
        source_name=f"polymarket_{source}_clob_midpoint",
    )
    wallet_tier_snapshots = build_wallet_activity_rows(
        watchlist,
        trades,
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
        source_name=f"polymarket_{source}_data_api_trades",
    )
    validated_watchlist = validate_live_market_watch_items(watchlist)
    validated_market = validate_live_market_snapshots(market_snapshots)
    validated_wallets = validate_live_wallet_tier_snapshots(wallet_tier_snapshots)
    validated_events = validate_live_event_candidates(empty_event_candidates_frame())

    written_watchlist = _write_output_frame(
        watchlist_path,
        validated_watchlist,
        append=append,
        dedupe_keys=("market_id",),
    )
    written_market = _write_output_frame(
        market_snapshots_path,
        validated_market,
        append=append,
        dedupe_keys=("bucket_end_utc", "market_id", "token_id"),
    )
    written_wallets = _write_output_frame(
        wallet_tier_snapshots_path,
        validated_wallets,
        append=append,
        dedupe_keys=("bucket_end_utc", "market_id", "tier"),
    )
    written_events = _write_output_frame(
        event_candidates_path,
        validated_events,
        append=append,
        dedupe_keys=("event_candidate_id",),
    )

    validation_report = validate_live_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        report_output_path=validation_report_path,
    )
    written_watchlist = validate_live_market_watch_items(pd.read_csv(watchlist_path))
    written_market = validate_live_market_snapshots(pd.read_csv(market_snapshots_path))
    written_wallets = validate_live_wallet_tier_snapshots(
        pd.read_csv(wallet_tier_snapshots_path)
    )
    written_events = validate_live_event_candidates(pd.read_csv(event_candidates_path))
    metadata = _build_metadata(
        source=source,
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
        max_markets=max_markets,
        trade_limit=trade_limit,
        curated_watchlist_path=curated_watchlist_path,
        append=append,
        watchlist=written_watchlist,
        market_snapshots=written_market,
        wallet_tier_snapshots=written_wallets,
        event_candidates=written_events,
        validation_report=validation_report,
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ReadOnlyCollectionResult(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
        metadata_path=metadata_path,
        watchlist_row_count=len(written_watchlist),
        market_snapshot_row_count=len(written_market),
        wallet_tier_snapshot_row_count=len(written_wallets),
        event_candidate_row_count=len(written_events),
    )


def fetch_gamma_markets(client: httpx.Client, *, limit: int) -> list[dict[str, Any]]:
    """Fetch public Gamma markets."""

    response = client.get(
        f"{GAMMA_BASE_URL}/markets",
        params={
            "limit": limit,
            "active": "true",
            "closed": "false",
            "archived": "false",
        },
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Gamma markets response must be a list")
    return [item for item in data if isinstance(item, dict)]


def fetch_midpoints_for_watchlist(
    client: httpx.Client,
    watchlist: pd.DataFrame,
) -> dict[str, float]:
    """Fetch public CLOB midpoint values for every token in the watchlist."""

    midpoints: dict[str, float] = {}
    for token_id in _token_ids_from_watchlist(watchlist):
        response = client.get(f"{CLOB_BASE_URL}/midpoint", params={"token_id": token_id})
        response.raise_for_status()
        data = response.json()
        midpoint = data.get("mid_price", data.get("mid", data.get("midpoint")))
        if midpoint is None:
            raise ValueError(f"CLOB midpoint response missing midpoint field for token {token_id}")
        midpoints[token_id] = float(midpoint)
    return midpoints


def fetch_trade_rows_for_watchlist(
    client: httpx.Client,
    watchlist: pd.DataFrame,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch public Data API trade rows for watchlist condition ids."""

    condition_ids = sorted(set(watchlist["condition_id"].astype(str)))
    if not condition_ids:
        return []
    response = client.get(
        f"{DATA_API_BASE_URL}/trades",
        params={
            "market": ",".join(condition_ids),
            "limit": limit,
            "takerOnly": "true",
        },
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Data API trades response must be a list")
    return [item for item in data if isinstance(item, dict)]


def build_watchlist_from_gamma_markets(
    markets: Iterable[dict[str, Any]],
    *,
    collected_at: datetime,
    bucket_minutes: int,
    max_markets: int,
    terms: Sequence[str] = DEFAULT_TERMS,
    excluded_terms: Sequence[str] = DEFAULT_EXCLUDED_TERMS,
    hard_excluded_terms: Sequence[str] = DEFAULT_HARD_EXCLUDED_TERMS,
) -> pd.DataFrame:
    """Return validated-shape watchlist rows from Gamma market payloads."""

    base = _base_live_fields(
        source_class="market_discovery",
        source_name="polymarket_gamma_markets",
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    rows: list[dict[str, Any]] = []
    for market in markets:
        if len(rows) >= max_markets:
            break
        token_ids = _parse_list_field(_coalesce(market, "clobTokenIds", "clob_token_ids"))
        condition_id = str(_coalesce(market, "conditionId", "condition_id", default="")).strip()
        if not token_ids or not condition_id:
            continue
        if not _is_active_market(market):
            continue
        if not is_politics_geo_market(
            market,
            terms=terms,
            excluded_terms=excluded_terms,
            hard_excluded_terms=hard_excluded_terms,
        ):
            continue
        market_id = condition_id
        rows.append(
            {
                **base,
                "watch_id": str(_coalesce(market, "id", default=market_id)),
                "market_id": market_id,
                "condition_id": condition_id,
                "token_ids": ",".join(token_ids),
                "question": str(_coalesce(market, "question", "title", default="")),
                "category": str(_coalesce(market, "category", default="politics")),
                "subcategory": str(_coalesce(market, "slug", default="")),
                "status": "active",
            }
        )
    return pd.DataFrame(rows, columns=MARKET_WATCH_LIVE_COLUMNS)


def build_watchlist_from_curated_watchlist(
    path: Path,
    *,
    collected_at: datetime,
    bucket_minutes: int,
    max_markets: int,
) -> pd.DataFrame:
    """Return monitor-ready watchlist rows from accepted curated entries."""

    curated = validate_curated_watchlist(read_curated_watchlist(path))
    accepted = curated[curated["review_status"] == "accepted"].head(max_markets)
    if accepted.empty:
        raise ValueError("curated watchlist has no accepted rows")
    base = _base_live_fields(
        source_class="market_discovery",
        source_name="polymarket_curated_watchlist",
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    rows = [
        {
            **base,
            "watch_id": row["watch_id"],
            "market_id": row["market_id"],
            "condition_id": row["condition_id"],
            "token_ids": row["token_ids"],
            "question": row["question"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "status": "active",
        }
        for row in accepted.to_dict(orient="records")
    ]
    return pd.DataFrame(rows, columns=MARKET_WATCH_LIVE_COLUMNS)


def is_politics_geo_market(
    market: dict[str, Any],
    *,
    terms: Sequence[str] = DEFAULT_TERMS,
    excluded_terms: Sequence[str] = DEFAULT_EXCLUDED_TERMS,
    hard_excluded_terms: Sequence[str] = DEFAULT_HARD_EXCLUDED_TERMS,
) -> bool:
    """Return True when a Gamma market appears politics/geopolitics-related."""

    haystack_parts = [
        str(market.get("question", "")),
        str(market.get("title", "")),
        str(market.get("slug", "")),
        str(market.get("description", "")),
    ]
    for key in ("tags", "events"):
        value = market.get(key)
        if isinstance(value, list):
            haystack_parts.extend(str(item) for item in value)
        elif value is not None:
            haystack_parts.append(str(value))
    haystack = " ".join(haystack_parts).lower()
    if any(term.lower() in haystack for term in hard_excluded_terms):
        return False
    if any(term.lower() in haystack for term in excluded_terms):
        strong_terms = (
            "war",
            "invade",
            "invasion",
            "sanction",
            "election",
            "president",
            "trump",
            "maduro",
            "iran",
            "israel",
            "ukraine",
            "russia",
            "venezuela",
            "china",
            "taiwan",
        )
        return any(term in haystack for term in strong_terms)
    return any(term.lower() in haystack for term in terms)


def build_market_snapshot_rows(
    watchlist: pd.DataFrame,
    midpoint_by_token: dict[str, float],
    *,
    collected_at: datetime,
    bucket_minutes: int,
    source_name: str,
) -> pd.DataFrame:
    """Build monitor-facing market snapshot rows from midpoint values."""

    base = _base_live_fields(
        source_class="market_state",
        source_name=source_name,
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    rows: list[dict[str, Any]] = []
    for item in watchlist.to_dict(orient="records"):
        for token_id in _parse_list_field(str(item["token_ids"])):
            midpoint = midpoint_by_token.get(token_id)
            if midpoint is None:
                continue
            rows.append(
                {
                    **base,
                    "market_id": item["market_id"],
                    "token_id": token_id,
                    "price": midpoint,
                    "midpoint": midpoint,
                    "best_bid": None,
                    "best_ask": None,
                    "spread": None,
                    "volume": None,
                    "open_interest": None,
                }
            )
    if not rows:
        raise ValueError("No CLOB midpoint values available for selected watchlist")
    return pd.DataFrame(rows, columns=MARKET_SNAPSHOT_LIVE_COLUMNS)


def build_wallet_activity_rows(
    watchlist: pd.DataFrame,
    trades: list[dict[str, Any]],
    *,
    collected_at: datetime,
    bucket_minutes: int,
    source_name: str,
) -> pd.DataFrame:
    """Aggregate public trade rows into wallet/activity monitor snapshots."""

    base = _base_live_fields(
        source_class="wallet_activity",
        source_name=source_name,
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    bucket_start, bucket_end = _closed_bucket_window(
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    market_ids = sorted(set(watchlist["market_id"].astype(str)))
    grouped: dict[str, list[dict[str, Any]]] = {market_id: [] for market_id in market_ids}
    for trade in trades:
        condition_id = str(trade.get("conditionId", trade.get("condition_id", ""))).strip()
        if condition_id not in grouped:
            continue
        timestamp = _trade_timestamp(trade)
        if timestamp is None or not (bucket_start <= timestamp < bucket_end):
            continue
        grouped[condition_id].append(trade)

    rows: list[dict[str, Any]] = []
    for market_id, market_trades in grouped.items():
        amount_by_wallet: dict[str, float] = {}
        for trade in market_trades:
            wallet = str(trade.get("proxyWallet", trade.get("user", ""))).strip()
            if not wallet:
                wallet = "unknown_wallet"
            amount = _trade_amount_usd(trade)
            amount_by_wallet[wallet] = amount_by_wallet.get(wallet, 0.0) + amount
        total_amount = float(sum(amount_by_wallet.values()))
        shares = [
            amount / total_amount
            for amount in amount_by_wallet.values()
            if total_amount > 0 and amount > 0
        ]
        rows.append(
            {
                **base,
                "market_id": market_id,
                "tier": "all_tiers",
                "active_wallets": len(amount_by_wallet),
                "trade_count": len(market_trades),
                "total_observed_amount_usd": total_amount,
                "top_tier_share": max(shares) if shares else 0.0,
                "hhi_concentration": sum(share * share for share in shares) if shares else 0.0,
                "filter_metadata": (
                    "polymarket_data_api_trades_aggregate_no_wallet_addresses"
                ),
            }
        )
    return pd.DataFrame(rows, columns=WALLET_TIER_SNAPSHOT_LIVE_COLUMNS)


def mock_gamma_markets() -> list[dict[str, Any]]:
    """Return a deterministic Gamma-style mock payload."""

    return [
        {
            "id": "mock_gamma_market_001",
            "question": "Will a major election or war event move this market?",
            "conditionId": "0x" + "a" * 64,
            "slug": "mock-politics-geo-market",
            "category": "Politics",
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["111", "222"]),
        },
        {
            "id": "mock_gamma_market_002",
            "question": "Will a sports team win?",
            "conditionId": "0x" + "b" * 64,
            "slug": "mock-sports-market",
            "category": "Sports",
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["333", "444"]),
        },
    ]


def mock_midpoints_for_watchlist(watchlist: pd.DataFrame) -> dict[str, float]:
    """Return deterministic midpoint values for watchlist token ids."""

    values: dict[str, float] = {}
    for index, token_id in enumerate(_token_ids_from_watchlist(watchlist)):
        values[token_id] = round(0.52 + (index * 0.02), 4)
    return values


def mock_trade_rows(
    watchlist: pd.DataFrame,
    *,
    collected_at: datetime,
) -> list[dict[str, Any]]:
    """Return deterministic Data-API-style trade rows for the closed bucket."""

    _, bucket_end = _closed_bucket_window(
        collected_at=collected_at,
        bucket_minutes=DEFAULT_BUCKET_MINUTES,
    )
    timestamp = int((bucket_end - pd.Timedelta(minutes=1)).timestamp())
    condition_id = str(watchlist.iloc[0]["condition_id"])
    return [
        {
            "proxyWallet": "0x" + "1" * 40,
            "conditionId": condition_id,
            "size": 100.0,
            "price": 0.52,
            "timestamp": timestamp,
            "side": "BUY",
        },
        {
            "proxyWallet": "0x" + "2" * 40,
            "conditionId": condition_id,
            "size": 50.0,
            "price": 0.54,
            "timestamp": timestamp,
            "side": "SELL",
        },
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--watchlist-output", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots-output", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument(
        "--wallet-tier-snapshots-output",
        type=Path,
        default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    )
    parser.add_argument("--event-candidates-output", type=Path, default=LIVE_EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--validation-report-output", type=Path, default=LIVE_VALIDATION_REPORT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=LIVE_METADATA_OUTPUT)
    parser.add_argument("--bucket-minutes", type=int, default=DEFAULT_BUCKET_MINUTES)
    parser.add_argument("--max-markets", type=int, default=DEFAULT_MAX_MARKETS)
    parser.add_argument("--trade-limit", type=int, default=DEFAULT_TRADE_LIMIT)
    parser.add_argument("--collected-at-utc", default=None)
    parser.add_argument("--curated-watchlist-input", type=Path, default=None)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = collect_readonly_polymarket_inputs(
            source=args.source,
            watchlist_path=args.watchlist_output,
            market_snapshots_path=args.market_snapshots_output,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots_output,
            event_candidates_path=args.event_candidates_output,
            validation_report_path=args.validation_report_output,
            metadata_path=args.metadata_output,
            bucket_minutes=args.bucket_minutes,
            max_markets=args.max_markets,
            trade_limit=args.trade_limit,
            collected_at_utc=args.collected_at_utc,
            curated_watchlist_path=args.curated_watchlist_input,
            append=args.append,
        )
    except (httpx.HTTPError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _base_live_fields(
    *,
    source_class: str,
    source_name: str,
    collected_at: datetime,
    bucket_minutes: int,
) -> dict[str, str]:
    bucket_start, bucket_end = _closed_bucket_window(
        collected_at=collected_at,
        bucket_minutes=bucket_minutes,
    )
    return {
        "collector_received_at_utc": _format_timestamp(collected_at),
        "source_timestamp_utc": "",
        "bucket_start_utc": _format_timestamp(bucket_start),
        "bucket_end_utc": _format_timestamp(bucket_end),
        "timestamp_source": "collector",
        "bucket_status": "closed",
        "source_class": source_class,
        "source_name": source_name,
    }


def _closed_bucket_window(
    *,
    collected_at: datetime,
    bucket_minutes: int,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    collected = pd.Timestamp(collected_at).tz_convert("UTC")
    minute = collected.minute - (collected.minute % bucket_minutes)
    bucket_end = collected.replace(minute=minute, second=0, microsecond=0)
    bucket_start = bucket_end - pd.Timedelta(minutes=bucket_minutes)
    return bucket_start, bucket_end


def _parse_collected_at(value: str | None) -> datetime:
    if value is None or not str(value).strip():
        return datetime.now(UTC).replace(microsecond=0)
    candidate = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        raise ValueError("collected_at_utc must include a UTC offset")
    return parsed.astimezone(UTC).replace(microsecond=0)


def _format_timestamp(value: datetime | pd.Timestamp) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _token_ids_from_watchlist(watchlist: pd.DataFrame) -> list[str]:
    token_ids: list[str] = []
    for value in watchlist["token_ids"].astype(str):
        token_ids.extend(_parse_list_field(value))
    return list(dict.fromkeys(token_ids))


def _parse_list_field(value: Any) -> list[str]:
    if value is None:
        return []
    candidate = str(value).strip()
    if not candidate or candidate.lower() in {"nan", "none", "null"}:
        return []
    if candidate.startswith("["):
        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            raise ValueError("list field JSON must decode to a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in candidate.replace(";", ",").split(",") if item.strip()]


def _coalesce(market: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = market.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return default


def _is_active_market(market: dict[str, Any]) -> bool:
    active = bool(market.get("active", True))
    closed = bool(market.get("closed", False))
    archived = bool(market.get("archived", False))
    return active and not closed and not archived


def _trade_timestamp(trade: dict[str, Any]) -> pd.Timestamp | None:
    value = trade.get("timestamp")
    if value is None:
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000.0
    return pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))


def _trade_amount_usd(trade: dict[str, Any]) -> float:
    size = _safe_float(trade.get("size"))
    price = _safe_float(trade.get("price"))
    return max(size * price, 0.0)


def _safe_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def empty_event_candidates_frame() -> pd.DataFrame:
    """Return an empty validated-shape event candidate frame.

    Live event/news collection is intentionally separate from the first
    read-only market collector. The empty file keeps the monitor-v2 input
    contract complete without inventing events.
    """

    return pd.DataFrame(columns=EVENT_CANDIDATE_LIVE_COLUMNS)


def _write_output_frame(
    path: Path,
    frame: pd.DataFrame,
    *,
    append: bool,
    dedupe_keys: Sequence[str],
) -> pd.DataFrame:
    """Write a frame and optionally append/dedupe existing rows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    output = frame.copy()
    if append and path.exists():
        existing = pd.read_csv(path)
        output = pd.concat([existing, output], ignore_index=True)
        keys = [key for key in dedupe_keys if key in output.columns]
        if keys and not output.empty:
            normalized_keys = output.loc[:, keys].astype(str)
            duplicate_mask = normalized_keys.duplicated(keep="last")
            output = output.loc[~duplicate_mask].reset_index(drop=True)
    output.to_csv(path, index=False)
    return output


def _build_metadata(
    *,
    source: str,
    collected_at: datetime,
    bucket_minutes: int,
    max_markets: int,
    trade_limit: int,
    curated_watchlist_path: Path | None,
    append: bool,
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
    validation_report: dict[str, Any],
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path,
) -> dict[str, Any]:
    return {
        "generated_at_utc": _format_timestamp(datetime.now(UTC).replace(microsecond=0)),
        "method": {
            "name": "polymarket_readonly_collector",
            "source": source,
            "bucket_minutes": bucket_minutes,
            "max_markets": max_markets,
            "trade_limit": trade_limit,
            "collector_received_at_utc": _format_timestamp(collected_at),
            "uses_public_gamma_markets": source == "live" and curated_watchlist_path is None,
            "uses_curated_watchlist": curated_watchlist_path is not None,
            "curated_watchlist_path": (
                "" if curated_watchlist_path is None else str(curated_watchlist_path)
            ),
            "accepted_curated_rows_only": curated_watchlist_path is not None,
            "uses_public_clob_midpoint": source == "live",
            "uses_public_data_api_trades": source == "live",
            "validates_outputs": True,
            "read_only": True,
            "append_to_existing_outputs": append,
        },
        "endpoints": {
            "gamma_markets": f"{GAMMA_BASE_URL}/markets",
            "clob_midpoint": f"{CLOB_BASE_URL}/midpoint",
            "data_api_trades": f"{DATA_API_BASE_URL}/trades",
        },
        "outputs": {
            "watchlist_path": str(watchlist_path),
            "market_snapshots_path": str(market_snapshots_path),
            "wallet_tier_snapshots_path": str(wallet_tier_snapshots_path),
            "event_candidates_path": str(event_candidates_path),
            "validation_report_path": str(validation_report_path),
            "watchlist_row_count": int(len(watchlist)),
            "market_snapshot_row_count": int(len(market_snapshots)),
            "wallet_tier_snapshot_row_count": int(len(wallet_tier_snapshots)),
            "event_candidate_row_count": int(len(event_candidates)),
            "validation_status": validation_report["status"],
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "read_only_public_endpoints_only": True,
            "no_authenticated_user_channel": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
            "wallet_rows_are_aggregate_all_tiers": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
