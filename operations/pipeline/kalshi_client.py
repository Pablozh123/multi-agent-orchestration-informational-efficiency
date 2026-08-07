"""Lesender Zugriff auf die oeffentliche Kalshi-Handels-API (trade-api/v2).

Phase 1 der Kalshi-Anbindung: nur Lesen, keine Authentifizierung, keine
Orders. Die Auth-Naht (`_auth_header`) ist vorbereitet, aber unbenutzt —
Signieren kommt erst mit `kalshi_execution.py` in Phase 3.

Belege zur API in `docs/project/KALSHI_MENTIONS_ANALYSE_2026-07-29.md` §4.
"""

from __future__ import annotations

import threading
import time

BASIS_URL = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_URL = "https://external-api.demo.kalshi.co/trade-api/v2"

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Ratelimit Basic-Stufe: 200 Read-Token/s, die meisten Requests kosten 10
# Token (~20 Requests/s). Wir fahren bewusst weit darunter — der Recorder
# soll neben dem Live-Bot laufen, ohne dessen Budget zu verbrauchen.
MIN_ABSTAND_S = 0.2

_drossel_lock = threading.Lock()
_letzter_ruf = [0.0]


def _drossle() -> None:
    """Mindestabstand zwischen zwei Requests einhalten (prozessweit)."""
    with _drossel_lock:
        wartezeit = MIN_ABSTAND_S - (time.monotonic() - _letzter_ruf[0])
        if wartezeit > 0:
            time.sleep(wartezeit)
        _letzter_ruf[0] = time.monotonic()


def _auth_header(methode: str, pfad: str) -> dict:
    """Platzhalter fuer Phase 3 (RSA-PSS ueber timestamp+METHODE+pfad).

    Bewusst leer: Phase 1 ruft ausschliesslich oeffentliche Endpunkte.
    """
    return {}


def hole(pfad: str, params: dict | None = None, basis: str = BASIS_URL) -> dict:
    """GET auf einen API-Pfad mit Retry und Drossel.

    `pfad` beginnt mit "/" und ist relativ zur Basis-URL.
    """
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(stop=stop_after_attempt(4), wait=wait_random_exponential(1, 12),
           reraise=True)
    def _abruf() -> dict:
        _drossle()
        resp = httpx.get(
            basis + pfad,
            params=params or {},
            headers={**HTTP_HEADERS, **_auth_header("GET", pfad)},
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()

    return _abruf()


def hole_serien(kategorie: str = "Mentions", basis: str = BASIS_URL) -> list[dict]:
    """Alle Serien einer Kategorie (z. B. 397 Serien unter 'Mentions')."""
    return hole("/series/", {"category": kategorie}, basis).get("series", [])


def hole_events(
    series_ticker: str, mit_maerkten: bool = False, basis: str = BASIS_URL
) -> list[dict]:
    """Events einer Serie, neueste zuerst (Kalshi-Reihenfolge)."""
    params = {"series_ticker": series_ticker, "limit": 50}
    if mit_maerkten:
        params["with_nested_markets"] = "true"
    return hole("/events", params, basis).get("events", [])


def hole_maerkte(event_ticker: str, basis: str = BASIS_URL) -> list[dict]:
    """Alle Maerkte eines Events inklusive Preis- und Volumenfeldern.

    Wichtig: die Preisfelder (`yes_bid_dollars` usw.) liefert nur dieser
    Endpunkt, NICHT `/markets/{ticker}` und nicht die verschachtelten
    Maerkte aus `/events?with_nested_markets=true`.
    """
    return hole("/markets", {"event_ticker": event_ticker, "limit": 200},
                basis).get("markets", [])


def hole_markt(ticker: str, basis: str = BASIS_URL) -> dict:
    """Einzelmarkt inklusive `rules_primary`/`rules_secondary`."""
    return hole(f"/markets/{ticker}", None, basis).get("market", {})


def hole_orderbuch(ticker: str, basis: str = BASIS_URL) -> dict:
    """Orderbuch eines Markts (Felder `orderbook_fp.yes_dollars`/`no_dollars`)."""
    return hole(f"/markets/{ticker}/orderbook", None, basis)


def zahl(wert) -> float | None:
    """Kalshi liefert Preise/Groessen als Dezimalstrings ('0.8200')."""
    if wert is None or wert == "":
        return None
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


def bestes_level(buch: dict, seite: str) -> tuple[float | None, float | None]:
    """Bester Preis und Groesse einer Buchseite ('yes' oder 'no').

    Kalshi listet je Seite aufsteigend `[preis, groesse]`; das beste
    (hoechste) Gebot steht am Ende. Beide Seiten sind Gebote — ein
    YES-Ask entsteht als 1 - bestes NO-Gebot.
    """
    levels = (buch.get("orderbook_fp") or buch.get("orderbook") or {}).get(
        f"{seite}_dollars"
    ) or []
    if not levels:
        return None, None
    preis, groesse = levels[-1][0], levels[-1][1]
    return zahl(preis), zahl(groesse)


def yes_quotes(buch: dict) -> tuple[float | None, float | None]:
    """(bester YES-Bid, bester YES-Ask) aus dem Zwei-Seiten-Buch.

    Der YES-Ask ist der Gegenwert des besten NO-Gebots: wer NO zu 0.19
    kauft, verkauft YES zu 0.81.
    """
    yes_bid, _ = bestes_level(buch, "yes")
    no_bid, _ = bestes_level(buch, "no")
    yes_ask = None if no_bid is None else round(1.0 - no_bid, 4)
    return yes_bid, yes_ask


def buch_als_polymarket(buch: dict, seite: str = "yes") -> dict:
    """Kalshi-Zwei-Seiten-Buch in das CLOB-Format {asks, bids} uebersetzen.

    Damit greifen `orderbook.ausfuehrbare_tiefe_usd` und die gesamte
    Budget-/Groessenlogik aus `execution.ExecutorBase` unveraendert auch
    auf Kalshi — statt sie ein zweites Mal zu schreiben.

    Kalshi fuehrt je Markt zwei Gebotsseiten. Ein YES-Ask ist das
    Spiegelbild eines NO-Gebots: wer NO zu 0.19 kauft, verkauft YES zu
    0.81. `seite="no"` dreht die Sicht um, damit NO-Kaeufe dieselbe
    Tiefenrechnung bekommen.
    """
    roh = (buch.get("orderbook_fp") or buch.get("orderbook") or {})
    gegen = "no" if seite == "yes" else "yes"

    def level(name: str) -> list[list]:
        return roh.get(f"{name}_dollars") or []

    asks = []
    for preis, groesse in level(gegen):
        p, g = zahl(preis), zahl(groesse)
        if p is None or g is None:
            continue
        asks.append({"price": round(1.0 - p, 4), "size": g})
    bids = []
    for preis, groesse in level(seite):
        p, g = zahl(preis), zahl(groesse)
        if p is None or g is None:
            continue
        bids.append({"price": p, "size": g})
    # CLOB-Konvention: Asks aufsteigend, Bids absteigend.
    asks.sort(key=lambda a: a["price"])
    bids.sort(key=lambda b: b["price"], reverse=True)
    return {"asks": asks, "bids": bids, "min_order_size": 1}


def gebuehr(preis: float, kontrakte: int = 1) -> float:
    """Kalshi-Taker-Gebuehr: ceil(0.07 * P * (1-P) * 100)/100 je Kontrakt.

    Maximum 1.75 Cent bei P = 0.50 — also genau im Zweifel-Fenster, aus
    dem alle bisherigen Fills der Polymarket-Strecke kamen. Maker zahlen
    ein Viertel davon; wir rechnen konservativ mit dem Taker-Satz.
    """
    import math

    je_kontrakt = math.ceil(0.07 * preis * (1.0 - preis) * 100.0) / 100.0
    return round(je_kontrakt * kontrakte, 4)
