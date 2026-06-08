"""Collect public Polymarket wallet-level activity rows for forensic review.

This module uses public Data API trade rows only. It does not use CLOB order
endpoints, authenticated channels, credentials, agents, MCP tools, ML systems,
or database writes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_readonly import (
    DATA_API_BASE_URL,
    LIVE_WATCHLIST_OUTPUT,
    fetch_trade_rows_for_watchlist,
)


PUBLIC_ACTIVITY_OUTPUT = RESULTS_DIR / "monitor_v2_polymarket_public_wallet_activity.csv"
PUBLIC_ACTIVITY_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_public_wallet_activity_metadata.json"
)

PUBLIC_ACTIVITY_COLUMNS: tuple[str, ...] = (
    "collected_at_utc",
    "source_name",
    "market_id",
    "condition_id",
    "timestamp_utc",
    "proxy_wallet",
    "side",
    "usdc_size",
    "price",
    "outcome",
    "transaction_hash",
    "name",
    "pseudonym",
    "title",
    "slug",
    "event_slug",
    "claim_scope",
)

WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
VALID_SIDES = {"BUY", "SELL"}


@dataclass(frozen=True)
class PublicActivityCollectionResult:
    """Summary of generated public wallet-activity artifacts."""

    activity_path: Path
    metadata_path: Path
    row_count: int
    wallet_count: int
    market_count: int
    source: str

    def to_dict(self) -> dict[str, int | str]:
        return {
            "activity_path": str(self.activity_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "wallet_count": self.wallet_count,
            "market_count": self.market_count,
            "source": self.source,
        }


def collect_public_wallet_activity(
    *,
    source: str = "mock",
    watchlist_path: Path = LIVE_WATCHLIST_OUTPUT,
    activity_path: Path = PUBLIC_ACTIVITY_OUTPUT,
    metadata_path: Path = PUBLIC_ACTIVITY_METADATA_OUTPUT,
    limit: int = 500,
    collected_at_utc: str | None = None,
    client: httpx.Client | None = None,
) -> PublicActivityCollectionResult:
    """Collect public wallet-level activity rows and write compact artifacts."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
    if not watchlist_path.exists():
        raise FileNotFoundError(f"watchlist not found: {watchlist_path}")

    collected_at = _parse_collected_at(collected_at_utc)
    watchlist = pd.read_csv(watchlist_path, keep_default_na=False)
    _validate_watchlist(watchlist)
    raw_rows = (
        mock_activity_rows(watchlist, collected_at=collected_at)
        if source == "mock"
        else _fetch_live_rows(watchlist, limit=limit, client=client)
    )
    activity = normalize_public_activity_rows(
        raw_rows,
        watchlist=watchlist,
        collected_at=collected_at,
        source_name=f"polymarket_{source}_data_api_public_activity",
    )
    validated = validate_public_activity(activity)

    activity_path.parent.mkdir(parents=True, exist_ok=True)
    validated.to_csv(activity_path, index=False)
    metadata = _metadata(
        activity=validated,
        source=source,
        watchlist_path=watchlist_path,
        activity_path=activity_path,
        limit=limit,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PublicActivityCollectionResult(
        activity_path=activity_path,
        metadata_path=metadata_path,
        row_count=int(len(validated)),
        wallet_count=int(validated["proxy_wallet"].nunique()) if not validated.empty else 0,
        market_count=int(validated["market_id"].nunique()) if not validated.empty else 0,
        source=source,
    )


def normalize_public_activity_rows(
    rows: Sequence[dict[str, Any]],
    *,
    watchlist: pd.DataFrame,
    collected_at: datetime,
    source_name: str,
) -> pd.DataFrame:
    """Normalize public Data API rows to the local wallet-activity contract."""

    _validate_watchlist(watchlist)
    market_lookup = {
        str(row["condition_id"]): str(row["market_id"])
        for row in watchlist[["condition_id", "market_id"]].to_dict(orient="records")
    }
    normalized: list[dict[str, object]] = []
    for row in rows:
        condition_id = str(row.get("conditionId", row.get("condition_id", ""))).strip()
        market_id = market_lookup.get(condition_id, condition_id)
        wallet = str(row.get("proxyWallet", row.get("proxy_wallet", ""))).strip()
        side = str(row.get("side", "")).upper().strip()
        timestamp = _timestamp_utc(row.get("timestamp", row.get("timestamp_utc", "")))
        if not condition_id or not wallet or not side:
            continue
        normalized.append(
            {
                "collected_at_utc": collected_at.isoformat().replace("+00:00", "Z"),
                "source_name": source_name,
                "market_id": market_id,
                "condition_id": condition_id,
                "timestamp_utc": timestamp,
                "proxy_wallet": wallet.lower(),
                "side": side,
                "usdc_size": _trade_usdc_size(row),
                "price": _number(row.get("price", 0.0)),
                "outcome": str(row.get("outcome", "")),
                "transaction_hash": str(
                    row.get("transactionHash", row.get("transaction_hash", ""))
                ),
                "name": str(row.get("name", "")),
                "pseudonym": str(row.get("pseudonym", "")),
                "title": str(row.get("title", "")),
                "slug": str(row.get("slug", "")),
                "event_slug": str(row.get("eventSlug", row.get("event_slug", ""))),
                "claim_scope": "public_polymarket_wallet_activity_forensic_review",
            }
        )
    return pd.DataFrame(normalized, columns=PUBLIC_ACTIVITY_COLUMNS)


def validate_public_activity(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize public wallet-level activity rows."""

    missing = [column for column in PUBLIC_ACTIVITY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"public wallet activity missing columns: {missing}")
    data = frame.loc[:, list(PUBLIC_ACTIVITY_COLUMNS)].copy()
    if data.empty:
        return data
    for column in (
        "market_id",
        "condition_id",
        "timestamp_utc",
        "proxy_wallet",
        "side",
        "claim_scope",
    ):
        if data[column].isna().any() or data[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"public wallet activity contains blank values in {column}")
        data[column] = data[column].astype(str).str.strip()
    invalid_wallets = [
        wallet for wallet in data["proxy_wallet"].astype(str) if WALLET_RE.fullmatch(wallet) is None
    ]
    if invalid_wallets:
        raise ValueError("public wallet activity contains invalid proxy_wallet values")
    invalid_sides = sorted(set(data["side"].astype(str).str.upper()) - VALID_SIDES)
    if invalid_sides:
        raise ValueError(f"public wallet activity contains invalid sides: {invalid_sides}")
    data["side"] = data["side"].astype(str).str.upper()
    data["timestamp_utc"] = pd.to_datetime(
        data["timestamp_utc"],
        utc=True,
        errors="raise",
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["collected_at_utc"] = pd.to_datetime(
        data["collected_at_utc"],
        utc=True,
        errors="raise",
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["usdc_size"] = pd.to_numeric(data["usdc_size"], errors="raise")
    data["price"] = pd.to_numeric(data["price"], errors="raise")
    if (data["usdc_size"] < 0).any():
        raise ValueError("public wallet activity contains negative usdc_size")
    if ((data["price"] < 0) | (data["price"] > 1)).any():
        raise ValueError("public wallet activity price must be between 0 and 1")
    for column in (
        "source_name",
        "outcome",
        "transaction_hash",
        "name",
        "pseudonym",
        "title",
        "slug",
        "event_slug",
    ):
        data[column] = data[column].fillna("").astype(str)
    return data.sort_values(["timestamp_utc", "market_id", "proxy_wallet"]).reset_index(drop=True)


def mock_activity_rows(watchlist: pd.DataFrame, *, collected_at: datetime) -> list[dict[str, Any]]:
    """Return deterministic public Data API style activity rows."""

    _validate_watchlist(watchlist)
    first = watchlist.iloc[0]
    condition_id = str(first["condition_id"])
    title = str(first.get("question", "Mock politics market"))
    base_time = int(collected_at.timestamp()) - 600
    return [
        _mock_row(condition_id, "0x" + "1" * 40, base_time, 1250.0, 0.42, title, "BUY"),
        _mock_row(condition_id, "0x" + "2" * 40, base_time + 60, 800.0, 0.43, title, "BUY"),
        _mock_row(condition_id, "0x" + "3" * 40, base_time + 90, 75.0, 0.44, title, "SELL"),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--watchlist", type=Path, default=LIVE_WATCHLIST_OUTPUT)
    parser.add_argument("--activity-output", type=Path, default=PUBLIC_ACTIVITY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=PUBLIC_ACTIVITY_METADATA_OUTPUT)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--collected-at-utc", default=None)
    args = parser.parse_args(argv)
    try:
        result = collect_public_wallet_activity(
            source=args.source,
            watchlist_path=args.watchlist,
            activity_path=args.activity_output,
            metadata_path=args.metadata_output,
            limit=args.limit,
            collected_at_utc=args.collected_at_utc,
        )
    except (FileNotFoundError, ValueError, httpx.HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _fetch_live_rows(
    watchlist: pd.DataFrame,
    *,
    limit: int,
    client: httpx.Client | None,
) -> list[dict[str, Any]]:
    own_client = client is None
    http_client = client or httpx.Client(timeout=20.0)
    try:
        return fetch_trade_rows_for_watchlist(http_client, watchlist, limit=limit)
    finally:
        if own_client:
            http_client.close()


def _validate_watchlist(watchlist: pd.DataFrame) -> None:
    missing = [column for column in ("market_id", "condition_id") if column not in watchlist.columns]
    if missing:
        raise ValueError(f"watchlist missing columns: {missing}")


def _parse_collected_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    return parsed.tz_convert("UTC").to_pydatetime().replace(microsecond=0)


def _timestamp_utc(value: object) -> str:
    if isinstance(value, (int, float)) or str(value).isdigit():
        return datetime.fromtimestamp(int(value), UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    return parsed.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _number(value: object) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _trade_usdc_size(row: dict[str, Any]) -> float:
    direct_value = row.get("usdcSize", row.get("usdc_size", ""))
    direct = _number(direct_value)
    if direct_value not in {None, ""}:
        return direct
    size = _number(row.get("size", 0.0))
    price = _number(row.get("price", 0.0))
    return max(size * price, 0.0)


def _mock_row(
    condition_id: str,
    wallet: str,
    timestamp: int,
    usdc_size: float,
    price: float,
    title: str,
    side: str,
) -> dict[str, Any]:
    return {
        "proxyWallet": wallet,
        "timestamp": timestamp,
        "conditionId": condition_id,
        "side": side,
        "usdcSize": usdc_size,
        "price": price,
        "outcome": "YES",
        "transactionHash": "0x" + wallet[-8:] * 8,
        "name": "",
        "pseudonym": f"wallet_{wallet[-4:]}",
        "title": title,
        "slug": "mock-politics-market",
        "eventSlug": "mock-politics-event",
    }


def _metadata(
    *,
    activity: pd.DataFrame,
    source: str,
    watchlist_path: Path,
    activity_path: Path,
    limit: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "polymarket_public_wallet_activity",
            "source": source,
            "uses_public_data_api": source == "live",
            "uses_order_endpoints": False,
            "uses_authentication": False,
            "does_not_write_database": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
        },
        "inputs": {
            "watchlist_path": str(watchlist_path),
            "data_api_endpoint": f"{DATA_API_BASE_URL}/trades",
            "limit": limit,
        },
        "outputs": {
            "activity_path": str(activity_path),
            "row_count": int(len(activity)),
            "wallet_count": int(activity["proxy_wallet"].nunique()) if not activity.empty else 0,
            "market_count": int(activity["market_id"].nunique()) if not activity.empty else 0,
            "contains_public_wallet_addresses": True,
            "contains_order_instructions": False,
        },
        "limitations": {
            "public_activity_rows_only": True,
            "not_a_misconduct_finding": True,
            "not_a_trade_or_return_test": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
