"""Papier-Executor: liest Feuerbefehle und bucht simulierte Kaeufe.

Stufe 1.5 der Kette. Die Feuerkette (isw_feuerkette) endet bewusst bei der
Order-Spezifikation; die echte Ausfuehrung liegt bei der Autorin. Dieses
Modul schliesst die Luecke dazwischen: Es liest ``feuerbefehle.jsonl`` und
bucht jeden gueltigen Befehl als PAPIER-Kauf in ein eigenes Journal — mit
denselben Regeln, die ein echter Executor haette, aber strukturell ohne die
Faehigkeit zu kaufen. Es kennt keine Wallet, keinen Key und keine
Order-API; ein Test sichert zu, dass das so bleibt.

Was der Papier-Kauf simuliert, und was nicht:

* Gebucht wird zum ``best_ask`` aus dem Befehl — dem Preis, den der
  Rekorder im Moment der Ausgabe wirklich im Buch gesehen hat. Ein echter
  Fill koennte schlechter sein (das Buch bewegt sich); der Befehl traegt
  keinen spaeteren Preis, also erfindet das Journal auch keinen.
* Ein abgelaufener Befehl (``gueltig_bis_utc`` ueberschritten) wird NIE
  gebucht. Sonst simulierte das Papier Fills, die der echte Executor nie
  bekommen haette — genau die Sorte Selbstbetrug, die dieses Projekt
  ueberall sonst aussortiert.
* Der Wochendeckel wird ein zweites Mal gefuehrt, diesmal ueber die
  tatsaechlich gebuchten Papier-Kaeufe. Die Feuerkette bremst schon bei
  der Ausgabe; Guertel und Hosentraeger sind hier billig.

Jeder gelesene Befehl erzeugt genau eine Journalzeile — Kauf ODER
Ablehnung mit Grund — und gilt danach als verarbeitet. Die
Betriebsgeschichte dieses Projekts besteht aus Ausfaellen, die wie
Normalbetrieb aussahen; ein Executor, der schweigend ueberspringt, waere
derselbe Fehler noch einmal.

Aufruf:

    python -m operations.pipeline.isw_papier_executor            # ein Durchlauf
    python -m operations.pipeline.isw_papier_executor --zeigen   # nur Stand, schreibt nichts
    python -m operations.pipeline.isw_papier_executor --folgen 20  # Schleife, alle 20 s
    python -m operations.pipeline.isw_papier_executor --live     # Watchdog-Betrieb

``--live`` spricht die Bot-Konventionen des Watchdogs: Profilordner aus
``BOT_PROFIL`` (Standard ``isw_papier``), Lebenszeichen je Zyklus nach
``bot_events.jsonl`` (die Watchdog-Schwelle liegt bei 600 s), und die
STOP-Datei beendet den Lauf mit demselben ``stop``-Grund, den auch die
anderen Bots schreiben — der Watchdog wertet das als "betreuungspflichtig,
sobald STOP weg ist", nicht als Laufende.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from operations.pipeline.isw_feuerkette import (
    STANDARD_BEFEHLE,
    WOCHENDECKEL_USDC,
)

STANDARD_JOURNAL = Path("data/live/isw_ukraine/papier_journal.jsonl")
LIVE_INTERVALL_S = 20.0   # Befehle verfallen nach 600 s; 20 s laesst Reserve.

# Bewusst NICHT aus config/watchdog importiert: config.py loest BOT_PROFIL
# beim Import gegen seine PROFILE-Tabelle auf, und der Watchdog startet
# diesen Executor mit BOT_PROFIL=isw_papier — einem Profil, das dort mit
# Absicht nicht steht (der Executor hat kein Event, keine Periode, kein
# live_dir im Profilsinn). Der Import beider Module liess den Prozess am
# 07.08. in einer stillen Neustart-Schleife sterben, bevor er sein erstes
# Ereignis schreiben konnte. Die Werte stehen darum lokal; dass sie mit
# watchdog.NOTAUS_GRUND und config.STOP_FILE identisch bleiben, sichert
# der Test (der ohne fremdes BOT_PROFIL importieren darf).
STOP_DATEI = Path("data/live/STOP")
NOTAUS_GRUND = "STOP-Datei"


@dataclass(frozen=True)
class PapierKauf:
    """Ein simulierter Fill. Preis und Menge kommen aus dem Befehl."""

    art: str
    zeit_utc: str
    befehl_zeit_utc: str
    markt_slug: str
    token_id: str
    seite: str
    preis: float
    shares: float
    einsatz_usdc: float
    siedlung: str


@dataclass(frozen=True)
class PapierAblehnung:
    """Ein Befehl, der bewusst nicht gebucht wurde."""

    art: str
    zeit_utc: str
    befehl_zeit_utc: str
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


def _zeilen_zu_dicts(zeilen: list[str]) -> tuple[list[dict], int]:
    """(lesbare Eintraege, Anzahl unlesbarer Zeilen).

    Eine halbe Zeile am Dateiende (der Rekorder schreibt gerade) oder eine
    korrupte Zeile darf nie den ganzen Durchlauf beenden.
    """
    eintraege: list[dict] = []
    unlesbar = 0
    for zeile in zeilen:
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            wert = json.loads(zeile)
        except ValueError:
            unlesbar += 1
            continue
        if isinstance(wert, dict):
            eintraege.append(wert)
        else:
            unlesbar += 1
    return eintraege, unlesbar


def papier_wochenverbrauch(journal: list[dict], jetzt: datetime) -> float:
    """Summe der Papier-Kaeufe der letzten 7 Tage, aus dem Journal."""
    grenze = jetzt - timedelta(days=7)
    summe = 0.0
    for eintrag in journal:
        if eintrag.get("art") != "papier_kauf":
            continue
        zeit = _lies_utc(eintrag.get("zeit_utc"))
        if zeit is not None and zeit >= grenze:
            try:
                summe += float(eintrag.get("einsatz_usdc") or 0.0)
            except (TypeError, ValueError):
                continue
    return round(summe, 2)


def _identitaet(eintrag: dict) -> tuple[str, str] | None:
    """Befehlsidentitaet: Ausgabezeitpunkt + Markt.

    Die Feuerkette stempelt alle Befehle eines Zyklus mit derselben
    ``zeit_utc`` und gibt je Markt hoechstens einen Befehl aus — das Paar
    ist damit eindeutig, ohne dass die Kette eine ID fuehren muesste.
    """
    zeit = eintrag.get("befehl_zeit_utc") or eintrag.get("zeit_utc")
    slug = eintrag.get("markt_slug")
    if not zeit or not slug:
        return None
    return (str(zeit), str(slug))


def verarbeite(befehl_zeilen: list[str],
               journal_zeilen: list[str],
               jetzt: datetime | None = None,
               wochendeckel_usdc: float = WOCHENDECKEL_USDC,
               ) -> tuple[list, dict]:
    """Neue Befehle → (neue Journaleintraege, Statistik).

    Rein und deterministisch: kein Netz, keine Datei, keine Uhr ausser
    ``jetzt``. Genau deshalb testbar — dieselbe Bauart wie
    ``isw_feuerkette.pruefe``.
    """
    jetzt = jetzt or _jetzt()
    zeit = _iso(jetzt)

    befehle, unlesbar_b = _zeilen_zu_dicts(befehl_zeilen)
    journal, unlesbar_j = _zeilen_zu_dicts(journal_zeilen)

    verarbeitet: set[tuple[str, str]] = set()
    for eintrag in journal:
        kennung = _identitaet(eintrag)
        if kennung is not None:
            verarbeitet.add(kennung)

    verbraucht = papier_wochenverbrauch(journal, jetzt)
    neu: list = []
    statistik = {"kaeufe": 0, "ablehnungen": 0, "bekannt": 0,
                 "unlesbar": unlesbar_b + unlesbar_j}

    def ablehnen(befehl: dict, grund: str, detail: str) -> None:
        neu.append(PapierAblehnung(
            art="papier_ablehnung",
            zeit_utc=zeit,
            befehl_zeit_utc=str(befehl.get("zeit_utc") or ""),
            markt_slug=str(befehl.get("markt_slug") or ""),
            grund=grund,
            detail=detail,
        ))
        statistik["ablehnungen"] += 1

    for befehl in befehle:
        if befehl.get("art") != "feuerbefehl":
            continue  # Ablehnungen der Kette sind Protokoll, kein Auftrag.
        kennung = (str(befehl.get("zeit_utc") or ""),
                   str(befehl.get("markt_slug") or ""))
        if kennung in verarbeitet:
            statistik["bekannt"] += 1
            continue
        verarbeitet.add(kennung)

        gueltig_bis = _lies_utc(befehl.get("gueltig_bis_utc"))
        if gueltig_bis is None:
            ablehnen(befehl, "gueltigkeit_unlesbar",
                     f"gueltig_bis_utc={befehl.get('gueltig_bis_utc')!r}")
            continue
        if jetzt > gueltig_bis:
            alter = (jetzt - gueltig_bis).total_seconds()
            ablehnen(befehl, "abgelaufen",
                     f"{alter:.0f}s nach Ablauf gelesen — ein spaeter Kauf "
                     "wuerde einen Fill simulieren, den es nie gab.")
            continue

        try:
            preis = float(befehl.get("best_ask"))
            max_preis = float(befehl.get("max_preis"))
            einsatz = float(befehl.get("einsatz_usdc"))
        except (TypeError, ValueError):
            ablehnen(befehl, "felder_unlesbar",
                     "best_ask/max_preis/einsatz_usdc nicht numerisch")
            continue
        if not 0.0 < preis <= 1.0:
            ablehnen(befehl, "preis_unplausibel", f"best_ask={preis}")
            continue
        if preis > max_preis:
            ablehnen(befehl, "ask_ueber_max",
                     f"best_ask={preis} > max_preis={max_preis}")
            continue

        if round(verbraucht + einsatz, 2) > wochendeckel_usdc:
            ablehnen(befehl, "wochendeckel_papier",
                     f"{verbraucht} USDC in 7 Tagen gebucht, {einsatz} "
                     f"noetig, Deckel {wochendeckel_usdc}")
            continue

        neu.append(PapierKauf(
            art="papier_kauf",
            zeit_utc=zeit,
            befehl_zeit_utc=str(befehl.get("zeit_utc") or ""),
            markt_slug=str(befehl.get("markt_slug") or ""),
            token_id=str(befehl.get("token_id") or ""),
            seite=str(befehl.get("seite") or "BUY_YES"),
            preis=preis,
            shares=round(einsatz / preis, 2),
            einsatz_usdc=einsatz,
            siedlung=str(befehl.get("siedlung") or ""),
        ))
        verbraucht = round(verbraucht + einsatz, 2)
        statistik["kaeufe"] += 1

    return neu, statistik


# ------------------------------------------------------------ Datei-Rand

def lese_zeilen(pfad: Path) -> list[str]:
    if not pfad.exists():
        return []
    try:
        return pfad.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def haenge_an(pfad: Path, eintraege: list) -> None:
    if not eintraege:
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("a", encoding="utf-8") as datei:
        for eintrag in eintraege:
            datei.write(json.dumps(asdict(eintrag), ensure_ascii=False) + "\n")


def durchlauf(befehle_pfad: Path, journal_pfad: Path,
              jetzt: datetime | None = None) -> dict:
    """Ein Lese-Pruef-Schreib-Durchlauf. Gibt die Statistik zurueck."""
    neu, statistik = verarbeite(lese_zeilen(befehle_pfad),
                                lese_zeilen(journal_pfad), jetzt=jetzt)
    haenge_an(journal_pfad, neu)
    for eintrag in neu:
        if isinstance(eintrag, PapierKauf):
            print(f"PAPIER-KAUF {eintrag.markt_slug} preis={eintrag.preis} "
                  f"shares={eintrag.shares} einsatz={eintrag.einsatz_usdc:.0f} USDC")
        else:
            print(f"papier-ablehnung {eintrag.markt_slug}: {eintrag.grund} "
                  f"({eintrag.detail})")
    return statistik


def _ereignis(live_dir: Path, art: str, **extra) -> None:
    """Lebenszeichen nach ``bot_events.jsonl`` — dieselbe Spur wie alle Bots.

    Schluckt Schreibfehler mit Warnung: das Journal ist das Fundament und
    darf nie am Lebenszeichen sterben.
    """
    eintrag = {"wall_ts_utc": _iso(_jetzt()), "art": art, **extra}
    try:
        live_dir.mkdir(parents=True, exist_ok=True)
        with (live_dir / "bot_events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    except OSError:
        print("WARNUNG bot_events.jsonl nicht schreibbar")


def live_lauf(befehle_pfad: Path, journal_pfad: Path, live_dir: Path,
              stop_datei: Path = STOP_DATEI,
              intervall_s: float = LIVE_INTERVALL_S,
              max_zyklen: int | None = None,
              schlaf=time.sleep,
              jetzt_fn=_jetzt) -> int:
    """Watchdog-Betrieb: Durchlauf + Herzschlag je Zyklus, STOP beendet.

    ``max_zyklen`` und ``schlaf`` sind fuer Tests injizierbar; im Betrieb
    laeuft die Schleife, bis die STOP-Datei erscheint oder der Watchdog
    den Prozess ersetzt.
    """
    _ereignis(live_dir, "start")
    zyklen = 0
    while max_zyklen is None or zyklen < max_zyklen:
        if stop_datei.exists():
            _ereignis(live_dir, "stop", grund=NOTAUS_GRUND)
            print(f"STOP-Datei gesehen ({stop_datei}) — Papier-Executor endet.")
            return 0
        statistik = durchlauf(befehle_pfad, journal_pfad, jetzt=jetzt_fn())
        _ereignis(live_dir, "herzschlag",
                  neu=statistik["kaeufe"] + statistik["ablehnungen"])
        zyklen += 1
        if max_zyklen is None or zyklen < max_zyklen:
            schlaf(intervall_s)
    return 0


def zeige_stand(journal_pfad: Path, jetzt: datetime | None = None) -> None:
    jetzt = jetzt or _jetzt()
    journal, _ = _zeilen_zu_dicts(lese_zeilen(journal_pfad))
    kaeufe = [e for e in journal if e.get("art") == "papier_kauf"]
    verbraucht = papier_wochenverbrauch(journal, jetzt)
    print(f"Papier-Journal: {len(kaeufe)} Kaeufe gesamt, "
          f"{sum(1 for e in journal if e.get('art') == 'papier_ablehnung')} "
          "Ablehnungen")
    print(f"Wochendeckel {WOCHENDECKEL_USDC:.0f} USDC | gebucht (7 Tage) "
          f"{verbraucht:.2f} | frei {WOCHENDECKEL_USDC - verbraucht:.2f}")


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Papier-Executor: Feuerbefehle -> simulierte Kaeufe")
    zerleger.add_argument("--befehle", type=Path, default=STANDARD_BEFEHLE)
    zerleger.add_argument("--journal", type=Path, default=STANDARD_JOURNAL)
    zerleger.add_argument("--zeigen", action="store_true",
                          help="nur den Journalstand ausgeben, nichts schreiben")
    zerleger.add_argument("--folgen", type=float, metavar="SEKUNDEN",
                          help="Dauerbetrieb: alle N Sekunden ein Durchlauf")
    zerleger.add_argument("--live", action="store_true",
                          help="Watchdog-Betrieb: Herzschlag, STOP-Datei, "
                               "Profilordner aus BOT_PROFIL")
    argumente = zerleger.parse_args(argv)

    if argumente.zeigen:
        zeige_stand(argumente.journal)
        return 0

    if argumente.live:
        profil = os.environ.get("BOT_PROFIL", "isw_papier")
        live_dir = Path("data/live") / profil
        print(f"Papier-Executor im Watchdog-Betrieb (Profil {profil}, "
              f"alle {LIVE_INTERVALL_S:.0f}s)")
        return live_lauf(argumente.befehle, argumente.journal, live_dir)

    if argumente.folgen:
        intervall = max(1.0, float(argumente.folgen))
        print(f"Papier-Executor folgt {argumente.befehle} "
              f"(alle {intervall:.0f}s, Strg+C beendet)")
        try:
            while True:
                durchlauf(argumente.befehle, argumente.journal)
                time.sleep(intervall)
        except KeyboardInterrupt:
            return 0

    statistik = durchlauf(argumente.befehle, argumente.journal)
    print(f"Durchlauf: {statistik['kaeufe']} Kaeufe, "
          f"{statistik['ablehnungen']} Ablehnungen, "
          f"{statistik['bekannt']} bereits verarbeitet, "
          f"{statistik['unlesbar']} unlesbare Zeilen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
