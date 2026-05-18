"""Audit the canonical readiness of the `events_timeline` table.

The audit is read-only. It reports missing canonical fields, invalid canonical
dates, and detectable duplicate events without deleting or rewriting legacy
event rows.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

from operations.tools.load_events import CANONICAL_EVENT_COLUMNS, DB_PATH


REQUIRED_EVENT_TABLE_COLUMNS: tuple[str, ...] = (
    *CANONICAL_EVENT_COLUMNS,
    "created_at",
)


AUDITED_MISSING_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_date",
    "title",
    "source_url",
    "expected_direction",
    "relevance_score",
)

AUDIT_SELECT_COLUMNS: tuple[str, ...] = (
    "id",
    "event_id",
    "event_date",
    "event_time_utc",
    "title",
    "source_url",
    "expected_direction",
    "relevance_score",
    "event_timestamp",
    "event_type",
)


def audit_event_catalog(db_path: Path = DB_PATH) -> dict[str, Any]:
    """Return a structured audit of canonical event catalog readiness."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return audit_event_catalog_connection(conn, db_path=db_path)
    finally:
        conn.close()


def audit_event_catalog_connection(
    conn: sqlite3.Connection,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Return a structured audit using an existing SQLite connection."""
    columns = _table_columns(conn)
    missing_schema_columns = [
        column for column in REQUIRED_EVENT_TABLE_COLUMNS
        if column not in columns
    ]
    if missing_schema_columns:
        return {
            "db_path": str(db_path) if db_path is not None else None,
            "table": "events_timeline",
            "row_count": 0,
            "missing_schema_columns": missing_schema_columns,
            "missing_event_id_count": 0,
            "missing_event_date_count": 0,
            "missing_title_count": 0,
            "missing_source_url_count": 0,
            "missing_expected_direction_count": 0,
            "missing_relevance_score_count": 0,
            "invalid_dates": [],
            "duplicate_events": {
                "event_id": [],
                "canonical_key": [],
                "legacy_key": [],
            },
        }

    raw_rows = conn.execute(
        """
        SELECT id, event_id, event_date, event_time_utc, title, source_url,
               expected_direction, relevance_score, event_timestamp, event_type
        FROM events_timeline
        ORDER BY id
        """
    ).fetchall()
    rows = [_row_to_dict(row) for row in raw_rows]

    missing_counts = {
        column: _missing_count(rows, column)
        for column in AUDITED_MISSING_COLUMNS
    }
    invalid_dates = _invalid_dates(rows)
    duplicate_events = _duplicate_events(rows)

    return {
        "db_path": str(db_path) if db_path is not None else None,
        "table": "events_timeline",
        "row_count": len(rows),
        "missing_schema_columns": [],
        "missing_event_id_count": missing_counts["event_id"],
        "missing_event_date_count": missing_counts["event_date"],
        "missing_title_count": missing_counts["title"],
        "missing_source_url_count": missing_counts["source_url"],
        "missing_expected_direction_count": missing_counts["expected_direction"],
        "missing_relevance_score_count": missing_counts["relevance_score"],
        "invalid_dates": invalid_dates,
        "duplicate_events": duplicate_events,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for event catalog audits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args(argv)

    try:
        report = audit_event_catalog(args.db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _table_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("PRAGMA table_info(events_timeline)").fetchall()
    return {row[1] for row in rows}


def _missing_count(rows: Sequence[dict[str, Any]], column: str) -> int:
    return sum(1 for row in rows if _is_blank(row[column]))


def _invalid_dates(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for row in rows:
        value = row["event_date"]
        if _is_blank(value):
            continue
        try:
            date.fromisoformat(str(value))
        except ValueError:
            invalid.append(
                {
                    "id": row["id"],
                    "column": "event_date",
                    "value": value,
                }
            )
    return invalid


def _duplicate_events(rows: Sequence[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "event_id": _duplicates(
            _key(row["event_id"]) for row in rows
        ),
        "canonical_key": _duplicates(
            _joined_key(row["event_date"], row["event_time_utc"], row["title"])
            for row in rows
        ),
        "legacy_key": _duplicates(
            _joined_key(row["event_timestamp"], row["event_type"])
            for row in rows
        ),
    }


def _duplicates(keys: Iterable[str | None]) -> list[dict[str, Any]]:
    counts = Counter(key for key in keys if key is not None)
    return [
        {"key": key, "count": count}
        for key, count in sorted(counts.items())
        if count > 1
    ]


def _joined_key(*values: object) -> str | None:
    if any(_is_blank(value) for value in values):
        return None
    return "|".join(str(value).strip() for value in values)


def _key(value: object) -> str | None:
    if _is_blank(value):
        return None
    return str(value).strip()


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _row_to_dict(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return dict(zip(AUDIT_SELECT_COLUMNS, row))


if __name__ == "__main__":
    raise SystemExit(main())
