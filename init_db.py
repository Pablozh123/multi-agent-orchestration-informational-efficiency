"""Initialisiert die SQLite-Datenbank fuer die BA-Thesis mit dem korrekten Zielschema.

Fuehrt alle PRAGMAs vor dem ersten CREATE TABLE aus (WAL-Modus, Busy-Timeout,
synchronous=NORMAL). Erstellt sechs Tabellen und alle notwendigen Indizes.
Das Skript ist idempotent: bei jedem Aufruf wird die bestehende Datei geloescht
und neu erstellt, um Schema-Divergenz zu verhindern.
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/thesis.db")

# PRAGMAs first — WAL must be set before any CREATE TABLE
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=10000;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS polymarket_prices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    price_timestamp  TEXT    NOT NULL,
    fetched_at       TEXT    NOT NULL,
    market_id        TEXT    NOT NULL,
    token_id         TEXT,
    price            REAL    NOT NULL CHECK(price >= 0.0 AND price <= 1.0),
    volume_24h       REAL,
    best_bid         REAL,
    best_ask         REAL,
    UNIQUE(price_timestamp, market_id, token_id)
);

CREATE TABLE IF NOT EXISTS whale_trades (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    price_timestamp  TEXT    NOT NULL,
    tx_hash          TEXT    UNIQUE,
    wallet_address   TEXT    NOT NULL,
    market_id        TEXT,
    direction        TEXT    NOT NULL CHECK(direction IN ('BUY', 'SELL')),
    amount_usd       REAL    NOT NULL,
    token_id         TEXT,
    price_at_trade   REAL
);

CREATE TABLE IF NOT EXISTS market_maker_exclusions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address   TEXT    NOT NULL UNIQUE,
    label            TEXT,
    source           TEXT,
    added_at         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS poll_forecasts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT    NOT NULL,
    source           TEXT    NOT NULL,
    candidate        TEXT    NOT NULL,
    probability      REAL    NOT NULL,
    poll_type        TEXT,
    UNIQUE(date, source, candidate, poll_type)
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT    NOT NULL,
    source           TEXT    NOT NULL,
    topic            TEXT,
    sentiment        REAL    NOT NULL,
    volume           INTEGER,
    raw_text_sample  TEXT
);

CREATE TABLE IF NOT EXISTS events_timeline (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp  TEXT    NOT NULL,
    event_type       TEXT    NOT NULL,
    event_category   TEXT,
    description      TEXT,
    impact_score     REAL
);

CREATE INDEX IF NOT EXISTS idx_prices_market_time
    ON polymarket_prices(market_id, price_timestamp);
CREATE INDEX IF NOT EXISTS idx_whale_wallet
    ON whale_trades(wallet_address);
CREATE INDEX IF NOT EXISTS idx_whale_time
    ON whale_trades(price_timestamp);
CREATE INDEX IF NOT EXISTS idx_polls_date_source
    ON poll_forecasts(date, source);
CREATE INDEX IF NOT EXISTS idx_sentiment_time
    ON sentiment_scores(timestamp, source);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Oeffnet eine SQLite-Verbindung mit WAL-Modus und Busy-Timeout.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei.

    Returns:
        Offene sqlite3.Connection mit gesetzten PRAGMAs.
    """
    # Open connection and apply WAL settings
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init(db_path: Path = DB_PATH, force_recreate: bool = True) -> None:
    """Initialisiert die SQLite-Datenbank mit dem korrekten Thesis-Schema.

    Loescht bei force_recreate=True die bestehende Datei, um Schema-Divergenz
    zu vermeiden. Erstellt alle sechs Tabellen sowie die erforderlichen Indizes.
    Verifiziert nach der Erstellung, dass der WAL-Modus aktiv ist.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei (Standard: data/thesis.db).
        force_recreate: Wenn True, wird eine bestehende Datei geloescht und
                        neu erstellt (empfohlen fuer Initialisierung).

    Raises:
        AssertionError: Wenn der WAL-Modus nach der Erstellung nicht aktiv ist.
    """
    # Delete existing database to avoid stale schema
    if force_recreate and db_path.exists():
        db_path.unlink()

    # Ensure parent directory exists (creates data/ if needed)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create fresh database and execute full schema
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)

    # Verify WAL mode is active — fails loudly if pragma was ignored
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal", f"WAL-Modus nicht gesetzt: journal_mode={mode!r}"

    # Report created tables
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()

    print(f"Datenbank initialisiert: {db_path}")
    print(f"Tabellen erstellt: {[t[0] for t in tables]}")


if __name__ == "__main__":
    init()
