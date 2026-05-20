"""Validate recorded monitor v2 input CSV files before live collection.

The validators in this module define the file boundary for the future
Polymarket politics/geo monitor. They validate recorded CSV inputs only and do
not call external APIs, databases, LLMs, agents, MCP tools, or order execution.
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


REPORT_OUTPUT = RESULTS_DIR / "monitor_v2_recorded_input_validation_report.json"

MARKET_WATCH_COLUMNS: tuple[str, ...] = (
    "watch_id",
    "market_id",
    "condition_id",
    "token_ids",
    "question",
    "category",
    "subcategory",
    "status",
    "source",
    "created_at",
    "updated_at",
)
MARKET_SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "market_id",
    "token_id",
    "price",
    "midpoint",
    "best_bid",
    "best_ask",
    "spread",
    "volume",
    "open_interest",
    "source",
)
WALLET_TIER_SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "market_id",
    "bucket",
    "tier",
    "active_wallets",
    "trade_count",
    "total_observed_amount_usd",
    "top_tier_share",
    "hhi_concentration",
    "source",
    "filter_metadata",
)
EVENT_CANDIDATE_COLUMNS: tuple[str, ...] = (
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


class MarketWatchItemRow(BaseModel):
    """One recorded monitor v2 watchlist row."""

    watch_id: str
    market_id: str
    condition_id: str
    token_ids: str
    question: str
    category: str
    subcategory: str = ""
    status: Literal["candidate", "active", "paused", "closed", "archived"]
    source: str
    created_at: str
    updated_at: str

    @field_validator(
        "watch_id",
        "market_id",
        "condition_id",
        "token_ids",
        "question",
        "category",
        "status",
        "source",
        "created_at",
        "updated_at",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("created_at", "updated_at")
    @classmethod
    def _datetime(cls, value: str) -> str:
        return _ensure_datetime(value)

    @field_validator("token_ids")
    @classmethod
    def _token_ids(cls, value: str) -> str:
        tokens = _parse_list_field(value)
        if not tokens:
            raise ValueError("token_ids must contain at least one token id")
        return value


class MarketSnapshotRow(BaseModel):
    """One recorded market snapshot row."""

    timestamp_utc: str
    market_id: str
    token_id: str
    price: float | None = Field(default=None, ge=0.0, le=1.0)
    midpoint: float | None = Field(default=None, ge=0.0, le=1.0)
    best_bid: float | None = Field(default=None, ge=0.0, le=1.0)
    best_ask: float | None = Field(default=None, ge=0.0, le=1.0)
    spread: float | None = Field(default=None, ge=0.0)
    volume: float | None = Field(default=None, ge=0.0)
    open_interest: float | None = Field(default=None, ge=0.0)
    source: str

    @field_validator("timestamp_utc")
    @classmethod
    def _timestamp(cls, value: str) -> str:
        return _ensure_datetime(value)

    @field_validator("market_id", "token_id", "source")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @model_validator(mode="after")
    def _market_values(self) -> "MarketSnapshotRow":
        if self.price is None and self.midpoint is None:
            raise ValueError("market snapshot requires price or midpoint")
        if self.best_bid is not None and self.best_ask is not None:
            if self.best_bid > self.best_ask:
                raise ValueError("best_bid must be <= best_ask")
        return self


class WalletTierSnapshotRow(BaseModel):
    """One recorded aggregate wallet-tier snapshot row."""

    timestamp_utc: str
    market_id: str
    bucket: str
    tier: str
    active_wallets: int = Field(ge=0)
    trade_count: int = Field(ge=0)
    total_observed_amount_usd: float = Field(ge=0.0)
    top_tier_share: float | None = Field(default=None, ge=0.0, le=1.0)
    hhi_concentration: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str
    filter_metadata: str

    @field_validator("timestamp_utc")
    @classmethod
    def _timestamp(cls, value: str) -> str:
        return _ensure_datetime(value)

    @field_validator("market_id", "bucket", "tier", "source", "filter_metadata")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("tier")
    @classmethod
    def _known_tier(cls, value: str) -> str:
        if value not in ALLOWED_TIERS:
            raise ValueError(f"tier must be one of {sorted(ALLOWED_TIERS)}")
        return value


class EventCandidateRow(BaseModel):
    """One recorded politics/geo event candidate row."""

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
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _non_empty_str(value)

    @field_validator("detected_at_utc", "published_at_utc")
    @classmethod
    def _datetime(cls, value: str) -> str:
        return _ensure_datetime(value)

    @model_validator(mode="after")
    def _review_requirements(self) -> "EventCandidateRow":
        if self.review_status in {"source_checked", "market_mapped", "accepted"}:
            if not self.source_url.strip():
                raise ValueError("source_url is required for checked event candidates")
        if self.review_status in {"market_mapped", "accepted"}:
            if not _parse_list_field(self.related_market_ids):
                raise ValueError("related_market_ids are required for mapped event candidates")
        return self


def validate_market_watch_items(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate recorded market watchlist rows."""

    return _validate_frame(frame, MARKET_WATCH_COLUMNS, MarketWatchItemRow, "market watchlist")


def validate_market_snapshots(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate recorded market snapshot rows."""

    return _validate_frame(frame, MARKET_SNAPSHOT_COLUMNS, MarketSnapshotRow, "market snapshots")


def validate_wallet_tier_snapshots(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate recorded aggregate wallet-tier snapshot rows."""

    if "wallet_address" in frame.columns:
        raise ValueError("wallet-tier snapshots must not contain wallet_address")
    return _validate_frame(
        frame,
        WALLET_TIER_SNAPSHOT_COLUMNS,
        WalletTierSnapshotRow,
        "wallet-tier snapshots",
    )


def validate_event_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate recorded event candidate rows."""

    return _validate_frame(frame, EVENT_CANDIDATE_COLUMNS, EventCandidateRow, "event candidates")


def validate_recorded_input_files(
    *,
    watchlist_path: Path | None = None,
    market_snapshots_path: Path | None = None,
    wallet_tier_snapshots_path: Path | None = None,
    event_candidates_path: Path | None = None,
    report_output_path: Path | None = None,
) -> dict[str, Any]:
    """Validate provided recorded input files and optionally write a report."""

    inputs = {
        "watchlist": watchlist_path,
        "market_snapshots": market_snapshots_path,
        "wallet_tier_snapshots": wallet_tier_snapshots_path,
        "event_candidates": event_candidates_path,
    }
    if all(path is None for path in inputs.values()):
        raise ValueError("At least one recorded input CSV path must be provided")

    validators = {
        "watchlist": validate_market_watch_items,
        "market_snapshots": validate_market_snapshots,
        "wallet_tier_snapshots": validate_wallet_tier_snapshots,
        "event_candidates": validate_event_candidates,
    }
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "status": "pass",
        "validated_inputs": {},
        "limitations": {
            "recorded_files_only": True,
            "does_not_call_external_apis": True,
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
            raise FileNotFoundError(f"Recorded monitor v2 input file not found: {path}")
        frame = pd.read_csv(path)
        validated = validators[name](frame)
        report["validated_inputs"][name] = {
            "path": str(path),
            "row_count": int(len(validated)),
            "columns": list(validated.columns),
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
        report = validate_recorded_input_files(
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
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")
    subset = frame.loc[:, list(columns)].copy()
    models = [model_cls.model_validate(_clean_row(row)) for row in subset.to_dict(orient="records")]
    return pd.DataFrame([model.model_dump() for model in models], columns=list(columns))


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


def _ensure_datetime(value: str) -> str:
    candidate = _non_empty_str(value).replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"datetime value is not parseable: {value!r}") from exc
    return value


def _non_empty_str(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"value must be str, got {type(value).__name__}")
    candidate = value.strip()
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


if __name__ == "__main__":
    raise SystemExit(main())
