"""Gemeinsame Hilfsfunktionen fuer alle Ingest-Skripte der BA-Thesis.

Stellt to_utc_iso() und get_connection() bereit, die von allen fuenf
Ingest-Skripten (polymarket, dune, gdelt, fivethirtyeight, rcp) importiert werden.
Alle Zeitstempel werden zu UTC ISO 8601 normalisiert.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Default database path used by all ingest scripts
DB_PATH = Path("data/thesis.db")


def to_utc_iso(value: int | str, source_format: str = "unix_ms") -> str:
    """Normalisiert Zeitstempel verschiedener Quellen zu UTC ISO 8601.

    Unterstuetzt drei Quellformate: Unix-Millisekunden (Polymarket CLOB API),
    Unix-Sekunden (generisch) und GDELT-Format (YYYYMMDDHHMMSS).
    Gibt immer einen String im Format 'YYYY-MM-DDTHH:MM:SS.ffffffZ' zurueck.

    Args:
        value: Der zu konvertierende Zeitstempel. Bei unix_ms und unix_s
               eine Ganzzahl; bei gdelt ein String.
        source_format: Quellformat des Zeitstempels. Erlaubte Werte:
                       'unix_ms' (Millisekunden seit Epoch),
                       'unix_s' (Sekunden seit Epoch),
                       'gdelt' (YYYYMMDDHHMMSS-String).

    Returns:
        UTC-Zeitstempel als ISO-8601-String, z.B. '2024-01-01T00:00:00.000000Z'.

    Raises:
        ValueError: Wenn source_format keinen der erlaubten Werte hat.
    """
    if source_format == "unix_ms":
        # Convert milliseconds to seconds, then create UTC datetime
        dt = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    elif source_format == "unix_s":
        # Convert seconds directly to UTC datetime
        dt = datetime.fromtimestamp(int(value), tz=timezone.utc)
    elif source_format == "gdelt":
        # Parse GDELT format string and attach UTC timezone
        dt = datetime.strptime(str(value), "%Y%m%d%H%M%S").replace(
            tzinfo=timezone.utc
        )
    else:
        raise ValueError(
            f"Unbekanntes source_format: {source_format!r}. "
            "Erlaubte Werte: 'unix_ms', 'unix_s', 'gdelt'."
        )

    # Always return microsecond precision with explicit Z suffix
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Oeffnet eine SQLite-Verbindung mit WAL-Modus und Busy-Timeout.

    Setzt journal_mode=WAL, busy_timeout=10000ms und synchronous=NORMAL,
    um gleichzeitige Lese- und Schreibzugriffe waehrend der Datenerhebung
    zuverlaessig zu unterstuetzen.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei. Standardmaessig data/thesis.db.

    Returns:
        Offene sqlite3.Connection mit gesetzten PRAGMAs.
    """
    # Open connection and configure WAL mode for concurrent access
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn
