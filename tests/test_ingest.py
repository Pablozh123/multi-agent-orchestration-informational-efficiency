"""Ingest-Verhaltenstests fuer alle fuenf Datenquellen.

Definiert das Verhaltenslastenheft fuer die Ingest-Module in Wave 1:
ingest/polymarket.py, ingest/fivethirtyeight.py, ingest/rcp.py,
ingest/dune.py, ingest/gdelt.py und ingest/events.py.

Alle Tests, die noch nicht implementierte Module importieren, werden
automatisch uebersprungen (pytest.importorskip). Das ermoeglicht einen
sauberen Exit-Code 0 in Wave 0, obwohl die Produktion noch nicht existiert.

Anforderungsabdeckung:
    DATA-01 — Polymarket: korrekte Zeilenanzahl und Zeitstempelformat
    DATA-02 — fetched_at >= price_timestamp (kein Lookahead-Bias)
    DATA-03 — Whale-Trades: Market-Maker-Filterung
    DATA-05 — GDELT: Sentiment-Parsing mit korrekten Schluesseln
    DATA-06 — FiveThirtyEight: CSV-Parsing mit Wahrscheinlichkeitsbereich
    DATA-07 — RCP: Prozent-zu-Wahrscheinlichkeits-Konvertierung
"""
import re
import textwrap
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Polymarket ingest tests
# ---------------------------------------------------------------------------

def test_polymarket_row_count(mock_polymarket_response: dict) -> None:
    """Prueft, dass parse_prices die korrekte Zeilenanzahl aus der API-Antwort extrahiert.

    Das Mock enthaelt 2 Preispunkte; parse_prices muss genau 2 Zeilen zurueckgeben.
    """
    polymarket = pytest.importorskip("ingest.polymarket")
    result: list[dict] = polymarket.parse_prices(
        mock_polymarket_response, market_id="presidential-2024", token_id="trump-wins"
    )
    assert len(result) == 2, (
        f"Erwartet 2 Zeilen, erhalten: {len(result)}"
    )


def test_no_lookahead_bias(mock_polymarket_response: dict) -> None:
    """Prueft, dass fetched_at immer >= price_timestamp ist (kein Lookahead-Bias).

    Ein fetched_at-Wert vor dem Beobachtungszeitpunkt wuerde die Analyse
    verfaelschen, da zukuenftige Informationen in historische Preise einfliessen
    wuerden (DATA-02).
    """
    polymarket = pytest.importorskip("ingest.polymarket")
    result: list[dict] = polymarket.parse_prices(
        mock_polymarket_response, market_id="presidential-2024", token_id="trump-wins"
    )
    for row in result:
        assert row["fetched_at"] >= row["price_timestamp"], (
            f"Lookahead-Bias erkannt: fetched_at={row['fetched_at']} "
            f"< price_timestamp={row['price_timestamp']}"
        )


@pytest.mark.parametrize("ts,expected_valid", [
    ("2024-01-01T00:00:00.000000Z", True),
    ("2024-11-05T18:30:59.123456Z", True),
    ("2024-01-01", False),
    ("2024-01-01T00:00:00", False),
    ("not-a-timestamp", False),
])
def test_price_timestamp_format(ts: str, expected_valid: bool) -> None:
    """Prueft das UTC-ISO-8601-Format von Zeitstempeln (parametrisiert).

    Gueltige Zeitstempel muessen dem Muster YYYY-MM-DDTHH:MM:SS.ffffffZ entsprechen.
    Ungueltige Formate wuerden in SQLite als Text gespeichert und spaetere
    Zeitreihenoperationen korrumpieren.
    """
    # Test the format checker directly — no ingest module needed
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
    is_valid = bool(re.match(pattern, ts))
    assert is_valid == expected_valid, (
        f"Zeitstempel '{ts}': erwartet valid={expected_valid}, erhalten valid={is_valid}"
    )


# ---------------------------------------------------------------------------
# FiveThirtyEight ingest tests
# ---------------------------------------------------------------------------

def test_fivethirtyeight_rows() -> None:
    """Prueft, dass parse_csv korrekte Datums- und Wahrscheinlichkeitswerte liefert.

    Alle geparsten Zeilen muessen ein YYYY-MM-DD-Datum und eine Wahrscheinlichkeit
    im Bereich [0.0, 1.0] haben. FiveThirtyEight liefert Prozentwerte (0-100),
    die normiert werden muessen.
    """
    fivethirtyeight = pytest.importorskip("ingest.fivethirtyeight")
    # Minimal CSV with required columns
    csv_text = textwrap.dedent("""\
        date,candidate,pct_estimate,source
        2024-10-01,Trump,53.2,FiveThirtyEight
        2024-10-01,Harris,45.8,FiveThirtyEight
    """)
    result: list[dict] = fivethirtyeight.parse_csv(csv_text)
    assert len(result) >= 1, "parse_csv muss mindestens eine Zeile zurueckgeben"
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for row in result:
        assert date_pattern.match(row["date"]), (
            f"Datum '{row['date']}' entspricht nicht YYYY-MM-DD"
        )
        assert 0.0 <= row["probability"] <= 1.0, (
            f"Wahrscheinlichkeit {row['probability']} ausserhalb [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# RCP ingest tests
# ---------------------------------------------------------------------------

def test_rcp_probability_range() -> None:
    """Prueft, dass poll_pct_to_probability einen Wert in (0.0, 1.0) zurueckgibt.

    Bei Trump 52%, Harris 47% muss die berechnete Wahrscheinlichkeit > 0.5 sein
    (Trump liegt vorne) und strikt zwischen 0 und 1 liegen.
    """
    rcp = pytest.importorskip("ingest.rcp")
    result: float = rcp.poll_pct_to_probability(trump_pct=52.0, harris_pct=47.0)
    assert 0.0 < result < 1.0, (
        f"Wahrscheinlichkeit {result} liegt ausserhalb (0.0, 1.0)"
    )
    assert result > 0.5, (
        f"Trump liegt mit 52% vorne — Wahrscheinlichkeit muss > 0.5 sein, erhalten: {result}"
    )


def test_rcp_symmetric() -> None:
    """Prueft, dass bei Gleichstand (50/50) die Wahrscheinlichkeit ~0.5 ergibt.

    Symmetrieeigenschaft der Normierungsfunktion: identische Umfragewerte
    muessen zu einer 50%-Wahrscheinlichkeit fuehren.
    """
    rcp = pytest.importorskip("ingest.rcp")
    result: float = rcp.poll_pct_to_probability(trump_pct=50.0, harris_pct=50.0)
    assert result == pytest.approx(0.5, abs=0.01), (
        f"Gleichstand 50/50 muss ~0.5 ergeben, erhalten: {result}"
    )


# ---------------------------------------------------------------------------
# Dune / whale ingest tests
# ---------------------------------------------------------------------------

def test_whale_trades_exclusion(mock_dune_response: list[dict]) -> None:
    """Prueft, dass filter_market_makers den Market-Maker-Wallet herausfiltert.

    Das Mock enthaelt '0xabc' (normal) und '0xdeadbeef' (Market Maker).
    Nach der Filterung darf nur '0xabc' verbleiben.
    """
    dune = pytest.importorskip("ingest.dune")
    result: list[dict] = dune.filter_market_makers(
        mock_dune_response, exclusion_list=["0xdeadbeef"]
    )
    assert len(result) == 1, (
        f"Erwartet 1 Zeile nach Filterung, erhalten: {len(result)}"
    )
    assert result[0]["wallet_address"] == "0xabc", (
        f"Falscher Wallet erhalten: {result[0]['wallet_address']}"
    )


def test_whale_address_lowercase(mock_dune_response: list[dict]) -> None:
    """Prueft, dass filter_market_makers Wallet-Adressen vor dem Vergleich normalisiert.

    Blockchain-Adressen muessen gemaess Konvention immer lowercase sein.
    Der Filter muss auch bei gemischter Gross-/Kleinschreibung korrekt funktionieren.
    """
    dune = pytest.importorskip("ingest.dune")
    # Pass exclusion list with mixed case — should still match lowercase wallet
    result: list[dict] = dune.filter_market_makers(
        mock_dune_response, exclusion_list=["0xDeAdBeEf"]
    )
    assert len(result) == 1, (
        "Gross-/Kleinschreibung in der Ausschlussliste darf kein Problem sein"
    )
    # All returned wallet addresses must be lowercase
    for row in result:
        assert row["wallet_address"] == row["wallet_address"].lower(), (
            f"Wallet-Adresse '{row['wallet_address']}' ist nicht lowercase"
        )


# ---------------------------------------------------------------------------
# GDELT sentiment ingest tests
# ---------------------------------------------------------------------------

def test_gdelt_sentiment_rows(mock_gdelt_response: list[dict]) -> None:
    """Prueft, dass parse_sentiment die erwarteten Schluessels zurueckgibt.

    Jede Ausgabezeile muss timestamp, source, topic und sentiment enthalten.
    Die source-Spalte muss 'gdelt' sein, um in der Datenbank korrekt
    attribuiert werden zu koennen.
    """
    gdelt = pytest.importorskip("ingest.gdelt")
    result: list[dict] = gdelt.parse_sentiment(mock_gdelt_response)
    assert len(result) >= 1, "parse_sentiment muss mindestens eine Zeile zurueckgeben"
    required_keys = {"timestamp", "source", "topic", "sentiment"}
    for row in result:
        missing = required_keys - set(row.keys())
        assert not missing, (
            f"Fehlende Schluessels in Sentiment-Zeile: {missing}"
        )
        assert row["source"] == "gdelt", (
            f"source muss 'gdelt' sein, erhalten: '{row['source']}'"
        )


# ---------------------------------------------------------------------------
# Events catalog tests
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=False, reason="ingest/events.py noch nicht implementiert")
def test_events_catalog_count() -> None:
    """Prueft, dass load_events mindestens 20 Ereignisse im Katalog enthaelt.

    Der Ereigniskatalog muss alle relevanten politischen Ereignisse der
    US-Wahl 2024 abdecken. Dieser Test wird gruenen, sobald events.py
    in Wave 1 implementiert wird.
    """
    from ingest import events  # type: ignore[import-not-found]
    result: list[Any] = events.load_events()
    assert len(result) >= 20, (
        f"Erwartet mindestens 20 Ereignisse, erhalten: {len(result)}"
    )
