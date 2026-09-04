"""Basisraten wiederkehrender Mention-Serien aus aufgeloesten Polymarket-Events.

Hintergrund (Recherche 27.08.2026, T2/T3, und Curtis-E6-Thesentest 04.09.):
Die wiederkehrenden Wortmaerkte der Podcast- und TV-Serien ("Will 'Software'
be said during the next All-In Podcast?") werden von den Market Makern bei
der Anlage mit generischen Prioren gequotet. Die eigene Historie derselben
Serie ist der bessere Prior — aber unsere Archivdateien unter
`data/raw/live_runs/resolutions_*.json` decken nur die Wochen ab, in denen
ein Bot lief (JRE 4, All-In 6). Die Gamma-API liefert je Serie bis zu 50
geschlossene Events mit aufgeloesten Outcomes (JRE 32, All-In 31 Wochen,
Stand 04.09.2026) — daraus rechnet dieses Modul die YES-Quote je
(Wort, Schwelle) und stellt sie den Quotes des aktuell offenen Events
gegenueber.

Was das Modul NICHT ist: kein Modell, kein Order-Pfad. Die Klassifikation
("YES-Kandidat", "NO-Kandidat", "fair") ist eine dokumentierte
Screening-Heuristik auf der Laplace-geglaetteten Quote; die
Wahrscheinlichkeiten sind Basisraten mit kleinem n, keine kalibrierten
Prognosen. Gast-, Plot- und Rezenz-Effekte (Curtis E6: Leprechaun 4/5 ->
NO, weil der Running Gag in E5/E6 fehlte) bleiben Sache der Autorin —
deshalb wird neben der Gesamtquote immer die Quote der letzten drei
Ereignisse ausgewiesen.

Abgrenzung zu `operations.pipeline.basisraten` (Bot-Veto seit PR #61): Das
Pipeline-Modul laedt dieselbe Serien-Historie fuer die Laufzeit des Bots
und schluesselt seit 04.09.2026 ebenfalls nach Wort und Schwelle (aus dem
Fragetext, Slug als Fallback; davor fielen AI 35+ und AI 50+ zusammen) —
aber ohne Rezenz und ohne Glaettung. Dieses Analyse-Modul ist das
Forschungs- und Screening-Werkzeug VOR dem Drop: Laplace-Glaettung,
letzte-3-Quote, Vergleich mit den Quotes des offenen Events, JSON-Export
fuer die Doku.

Guardrails: read-only, hoechstens 50 Events je Abfrage, Ausgabe je Block
begrenzt, keine Rohtabellen in Prompts.

Aufruf:

    python -m operations.analysis.mention_basisraten --serie 11275 --offen 961501
    python -m operations.analysis.mention_basisraten --serie 11300 --serie 12413 \
        --json data/results/mention_basisraten_2026-09-04.json

Bekannte Serien (Gamma series_id, Stand 04.09.2026): 11275 Rogan Mentions,
11300 All-In Podcast, 12413 President Curtis Mentions, 10659 Leavitt Next
Briefing (wechselnde Sprecher!), 12076 Elon-Post-Woche.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

GAMMA = "https://gamma-api.polymarket.com"
UA = {"User-Agent": "ba-thesis mention_basisraten (read-only)"}

# Guardrail: hoechstens 50 Zeilen je Abfrage (AGENTS.md / CLAUDE.md).
MAX_EVENTS_JE_ABFRAGE = 50

# Screening-Schwellen der Klassifikation (Heuristik, siehe Modul-Doku).
TAKER_EDGE_MIN = 0.15   # Laplace-Quote minus Ask
MAKER_EDGE_MIN = 0.25   # Laplace-Quote minus Bid, nur bei Quote >= MAKER_MIN_QUOTE
MAKER_MIN_QUOTE = 0.60
NO_EDGE_MIN = 0.15      # Bid minus Laplace-Quote, nur bei Quote <= NO_MAX_QUOTE
NO_MAX_QUOTE = 0.50

# Aufgeloest heisst: Outcome-Preis am Rand. Alles dazwischen ist unklar.
AUFGELOEST_YES_MIN = 0.9
AUFGELOEST_NO_MAX = 0.1

# Gerade und typografische Anfuehrungszeichen (wie market_rules._ZITAT).
_ZITAT = re.compile(r"[\"“”‘’]([^\"“”‘’]+)[\"“”‘’]")
_SCHWELLE = re.compile(r"(\d+)\+")

Lader = Callable[[str], object]


@dataclass(frozen=True)
class Schluessel:
    """Ein Wortmarkt der Serie: zitierte Terme (durch '/' verbunden) + Schwelle."""

    wort: str
    schwelle: int


@dataclass
class Beobachtung:
    event_id: str
    event_titel: str
    ende: str
    frage: str
    outcome: bool


@dataclass
class Basisrate:
    wort: str
    schwelle: int
    n: int
    yes: int
    quote: float
    laplace: float
    letzte3_yes: int
    letzte3_n: int
    historie: list[str]


# ----------------------------------------------------------------- Parsing

def parse_frage(frage: str) -> Schluessel | None:
    """'Will "Hundred" or "Thousand" be said 10+ times ...' -> hundred/thousand, 10.

    Fragen ohne zitierten Term (z. B. "Will no episode air?") sind
    Meta-Maerkte und liefern None.
    """
    terme = [t.strip().lower() for t in _ZITAT.findall(frage or "")]
    if not terme:
        return None
    m = _SCHWELLE.search(frage)
    return Schluessel("/".join(terme), int(m.group(1)) if m else 1)


def _als_liste(wert) -> list:
    if isinstance(wert, str):
        try:
            wert = json.loads(wert)
        except json.JSONDecodeError:
            return []
    return list(wert or [])


def outcome_aus_markt(markt: dict) -> bool | None:
    """YES/NO eines geschlossenen Marktes aus `outcomePrices`, sonst None.

    Die Reihenfolge der Preise folgt `outcomes` (meist ["Yes", "No"], aber
    nicht garantiert), deshalb wird der Index von "Yes" gesucht.
    """
    if not markt.get("closed"):
        return None
    preise = _als_liste(markt.get("outcomePrices"))
    outcomes = [str(o).lower() for o in _als_liste(markt.get("outcomes"))]
    if not preise:
        return None
    idx = outcomes.index("yes") if "yes" in outcomes else 0
    try:
        p = float(preise[idx])
    except (IndexError, TypeError, ValueError):
        return None
    if p >= AUFGELOEST_YES_MIN:
        return True
    if p <= AUFGELOEST_NO_MAX:
        return False
    return None


# ------------------------------------------------------------- Aggregation

def sammle_beobachtungen(events: list[dict]) -> dict[Schluessel, list[Beobachtung]]:
    """Alle aufgeloesten Wortmaerkte der Events, gruppiert nach Schluessel."""
    beob: dict[Schluessel, list[Beobachtung]] = {}
    for ev in events:
        for m in ev.get("markets") or []:
            key = parse_frage(m.get("question") or "")
            if key is None:
                continue
            outcome = outcome_aus_markt(m)
            if outcome is None:
                continue
            beob.setdefault(key, []).append(Beobachtung(
                event_id=str(ev.get("id")),
                event_titel=ev.get("title") or "",
                ende=(ev.get("endDate") or "")[:10],
                frage=m.get("question") or "",
                outcome=outcome,
            ))
    return beob


def laplace(yes: int, n: int) -> float:
    return (yes + 1) / (n + 2)


def basisraten(beob: dict[Schluessel, list[Beobachtung]]) -> list[Basisrate]:
    zeilen: list[Basisrate] = []
    for key, liste in beob.items():
        liste = sorted(liste, key=lambda b: b.ende)
        n = len(liste)
        yes = sum(1 for b in liste if b.outcome)
        letzte3 = liste[-3:]
        zeilen.append(Basisrate(
            wort=key.wort, schwelle=key.schwelle, n=n, yes=yes,
            quote=round(yes / n, 3), laplace=round(laplace(yes, n), 3),
            letzte3_yes=sum(1 for b in letzte3 if b.outcome), letzte3_n=len(letzte3),
            historie=[f"{b.ende}:{'Y' if b.outcome else 'N'}" for b in liste],
        ))
    zeilen.sort(key=lambda z: (-z.n, z.wort, z.schwelle))
    return zeilen


# -------------------------------------------------------------- Vergleich

def klassifiziere(rate: Basisrate, bid: float | None, ask: float | None) -> str:
    """Screening-Label gegen die aktuellen Quotes (Heuristik, siehe Doku)."""
    if bid is None or ask is None:
        return "keine Quotes"
    p = rate.laplace
    if p - ask >= TAKER_EDGE_MIN:
        return "YES-Kandidat (Taker)"
    if p >= MAKER_MIN_QUOTE and p - bid >= MAKER_EDGE_MIN:
        return "YES-Kandidat (Maker-Bid)"
    if p <= NO_MAX_QUOTE and bid - p >= NO_EDGE_MIN:
        return "NO-Kandidat (Maker)"
    return "fair"


def _preis(wert) -> float | None:
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


def vergleiche(raten: list[Basisrate], offenes_event: dict) -> list[dict]:
    """Quotes des offenen Events gegen die Basisraten der Serie."""
    index = {(r.wort, r.schwelle): r for r in raten}
    zeilen = []
    for m in offenes_event.get("markets") or []:
        frage = m.get("question") or ""
        key = parse_frage(frage)
        bid, ask = _preis(m.get("bestBid")), _preis(m.get("bestAsk"))
        rate = index.get((key.wort, key.schwelle)) if key else None
        zeilen.append({
            "frage": frage,
            "bid": bid,
            "ask": ask,
            "n": rate.n if rate else 0,
            "yes": rate.yes if rate else 0,
            "laplace": rate.laplace if rate else None,
            "letzte3": f"{rate.letzte3_yes}/{rate.letzte3_n}" if rate else "-",
            "label": klassifiziere(rate, bid, ask) if rate else "keine Historie",
        })
    return zeilen


# ------------------------------------------------------------------ Laden

def hole_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def lade_serie(serie_id: int | str, lader: Lader = hole_json,
               limit: int = MAX_EVENTS_JE_ABFRAGE) -> list[dict]:
    limit = min(int(limit), MAX_EVENTS_JE_ABFRAGE)
    url = GAMMA + "/events?" + urllib.parse.urlencode({
        "series_id": str(serie_id), "closed": "true", "limit": limit,
        "order": "endDate", "ascending": "false"})
    return list(lader(url) or [])


def lade_event(event_id: int | str, lader: Lader = hole_json) -> dict:
    return dict(lader(f"{GAMMA}/events/{event_id}") or {})


# -------------------------------------------------------------------- CLI

def _tabelle_basisraten(raten: list[Basisrate], max_zeilen: int = 40) -> str:
    kopf = f"{'Wort':<34} {'S':>3} {'n':>3} {'YES':>4} {'Quote':>6} {'Lapl.':>6} {'letzte3':>8}"
    zeilen = [kopf]
    for r in raten[:max_zeilen]:
        zeilen.append(f"{r.wort[:34]:<34} {r.schwelle:>3} {r.n:>3} {r.yes:>4} "
                      f"{r.quote:>6.2f} {r.laplace:>6.2f} {r.letzte3_yes}/{r.letzte3_n:>6}")
    if len(raten) > max_zeilen:
        zeilen.append(f"... {len(raten) - max_zeilen} weitere Zeilen nur im JSON")
    return "\n".join(zeilen)


def _tabelle_vergleich(zeilen: list[dict]) -> str:
    out = [f"{'Frage':<60} {'bid':>6} {'ask':>6} {'n':>3} {'Lapl.':>6} {'letzte3':>8}  Label"]
    for z in zeilen[:MAX_EVENTS_JE_ABFRAGE]:
        lap = f"{z['laplace']:.2f}" if z["laplace"] is not None else "-"
        out.append(f"{z['frage'][:60]:<60} {str(z['bid']):>6} {str(z['ask']):>6} "
                   f"{z['n']:>3} {lap:>6} {z['letzte3']:>8}  {z['label']}")
    return "\n".join(out)


def main(argv: list[str] | None = None, lader: Lader = hole_json) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--serie", action="append", required=True,
                    help="Gamma series_id (mehrfach moeglich)")
    ap.add_argument("--offen", help="Event-ID des offenen Events fuer den Quote-Vergleich")
    ap.add_argument("--limit", type=int, default=MAX_EVENTS_JE_ABFRAGE,
                    help=f"Events je Serie, hoechstens {MAX_EVENTS_JE_ABFRAGE}")
    ap.add_argument("--json", type=Path, help="Ergebnis zusaetzlich als JSON schreiben")
    args = ap.parse_args(argv)

    ergebnis: dict = {"stand_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "quelle": "gamma-api.polymarket.com (oeffentlich, read-only)",
                      "serien": {}}
    alle_beob: dict[Schluessel, list[Beobachtung]] = {}
    for sid in args.serie:
        events = lade_serie(sid, lader=lader, limit=args.limit)
        beob = sammle_beobachtungen(events)
        raten = basisraten(beob)
        ergebnis["serien"][str(sid)] = {
            "n_events": len(events),
            "events": [{"id": str(e.get("id")), "ende": (e.get("endDate") or "")[:10],
                        "titel": e.get("title")} for e in events],
            "basisraten": [asdict(r) for r in raten],
        }
        for k, v in beob.items():
            alle_beob.setdefault(k, []).extend(v)
        print(f"\n== Serie {sid}: {len(events)} geschlossene Events, "
              f"{len(raten)} Wortmaerkte ==")
        print(_tabelle_basisraten(raten))

    if args.offen:
        offen = lade_event(args.offen, lader=lader)
        vergleich = vergleiche(basisraten(alle_beob), offen)
        ergebnis["vergleich"] = {"event_id": str(args.offen), "titel": offen.get("title"),
                                 "zeilen": vergleich}
        print(f"\n== Offenes Event {args.offen}: {offen.get('title')} ==")
        print(_tabelle_vergleich(vergleich))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"\nJSON: {args.json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
