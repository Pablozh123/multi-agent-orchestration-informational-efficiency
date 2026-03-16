"""Ereigniskatalog-Ingest fuer die BA-Thesis Ereignisstudie.

Laedt den manuell kuratierten Ereigniskatalog (data/events_catalog.json) und
schreibt ihn in die events_timeline-Tabelle der SQLite-Datenbank.

Zweck: Der Ereigniskatalog ist die Referenzmenge fuer H2 (Reaktionsgeschwindigkeit)
und H3 (Whale-Timing) der Analyse. Alle Ereignisse haben exakte UTC-Zeitstempel
und Kategorie-Labels, bevor Ereignisfenster berechnet werden koennen.

Keine API-Aufrufe — rein statischer JSON-Loader.
"""
import json
import re
import sqlite3
from pathlib import Path

from ingest import DB_PATH, get_connection

# Path to the curated events catalog JSON file
CATALOG_PATH: Path = Path("data/events_catalog.json")

# Required fields for each event entry
_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"event_timestamp", "event_type", "event_category", "description"}
)

# UTC ISO 8601 timestamp pattern: YYYY-MM-DDTHH:MM:SS.ffffffZ
_TIMESTAMP_PATTERN: re.Pattern[str] = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
)


def load_events(catalog_path: Path = CATALOG_PATH) -> list[dict]:
    """Laedt und validiert den Ereigniskatalog aus einer JSON-Datei.

    Liest events_catalog.json, prueft jeden Eintrag auf Vollstaendigkeit und
    korrektes Zeitstempelformat und gibt eine validierte Liste zurueck.
    Mindestens 20 Ereignisse muessen enthalten sein.

    Args:
        catalog_path: Pfad zur JSON-Katalogdatei. Standardmaessig
                      data/events_catalog.json.

    Returns:
        Liste von validierten Event-Dicts mit mindestens den Schluesseln
        event_timestamp, event_type, event_category und description.

    Raises:
        ValueError: Wenn ein Eintrag fehlende Pflichtfelder hat oder der
                    event_timestamp kein gueltiges UTC-ISO-8601-Format hat.
        AssertionError: Wenn der Katalog weniger als 20 Ereignisse enthaelt.
    """
    # Load raw JSON from disk
    with open(catalog_path, encoding="utf-8") as fh:
        events: list[dict] = json.load(fh)

    # Validate each event entry
    for i, event in enumerate(events):
        missing = _REQUIRED_FIELDS - set(event.keys())
        if missing:
            raise ValueError(
                f"Ereignis {i} fehlt Pflichtfelder: {missing}"
            )

        ts = event["event_timestamp"]
        if not _TIMESTAMP_PATTERN.match(ts):
            raise ValueError(
                f"Ereignis {i} hat ungueliges Zeitstempelformat: {ts!r}. "
                "Erwartet: YYYY-MM-DDTHH:MM:SS.ffffffZ"
            )

    # Ensure minimum event count for analysis completeness
    assert len(events) >= 20, (
        f"Katalog enthaelt nur {len(events)} Ereignisse, mindestens 20 benoetigt."
    )

    return events


def ingest_events(db_path: Path = DB_PATH) -> int:
    """Laedt den Ereigniskatalog und schreibt ihn in die events_timeline-Tabelle.

    Verwendet INSERT OR IGNORE, damit wiederholte Ausfuehrungen keine Duplikate
    erzeugen. Gibt die Anzahl der tatsaechlich eingefuegten Zeilen zurueck.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei. Standardmaessig data/thesis.db.

    Returns:
        Anzahl der in events_timeline eingefuegten Zeilen.
    """
    events = load_events()
    conn: sqlite3.Connection = get_connection(db_path)

    inserted = 0
    with conn:
        for event in events:
            # Check for existing row by (event_timestamp, event_type) to ensure idempotency.
            # events_timeline has no UNIQUE constraint, so we guard against duplicates manually.
            existing = conn.execute(
                "SELECT COUNT(*) FROM events_timeline WHERE event_timestamp = ? AND event_type = ?",
                (event["event_timestamp"], event["event_type"]),
            ).fetchone()[0]
            if existing > 0:
                # Skip — already ingested in a previous run
                continue

            cursor = conn.execute(
                """
                INSERT INTO events_timeline
                    (event_timestamp, event_type, event_category, description, impact_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event["event_timestamp"],
                    event["event_type"],
                    event["event_category"],
                    event["description"],
                    event.get("impact_score"),
                ),
            )
            inserted += cursor.rowcount

    conn.close()
    return inserted


if __name__ == "__main__":
    print(f"Inserted {ingest_events()} events")
