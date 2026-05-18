"""Deterministic data inventory for thesis.db.

The inventory is intentionally aggregate-only: table shapes, row counts,
date ranges, null counts, and compact source/candidate coverage. It does not
dump raw rows and does not call external APIs.

Usage:
    python -m operations.analysis.data_inventory
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DB_PATH = Path("data/thesis.db")
MAX_GROUPS = 20

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

DATE_COLUMNS = {
    "polymarket_prices": "price_timestamp",
    "whale_trades": "price_timestamp",
    "poll_forecasts": "date",
    "sentiment_scores": "timestamp",
    "events_timeline": "event_timestamp",
    "market_maker_exclusions": "added_at",
    "analysis_summaries": "computed_at",
    "llm_audit_log": "timestamp",
}

COVERAGE_COLUMNS = ("source", "candidate", "event_category", "direction")
DATE_NAME_HINTS = ("date", "timestamp", "time", "created_at", "computed_at", "fetched_at")


def _is_likely_date_column(column: str) -> bool:
    """Return True when a column name looks like a date or timestamp field."""
    lowered = column.lower()
    return lowered.endswith("_at") or any(hint in lowered for hint in DATE_NAME_HINTS)


@dataclass(frozen=True)
class ColumnInventory:
    """Column metadata plus null count."""

    name: str
    type: str
    not_null: bool
    primary_key: bool
    null_count: int


@dataclass(frozen=True)
class TableInventory:
    """Aggregate inventory for one SQLite table."""

    name: str
    row_count: int
    columns: list[ColumnInventory]
    date_column: str | None
    date_min: str | None
    date_max: str | None
    coverage: dict[str, dict[str, int]]


def _quote_identifier(identifier: str) -> str:
    """Return a safely quoted SQLite identifier."""
    if not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"unsafe SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def _list_tables(conn: sqlite3.Connection) -> list[str]:
    """Return non-system table names from the database."""
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _table_columns(conn: sqlite3.Connection, table: str) -> list[tuple[str, str, bool, bool]]:
    """Return (name, type, not_null, primary_key) for a table."""
    quoted = _quote_identifier(table)
    rows = conn.execute(f"PRAGMA table_info({quoted})").fetchall()
    return [
        (str(row[1]), str(row[2]), bool(row[3]), bool(row[5]))
        for row in rows
    ]


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    quoted = _quote_identifier(table)
    return int(conn.execute(f"SELECT COUNT(1) FROM {quoted}").fetchone()[0])


def _null_count(conn: sqlite3.Connection, table: str, column: str) -> int:
    quoted_table = _quote_identifier(table)
    quoted_column = _quote_identifier(column)
    return int(
        conn.execute(
            f"SELECT COUNT(1) FROM {quoted_table} WHERE {quoted_column} IS NULL"
        ).fetchone()[0]
    )


def _date_range(
    conn: sqlite3.Connection,
    table: str,
    columns: set[str],
) -> tuple[str | None, str | None, str | None]:
    quoted_table = _quote_identifier(table)
    preferred = DATE_COLUMNS.get(table)
    candidates: list[str] = []

    if preferred in columns:
        candidates.append(preferred)

    candidates.extend(
        column
        for column in sorted(columns)
        if column not in candidates
        and _is_likely_date_column(column)
    )

    for date_column in candidates:
        quoted_column = _quote_identifier(date_column)
        row = conn.execute(
            f"""
            SELECT MIN({quoted_column}) AS date_min, MAX({quoted_column}) AS date_max
            FROM {quoted_table}
            WHERE {quoted_column} IS NOT NULL
            """
        ).fetchone()
        if row[0] is not None or row[1] is not None:
            return date_column, row[0], row[1]

    if candidates:
        return candidates[0], None, None
    return None, None, None


def _coverage_counts(
    conn: sqlite3.Connection,
    table: str,
    columns: set[str],
) -> dict[str, dict[str, int]]:
    quoted_table = _quote_identifier(table)
    coverage: dict[str, dict[str, int]] = {}

    for column in COVERAGE_COLUMNS:
        if column not in columns:
            continue
        quoted_column = _quote_identifier(column)
        rows = conn.execute(
            f"""
            SELECT {quoted_column} AS value, COUNT(1) AS row_count
            FROM {quoted_table}
            WHERE {quoted_column} IS NOT NULL
            GROUP BY {quoted_column}
            ORDER BY row_count DESC, value ASC
            LIMIT ?
            """,
            (MAX_GROUPS,),
        ).fetchall()
        coverage[column] = {str(value): int(count) for value, count in rows}

    return coverage


def inventory_table(conn: sqlite3.Connection, table: str) -> TableInventory:
    """Build aggregate inventory for one table."""
    column_meta = _table_columns(conn, table)
    column_names = {name for name, _, _, _ in column_meta}
    columns = [
        ColumnInventory(
            name=name,
            type=column_type,
            not_null=not_null,
            primary_key=primary_key,
            null_count=_null_count(conn, table, name),
        )
        for name, column_type, not_null, primary_key in column_meta
    ]
    date_column, date_min, date_max = _date_range(conn, table, column_names)

    return TableInventory(
        name=table,
        row_count=_row_count(conn, table),
        columns=columns,
        date_column=date_column,
        date_min=date_min,
        date_max=date_max,
        coverage=_coverage_counts(conn, table, column_names),
    )


def generate_inventory(db_path: Path = DB_PATH) -> dict[str, Any]:
    """Generate a complete aggregate inventory for the SQLite database."""
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        tables = [inventory_table(conn, table) for table in _list_tables(conn)]
    finally:
        conn.close()

    return {
        "database": db_path.as_posix(),
        "table_count": len(tables),
        "tables": [asdict(table) for table in tables],
    }


def main() -> int:
    """Print the data inventory as deterministic JSON."""
    try:
        inventory = generate_inventory(DB_PATH)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(inventory, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
