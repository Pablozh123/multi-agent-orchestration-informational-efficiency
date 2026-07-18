"""Watchdog: haelt die Live-Bots am Leben (gegen PC-Sleep/Session-Teardown).

Hintergrund: die Bots laufen als detachte Prozesse und sterben bei
System-Sleep oder wenn die startende Sitzung endet — ohne Crash, still
(Befund 12./13./16.7., je Stunden stiller Ausfall). Dieser Watchdog macht
EINEN Pruef-Durchlauf und beendet sich; ein Windows-Scheduled-Task ruft
ihn alle 5 Min auf (ueberlebt Reboot/Sleep besser als ein Dauerprozess).

Lebenssignal je Profil ist der Event-Log-Heartbeat (die Bots schreiben
mind. alle paar Minuten ein Event). Zusaetzlich eine PID-Datei, um eine
HAENGENDE Instanz vor dem Neustart sauber zu killen (kein Doppelstart).

Sicherheiten:
- Respektiert den Kill-Switch data/live/STOP (startet dann nichts).
- Startet einen Bot NICHT neu, dessen letztes Event `fertig`/`stop` ist
  (der hat seinen Lauf korrekt beendet — z.B. Audio-Episode fertig).
- Nur innerhalb des konfigurierten Zeitfensters (ende_utc).
- Idempotent: der Neustart-Schutz der Bots (getradet aus dem Log)
  verhindert Doppeltrades.

Konfiguration: data/live/watchdog.json (gitignored, pro Woche editierbar):
  {"managed": {"elon_july13": {"modul": "elon_bot",
                               "ende_utc": "2026-07-20T04:00:00Z",
                               "aktiv": true}}}
Fehlt die Datei, wird DEFAULT_MANAGED genutzt.

Aufruf (vom Scheduler): python -m operations.pipeline.watchdog
Test ohne Neustart:      python -m operations.pipeline.watchdog --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

from operations.pipeline import config

REPO_ROOT = config.REPO_ROOT
LIVE_ROOT = REPO_ROOT / "data" / "live"
STOP_FILE = config.STOP_FILE
WATCHDOG_JSON = LIVE_ROOT / "watchdog.json"
WATCHDOG_LOG = LIVE_ROOT / "watchdog.log"
STALE_S = 600.0  # >10 min ohne Event = tot (Bots schreiben alle <=5 min)

DEFAULT_MANAGED = {
    "elon_july13": {"modul": "elon_bot",
                    "ende_utc": "2026-07-20T04:00:00Z", "aktiv": True},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _log(zeile: str) -> None:
    WATCHDOG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(f"{_now().strftime('%Y-%m-%dT%H:%M:%SZ')} {zeile}\n")
    print(zeile)


def lade_managed() -> dict:
    if WATCHDOG_JSON.exists():
        try:
            return json.load(open(WATCHDOG_JSON, encoding="utf-8")).get(
                "managed", {})
        except Exception as ex:  # noqa: BLE001
            _log(f"WARN watchdog.json unlesbar ({ex}); nutze Default.")
    return DEFAULT_MANAGED


def _letztes_event(profil: str) -> tuple[str | None, float | None]:
    """(art, alter_sekunden) des letzten Log-Events oder (None, None)."""
    pfad = LIVE_ROOT / profil / "bot_events.jsonl"
    if not pfad.exists():
        return None, None
    letzte = None
    with open(pfad, encoding="utf-8", errors="replace") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile:
                letzte = zeile
    if not letzte:
        return None, None
    try:
        e = json.loads(letzte)
        ts = datetime.strptime(e["wall_ts_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
        return e.get("art"), (_now() - ts).total_seconds()
    except Exception:  # noqa: BLE001
        return None, None


def _pid_lebt(pid: int) -> bool:
    """Windows: prueft via tasklist, ob die PID laeuft.

    Bytes-Vergleich (kein text=True): die tasklist-Ausgabe kommt in der
    OEM-Codepage (cp850 o.ae.) und crasht sonst den cp1252-Decoder.
    """
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, timeout=15)
        return str(pid).encode() in (out.stdout or b"")
    except Exception:  # noqa: BLE001
        return False


def _kill_haenger(profil: str) -> None:
    """Killt eine als PID-Datei bekannte, noch laufende (haengende) Instanz."""
    pidfile = LIVE_ROOT / profil / "bot.pid"
    if not pidfile.exists():
        return
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return
    if _pid_lebt(pid):
        _log(f"  kille haengende Instanz {profil} PID {pid}")
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                           capture_output=True, timeout=15)
        except Exception as ex:  # noqa: BLE001
            _log(f"  taskkill-Fehler: {ex}")


def _starte(profil: str, modul: str) -> None:
    live_dir = LIVE_ROOT / profil
    live_dir.mkdir(parents=True, exist_ok=True)
    import os as _os

    umg = dict(_os.environ)
    umg["BOT_PROFIL"] = profil
    umg["PYTHONIOENCODING"] = "utf-8"
    # Intel-Fortran-RTL (via speechbrain/scipy in Profilen mit Sprecher-
    # Verifikation) bricht sonst ab, wenn das kurzlebige Konsolenfenster
    # des Watchdog-Tasks schliesst: "forrtl: error (200) ... window-CLOSE
    # event" (mrbeast_gaming 18.7.). Profile ohne speechbrain (elon,
    # allin) waren nie betroffen.
    umg["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"
    # Detached, eigene Prozessgruppe; Logs anhaengen.
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    with open(live_dir / "bot_stdout.log", "a", encoding="utf-8") as out, \
            open(live_dir / "bot_stderr.log", "a", encoding="utf-8") as err:
        subprocess.Popen(
            [sys.executable, "-m", f"operations.pipeline.{modul}", "--live"],
            cwd=str(REPO_ROOT), env=umg, stdout=out, stderr=err,
            stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    _log(f"  NEUGESTARTET {profil} ({modul})")


def durchlauf(dry_run: bool) -> None:
    if STOP_FILE.exists():
        _log("STOP-Datei aktiv — Watchdog startet nichts.")
        return
    managed = lade_managed()
    jetzt = _now()
    aktionen = 0
    for profil, cfg in managed.items():
        if not cfg.get("aktiv", True):
            continue
        ende = cfg.get("ende_utc")
        if ende:
            try:
                if jetzt > datetime.strptime(
                        ende, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc):
                    continue  # Fenster vorbei — nicht mehr betreuen
            except ValueError:
                pass
        art, alter = _letztes_event(profil)
        if art in ("fertig", "stop"):
            continue  # Lauf korrekt beendet — nicht neu starten
        lebt = alter is not None and alter < STALE_S
        if lebt:
            continue
        # Tot oder haengend -> neu starten.
        zustand = "kein Log" if alter is None else f"letztes Event vor {alter:.0f}s ({art})"
        _log(f"{profil}: TOT ({zustand}) -> Neustart"
             + (" [dry-run, kein Start]" if dry_run else ""))
        aktionen += 1
        if not dry_run:
            _kill_haenger(profil)
            _starte(profil, cfg["modul"])
    if aktionen == 0:
        _log("alle betreuten Bots leben (oder korrekt beendet).")


def main() -> None:
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true",
                   help="nur pruefen/loggen, nichts neu starten")
    p.add_argument("--loop", type=float, default=0.0, metavar="SEK",
                   help="Dauerbetrieb: alle SEK Sekunden pruefen (statt "
                        "Einzeldurchlauf). Nur als Interim ohne Scheduled "
                        "Task — ueberlebt PC-Sleep NICHT (dafuer den Task).")
    argv = p.parse_args()
    if argv.loop > 0:
        import time
        _log(f"Watchdog-Loop gestartet (alle {argv.loop:.0f}s).")
        while True:
            try:
                durchlauf(dry_run=argv.dry_run)
            except Exception as ex:  # noqa: BLE001 - Loop nie sterben lassen
                _log(f"FEHLER im Durchlauf: {ex}")
            time.sleep(argv.loop)
    else:
        durchlauf(dry_run=argv.dry_run)


if __name__ == "__main__":
    main()
