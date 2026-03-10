"""FiveThirtyEight CSV-Ingest fuer die BA-Thesis Prognoseanalyse.

Laedt den oeffentlichen FiveThirtyEight-Datensatz fuer die US-Praesidentschaftswahl 2024
vom GitHub-Repository und schreibt die normierten Wahrscheinlichkeitswerte in die
poll_forecasts-Tabelle der Thesis-Datenbank.

Quell-URL: https://raw.githubusercontent.com/fivethirtyeight/data/master/polls/
           2024-averages/presidential_general_averages_2024-09-12_uncorrected.csv
"""
import io
import logging
import sqlite3
from pathlib import Path

import httpx
import pandas as pd

from ingest import DB_PATH, get_connection

logger = logging.getLogger(__name__)

# Primary CSV download URL — FiveThirtyEight 2024 presidential averages
_CSV_URL = (
    "https://raw.githubusercontent.com/fivethirtyeight/data/master/"
    "polls/2024-averages/presidential_general_averages_2024-09-12_uncorrected.csv"
)

# Candidate name aliases used in the CSV
_TRUMP_NAMES = frozenset(["donald trump", "trump", "d. trump"])
_HARRIS_NAMES = frozenset(["kamala harris", "harris", "k. harris"])

# Priority order for detecting the forecast probability column
_PROB_COLUMN_CANDIDATES = ["pct_estimate", "mean", "avg", "value"]


def parse_csv(csv_text: str) -> list[dict]:
    """Parst den FiveThirtyEight-CSV-Text und gibt normierte Zeilen zurueck.

    Liest die CSV-Daten mit pandas, erkennt automatisch die Wahrscheinlichkeitsspalte
    und normiert Prozentwerte (0–100) auf den Bereich [0.0, 1.0]. Filtert auf Trump-
    und Harris-Zeilen; dritte Kandidaten werden ignoriert.

    Args:
        csv_text: Rohtext des CSV-Downloads von GitHub.

    Returns:
        Liste von Dicts mit den Schluesseln: date (YYYY-MM-DD), source, candidate,
        probability, poll_type. Alle probability-Werte liegen in [0.0, 1.0].

    Raises:
        ValueError: Wenn keine bekannte Wahrscheinlichkeitsspalte gefunden wird.
        AssertionError: Wenn ein probability-Wert ausserhalb [0.0, 1.0] liegt.
    """
    df = pd.read_csv(io.StringIO(csv_text))

    # Normalize column names to lowercase for consistent matching
    df.columns = [c.strip().lower() for c in df.columns]

    # Detect the forecast probability column
    prob_col: str | None = None
    for candidate_col in _PROB_COLUMN_CANDIDATES:
        if candidate_col in df.columns:
            prob_col = candidate_col
            break

    if prob_col is None:
        raise ValueError(
            f"Keine Wahrscheinlichkeitsspalte gefunden. "
            f"Gesucht: {_PROB_COLUMN_CANDIDATES}. "
            f"Verfuegbare Spalten: {list(df.columns)}"
        )

    # Detect candidate name column ('candidate' or 'name')
    cand_col = "candidate" if "candidate" in df.columns else "name"

    rows: list[dict] = []
    for _, row in df.iterrows():
        raw_name = str(row[cand_col]).strip().lower()

        # Map to canonical candidate name — skip third-party candidates
        if raw_name in _TRUMP_NAMES:
            canonical = "trump"
        elif raw_name in _HARRIS_NAMES:
            canonical = "harris"
        else:
            continue

        # Normalize raw probability: divide by 100 if value appears to be a percentage
        raw_prob = float(row[prob_col])
        probability = raw_prob / 100.0 if raw_prob > 1.0 else raw_prob

        # Normalize date to YYYY-MM-DD string
        date_val = str(row["date"]).strip()
        # pandas may parse dates differently; ensure clean YYYY-MM-DD
        try:
            date_str = pd.to_datetime(date_val).strftime("%Y-%m-%d")
        except Exception:
            date_str = date_val[:10]  # fallback: take first 10 chars

        rows.append(
            {
                "date": date_str,
                "source": "fivethirtyeight",
                "candidate": canonical,
                "probability": probability,
                "poll_type": "model",
            }
        )

    # Invariant: all probabilities must be in [0.0, 1.0]
    assert all(
        0.0 <= r["probability"] <= 1.0 for r in rows
    ), "Normierungsfehler: probability-Wert ausserhalb [0.0, 1.0]"

    return rows


def ingest_fivethirtyeight(db_path: Path = DB_PATH) -> int:
    """Laedt den FiveThirtyEight-CSV und schreibt die Daten in poll_forecasts.

    Laedt den CSV-Datensatz von GitHub, parst ihn mit parse_csv(), protokolliert
    den Datumsbereich und schreibt die Zeilen idempotent (INSERT OR IGNORE) in
    die Datenbank. Gibt eine Warnung aus, wenn die Daten vor dem 1. Februar 2024
    beginnen.

    Args:
        db_path: Pfad zur SQLite-Datenbank. Standardmaessig data/thesis.db.

    Returns:
        Anzahl der erfolgreich eingefuegten Zeilen.
    """
    logger.info("Lade FiveThirtyEight-CSV von %s", _CSV_URL)

    response = httpx.get(_CSV_URL, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    rows = parse_csv(response.text)

    if not rows:
        logger.warning("FiveThirtyEight CSV ergab 0 Zeilen nach Filterung.")
        return 0

    # Log date coverage for diagnostics
    dates = sorted(r["date"] for r in rows)
    min_date, max_date = dates[0], dates[-1]
    logger.info(
        "FiveThirtyEight Datumsabdeckung: %s bis %s (%d Zeilen)",
        min_date,
        max_date,
        len(rows),
    )
    print(f"FiveThirtyEight: {len(rows)} Zeilen, {min_date} bis {max_date}")

    # Warn if coverage does not reach back to early 2024
    if min_date > "2024-02-01":
        logger.warning(
            "FiveThirtyEight CSV partial coverage — starting %s", min_date
        )

    conn = get_connection(db_path)
    inserted = 0
    try:
        for row in rows:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO poll_forecasts
                    (date, source, candidate, probability, poll_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["date"],
                    row["source"],
                    row["candidate"],
                    row["probability"],
                    row["poll_type"],
                ),
            )
            inserted += cursor.rowcount
        conn.commit()
        logger.info("FiveThirtyEight: %d Zeilen eingefuegt.", inserted)
    finally:
        conn.close()

    return inserted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = ingest_fivethirtyeight()
    print(f"Eingefuegt: {count} Zeilen")
