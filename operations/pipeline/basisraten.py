"""Basisraten je Marktwort aus der Gamma-Serien-Historie.

Die woechentlichen Mention-Events einer Show haengen an einer Gamma-Serie
(All-In: series_id 11300). Aus den AUFGELOESTEN Wochen laesst sich je
Wort ablesen, wie oft es tatsaechlich fiel (Basisrate). Verwendung als
Zaehler-Misstrauen fuer die NO-Seite: zaehlt unser Transkript 0 bei
einem Wort, das historisch fast jede Woche faellt (anthropic: 16/16),
ist das eher unser Messfehler als echte Abwesenheit -> kein NO-Kauf
(decision.no_sperre). Netzfehler sind fail-safe: ohne Historie bleibt
das Verhalten unveraendert.
"""

from __future__ import annotations

import json
from pathlib import Path

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule


def wort_schluessel(slug: str) -> str:
    """Normalisiert einen Markt-Slug auf den Wort-Teil.

    "will-tension-be-said-during-...-20260713..." -> "tension";
    Or-Maerkte behalten ihre Form ("midterm-or-midterms"). Der Schluessel
    ist ueber die Wochen stabil, weil Polymarket dasselbe Slug-Schema
    nutzt.
    """
    kurz = slug
    if kurz.startswith("will-"):
        kurz = kurz[len("will-"):]
    return kurz.split("-be-said")[0]


def _aufloesung(market: dict) -> str | None:
    """'YES'/'NO' fuer aufgeloeste Maerkte, sonst None."""
    preise = market.get("outcomePrices")
    if isinstance(preise, str):
        try:
            preise = json.loads(preise)
        except json.JSONDecodeError:
            return None
    if not preise or len(preise) != 2:
        return None
    try:
        y = float(preise[0])
    except (TypeError, ValueError):
        return None
    if y >= 0.99:
        return "YES"
    if y <= 0.01:
        return "NO"
    return None


def historie_aus_events(events: list[dict]) -> dict[str, list[str]]:
    """Wort-Schluessel -> Liste der Aufloesungen ('YES'/'NO'), nur
    aufgeloeste Maerkte. Offene Wochen (auch das laufende Event) fallen
    dadurch automatisch heraus."""
    out: dict[str, list[str]] = {}
    for ev in events:
        for m in ev.get("markets", []):
            erg = _aufloesung(m)
            if erg is None:
                continue
            out.setdefault(wort_schluessel(m.get("slug", "")), []).append(erg)
    return out


def hole_serien_historie(
    serie_id: str, snapshot_pfad: Path | None = None
) -> dict[str, list[str]]:
    """Laedt alle Events der Serie von Gamma und baut die Historie.

    Schreibt die Roh-Events als Snapshot neben die Laufdaten
    (Nachvollziehbarkeit; Guardrail: dokumentierte, gecachte Quelle).
    """
    import httpx

    events: list[dict] = []
    offset = 0
    while True:
        r = httpx.get(
            "https://gamma-api.polymarket.com/events",
            params={"series_id": serie_id, "limit": 100, "offset": offset},
            headers=config.HTTP_HEADERS,
            timeout=30.0,
        )
        r.raise_for_status()
        batch = r.json()
        events.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
    pfad = snapshot_pfad or (config.LIVE_DIR / "basisraten_snapshot.json")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump({"serie_id": serie_id, "events": len(events),
                   "historie": historie_aus_events(events)}, f,
                  ensure_ascii=False, indent=1)
    return historie_aus_events(events)


def reichere_mit_basisraten(
    rules: list[MarketRule], historie: dict[str, list[str]]
) -> None:
    """Setzt basisrate/basis_n je Regel aus der Historie (in place)."""
    for r in rules:
        eintraege = historie.get(wort_schluessel(r.slug), [])
        r.basis_n = len(eintraege)
        r.basisrate = (
            sum(1 for e in eintraege if e == "YES") / len(eintraege)
            if eintraege else None
        )
