"""Initialisiert die SQLite-Datenbank mit dem Thesis-Schema."""
import sqlite3

DB_PATH = "data/thesis.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS polymarket_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    market_id TEXT NOT NULL,
    token_id TEXT,
    price REAL NOT NULL,
    volume REAL,
    UNIQUE(timestamp, market_id, token_id)
);

CREATE TABLE IF NOT EXISTS whale_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tx_hash TEXT UNIQUE,
    wallet_address TEXT NOT NULL,
    market_id TEXT,
    direction TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    token_id TEXT,
    price_at_trade REAL
);

CREATE TABLE IF NOT EXISTS poll_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    candidate TEXT NOT NULL,
    probability REAL NOT NULL,
    poll_type TEXT,
    UNIQUE(date, source, candidate, poll_type)
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    topic TEXT,
    sentiment REAL NOT NULL,
    volume INTEGER,
    raw_text_sample TEXT
);

CREATE TABLE IF NOT EXISTS events_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT,
    impact_score REAL
);

CREATE INDEX IF NOT EXISTS idx_prices_market_time
    ON polymarket_prices(market_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_whale_wallet
    ON whale_transactions(wallet_address);
CREATE INDEX IF NOT EXISTS idx_whale_time
    ON whale_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_polls_date_source
    ON poll_forecasts(date, source);
CREATE INDEX IF NOT EXISTS idx_sentiment_time
    ON sentiment_scores(timestamp, source);
"""

def init():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.close()
    print(f"Datenbank initialisiert: {DB_PATH}")

    # Verifizieren
    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    print(f"Tabellen erstellt: {[t[0] for t in tables]}")
    conn.close()

if __name__ == "__main__":
    init()
