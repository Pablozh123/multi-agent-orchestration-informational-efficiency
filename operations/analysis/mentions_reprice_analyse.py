"""Auswertung aufgezeichneter Orderbuecher von Mentions-Maerkten.

Beantwortet die Frage, ob ein Latenz-Edge auf Erwaehnungsmaerkten
ueberhaupt existieren KANN: Wie lange nach dem ersten Preisausbruch war
noch Tiefe unterhalb der Ask-Obergrenze im Buch?

Eingabe ist ein Buch-Protokoll (JSONL), wie es der read-only Rekorder
ueber ein Call- oder Drop-Fenster schreibt. Eine Zeile je Markt und
Messrunde mit `best_ask` und der ausfuehrbaren Tiefe je Deckel.

Kernbegriffe
------------
Ausbruch (t0)
    Erster Messpunkt, an dem der Ask die Ruhelage um mindestens
    MINDEST_SPRUNG uebersteigt UND dort bleibt. Die Persistenz-Pruefung
    ist wesentlich: In duennen Buechern erzeugen Einzeltrades ueber
    wenige Shares Ausschlaege, die wie ein Ausbruch aussehen (Tesla
    22.07.: ein 1.2-Share-Print liess "Software" von 0.94 auf 0.50
    fallen). Ohne Persistenz misst man Rauschen.

Fenster
    Zeitraum ab t0, in dem noch mindestens MINDEST_USD ausfuehrbare
    Tiefe unter dem Deckel lag. Das ist die Groesse, auf die es
    ankommt — nicht der Preis selbst.

Verzoegerung
    Zeit, die eine Pipeline vom gesprochenen Wort bis zur Order
    braucht. Fuer die Live-Stream-Strecke gemessen: rund 10-15 s
    (Broadcast-Verzug 4.3 s + Chunk-Fuellzeit + Transkription).
    Die Auswertung fragt: War zu t0 + Verzoegerung noch etwas da?

Das Urteil folgt einem VOR der Messung festgelegten Kriterium (siehe
URTEIL_*), damit es nicht nachtraeglich passend gemacht wird.

Aufruf:
    python -m operations.analysis.mentions_reprice_analyse \
        --protokoll buch_<slug>.jsonl [--verzoegerung 10] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# --- Parameter der Auswertung (vor der Messung festgelegt) ----------------
DECKEL_FELD = "tiefe_usd_bis_90"   # Ask-Obergrenze des Audio-Profils (0.90)
MINDEST_SPRUNG = 0.08              # ab hier gilt eine Bewegung als Ausbruch
PERSISTENZ_N = 3                   # so viele Punkte muss sie halten
MINDEST_USD = 50.0                 # darunter ist ein Fill wirtschaftlich egal
VERZOEGERUNG_S = 10.0              # Pipeline-Latenz Wort -> Order
BASIS_MIN_N = 3                    # Messpunkte fuer die Ruhelage
VORGEPREIST_AB = 0.90              # daraus ist per Konstruktion nichts zu holen

# Urteil auf Event-Ebene
URTEIL_FENSTER_AB = 3              # so viele Maerkte mit Fenster = Edge moeglich


@dataclass
class Messpunkt:
    ts: datetime
    ask: float | None
    tiefe: float


@dataclass
class Marktbefund:
    wort: str
    schwelle: int
    n_punkte: int
    ruhelage: float | None = None
    ask_start: float | None = None
    ask_ende: float | None = None
    t0: datetime | None = None
    sekunden_bis_t0: float | None = None
    tiefe_bei_verzoegerung: float | None = None
    max_tiefe_nach_t0: float | None = None
    fenster_s: float | None = None
    klasse: str = "unbestimmt"
    begruendung: str = ""

    def zeile(self) -> str:
        t0 = self.t0.strftime("%H:%M:%S") if self.t0 else "-"
        tv = ("%8.0f" % self.tiefe_bei_verzoegerung
              if self.tiefe_bei_verzoegerung is not None else "       -")
        fe = ("%6.0f" % self.fenster_s if self.fenster_s is not None else "     -")
        ruhe = "%.3f" % self.ruhelage if self.ruhelage is not None else "  -  "
        return (f"{self.wort[:22]:22} {ruhe:>5} {t0:>8} {tv} USD {fe} s  "
                f"{self.klasse}")


@dataclass
class Eventbefund:
    quelle: str
    maerkte: list[Marktbefund] = field(default_factory=list)
    urteil: str = ""
    urteil_begruendung: str = ""
    fenster_von: datetime | None = None
    fenster_bis: datetime | None = None


def _parse_ts(roh: str) -> datetime:
    return datetime.fromisoformat(roh.replace("Z", "+00:00")).astimezone(
        timezone.utc)


def lade_protokoll(pfad: Path) -> dict[str, list[Messpunkt]]:
    """Liest das JSONL und gruppiert die Messpunkte je Wort (zeitsortiert)."""
    reihen: dict[str, list[Messpunkt]] = {}
    schwellen: dict[str, int] = {}
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                d = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if d.get("art") != "buch":
                continue
            wort = d.get("wort")
            if not wort:
                continue
            ask = d.get("best_ask")
            reihen.setdefault(wort, []).append(Messpunkt(
                ts=_parse_ts(d["wall_ts_utc"]),
                ask=float(ask) if ask is not None else None,
                tiefe=float(d.get(DECKEL_FELD) or 0.0),
            ))
            schwellen[wort] = int(d.get("schwelle") or 1)
    for reihe in reihen.values():
        reihe.sort(key=lambda m: m.ts)
    lade_protokoll.schwellen = schwellen  # type: ignore[attr-defined]
    return reihen


def ruhelage(reihe: list[Messpunkt], basis_n: int = BASIS_MIN_N) -> float | None:
    """Median der ersten Asks — robust gegen einen Ausreisser am Anfang."""
    asks = [m.ask for m in reihe if m.ask is not None][:max(basis_n, 1)]
    if len(asks) < 1:
        return None
    return statistics.median(asks)


def finde_ausbruch(
    reihe: list[Messpunkt],
    basis: float,
    mindest_sprung: float = MINDEST_SPRUNG,
    persistenz_n: int = PERSISTENZ_N,
) -> int | None:
    """Index des ersten persistenten Ausbruchs nach oben, sonst None.

    Persistenz: Nach dem Ausbruch muessen die naechsten `persistenz_n`
    Punkte im Mittel oberhalb der halben Sprunghoehe bleiben. Damit
    faellt ein einzelner Ausreisser-Print heraus, der sonst als Ausbruch
    gezaehlt wuerde.
    """
    schwelle = basis + mindest_sprung
    halt = basis + mindest_sprung / 2.0
    for i, m in enumerate(reihe):
        if m.ask is None or m.ask < schwelle:
            continue
        folgende = [p.ask for p in reihe[i + 1:i + 1 + persistenz_n]
                    if p.ask is not None]
        if not folgende:
            # Ausbruch am Reihenende: nicht pruefbar, konservativ verwerfen.
            continue
        if statistics.mean(folgende) >= halt:
            return i
    return None


def fenster_kennzahlen(
    reihe: list[Messpunkt],
    i0: int,
    verzoegerung_s: float = VERZOEGERUNG_S,
    mindest_usd: float = MINDEST_USD,
) -> tuple[float | None, float, float]:
    """(Tiefe bei t0+Verzoegerung, max. Tiefe nach t0, Fensterdauer in s)."""
    t0 = reihe[i0].ts
    ziel = t0.timestamp() + verzoegerung_s
    tiefe_bei = None
    for m in reihe[i0:]:
        if m.ts.timestamp() >= ziel:
            tiefe_bei = m.tiefe
            break
    nach = [m for m in reihe[i0:]]
    max_tiefe = max((m.tiefe for m in nach), default=0.0)
    # Fensterdauer: bis die Tiefe dauerhaft unter die Schwelle faellt.
    dauer = 0.0
    for m in nach:
        if m.tiefe >= mindest_usd:
            dauer = m.ts.timestamp() - t0.timestamp()
        else:
            break
    return tiefe_bei, max_tiefe, dauer


def bewerte_markt(
    wort: str,
    schwelle: int,
    reihe: list[Messpunkt],
    verzoegerung_s: float = VERZOEGERUNG_S,
    mindest_usd: float = MINDEST_USD,
) -> Marktbefund:
    b = Marktbefund(wort=wort, schwelle=schwelle, n_punkte=len(reihe))
    asks = [m.ask for m in reihe if m.ask is not None]
    if not asks:
        b.klasse = "keine_daten"
        b.begruendung = "kein einziger Ask im Protokoll"
        return b
    b.ask_start, b.ask_ende = asks[0], asks[-1]
    b.ruhelage = ruhelage(reihe)

    if b.ruhelage is not None and b.ruhelage >= VORGEPREIST_AB:
        b.klasse = "vorgepreist"
        b.begruendung = (f"Ruhelage {b.ruhelage:.3f} >= {VORGEPREIST_AB} — "
                         "unter dem Deckel war per Konstruktion nichts zu holen")
        return b

    i0 = finde_ausbruch(reihe, b.ruhelage or 0.0)
    if i0 is None:
        b.klasse = "kein_ausbruch"
        b.begruendung = (f"kein persistenter Sprung >= {MINDEST_SPRUNG} "
                         "ueber der Ruhelage im Messfenster")
        return b

    b.t0 = reihe[i0].ts
    b.sekunden_bis_t0 = (b.t0 - reihe[0].ts).total_seconds()
    tiefe_bei, max_tiefe, dauer = fenster_kennzahlen(
        reihe, i0, verzoegerung_s, mindest_usd)
    b.tiefe_bei_verzoegerung = tiefe_bei
    b.max_tiefe_nach_t0 = max_tiefe
    b.fenster_s = dauer

    if tiefe_bei is None:
        b.klasse = "abgeschnitten"
        b.begruendung = ("Aufzeichnung endet vor t0 + "
                         f"{verzoegerung_s:.0f}s — nicht bewertbar")
    elif tiefe_bei >= mindest_usd:
        b.klasse = "FENSTER"
        b.begruendung = (f"{tiefe_bei:.0f} USD Tiefe noch "
                         f"{verzoegerung_s:.0f}s nach dem Ausbruch")
    else:
        b.klasse = "zu_schnell"
        b.begruendung = (f"nur {tiefe_bei:.0f} USD nach "
                         f"{verzoegerung_s:.0f}s (Mindestmass {mindest_usd:.0f})")
    return b


def bewerte_event(
    reihen: dict[str, list[Messpunkt]],
    schwellen: dict[str, int] | None = None,
    quelle: str = "",
    verzoegerung_s: float = VERZOEGERUNG_S,
    mindest_usd: float = MINDEST_USD,
) -> Eventbefund:
    """Wendet das vorab festgelegte Urteilskriterium auf alle Maerkte an."""
    schwellen = schwellen or {}
    ev = Eventbefund(quelle=quelle)
    for wort, reihe in sorted(reihen.items()):
        ev.maerkte.append(bewerte_markt(
            wort, schwellen.get(wort, 1), reihe, verzoegerung_s, mindest_usd))
    alle_punkte = [m.ts for reihe in reihen.values() for m in reihe]
    if alle_punkte:
        ev.fenster_von, ev.fenster_bis = min(alle_punkte), max(alle_punkte)

    n_fenster = sum(1 for m in ev.maerkte if m.klasse == "FENSTER")
    n_ausbruch = sum(1 for m in ev.maerkte
                     if m.klasse in ("FENSTER", "zu_schnell"))
    if n_fenster >= URTEIL_FENSTER_AB:
        ev.urteil = "EDGE MOEGLICH"
        ev.urteil_begruendung = (
            f"{n_fenster} Maerkte hatten {verzoegerung_s:.0f}s nach dem "
            f"Ausbruch noch >= {mindest_usd:.0f} USD Tiefe "
            f"(Kriterium: >= {URTEIL_FENSTER_AB}).")
    elif n_ausbruch == 0:
        ev.urteil = "NICHT MESSBAR"
        ev.urteil_begruendung = (
            "kein einziger persistenter Ausbruch im Messfenster — entweder "
            "war alles vorgepreist, oder die Aufzeichnung lag daneben.")
    elif n_fenster == 0:
        ev.urteil = "KEIN EDGE"
        ev.urteil_begruendung = (
            f"{n_ausbruch} Maerkte brachen aus, aber bei keinem war nach "
            f"{verzoegerung_s:.0f}s noch >= {mindest_usd:.0f} USD zu holen.")
    else:
        ev.urteil = "GRENZFALL"
        ev.urteil_begruendung = (
            f"nur {n_fenster} Markt/Maerkte mit Fenster "
            f"(Kriterium: >= {URTEIL_FENSTER_AB}) — zu duenn fuer eine "
            "Aussage, weiterer Datenpunkt noetig.")
    return ev


def _bericht(ev: Eventbefund, verzoegerung_s: float) -> str:
    z = []
    z.append("=" * 78)
    z.append(f"Reprice-Analyse: {ev.quelle}")
    if ev.fenster_von and ev.fenster_bis:
        dauer = (ev.fenster_bis - ev.fenster_von).total_seconds() / 60
        z.append(f"Messfenster {ev.fenster_von.strftime('%Y-%m-%d %H:%M:%S')} "
                 f"bis {ev.fenster_bis.strftime('%H:%M:%S')} UTC "
                 f"({dauer:.0f} min)")
    z.append(f"Annahme Pipeline-Verzoegerung: {verzoegerung_s:.0f}s, "
             f"Mindesttiefe {MINDEST_USD:.0f} USD unter Deckel 0.90")
    z.append("=" * 78)
    z.append(f"{'Wort':22} {'Ruhe':>5} {'t0':>8} {'Tiefe@t0+v':>12} "
             f"{'Fenster':>8}  Klasse")
    z.append("-" * 78)
    rang = {"FENSTER": 0, "zu_schnell": 1, "abgeschnitten": 2,
            "kein_ausbruch": 3, "vorgepreist": 4, "keine_daten": 5}
    for m in sorted(ev.maerkte, key=lambda x: (rang.get(x.klasse, 9), x.wort)):
        z.append(m.zeile())
    z.append("-" * 78)
    zaehl: dict[str, int] = {}
    for m in ev.maerkte:
        zaehl[m.klasse] = zaehl.get(m.klasse, 0) + 1
    z.append("Verteilung: " + ", ".join(
        f"{k}={v}" for k, v in sorted(zaehl.items())))
    z.append("")
    z.append(f"URTEIL: {ev.urteil}")
    z.append(f"  {ev.urteil_begruendung}")
    z.append("")
    z.append("Hinweis: Ohne Audio ist t0 der Zeitpunkt der MARKTBEWEGUNG,")
    z.append("nicht des gesprochenen Worts. Das Wort fiel frueher; die hier")
    z.append("gemessenen Fenster sind daher eine OBERGRENZE dessen, was eine")
    z.append("Pipeline haette erreichen koennen.")
    return "\n".join(z)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--protokoll", required=True, type=Path,
                   help="Buch-Protokoll (JSONL) des Rekorders")
    p.add_argument("--verzoegerung", type=float, default=VERZOEGERUNG_S,
                   help=f"Pipeline-Latenz in s (Standard {VERZOEGERUNG_S:.0f})")
    p.add_argument("--mindest-usd", type=float, default=MINDEST_USD,
                   help=f"Mindesttiefe in USD (Standard {MINDEST_USD:.0f})")
    p.add_argument("--json", type=Path, help="Befund zusaetzlich als JSON")
    a = p.parse_args()

    reihen = lade_protokoll(a.protokoll)
    if not reihen:
        raise SystemExit(f"keine Buch-Zeilen in {a.protokoll}")
    schwellen = getattr(lade_protokoll, "schwellen", {})
    ev = bewerte_event(reihen, schwellen, a.protokoll.name,
                       a.verzoegerung, a.mindest_usd)
    print(_bericht(ev, a.verzoegerung))

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({
                "quelle": ev.quelle,
                "urteil": ev.urteil,
                "urteil_begruendung": ev.urteil_begruendung,
                "verzoegerung_s": a.verzoegerung,
                "mindest_usd": a.mindest_usd,
                "maerkte": [{
                    "wort": m.wort, "schwelle": m.schwelle,
                    "n_punkte": m.n_punkte, "ruhelage": m.ruhelage,
                    "ask_start": m.ask_start, "ask_ende": m.ask_ende,
                    "t0": m.t0.isoformat() if m.t0 else None,
                    "tiefe_bei_verzoegerung": m.tiefe_bei_verzoegerung,
                    "max_tiefe_nach_t0": m.max_tiefe_nach_t0,
                    "fenster_s": m.fenster_s,
                    "klasse": m.klasse, "begruendung": m.begruendung,
                } for m in ev.maerkte],
            }, f, ensure_ascii=False, indent=2)
        print(f"\nJSON geschrieben: {a.json}")


if __name__ == "__main__":
    main()
