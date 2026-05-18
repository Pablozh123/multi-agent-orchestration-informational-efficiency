"""Canonical event catalog loader for H2 event-window preparation.

The loader is deterministic and local-only. It reads a manually curated CSV,
validates canonical event fields, and upserts rows by `event_id` without
touching legacy rows that have no canonical identifier.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Sequence


DB_PATH = Path("data/thesis.db")
SEED_PATH = Path("data/events_timeline_seed.csv")

CANONICAL_EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "event_time_utc",
    "title",
    "description",
    "event_type",
    "source_url",
    "expected_direction",
    "relevance_score",
)


@dataclass(frozen=True)
class LoadEventsResult:
    """Summary of a canonical event catalog load."""

    inserted: int
    updated: int
    input_rows: int

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-friendly summary."""
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "input_rows": self.input_rows,
        }


def read_event_seed(csv_path: Path = SEED_PATH) -> list[dict[str, str]]:
    """Read canonical event rows from CSV and validate the header."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Event seed CSV not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Event seed CSV has no header: {csv_path}")
        missing = [
            column for column in CANONICAL_EVENT_COLUMNS
            if column not in reader.fieldnames
        ]
        if missing:
            raise ValueError(f"Event seed CSV is missing columns: {missing}")
        return [
            {column: (row.get(column) or "").strip() for column in CANONICAL_EVENT_COLUMNS}
            for row in reader
        ]


def validate_event_row(row: dict[str, str], row_number: int = 1) -> dict[str, str | float]:
    """Validate and normalize one canonical event CSV row.

    Required fields must be non-empty. `event_date` must be an ISO date,
    `event_time_utc` must be an ISO time, and `relevance_score` must be a
    number between 0 and 1.
    """
    missing = [
        column for column in CANONICAL_EVENT_COLUMNS
        if _is_blank(row.get(column))
    ]
    if missing:
        raise ValueError(f"event row {row_number} missing canonical fields: {missing}")

    event_date = _normalize_date(row["event_date"], row_number)
    event_time_utc = _normalize_time(row["event_time_utc"], row_number)
    relevance_score = _normalize_relevance_score(row["relevance_score"], row_number)

    return {
        "event_id": row["event_id"].strip(),
        "event_date": event_date,
        "event_time_utc": event_time_utc,
        "title": row["title"].strip(),
        "description": row["description"].strip(),
        "event_type": row["event_type"].strip(),
        "source_url": row["source_url"].strip(),
        "expected_direction": row["expected_direction"].strip(),
        "relevance_score": relevance_score,
    }


def upsert_events(
    conn: sqlite3.Connection,
    rows: Sequence[dict[str, str]],
) -> LoadEventsResult:
    """Validate and upsert canonical events by `event_id`.

    Legacy rows with NULL or blank `event_id` are preserved because the lookup is
    only performed against explicit canonical identifiers.
    """
    inserted = 0
    updated = 0
    validated = [
        validate_event_row(row, row_number=index)
        for index, row in enumerate(rows, start=1)
    ]

    with conn:
        for row in validated:
            existing = conn.execute(
                """
                SELECT id
                FROM events_timeline
                WHERE event_id = ?
                ORDER BY id
                LIMIT 2
                """,
                (row["event_id"],),
            ).fetchall()
            if len(existing) > 1:
                raise ValueError(
                    f"multiple existing events share event_id={row['event_id']!r}"
                )
            if existing:
                conn.execute(
                    """
                    UPDATE events_timeline
                    SET event_date = ?,
                        event_time_utc = ?,
                        title = ?,
                        description = ?,
                        event_type = ?,
                        source_url = ?,
                        expected_direction = ?,
                        relevance_score = ?
                    WHERE event_id = ?
                    """,
                    (
                        row["event_date"],
                        row["event_time_utc"],
                        row["title"],
                        row["description"],
                        row["event_type"],
                        row["source_url"],
                        row["expected_direction"],
                        row["relevance_score"],
                        row["event_id"],
                    ),
                )
                updated += 1
            else:
                conn.execute(
                    """
                    INSERT INTO events_timeline
                        (event_id, event_date, event_time_utc, title,
                         description, event_type, source_url,
                         expected_direction, relevance_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        row["event_id"],
                        row["event_date"],
                        row["event_time_utc"],
                        row["title"],
                        row["description"],
                        row["event_type"],
                        row["source_url"],
                        row["expected_direction"],
                        row["relevance_score"],
                    ),
                )
                inserted += 1

    return LoadEventsResult(
        inserted=inserted,
        updated=updated,
        input_rows=len(rows),
    )


def load_events_from_csv(
    db_path: Path = DB_PATH,
    csv_path: Path = SEED_PATH,
) -> LoadEventsResult:
    """Load canonical events from CSV into SQLite."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    rows = read_event_seed(csv_path)
    conn = sqlite3.connect(db_path)
    try:
        return upsert_events(conn, rows)
    finally:
        conn.close()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the canonical event loader."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--csv", type=Path, default=SEED_PATH)
    args = parser.parse_args(argv)

    try:
        result = load_events_from_csv(db_path=args.db, csv_path=args.csv)
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _normalize_date(value: str, row_number: int) -> str:
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except ValueError as exc:
        raise ValueError(
            f"event row {row_number} has invalid event_date: {value!r}"
        ) from exc


def _normalize_time(value: str, row_number: int) -> str:
    normalized = value.strip().removesuffix("Z")
    try:
        parsed = time.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"event row {row_number} has invalid event_time_utc: {value!r}"
        ) from exc
    return parsed.replace(microsecond=0).isoformat()


def _normalize_relevance_score(value: str, row_number: int) -> float:
    try:
        score = float(value)
    except ValueError as exc:
        raise ValueError(
            f"event row {row_number} has invalid relevance_score: {value!r}"
        ) from exc
    if score < 0.0 or score > 1.0:
        raise ValueError(
            f"event row {row_number} relevance_score must be between 0 and 1"
        )
    return score


if __name__ == "__main__":
    raise SystemExit(main())
