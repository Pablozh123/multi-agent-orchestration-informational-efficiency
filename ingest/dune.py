"""Dune Analytics Ingest fuer Whale-Trades von Polymarket (CLOB auf Polygon).

Laedt grosse Trades (>= $10.000) von der Dune Analytics API, filtert bekannte
Market-Maker-Wallets heraus und speichert die bereinigten Whale-Trades in der
SQLite-Datenbank. Setzt das DUNE_API_KEY in der .env-Datei voraus.

Anforderungsabdeckung:
    DATA-05 — Whale-Transaktionen mit Market-Maker-Ausschluss fuer H3-Analyse.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

from ingest import DB_PATH, get_connection, to_utc_iso

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Replace with actual query ID from Dune web UI after developing and testing the query.
# See user_setup in 01-04-PLAN.md: https://dune.com/queries/new
DUNE_QUERY_ID: int = 0  # REPLACE with actual query ID from Dune web UI

WHALE_THRESHOLD_USD: float = 10_000.0

EXCLUSIONS_PATH: Path = Path("data/market_maker_exclusions.json")

# Dune Analytics REST API base URL
_DUNE_API_BASE = "https://api.dune.com/api/v1"


# ---------------------------------------------------------------------------
# Pure helper: market-maker filter
# ---------------------------------------------------------------------------

def filter_market_makers(
    rows: list[dict], exclusion_list: list[str]
) -> list[dict]:
    """Filtert Market-Maker-Wallets aus einer Liste von Trade-Zeilen.

    Entfernt alle Eintraege, deren wallet_address in der Ausschlussliste
    enthalten ist (case-insensitiv). Normalisiert wallet_address in den
    zurueckgegebenen Zeilen auf Kleinschreibung.

    Args:
        rows: Liste von Trade-Dicts mit dem Schluessel 'wallet_address'.
        exclusion_list: Liste bekannter Market-Maker-Wallet-Adressen (beliebige Gross-/Kleinschreibung).

    Returns:
        Gefilterte Liste ohne Market-Maker-Eintraege; wallet_address ist lowercase.
    """
    # Build a lowercase set for O(1) lookup
    exclusion_set = {addr.lower() for addr in exclusion_list}

    filtered: list[dict] = []
    for row in rows:
        # Normalize wallet address to lowercase before comparison and storage
        wallet_lower = row["wallet_address"].lower()
        if wallet_lower not in exclusion_set:
            # Return a copy with lowercase wallet to avoid mutating caller's data
            filtered_row = dict(row)
            filtered_row["wallet_address"] = wallet_lower
            filtered.append(filtered_row)
    return filtered


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _populate_market_maker_exclusions(conn: sqlite3.Connection) -> None:
    """Befuellt die market_maker_exclusions-Tabelle aus der statischen JSON-Datei.

    Laedt EXCLUSIONS_PATH und schreibt jeden Eintrag via INSERT OR IGNORE,
    sodass Duplikate bei wiederholten Laeufen ignoriert werden.

    Args:
        conn: Offene SQLite-Verbindung.
    """
    if not EXCLUSIONS_PATH.exists():
        return

    with EXCLUSIONS_PATH.open(encoding="utf-8") as fh:
        entries: list[dict] = json.load(fh)

    added_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    conn.executemany(
        """
        INSERT OR IGNORE INTO market_maker_exclusions
            (wallet_address, label, source, added_at)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                entry["wallet_address"].lower(),
                entry.get("label"),
                entry.get("source"),
                added_at,
            )
            for entry in entries
        ],
    )
    conn.commit()


def load_exclusions(db_path: Path = DB_PATH) -> list[str]:
    """Laedt alle Market-Maker-Wallet-Adressen aus der Datenbank.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei.

    Returns:
        Liste aller wallet_address-Werte aus market_maker_exclusions (lowercase).
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT wallet_address FROM market_maker_exclusions"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Dune API helpers
# ---------------------------------------------------------------------------

def _fetch_dune_results(api_key: str, query_id: int) -> list[dict]:
    """Ruft die Ergebnisse einer Dune-Query via REST API ab.

    Sendet einen GET-Request mit X-DUNE-API-KEY-Header und gibt die
    Zeilen aus dem Antwortobjekt zurueck.

    Args:
        api_key: Dune Analytics API Key.
        query_id: ID der vorkonfigurierten Dune-Query.

    Returns:
        Liste von Zeilen-Dicts aus dem Dune-Antwortobjekt.

    Raises:
        httpx.HTTPStatusError: Bei HTTP-Fehlern (4xx/5xx).
    """
    url = f"{_DUNE_API_BASE}/query/{query_id}/results"
    headers = {"X-DUNE-API-KEY": api_key}

    response = httpx.get(url, headers=headers, timeout=60.0)
    response.raise_for_status()

    data = response.json()
    return data.get("result", {}).get("rows", [])


def _normalize_direction(raw: str) -> str:
    """Normalisiert Handelsrichtungen auf 'BUY' oder 'SELL'.

    Dune-Queries koennen verschiedene Schreibweisen liefern
    ('buy', 'BUY', 'Buy', 'sell', 'SELL', 'Sell'). Die whale_trades-Tabelle
    erfordert exakt 'BUY' oder 'SELL' (CHECK-Constraint).

    Args:
        raw: Rohwert der direction/side-Spalte aus der Dune-Antwort.

    Returns:
        'BUY' oder 'SELL'.

    Raises:
        ValueError: Wenn raw keiner bekannten Richtung zugeordnet werden kann.
    """
    normalized = raw.strip().upper()
    if normalized in ("BUY", "B", "LONG"):
        return "BUY"
    if normalized in ("SELL", "S", "SHORT"):
        return "SELL"
    raise ValueError(f"Unbekannte Handelsrichtung: {raw!r}")


def _map_row(raw_row: dict) -> dict | None:
    """Mappt eine Dune-Ergebniszeile auf das whale_trades-Schema.

    Behandelt Abweichungen in den Spaltennamen verschiedener Dune-Queries
    (z.B. 'taker' vs. 'wallet', 'size_usd' vs. 'amount_usd', 'side' vs. 'direction').

    Args:
        raw_row: Einzelne Zeile aus der Dune-API-Antwort.

    Returns:
        Dict mit den Schluesseln des whale_trades-Schemas, oder None wenn
        Pflichtfelder fehlen oder der Trade unter dem Whale-Schwellenwert liegt.
    """
    # Handle column name variations for wallet address
    wallet_raw = (
        raw_row.get("taker")
        or raw_row.get("wallet")
        or raw_row.get("wallet_address")
        or ""
    )
    if not wallet_raw:
        return None

    # Handle column name variations for trade size
    amount_raw = (
        raw_row.get("amount_usd")
        or raw_row.get("size_usd")
        or raw_row.get("usd_amount")
        or 0.0
    )
    try:
        amount_usd = float(amount_raw)
    except (TypeError, ValueError):
        return None

    # Apply whale threshold filter
    if amount_usd < WHALE_THRESHOLD_USD:
        return None

    # Handle timestamp column variations
    ts_raw = (
        raw_row.get("block_time")
        or raw_row.get("timestamp")
        or raw_row.get("evt_block_time")
        or ""
    )
    # Convert to UTC ISO 8601 if it's a unix timestamp, or pass through if already ISO
    if ts_raw and isinstance(ts_raw, (int, float)):
        price_timestamp = to_utc_iso(int(ts_raw), source_format="unix_s")
    elif ts_raw:
        # Already a string timestamp — normalize by ensuring Z suffix
        price_timestamp = str(ts_raw).rstrip("Z") + "Z" if ts_raw else ""
    else:
        price_timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    # Handle direction/side column variations
    direction_raw = (
        raw_row.get("direction")
        or raw_row.get("side")
        or "BUY"
    )
    try:
        direction = _normalize_direction(str(direction_raw))
    except ValueError:
        return None

    return {
        "price_timestamp": price_timestamp,
        "tx_hash": raw_row.get("tx_hash") or raw_row.get("transaction_hash") or "",
        "wallet_address": wallet_raw.lower(),
        "market_id": raw_row.get("market_id") or raw_row.get("condition_id") or raw_row.get("outcome_id") or "",
        "direction": direction,
        "amount_usd": amount_usd,
        "token_id": raw_row.get("token_id") or raw_row.get("outcome_id") or "",
        "price_at_trade": float(raw_row.get("price", 0.0) or 0.0),
    }


# ---------------------------------------------------------------------------
# Main ingest function
# ---------------------------------------------------------------------------

def ingest_dune(db_path: Path = DB_PATH) -> int:
    """Laedt Whale-Trades von Dune Analytics und schreibt sie in die Datenbank.

    Ablauf:
    1. Laedt DUNE_API_KEY aus .env.
    2. Befuellt market_maker_exclusions-Tabelle aus der JSON-Datei.
    3. Ruft Dune API fuer DUNE_QUERY_ID ab.
    4. Mappt und filtert Rohdaten (Whale-Schwellenwert, Market-Maker-Ausschluss).
    5. Schreibt bereinigte Zeilen via INSERT OR IGNORE in whale_trades.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei. Standardmaessig data/thesis.db.

    Returns:
        Anzahl der neu eingefuegten Zeilen (0 bei Duplikaten durch INSERT OR IGNORE).

    Raises:
        EnvironmentError: Wenn DUNE_API_KEY nicht in .env gesetzt ist.
    """
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("DUNE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "DUNE_API_KEY ist nicht gesetzt. "
            "Bitte in .env eintragen: DUNE_API_KEY=your_key_here"
        )

    conn = get_connection(db_path)
    try:
        # Populate market maker exclusions from static JSON file
        _populate_market_maker_exclusions(conn)
        conn.commit()

        # Load exclusion list from DB for filtering
        exclusion_rows = conn.execute(
            "SELECT wallet_address FROM market_maker_exclusions"
        ).fetchall()
        exclusion_list = [row[0] for row in exclusion_rows]

        # Fetch raw data from Dune Analytics API
        raw_rows = _fetch_dune_results(api_key, DUNE_QUERY_ID)

        # Map to whale_trades schema and apply whale threshold filter
        mapped: list[dict] = []
        for raw_row in raw_rows:
            row = _map_row(raw_row)
            if row is not None:
                mapped.append(row)

        # Apply market-maker exclusion filter
        filtered = filter_market_makers(mapped, exclusion_list)

        # Insert filtered rows (INSERT OR IGNORE prevents duplicates via tx_hash UNIQUE)
        inserted = 0
        for row in filtered:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO whale_trades
                    (price_timestamp, tx_hash, wallet_address, market_id,
                     direction, amount_usd, token_id, price_at_trade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["price_timestamp"],
                    row["tx_hash"],
                    row["wallet_address"],
                    row["market_id"],
                    row["direction"],
                    row["amount_usd"],
                    row["token_id"],
                    row["price_at_trade"],
                ),
            )
            inserted += cursor.rowcount

        conn.commit()
        print(f"Whale-Trades eingefuegt: {inserted} (von {len(filtered)} gefilterten Zeilen)")
        return inserted

    finally:
        conn.close()


if __name__ == "__main__":
    ingest_dune()
