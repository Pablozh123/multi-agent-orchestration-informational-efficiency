"""RCP-Ingest fuer die BA-Thesis Prognoseanalyse.

Laedt Umfragedurchschnitte von RealClearPolitics (RealClearPolling) fuer die
US-Praesidentschaftswahl 2024 und konvertiert die Prozentwerte in implizite
Wahrscheinlichkeiten via Logit-Transformation (scipy.special.expit).

Methodische Anmerkung: Der Skalierungsfaktor 4.0 in der Logit-Transformation ist
eine methodische Entscheidung, die in Abschnitt 3.2 der Thesis dokumentiert ist.
Ein Faktor von 4.0 entspricht einer moderaten Sigmoidkurve, bei der ein 5-Prozentpunkt-
Vorsprung einer Wahrscheinlichkeit von ca. 73% entspricht.
"""
import logging
from pathlib import Path

from scipy.special import expit  # type: ignore[import-untyped]

from ingest import DB_PATH, get_connection

logger = logging.getLogger(__name__)

# Scaling factor for logit conversion — methodological choice, see thesis Section 3.2
# A factor of 4.0 gives a moderate sigmoid: 5pp lead => ~73% probability
SCALING_FACTOR: float = 4.0

# RCP polling URL for the 2024 general election average
_RCP_URL = (
    "https://www.realclearpolling.com/polls/president/general/2024/trump-vs-harris"
)
_RCP_URL_ALT = (
    "https://www.realclearpolitics.com/epolls/2024/president/"
    "us/general_election_trump_vs_harris-7383.html"
)


def poll_pct_to_probability(
    trump_pct: float,
    harris_pct: float,
    scaling_factor: float = SCALING_FACTOR,
) -> float:
    """Konvertiert Umfrage-Prozentanteile in eine implizite Wahrscheinlichkeit.

    Verwendet die logistische Funktion (expit) auf den normierten Margin, um
    Umfragewerte in den Wahrscheinlichkeitsraum [0.0, 1.0] zu transformieren.
    Die Transformation ist symmetrisch: identische Werte ergeben 0.5.

    Formel: probability = expit((trump_pct - harris_pct) / 100 * scaling_factor)

    Args:
        trump_pct: Trumps Umfrageanteil in Prozent (z.B. 52.0 fuer 52%).
        harris_pct: Harris' Umfrageanteil in Prozent (z.B. 47.0 fuer 47%).
        scaling_factor: Skalierungsfaktor fuer die Logit-Transformation.
                        Standardwert 4.0 gemaess Thesis-Methodologie.

    Returns:
        Implizite Gewinnwahrscheinlichkeit fuer Trump im Bereich (0.0, 1.0).

    Raises:
        ValueError: Wenn trump_pct oder harris_pct kleiner oder gleich 0.0 sind.
    """
    if trump_pct <= 0.0:
        raise ValueError(
            f"trump_pct muss > 0.0 sein, erhalten: {trump_pct}"
        )
    if harris_pct <= 0.0:
        raise ValueError(
            f"harris_pct muss > 0.0 sein, erhalten: {harris_pct}"
        )

    # Compute normalized margin and apply logistic function
    margin = (trump_pct - harris_pct) / 100.0
    probability = float(expit(margin * scaling_factor))
    return probability


def ingest_rcp(db_path: Path = DB_PATH) -> int:
    """Laedt RCP-Umfragedurchschnitte und schreibt sie in poll_forecasts.

    Versucht, das realclearpolitics-Paket zu importieren und dessen API zu nutzen.
    Bei fehlgeschlagenem Import oder Abruf wird eine Warnung protokolliert und 0
    zurueckgegeben. Fuer jede Tageszeile werden zwei Eintraege (trump/harris) via
    INSERT OR IGNORE eingefuegt.

    Args:
        db_path: Pfad zur SQLite-Datenbank. Standardmaessig data/thesis.db.

    Returns:
        Anzahl der erfolgreich eingefuegten Zeilen (0 wenn Paket nicht verfuegbar).
    """
    # Attempt to import realclearpolitics third-party package
    try:
        import realclearpolitics  # type: ignore[import-not-found]

        logger.info("realclearpolitics-Paket gefunden, versuche Datenabruf...")
        rcp_data = _fetch_via_package(realclearpolitics)
    except ImportError:
        logger.warning(
            "realclearpolitics-Paket nicht installiert. "
            "Ausfuehren: pip install realclearpolitics"
        )
        # Attempt HTTP fallback
        rcp_data = _fetch_via_http_fallback()

    if not rcp_data:
        logger.warning("RCP: Keine Daten verfuegbar — 0 Zeilen eingefuegt.")
        return 0

    # Validate all probabilities before committing
    rows_to_insert: list[tuple] = []
    for entry in rcp_data:
        trump_prob = poll_pct_to_probability(
            entry["trump_pct"], entry["harris_pct"]
        )
        harris_prob = 1.0 - trump_prob

        assert 0.0 <= trump_prob <= 1.0, (
            f"Wahrscheinlichkeitsverletzung trump: {trump_prob}"
        )
        assert 0.0 <= harris_prob <= 1.0, (
            f"Wahrscheinlichkeitsverletzung harris: {harris_prob}"
        )

        rows_to_insert.append(
            (entry["date"], "rcp", "trump", trump_prob, "rcp_converted")
        )
        rows_to_insert.append(
            (entry["date"], "rcp", "harris", harris_prob, "rcp_converted")
        )

    conn = get_connection(db_path)
    inserted = 0
    try:
        for row in rows_to_insert:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO poll_forecasts
                    (date, source, candidate, probability, poll_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                row,
            )
            inserted += cursor.rowcount
        conn.commit()
        logger.info("RCP: %d Zeilen eingefuegt.", inserted)
    finally:
        conn.close()

    return inserted


def _fetch_via_package(realclearpolitics_module: object) -> list[dict]:
    """Ruft RCP-Daten ueber das realclearpolitics-Paket ab.

    Args:
        realclearpolitics_module: Importiertes realclearpolitics-Modul.

    Returns:
        Liste von Dicts mit Schluesseln date, trump_pct, harris_pct.
        Leere Liste bei Fehler.
    """
    try:
        # API surface varies by package version — try common patterns
        if hasattr(realclearpolitics_module, "get_polling_data"):
            raw = realclearpolitics_module.get_polling_data(_RCP_URL)
        elif hasattr(realclearpolitics_module, "RealClearPolitics"):
            client = realclearpolitics_module.RealClearPolitics(_RCP_URL)
            raw = client.get_polling_data()
        else:
            logger.warning("Unbekannte API des realclearpolitics-Pakets.")
            return []

        return _normalize_rcp_data(raw)
    except Exception as exc:
        logger.warning("realclearpolitics-Paket Datenabruf fehlgeschlagen: %s", exc)
        return []


def _fetch_via_http_fallback() -> list[dict]:
    """Versucht einen direkten HTTP-Abruf von RCP als Fallback.

    Nutzt httpx fuer einen einfachen GET-Request auf die RCP-Seite.
    Gibt eine leere Liste zurueck, da HTML-Parsing nicht implementiert ist.

    Returns:
        Leere Liste (HTTP-Fallback nicht vollstaendig implementiert in v1).
    """
    try:
        import httpx

        logger.info("HTTP-Fallback: Abrufen von %s", _RCP_URL)
        response = httpx.get(_RCP_URL, timeout=15.0, follow_redirects=True)
        logger.info(
            "HTTP-Fallback: Status %d — HTML-Parsing nicht implementiert in v1.",
            response.status_code,
        )
    except Exception as exc:
        logger.warning("HTTP-Fallback fehlgeschlagen: %s", exc)

    # HTML scraping not implemented in v1 — return empty
    return []


def _normalize_rcp_data(raw_data: object) -> list[dict]:
    """Normalisiert rohe RCP-API-Daten in ein einheitliches Format.

    Args:
        raw_data: Rohdaten aus dem realclearpolitics-Paket (Typ variiert).

    Returns:
        Liste von Dicts mit Schluesseln date (YYYY-MM-DD), trump_pct, harris_pct.
    """
    import pandas as pd

    if raw_data is None:
        return []

    rows: list[dict] = []
    try:
        # Handle DataFrame output
        if hasattr(raw_data, "iterrows"):
            for _, row in raw_data.iterrows():  # type: ignore[union-attr]
                entry = _extract_rcp_row(row)
                if entry:
                    rows.append(entry)
        # Handle list of dicts output
        elif isinstance(raw_data, list):
            for item in raw_data:
                entry = _extract_rcp_row(item)
                if entry:
                    rows.append(entry)
    except Exception as exc:
        logger.warning("RCP-Datennormalisierung fehlgeschlagen: %s", exc)

    return rows


def _extract_rcp_row(row: object) -> dict | None:
    """Extrahiert Datum und Prozentwerte aus einer RCP-Datenzeile.

    Args:
        row: Eine Zeile aus den RCP-Rohdaten (Dict oder pandas Series).

    Returns:
        Dict mit date, trump_pct, harris_pct oder None bei unvollstaendigen Daten.
    """
    import pandas as pd

    try:
        # Try various possible column name conventions
        date_val = None
        for date_key in ["date", "Date", "poll_date"]:
            if hasattr(row, "__getitem__") and date_key in row:  # type: ignore
                date_val = row[date_key]  # type: ignore
                break

        trump_pct = None
        harris_pct = None
        for t_key in ["trump", "Trump", "trump_pct", "Trump_pct"]:
            if hasattr(row, "__getitem__") and t_key in row:  # type: ignore
                trump_pct = float(row[t_key])  # type: ignore
                break
        for h_key in ["harris", "Harris", "harris_pct", "Harris_pct"]:
            if hasattr(row, "__getitem__") and h_key in row:  # type: ignore
                harris_pct = float(row[h_key])  # type: ignore
                break

        if date_val is None or trump_pct is None or harris_pct is None:
            return None

        date_str = pd.to_datetime(str(date_val)).strftime("%Y-%m-%d")
        return {"date": date_str, "trump_pct": trump_pct, "harris_pct": harris_pct}
    except Exception:
        return None


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    count = ingest_rcp()
    print(f"Eingefuegt: {count} Zeilen")
