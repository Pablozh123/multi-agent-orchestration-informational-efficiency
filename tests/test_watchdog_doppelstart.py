"""Tests fuer den Doppelstart-Schutz des Watchdogs.

Vorfall 18.7.: der Scheduled Task feuerte ueber zwei Trigger (5-Min-
Intervall + Anmeldung) gleichzeitig, zwei parallele Watchdog-Instanzen
starteten elon_july13 und mrbeast_gaming je DOPPELT (vier Prozesse mit
identischer CreationDate; die Doppelgaenger standen in keiner bot.pid).
Zwei Schutzschichten dagegen: (1) exklusiver Instanz-Lock, (2) Prozess-
Gegencheck via Win32_Process vor jedem Start.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from operations.pipeline import watchdog

REPO_ROOT = Path(watchdog.__file__).resolve().parents[2]

# Kind-Prozess fuer die Lock-Tests: nimmt den Lock, meldet sich, wartet
# auf stdin-EOF und beendet sich (Lock-Freigabe allein durch Prozessende).
KIND_SNIPPET = (
    "import sys\n"
    "from pathlib import Path\n"
    "from operations.pipeline import watchdog\n"
    "ok = watchdog.instanz_lock(Path(sys.argv[1]))\n"
    "print('GEHALTEN' if ok else 'FEHLGESCHLAGEN', flush=True)\n"
    "sys.stdin.read()\n"
)


@pytest.fixture(autouse=True)
def _isolierte_pfade(tmp_path, monkeypatch):
    """Alle Watchdog-Pfade auf tmp umbiegen; nie echte Prozesse anfassen."""
    live = tmp_path / "live"
    monkeypatch.setattr(watchdog, "LIVE_ROOT", live)
    monkeypatch.setattr(watchdog, "WATCHDOG_JSON", live / "watchdog.json")
    monkeypatch.setattr(watchdog, "WATCHDOG_LOG", live / "watchdog.log")
    monkeypatch.setattr(watchdog, "WATCHDOG_LOCK", live / "watchdog.lock")
    monkeypatch.setattr(watchdog, "STOP_FILE", live / "STOP")
    # Sicherheitsnetz: Tests duerfen nie tasklist/taskkill erreichen.
    monkeypatch.setattr(watchdog, "_pid_lebt", lambda pid: False)
    yield
    watchdog.instanz_lock_freigeben()


def _schreibe_managed(cfg: dict) -> None:
    watchdog.WATCHDOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    watchdog.WATCHDOG_JSON.write_text(
        json.dumps({"managed": cfg}), encoding="utf-8")


def _schreibe_event(profil: str, ts: str, art: str = "post") -> None:
    d = watchdog.LIVE_ROOT / profil
    d.mkdir(parents=True, exist_ok=True)
    (d / "bot_events.jsonl").write_text(
        json.dumps({"wall_ts_utc": ts, "art": art}) + "\n", encoding="utf-8")


# ------------------------------------------------------------ Instanz-Lock


def test_instanz_lock_exklusiv_im_selben_prozess(tmp_path) -> None:
    pfad = tmp_path / "watchdog.lock"
    assert watchdog.instanz_lock(pfad) is True
    assert watchdog.instanz_lock(pfad) is False


def test_stale_lockdatei_blockiert_nicht(tmp_path) -> None:
    # Nach einem Crash liegengebliebene Datei darf NIE blockieren: das
    # Gate ist der OS-Lock, nicht die Datei-Existenz (kein O_EXCL).
    pfad = tmp_path / "watchdog.lock"
    pfad.write_text("99999", encoding="utf-8")
    assert watchdog.instanz_lock(pfad) is True


def test_lock_datei_traegt_halter_pid(tmp_path) -> None:
    pfad = tmp_path / "watchdog.lock"
    assert watchdog.instanz_lock(pfad) is True
    watchdog.instanz_lock_freigeben()
    assert pfad.read_text(encoding="utf-8") == str(os.getpid())


def test_lock_exklusiv_ueber_prozessgrenze_und_frei_nach_ende(
        tmp_path) -> None:
    pfad = tmp_path / "watchdog.lock"
    kind = subprocess.Popen(
        [sys.executable, "-c", KIND_SNIPPET, str(pfad)],
        cwd=str(REPO_ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    try:
        assert kind.stdout.readline().strip() == "GEHALTEN", (
            kind.stderr.read())
        # Solange das Kind lebt, ist der Lock belegt ...
        assert watchdog.instanz_lock(pfad) is False
        # ... nach Prozessende gibt das OS ihn frei (ohne Aufraeumen).
        kind.stdin.close()
        kind.wait(timeout=30)
        assert watchdog.instanz_lock(pfad) is True
    finally:
        if kind.poll() is None:
            kind.kill()


def test_main_beendet_still_bei_belegtem_lock(monkeypatch) -> None:
    assert watchdog.instanz_lock() is True  # erste Instanz haelt den Lock
    aufrufe: list[bool] = []
    monkeypatch.setattr(watchdog, "durchlauf",
                        lambda dry_run: aufrufe.append(dry_run))
    monkeypatch.setattr(sys, "argv", ["watchdog"])
    watchdog.main()  # zweite Instanz: kein Durchlauf, kein Fehler
    assert aufrufe == []
    log = watchdog.WATCHDOG_LOG.read_text(encoding="utf-8")
    assert "Instanz-Lock belegt" in log


def test_main_laeuft_bei_freiem_lock(monkeypatch) -> None:
    aufrufe: list[bool] = []
    monkeypatch.setattr(watchdog, "durchlauf",
                        lambda dry_run: aufrufe.append(dry_run))
    monkeypatch.setattr(sys, "argv", ["watchdog", "--dry-run"])
    watchdog.main()
    assert aufrufe == [True]


# ------------------------------------------- Doppelstart-Gegencheck (Start)

CMD_ELON = '"C:\\Python314\\python.exe" -m operations.pipeline.elon_bot --live'
CMD_BOT = '"C:\\Python314\\python.exe" -m operations.pipeline.bot --live'


def test_gegencheck_blockt_unbekannten_doppelgaenger(monkeypatch) -> None:
    # Vorfall 18.7.: laufender elon_bot-Prozess steht in KEINER bot.pid.
    _schreibe_managed({"elon_july13": {"modul": "elon_bot"}})
    _schreibe_event("elon_july13", "2026-01-01T00:00:00Z")  # stale -> Neustart
    monkeypatch.setattr(watchdog, "_python_prozesse",
                        lambda: [(4242, CMD_ELON)])
    starts: list[tuple[str, str]] = []
    monkeypatch.setattr(watchdog, "_starte",
                        lambda p, m: starts.append((p, m)))
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    log = watchdog.WATCHDOG_LOG.read_text(encoding="utf-8")
    assert "DOPPELSTART-VERDACHT" in log


def test_gegencheck_akzeptiert_pid_eines_betreuten_profils(
        monkeypatch) -> None:
    # Zwei Profile teilen das Modul "bot": der laufende Prozess gehoert
    # laut bot.pid dem lebenden Schwesterprofil -> Start ist erlaubt.
    _schreibe_managed({
        "jre_july13": {"modul": "bot"},
        "lemonade_july15": {"modul": "bot"},
    })
    _schreibe_event("jre_july13", "2026-01-01T00:00:00Z")  # tot
    _schreibe_event("lemonade_july15",
                    watchdog._now().strftime("%Y-%m-%dT%H:%M:%SZ"))  # lebt
    (watchdog.LIVE_ROOT / "lemonade_july15" / "bot.pid").write_text(
        "4242", encoding="utf-8")
    monkeypatch.setattr(watchdog, "_python_prozesse",
                        lambda: [(4242, CMD_BOT)])
    starts: list[tuple[str, str]] = []
    monkeypatch.setattr(watchdog, "_starte",
                        lambda p, m: starts.append((p, m)))
    watchdog.durchlauf(dry_run=False)
    assert starts == [("jre_july13", "bot")]


def test_gegencheck_faellt_offen_aus_ohne_prozessliste(monkeypatch) -> None:
    # Scan nicht verfuegbar (PowerShell-Fehler, Nicht-Windows): der
    # Watchdog muss seinen Kernjob (tote Bots beleben) trotzdem tun.
    _schreibe_managed({"elon_july13": {"modul": "elon_bot"}})
    _schreibe_event("elon_july13", "2026-01-01T00:00:00Z")
    monkeypatch.setattr(watchdog, "_python_prozesse", lambda: None)
    starts: list[tuple[str, str]] = []
    monkeypatch.setattr(watchdog, "_starte",
                        lambda p, m: starts.append((p, m)))
    watchdog.durchlauf(dry_run=False)
    assert starts == [("elon_july13", "elon_bot")]
    log = watchdog.WATCHDOG_LOG.read_text(encoding="utf-8")
    assert "ohne Doppelstart-Gegencheck" in log


def test_fremde_instanzen_matcht_nur_das_exakte_modul(monkeypatch) -> None:
    monkeypatch.setattr(watchdog, "_python_prozesse", lambda: [
        (1, CMD_BOT),
        (2, '"C:\\Python314\\python.exe" -m operations.pipeline.bot_recorder'),
        (3, '"C:\\Python314\\python.exe" -m operations.pipeline.watchdog'),
        (4, ""),
    ])
    assert watchdog._fremde_instanzen("bot", {}) == [1]


def test_parse_prozessliste_objekt_liste_und_leer() -> None:
    # ConvertTo-Json liefert bei genau einem Treffer ein Objekt statt
    # einer Liste; leere Ausgabe heisst: kein python.exe unterwegs.
    einzel = '{"ProcessId":42,"CommandLine":"python.exe -m x"}'
    liste = '[{"ProcessId":1,"CommandLine":null},{"ProcessId":2,"CommandLine":"x"}]'
    assert watchdog._parse_prozessliste(einzel) == [(42, "python.exe -m x")]
    assert watchdog._parse_prozessliste(liste) == [(1, ""), (2, "x")]
    assert watchdog._parse_prozessliste("") == []
    assert watchdog._parse_prozessliste("  \n") == []


@pytest.mark.skipif(sys.platform != "win32",
                    reason="Win32_Process-Scan gibt es nur unter Windows")
def test_python_prozesse_liefert_eigenen_prozess() -> None:
    prozesse = watchdog._python_prozesse()
    assert prozesse is not None
    assert os.getpid() in [pid for pid, _ in prozesse]
