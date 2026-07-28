"""Kalshi-Mentions-Maerkte in die bestehende MarketRule uebersetzen.

Anders als bei Polymarket muss hier nichts aus dem Fragetext geraten
werden: Kalshi fuehrt das Zielwort strukturiert in `custom_strike.Word`
und regelt die zaehlenden Wortformen im Markttext selbst.

Drei Regelunterschiede, die diese Datei umsetzt (Belege in
`docs/project/KALSHI_MENTIONS_ANALYSE_2026-07-29.md` §2):

1. **Keine Zaehlschwellen.** Alle Mentions-Maerkte sind binaer, die
   Schwelle ist immer 1.
2. **Varianten sind deterministisch.** Laut `rules_secondary` zaehlen die
   exakte Phrase sowie Plural- und Genitivform, ausdruecklich KEINE
   Tempus-/Grammatikflexionen. `counter_engine.compile_patterns` deckt
   das Suffix `('s|s|')` bereits ab; hier werden nur die Plurale ergaenzt,
   die nicht durch ein angehaengtes "s" entstehen (Tax -> Taxes).
3. **Alternativen stehen mit " / " im Wortfeld** ("AI / Artificial
   Intelligence") und sind gleichwertige Treffer.

Aufgeloest wird auf Kalshi primaer per **Video**, nicht per Transkript.
Ein Transkriptfehler zaehlt dort also gegen uns — darum bleibt
`homophon_sensitiv` genauso scharf wie auf der Polymarket-Seite.
"""

from __future__ import annotations

import re

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule

# Meta-Markt jeder Kalshi-Mentions-Serie: fragt, ob das Event ueberhaupt
# stattfindet. Sein `rules_primary` ist ein Template-Artefakt ("If the
# Chair ... says Event does not qualify") und kein Wortmarkt.
NQE_SUFFIX = "-NQE"
NQE_WORT = "event does not qualify"

# Kalshi trennt gleichwertige Alternativen im Wortfeld mit Schraegstrich.
_ALTERNATIV_TRENNER = re.compile(r"\s*/\s*")

# Handelbar sind nur laufende Maerkte; alles andere (initialized, closed,
# settled, finalized, determined) wird uebersprungen.
AKTIVE_STATUS = frozenset({"active", "open"})


def _plural(wort: str) -> str | None:
    """Plural, falls er NICHT durch blosses Anhaengen von "s" entsteht.

    `compile_patterns` matcht "s" bereits als optionales Suffix — nur die
    Sonderfaelle brauchen eine eigene Variante. Unregelmaessige Plurale
    (leaf/leaves) werden bewusst nicht geraten: eine falsche Variante
    erzeugt Geistertreffer, eine fehlende nur einen verpassten Treffer.
    """
    w = wort.strip()
    if not w or not w[-1].isalpha():
        return None
    klein = w.lower()
    if klein.endswith(("s", "x", "z", "ch", "sh")):
        return w + "es"
    if klein.endswith("y") and len(w) > 1 and w[-2].lower() not in "aeiou":
        return w[:-1] + "ies"
    return None


def wort_varianten(wortfeld: str) -> list[str]:
    """Zaehlbare Varianten aus einem Kalshi-`custom_strike.Word`.

    Alternativen werden am Schraegstrich getrennt, je Alternative kommt
    bei Bedarf die Pluralform dazu. Reihenfolge bleibt erhalten,
    Duplikate fallen raus.
    """
    varianten: list[str] = []
    for teil in _ALTERNATIV_TRENNER.split(wortfeld or ""):
        teil = teil.strip()
        if not teil:
            continue
        for kandidat in (teil, _plural(teil)):
            if kandidat and kandidat not in varianten:
                varianten.append(kandidat)
    return varianten


def _wortfeld(markt: dict) -> str:
    """Zielwort des Markts; `custom_strike` hat Vorrang vor dem Untertitel."""
    strike = markt.get("custom_strike") or {}
    wort = strike.get("Word") or strike.get("word") or ""
    return (wort or markt.get("yes_sub_title") or "").strip()


def _ist_nqe(markt: dict, wortfeld: str) -> bool:
    ticker = str(markt.get("ticker") or "")
    return ticker.upper().endswith(NQE_SUFFIX) or wortfeld.lower() == NQE_WORT


def build_rule(markt: dict) -> MarketRule:
    """Leitet eine MarketRule aus einem Kalshi-Marktobjekt ab (oder SKIP).

    `market_id` und beide Token-Felder tragen den Kalshi-Ticker: anders als
    bei Polymarket gibt es hier kein Token je Ausgang, sondern einen Markt
    mit zwei Seiten (Order-Feld `side`: `bid` = YES, `ask` = NO).
    """
    ticker = str(markt.get("ticker") or "")
    titel = markt.get("title") or ""
    wortfeld = _wortfeld(markt)
    regeln = " ".join(
        str(markt.get(k) or "") for k in ("rules_primary", "rules_secondary")
    )

    def skip(grund: str) -> MarketRule:
        return MarketRule(
            market_id=ticker, slug=ticker, question=titel, varianten=[],
            schwelle=0, yes_token_id=ticker, no_token_id=ticker,
            homophon_sensitiv=False, status="skip", skip_grund=grund,
            resolution_hinweis=regeln[:400],
            extra={"venue": "kalshi", "wort": wortfeld,
                   "event_ticker": markt.get("event_ticker")},
        )

    if not ticker:
        return skip("kein_ticker")
    if _ist_nqe(markt, wortfeld):
        return skip("nqe_meta_markt_ohne_wortzaehlung")
    if not wortfeld:
        return skip("kein_zielwort")
    if str(markt.get("status") or "").lower() not in AKTIVE_STATUS:
        return skip(f"status_{markt.get('status')}")

    varianten = wort_varianten(wortfeld)
    if not varianten:
        return skip("keine_varianten_ableitbar")

    basis_begriffe = [t.strip() for t in _ALTERNATIV_TRENNER.split(wortfeld)]
    homophon = any(
        b.lower() in config.HOMOPHON_BEGRIFFE for b in basis_begriffe if b
    )
    boilerplate = any(
        b.lower() in config.BOILERPLATE_BEGRIFFE for b in basis_begriffe if b
    )

    return MarketRule(
        market_id=ticker,
        slug=ticker,
        question=titel,
        varianten=varianten,
        schwelle=1,  # Kalshi-Mentions sind ausnahmslos binaer
        yes_token_id=ticker,
        no_token_id=ticker,
        homophon_sensitiv=homophon,
        status="active",
        resolution_hinweis=regeln[:400],
        boilerplate_sensitiv=boilerplate,
        extra={
            "venue": "kalshi",
            "wort": wortfeld,
            "event_ticker": markt.get("event_ticker"),
            # Auf Kalshi entscheidet das Video, nicht das Transkript —
            # nachgelagerte NO-Logik muss das wissen (Phase 2).
            "aufloesung": "video_primaer",
            "close_time": markt.get("close_time"),
        },
    )


def build_rules(maerkte: list[dict]) -> list[MarketRule]:
    return [build_rule(m) for m in maerkte]


def aktive(regeln: list[MarketRule]) -> list[MarketRule]:
    return [r for r in regeln if r.status == "active"]
