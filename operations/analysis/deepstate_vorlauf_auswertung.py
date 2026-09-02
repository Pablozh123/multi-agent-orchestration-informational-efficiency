"""Auswertung des DeepState-Vorlaufs: DeepState-Karte -> ISW-Karte -> Markt.

Beantwortet drei Fragen, die das Latenzrennen an der ISW-Quelle (verloren,
siehe Hannivka 01.09.) nicht beantworten kann:

    1. Trefferquote   Wie oft folgt auf eine DeepState-Beruehrung einer
                      Siedlung binnen FENSTER_H eine ISW-Schattierung
                      derselben Siedlung?  (bestaetigt / (bestaetigt +
                      fehlalarm))
    2. Vorlauf        Wie lange VOR der ISW-Erkennung lag die
                      DeepState-Erkennung?  (Median in Stunden)
    3. Preisraum      Wo stand der Markt bei der DeepState-Erkennung, und
                      wo bei der ISW-Erkennung?  (delta = ISW-T+0 minus
                      DeepState-T+0; positiv = der Markt ist zwischen den
                      beiden Quellen gestiegen, der Vorlauf war handelbar)

Dazu die Gegenrichtung: ISW-Ereignisse OHNE vorherige DeepState-Beruehrung
(„verpasst") und DeepState-Ereignisse, bei denen ISW bereits VORHER
geschaltet hatte („isw_zuerst").

Eingaben sind die beiden Rekorder-Protokolle (JSONL):

    data/live/deepstate_ukraine/ereignisse.jsonl   (`ds_treffer`)
    data/live/isw_ukraine/ereignisse.jsonl         (`kandidat_treffer`)

Verknuepft wird ueber den Siedlungsnamen (beide Rekorder lesen ihn aus
demselben ISW-Siedlungslayer, die Schreibweise ist identisch). Analyseeinheit
ist das Siedlungsereignis: dieselbe Kartenaenderung trifft mehrere Maerkte
derselben Siedlung (verschiedene Deadlines) — korrelierte Instanzen, keine
unabhaengigen Stichproben; Preise werden je Siedlungsereignis als Median
ueber die Marktzeilen gefuehrt. Auf ISW-Seite zaehlen ALLE russisch
polarisierten Treffer, auch capture-all-of: das physische Ereignis ist
dasselbe, nur die Marktregel unterscheidet sich.

Aufruf:

    python -m operations.analysis.deepstate_vorlauf_auswertung \
        --deepstate data/live/deepstate_ukraine/ereignisse.jsonl \
        --isw data/live/isw_ukraine/ereignisse.jsonl
    ... --fenster-h 96     # DeepState -> ISW-Fenster (Standard 96 h)
    ... --json out.json    # zusaetzlich maschinenlesbar
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# Vier Tage: ISW arbeitet im US-Arbeitstag und zieht Wochenenden nach;
# DeepState meldet auch am Wochenende. Laenger, und ein spaeterer,
# unabhaengiger ISW-Vorstoss wuerde einem alten DeepState-Ereignis
# zugerechnet.
FENSTER_H = 96.0


def _epoch(iso_utc: str) -> float:
    return datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc).timestamp()


def _median(werte: list[float]) -> float | None:
    werte = [w for w in werte if w is not None]
    return round(statistics.median(werte), 4) if werte else None


def lies_protokoll(pfad: Path) -> list[dict]:
    zeilen: list[dict] = []
    defekt = 0
    if not pfad.exists():
        return zeilen
    with pfad.open(encoding="utf-8") as datei:
        for roh in datei:
            roh = roh.strip()
            if not roh:
                continue
            try:
                d = json.loads(roh)
            except json.JSONDecodeError:
                defekt += 1
                continue
            if isinstance(d, dict):
                zeilen.append(d)
    if defekt:
        zeilen.append({"art": "_defekte_zeilen", "n": defekt})
    return zeilen


@dataclass
class DSEreignis:
    """Eine DeepState-Beruehrung einer Siedlung (ueber ihre Marktzeilen)."""

    siedlung: str
    klasse: str
    erkannt_utc: str
    karte_id: int | None
    n_maerkte: int
    preis_t0: float | None
    auswertbar: bool
    erwaehnt: bool
    nach_ausfall_s: float


@dataclass
class ISWEreignis:
    """Eine ISW-Schattierung einer Siedlung (ueber ihre Marktzeilen)."""

    siedlung: str
    layer: str
    erkannt_utc: str
    n_maerkte: int
    preis_t0: float | None


def baue_ds_ereignisse(zeilen: list[dict]) -> list[DSEreignis]:
    gruppen: dict[tuple[str, str, str], list[dict]] = {}
    for d in zeilen:
        if d.get("art") != "ds_treffer":
            continue
        if not (d.get("siedlung") and d.get("klasse") and d.get("zeit_utc")):
            continue
        if d.get("polaritaet") not in (None, "russisch"):
            continue
        gruppen.setdefault(
            (d["siedlung"], d["klasse"], d["zeit_utc"]), []).append(d)
    heraus = [
        DSEreignis(
            siedlung=siedlung,
            klasse=klasse,
            erkannt_utc=erkannt,
            karte_id=gruppe[0].get("karte_id"),
            n_maerkte=len(gruppe),
            preis_t0=_median([g.get("preis_yes") for g in gruppe]),
            auswertbar=any(bool(g.get("auswertbar")) for g in gruppe),
            erwaehnt=any(bool(g.get("erwaehnt")) for g in gruppe),
            nach_ausfall_s=max(float(g.get("nach_ausfall_s") or 0.0)
                               for g in gruppe),
        )
        for (siedlung, klasse, erkannt), gruppe in gruppen.items()
    ]
    heraus.sort(key=lambda e: e.erkannt_utc)
    return heraus


def baue_isw_ereignisse(zeilen: list[dict]) -> list[ISWEreignis]:
    gruppen: dict[tuple[str, str, str], list[dict]] = {}
    for d in zeilen:
        if d.get("art") != "kandidat_treffer":
            continue
        if not (d.get("siedlung") and d.get("layer") and d.get("zeit_utc")):
            continue
        if d.get("polaritaet") not in (None, "russisch"):
            continue
        gruppen.setdefault(
            (d["siedlung"], d["layer"], d["zeit_utc"]), []).append(d)
    heraus = [
        ISWEreignis(
            siedlung=siedlung,
            layer=layer,
            erkannt_utc=erkannt,
            n_maerkte=len(gruppe),
            preis_t0=_median([g.get("preis_yes") for g in gruppe]),
        )
        for (siedlung, layer, erkannt), gruppe in gruppen.items()
    ]
    heraus.sort(key=lambda e: e.erkannt_utc)
    return heraus


@dataclass
class Verknuepfung:
    """Ein DeepState-Ereignis samt seinem ISW-Gegenstueck (falls vorhanden)."""

    siedlung: str
    klasse: str
    ds_erkannt_utc: str
    preis_ds_t0: float | None
    status: str                    # bestaetigt|fehlalarm|offen|isw_zuerst
    isw_erkannt_utc: str | None = None
    isw_layer: str | None = None
    vorlauf_s: float | None = None     # ISW-Erkennung minus DS-Erkennung
    preis_isw_t0: float | None = None
    delta: float | None = None         # preis_isw_t0 - preis_ds_t0
    auswertbar: bool = False
    erwaehnt: bool = False
    nach_ausfall_s: float = 0.0


def verknuepfe(ds: list[DSEreignis], isw: list[ISWEreignis],
               fenster_s: float, jetzt_ts: float) -> list[Verknuepfung]:
    """Jedem DeepState-Ereignis das erste ISW-Ereignis derselben Siedlung
    im Fenster danach zuordnen; ISW-Ereignisse im Fenster DAVOR machen es
    zu `isw_zuerst` (die Karte war nicht voraus)."""
    isw_je_siedlung: dict[str, list[ISWEreignis]] = {}
    for e in isw:
        isw_je_siedlung.setdefault(e.siedlung, []).append(e)
    heraus: list[Verknuepfung] = []
    for e in ds:
        t_ds = _epoch(e.erkannt_utc)
        v = Verknuepfung(
            siedlung=e.siedlung, klasse=e.klasse,
            ds_erkannt_utc=e.erkannt_utc, preis_ds_t0=e.preis_t0,
            status="offen", auswertbar=e.auswertbar, erwaehnt=e.erwaehnt,
            nach_ausfall_s=e.nach_ausfall_s,
        )
        kandidaten = isw_je_siedlung.get(e.siedlung, [])
        vorher = [i for i in kandidaten
                  if t_ds - fenster_s <= _epoch(i.erkannt_utc) < t_ds]
        nachher = [i for i in kandidaten
                   if t_ds <= _epoch(i.erkannt_utc) <= t_ds + fenster_s]
        if vorher:
            i = max(vorher, key=lambda x: x.erkannt_utc)
            v.status = "isw_zuerst"
            v.isw_erkannt_utc, v.isw_layer = i.erkannt_utc, i.layer
            v.preis_isw_t0 = i.preis_t0
            v.vorlauf_s = round(_epoch(i.erkannt_utc) - t_ds, 1)
        elif nachher:
            i = min(nachher, key=lambda x: x.erkannt_utc)
            v.status = "bestaetigt"
            v.isw_erkannt_utc, v.isw_layer = i.erkannt_utc, i.layer
            v.preis_isw_t0 = i.preis_t0
            v.vorlauf_s = round(_epoch(i.erkannt_utc) - t_ds, 1)
            if v.preis_ds_t0 is not None and i.preis_t0 is not None:
                v.delta = round(i.preis_t0 - v.preis_ds_t0, 4)
        elif jetzt_ts - t_ds > fenster_s:
            v.status = "fehlalarm"
        heraus.append(v)
    return heraus


def isw_ohne_deepstate(ds: list[DSEreignis], isw: list[ISWEreignis],
                       fenster_s: float) -> list[ISWEreignis]:
    """ISW-Ereignisse, denen im Fenster davor KEINE DeepState-Beruehrung
    derselben Siedlung vorausging — die Faelle, in denen DeepState nichts
    gebracht haette."""
    ds_je_siedlung: dict[str, list[float]] = {}
    for e in ds:
        ds_je_siedlung.setdefault(e.siedlung, []).append(_epoch(e.erkannt_utc))
    heraus: list[ISWEreignis] = []
    for i in isw:
        t_isw = _epoch(i.erkannt_utc)
        if not any(t_isw - fenster_s <= t <= t_isw
                   for t in ds_je_siedlung.get(i.siedlung, [])):
            heraus.append(i)
    return heraus


def fasse_zusammen(verkn: list[Verknuepfung], isw: list[ISWEreignis],
                   verpasst: list[ISWEreignis]) -> dict:
    status = {s: sum(1 for v in verkn if v.status == s)
              for s in ("bestaetigt", "fehlalarm", "offen", "isw_zuerst")}
    entschieden = status["bestaetigt"] + status["fehlalarm"]
    bestaetigt = [v for v in verkn if v.status == "bestaetigt"]
    je_klasse: dict[str, dict] = {}
    for klasse in sorted({v.klasse for v in verkn}):
        vk = [v for v in verkn if v.klasse == klasse]
        bk = [v for v in vk if v.status == "bestaetigt"]
        fk = sum(1 for v in vk if v.status == "fehlalarm")
        je_klasse[klasse] = {
            "n": len(vk),
            "bestaetigt": len(bk),
            "fehlalarm": fk,
            "trefferquote": (round(len(bk) / (len(bk) + fk), 3)
                             if (len(bk) + fk) else None),
            "median_vorlauf_h": (round(_median([v.vorlauf_s for v in bk]) / 3600, 2)
                                 if bk and _median([v.vorlauf_s for v in bk])
                                 is not None else None),
        }
    median_vorlauf = _median([v.vorlauf_s for v in bestaetigt])
    return {
        "n_deepstate": len(verkn),
        "status": status,
        "trefferquote": (round(status["bestaetigt"] / entschieden, 3)
                         if entschieden else None),
        "median_vorlauf_h": (round(median_vorlauf / 3600, 2)
                             if median_vorlauf is not None else None),
        "median_preis_ds_t0": _median([v.preis_ds_t0 for v in bestaetigt]),
        "median_preis_isw_t0": _median([v.preis_isw_t0 for v in bestaetigt]),
        "median_delta": _median([v.delta for v in bestaetigt]),
        "n_isw": len(isw),
        "n_isw_verpasst": len(verpasst),
        "anteil_isw_mit_vorlauf": (round(1 - len(verpasst) / len(isw), 3)
                                   if isw else None),
        "je_klasse": je_klasse,
    }


def formatiere_bericht(verkn: list[Verknuepfung], verpasst: list[ISWEreignis],
                       zusammenfassung: dict, fenster_h: float) -> str:
    zeilen = ["DeepState-Vorlauf-Auswertung", "=" * 78]
    zeilen.append(f"{'DS erkannt (UTC)':20} {'Siedlung':22} {'Klasse':9} "
                  f"{'DS-T0':>6} {'ISW-T0':>6} {'delta':>6} {'Vorlauf':>9} "
                  f"Status")
    zeilen.append("-" * 96)
    for v in verkn:
        vorlauf = (f"{v.vorlauf_s / 3600:+.1f}h" if v.vorlauf_s is not None
                   else "-")
        zeilen.append(
            f"{v.ds_erkannt_utc:20} {v.siedlung[:22]:22} {v.klasse:9} "
            f"{_fmt(v.preis_ds_t0):>6} {_fmt(v.preis_isw_t0):>6} "
            f"{_fmt(v.delta):>6} {vorlauf:>9} {v.status}"
            f"{'' if v.auswertbar else '  [nicht auswertbar]'}"
            f"{'  [erwaehnt]' if v.erwaehnt else ''}")
    zeilen.append("")
    z = zusammenfassung
    zeilen.append(
        f"DeepState-Siedlungsereignisse: {z['n_deepstate']}  |  "
        f"Status: {json.dumps(z['status'])}  |  "
        f"Trefferquote: {z['trefferquote']}  |  "
        f"Median Vorlauf: {z['median_vorlauf_h']} h  |  "
        f"Median DS-T0: {z['median_preis_ds_t0']}  |  "
        f"Median delta: {z['median_delta']}")
    for klasse, k in z["je_klasse"].items():
        zeilen.append(f"  {klasse:10} {json.dumps(k)}")
    zeilen.append(
        f"ISW-Siedlungsereignisse: {z['n_isw']}, davon ohne DeepState-Vorlauf "
        f"im {fenster_h:.0f}-h-Fenster: {z['n_isw_verpasst']} "
        f"(Anteil mit Vorlauf: {z['anteil_isw_mit_vorlauf']})")
    for i in verpasst:
        zeilen.append(f"  verpasst  {i.erkannt_utc} {i.siedlung} {i.layer} "
                      f"T0={_fmt(i.preis_t0)}")
    return "\n".join(zeilen)


def _fmt(wert: float | None) -> str:
    return "-" if wert is None else f"{wert:.3f}"


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="DeepState -> ISW -> Markt: Vorlauf und Trefferquote")
    zerleger.add_argument("--deepstate", type=Path, required=True)
    zerleger.add_argument("--isw", type=Path, required=True)
    zerleger.add_argument("--fenster-h", type=float, default=FENSTER_H)
    zerleger.add_argument("--json", type=Path, default=None)
    zerleger.add_argument("--jetzt", default=None,
                          help="Bezugszeit UTC (ISO, fuer Tests)")
    argumente = zerleger.parse_args(argv)

    jetzt_ts = (_epoch(argumente.jetzt) if argumente.jetzt
                else datetime.now(timezone.utc).timestamp())
    fenster_s = argumente.fenster_h * 3600
    ds = baue_ds_ereignisse(lies_protokoll(argumente.deepstate))
    isw = baue_isw_ereignisse(lies_protokoll(argumente.isw))
    verkn = verknuepfe(ds, isw, fenster_s, jetzt_ts)
    verpasst = isw_ohne_deepstate(ds, isw, fenster_s)
    zusammenfassung = fasse_zusammen(verkn, isw, verpasst)
    print(formatiere_bericht(verkn, verpasst, zusammenfassung,
                             argumente.fenster_h))
    if argumente.json:
        argumente.json.parent.mkdir(parents=True, exist_ok=True)
        argumente.json.write_text(json.dumps({
            "fenster_h": argumente.fenster_h,
            "zusammenfassung": zusammenfassung,
            "verknuepfungen": [asdict(v) for v in verkn],
            "isw_verpasst": [asdict(i) for i in verpasst],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
