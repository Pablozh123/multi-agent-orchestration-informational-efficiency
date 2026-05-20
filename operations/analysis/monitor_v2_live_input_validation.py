"""Validate replay-first monitor v2 live input CSV files.

This module defines the local file boundary for the future live-capable
Polymarket politics/geo monitor. It validates mocked or replayed CSV inputs
only and does not call external APIs, WebSockets, databases, LLMs, agents, MCP
tools, ML systems, or order-execution paths.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Sequence

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_distribution_inventory import TIER_ORDER


REPORT_OUTPUT = RESULTS_DIR / "monitor_v2_live_input_validation_report.json"

TIMESTAMP_COLUMNS: tuple[str, ...] = (
    "collector_received_at_utc",
    "source_timestamp_utc",
    "bucket_start_utc",
    "bucket_end_utc",
    "timestamp_source",
    "bucket_status",
)
SOURCE_COLUMNS: tuple[str, ...] = (
    "source_class",
    "source_name",
)
MARKET_WATCH_LIVE_COLUMNS: tuple[str, ...] = (
    *TIMESTAMP_COLUMNS,
    *SOURCE_COLUMNS,
    "watch_id",
    "market_id",
    "condition_id",
    "token_ids",
    "question",
    "category",
    "subcategory",
    "status",
)
MARKET_SNAPSHOT_LIVE_COLUMNS: tuple[str, ...] = (
    *TIMESTAMP_COLUMNS,
    *SOURCE_COLUMNS,
    "market_id",
    "token_id",
    "price",
    "midpoint",
    "best_bid",
    "best_ask",
    "spread",
    "volume",
    "open_interest",
)
WALLET_TIER_SNAPSHOT_LIVE_COLUMNS: tuple[str, ...] = (
    *TIMESTAMP_COLUMNS,
    *SOURCE_COLUMNS,
    "market_id",
    "tier",
    "active_wallets",
    "trade_count",
    "total_observed_amount_usd",
    "top_tier_share",
    "hhi_concentration",
    "filter_metadata",
)
EVENT_CANDIDATE_LIVE_COLUMNS: tuple[str, ...] = (
    *TIMESTAMP_COLUMNS,
    *SOURCE_COLUMNS,
    "event_candidate_id",
    "detected_at_utc",
    "published_at_utc",
    "title",
    "source_url",
    "event_type",
    "related_market_ids",
    "expected_effect",
    "review_status",
    "review_notes",
)

SOURCE_CLASSES = {
    "market_discovery",
    "market_state",
    "wallet_activity",
    "event_candidates",
}
WATCHLIST_STATUSES = {"candidate", "active", "paused", "closed", "archived"}
EVENT_REVIEW_STATUSES = {
    "candidate",
    "source_checked",
    "market_mapped",
    "accepted",
    "rejected",
    "needs_followup",
}
ALLOWED_TIERS = {*TIER_ORDER, "all_tiers"}


class LiveInputBaseRow(BaseModel):
    """Shared timestamp and source fields for replay-first live inputs."""

    collector_received_at_utc: str
    source_timestamp_utc: str | None = ""
    bucket_start_utc: str
    bucket_end_utc: str
    timestamp_source: Literal["source", "collector", "derived"]
    bucket_status: Literal["closed", "open", "diagnostic"]
    source_class: Literal[
        "market_discovery",
        "market_state",
        "wallet_activity",
        "event_candidates",
    ]
    source_name: str

    @field_validator(
        "collector_received_at_utc",
        "bucket_start_utc",
        "bucket_end_utc",
        mode="before",
    )
    @classmethod
    def _required_datetime(cls, value: str) -> str:
        return _ensure_utc_datetime(value)

    @field_validator("source_timestamp_utc", mode="before")
    @classmethod
    def _optional_source_datetime(cls, value: str | None) -> str:
        if value is None or str(value).strip() == "":
            return ""
        return _ensure_utc_datetime(value)

    @field_validator("source_name", mode="before")
    @classmethod
    def _source_name(cls, value: str) -> str:
        return _non_empty_str(value)

    @model_validator(mode="after")
    def _timestamp_contract(self) -> "LiveInputBaseRow":
        bucket_start = _parse_utc_datetime(self.bucket_start_utc)
        bucket_end = _parse_utc_datetime(self.bucket_end_utc)
        collector_received = _parse_utc_datetime(self.collector_received_at_utc)
        if bucket_start >= bucket_end:
            raise ValueError("bucket_start_utc must be before bucket_end_utc")
        if self.bucket_status == "closed" and collector_received < bucket_end:
            raise ValueError("closed buckets require collector_received_at_utc >= bucket_end_utc")
        if self.timestamp_source == "source" and not self.source_timestamp_utc:
            raise ValueError("source_timestamp_utc is required when timestamp_source=source")
        return self


class MarketWatchLiveRow(LiveInputBaseRow):
    """One replay-first live watchlist row."""

    watch_id: str
    market_id: str
    condition_id: str
    token_ids: str
    question: str
    category: str
    subcategory: str = ""
    status: Literal["candidate", "active", "paused", "closed", "archived"]

    @field_validator(
        "watch_id",
        "market_id",
        "condition_id",
        "token_ids",
        "question",
        "category",
        "status",
        mode="before",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("token_ids")
    @classmethod
    def _token_ids(cls, value: str) -> str:
        if not _parse_list_field(value):
            raise ValueError("token_ids must contain at least one token id")
        return value

    @model_validator(mode="after")
    def _source_class_contract(self) -> "MarketWatchLiveRow":
        if self.source_class != "market_discovery":
            raise ValueError("watchlist rows require source_class=market_discovery")
        return self


class MarketSnapshotLiveRow(LiveInputBaseRow):
    """One replay-first market-state snapshot row."""

    market_id: str
    token_id: str
    price: float | None = Field(default=None, ge=0.0, le=1.0)
    midpoint: float | None = Field(default=None, ge=0.0, le=1.0)
    best_bid: float | None = Field(default=None, ge=0.0, le=1.0)
    best_ask: float | None = Field(default=None, ge=0.0, le=1.0)
    spread: float | None = Field(default=None, ge=0.0)
    volume: float | None = Field(default=None, ge=0.0)
    open_interest: float | None = Field(default=None, ge=0.0)

    @field_validator("market_id", "token_id", mode="before")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @model_validator(mode="after")
    def _market_snapshot_contract(self) -> "MarketSnapshotLiveRow":
        if self.source_class != "market_state":
            raise ValueError("market snapshots require source_class=market_state")
        if self.price is None and self.midpoint is None:
            raise ValueError("market snapshot requires price or midpoint")
        if self.best_bid is not None and self.best_ask is not None:
            if self.best_bid > self.best_ask:
                raise ValueError("best_bid must be <= best_ask")
        return self


class WalletTierSnapshotLiveRow(LiveInputBaseRow):
    """One replay-first aggregate wallet-tier snapshot row."""

    market_id: str
    tier: str
    active_wallets: int = Field(ge=0)
    trade_count: int = Field(ge=0)
    total_observed_amount_usd: float = Field(ge=0.0)
    top_tier_share: float | None = Field(default=None, ge=0.0, le=1.0)
    hhi_concentration: float | None = Field(default=None, ge=0.0, le=1.0)
    filter_metadata: str

    @field_validator("market_id", "tier", "filter_metadata", mode="before")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("tier")
    @classmethod
    def _known_tier(cls, value: str) -> str:
        if value not in ALLOWED_TIERS:
            raise ValueError(f"tier must be one of {sorted(ALLOWED_TIERS)}")
        return value

    @model_validator(mode="after")
    def _wallet_snapshot_contract(self) -> "WalletTierSnapshotLiveRow":
        if self.source_class != "wallet_activity":
            raise ValueError("wallet-tier snapshots require source_class=wallet_activity")
        return self


class EventCandidateLiveRow(LiveInputBaseRow):
    """One replay-first politics/geo event candidate row."""

    event_candidate_id: str
    detected_at_utc: str
    published_at_utc: str
    title: str
    source_url: str = ""
    event_type: str
    related_market_ids: str = ""
    expected_effect: str
    review_status: Literal[
        "candidate",
        "source_checked",
        "market_mapped",
        "accepted",
        "rejected",
        "needs_followup",
    ]
    review_notes: str = ""

    @field_validator(
        "event_candidate_id",
        "detected_at_utc",
        "published_at_utc",
        "title",
        "event_type",
        "expected_effect",
        "review_status",
        mode="before",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("detected_at_utc", "published_at_utc", mode="before")
    @classmethod
    def _event_datetime(cls, value: str) -> str:
        return _ensure_utc_datetime(value)

    @model_validator(mode="after")
    def _event_contract(self) -> "EventCandidateLiveRow":
        if self.source_class != "event_candidates":
            raise ValueError("event candidates require source_class=event_candidates")
        if self.review_status in {"source_checked", "market_mapped", "accepted"}:
            if not self.source_url.strip():
                raise ValueError("source_url is required for checked event candidates")
        if self.review_status in {"market_mapped", "accepted"}:
            if not _parse_list_field(self.related_market_ids):
                raise ValueError("related_market_ids are required for mapped event candidates")
        if self.review_status == "accepted":
            detected = _parse_utc_datetime(self.detected_at_utc)
            published = _parse_utc_datetime(self.published_at_utc)
            if detected < published:
                raise ValueError("accepted event detected_at_utc must be >= published_at_utc")
        return self


def validate_live_market_watch_items(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate replay-first live watchlist rows."""

    return _validate_frame(frame, MARKET_WATCH_LIVE_COLUMNS, MarketWatchLiveRow, "live watchlist")


def validate_live_market_snapshots(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate replay-first live market-state snapshot rows."""

    return _validate_frame(
        frame,
        MARKET_SNAPSHOT_LIVE_COLUMNS,
        MarketSnapshotLiveRow,
        "live market snapshots",
    )


def validate_live_wallet_tier_snapshots(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate replay-first live aggregate wallet-tier snapshot rows."""

    return _validate_frame(
        frame,
        WALLET_TIER_SNAPSHOT_LIVE_COLUMNS,
        WalletTierSnapshotLiveRow,
        "live wallet-tier snapshots",
    )


def validate_live_event_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate replay-first live event candidate rows."""

    return _validate_frame(
        frame,
        EVENT_CANDIDATE_LIVE_COLUMNS,
        EventCandidateLiveRow,
        "live event candidates",
    )


def validate_live_input_files(
    *,
    watchlist_path: Path | None = None,
    market_snapshots_path: Path | None = None,
    wallet_tier_snapshots_path: Path | None = None,
    event_candidates_path: Path | None = None,
    report_output_path: Path | None = None,
) -> dict[str, Any]:
    """Validate provided replay-first live input files and optionally write a report."""

    inputs = {
        "watchlist": watchlist_path,
        "market_snapshots": market_snapshots_path,
        "wallet_tier_snapshots": wallet_tier_snapshots_path,
        "event_candidates": event_candidates_path,
    }
    if all(path is None for path in inputs.values()):
        raise ValueError("At least one monitor v2 live input CSV path must be provided")

    validators = {
        "watchlist": validate_live_market_watch_items,
        "market_snapshots": validate_live_market_snapshots,
        "wallet_tier_snapshots": validate_live_wallet_tier_snapshots,
        "event_candidates": validate_live_event_candidates,
    }
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "status": "pass",
        "input_mode": "replay_first_live_input_files",
        "validated_inputs": {},
        "limitations": {
            "local_csv_files_only": True,
            "does_not_call_external_apis": True,
            "does_not_connect_to_websocket": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }
    for name, path in inputs.items():
        if path is None:
            continue
        if not path.exists():
            raise FileNotFoundError(f"Monitor v2 live input file not found: {path}")
        frame = pd.read_csv(path)
        validated = validators[name](frame)
        report["validated_inputs"][name] = {
            "path": str(path),
            "row_count": int(len(validated)),
            "columns": list(validated.columns),
            "source_classes": sorted(validated["source_class"].dropna().astype(str).unique()),
            "bucket_status_counts": _value_counts(validated, "bucket_status"),
        }

    if report_output_path is not None:
        report_output_path.parent.mkdir(parents=True, exist_ok=True)
        report_output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchlist", type=Path, default=None)
    parser.add_argument("--market-snapshots", type=Path, default=None)
    parser.add_argument("--wallet-tier-snapshots", type=Path, default=None)
    parser.add_argument("--event-candidates", type=Path, default=None)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT)
    args = parser.parse_args(argv)

    try:
        report = validate_live_input_files(
            watchlist_path=args.watchlist,
            market_snapshots_path=args.market_snapshots,
            wallet_tier_snapshots_path=args.wallet_tier_snapshots,
            event_candidates_path=args.event_candidates,
            report_output_path=args.report_output,
        )
    except (FileNotFoundError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _validate_frame(
    frame: pd.DataFrame,
    columns: Sequence[str],
    model_cls: type[BaseModel],
    name: str,
) -> pd.DataFrame:
    _assert_no_wallet_address_fields(frame, name)
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")
    subset = frame.loc[:, list(columns)].copy()
    models = [model_cls.model_validate(_clean_row(row)) for row in subset.to_dict(orient="records")]
    return pd.DataFrame([model.model_dump() for model in models], columns=list(columns))


def _assert_no_wallet_address_fields(frame: pd.DataFrame, name: str) -> None:
    forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
    if forbidden:
        raise ValueError(f"{name} must not contain wallet-address fields: {forbidden}")


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


def _ensure_utc_datetime(value: str) -> str:
    _parse_utc_datetime(value)
    return _non_empty_str(value)


def _parse_utc_datetime(value: str) -> datetime:
    candidate = _non_empty_str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"datetime value is not parseable: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"datetime value must include UTC offset: {value!r}")
    return parsed.astimezone(UTC)


def _non_empty_str(value: str) -> str:
    if value is None:
        raise TypeError("value must be str, got NoneType")
    candidate = str(value).strip()
    if not candidate:
        raise ValueError("value must be a non-empty string")
    return candidate


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


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    counts = frame[column].value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


if __name__ == "__main__":
    raise SystemExit(main())
