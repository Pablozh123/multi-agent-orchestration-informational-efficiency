"""GDELT DOC API Ingest-Skript fuer Sentiment-Scores der US-Wahl 2024.

Fragt die GDELT DOC API fuer jeden Tag von Januar bis November 2024 ab,
berechnet den durchschnittlichen Tone-Score und schreibt die Ergebnisse
in die sentiment_scores-Tabelle der SQLite-Datenbank.

Anforderungsabdeckung:
    DATA-06 — GDELT-Sentiment als Eingangssignal fuer den Sentiment-Agenten
"""
import sqlite3
import time
from pathlib import Path

import httpx
import pandas as pd
from tqdm import tqdm

from ingest import DB_PATH, get_connection

# GDELT DOC API endpoint (no API key required — open access)
GDELT_DOC_API: str = "https://api.gdeltproject.org/api/v2/doc/doc"

# Default keyword query for US election 2024 coverage
KEYWORD_QUERY: str = "election usa 2024 trump harris"

# Topic label written to sentiment_scores for all GDELT rows
TOPIC: str = "us_election_2024"


def parse_sentiment(rows: list[dict]) -> list[dict]:
    """Wandelt aggregierte GDELT-Tageszeilen in Sentiment-Score-Dicts um.

    Nimmt eine Liste von voraggregrierten GDELT-Tageseintraegen (wie sie von
    fetch_daily_sentiment zurueckgegeben werden) und gibt eine Liste von Dicts
    zurueck, die direkt in sentiment_scores eingefuegt werden koennen.

    Args:
        rows: Liste von Dicts mit den Schluesseln 'date' (YYYY-MM-DD),
              'tone' (float) und 'num_articles' (int).

    Returns:
        Liste von Dicts mit den Schluesseln timestamp, source, topic,
        sentiment, volume, raw_text_sample.
    """
    result: list[dict] = []
    for row in rows:
        # Format date as full UTC ISO 8601 timestamp at midnight
        ts = row["date"] + "T00:00:00.000000Z"
        result.append(
            {
                "timestamp": ts,
                "source": "gdelt",
                "topic": TOPIC,
                "sentiment": float(row["tone"]),
                "volume": int(row["num_articles"]),
                "raw_text_sample": None,
            }
        )
    return result


def fetch_daily_sentiment(
    date_str: str,
    keyword_query: str = KEYWORD_QUERY,
) -> dict:
    """Fragt die GDELT DOC API fuer einen einzelnen Tag ab und aggregiert die Tone-Werte.

    Baut eine Anfrage an den GDELT DOC API-Endpunkt mit einem Tageszeitfenster
    (00:00:00 bis 23:59:59 UTC) und berechnet den Durchschnitts-Tone aller
    zurueckgegebenen Artikel. Gibt bei leerer Antwort Nullwerte zurueck.

    Args:
        date_str: Datum im Format 'YYYY-MM-DD', z.B. '2024-03-15'.
        keyword_query: Suchbegriffe fuer die GDELT-Anfrage.

    Returns:
        Dict mit den Schluesseln 'date' (str), 'tone' (float) und
        'num_articles' (int).
    """
    # Build date-range parameters: one full day window
    date_compact = date_str.replace("-", "")
    params = {
        "query": keyword_query,
        "mode": "artlist",
        "format": "json",
        "STARTDATETIME": date_compact + "000000",
        "ENDDATETIME": date_compact + "235959",
        "maxrecords": "250",
    }

    try:
        response = httpx.get(GDELT_DOC_API, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        # Return zero-row entry on network or parse failure
        return {"date": date_str, "tone": 0.0, "num_articles": 0}

    articles = data.get("articles", []) or []
    if not articles:
        return {"date": date_str, "tone": 0.0, "num_articles": 0}

    # Average the tone values across all returned articles
    tones = [float(a.get("tone", 0.0)) for a in articles if a.get("tone") is not None]
    avg_tone = sum(tones) / len(tones) if tones else 0.0

    return {
        "date": date_str,
        "tone": avg_tone,
        "num_articles": len(articles),
    }


def ingest_gdelt(
    db_path: Path = DB_PATH,
    start: str = "2024-01-01",
    end: str = "2024-11-05",
) -> int:
    """Ingested taeglich aggregierte GDELT-Sentiment-Werte in die Datenbank.

    Iteriert ueber jeden Tag im angegebenen Zeitraum und prueft, ob bereits
    ein Eintrag fuer diesen Tag existiert (Idempotenz). Neue Tage werden
    einzeln von der GDELT DOC API abgefragt und in sentiment_scores
    gespeichert. Zwischen den API-Aufrufen wird 0.2 Sekunden gewartet,
    um Rate-Limiting zu vermeiden.

    Args:
        db_path: Pfad zur SQLite-Datenbankdatei.
        start: Startdatum des Ingestionszeitraums im Format 'YYYY-MM-DD'.
        end: Enddatum des Ingestionszeitraums im Format 'YYYY-MM-DD'.

    Returns:
        Anzahl der neu eingefuegten Zeilen.
    """
    conn: sqlite3.Connection = get_connection(db_path)
    inserted: int = 0

    # Generate all dates in the range (inclusive)
    date_range = pd.date_range(start=start, end=end, freq="D")

    with tqdm(total=len(date_range), desc="GDELT ingest", unit="day") as pbar:
        for dt in date_range:
            date_str = dt.strftime("%Y-%m-%d")
            ts = date_str + "T00:00:00.000000Z"

            # Skip if this day already has a GDELT row (idempotent runs)
            existing = conn.execute(
                "SELECT COUNT(*) FROM sentiment_scores WHERE timestamp=? AND source='gdelt'",
                (ts,),
            ).fetchone()[0]
            if existing > 0:
                pbar.update(1)
                continue

            # Fetch sentiment for this day from GDELT DOC API
            daily = fetch_daily_sentiment(date_str)
            parsed = parse_sentiment([daily])

            # Insert parsed row into sentiment_scores
            for row in parsed:
                conn.execute(
                    """INSERT OR IGNORE INTO sentiment_scores
                       (timestamp, source, topic, sentiment, volume, raw_text_sample)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        row["timestamp"],
                        row["source"],
                        row["topic"],
                        row["sentiment"],
                        row["volume"],
                        row["raw_text_sample"],
                    ),
                )
                inserted += 1

            conn.commit()
            pbar.update(1)

            # Respect GDELT's implicit rate limit
            time.sleep(0.2)

    conn.close()
    print(f"GDELT ingest complete: {inserted} rows inserted.")
    return inserted


if __name__ == "__main__":
    ingest_gdelt()
