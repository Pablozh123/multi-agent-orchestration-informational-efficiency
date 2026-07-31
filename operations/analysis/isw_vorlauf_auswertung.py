"""Auswertung des ISW-Rekorder-Protokolls: die Vorlauf-Verteilung.

Beantwortet die Frage, ob auf den Ukraine-Karten-Maerkten ein Latenz-Edge
gegenueber der Aufloesungsquelle (ISW-Karte) existiert — und wie oft. Die
beiden bisher gemessenen Faelle spannen das Spektrum auf:

    Krasnoiarske (22.07.)          Markt 0.046, 18m43s totes Fenster,
                                   Sweep auf 0.93 -> Kante ~50 pp
    Oleksiyevo-Druzhkivka (29.07.) Markt 0.89 bei T+0, Restbewegung
                                   +6 pp binnen 30 min -> Kante ~5 pp

Die entscheidende Groesse ist deshalb nicht der mittlere Vorlauf, sondern
der ANTEIL der Ueberraschungsfaelle — Ereignisse, bei denen der Markt die
ISW-Schattierung noch nicht eingepreist hatte.

Eingabe ist das Ereignisprotokoll des Rekorders (JSONL,
`data/live/isw_ukraine/ereignisse.jsonl`). Ausgewertet werden
ausschliesslich BESTAETIGTE, AUSWERTBARE Treffer (russische Polaritaet,
Beruehrungskriterium, Beruhigungsfenster ueberstanden); Flaps
(`treffer_verworfen`) und Marktschluesse werden gezaehlt, aber nicht in
die Verteilung aufgenommen. Marktschluss vor Fensterende
(`treffer_markt_geschlossen`) ist gesondert ausgewiesen — oft der Fall
"aufgeloest wegen des Ereignisses".

Klassifikation nach dem T+0-Preis (YES-Mittelpreis bei Erkennung);
Schwellen laut Messprotokoll ISW_VORLAUF_MESSPROTOKOLL_2026-07-30.md:

    ueberraschung   T+0 <  0.50   Markt hatte die Schattierung nicht
    teilweise       0.50 - 0.85   Markt war unterwegs, aber nicht fertig
    antizipiert     T+0 >  0.85   Markt war der Karte voraus

Verknuepfung der Protokollzeilen: `kandidat_treffer` traegt die
T+0-Messung; `treffer_bestaetigt`/`_verworfen`/`_markt_geschlossen`
verweisen per (slug, layer, erste_sichtung_utc) exakt darauf.
Nachfassungen tragen keinen direkten Verweis — sie werden ueber
zeit_utc - real_s = erste Sichtung (Toleranz NACHFASS_TOLERANZ_S)
zugeordnet, denn unter Backoff weicht die reale von der geplanten
Minute ab.

Bekannte Restluecke des Rekorders (dokumentiert): nach einem Absturz
zwischen Protokollzeile und Zustands-Schreiben kann ein Kandidat doppelt
protokolliert sein — identische (slug, layer, zeit_utc) werden deshalb
dedupliziert.

Aufruf:

    python -m operations.analysis.isw_vorlauf_auswertung \
        --protokoll data/live/isw_ukraine/ereignisse.jsonl
    ... --mit-referenz     # nimmt den rekonstruierten Krasnoiarske-Fall
                           # vom 22.07. als Referenzzeile auf
    ... --json out.json    # zusaetzlich maschinenlesbar
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# Klassifikations-Schwellen (Messprotokoll vom 30.07., Entwurf).
UEBERRASCHUNG_MAX = 0.50
ANTIZIPIERT_MIN = 0.85

# Go/No-Go-Schwellen laut Messprotokoll §6. Vorschlagswerte — das
# Einfrieren ist Sache der Studentin; danach nur per Amendment aenderbar.
GO_SCHWELLEN = {
    "min_n_ereignisse": 10,
    "min_anteil_ueberraschung": 0.20,
    "min_median_tiefe_usd": 100.0,
    "min_median_delta_t30": 0.10,
}

# Zuordnungstoleranz Nachfassung -> Kandidat: real_s ist auf 0.1 s
# gerundet, zeit_utc auf ganze Sekunden.
NACHFASS_TOLERANZ_S = 3.0

# Wie weit darf die REALE Messzeit vom geplanten T+n abweichen, damit der
# Preis noch als T+n gilt? Der Rekorder holt Nachfassungen am Ende eines
# Poll-Zyklus (Ruhe-Takt 120 s), und offene Auftraege ueberleben im
# Zustand: nach einem Absturz mit Watchdog-Neustart feuert eine
# 30-Minuten-Nachfassung notfalls Stunden spaeter. Ohne Pruefung landet
# so eine 95-Minuten-Bewegung als delta_t30 in der Verteilung und hebt
# Go-Kriterium 3 kuenstlich (Review-Befund 30.07.). Verspaetete Messungen
# werden verworfen und gezaehlt, nicht stillschweigend umetikettiert.
NACHFASS_GRACE_S = 180.0


@dataclass
class Ereignis:
    """Ein auswertbarer, abgeschlossener Treffer mit allen Messpunkten."""

    slug: str
    siedlung: str
    layer: str
    quelle: str                 # "rekorder" | "rekonstruiert"
    status: str                 # "bestaetigt" | "markt_geschlossen"
    feature_zeit_utc: str | None
    erkannt_utc: str
    vorlauf_s: float | None     # Erkennung minus juengste Flaechen-Aenderung
    preis_t0: float | None
    best_ask_t0: float | None
    buch_usd_030: float | None
    buch_usd_050: float | None
    preis_t1: float | None
    preis_t5: float | None
    preis_t30: float | None
    delta_t30: float | None     # preis_t30 - preis_t0
    klasse: str                 # ueberraschung | teilweise | antizipiert | unbekannt


# Rekonstruierter Referenzfall vom 22.07. (vor Rekorder-Armierung); Zahlen
# aus docs/project/UKRAINE_ISW_LATENZ_SONDIERUNG.md, Abschnitte 2 und 11.
REFERENZ_KRASNOIARSKE = Ereignis(
    slug="will-russia-enter-krasnoiarske-by-july-31",
    siedlung="Krasnoyarske",
    layer="infiltration",
    quelle="rekonstruiert",
    status="bestaetigt",
    feature_zeit_utc="2026-07-22T20:39:00Z",
    erkannt_utc="2026-07-22T20:57:43Z",   # Markt-Sweep = erste Reaktion
    vorlauf_s=1123.0,                     # 18 min 43 s totes Fenster
    preis_t0=0.046,
    best_ask_t0=0.395,                    # billigster Fill im Sweep
    buch_usd_030=None,
    buch_usd_050=None,
    preis_t1=None,
    preis_t5=0.9465,                      # 21:06:07, Minutenhistorie
    preis_t30=0.8700,                     # 21:39:07, Minutenhistorie
    delta_t30=0.824,
    klasse="ueberraschung",
)


def _epoch(iso_utc: str) -> float:
    return datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc).timestamp()


def klassifiziere(preis_t0: float | None) -> str:
    if preis_t0 is None:
        return "unbekannt"
    if preis_t0 < UEBERRASCHUNG_MAX:
        return "ueberraschung"
    if preis_t0 > ANTIZIPIERT_MIN:
        return "antizipiert"
    return "teilweise"


def lies_protokoll(pfad: Path) -> list[dict]:
    """JSONL einlesen; defekte Zeilen zaehlen statt abbrechen."""
    zeilen: list[dict] = []
    defekte = 0
    with open(pfad, encoding="utf-8", errors="replace") as datei:
        for roh in datei:
            roh = roh.strip()
            if not roh:
                continue
            try:
                d = json.loads(roh)
            except json.JSONDecodeError:
                defekte += 1
                continue
            if isinstance(d, dict) and d.get("art"):
                zeilen.append(d)
    if defekte:
        zeilen.append({"art": "_defekte_zeilen", "n": defekte})
    return zeilen


def baue_ereignisse(zeilen: list[dict]) -> tuple[list[Ereignis], dict]:
    """Kandidaten mit Abschluessen und Nachfassungen verknuepfen."""
    kandidaten: dict[tuple[str, str, str], dict] = {}
    # Auch die nicht auswertbaren Kandidaten merken: ihre Abschluesse und
    # Nachfassungen sind erwartete Nicht-Treffer und duerfen die
    # Hygiene-Zaehler nicht mit Falschmeldungen fluten.
    uebersprungene: set[tuple[str, str]] = set()
    abschluesse: dict[tuple[str, str, str], str] = {}
    nachfassungen: list[dict] = []
    zaehler = {
        "zeilen": 0, "defekte_zeilen": 0,
        "kandidat_treffer": 0, "kandidat_treffer_dupliziert": 0,
        "kandidat_treffer_wiederholt": 0,
        "nicht_auswertbar": 0, "kandidat_verlust": 0,
        "treffer_verworfen": 0, "verlust_bestaetigt": 0,
        "verlust_verworfen": 0, "nachfassung_unzuordenbar": 0,
        "nachfassung_verspaetet": 0, "abschluss_ohne_kandidat": 0,
        "fehler": 0, "lauf_fehler": 0,
    }

    for d in zeilen:
        art = d.get("art")
        if art == "_defekte_zeilen":
            zaehler["defekte_zeilen"] = d.get("n", 0)
            continue
        zaehler["zeilen"] += 1
        if art == "kandidat_treffer":
            zaehler["kandidat_treffer"] += 1
            if not d.get("auswertbar"):
                zaehler["nicht_auswertbar"] += 1
                if d.get("slug") and d.get("layer"):
                    uebersprungene.add((d["slug"], d["layer"]))
                continue
            if not (d.get("slug") and d.get("layer") and d.get("zeit_utc")):
                zaehler["defekte_zeilen"] += 1
                continue
            schluessel = (d["slug"], d["layer"], d["zeit_utc"])
            if schluessel in kandidaten:
                zaehler["kandidat_treffer_dupliziert"] += 1
                continue
            kandidaten[schluessel] = d
        elif art in ("treffer_bestaetigt", "treffer_verworfen",
                     "treffer_markt_geschlossen"):
            if art == "treffer_verworfen":
                zaehler["treffer_verworfen"] += 1
            schluessel = (d.get("slug"), d.get("layer"),
                          d.get("erste_sichtung_utc"))
            abschluesse[schluessel] = art
        elif art == "nachfassung":
            nachfassungen.append(d)
        elif art in zaehler:
            zaehler[art] += 1

    # Nachfassungen den Kandidaten zuordnen: zeit_utc - real_s = Sichtung.
    nachfass_je_kandidat: dict[tuple[str, str, str], dict[int, float | None]] = {}
    kandidaten_epochen = {
        schluessel: _epoch(schluessel[2]) for schluessel in kandidaten
    }
    for n in nachfassungen:
        real_s = n.get("real_s")
        if real_s is None:
            zaehler["nachfassung_unzuordenbar"] += 1
            continue
        sichtung = _epoch(n["zeit_utc"]) - real_s
        treffer = None
        for schluessel, epoche in kandidaten_epochen.items():
            if (schluessel[0] == n.get("slug")
                    and schluessel[1] == n.get("layer")
                    and abs(epoche - sichtung) <= NACHFASS_TOLERANZ_S):
                treffer = schluessel
                break
        if treffer is None:
            # Nachfassungen nicht auswertbarer Maerkte sind erwartet.
            if (n.get("slug"), n.get("layer")) not in uebersprungene:
                zaehler["nachfassung_unzuordenbar"] += 1
            continue
        minute = int(n.get("geplante_minute", 0))
        # Der Preis gilt nur als T+minute, wenn er auch dort gemessen wurde.
        if abs(real_s - minute * 60) > NACHFASS_GRACE_S:
            zaehler["nachfassung_verspaetet"] += 1
            continue
        nachfass_je_kandidat.setdefault(treffer, {})[minute] = n.get("preis_yes")

    # Abschluesse ohne zugehoerigen Kandidaten: die Kandidatenzeile ging
    # verloren (Schreibfehler im Rekorder). Das Ereignis fehlt dann still
    # in der Verteilung — deshalb zaehlen. Nicht-auswertbare Kandidaten
    # sind ausgenommen, deren Abschluesse verwaisen konstruktionsbedingt.
    for schluessel in abschluesse:
        if schluessel in kandidaten:
            continue
        if (schluessel[0], schluessel[1]) in uebersprungene:
            continue     # nicht auswertbarer Markt, Abschluss erwartet
        zaehler["abschluss_ohne_kandidat"] += 1

    # Mehrfache Kandidaten desselben (slug, layer) ohne dazwischenliegenden
    # Abschluss deuten auf eine Doppelerkennung nach Absturz hin (der
    # Rekorder schreibt die Protokollzeile vor dem Zustand). Sie werden
    # NICHT zusammengefasst — echte Wiederholungen gibt es auch —, aber
    # ausgewiesen, damit die Auswertung nicht stillschweigend doppelt zaehlt.
    nach_markt: dict[tuple[str, str], int] = {}
    for slug, layer, _zeit in kandidaten:
        nach_markt[(slug, layer)] = nach_markt.get((slug, layer), 0) + 1
    zaehler["kandidat_treffer_wiederholt"] = sum(
        n - 1 for n in nach_markt.values() if n > 1)

    ereignisse: list[Ereignis] = []
    for schluessel, k in kandidaten.items():
        abschluss = abschluesse.get(schluessel)
        if abschluss == "treffer_verworfen" or abschluss is None:
            # Flap oder noch im Beruhigungsfenster -> keine Messzeile.
            continue
        status = ("markt_geschlossen"
                  if abschluss == "treffer_markt_geschlossen"
                  else "bestaetigt")
        nf = nachfass_je_kandidat.get(schluessel, {})
        preis_t0 = k.get("preis_yes")
        preis_t30 = nf.get(30)
        buch = k.get("buch") or {}
        ereignisse.append(Ereignis(
            slug=k.get("slug", ""),
            siedlung=k.get("siedlung", ""),
            layer=k.get("layer", ""),
            quelle="rekorder",
            status=status,
            feature_zeit_utc=k.get("feature_zeit_utc"),
            erkannt_utc=k.get("zeit_utc", ""),
            vorlauf_s=k.get("vorlauf_s"),
            preis_t0=preis_t0,
            best_ask_t0=buch.get("best_ask"),
            buch_usd_030=buch.get("usd_bis_030"),
            buch_usd_050=buch.get("usd_bis_050"),
            preis_t1=nf.get(1),
            preis_t5=nf.get(5),
            preis_t30=preis_t30,
            delta_t30=(round(preis_t30 - preis_t0, 4)
                       if preis_t30 is not None and preis_t0 is not None
                       else None),
            klasse=klassifiziere(preis_t0),
        ))
    ereignisse.sort(key=lambda e: e.erkannt_utc)
    return ereignisse, zaehler


def _median(werte: list[float]) -> float | None:
    return round(statistics.median(werte), 4) if werte else None


@dataclass
class Siedlungsereignis:
    """Ein physisches ISW-Ereignis, aggregiert über seine Marktzeilen.

    Analyseeinheit laut Messprotokoll §3: dieselbe ISW-Änderung trifft
    mehrere Märkte derselben Siedlung (verschiedene Deadlines). Das sind
    korrelierte Instanzen, keine unabhängigen Stichproben.
    """

    siedlung: str
    layer: str
    erkannt_utc: str
    n_maerkte: int
    quelle: str
    vorlauf_s: float | None
    preis_t0: float | None        # Median über die Marktzeilen
    delta_t30: float | None       # Median über die Marktzeilen
    buch_usd_050: float | None    # Median über die Marktzeilen
    klasse: str


def baue_siedlungsereignisse(ereignisse: list[Ereignis]) -> list[Siedlungsereignis]:
    """Marktzeilen zu physischen Ereignissen zusammenfassen."""
    gruppen: dict[tuple[str, str, str], list[Ereignis]] = {}
    for e in ereignisse:
        gruppen.setdefault((e.siedlung, e.layer, e.erkannt_utc), []).append(e)
    heraus: list[Siedlungsereignis] = []
    for (siedlung, layer, erkannt), gruppe in gruppen.items():
        preis = _median([e.preis_t0 for e in gruppe if e.preis_t0 is not None])
        heraus.append(Siedlungsereignis(
            siedlung=siedlung,
            layer=layer,
            erkannt_utc=erkannt,
            n_maerkte=len(gruppe),
            quelle=gruppe[0].quelle,
            vorlauf_s=_median(
                [e.vorlauf_s for e in gruppe if e.vorlauf_s is not None]),
            preis_t0=preis,
            delta_t30=_median(
                [e.delta_t30 for e in gruppe if e.delta_t30 is not None]),
            buch_usd_050=_median(
                [e.buch_usd_050 for e in gruppe
                 if e.buch_usd_050 is not None]),
            klasse=klassifiziere(preis),
        ))
    heraus.sort(key=lambda s: s.erkannt_utc)
    return heraus


def fasse_zusammen(ereignisse: list[Ereignis],
                   schwellen: dict | None = None) -> dict:
    """Verteilungskennzahlen und Go/No-Go-Prüfung.

    Die Go-Kriterien des Messprotokolls (§6) werden ausdrücklich "in den
    Überraschungsfällen" gemessen — also über die als `ueberraschung`
    klassifizierten SIEDLUNGSEREIGNISSE, nicht über einzeln klassifizierte
    Marktzeilen. Eine Marktzeile mit T+0 = 0.48 in einem insgesamt
    "teilweise"-Ereignis gehört nicht in den Überraschungs-Median, und
    korrelierte Zeilen desselben Ereignisses dürfen ihn nicht mehrfach
    gewichten (Review-Befund 30.07.).

    Der Nenner des Überraschungsanteils sind die KLASSIFIZIERBAREN
    Ereignisse. Ereignisse ohne T+0-Preis (Budget erschöpft) sind keine
    Aussage "war eingepreist" — sie würden den Anteil sonst einseitig nach
    unten verwässern und die 20-%-Schwelle kippen. Sie werden gesondert
    ausgewiesen.
    """
    schwellen = schwellen or GO_SCHWELLEN
    je_klasse: dict[str, dict] = {}
    for klasse in ("ueberraschung", "teilweise", "antizipiert", "unbekannt"):
        gruppe = [e for e in ereignisse if e.klasse == klasse]
        if not gruppe:
            continue
        je_klasse[klasse] = {
            "n": len(gruppe),
            "median_vorlauf_s": _median(
                [e.vorlauf_s for e in gruppe if e.vorlauf_s is not None]),
            "median_preis_t0": _median(
                [e.preis_t0 for e in gruppe if e.preis_t0 is not None]),
            "median_delta_t30": _median(
                [e.delta_t30 for e in gruppe if e.delta_t30 is not None]),
            "median_buch_usd_050": _median(
                [e.buch_usd_050 for e in gruppe
                 if e.buch_usd_050 is not None]),
        }

    physisch = baue_siedlungsereignisse(ereignisse)
    klassen: dict[str, int] = {}
    for s in physisch:
        klassen[s.klasse] = klassen.get(s.klasse, 0) + 1
    n_klassifizierbar = sum(n for k, n in klassen.items() if k != "unbekannt")
    n_ueberraschung = klassen.get("ueberraschung", 0)
    ueberraschungen = [s for s in physisch if s.klasse == "ueberraschung"]

    anteil = (round(n_ueberraschung / n_klassifizierbar, 3)
              if n_klassifizierbar else None)
    med_tiefe = _median([s.buch_usd_050 for s in ueberraschungen
                         if s.buch_usd_050 is not None])
    med_delta = _median([s.delta_t30 for s in ueberraschungen
                         if s.delta_t30 is not None])
    kriterien = {
        "1_anteil_ueberraschung": {
            "wert": anteil, "schwelle": schwellen["min_anteil_ueberraschung"],
            "erfuellt": anteil is not None
            and anteil >= schwellen["min_anteil_ueberraschung"],
        },
        "2_median_tiefe_usd_050": {
            "wert": med_tiefe, "schwelle": schwellen["min_median_tiefe_usd"],
            "erfuellt": med_tiefe is not None
            and med_tiefe >= schwellen["min_median_tiefe_usd"],
        },
        "3_median_delta_t30": {
            "wert": med_delta, "schwelle": schwellen["min_median_delta_t30"],
            "erfuellt": med_delta is not None
            and med_delta >= schwellen["min_median_delta_t30"],
        },
    }
    genug = n_klassifizierbar >= schwellen["min_n_ereignisse"]
    alle_erfuellt = all(k["erfuellt"] for k in kriterien.values())
    entscheidung = ("go_paper" if (genug and alle_erfuellt)
                    else "no_go" if genug else "weiter_messen")

    return {
        "n_marktzeilen": len(ereignisse),
        "n_siedlungsereignisse": len(physisch),
        "n_klassifizierbar": n_klassifizierbar,
        "anteil_ueberraschung": anteil,
        "klassen_siedlungsereignisse": klassen,
        "je_klasse_marktzeilen": je_klasse,
        "go_pruefung": {
            "kriterien": kriterien,
            "min_n_ereignisse": schwellen["min_n_ereignisse"],
            "n_erreicht": n_klassifizierbar,
            "entscheidung": entscheidung,
        },
    }


def formatiere_bericht(ereignisse: list[Ereignis], zaehler: dict,
                       zusammenfassung: dict) -> str:
    zeilen = ["ISW-Vorlauf-Auswertung", "=" * 78]
    kopf = (f"{'erkannt (UTC)':20s} {'Siedlung':22s} {'Layer':12s} "
            f"{'T+0':>6s} {'T+30':>6s} {'d30':>7s} {'Vorlauf':>9s} "
            f"{'Buch<=.50':>9s} Klasse")
    zeilen += [kopf, "-" * len(kopf)]
    for e in ereignisse:
        def f(wert, breite, nachkomma=3):
            return (f"{wert:>{breite}.{nachkomma}f}"
                    if wert is not None else " " * (breite - 1) + "-")
        vorlauf = (f"{e.vorlauf_s:>8.0f}s" if e.vorlauf_s is not None
                   else "        -")
        marke = "*" if e.quelle == "rekonstruiert" else " "
        zeilen.append(
            f"{e.erkannt_utc:20s} {e.siedlung[:22]:22s} {e.layer:12s} "
            f"{f(e.preis_t0, 6)} {f(e.preis_t30, 6)} {f(e.delta_t30, 7)} "
            f"{vorlauf} {f(e.buch_usd_050, 9, 0)} {e.klasse}{marke}")
    zeilen.append("")
    zeilen.append(
        f"Siedlungsereignisse: {zusammenfassung['n_siedlungsereignisse']} "
        f"({zusammenfassung['n_marktzeilen']} Marktzeilen, "
        f"{zusammenfassung['n_klassifizierbar']} klassifizierbar)"
        f"  |  Anteil Ueberraschung: "
        f"{zusammenfassung['anteil_ueberraschung']}"
        f"  |  Klassen: "
        f"{json.dumps(zusammenfassung['klassen_siedlungsereignisse'])}")
    for klasse, kennzahlen in zusammenfassung["je_klasse_marktzeilen"].items():
        zeilen.append(f"  {klasse:14s} {json.dumps(kennzahlen)}")

    pruefung = zusammenfassung["go_pruefung"]
    zeilen.append("")
    zeilen.append("Go-Pruefung (Messprotokoll 30.07., ueber "
                  "Ueberraschungs-Siedlungsereignisse):")
    for name, k in pruefung["kriterien"].items():
        haken = "erfuellt" if k["erfuellt"] else "offen    "
        zeilen.append(f"  [{haken}] {name:26s} wert={k['wert']} "
                      f"schwelle={k['schwelle']}")
    zeilen.append(f"  N: {pruefung['n_erreicht']}/"
                  f"{pruefung['min_n_ereignisse']}"
                  f"  ->  ENTSCHEIDUNG: {pruefung['entscheidung']}")

    zeilen.append("")
    zeilen.append("Protokoll-Hygiene: " + json.dumps({
        k: v for k, v in zaehler.items() if v}))
    zeilen.append("(* = rekonstruierter Referenzfall, nicht vom Rekorder "
                  "gemessen)")
    return "\n".join(zeilen)


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Vorlauf-Verteilung aus dem ISW-Rekorder-Protokoll")
    zerleger.add_argument("--protokoll", type=Path, required=True)
    zerleger.add_argument("--json", type=Path, default=None,
                          help="Ergebnis zusaetzlich als JSON schreiben")
    zerleger.add_argument("--mit-referenz", action="store_true",
                          help="rekonstruierten Krasnoiarske-Fall (22.07.) "
                               "als Referenzzeile aufnehmen")
    argumente = zerleger.parse_args(argv)

    if not argumente.protokoll.exists():
        print(f"Protokoll nicht gefunden: {argumente.protokoll}")
        return 1
    zeilen = lies_protokoll(argumente.protokoll)
    ereignisse, zaehler = baue_ereignisse(zeilen)
    if argumente.mit_referenz:
        ereignisse = sorted(
            ereignisse + [REFERENZ_KRASNOIARSKE],
            key=lambda e: e.erkannt_utc)
    zusammenfassung = fasse_zusammen(ereignisse)
    print(formatiere_bericht(ereignisse, zaehler, zusammenfassung))
    if argumente.json:
        argumente.json.write_text(json.dumps({
            "ereignisse": [asdict(e) for e in ereignisse],
            "siedlungsereignisse": [
                asdict(s) for s in baue_siedlungsereignisse(ereignisse)],
            "zusammenfassung": zusammenfassung,
            "zaehler": zaehler,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
