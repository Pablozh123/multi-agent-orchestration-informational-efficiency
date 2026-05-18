"""Tests for the deterministic SQLite data inventory."""
from __future__ import annotations

import sqlite3

import pytest


def test_inventory_reports_expected_core_schema(tmp_path):
    """Inventory sees the thesis schema created by init_db.py."""
    from init_db import init
    from operations.analysis.data_inventory import generate_inventory

    db_path = tmp_path / "thesis.db"
    init(db_path=db_path, force_recreate=True)

    inventory = generate_inventory(db_path)
    tables = {table["name"]: table for table in inventory["tables"]}

    expected_tables = {
        "analysis_summaries",
        "events_timeline",
        "llm_audit_log",
        "market_maker_exclusions",
        "poll_forecasts",
        "polymarket_prices",
        "sentiment_scores",
        "whale_trades",
    }
    assert set(tables) == expected_tables
    assert tables["polymarket_prices"]["date_column"] == "price_timestamp"
    assert tables["poll_forecasts"]["date_column"] == "date"
    assert tables["whale_trades"]["date_column"] == "price_timestamp"

    price_columns = {column["name"] for column in tables["polymarket_prices"]["columns"]}
    assert {"price_timestamp", "market_id", "token_id", "price"}.issubset(price_columns)


def test_inventory_uses_aggregate_coverage_only(tmp_path):
    """Coverage output contains counts, not raw database rows."""
    from operations.analysis.data_inventory import generate_inventory

    db_path = tmp_path / "inventory.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE poll_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            candidate TEXT NOT NULL,
            probability REAL NOT NULL,
            poll_type TEXT
        );
        INSERT INTO poll_forecasts
            (date, source, candidate, probability, poll_type)
        VALUES
            ('2024-03-01', 'fivethirtyeight', 'trump', 0.55, 'model'),
            ('2024-03-02', 'fivethirtyeight', 'trump', 0.56, 'model'),
            ('2024-03-02', 'fivethirtyeight', 'harris', 0.44, 'model');
        """
    )
    conn.close()

    inventory = generate_inventory(db_path)
    table = inventory["tables"][0]

    assert table["row_count"] == 3
    assert table["date_min"] == "2024-03-01"
    assert table["date_max"] == "2024-03-02"
    assert table["coverage"]["source"] == {"fivethirtyeight": 3}
    assert table["coverage"]["candidate"] == {"trump": 2, "harris": 1}
    assert "probability" not in table["coverage"]


def test_inventory_detects_likely_date_column_without_static_mapping(tmp_path):
    """Inventory detects date-like columns on ad hoc tables."""
    from operations.analysis.data_inventory import generate_inventory

    db_path = tmp_path / "inventory.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE custom_source (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observed_at TEXT NOT NULL,
            value REAL NOT NULL
        );
        INSERT INTO custom_source (observed_at, value)
        VALUES
            ('2024-01-02T00:00:00Z', 1.0),
            ('2024-01-03T00:00:00Z', 2.0);
        """
    )
    conn.close()

    inventory = generate_inventory(db_path)
    table = inventory["tables"][0]

    assert table["date_column"] == "observed_at"
    assert table["date_min"] == "2024-01-02T00:00:00Z"
    assert table["date_max"] == "2024-01-03T00:00:00Z"


def test_inventory_rejects_unsafe_identifiers():
    """Dynamic SQLite identifiers are allow-listed by syntax."""
    from operations.analysis.data_inventory import _quote_identifier

    assert _quote_identifier("poll_forecasts") == '"poll_forecasts"'
    with pytest.raises(ValueError):
        _quote_identifier("poll_forecasts; DROP TABLE poll_forecasts")


def test_main_reports_missing_database(capsys, monkeypatch, tmp_path):
    """CLI returns a clear error instead of a traceback when thesis.db is absent."""
    from operations.analysis import data_inventory

    missing_db = tmp_path / "missing.db"
    monkeypatch.setattr(data_inventory, "DB_PATH", missing_db)

    exit_code = data_inventory.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "ERROR:" in captured.err
    assert str(missing_db) in captured.err
