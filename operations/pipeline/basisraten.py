"""Basisraten je Marktwort und Schwelle aus der Gamma-Serien-Historie.

Die woechentlichen Mention-Events einer Show haengen an einer Gamma-Serie
(All-In: series_id 11300). Aus den AUFGELOESTEN Wochen laesst sich je
Wort ablesen, wie oft es tatsaechlich fiel (Basisrate). Verwendung als
Zaehler-Misstrauen fuer die NO-Seite: zaehlt unser Transkript 0 bei
einem Wort, das historisch fast jede Woche faellt (anthropic: 16/16),
ist das eher unser Messfehler als echte Abwesenheit -> kein NO-Kauf
(decision.no_sperre). Netzfehler sind fail-safe: ohne Historie bleibt
das Verhalten unveraendert.

Schluessel ist Wort PLUS Schwelle (seit 04.09.2026): Bracket-Maerkte
derselben Serie fuehren dasselbe Wort mit verschiedenen Schwellen (All-In
"AI" 35+/50+, JRE "People" 100+/200+) — verschiedene Ereignisse, die
vorher unter dem Slug-Wort zusammenliefen (Live-Snapshot allin_september4:
"ai" n=17 aus sechs Schwellen). Slugs ohne Schwelle behalten ihren
bisherigen Schluessel ("anthropic"); siehe basis_schluessel().
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule, parse_schwelle

# Schwelle im Slug: "...-be-said-50-times-during-..." (All-In, JRE) bzw.
# "...-say-<wort>-10-times-during-..." (MrBeast, Earnings). Nur Fallback
# ohne Fragetext — die Schwelle kommt wie in build_rule aus dem Fragetext
# (groupItemThreshold ist keine Schwelle, Lehre 24.07.).
_SLUG_SCHWELLE = re.compile(r"-(\d+)-times(?=-|$)")
_WORT_SCHWELLE_SUFFIX = re.compile(r"-\d+-times$")

# Versionsfeld von basisraten_snapshot.json. Snapshots OHNE Feld (bis
# 04.09.2026) fuehren Schluessel ohne Schwelle: "ai" = alle AI-Brackets
# gemischt. Ab 2 ist der Schluessel basis_schluessel() (Wort + Schwelle).
SNAPSHOT_SCHEMA = 2


def wort_schluessel(slug: str) -> str:
    """Normalisiert einen Markt-Slug auf den reinen Wort-Teil (ohne Schwelle).

    Drei Slug-Schemata der Mention-Serien:
    "will-tension-be-said-during-...-20260713..."               -> "tension"
    "will-ai-be-said-50-times-during-...-20260831"              -> "ai"
    "will-mrbeast-say-minecraft-during-his-next-...-<ts>"       -> "minecraft"
    "will-mrbeast-say-dollar-10-times-during-his-next-...-<ts>" -> "dollar"
    "will-trump-post-football-on-truth-social-this-week-<ts>"   -> "football"
    Or-Maerkte behalten ihre Form ("midterm-or-midterms"). Der Schluessel
    ist ueber die Wochen stabil, weil Polymarket je Serie dasselbe Schema
    nutzt; der Wochen-Timestamp muss dafuer abgeschnitten werden (sonst
    matcht keine Vorwoche — Live-Befund mrbeast_gaming 18.07.:
    mit_historie=0 trotz 3 aufgeloester Vorwochen). Die Schwelle gehoert
    nicht ins Wort, sondern in basis_schluessel().
    """
    kurz = slug
    if kurz.startswith("will-"):
        kurz = kurz[len("will-"):]
    wort = kurz
    if "-be-said" in kurz:
        wort = kurz.split("-be-said")[0]
    elif "-say-" in kurz and "-during" in kurz.split("-say-", 1)[1]:
        wort = kurz.split("-say-", 1)[1].split("-during")[0]
    elif "-post-" in kurz and "-on-truth-social" in kurz.split("-post-", 1)[1]:
        wort = kurz.split("-post-", 1)[1].split("-on-truth-social")[0]
    return _WORT_SCHWELLE_SUFFIX.sub("", wort)


def schwelle_aus_slug(slug: str) -> int:
    """Schwelle aus dem Slug ("...-be-said-50-times-..." -> 50), sonst 1."""
    treffer = _SLUG_SCHWELLE.search(slug)
    return int(treffer.group(1)) if treffer else 1


def basis_schluessel(slug: str, question: str | None = None) -> str:
    """Schluessel der Historie: Wort plus Schwelle.

    Schwelle 1 -> nur das Wort ("anthropic"): Slugs ohne Schwelle behalten
    damit ihren bisherigen Schluessel. Bracket-Maerkte werden getrennt:
    "ai-35-times" vs. "ai-50-times". Die Schwelle kommt aus dem Fragetext
    (parse_schwelle, dieselbe Quelle wie build_rule); ohne Fragetext aus
    dem Slug. Im "-say-"-Schema (MrBeast, Earnings) ergibt das denselben
    Schluessel wie bisher ("hundred-or-thousand-or-million-10-times").
    """
    schwelle = parse_schwelle(question) if question else schwelle_aus_slug(slug)
    wort = wort_schluessel(slug)
    if schwelle <= 1:
        return wort
    return f"{wort}-{schwelle}-times"


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
    """basis_schluessel -> Liste der Aufloesungen ('YES'/'NO'), nur
    aufgeloeste Maerkte. Offene Wochen (auch das laufende Event) fallen
    dadurch automatisch heraus."""
    out: dict[str, list[str]] = {}
    for ev in events:
        for m in ev.get("markets", []):
            erg = _aufloesung(m)
            if erg is None:
                continue
            key = basis_schluessel(m.get("slug", ""), m.get("question"))
            out.setdefault(key, []).append(erg)
    return out


def hole_serien_historie(
    serie_id: str, snapshot_pfad: Path | None = None
) -> dict[str, list[str]]:
    """Laedt alle Events der Serie von Gamma und baut die Historie.

    Schreibt die Historie als Snapshot neben die Laufdaten
    (Nachvollziehbarkeit; Guardrail: dokumentierte, gecachte Quelle).
    Das Feld "schema" (SNAPSHOT_SCHEMA) sagt, wie die Schluessel gebaut
    sind — Snapshots ohne das Feld stammen aus der Zeit ohne Schwelle.
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
    historie = historie_aus_events(events)
    pfad = snapshot_pfad or (config.LIVE_DIR / "basisraten_snapshot.json")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump({"schema": SNAPSHOT_SCHEMA, "serie_id": serie_id,
                   "events": len(events), "historie": historie}, f,
                  ensure_ascii=False, indent=1)
    return historie


def reichere_mit_basisraten(
    rules: list[MarketRule], historie: dict[str, list[str]]
) -> None:
    """Setzt basisrate/basis_n je Regel aus der Historie (in place).

    Fail-safe: ohne passenden Schluessel bleibt basisrate None und
    basis_n 0 — dann greift kein Veto (decision.no_sperre).
    """
    for r in rules:
        eintraege = historie.get(basis_schluessel(r.slug, r.question), [])
        r.basis_n = len(eintraege)
        r.basisrate = (
            sum(1 for e in eintraege if e == "YES") / len(eintraege)
            if eintraege else None
        )
