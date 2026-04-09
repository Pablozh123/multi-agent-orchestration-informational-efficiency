"""DuckDB-basierte Query-Tools fuer die Agenten (CLAUDE.md v2.1 §8.3).

Alle Agent-sichtbaren Daten-Zugriffe laufen ueber diese Funktionen. Harte
Invariante: jede Abfrage ist auf maximal 50 Zeilen beschraenkt (Iceberg-
Prinzip — Rohdaten bleiben unten, Agenten sehen nur die Spitze).

DuckDB wird via ATTACH an die bestehende thesis.db gehaengt, damit wir
OLAP-Queries ueber die bereits gefuellten SQLite-Tabellen fahren koennen,
ohne die Daten zu kopieren.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb


logger = logging.getLogger(__name__)

DB_PATH = Path("data/thesis.db")

# Invariant — agents never see more than this many raw rows per call.
MAX_ROWS_PER_QUERY = 50


# --- Connection helper ---------------------------------------------------


def _attach(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Haengt die SQLite-thesis.db per DuckDB-ATTACH an und gibt die Connection zurueck."""
    if not db_path.exists():
        raise FileNotFoundError(f"thesis.db not found at {db_path}")
    conn = duckdb.connect(":memory:")
    conn.execute("INSTALL sqlite; LOAD sqlite;")
    conn.execute(f"ATTACH '{db_path.as_posix()}' AS thesis (TYPE sqlite)")
    return conn


def _rows_to_dicts(result: duckdb.DuckDBPyRelation) -> list[dict[str, Any]]:
    """Konvertiert ein DuckDB-Result in eine Liste von Dicts."""
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


# --- Polymarket prices ---------------------------------------------------


def fetch_polymarket_prices(
    date_range: tuple[str, str],
    resolution: str = "daily",
) -> list[dict[str, Any]]:
    """Liefert Polymarket-Preiszeilen fuer ein Zeitfenster (max. 50).

    Args:
        date_range: (start_iso, end_iso) als YYYY-MM-DD oder vollstaendige ISO-Strings.
        resolution: 'daily' (ein Sample pro Tag) oder 'raw' (limitiert auf 50).

    Returns:
        Liste von Dicts mit price_timestamp, market_id, token_id, price, volume_24h.
    """
    start, end = date_range
    conn = _attach()
    try:
        if resolution == "daily":
            sql = """
                SELECT
                    CAST(price_timestamp AS VARCHAR) AS price_timestamp,
                    market_id,
                    token_id,
                    AVG(price) AS price,
                    MAX(volume_24h) AS volume_24h
                FROM thesis.polymarket_prices
                WHERE price_timestamp BETWEEN ? AND ?
                GROUP BY strftime(CAST(price_timestamp AS TIMESTAMP), '%Y-%m-%d'),
                         market_id, token_id, price_timestamp
                ORDER BY price_timestamp
                LIMIT ?
            """
        else:
            sql = """
                SELECT price_timestamp, market_id, token_id, price, volume_24h
                FROM thesis.polymarket_prices
                WHERE price_timestamp BETWEEN ? AND ?
                ORDER BY price_timestamp
                LIMIT ?
            """
        result = conn.execute(sql, (start, end, MAX_ROWS_PER_QUERY))
        rows = _rows_to_dicts(result)
        logger.info(
            "fetch_polymarket_prices(range=%s..%s, res=%s) -> %d rows",
            start, end, resolution, len(rows),
        )
        return rows
    finally:
        conn.close()


# --- Whale activity ------------------------------------------------------


def query_whale_activity(
    wallet: str | None = None,
    week: str | None = None,
    min_usd: float | None = None,
) -> list[dict[str, Any]]:
    """Liefert Whale-Trades mit optionalen Filtern (max. 50).

    Args:
        wallet: Optional — exakte (lowercase) Wallet-Adresse.
        week: Optional — ISO-Woche als 'YYYY-Www' (z.B. '2024-W40') ODER Datum YYYY-MM-DD.
        min_usd: Optional — minimales amount_usd.

    Returns:
        Whale-Trades-Zeilen, chronologisch sortiert.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if wallet:
        conditions.append("LOWER(wallet_address) = ?")
        params.append(wallet.lower())
    if week:
        # Accept either 'YYYY-Www' or a plain date; convert to a week filter
        if "W" in week:
            conditions.append(
                "strftime(CAST(REPLACE(price_timestamp, ' UTCZ', 'Z') AS TIMESTAMP),"
                " '%G-W%V') = ?"
            )
            params.append(week)
        else:
            conditions.append(
                "CAST(REPLACE(price_timestamp, ' UTCZ', 'Z') AS TIMESTAMP) >= ?"
            )
            params.append(week)
    if min_usd is not None:
        conditions.append("amount_usd >= ?")
        params.append(min_usd)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT
            price_timestamp,
            wallet_address,
            market_id,
            direction,
            amount_usd,
            token_id,
            price_at_trade
        FROM thesis.whale_trades
        {where}
        ORDER BY price_timestamp DESC
        LIMIT ?
    """
    params.append(MAX_ROWS_PER_QUERY)

    conn = _attach()
    try:
        result = conn.execute(sql, tuple(params))
        rows = _rows_to_dicts(result)
        logger.info(
            "query_whale_activity(wallet=%s, week=%s, min_usd=%s) -> %d rows",
            wallet, week, min_usd, len(rows),
        )
        return rows
    finally:
        conn.close()


# --- Sentiment -----------------------------------------------------------


def fetch_sentiment_data(
    date_range: tuple[str, str],
    theme: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Sentiment-Scores fuer ein Zeitfenster (max. 50).

    Args:
        date_range: (start_iso, end_iso).
        theme: Optional — Filter auf sentiment_scores.topic.

    Returns:
        Zeilen mit timestamp, source, topic, sentiment, volume.
    """
    start, end = date_range
    conditions = ["timestamp BETWEEN ? AND ?"]
    params: list[Any] = [start, end]
    if theme:
        conditions.append("topic = ?")
        params.append(theme)

    sql = f"""
        SELECT timestamp, source, topic, sentiment, volume
        FROM thesis.sentiment_scores
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp
        LIMIT ?
    """
    params.append(MAX_ROWS_PER_QUERY)

    conn = _attach()
    try:
        result = conn.execute(sql, tuple(params))
        rows = _rows_to_dicts(result)
        logger.info(
            "fetch_sentiment_data(range=%s..%s, theme=%s) -> %d rows",
            start, end, theme, len(rows),
        )
        return rows
    finally:
        conn.close()


# --- Poll forecasts ------------------------------------------------------


def query_poll_data(
    date_range: tuple[str, str],
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Poll-Forecasts fuer ein Zeitfenster (max. 50).

    Args:
        date_range: (start_iso, end_iso) als YYYY-MM-DD.
        source: Optional — Filter auf source (z.B. 'fivethirtyeight', 'rcp').
    """
    start, end = date_range
    conditions = ["date BETWEEN ? AND ?"]
    params: list[Any] = [start, end]
    if source:
        conditions.append("source = ?")
        params.append(source)

    sql = f"""
        SELECT date, source, candidate, probability, poll_type
        FROM thesis.poll_forecasts
        WHERE {' AND '.join(conditions)}
        ORDER BY date
        LIMIT ?
    """
    params.append(MAX_ROWS_PER_QUERY)

    conn = _attach()
    try:
        result = conn.execute(sql, tuple(params))
        rows = _rows_to_dicts(result)
        logger.info(
            "query_poll_data(range=%s..%s, source=%s) -> %d rows",
            start, end, source, len(rows),
        )
        return rows
    finally:
        conn.close()


# --- Events --------------------------------------------------------------


def query_events_in_window(
    date_range: tuple[str, str],
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert events_timeline-Eintraege fuer ein Zeitfenster (max. 50)."""
    start, end = date_range
    conditions = ["event_timestamp BETWEEN ? AND ?"]
    params: list[Any] = [start, end]
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)

    sql = f"""
        SELECT event_timestamp, event_type, event_category, description, impact_score
        FROM thesis.events_timeline
        WHERE {' AND '.join(conditions)}
        ORDER BY event_timestamp
        LIMIT ?
    """
    params.append(MAX_ROWS_PER_QUERY)

    conn = _attach()
    try:
        result = conn.execute(sql, tuple(params))
        rows = _rows_to_dicts(result)
        logger.info(
            "query_events_in_window(range=%s..%s, type=%s) -> %d rows",
            start, end, event_type, len(rows),
        )
        return rows
    finally:
        conn.close()


# --- Aggregated summary --------------------------------------------------


def generate_data_summary(
    table: str,
    date_range: tuple[str, str],
) -> dict[str, Any]:
    """Kleine Aggregation einer Tabelle im Zeitfenster — keine Rohdaten.

    Gibt COUNT, Zeitbereich und ggf. AVG zurueck. Keine Zeilen, nur
    Zusammenfassung — ideal fuer den Prompt-Kontext der Agenten.
    """
    allowed = {
        "polymarket_prices": ("price_timestamp", "price"),
        "whale_trades": ("price_timestamp", "amount_usd"),
        "sentiment_scores": ("timestamp", "sentiment"),
        "poll_forecasts": ("date", "probability"),
        "events_timeline": ("event_timestamp", "impact_score"),
    }
    if table not in allowed:
        raise ValueError(f"table {table!r} not in allowed set: {sorted(allowed)}")

    ts_col, val_col = allowed[table]
    start, end = date_range
    sql = f"""
        SELECT
            COUNT(*) AS row_count,
            MIN({ts_col}) AS first_ts,
            MAX({ts_col}) AS last_ts,
            AVG(CAST({val_col} AS DOUBLE)) AS avg_value,
            MIN(CAST({val_col} AS DOUBLE)) AS min_value,
            MAX(CAST({val_col} AS DOUBLE)) AS max_value
        FROM thesis.{table}
        WHERE {ts_col} BETWEEN ? AND ?
    """
    conn = _attach()
    try:
        result = conn.execute(sql, (start, end))
        row = result.fetchone()
        if row is None:
            return {"table": table, "row_count": 0}
        summary = {
            "table": table,
            "date_range": [start, end],
            "row_count": int(row[0] or 0),
            "first_ts": row[1],
            "last_ts": row[2],
            "avg_value": float(row[3]) if row[3] is not None else None,
            "min_value": float(row[4]) if row[4] is not None else None,
            "max_value": float(row[5]) if row[5] is not None else None,
        }
        logger.info(
            "generate_data_summary(table=%s, range=%s..%s) -> count=%d",
            table, start, end, summary["row_count"],
        )
        return summary
    finally:
        conn.close()


# --- Pre-computed summaries -----------------------------------------------


def get_precomputed_summary(metric_name: str) -> list[dict[str, Any]]:
    """Liest Summary-Zeilen aus analysis_summaries fuer eine Metrik (max. 50)."""
    sql = """
        SELECT table_name, metric_name, date_range_start, date_range_end,
               value_json, computed_at
        FROM thesis.analysis_summaries
        WHERE metric_name = ?
        ORDER BY computed_at DESC
        LIMIT ?
    """
    conn = _attach()
    try:
        result = conn.execute(sql, (metric_name, MAX_ROWS_PER_QUERY))
        rows = _rows_to_dicts(result)
        logger.info(
            "get_precomputed_summary(metric=%s) -> %d rows", metric_name, len(rows)
        )
        return rows
    finally:
        conn.close()
