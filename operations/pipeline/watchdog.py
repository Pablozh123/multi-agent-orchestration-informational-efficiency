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
- Instanz-Lock (data/live/watchdog.lock): genau EIN Watchdog pro Repo;
  jede weitere Instanz beendet sich sofort still. Grund: am 18.7.
  feuerten zwei Task-Trigger (5-Min-Intervall + Anmeldung) gleichzeitig,
  zwei parallele Durchlaeufe starteten zwei Profile je DOPPELT.
- Doppelstart-Gegencheck vor jedem Start: laeuft laut Win32_Process
  schon ein Python-Prozess mit dem Bot-Modul, der keiner bot.pid der
  betreuten Profile zuzuordnen ist, wird NICHT gestartet (die
  Doppelgaenger vom 18.7. standen in keiner PID-Datei).
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
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from operations.pipeline import config

REPO_ROOT = config.REPO_ROOT
LIVE_ROOT = REPO_ROOT / "data" / "live"
STOP_FILE = config.STOP_FILE
WATCHDOG_JSON = LIVE_ROOT / "watchdog.json"
WATCHDOG_LOG = LIVE_ROOT / "watchdog.log"
WATCHDOG_LOCK = LIVE_ROOT / "watchdog.lock"
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


# ------------------------------------------------- Instanz-Lock (18.7.)
# Zwei parallel gefeuerte Task-Trigger liessen am 18.7. um 15:10:01 zwei
# Watchdog-Durchlaeufe im selben Sekundenfenster laufen — beide sahen
# dieselben Profile als tot und starteten sie je doppelt. Darum haelt
# genau EINE Instanz pro Repo einen exklusiven OS-Lock.

_LOCK_FD: int | None = None


def instanz_lock(pfad: Path | None = None) -> bool:
    """Nimmt den exklusiven Instanz-Lock; False = andere Instanz laeuft.

    Das Gate ist der OS-Dateilock (msvcrt.locking unter Windows, flock
    sonst), NICHT die Datei-Existenz: eine nach einem Crash liegen-
    gebliebene Datei blockiert nie (deshalb kein O_EXCL, und die Datei
    wird nie geloescht). Das OS gibt den Lock bei jedem Prozessende
    frei — auch nach Kill oder Absturz. Der Handle bleibt dafuer
    bewusst bis zum Prozessende offen.
    """
    global _LOCK_FD
    ziel = WATCHDOG_LOCK if pfad is None else pfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(ziel), os.O_CREAT | os.O_RDWR)
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return False
    try:  # Halter-PID als Forensik-Notiz (lesbar, sobald der Lock frei ist)
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode("ascii"))
    except OSError:
        pass
    _LOCK_FD = fd
    return True


def instanz_lock_freigeben() -> None:
    """Gibt den Lock explizit frei (Tests; im Betrieb reicht Prozessende)."""
    global _LOCK_FD
    if _LOCK_FD is None:
        return
    try:
        if sys.platform == "win32":
            import msvcrt
            os.lseek(_LOCK_FD, 0, os.SEEK_SET)
            msvcrt.locking(_LOCK_FD, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(_LOCK_FD, fcntl.LOCK_UN)
    except OSError:
        pass
    os.close(_LOCK_FD)
    _LOCK_FD = None


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


# ----------------------------- Doppelstart-Gegencheck via Win32_Process
# Die Doppelgaenger vom 18.7. standen in KEINER bot.pid — die PID-Datei
# allein reicht als Schutz nicht. Vor jedem Start wird darum die echte
# Prozessliste befragt: lieber einen 5-Min-Zyklus Verzoegerung als ein
# doppelt tradender Bot.


def _parse_prozessliste(text: str) -> list[tuple[int, str]]:
    """Parst die ConvertTo-Json-Ausgabe (Objekt ODER Liste; leer = [])."""
    text = text.strip()
    if not text:
        return []
    daten = json.loads(text)
    if isinstance(daten, dict):  # Einzeltreffer kommt ohne Listen-Klammer
        daten = [daten]
    return [(int(p["ProcessId"]), p.get("CommandLine") or "") for p in daten]


def _python_prozesse() -> list[tuple[int, str]] | None:
    """(PID, Kommandozeile) aller python-Prozesse; None = nicht ermittelbar.

    Win32_Process via PowerShell: tasklist kennt keine Kommandozeilen,
    und wmic ist auf aktuellem Win11 nicht mehr verlaesslich vorhanden.
    Unter Nicht-Windows gibt es den Scan nicht — der Gegencheck faellt
    dann offen aus (Aufrufer startet mit WARN im Log).
    """
    if sys.platform != "win32":
        return None
    befehl = (
        "Get-CimInstance Win32_Process "
        "-Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
        "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             befehl],
            capture_output=True, timeout=30)
        if out.returncode != 0:
            return None
        text = (out.stdout or b"").decode("utf-8", errors="replace")
        return _parse_prozessliste(text)
    except Exception:  # noqa: BLE001
        return None


def _fremde_instanzen(modul: str, managed: dict) -> list[int] | None:
    """PIDs laufender <modul>-Prozesse ohne bot.pid-Zuordnung (None=kein Scan).

    Bekannt sind die PIDs aus den bot.pid-Dateien ALLER betreuten
    Profile (Profile koennen sich ein Modul teilen, z.B. "bot" fuer die
    Audio-Shows). Alles andere mit passendem Modul ist Doppelstart-
    Verdacht.
    """
    prozesse = _python_prozesse()
    if prozesse is None:
        return None
    bekannt: set[int] = set()
    for profil in managed:
        pidfile = LIVE_ROOT / profil / "bot.pid"
        if pidfile.exists():
            try:
                bekannt.add(int(pidfile.read_text(encoding="utf-8").strip()))
            except (ValueError, OSError):
                pass
    muster = re.compile(
        r"operations\.pipeline\." + re.escape(modul) + r"(?=\s|$)")
    return [pid for pid, cmd in prozesse
            if muster.search(cmd) and pid not in bekannt]


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
            fremde = _fremde_instanzen(cfg["modul"], managed)
            if fremde:
                _log(f"  DOPPELSTART-VERDACHT {profil}: {cfg['modul']}-"
                     f"Prozesse ohne bot.pid laufen bereits (PID "
                     f"{', '.join(map(str, fremde))}) — Start uebersprungen.")
                continue
            if fremde is None:
                _log(f"  WARN {profil}: Prozessliste nicht ermittelbar — "
                     "Start ohne Doppelstart-Gegencheck.")
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
    if not instanz_lock():
        _log("Instanz-Lock belegt (andere Watchdog-Instanz laeuft) — "
             "beende still.")
        return
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
