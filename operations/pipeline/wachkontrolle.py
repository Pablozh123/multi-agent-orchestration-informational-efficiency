"""Wachkontrolle: prüft, ob die erwarteten Messposten überhaupt besetzt sind.

Der Watchdog hält am Leben, was in `data/live/watchdog.json` steht. Er kann
nicht bemerken, was dort NICHT mehr steht — und genau daran starb die
Messreihe am 05.08.2026: Die Datei wurde um 19:25 auf einen Juli-Stand
zurückgesetzt, `isw_ukraine` fiel heraus, der Rekorder lief noch zwei
Stunden und blieb dann tot. Der Watchdog protokollierte währenddessen
wahrheitsgemäss „alle betreuten Bots leben" — 26 h 39 min stiller Ausfall
mit vollständigem Datenverlust für das Fenster (ein kompletter
ISW-Tageszyklus). Ein fehlendes Profil ist von ruhigem Betrieb nicht zu
unterscheiden, solange man nur den Watchdog fragt.

Deshalb liegt die Sollbesetzung NICHT in `data/live/` (gitignored, genau
die Datei, die zurückgesetzt wurde), sondern versioniert in
`data/wachposten.json`. Diese Kontrolle vergleicht Soll gegen Ist und
schlägt an, wenn ein Posten fehlt, deaktiviert wurde, sein Betreuungsfenster
verloren hat oder schweigt.

Geprüft wird je Posten:

- `posten_fehlt`         — steht nicht mehr in `watchdog.json` (Fall 05.08.)
- `posten_deaktiviert`   — steht drin, aber `aktiv: false`
- `modul_abweichung`     — betreut, aber mit dem falschen Modul
- `fenster_abgelaufen`   — `ende_utc` ist vorbei, der Watchdog überspringt ihn
- `fenster_zu_kurz`      — `ende_utc` endet vor dem Soll (künftiger Stillstand)
- `herzschlag_fehlt`     — kein `bot_events.jsonl`
- `herzschlag_alt`       — letztes Event älter als `max_herzschlag_s`
- `posten_beendet`       — letztes Event `stop`/`fertig`; der Watchdog
                           startet einen so beendeten Bot NIE wieder neu
- `stop_datei`           — `data/live/STOP` gesetzt, der Watchdog startet gar
                           nichts (global, nicht postenbezogen)
- `watchdog_json_fehlt` / `watchdog_json_unlesbar` — der Watchdog fällt dann
                           auf `DEFAULT_MANAGED` zurück, in dem kein
                           Messposten steht: alle Posten sind unbesetzt.

Die Herzschlag-Schwelle ist bewusst grosszügiger als die des Watchdogs
(`STALE_S` 600 s): der Watchdog darf einen toten Bot erst bemerken und dann
neu starten. Erst wenn er das mehrere Zyklen lang nicht geschafft hat, ist
das ein Befund für die Kontrolle und kein normaler Neustart.

Aufruf (Rückgabecodes für den Scheduler):

    python -m operations.pipeline.wachkontrolle
    python -m operations.pipeline.wachkontrolle --live-root C:/.../data/live
    python -m operations.pipeline.wachkontrolle --json

    0 = alle Posten besetzt      2 = nur Warnungen
    1 = kritische Befunde        3 = Sollbesetzung nicht lesbar
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STANDARD_WACHPOSTEN = REPO_ROOT / "data" / "wachposten.json"
STANDARD_LIVE_ROOT = REPO_ROOT / "data" / "live"

# Watchdog-Takt 5 min, STALE_S 600 s: nach 30 min hatte er rund fünf
# Gelegenheiten zum Neustart. Was dann noch schweigt, schweigt nicht wegen
# eines laufenden Neustarts.
STANDARD_MAX_HERZSCHLAG_S = 1800.0

KRITISCH = "kritisch"
WARNUNG = "warnung"


@dataclass(frozen=True)
class Befund:
    """Ein Prüfergebnis. `posten` ist `*` bei globalen Befunden."""

    posten: str
    code: str
    schwere: str
    text: str

    def zeile(self) -> str:
        return f"{self.schwere.upper()} {self.posten}: {self.text}"


def _jetzt() -> datetime:
    return datetime.now(UTC)


def _lies_utc(wert: str | None) -> datetime | None:
    """ISO-Zeitstempel mit `Z` oder Offset; None bei Unlesbarkeit."""
    if not wert:
        return None
    try:
        zeit = datetime.fromisoformat(str(wert).replace("Z", "+00:00"))
    except ValueError:
        return None
    return zeit if zeit.tzinfo else zeit.replace(tzinfo=UTC)


def lade_wachposten(pfad: Path) -> dict[str, dict]:
    """Versionierte Sollbesetzung; `{}` wenn die Datei fehlt.

    Fehlt sie, gibt es keine Erwartung und damit nichts zu prüfen — die
    Einbindung im Watchdog bleibt dann still. Der CLI-Aufruf wertet das
    dagegen als Aufrufproblem (Code 3), damit ein Tippfehler im Pfad nicht
    als „alles in Ordnung" durchgeht.
    """
    if not pfad.exists():
        return {}
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    posten = daten.get("posten", {})
    if not isinstance(posten, dict):
        raise ValueError("`posten` muss ein Objekt sein")
    return {name: cfg for name, cfg in posten.items()
            if isinstance(cfg, dict) and cfg.get("erwartet", True)}


def lade_managed(pfad: Path) -> tuple[dict | None, str | None]:
    """(`managed`-Block, Fehlergrund). `None` heisst: der Watchdog betreut
    nichts von dem, was hier erwartet wird."""
    if not pfad.exists():
        return None, "fehlt"
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return None, str(ex)
    managed = daten.get("managed")
    if not isinstance(managed, dict):
        return None, "kein `managed`-Block"
    return managed, None


def letztes_event(live_root: Path,
                  posten: str) -> tuple[str | None, float | None]:
    """(`art`, Alter in Sekunden) des letzten Herzschlags; `(None, None)`
    wenn es kein lesbares Event gibt.

    Gelesen wird dieselbe Datei, an der auch der Watchdog das Leben eines
    Profils misst (`bot_events.jsonl`) — nur eben gegen die Sollbesetzung
    statt gegen seine eigene Liste.
    """
    pfad = live_root / posten / "bot_events.jsonl"
    if not pfad.exists():
        return None, None
    letzte = None
    try:
        with pfad.open(encoding="utf-8", errors="replace") as datei:
            for zeile in datei:
                zeile = zeile.strip()
                if zeile:
                    letzte = zeile
    except OSError:
        return None, None
    if not letzte:
        return None, None
    try:
        eintrag = json.loads(letzte)
    except ValueError:
        return None, None
    zeit = _lies_utc(eintrag.get("wall_ts_utc"))
    if zeit is None:
        return eintrag.get("art"), None
    return eintrag.get("art"), (_jetzt() - zeit).total_seconds()


def _pruefe_betreuung(name: str, soll: dict, ist: dict | None,
                      jetzt: datetime) -> list[Befund]:
    """Soll-Ist-Abgleich der Watchdog-Eintragung eines Postens."""
    if ist is None:
        return [Befund(
            name, "posten_fehlt", KRITISCH,
            "steht nicht mehr in watchdog.json — der Watchdog betreut ihn "
            "nicht und meldet trotzdem 'alle betreuten Bots leben'. "
            f"Erwartet laut Sollbesetzung: modul={soll.get('modul')}.")]

    befunde: list[Befund] = []
    if not ist.get("aktiv", True):
        befunde.append(Befund(
            name, "posten_deaktiviert", KRITISCH,
            "steht in watchdog.json, ist aber aktiv=false — wird nicht "
            "neu gestartet."))

    soll_modul = soll.get("modul")
    ist_modul = ist.get("modul")
    if soll_modul and ist_modul != soll_modul:
        befunde.append(Befund(
            name, "modul_abweichung", KRITISCH,
            f"wird als modul={ist_modul!r} betreut, erwartet ist "
            f"{soll_modul!r}."))

    ist_ende = _lies_utc(ist.get("ende_utc"))
    if ist.get("ende_utc") and ist_ende is None:
        befunde.append(Befund(
            name, "fenster_unlesbar", WARNUNG,
            f"ende_utc={ist.get('ende_utc')!r} ist kein lesbarer "
            "Zeitstempel; der Watchdog ignoriert das Fenster dann."))
    elif ist_ende is not None and ist_ende <= jetzt:
        befunde.append(Befund(
            name, "fenster_abgelaufen", KRITISCH,
            f"Betreuungsfenster endete {ist.get('ende_utc')} — der "
            "Watchdog überspringt den Posten seither."))
    else:
        soll_ende = _lies_utc(soll.get("ende_utc"))
        if soll_ende is not None and ist_ende is not None \
                and ist_ende < soll_ende:
            befunde.append(Befund(
                name, "fenster_zu_kurz", WARNUNG,
                f"Betreuung endet {ist.get('ende_utc')}, die Messung ist "
                f"bis {soll.get('ende_utc')} geplant — ab dann stiller "
                "Stillstand."))
    return befunde


def _pruefe_herzschlag(name: str, soll: dict,
                       live_root: Path) -> list[Befund]:
    """Lebenszeichen des Postens, unabhängig von seiner Eintragung."""
    grenze = float(soll.get("max_herzschlag_s", STANDARD_MAX_HERZSCHLAG_S))
    art, alter = letztes_event(live_root, name)
    if alter is None:
        return [Befund(
            name, "herzschlag_fehlt", KRITISCH,
            f"kein lesbares Lebenszeichen in {name}/bot_events.jsonl.")]
    if art in ("stop", "fertig"):
        return [Befund(
            name, "posten_beendet", KRITISCH,
            f"letztes Event ist {art!r} (vor {alter / 60:.0f} min) — einen "
            "so beendeten Bot startet der Watchdog nie wieder neu.")]
    if alter > grenze:
        return [Befund(
            name, "herzschlag_alt", KRITISCH,
            f"letztes Lebenszeichen vor {alter / 3600:.1f} h "
            f"(Grenze {grenze / 3600:.1f} h) — der Watchdog bekommt ihn "
            "nicht hoch.")]
    return []


def pruefe(wachposten: dict[str, dict], watchdog_json: Path,
           live_root: Path, jetzt: datetime | None = None) -> list[Befund]:
    """Vollständiger Soll-Ist-Abgleich. Leere Liste = alle Posten besetzt."""
    jetzt = jetzt or _jetzt()
    befunde: list[Befund] = []
    if not wachposten:
        return befunde

    if (live_root / "STOP").exists():
        befunde.append(Befund(
            "*", "stop_datei", KRITISCH,
            "data/live/STOP ist gesetzt — der Watchdog startet nichts, "
            "auch keinen Messposten."))

    managed, fehler = lade_managed(watchdog_json)
    if managed is None:
        code = ("watchdog_json_fehlt" if fehler == "fehlt"
                else "watchdog_json_unlesbar")
        befunde.append(Befund(
            "*", code, KRITISCH,
            f"watchdog.json nicht verwertbar ({fehler}) — der Watchdog "
            "fällt auf DEFAULT_MANAGED zurück, in dem kein Messposten "
            "steht. Alle erwarteten Posten sind unbesetzt."))

    for name in sorted(wachposten):
        soll = wachposten[name]
        if managed is not None:
            befunde.extend(
                _pruefe_betreuung(name, soll, managed.get(name), jetzt))
        befunde.extend(_pruefe_herzschlag(name, soll, live_root))
    return befunde


def rueckgabecode(befunde: list[Befund]) -> int:
    if any(b.schwere == KRITISCH for b in befunde):
        return 1
    return 2 if befunde else 0


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Prüft die Sollbesetzung der Watchdog-Messposten")
    zerleger.add_argument("--wachposten", type=Path,
                          default=STANDARD_WACHPOSTEN,
                          help="versionierte Sollbesetzung "
                               "(Standard: data/wachposten.json)")
    zerleger.add_argument("--live-root", type=Path, default=STANDARD_LIVE_ROOT,
                          help="data/live des Live-Klons (der Zweit-Klon "
                               "hat kein eigenes data/live)")
    zerleger.add_argument("--json", action="store_true",
                          help="Befunde als JSON statt als Text")
    argumente = zerleger.parse_args(argv)
    for strom in (sys.stdout, sys.stderr):
        try:  # Befundtexte tragen Umlaute; Windows-Konsole ist cp1252.
            strom.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    try:
        wachposten = lade_wachposten(argumente.wachposten)
    except (OSError, ValueError) as ex:
        print(f"Sollbesetzung {argumente.wachposten} unlesbar: {ex}",
              file=sys.stderr)
        return 3
    if not wachposten:
        print(f"Keine Sollbesetzung in {argumente.wachposten} — "
              "nichts zu prüfen.", file=sys.stderr)
        return 3

    befunde = pruefe(wachposten,
                     watchdog_json=argumente.live_root / "watchdog.json",
                     live_root=argumente.live_root)
    if argumente.json:
        print(json.dumps([asdict(b) for b in befunde], ensure_ascii=False,
                         indent=2))
    elif befunde:
        for befund in befunde:
            print(befund.zeile())
    else:
        print(f"alle {len(wachposten)} erwarteten Posten besetzt und wach.")
    return rueckgabecode(befunde)


if __name__ == "__main__":
    raise SystemExit(main())
