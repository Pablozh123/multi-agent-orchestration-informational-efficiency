"""Collect a read-only Polymarket snapshot for the Swiss 10-million vote.

The collector reads public Gamma event metadata for the 14 June 2026 Swiss
referendum market and writes a bounded local CSV snapshot. It does not use
authenticated user channels, order endpoints, agents, MCP tools, ML systems,
LLMs, or database writes.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
EVENT_SLUG = "switzerlands-june-referendum-what-will-pass"
TEN_MILLION_MARKET_SLUG = (
    "will-the-no-to-ten-million-switzerland-initiative-be-approved-in-"
    "switzerlands-june-14-2026-popular-vote"
)
MARKET_URL = (
    "https://polymarket.com/de/event/"
    f"{EVENT_SLUG}?marketSlug={TEN_MILLION_MARKET_SLUG}&outcomeIndex=1"
)

SNAPSHOT_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_polymarket_snapshots.csv"
SNAPSHOT_METADATA_OUTPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_polymarket_snapshot_metadata.json"
)

SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "collected_at_utc",
    "source_timestamp_utc",
    "event_slug",
    "market_slug",
    "market_id",
    "condition_id",
    "question",
    "yes_token_id",
    "no_token_id",
    "yes_probability",
    "no_probability",
    "best_bid",
    "best_ask",
    "last_trade_price",
    "one_day_price_change",
    "one_week_price_change",
    "volume_usd",
    "liquidity_usd",
    "source_url",
)


@dataclass(frozen=True)
class SwissReferendumSnapshotResult:
    """Summary of the generated Polymarket snapshot artifact."""

    snapshots_path: Path
    metadata_path: Path
    row_count: int
    latest_yes_probability: float
    latest_no_probability: float
    market_id: str

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly summary."""

        return {
            "snapshots_path": str(self.snapshots_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "latest_yes_probability": self.latest_yes_probability,
            "latest_no_probability": self.latest_no_probability,
            "market_id": self.market_id,
        }


def collect_swiss_referendum_polymarket_snapshot(
    *,
    source: str = "mock",
    snapshots_path: Path = SNAPSHOT_OUTPUT,
    metadata_path: Path = SNAPSHOT_METADATA_OUTPUT,
    collected_at_utc: str | None = None,
    append: bool = True,
    client: httpx.Client | None = None,
) -> SwissReferendumSnapshotResult:
    """Collect and persist one read-only Polymarket probability snapshot."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")

    collected_at = _parse_collected_at(collected_at_utc)
    own_client = client is None
    http_client = client or httpx.Client(timeout=20.0)
    try:
        event = (
            mock_gamma_event()
            if source == "mock"
            else fetch_gamma_event(http_client, event_slug=EVENT_SLUG)
        )
    finally:
        if own_client:
            http_client.close()

    row = build_snapshot_row(event, collected_at=collected_at)
    frame = validate_snapshot_frame(pd.DataFrame([row], columns=SNAPSHOT_COLUMNS))
    written = _write_snapshot_frame(snapshots_path, frame, append=append)
    metadata = _build_metadata(
        source=source,
        collected_at=collected_at,
        snapshots_path=snapshots_path,
        snapshot_frame=written,
        append=append,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    latest = written.sort_values("collected_at_utc").iloc[-1]
    return SwissReferendumSnapshotResult(
        snapshots_path=snapshots_path,
        metadata_path=metadata_path,
        row_count=int(len(written)),
        latest_yes_probability=float(latest["yes_probability"]),
        latest_no_probability=float(latest["no_probability"]),
        market_id=str(latest["market_id"]),
    )


def fetch_gamma_event(
    client: httpx.Client,
    *,
    event_slug: str = EVENT_SLUG,
) -> dict[str, Any]:
    """Fetch public Gamma event metadata by slug."""

    response = client.get(f"{GAMMA_BASE_URL}/events", params={"slug": event_slug})
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        if not data:
            raise ValueError(f"No Gamma event found for slug {event_slug!r}")
        candidate = data[0]
    else:
        candidate = data
    if not isinstance(candidate, dict):
        raise ValueError("Gamma event response must be an object or non-empty list")
    return candidate


def build_snapshot_row(
    event: dict[str, Any],
    *,
    collected_at: datetime,
) -> dict[str, Any]:
    """Extract the 10-million initiative market from a Gamma event payload."""

    market = _select_ten_million_market(event)
    outcomes = _parse_json_list(market.get("outcomes"))
    prices = [_safe_float(value) for value in _parse_json_list(market.get("outcomePrices"))]
    token_ids = _parse_json_list(market.get("clobTokenIds"))
    yes_index = _find_outcome_index(outcomes, "Yes")
    no_index = _find_outcome_index(outcomes, "No")
    if yes_index >= len(prices) or no_index >= len(prices):
        raise ValueError("Gamma market is missing Yes/No outcome prices")
    if yes_index >= len(token_ids) or no_index >= len(token_ids):
        raise ValueError("Gamma market is missing Yes/No CLOB token ids")

    return {
        "collected_at_utc": _format_timestamp(collected_at),
        "source_timestamp_utc": str(market.get("updatedAt", "")),
        "event_slug": str(event.get("slug", EVENT_SLUG)),
        "market_slug": str(market.get("slug", "")),
        "market_id": str(market.get("id", "")),
        "condition_id": str(market.get("conditionId", "")),
        "question": _clean_text(market.get("question", "")),
        "yes_token_id": str(token_ids[yes_index]),
        "no_token_id": str(token_ids[no_index]),
        "yes_probability": float(prices[yes_index]),
        "no_probability": float(prices[no_index]),
        "best_bid": _safe_float(market.get("bestBid")),
        "best_ask": _safe_float(market.get("bestAsk")),
        "last_trade_price": _safe_float(market.get("lastTradePrice")),
        "one_day_price_change": _safe_float(market.get("oneDayPriceChange")),
        "one_week_price_change": _safe_float(market.get("oneWeekPriceChange")),
        "volume_usd": _safe_float(market.get("volumeNum", market.get("volume"))),
        "liquidity_usd": _safe_float(market.get("liquidityNum", market.get("liquidity"))),
        "source_url": MARKET_URL,
    }


def validate_snapshot_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the local Polymarket snapshot contract."""

    missing = [column for column in SNAPSHOT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"snapshot frame missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"snapshot frame must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(SNAPSHOT_COLUMNS)].copy()
    for column in ("yes_probability", "no_probability"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if not normalized[column].between(0.0, 1.0).all():
            raise ValueError(f"{column} values must be between 0 and 1")
    for column in (
        "best_bid",
        "best_ask",
        "last_trade_price",
        "one_day_price_change",
        "one_week_price_change",
        "volume_usd",
        "liquidity_usd",
    ):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    for column in (
        "collected_at_utc",
        "event_slug",
        "market_slug",
        "market_id",
        "condition_id",
        "question",
        "yes_token_id",
        "no_token_id",
        "source_url",
    ):
        if normalized[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"snapshot column {column!r} must not be blank")
    if not (normalized["market_slug"] == TEN_MILLION_MARKET_SLUG).all():
        raise ValueError("snapshot must target the 10-million initiative market")
    return normalized


def mock_gamma_event() -> dict[str, Any]:
    """Return a deterministic Gamma-style fixture for tests and dry runs."""

    return {
        "slug": EVENT_SLUG,
        "markets": [
            {
                "id": "1845700",
                "question": (
                    "Will the No to ten million Switzerland initiative be "
                    "approved in Switzerland's June 14, 2026 popular vote?"
                ),
                "conditionId": "0x" + "8" * 64,
                "slug": TEN_MILLION_MARKET_SLUG,
                "outcomes": json.dumps(["Yes", "No"]),
                "outcomePrices": json.dumps(["0.225", "0.775"]),
                "clobTokenIds": json.dumps(["111", "222"]),
                "updatedAt": "2026-06-08T13:47:46.934575Z",
                "bestBid": 0.22,
                "bestAsk": 0.23,
                "lastTradePrice": 0.24,
                "oneDayPriceChange": -0.03,
                "oneWeekPriceChange": -0.15,
                "volumeNum": 247246.8461,
                "liquidityNum": 18121.7918,
            }
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--snapshots-output", type=Path, default=SNAPSHOT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=SNAPSHOT_METADATA_OUTPUT)
    parser.add_argument("--collected-at-utc", default=None)
    parser.add_argument("--append", action="store_true", default=False)
    args = parser.parse_args(argv)

    try:
        result = collect_swiss_referendum_polymarket_snapshot(
            source=args.source,
            snapshots_path=args.snapshots_output,
            metadata_path=args.metadata_output,
            collected_at_utc=args.collected_at_utc,
            append=args.append,
        )
    except (httpx.HTTPError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _select_ten_million_market(event: dict[str, Any]) -> dict[str, Any]:
    markets = event.get("markets")
    if not isinstance(markets, list):
        raise ValueError("Gamma event response must contain a markets list")
    for market in markets:
        if not isinstance(market, dict):
            continue
        if str(market.get("slug", "")) == TEN_MILLION_MARKET_SLUG:
            return market
    for market in markets:
        if not isinstance(market, dict):
            continue
        title = str(market.get("groupItemTitle", market.get("question", ""))).lower()
        if "ten million" in title and "switzerland" in title:
            return market
    raise ValueError("10-million initiative market not found in Gamma event")


def _parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    parsed = json.loads(str(value))
    if not isinstance(parsed, list):
        raise ValueError("Gamma list field must decode to a list")
    return [str(item) for item in parsed]


def _find_outcome_index(outcomes: list[str], label: str) -> int:
    for index, outcome in enumerate(outcomes):
        if outcome.strip().lower() == label.lower():
            return index
    raise ValueError(f"Gamma market is missing {label!r} outcome")


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


def _safe_float(value: Any) -> float:
    try:
        if value is None or str(value).strip() == "":
            return float("nan")
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _clean_text(value: Any) -> str:
    text = str(value)
    try:
        text = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        pass
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _write_snapshot_frame(path: Path, frame: pd.DataFrame, *, append: bool) -> pd.DataFrame:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = frame.copy()
    if append and path.exists():
        existing = validate_snapshot_frame(pd.read_csv(path))
        output = pd.concat([existing, output], ignore_index=True)
        output = output.drop_duplicates(
            subset=["collected_at_utc", "market_slug"],
            keep="last",
        )
    output = output.sort_values(["collected_at_utc", "market_slug"]).reset_index(drop=True)
    output.to_csv(path, index=False)
    return output


def _build_metadata(
    *,
    source: str,
    collected_at: datetime,
    snapshots_path: Path,
    snapshot_frame: pd.DataFrame,
    append: bool,
) -> dict[str, Any]:
    latest = snapshot_frame.sort_values("collected_at_utc").iloc[-1]
    return {
        "generated_at_utc": _format_timestamp(datetime.now(UTC).replace(microsecond=0)),
        "method": {
            "name": "swiss_referendum_10mio_polymarket_snapshot",
            "source": source,
            "event_slug": EVENT_SLUG,
            "market_slug": TEN_MILLION_MARKET_SLUG,
            "collector_received_at_utc": _format_timestamp(collected_at),
            "append_to_existing_outputs": append,
            "read_only": True,
            "uses_public_gamma_event_metadata": source == "live",
        },
        "endpoints": {"gamma_events": f"{GAMMA_BASE_URL}/events"},
        "outputs": {
            "snapshots_path": str(snapshots_path),
            "row_count": int(len(snapshot_frame)),
            "latest_yes_probability": float(latest["yes_probability"]),
            "latest_no_probability": float(latest["no_probability"]),
            "latest_collected_at_utc": str(latest["collected_at_utc"]),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "read_only_public_endpoint_only": source == "live",
            "gamma_prices_are_snapshot_values": True,
            "does_not_use_order_endpoints": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_send_orders": True,
            "no_causal_or_profitability_claim": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
