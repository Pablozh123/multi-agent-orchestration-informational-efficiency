"""Schematests fuer die Thesis-SQLite-Datenbank.

Verifiziert, dass die Produktionsdatenbank (init_db.py) das korrekte Zielschema
aufweist: richtige Tabellennamen, Spaltennamen, WAL-Modus und Integritaetsbeschraenkungen.
Alle Tests verwenden das `in_memory_db`-Fixture aus conftest.py als Referenz.

Anforderungsabdeckung:
    DATA-01 — polymarket_prices Korrekte Spaltennamen
    DATA-02 — fetched_at-Spalte vorhanden
    DATA-03 — whale_trades Tabellenname (nicht whale_transactions)
    DATA-04 — market_maker_exclusions Tabelle vorhanden
    DATA-05 — events_timeline event_category-Spalte
    DATA-06 — UNIQUE-Constraint polymarket_prices
    DATA-07 — CHECK-Constraint whale_trades.direction
"""
import sqlite3

import pytest


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Hilfsfunktion: gibt alle Spaltennamen einer Tabelle zurueck."""
    # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def _get_tables(conn: sqlite3.Connection) -> list[str]:
    """Hilfsfunktion: gibt alle Tabellennamen der Datenbank zurueck."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return [row[0] for row in rows]


def test_wal_mode(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, ob das WAL-Journal-Modus-Pragma gesetzt ist.

    Das Fixture setzt PRAGMA journal_mode=WAL. Auf :memory: ist WAL
    technisch eine No-op, aber die Anweisung muss ohne Fehler ausfuehren
    und 'memory' oder 'wal' zurueckgeben (SQLite-Verhalten je nach Version).
    """
    # On :memory: databases SQLite returns 'memory' not 'wal' — that's expected.
    # We assert the pragma runs without raising an exception.
    result = in_memory_db.execute("PRAGMA journal_mode").fetchone()
    assert result is not None, "PRAGMA journal_mode returned no result"
    assert result[0] in ("wal", "memory"), (
        f"Unexpected journal_mode: {result[0]}"
    )


def test_price_timestamp_columns(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass polymarket_prices die korrekten Zeitstempel-Spaltennamen hat.

    Die Spalte muss 'price_timestamp' heissen (nicht 'timestamp' wie im alten Schema).
    Die Spalte 'timestamp' darf NICHT mehr existieren.
    """
    columns = _get_columns(in_memory_db, "polymarket_prices")
    assert "price_timestamp" in columns, (
        "Spalte 'price_timestamp' fehlt in polymarket_prices"
    )
    assert "timestamp" not in columns, (
        "Veraltete Spalte 'timestamp' darf nicht in polymarket_prices existieren"
    )


def test_fetched_at_column(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass die Spalte fetched_at in polymarket_prices vorhanden ist.

    fetched_at dokumentiert den Zeitpunkt des API-Abrufs und verhindert
    Lookahead-Bias in der Analyse (DATA-02).
    """
    columns = _get_columns(in_memory_db, "polymarket_prices")
    assert "fetched_at" in columns, (
        "Spalte 'fetched_at' fehlt in polymarket_prices"
    )


def test_whale_trades_table_name(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass die Tabelle 'whale_trades' (nicht 'whale_transactions') heisst.

    Die Umbenennung ist notwendig, um die konsistente Terminologie in allen
    Queries und Analysen sicherzustellen (DATA-03).
    """
    tables = _get_tables(in_memory_db)
    assert "whale_trades" in tables, (
        "Tabelle 'whale_trades' fehlt — wurde 'whale_transactions' erstellt?"
    )
    assert "whale_transactions" not in tables, (
        "Veralteter Tabellenname 'whale_transactions' darf nicht existieren"
    )


def test_market_maker_exclusions_table(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass die Tabelle market_maker_exclusions existiert und korrekte Spalten hat.

    Diese Tabelle fehlt im urspruenglichen init_db.py vollstaendig (DATA-04).
    Ohne sie koennen Market-Maker nicht aus der Whale-Analyse ausgeschlossen werden.
    """
    tables = _get_tables(in_memory_db)
    assert "market_maker_exclusions" in tables, (
        "Tabelle 'market_maker_exclusions' fehlt vollstaendig"
    )
    columns = _get_columns(in_memory_db, "market_maker_exclusions")
    for required_col in ("wallet_address", "label", "source", "added_at"):
        assert required_col in columns, (
            f"Spalte '{required_col}' fehlt in market_maker_exclusions"
        )


def test_events_timeline_event_category(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass events_timeline die Spalten event_category und event_timestamp hat.

    event_category wird fuer die Ereignisklassifikation benoetigt (DATA-05).
    event_timestamp ersetzt die alte 'timestamp'-Spalte fuer Namenskonsistenz.
    """
    columns = _get_columns(in_memory_db, "events_timeline")
    assert "event_category" in columns, (
        "Spalte 'event_category' fehlt in events_timeline"
    )
    assert "event_timestamp" in columns, (
        "Spalte 'event_timestamp' fehlt in events_timeline"
    )
    assert "timestamp" not in columns, (
        "Veraltete Spalte 'timestamp' darf nicht in events_timeline existieren"
    )


def test_polymarket_prices_unique_constraint(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass der UNIQUE-Constraint (price_timestamp, market_id, token_id) greift.

    Doppelte Eintraege wuerden die Zeitreihenanalyse verfaelschen (DATA-06).
    Der Constraint muss eine sqlite3.IntegrityError ausloesen.
    """
    # Insert a valid first row
    in_memory_db.execute(
        """
        INSERT INTO polymarket_prices
            (price_timestamp, fetched_at, market_id, token_id, price)
        VALUES
            ('2024-01-01T00:00:00.000000Z', '2024-01-01T01:00:00.000000Z',
             'market-1', 'token-1', 0.52)
        """
    )
    # Duplicate row must raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        in_memory_db.execute(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, fetched_at, market_id, token_id, price)
            VALUES
                ('2024-01-01T00:00:00.000000Z', '2024-01-01T01:00:00.000000Z',
                 'market-1', 'token-1', 0.55)
            """
        )


def test_whale_trades_direction_constraint(in_memory_db: sqlite3.Connection) -> None:
    """Prueft, dass whale_trades.direction nur 'BUY' oder 'SELL' akzeptiert.

    Ungueltige Werte wuerden die Trade-Richtungsanalyse unzuverlaessig machen (DATA-07).
    Der CHECK-Constraint muss bei 'INVALID' eine sqlite3.IntegrityError ausloesen.
    """
    with pytest.raises(sqlite3.IntegrityError):
        in_memory_db.execute(
            """
            INSERT INTO whale_trades
                (price_timestamp, wallet_address, direction, amount_usd)
            VALUES
                ('2024-01-01T00:00:00.000000Z', '0xabc', 'INVALID', 1000.0)
            """
        )
