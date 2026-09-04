"""Tests for idempotent SQLite schema migrations."""
from __future__ import annotations

import sqlite3

import pytest


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(1) FROM {table}").fetchone()[0])


def _assert_required_columns(conn: sqlite3.Connection) -> None:
    from operations.db.migrations import REQUIRED_ARCHITECTURE_COLUMNS

    for table, required_columns in REQUIRED_ARCHITECTURE_COLUMNS.items():
        columns = _columns(conn, table)
        for column in required_columns:
            if column == "id":
                continue
            assert column in columns, f"{table}.{column} is missing"


def test_migrate_creates_required_tables_in_empty_database(tmp_path):
    """Migration creates support tables when the SQLite file exists but is empty."""
    from operations.db.migrations import REQUIRED_TABLES, migrate

    db_path = tmp_path / "empty.db"
    sqlite3.connect(db_path).close()

    migrate(db_path)

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert set(REQUIRED_TABLES).issubset(tables)
        for table in REQUIRED_TABLES:
            assert "created_at" in _columns(conn, table)
        _assert_required_columns(conn)
    finally:
        conn.close()


def test_migrate_runs_twice_without_duplicate_columns(tmp_path):
    """Migration is idempotent across repeated runs."""
    from operations.db.migrations import REQUIRED_TABLES, migrate

    db_path = tmp_path / "twice.db"
    sqlite3.connect(db_path).close()

    migrate(db_path)
    migrate(db_path)

    conn = sqlite3.connect(db_path)
    try:
        for table in REQUIRED_TABLES:
            assert _columns(conn, table).count("created_at") == 1
            for column in _columns(conn, table):
                assert _columns(conn, table).count(column) == 1
        _assert_required_columns(conn)
    finally:
        conn.close()


def test_migrate_preserves_existing_support_table_rows(tmp_path):
    """Existing rows survive migration and receive created_at metadata."""
    from operations.db.migrations import migrate

    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE events_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_category TEXT,
            description TEXT,
            impact_score REAL
        );
        INSERT INTO events_timeline
            (event_timestamp, event_type, event_category, description, impact_score)
        VALUES
            ('2024-07-21T00:00:00.000000Z', 'biden_withdrawal',
             'poll_shock', 'Biden withdraws', 1.0);

        CREATE TABLE analysis_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            date_range_start TEXT,
            date_range_end TEXT,
            value_json TEXT NOT NULL,
            computed_at TEXT NOT NULL
        );
        INSERT INTO analysis_summaries
            (table_name, metric_name, value_json, computed_at)
        VALUES
            ('polymarket_prices', 'weekly_avg_price', '{}',
             '2026-04-14T23:00:32+00:00');

        CREATE TABLE llm_audit_log (
            call_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            tier INTEGER NOT NULL,
            system_prompt_hash TEXT,
            system_prompt_version TEXT,
            user_prompt TEXT,
            response TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_usd REAL,
            cached_tokens INTEGER,
            tools_called TEXT,
            tool_results_summary TEXT,
            consistency_group_id TEXT
        );
        INSERT INTO llm_audit_log
            (call_id, run_id, timestamp, model, tier)
        VALUES
            ('call-1', 'run-1', '2026-04-14T23:01:43+00:00',
             'claude-test', 1);
        """
    )
    conn.close()

    migrate(db_path)

    conn = sqlite3.connect(db_path)
    try:
        assert _row_count(conn, "events_timeline") == 1
        assert _row_count(conn, "analysis_summaries") == 1
        assert _row_count(conn, "llm_audit_log") == 1
        _assert_required_columns(conn)
        for table in ("events_timeline", "analysis_summaries", "llm_audit_log"):
            assert "created_at" in _columns(conn, table)
            nulls = conn.execute(
                f"SELECT COUNT(1) FROM {table} WHERE created_at IS NULL"
            ).fetchone()[0]
            assert nulls == 0
    finally:
        conn.close()


def test_migrate_adds_new_architecture_columns_to_existing_tables(tmp_path):
    """Legacy support tables receive new architecture columns additively."""
    from operations.db.migrations import migrate

    db_path = tmp_path / "old-shape.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE events_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_category TEXT,
            description TEXT,
            impact_score REAL
        );
        CREATE TABLE analysis_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            date_range_start TEXT,
            date_range_end TEXT,
            value_json TEXT NOT NULL,
            computed_at TEXT NOT NULL
        );
        CREATE TABLE llm_audit_log (
            call_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            tier INTEGER NOT NULL,
            system_prompt_hash TEXT,
            system_prompt_version TEXT,
            user_prompt TEXT,
            response TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_usd REAL,
            cached_tokens INTEGER,
            tools_called TEXT,
            tool_results_summary TEXT,
            consistency_group_id TEXT
        );
        """
    )
    conn.close()

    migrate(db_path)
    migrate(db_path)

    conn = sqlite3.connect(db_path)
    try:
        _assert_required_columns(conn)
        event_columns = _columns(conn, "events_timeline")
        assert "event_timestamp" in event_columns
        assert "event_category" in event_columns
        summary_columns = _columns(conn, "analysis_summaries")
        assert "table_name" in summary_columns
        assert "metric_name" in summary_columns
        assert "value_json" in summary_columns
        assert "computed_at" in summary_columns
    finally:
        conn.close()


def test_migrate_preserves_existing_created_at_values(tmp_path):
    """Rows that already have created_at are not overwritten."""
    from operations.db.migrations import migrate

    db_path = tmp_path / "existing-created-at.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE events_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_category TEXT,
            description TEXT,
            impact_score REAL,
            created_at TEXT
        );
        INSERT INTO events_timeline
            (event_timestamp, event_type, created_at)
        VALUES
            ('2024-11-05T12:00:00.000000Z', 'election_day',
             '2024-01-01 00:00:00');
        """
    )
    conn.close()

    migrate(db_path)

    conn = sqlite3.connect(db_path)
    try:
        created_at = conn.execute(
            "SELECT created_at FROM events_timeline WHERE event_type = 'election_day'"
        ).fetchone()[0]
        assert created_at == "2024-01-01 00:00:00"
    finally:
        conn.close()


def test_table_exists_reports_presence_and_absence(tmp_path):
    """table_exists distinguishes a created table from one that was never created."""
    from operations.db.migrations import table_exists

    db_path = tmp_path / "presence.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE events_timeline (id INTEGER PRIMARY KEY)")
        assert table_exists(conn, "events_timeline") is True
        assert table_exists(conn, "analysis_summaries") is False
    finally:
        conn.close()


def test_column_exists_rejects_unsupported_table_identifier(tmp_path):
    """Table names outside the fixed allowlist are rejected, not interpolated into SQL."""
    from operations.db.migrations import column_exists

    db_path = tmp_path / "guard.db"
    conn = sqlite3.connect(db_path)
    try:
        with pytest.raises(ValueError, match="unsupported SQLite identifier"):
            column_exists(conn, "events_timeline; DROP TABLE events_timeline;--", "id")
    finally:
        conn.close()


def test_main_reports_missing_database(capsys, monkeypatch, tmp_path):
    """CLI path returns a clear error when data/thesis.db is missing."""
    from operations.db import migrations

    missing_db = tmp_path / "missing.db"
    monkeypatch.setattr(migrations, "DB_PATH", missing_db)

    exit_code = migrations.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "ERROR:" in captured.err
    assert str(missing_db) in captured.err
