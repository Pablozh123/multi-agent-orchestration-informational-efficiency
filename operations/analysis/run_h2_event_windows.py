"""Generate deterministic H2 event-window output CSVs.

The runner reads curated events from the tracked seed CSV and daily
Polymarket prices from SQLite. It does not write to the database and does not
call external APIs or LLMs.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Sequence

import pandas as pd

from operations.analysis.event_study import (
    DEFAULT_ESTIMATION_WINDOW,
    PRIMARY_DAILY_WINDOW,
    SECONDARY_DAILY_WINDOW,
    EventWindow,
    compute_event_window_car,
    summarize_event_window_car,
)
from operations.tools.load_events import (
    CANONICAL_EVENT_COLUMNS,
    DB_PATH,
    SEED_PATH,
    read_event_seed,
    validate_event_row,
)


RESULTS_DIR = Path("data/results")
ROWS_OUTPUT = "h2_event_window_rows.csv"
SUMMARY_OUTPUT = "h2_event_window_summary.csv"
SELECTED_WINDOWS: tuple[EventWindow, ...] = (
    PRIMARY_DAILY_WINDOW,
    SECONDARY_DAILY_WINDOW,
)


@dataclass(frozen=True)
class H2OutputResult:
    """Summary of generated H2 output artifacts."""

    rows_path: Path
    summary_path: Path
    event_count: int
    event_window_row_count: int
    summary_row_count: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-friendly result summary."""

        return {
            "rows_path": str(self.rows_path),
            "summary_path": str(self.summary_path),
            "event_count": self.event_count,
            "event_window_row_count": self.event_window_row_count,
            "summary_row_count": self.summary_row_count,
        }


def load_curated_events(csv_path: Path = SEED_PATH) -> pd.DataFrame:
    """Load and validate curated seed events as a DataFrame."""

    rows = [
        validate_event_row(row, row_number=index)
        for index, row in enumerate(read_event_seed(csv_path), start=1)
    ]
    frame = pd.DataFrame(rows, columns=CANONICAL_EVENT_COLUMNS)
    if frame.empty:
        raise ValueError(f"Event seed CSV has no curated rows: {csv_path}")

    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise").dt.date
    frame["relevance_score"] = pd.to_numeric(
        frame["relevance_score"],
        errors="raise",
    )
    return frame.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def load_daily_polymarket_prices(
    db_path: Path,
    *,
    start_date: date,
    end_date: date,
    market_id: str | None = None,
    token_id: str | None = None,
) -> pd.DataFrame:
    """Load one daily Polymarket probability series from SQLite."""

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    sql = """
        SELECT price_timestamp, market_id, token_id, price
        FROM polymarket_prices
        WHERE substr(price_timestamp, 1, 10) BETWEEN ? AND ?
    """
    params: list[object] = [start_date.isoformat(), end_date.isoformat()]
    if market_id is not None:
        sql += " AND market_id = ?"
        params.append(market_id)
    if token_id is not None:
        sql += " AND token_id = ?"
        params.append(token_id)
    sql += " ORDER BY price_timestamp"

    conn = sqlite3.connect(db_path)
    try:
        frame = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()

    if frame.empty:
        raise ValueError(
            f"No Polymarket prices found between {start_date} and {end_date}"
        )

    series_count = frame[["market_id", "token_id"]].drop_duplicates().shape[0]
    if market_id is None and token_id is None and series_count > 1:
        raise ValueError(
            "Multiple Polymarket price series found; pass market_id or token_id"
        )

    frame["date"] = pd.to_datetime(
        frame["price_timestamp"],
        errors="raise",
        utc=True,
    ).dt.date
    frame["price"] = pd.to_numeric(frame["price"], errors="raise")
    return (
        frame.sort_values(["date", "price_timestamp"])
        .drop_duplicates("date", keep="last")[["date", "price"]]
        .reset_index(drop=True)
    )


def generate_h2_event_window_outputs(
    *,
    db_path: Path = DB_PATH,
    events_csv_path: Path = SEED_PATH,
    output_dir: Path = RESULTS_DIR,
    windows: Sequence[EventWindow] = SELECTED_WINDOWS,
    market_id: str | None = None,
    token_id: str | None = None,
) -> H2OutputResult:
    """Generate H2 event-window row and summary CSV outputs."""

    if not windows:
        raise ValueError("At least one event window is required")

    events = load_curated_events(events_csv_path)
    start_date, end_date = _price_query_bounds(events, windows)
    prices = load_daily_polymarket_prices(
        db_path,
        start_date=start_date,
        end_date=end_date,
        market_id=market_id,
        token_id=token_id,
    )

    row_frames = [
        compute_event_window_car(
            prices,
            events[["event_id", "event_date"]],
            window=window,
            estimation_window_days=DEFAULT_ESTIMATION_WINDOW,
        )
        for window in windows
    ]
    event_rows = pd.concat(row_frames, ignore_index=True)
    event_rows = event_rows.sort_values(
        ["event_id", "window_label", "relative_day"],
    ).reset_index(drop=True)

    summary = summarize_event_window_car(event_rows)
    summary = (
        events.merge(summary, on="event_id", how="inner")
        .sort_values(["event_date", "event_id", "window_label"])
        .reset_index(drop=True)
    )
    summary["event_date"] = summary["event_date"].astype(str)

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / ROWS_OUTPUT
    summary_path = output_dir / SUMMARY_OUTPUT
    event_rows.to_csv(rows_path, index=False)
    summary.to_csv(summary_path, index=False)

    return H2OutputResult(
        rows_path=rows_path,
        summary_path=summary_path,
        event_count=len(events),
        event_window_row_count=len(event_rows),
        summary_row_count=len(summary),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--events", type=Path, default=SEED_PATH)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--market-id", default=None)
    parser.add_argument("--token-id", default=None)
    args = parser.parse_args(argv)

    try:
        result = generate_h2_event_window_outputs(
            db_path=args.db,
            events_csv_path=args.events,
            output_dir=args.output_dir,
            market_id=args.market_id,
            token_id=args.token_id,
        )
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _price_query_bounds(
    events: pd.DataFrame,
    windows: Sequence[EventWindow],
) -> tuple[date, date]:
    event_dates = list(events["event_date"])
    min_offset = min(
        [DEFAULT_ESTIMATION_WINDOW[0], *(window.start_day for window in windows)]
    )
    max_offset = max(window.end_day for window in windows)
    query_start = min(event_dates) + timedelta(days=min_offset - 1)
    query_end = max(event_dates) + timedelta(days=max_offset)
    return query_start, query_end


if __name__ == "__main__":
    raise SystemExit(main())
