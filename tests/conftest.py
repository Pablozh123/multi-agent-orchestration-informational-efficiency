"""Pytest-Fixtures fuer die Thesis-Testsuite.

Stellt In-Memory-Datenbankfixtures und Mock-API-Antworten bereit,
damit alle Tests isoliert und ohne Netzwerkzugriff laufen koennen.
"""
import sqlite3
from typing import Generator

import pytest


# Target schema — canonical definition of what the production init_db.py MUST produce.
# Tests run against this fixture; mismatches in init_db.py will surface as failures.
_TARGET_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS polymarket_prices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    price_timestamp  TEXT    NOT NULL,
    fetched_at       TEXT    NOT NULL,
    market_id        TEXT    NOT NULL,
    token_id         TEXT,
    price            REAL    NOT NULL,
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


@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Erstellt eine In-Memory-SQLite-Datenbank mit dem Zielschema.

    Verwendet `:memory:` als Pfad, sodass keine Datei auf dem Dateisystem
    angelegt wird und jeder Test eine saubere, isolierte Datenbankinstanz erhaelt.
    Das hier definierte Schema ist die verbindliche Referenz (Single Source of Truth)
    fuer alle Schematests in test_schema.py.

    Yields:
        sqlite3.Connection: Offene Verbindung zur In-Memory-Datenbank.
    """
    # Open in-memory connection with WAL pragma (no-op on :memory:, documents intent)
    conn = sqlite3.connect(":memory:")
    conn.executescript(_TARGET_SCHEMA)
    yield conn
    conn.close()


@pytest.fixture
def mock_polymarket_response() -> dict:
    """Gibt eine minimale Mock-Antwort der Polymarket CLOB API zurueck.

    Das Format entspricht dem `/prices-history`-Endpunkt mit zwei Preispunkten
    fuer Januar 2024 (Unix-Sekunden-Zeitstempel, wie von der CLOB API geliefert).

    Returns:
        dict: Simulierte API-Antwort mit 'history'-Liste.
    """
    # Two price observations: 2024-01-01T00:00:00Z and 2024-01-02T00:00:00Z
    return {
        "history": [
            {"t": 1704067200, "p": 0.52},
            {"t": 1704153600, "p": 0.55},
        ]
    }


@pytest.fixture
def mock_dune_response() -> list[dict]:
    """Gibt eine minimale Mock-Antwort der Dune Analytics API zurueck.

    Enthaelt zwei Whale-Trade-Zeilen:
    - `0xabc`: normaler Wallet, soll nach dem Filtern erhalten bleiben
    - `0xdeadbeef`: bekannter Market-Maker, soll herausgefiltert werden

    Returns:
        list[dict]: Liste von simulierten Trade-Eintraegen.
    """
    return [
        {
            # Normal wallet — should survive market-maker filter
            "tx_hash": "0xaaa111",
            "wallet_address": "0xabc",
            "market_id": "presidential-2024",
            "direction": "BUY",
            "amount_usd": 5000.0,
            "token_id": "trump-wins",
            "price_at_trade": 0.52,
            "block_time": "2024-01-01T12:00:00Z",
        },
        {
            # Known market maker — should be excluded
            "tx_hash": "0xbbb222",
            "wallet_address": "0xdeadbeef",
            "market_id": "presidential-2024",
            "direction": "SELL",
            "amount_usd": 250000.0,
            "token_id": "trump-wins",
            "price_at_trade": 0.55,
            "block_time": "2024-01-01T13:00:00Z",
        },
    ]


@pytest.fixture
def mock_gdelt_response() -> list[dict]:
    """Gibt eine minimale Mock-Antwort der GDELT API zurueck.

    Enthaelt einen Sentiment-Eintrag fuer den 1. Januar 2024 mit negativem
    Ton (typisch fuer Wahlberichterstattung) und 42 Artikeln.

    Returns:
        list[dict]: Liste von simulierten GDELT-Sentiment-Eintraegen.
    """
    # One sentiment record: slightly negative tone, moderate article count
    return [
        {
            "date": "2024-01-01",
            "tone": -2.5,
            "num_articles": 42,
        }
    ]
