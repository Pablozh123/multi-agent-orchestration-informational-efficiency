"""Polymarket CLOB API Ingest-Skript fuer historische Preisdaten.

Laedt historische Preisverlaeufe des US-Praesidentschaftswahl-2024-Marktes
von der Polymarket CLOB API und schreibt sie in die SQLite-Tabelle
polymarket_prices.

Lookahead-Bias-Schutz: price_timestamp enthaelt den Zeitpunkt der Beobachtung
(aus der API-Antwort), fetched_at den Zeitpunkt des API-Abrufs. Ein Datenpunkt
darf in der Analyse nur verwendet werden, wenn er zu einem Zeitpunkt abgerufen
wurde, der nach oder gleich dem Beobachtungszeitpunkt liegt.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ingest import DB_PATH, get_connection, to_utc_iso

# Module-level logger — no side effects at import time
logger = logging.getLogger(__name__)

# Polymarket CLOB API base URL
_CLOB_BASE_URL = "https://clob.polymarket.com"
# Gamma API base URL for market metadata
_GAMMA_BASE_URL = "https://gamma-api.polymarket.com"

# Known stable IDs for 2024 US Presidential Election market (resolved Nov 2024)
# Verified 2026-03-16 via CLOB /markets/{condition_id} endpoint
_CONDITION_ID = "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"
_YES_TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"


def parse_prices(
    response: dict,
    market_id: str,
    token_id: str,
    fetched_at: str | None = None,
) -> list[dict]:
    """Wandelt eine rohe CLOB-API-Antwort in eine Liste von Datenbankzeilen um.

    Extrahiert alle Preispunkte aus dem 'history'-Feld der Polymarket CLOB API
    und konvertiert die Unix-Millisekunden-Zeitstempel in UTC ISO 8601.
    Der Parameter fetched_at repraesentiert den Zeitpunkt des API-Abrufs und
    muss immer >= price_timestamp sein, um Lookahead-Bias zu vermeiden.

    Args:
        response: Rohe JSON-Antwort der CLOB API:
                  {"history": [{"t": <unix_ms>, "p": <price>}, ...]}
        market_id: Stabile Marktkennung (z.B. condition_id aus der Gamma API).
        token_id: Token-ID des YES-Outcome-Tokens.
        fetched_at: UTC ISO 8601 Zeitstempel des API-Abrufs. Wenn nicht
                    angegeben, wird der aktuelle UTC-Zeitpunkt verwendet.
                    Muss >= price_timestamp aller zurueckgegebenen Zeilen sein.

    Returns:
        Liste von Dicts mit den Schluesseln: price_timestamp, fetched_at,
        market_id, token_id, price, volume_24h, best_bid, best_ask.
        Leere Liste, wenn response['history'] fehlt oder leer ist.
    """
    # Use current UTC time if fetched_at is not provided
    if fetched_at is None:
        fetched_at = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        )

    history = response.get("history", [])
    if not history:
        return []

    rows: list[dict] = []
    for entry in history:
        # Convert Unix seconds to UTC ISO 8601 string (CLOB API returns seconds, not ms)
        price_timestamp = to_utc_iso(entry["t"], "unix_s")
        price = float(entry["p"])

        rows.append(
            {
                "price_timestamp": price_timestamp,
                "fetched_at": fetched_at,
                "market_id": market_id,
                "token_id": token_id,
                "price": price,
                # CLOB prices-history does not provide these fields
                "volume_24h": None,
                "best_bid": None,
                "best_ask": None,
            }
        )

    return rows


async def fetch_polymarket_prices(
    token_id: str,
    fidelity: int = 1440,
) -> dict:
    """Ruft historische Preisdaten fuer einen Token von der Polymarket CLOB API ab.

    Verwendet fidelity=1440 (taeglich) als Standard, da feiner aufgeloeste
    Daten fuer abgeschlossene Maerkte ein leeres history-Array zurueckgeben.

    Args:
        token_id: Polymarket CLOB Token-ID (YES-Outcome-Token).
        fidelity: Zeitaufloesungm in Minuten. 1440 = taeglich (Standard).
                  720 = halbstaeglich als Fallback fuer einige Maerkte.

    Returns:
        Rohe JSON-Antwort als Dict: {"history": [{"t": ..., "p": ...}, ...]}

    Raises:
        httpx.HTTPStatusError: Bei HTTP-Fehlerantworten (4xx/5xx).
    """
    url = f"{_CLOB_BASE_URL}/prices-history"
    params = {"market": token_id, "interval": "max", "fidelity": fidelity}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def resolve_token_id() -> tuple[str, str]:
    """Ermittelt die market_id und token_id des 2024-Praesidentschaftsmarkts.

    Fragt die Polymarket CLOB API ab (funktioniert auch fuer archivierte Maerkte,
    im Gegensatz zur Gamma API die nur aktive Maerkte liefert).
    Faellt auf bekannte Konstanten zurueck wenn die API nicht antwortet.

    Returns:
        Tupel (market_id, token_id), wobei market_id die condition_id und
        token_id die ID des YES-Outcome-Tokens ist.
    """
    url = f"{_CLOB_BASE_URL}/markets/{_CONDITION_ID}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            market_id: str = data.get("condition_id", _CONDITION_ID)
            for token in data.get("tokens", []):
                if token.get("outcome", "").upper() == "YES":
                    token_id: str = token["token_id"]
                    logger.info(
                        "Polymarket market resolved via CLOB: market_id=%s token_id=%s",
                        market_id,
                        token_id,
                    )
                    print(f"Resolved via CLOB: market_id={market_id}, token_id={token_id}")
                    return market_id, token_id

    # Hardcoded fallback — verified 2026-03-16
    logger.warning("CLOB market lookup failed, using hardcoded fallback constants.")
    print(f"Using hardcoded fallback: market_id={_CONDITION_ID}")
    return _CONDITION_ID, _YES_TOKEN_ID


async def ingest_polymarket(db_path: Path = DB_PATH) -> int:
    """Holt Polymarket-Preisdaten und schreibt sie idempotent in die SQLite-Datenbank.

    Workflow:
      1. Ermittle market_id und token_id dynamisch ueber die Gamma API.
      2. Rufe Preishistorie mit fidelity=1440 (taeglich) von der CLOB API ab.
      3. Bei leerer Antwort: Warnung loggen, Rohantwort zur Diagnose speichern.
      4. Parse und schreibe Zeilen mit INSERT OR IGNORE (idempotent).

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei. Standard: data/thesis.db.

    Returns:
        Anzahl der neu eingefuegten Zeilen (bei Duplikaten wird gezaehlt,
        wie viele tatsaechlich eingefuegt wurden).
    """
    # Resolve current market and token IDs dynamically
    market_id, token_id = await resolve_token_id()

    # Record fetch timestamp before API call to avoid lookahead bias
    fetched_at = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    )

    # Fetch price history from CLOB API
    response = await fetch_polymarket_prices(token_id)

    # Handle empty history (resolved market + wrong fidelity scenario)
    if not response.get("history"):
        logger.warning(
            "CLOB API returned empty history for token_id=%s. "
            "Saving debug response to data/polymarket_debug.json.",
            token_id,
        )
        debug_path = Path("data/polymarket_debug.json")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(
                {"token_id": token_id, "fidelity": 1440, "response": response},
                f,
                indent=2,
            )
        print(
            f"Warning: empty history. Debug response saved to {debug_path}"
        )
        return 0

    # Parse raw API response into database rows
    rows = parse_prices(response, market_id, token_id, fetched_at)

    # Write rows to SQLite with idempotent INSERT OR IGNORE
    conn: sqlite3.Connection = get_connection(db_path)
    inserted = 0
    try:
        for row in rows:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO polymarket_prices
                    (price_timestamp, fetched_at, market_id, token_id,
                     price, volume_24h, best_bid, best_ask)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["price_timestamp"],
                    row["fetched_at"],
                    row["market_id"],
                    row["token_id"],
                    row["price"],
                    row["volume_24h"],
                    row["best_bid"],
                    row["best_ask"],
                ),
            )
            inserted += cursor.rowcount
        conn.commit()
    finally:
        conn.close()

    print(f"Inserted {inserted} rows into polymarket_prices.")
    return inserted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(ingest_polymarket())
