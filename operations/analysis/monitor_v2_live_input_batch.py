"""Generate local replay-first monitor v2 live-style input files.

This prototype writes mocked local input files for the future live-capable
Polymarket politics/geo monitor and validates them immediately. It does not
call external APIs, WebSockets, databases, LLMs, agents, MCP tools, ML systems,
or order-execution paths.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
from pydantic import ValidationError

from operations.analysis.monitor_v2_live_input_validation import (
    EVENT_CANDIDATE_LIVE_COLUMNS,
    MARKET_SNAPSHOT_LIVE_COLUMNS,
    MARKET_WATCH_LIVE_COLUMNS,
    REPORT_OUTPUT,
    WALLET_TIER_SNAPSHOT_LIVE_COLUMNS,
    validate_live_event_candidates,
    validate_live_input_files,
    validate_live_market_snapshots,
    validate_live_market_watch_items,
    validate_live_wallet_tier_snapshots,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR


LIVE_WATCHLIST_OUTPUT = RESULTS_DIR / "monitor_v2_live_watchlist.csv"
LIVE_MARKET_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_live_market_snapshots.csv"
LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT = RESULTS_DIR / "monitor_v2_live_wallet_tier_snapshots.csv"
LIVE_EVENT_CANDIDATES_OUTPUT = RESULTS_DIR / "monitor_v2_live_event_candidates.csv"
LIVE_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_live_inputs_metadata.json"

DEFAULT_MARKET_ID = "mock_polymarket_politics_geo_001"
DEFAULT_GENERATED_AT_UTC = "2026-05-20T00:30:00Z"


@dataclass(frozen=True)
class LiveInputBatchResult:
    """Summary of generated local monitor v2 live-style input artifacts."""

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


def generate_local_live_input_batch(
    *,
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    market_snapshots_path: Path = LIVE_MARKET_SNAPSHOTS_OUTPUT,
    wallet_tier_snapshots_path: Path = LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    event_candidates_path: Path = LIVE_EVENT_CANDIDATES_OUTPUT,
    validation_report_path: Path = REPORT_OUTPUT,
    metadata_path: Path = LIVE_METADATA_OUTPUT,
    market_id: str = DEFAULT_MARKET_ID,
    generated_at_utc: str = DEFAULT_GENERATED_AT_UTC,
) -> LiveInputBatchResult:
    """Write and validate local replay-first live-style input files."""

    watchlist = build_mock_live_watchlist(market_id=market_id)
    market_snapshots = build_mock_live_market_snapshots(market_id=market_id)
    wallet_tier_snapshots = build_mock_live_wallet_tier_snapshots(market_id=market_id)
    event_candidates = build_mock_live_event_candidates(market_id=market_id)

    validated_watchlist = validate_live_market_watch_items(watchlist)
    validated_market = validate_live_market_snapshots(market_snapshots)
    validated_wallets = validate_live_wallet_tier_snapshots(wallet_tier_snapshots)
    validated_events = validate_live_event_candidates(event_candidates)
    validate_live_batch_consistency(
        watchlist=validated_watchlist,
        market_snapshots=validated_market,
        wallet_tier_snapshots=validated_wallets,
        event_candidates=validated_events,
    )

    for path, frame in (
        (watchlist_path, validated_watchlist),
        (market_snapshots_path, validated_market),
        (wallet_tier_snapshots_path, validated_wallets),
        (event_candidates_path, validated_events),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    validation_report = validate_live_input_files(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        report_output_path=None,
    )
    validation_report["generated_at_utc"] = generated_at_utc
    validation_report_path.parent.mkdir(parents=True, exist_ok=True)
    validation_report_path.write_text(
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            _build_metadata(
                generated_at_utc=generated_at_utc,
                watchlist_path=watchlist_path,
                market_snapshots_path=market_snapshots_path,
                wallet_tier_snapshots_path=wallet_tier_snapshots_path,
                event_candidates_path=event_candidates_path,
                validation_report_path=validation_report_path,
                watchlist=validated_watchlist,
                market_snapshots=validated_market,
                wallet_tier_snapshots=validated_wallets,
                event_candidates=validated_events,
                validation_report=validation_report,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return LiveInputBatchResult(
        watchlist_path=watchlist_path,
        market_snapshots_path=market_snapshots_path,
        wallet_tier_snapshots_path=wallet_tier_snapshots_path,
        event_candidates_path=event_candidates_path,
        validation_report_path=validation_report_path,
        metadata_path=metadata_path,
        watchlist_row_count=len(validated_watchlist),
        market_snapshot_row_count=len(validated_market),
        wallet_tier_snapshot_row_count=len(validated_wallets),
        event_candidate_row_count=len(validated_events),
    )


def build_mock_live_watchlist(*, market_id: str = DEFAULT_MARKET_ID) -> pd.DataFrame:
    """Return one mocked live-style politics/geo watchlist row."""

    return pd.DataFrame(
        [
            {
                **_base_live_fields("market_discovery", "2026-05-20T00:00:00Z"),
                "watch_id": "watch_mock_politics_geo_001",
                "market_id": market_id,
                "condition_id": "mock_condition_001",
                "token_ids": "yes_token,no_token",
                "question": "Mock politics/geopolitics market for replay-first monitor v2",
                "category": "politics",
                "subcategory": "geopolitics",
                "status": "active",
            }
        ],
        columns=MARKET_WATCH_LIVE_COLUMNS,
    )


def build_mock_live_market_snapshots(*, market_id: str = DEFAULT_MARKET_ID) -> pd.DataFrame:
    """Return deterministic mocked market-state rows for 15-minute buckets."""

    rows = []
    prices = (0.50, 0.52, 0.56, 0.55)
    volumes = (1000.0, 1125.0, 1840.0, 1550.0)
    for index, bucket_start in enumerate(_bucket_starts()):
        price = prices[index]
        rows.append(
            {
                **_base_live_fields("market_state", bucket_start),
                "market_id": market_id,
                "token_id": "yes_token",
                "price": price,
                "midpoint": price,
                "best_bid": round(price - 0.01, 4),
                "best_ask": round(price + 0.01, 4),
                "spread": 0.02,
                "volume": volumes[index],
                "open_interest": 5000.0 + (index * 100.0),
            }
        )
    return pd.DataFrame(rows, columns=MARKET_SNAPSHOT_LIVE_COLUMNS)


def build_mock_live_wallet_tier_snapshots(*, market_id: str = DEFAULT_MARKET_ID) -> pd.DataFrame:
    """Return deterministic mocked aggregate wallet-tier rows."""

    rows = []
    tiers = ("tier_1_top_1pct", "tier_4_observed_baseline")
    amount_by_bucket = (
        (25000.0, 45000.0),
        (42000.0, 50000.0),
        (125000.0, 62000.0),
        (64000.0, 58000.0),
    )
    active_by_bucket = ((2, 14), (3, 17), (7, 22), (4, 18))
    for bucket_index, bucket_start in enumerate(_bucket_starts()):
        for tier_index, tier in enumerate(tiers):
            rows.append(
                {
                    **_base_live_fields("wallet_activity", bucket_start),
                    "market_id": market_id,
                    "tier": tier,
                    "active_wallets": active_by_bucket[bucket_index][tier_index],
                    "trade_count": active_by_bucket[bucket_index][tier_index] + 1,
                    "total_observed_amount_usd": amount_by_bucket[bucket_index][tier_index],
                    "top_tier_share": 0.67 if tier == "tier_1_top_1pct" else 0.67,
                    "hhi_concentration": 0.51,
                    "filter_metadata": "mocked_replay_no_wallet_addresses",
                }
            )
    return pd.DataFrame(rows, columns=WALLET_TIER_SNAPSHOT_LIVE_COLUMNS)


def build_mock_live_event_candidates(*, market_id: str = DEFAULT_MARKET_ID) -> pd.DataFrame:
    """Return one reviewed mocked politics/geo event candidate row."""

    return pd.DataFrame(
        [
            {
                **_base_live_fields("event_candidates", "2026-05-20T00:15:00Z"),
                "event_candidate_id": "event_candidate_mock_geo_001",
                "detected_at_utc": "2026-05-20T00:27:00Z",
                "published_at_utc": "2026-05-20T00:24:00Z",
                "title": "Mock reviewed politics/geopolitics event",
                "source_url": "https://example.com/mock-politics-geo-event",
                "event_type": "geopolitical_news",
                "related_market_ids": market_id,
                "expected_effect": "uncertainty_change",
                "review_status": "accepted",
                "review_notes": "mocked local fixture; not a real event",
            }
        ],
        columns=EVENT_CANDIDATE_LIVE_COLUMNS,
    )


def validate_live_batch_consistency(
    *,
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
) -> None:
    """Validate cross-file market consistency for generated live-style inputs."""

    watch_markets = set(watchlist["market_id"].astype(str))
    if not watch_markets:
        raise ValueError("live watchlist contains no market_id values")
    for name, frame in (
        ("live market snapshots", market_snapshots),
        ("live wallet-tier snapshots", wallet_tier_snapshots),
    ):
        unknown = sorted(set(frame["market_id"].astype(str)) - watch_markets)
        if unknown:
            raise ValueError(f"{name} contain market_id values outside watchlist: {unknown}")
    for row in event_candidates.to_dict(orient="records"):
        related = set(_parse_list_field(str(row["related_market_ids"])))
        if str(row["review_status"]) in {"market_mapped", "accepted"}:
            if not related.intersection(watch_markets):
                raise ValueError(
                    "mapped or accepted event candidates must reference a watchlist market"
                )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist-output", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--market-snapshots-output", type=Path, default=LIVE_MARKET_SNAPSHOTS_OUTPUT)
    parser.add_argument(
        "--wallet-tier-snapshots-output",
        type=Path,
        default=LIVE_WALLET_TIER_SNAPSHOTS_OUTPUT,
    )
    parser.add_argument("--event-candidates-output", type=Path, default=LIVE_EVENT_CANDIDATES_OUTPUT)
    parser.add_argument("--validation-report-output", type=Path, default=REPORT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=LIVE_METADATA_OUTPUT)
    parser.add_argument("--market-id", default=DEFAULT_MARKET_ID)
    parser.add_argument("--generated-at-utc", default=DEFAULT_GENERATED_AT_UTC)
    args = parser.parse_args(argv)

    try:
        result = generate_local_live_input_batch(
            watchlist_path=args.watchlist_output,
            market_snapshots_path=args.market_snapshots_output,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots_output,
            event_candidates_path=args.event_candidates_output,
            validation_report_path=args.validation_report_output,
            metadata_path=args.metadata_output,
            market_id=args.market_id,
            generated_at_utc=args.generated_at_utc,
        )
    except (FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _base_live_fields(source_class: str, bucket_start_utc: str) -> dict[str, str]:
    start = pd.Timestamp(bucket_start_utc, tz="UTC")
    end = start + pd.Timedelta(minutes=15)
    source_timestamp = end - pd.Timedelta(seconds=30)
    collector_received = end + pd.Timedelta(seconds=5)
    return {
        "collector_received_at_utc": _format_timestamp(collector_received),
        "source_timestamp_utc": _format_timestamp(source_timestamp),
        "bucket_start_utc": _format_timestamp(start),
        "bucket_end_utc": _format_timestamp(end),
        "timestamp_source": "source",
        "bucket_status": "closed",
        "source_class": source_class,
        "source_name": "mocked_local_replay_fixture",
    }


def _bucket_starts() -> tuple[str, ...]:
    return (
        "2026-05-20T00:00:00Z",
        "2026-05-20T00:15:00Z",
        "2026-05-20T00:30:00Z",
        "2026-05-20T00:45:00Z",
    )


def _format_timestamp(value: pd.Timestamp) -> str:
    return value.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_list_field(value: str) -> list[str]:
    candidate = value.strip()
    if not candidate:
        return []
    if candidate.startswith("["):
        parsed = json.loads(candidate)
        if not isinstance(parsed, list):
            raise ValueError("list field JSON must decode to a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in candidate.replace(";", ",").split(",") if item.strip()]


def _build_metadata(
    *,
    generated_at_utc: str,
    watchlist_path: Path,
    market_snapshots_path: Path,
    wallet_tier_snapshots_path: Path,
    event_candidates_path: Path,
    validation_report_path: Path,
    watchlist: pd.DataFrame,
    market_snapshots: pd.DataFrame,
    wallet_tier_snapshots: pd.DataFrame,
    event_candidates: pd.DataFrame,
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": generated_at_utc,
        "method": {
            "name": "monitor_v2_live_input_batch",
            "input_mode": "mocked_local_replay_fixture",
            "bucket_minutes": 15,
            "validates_outputs": True,
            "checks_cross_file_market_consistency": True,
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
            "mocked_local_fixture_only": True,
            "does_not_call_external_apis": True,
            "does_not_connect_to_websocket": True,
            "does_not_write_database": True,
            "does_not_score_alerts": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
