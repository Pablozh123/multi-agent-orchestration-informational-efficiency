"""Collect bounded Polymarket price history around Swiss referendum polls.

The collector reads public CLOB price-history data for the Yes token of the
Swiss 10-million initiative market. It only fetches bounded windows around
curated poll publication timestamps and writes local file artifacts.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.swiss_referendum_polymarket import SNAPSHOT_OUTPUT


CLOB_BASE_URL = "https://clob.polymarket.com"
POLL_INPUT = Path("data/swiss_referendum_10mio_polls.csv")
HISTORY_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_polymarket_price_history.csv"
HISTORY_METADATA_OUTPUT = (
    RESULTS_DIR / "swiss_referendum_10mio_polymarket_price_history_metadata.json"
)

HISTORY_COLUMNS: tuple[str, ...] = (
    "observed_at_utc",
    "poll_id",
    "poll_published_at_utc",
    "window_start_utc",
    "window_end_utc",
    "token_id",
    "yes_probability",
    "source_name",
    "source_url",
)


@dataclass(frozen=True)
class SwissReferendumHistoryResult:
    """Summary of generated price-history artifacts."""

    history_path: Path
    metadata_path: Path
    row_count: int
    poll_count: int
    token_id: str

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly summary."""

        return {
            "history_path": str(self.history_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
            "poll_count": self.poll_count,
            "token_id": self.token_id,
        }


def collect_swiss_referendum_price_history(
    *,
    source: str = "mock",
    poll_input_path: Path = POLL_INPUT,
    snapshots_path: Path = SNAPSHOT_OUTPUT,
    history_path: Path = HISTORY_OUTPUT,
    metadata_path: Path = HISTORY_METADATA_OUTPUT,
    hours_before: int = 24,
    hours_after: int = 48,
    fidelity_minutes: int = 60,
    token_id: str | None = None,
    client: httpx.Client | None = None,
) -> SwissReferendumHistoryResult:
    """Collect bounded public price history around every curated poll release."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    if hours_before < 0 or hours_after < 0:
        raise ValueError("history window hours must be >= 0")
    if hours_before + hours_after <= 0:
        raise ValueError("history window must include at least one hour")
    if fidelity_minutes < 1:
        raise ValueError("fidelity_minutes must be >= 1")

    polls = _read_poll_rows(poll_input_path)
    yes_token_id = token_id or _read_yes_token_id(snapshots_path)
    own_client = client is None
    http_client = client or httpx.Client(timeout=20.0)
    try:
        rows: list[dict[str, Any]] = []
        for poll in polls:
            window_start = poll["published_ts"] - pd.Timedelta(hours=hours_before)
            window_end = poll["published_ts"] + pd.Timedelta(hours=hours_after)
            history = (
                mock_price_history_points(
                    poll,
                    window_start=window_start,
                    window_end=window_end,
                    token_id=yes_token_id,
                )
                if source == "mock"
                else fetch_clob_price_history(
                    http_client,
                    token_id=yes_token_id,
                    start_ts=window_start,
                    end_ts=window_end,
                    fidelity_minutes=fidelity_minutes,
                )
            )
            rows.extend(
                _history_rows_for_poll(
                    poll,
                    history=history,
                    token_id=yes_token_id,
                    window_start=window_start,
                    window_end=window_end,
                )
            )
    finally:
        if own_client:
            http_client.close()

    frame = validate_history_frame(pd.DataFrame(rows, columns=HISTORY_COLUMNS))
    history_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(history_path, index=False)
    metadata = _build_metadata(
        source=source,
        poll_count=len(polls),
        row_count=len(frame),
        token_id=yes_token_id,
        poll_input_path=poll_input_path,
        snapshots_path=snapshots_path,
        history_path=history_path,
        hours_before=hours_before,
        hours_after=hours_after,
        fidelity_minutes=fidelity_minutes,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SwissReferendumHistoryResult(
        history_path=history_path,
        metadata_path=metadata_path,
        row_count=int(len(frame)),
        poll_count=int(len(polls)),
        token_id=yes_token_id,
    )


def fetch_clob_price_history(
    client: httpx.Client,
    *,
    token_id: str,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    fidelity_minutes: int,
) -> list[dict[str, Any]]:
    """Fetch public CLOB price-history points for one bounded interval."""

    response = client.get(
        f"{CLOB_BASE_URL}/prices-history",
        params={
            "market": token_id,
            "startTs": int(start_ts.timestamp()),
            "endTs": int(end_ts.timestamp()),
            "fidelity": fidelity_minutes,
        },
    )
    response.raise_for_status()
    data = response.json()
    history = data.get("history") if isinstance(data, dict) else None
    if not isinstance(history, list):
        raise ValueError("CLOB price-history response must contain a history list")
    return [item for item in history if isinstance(item, dict)]


def validate_history_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate local price-history rows."""

    missing = [column for column in HISTORY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"history frame missing required columns: {missing}")
    forbidden = [column for column in frame.columns if "wallet" in column.lower()]
    if forbidden:
        raise ValueError(f"history frame must not contain wallet columns: {forbidden}")
    normalized = frame.loc[:, list(HISTORY_COLUMNS)].copy()
    if normalized.empty:
        raise ValueError("history frame must contain at least one row")
    normalized["yes_probability"] = pd.to_numeric(
        normalized["yes_probability"],
        errors="raise",
    )
    if not normalized["yes_probability"].between(0.0, 1.0).all():
        raise ValueError("history yes_probability values must be between 0 and 1")
    for column in (
        "observed_at_utc",
        "poll_published_at_utc",
        "window_start_utc",
        "window_end_utc",
    ):
        pd.to_datetime(normalized[column], errors="raise", utc=True)
    for column in ("token_id", "source_name", "source_url"):
        if normalized[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"history column {column!r} must not be blank")
    return (
        normalized.drop_duplicates(["observed_at_utc", "poll_id", "token_id"])
        .sort_values(["poll_published_at_utc", "observed_at_utc", "poll_id"])
        .reset_index(drop=True)
    )


def mock_price_history_points(
    poll: dict[str, Any],
    *,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    token_id: str,
) -> list[dict[str, Any]]:
    """Return deterministic mock CLOB-style history points."""

    del token_id
    yes_share = float(poll["yes_share"])
    published_ts = poll["published_ts"]
    return [
        {"t": int((published_ts - pd.Timedelta(hours=1)).timestamp()), "p": yes_share + 0.02},
        {"t": int((published_ts + pd.Timedelta(hours=1)).timestamp()), "p": yes_share - 0.03},
        {"t": int(window_start.timestamp()), "p": yes_share + 0.01},
        {"t": int(window_end.timestamp()), "p": yes_share - 0.04},
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--poll-input", type=Path, default=POLL_INPUT)
    parser.add_argument("--snapshots", type=Path, default=SNAPSHOT_OUTPUT)
    parser.add_argument("--history-output", type=Path, default=HISTORY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=HISTORY_METADATA_OUTPUT)
    parser.add_argument("--hours-before", type=int, default=24)
    parser.add_argument("--hours-after", type=int, default=48)
    parser.add_argument("--fidelity-minutes", type=int, default=60)
    parser.add_argument("--token-id", default=None)
    args = parser.parse_args(argv)

    try:
        result = collect_swiss_referendum_price_history(
            source=args.source,
            poll_input_path=args.poll_input,
            snapshots_path=args.snapshots,
            history_path=args.history_output,
            metadata_path=args.metadata_output,
            hours_before=args.hours_before,
            hours_after=args.hours_after,
            fidelity_minutes=args.fidelity_minutes,
            token_id=args.token_id,
        )
    except (httpx.HTTPError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _read_poll_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"poll catalog not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = ("poll_id", "published_at_utc", "yes_share", "source_url")
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"poll catalog missing required columns: {missing}")
    rows: list[dict[str, Any]] = []
    for item in frame.to_dict(orient="records"):
        poll_id = str(item["poll_id"]).strip()
        if not poll_id:
            raise ValueError("poll_id must not be blank")
        published_ts = pd.Timestamp(str(item["published_at_utc"])).tz_convert("UTC")
        yes_share = float(item["yes_share"])
        if not 0.0 <= yes_share <= 1.0:
            raise ValueError("poll yes_share values must be between 0 and 1")
        rows.append(
            {
                "poll_id": poll_id,
                "published_at_utc": _format_timestamp(published_ts),
                "published_ts": published_ts,
                "yes_share": yes_share,
                "source_url": str(item["source_url"]).strip(),
            }
        )
    return sorted(rows, key=lambda row: (row["published_ts"], row["poll_id"]))


def _read_yes_token_id(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Polymarket snapshot file not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "yes_token_id" not in frame.columns:
        raise ValueError("snapshot file missing yes_token_id column")
    token = str(frame.sort_values("collected_at_utc").iloc[-1]["yes_token_id"]).strip()
    if not token:
        raise ValueError("yes_token_id must not be blank")
    return token


def _history_rows_for_poll(
    poll: dict[str, Any],
    *,
    history: list[dict[str, Any]],
    token_id: str,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for point in history:
        observed_ts = _history_timestamp(point)
        if observed_ts is None or not (window_start <= observed_ts <= window_end):
            continue
        price = _safe_float(point.get("p", point.get("price")))
        if price is None:
            continue
        rows.append(
            {
                "observed_at_utc": _format_timestamp(observed_ts),
                "poll_id": poll["poll_id"],
                "poll_published_at_utc": poll["published_at_utc"],
                "window_start_utc": _format_timestamp(window_start),
                "window_end_utc": _format_timestamp(window_end),
                "token_id": token_id,
                "yes_probability": price,
                "source_name": "polymarket_clob_prices_history",
                "source_url": f"{CLOB_BASE_URL}/prices-history",
            }
        )
    return rows


def _history_timestamp(point: dict[str, Any]) -> pd.Timestamp | None:
    value = point.get("t", point.get("timestamp"))
    if value is None:
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000.0
    return pd.Timestamp(datetime.fromtimestamp(timestamp, tz=UTC))


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_timestamp(value: pd.Timestamp | datetime) -> str:
    return pd.Timestamp(value).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_metadata(
    *,
    source: str,
    poll_count: int,
    row_count: int,
    token_id: str,
    poll_input_path: Path,
    snapshots_path: Path,
    history_path: Path,
    hours_before: int,
    hours_after: int,
    fidelity_minutes: int,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "swiss_referendum_10mio_price_history_collector",
            "source": source,
            "hours_before": hours_before,
            "hours_after": hours_after,
            "fidelity_minutes": fidelity_minutes,
            "token_id": token_id,
            "bounded_poll_windows_only": True,
            "read_only": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "endpoints": {"clob_prices_history": f"{CLOB_BASE_URL}/prices-history"},
        "outputs": {
            "poll_input_path": str(poll_input_path),
            "snapshots_path": str(snapshots_path),
            "history_path": str(history_path),
            "poll_count": poll_count,
            "row_count": row_count,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "historical_chart_points_are_public_clob_history": source == "live",
            "no_causal_claim_from_price_history": True,
            "no_profitability_or_tradeability_claim": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
