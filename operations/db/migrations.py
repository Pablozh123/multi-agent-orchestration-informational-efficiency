"""Idempotent SQLite migrations for thesis support tables.

The migration layer is intentionally small and additive. It creates missing
support tables and adds missing architecture columns without dropping,
renaming, truncating, or recreating existing thesis data.

Usage:
    python -m operations.db.migrations
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


DB_PATH = Path("data/thesis.db")
REQUIRED_TABLES = ("events_timeline", "analysis_summaries", "llm_audit_log")


SUPPORT_TABLE_COLUMNS = {
    "events_timeline": {
        "event_id": "TEXT",
        "event_date": "TEXT",
        "event_time_utc": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "event_type": "TEXT",
        "source_url": "TEXT",
        "expected_direction": "TEXT",
        "relevance_score": "REAL",
        "created_at": "TEXT",
        # Compatibility columns used by the current deterministic tooling.
        "id": "INTEGER",
        "event_timestamp": "TEXT",
        "event_category": "TEXT",
        "impact_score": "REAL",
    },
    "analysis_summaries": {
        "summary_id": "TEXT",
        "run_id": "TEXT",
        "summary_type": "TEXT",
        "date_range_start": "TEXT",
        "date_range_end": "TEXT",
        "input_tables": "TEXT",
        "metrics_json": "TEXT",
        "summary_json": "TEXT",
        "created_at": "TEXT",
        # Compatibility columns used by the current deterministic tooling.
        "id": "INTEGER",
        "table_name": "TEXT",
        "metric_name": "TEXT",
        "value_json": "TEXT",
        "computed_at": "TEXT",
    },
    "llm_audit_log": {
        "call_id": "TEXT",
        "run_id": "TEXT",
        "timestamp": "TEXT",
        "model": "TEXT",
        "tier": "INTEGER",
        "system_prompt_hash": "TEXT",
        "system_prompt_version": "TEXT",
        "user_prompt": "TEXT",
        "response": "TEXT",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "cost_usd": "REAL",
        "cached_tokens": "INTEGER",
        "tools_called": "TEXT",
        "tool_results_summary": "TEXT",
        "consistency_group_id": "TEXT",
        # Kept as additive metadata from the support-table migration.
        "created_at": "TEXT",
    },
}

REQUIRED_ARCHITECTURE_COLUMNS = {
    table_name: tuple(columns.keys())
    for table_name, columns in SUPPORT_TABLE_COLUMNS.items()
}


CREATE_TABLE_SQL = {
    "events_timeline": """
        CREATE TABLE IF NOT EXISTS events_timeline (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id            TEXT,
            event_date          TEXT,
            event_time_utc      TEXT,
            title               TEXT,
            description         TEXT,
            event_type          TEXT,
            source_url          TEXT,
            expected_direction  TEXT,
            relevance_score     REAL,
            event_timestamp     TEXT,
            event_category      TEXT,
            impact_score        REAL,
            created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "analysis_summaries": """
        CREATE TABLE IF NOT EXISTS analysis_summaries (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id        TEXT,
            run_id            TEXT,
            summary_type      TEXT,
            date_range_start  TEXT,
            date_range_end    TEXT,
            input_tables      TEXT,
            metrics_json      TEXT,
            summary_json      TEXT,
            table_name        TEXT,
            metric_name       TEXT,
            value_json        TEXT,
            computed_at       TEXT,
            created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "llm_audit_log": """
        CREATE TABLE IF NOT EXISTS llm_audit_log (
            call_id                TEXT PRIMARY KEY,
            run_id                 TEXT NOT NULL,
            timestamp              TEXT NOT NULL,
            model                  TEXT NOT NULL,
            tier                   INTEGER NOT NULL,
            system_prompt_hash     TEXT,
            system_prompt_version  TEXT,
            user_prompt            TEXT,
            response               TEXT,
            input_tokens           INTEGER,
            output_tokens          INTEGER,
            cost_usd               REAL,
            cached_tokens          INTEGER,
            tools_called           TEXT,
            tool_results_summary   TEXT,
            consistency_group_id   TEXT,
            created_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_events_date ON events_timeline(event_date)",
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events_timeline(event_timestamp)",
    """
    CREATE INDEX IF NOT EXISTS idx_summaries_run_type
        ON analysis_summaries(run_id, summary_type)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_summaries_metric
        ON analysis_summaries(table_name, metric_name)
    """,
    "CREATE INDEX IF NOT EXISTS idx_audit_run ON llm_audit_log(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_time ON llm_audit_log(timestamp)",
)


def _allowed_identifiers() -> set[str]:
    """Return identifiers the migration may use in generated SQL."""
    identifiers = set(REQUIRED_TABLES)
    for columns in SUPPORT_TABLE_COLUMNS.values():
        identifiers.update(columns)
    return identifiers


def _quote_identifier(identifier: str) -> str:
    """Return a safely quoted SQLite identifier for known required objects."""
    if identifier not in _allowed_identifiers():
        raise ValueError(f"unsupported SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Return True if a non-system table exists."""
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Return True if `column_name` exists on `table_name`."""
    quoted_table = _quote_identifier(table_name)
    rows = conn.execute(f"PRAGMA table_info({quoted_table})").fetchall()
    return any(row[1] == column_name for row in rows)


def ensure_required_tables(conn: sqlite3.Connection) -> None:
    """Create required support tables if they are missing."""
    for table_name in REQUIRED_TABLES:
        conn.execute(CREATE_TABLE_SQL[table_name])


def ensure_required_indexes(conn: sqlite3.Connection) -> None:
    """Create support-table indexes after required columns exist."""
    for sql in INDEX_SQL:
        conn.execute(sql)


def ensure_required_columns(conn: sqlite3.Connection) -> None:
    """Add missing support-table columns without rewriting existing data."""
    for table_name in REQUIRED_TABLES:
        quoted_table = _quote_identifier(table_name)
        for column_name, column_type in SUPPORT_TABLE_COLUMNS[table_name].items():
            if column_name == "id":
                # Existing and newly-created compatibility schemas already use
                # id as a primary key where needed. Adding another id column to
                # a canonical table would be ambiguous, so only add non-id cols.
                continue
            if not column_exists(conn, table_name, column_name):
                quoted_column = _quote_identifier(column_name)
                conn.execute(
                    f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {column_type}"
                )


def ensure_created_at_columns(conn: sqlite3.Connection) -> None:
    """Backfill `created_at` metadata for required support tables."""
    for table_name in REQUIRED_TABLES:
        quoted_table = _quote_identifier(table_name)
        if not column_exists(conn, table_name, "created_at"):
            conn.execute(f"ALTER TABLE {quoted_table} ADD COLUMN created_at TEXT")
        conn.execute(
            f"""
            UPDATE {quoted_table}
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
            """
        )


def migrate(db_path: Path = DB_PATH) -> None:
    """Run all idempotent support-table migrations for a SQLite database."""
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        with conn:
            ensure_required_tables(conn)
            ensure_required_columns(conn)
            ensure_created_at_columns(conn)
            ensure_required_indexes(conn)
    finally:
        conn.close()


def main() -> int:
    """CLI entry point for `python -m operations.db.migrations`."""
    try:
        migrate(DB_PATH)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Migrations applied successfully: {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
