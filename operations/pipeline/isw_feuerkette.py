"""Feuerkette: vom ISW-Kandidaten zur fertigen Order-Spezifikation.

Der Rekorder misst den Vorlauf ISW-Karte → Polymarket. Gemessen ist damit
auch, dass die Kante ausschliesslich im Überraschungsmoment lebt
(Krasnoiarske +82 pp, Oleksiyevo +6 pp, Myrne +1,5 pp) und dass das
Fenster kurz ist: Bei Krasnoiarske lagen zwischen ISW-Polygon und erstem
Trade 18 min 43 s. Ein Signal, das nur als Zeile in einer JSONL-Datei
landet, ist in dieser Zeit wertlos.

Diese Kette endet bei der **Order-Spezifikation**. Sie platziert nichts,
kennt keine Keys und keine Wallet. Das Auslösen liegt bei der Autorin.

Drei Entwurfsentscheidungen, alle aus den Messdaten:

1. **Feuern am Kandidaten, nicht an der Bestätigung.** Das
   Beruhigungsfenster des Rekorders dauert 3600 s — länger als das ganze
   Krasnoiarske-Fenster. Es filtert Flap-Artefakte für die *Statistik*;
   für den Handel kostet es die gesamte Kante. Im Live-Protokoll wurden
   bisher 17 von 17 Kandidaten bestätigt, 0 Flaps. Mess-Trigger und
   Feuer-Trigger sind darum getrennt: die Bestätigung läuft unverändert
   weiter, dieses Modul hängt am Kandidaten.

2. **Der Deckel prüft `best_ask`, nie den Midpoint.** Im
   Krasnoiarske-Sweep zeigte der Midpoint 0.046, der billigste echte Fill
   lag bei **0.395** (Review-Befund 24.07., siehe `buch_tiefe`). Ein Gate
   auf `preis_yes` würde in dem Glauben feuern, zum Midpoint kaufen zu
   können. Fehlt das Orderbuch (Preisbudget je Zyklus erschöpft), wird
   NICHT gefeuert — ein unbekannter Ask ist kein niedriger Ask.

3. **Ein Siedlungsereignis, ein Markt.** Dieselbe Schattierung trifft
   mehrere Laufzeiten gleichzeitig (Krasnoiarske 3 Märkte, Oleksiyevo 2).
   Ohne Gruppierung entstünde drei- statt einfaches Exposure. Gewählt
   wird der kurzdatierteste Markt: bei Krasnoiarske ging genau der
   `july-31`-Markt von 0.046 auf 0.93.

Jeder Kandidat erzeugt entweder einen Feuerbefehl ODER eine
protokollierte Ablehnung mit Grund. Das ist Absicht: Die
Betriebsgeschichte dieses Projekts besteht aus Ausfällen, die wie
Normalbetrieb aussahen. Eine Kette, die schweigend nicht feuert, wäre
derselbe Fehler noch einmal.

Aufruf (Trockenlauf gegen das Live-Protokoll):

    python -m operations.pipeline.isw_feuerkette --zeigen
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

# --- Parameter der Autorin (07.08.2026) -------------------------------
ASK_DECKEL = 0.60              # teurer wird nicht gekauft
EINSATZ_USDC = 200.0           # je Siedlungsereignis, nicht je Markt
WOCHENDECKEL_USDC = 400.0      # rollend über 7 Tage

# Ein Feuerbefehl verfällt. Das Krasnoiarske-Fenster war 1123 s lang, die
# Erkennung kostet ~120 s davon. Wer den Befehl später aufgreift, kauft
# in einen Markt, der die Nachricht längst hat.
GUELTIG_S = 600.0

STANDARD_BEFEHLE = Path("data/live/isw_ukraine/feuerbefehle.jsonl")


@dataclass(frozen=True)
class Feuerbefehl:
    """Alles, was ein Executor braucht — und nichts, was er nicht darf."""

    art: str
    zeit_utc: str
    gueltig_bis_utc: str
    markt_slug: str
    token_id: str
    seite: str
    max_preis: float
    einsatz_usdc: float
    shares_bei_deckel: float
    best_ask: float
    ende_utc: str | None
    siedlung: str
    layer: str
    vorlauf_s: float | None
    nach_ausfall_s: float = 0.0
    geschwister_maerkte: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Ablehnung:
    """Ein Kandidat, der bewusst nicht gefeuert hat."""

    art: str
    zeit_utc: str
    markt_slug: str
    grund: str
    detail: str


def _jetzt() -> datetime:
    return datetime.now(UTC)


def _iso(zeit: datetime) -> str:
    return zeit.strftime("%Y-%m-%dT%H:%M:%SZ")


def _lies_utc(wert: str | None) -> datetime | None:
    if not wert:
        return None
    try:
        zeit = datetime.fromisoformat(str(wert).replace("Z", "+00:00"))
    except ValueError:
        return None
    return zeit if zeit.tzinfo else zeit.replace(tzinfo=UTC)


# ---------------------------------------------------------- Wochendeckel

def wochenverbrauch(pfad: Path, jetzt: datetime) -> float:
    """Summe der in den letzten 7 Tagen ausgegebenen Feuerbefehle.

    Die Buchhaltung liest die ausgegebenen Befehle zurück, statt einen
    eigenen Zähler zu führen: Ein Zähler kann von der Realität abweichen,
    die Befehlsdatei IST die Realität dessen, was diese Kette
    freigegeben hat.

    Bewusst konservativ: Gezählt wird der ausgegebene Befehl, nicht der
    ausgeführte Trade. Läuft der Executor nicht, bremst der Deckel
    trotzdem — lieber zu wenig handeln als den Deckel zu überschreiten,
    weil eine Rückmeldung fehlte.
    """
    if not pfad.exists():
        return 0.0
    grenze = jetzt - timedelta(days=7)
    summe = 0.0
    try:
        with pfad.open(encoding="utf-8", errors="replace") as datei:
            for zeile in datei:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    eintrag = json.loads(zeile)
                except ValueError:
                    continue
                if eintrag.get("art") != "feuerbefehl":
                    continue
                zeit = _lies_utc(eintrag.get("zeit_utc"))
                if zeit is not None and zeit >= grenze:
                    summe += float(eintrag.get("einsatz_usdc") or 0.0)
    except OSError:
        return 0.0
    return round(summe, 2)


# ------------------------------------------------------------ Marktwahl

def waehle_markt(gruppe: list[tuple[dict, object]]) -> tuple[dict, object]:
    """Kurzdatiertester Markt eines Siedlungsereignisses.

    Märkte ohne lesbares `ende_utc` landen hinten — ein unbekanntes
    Enddatum darf einen bekannten, kurz laufenden Markt nie verdrängen.
    Bei Gleichstand entscheidet der Slug, damit die Wahl deterministisch
    bleibt.
    """
    def schluessel(eintrag: tuple[dict, object]):
        _, ziel = eintrag
        ende = _lies_utc(getattr(ziel, "ende_utc", None))
        return (ende is None, ende or datetime.max.replace(tzinfo=UTC),
                getattr(ziel, "slug", ""))

    return sorted(gruppe, key=schluessel)[0]


# ------------------------------------------------------------ Kernlogik

def _ask_aus(meldung: dict) -> float | None:
    buch = meldung.get("buch")
    if not isinstance(buch, dict):
        return None
    ask = buch.get("best_ask")
    try:
        return float(ask) if ask is not None else None
    except (TypeError, ValueError):
        return None


def pruefe(meldungen: list[dict],
           ziel_nach_slug: dict[str, object],
           verbraucht_usdc: float = 0.0,
           jetzt: datetime | None = None,
           ask_deckel: float = ASK_DECKEL,
           einsatz_usdc: float = EINSATZ_USDC,
           wochendeckel_usdc: float = WOCHENDECKEL_USDC,
           ) -> tuple[list[Feuerbefehl], list[Ablehnung]]:
    """Kandidaten eines Zyklus → (Feuerbefehle, Ablehnungen).

    Rein und deterministisch: kein Netz, keine Uhr ausser `jetzt`, keine
    Datei. Genau deshalb testbar.
    """
    jetzt = jetzt or _jetzt()
    zeit = _iso(jetzt)
    gueltig = _iso(jetzt + timedelta(seconds=GUELTIG_S))
    befehle: list[Feuerbefehl] = []
    ablehnungen: list[Ablehnung] = []

    def ablehnen(slug: str, grund: str, detail: str) -> None:
        ablehnungen.append(Ablehnung("ablehnung", zeit, slug, grund, detail))

    # 1. Vorfilter je Marktzeile.
    tauglich: list[tuple[dict, object]] = []
    for meldung in meldungen:
        slug = str(meldung.get("slug") or "")
        if meldung.get("art") != "kandidat_treffer":
            continue
        if not meldung.get("auswertbar"):
            ablehnen(slug, "nicht_auswertbar",
                     f"polaritaet={meldung.get('polaritaet')} "
                     f"kriterium={meldung.get('kriterium')}")
            continue
        if meldung.get("markt_bereits_qualifiziert"):
            ablehnen(slug, "bereits_qualifiziert",
                     "Deckung war schon bestätigt — keine neue Nachricht.")
            continue
        ziel = ziel_nach_slug.get(slug)
        if ziel is None:
            ablehnen(slug, "markt_unbekannt",
                     "kein Marktziel zum Slug (Marktliste veraltet?)")
            continue
        ask = _ask_aus(meldung)
        if ask is None:
            # Preisbudget je Zyklus erschöpft oder Buch leer. Ein
            # unbekannter Ask ist kein niedriger Ask.
            ablehnen(slug, "kein_orderbuch",
                     "best_ask nicht ermittelt — es wird nicht blind gekauft.")
            continue
        if ask > ask_deckel:
            ablehnen(slug, "ask_ueber_deckel",
                     f"best_ask={ask} > {ask_deckel} — der Markt hat die "
                     "Nachricht bereits.")
            continue
        tauglich.append((meldung, ziel))

    # 2. Auf Siedlungsereignisse gruppieren (mehrere Laufzeiten je Ereignis).
    gruppen: dict[object, list[tuple[dict, object]]] = {}
    for meldung, ziel in tauglich:
        schluessel = (getattr(ziel, "siedlung_objectid", None),
                      meldung.get("layer"))
        gruppen.setdefault(schluessel, []).append((meldung, ziel))

    # 3. Je Gruppe genau ein Markt, gegen den Wochendeckel.
    offen = round(wochendeckel_usdc - verbraucht_usdc, 2)
    for schluessel in sorted(gruppen, key=lambda k: str(k)):
        gruppe = gruppen[schluessel]
        meldung, ziel = waehle_markt(gruppe)
        slug = str(meldung.get("slug") or "")
        geschwister = sorted(str(m.get("slug") or "") for m, _ in gruppe
                             if m is not meldung)
        if offen < einsatz_usdc:
            ablehnen(slug, "wochendeckel",
                     f"nur {offen} USDC frei, {einsatz_usdc} noetig "
                     f"(Deckel {wochendeckel_usdc} USDC rollend 7 Tage)")
            continue
        ask = _ask_aus(meldung) or ask_deckel
        befehle.append(Feuerbefehl(
            art="feuerbefehl",
            zeit_utc=zeit,
            gueltig_bis_utc=gueltig,
            markt_slug=slug,
            token_id=str(getattr(ziel, "token_yes", "")),
            seite="BUY_YES",
            max_preis=ask_deckel,
            einsatz_usdc=einsatz_usdc,
            shares_bei_deckel=round(einsatz_usdc / ask_deckel, 2),
            best_ask=ask,
            ende_utc=getattr(ziel, "ende_utc", None),
            siedlung=str(meldung.get("siedlung") or ""),
            layer=str(meldung.get("layer") or ""),
            vorlauf_s=meldung.get("vorlauf_s"),
            nach_ausfall_s=float(meldung.get("nach_ausfall_s") or 0.0),
            geschwister_maerkte=geschwister,
        ))
        offen = round(offen - einsatz_usdc, 2)

    return befehle, ablehnungen


def schreibe(pfad: Path, eintraege: list) -> None:
    """Befehle und Ablehnungen anhaengen; beides in dieselbe Spur."""
    if not eintraege:
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("a", encoding="utf-8") as datei:
        for eintrag in eintraege:
            datei.write(json.dumps(asdict(eintrag), ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Feuerkette ISW-Kandidat -> Order-Spezifikation")
    zerleger.add_argument("--befehle", type=Path, default=STANDARD_BEFEHLE,
                          help="Befehlsspur (Standard: "
                               "data/live/isw_ukraine/feuerbefehle.jsonl)")
    zerleger.add_argument("--zeigen", action="store_true",
                          help="Wochenverbrauch und offenes Budget anzeigen")
    argumente = zerleger.parse_args(argv)
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    jetzt = _jetzt()
    verbraucht = wochenverbrauch(argumente.befehle, jetzt)
    offen = round(WOCHENDECKEL_USDC - verbraucht, 2)
    print(f"Wochendeckel {WOCHENDECKEL_USDC:.0f} USDC | verbraucht "
          f"{verbraucht:.2f} | frei {offen:.2f}")
    print(f"Ask-Deckel {ASK_DECKEL} | Einsatz {EINSATZ_USDC:.0f} USDC je "
          f"Siedlungsereignis | Befehl gueltig {GUELTIG_S:.0f}s")
    if argumente.zeigen and argumente.befehle.exists():
        print(f"Spur: {argumente.befehle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
