"""Tests fuer die per-Profil-Startwache der Live-Bots.

Vorfall 22.7. 10:55:02-03Z: Watchdog-Tick und starte_bots.ps1 starteten
lemonade_july22 sekundengleich DOPPELT. Das Skript prueft je Profil nur
bot.pid — die schrieb der 1 s aeltere Watchdog-Start aber erst NACH dem
Trading-Setup (Imports, Modell-Laden: zehn+ Sekunden Race-Fenster
zwischen Prozessstart und PID-Write in bot.lauf).

Die Wache schliesst die ganze Klasse dieser Starter-Races am Ursprung:
sie lebt im BOT selbst (egal wer startet — Watchdog, Skript, Hand), als
OS-Dateilock auf data/live/<profil>/start.lock nach der Mechanik von
watchdog.instanz_lock (PR #18): Handle bleibt bis Prozessende offen, das
OS raeumt bei JEDEM Prozessende auf (auch Kill/Crash), eine liegen-
gebliebene Datei blockiert nie. bot.pid wird atomar SOFORT nach dem
Wache-Gewinn geschrieben, nicht erst nach dem Setup.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from operations.pipeline import config, startwache

REPO_ROOT = Path(startwache.__file__).resolve().parents[2]

# Kind-Prozess: nimmt die Wache, meldet sich, wartet auf stdin-EOF und
# beendet sich (Freigabe allein durch Prozessende, kein Aufraeum-Code).
KIND_SNIPPET = (
    "import sys\n"
    "from pathlib import Path\n"
    "from operations.pipeline import startwache\n"
    "ok = startwache.wache_nehmen(Path(sys.argv[1]))\n"
    "print('GEHALTEN' if ok else 'FEHLGESCHLAGEN', flush=True)\n"
    "sys.stdin.read()\n"
)


@pytest.fixture(autouse=True)
def _wache_aufraeumen():
    yield
    startwache.wache_freigeben()


# ------------------------------------------------------------ Kern: Lock


def test_wache_exklusiv_im_selben_prozess(tmp_path) -> None:
    erste = startwache.Startwache(tmp_path)
    zweite = startwache.Startwache(tmp_path)
    assert erste.nehmen() is True
    assert zweite.nehmen() is False
    erste.freigeben()


def test_wache_frei_nach_freigabe(tmp_path) -> None:
    erste = startwache.Startwache(tmp_path)
    assert erste.nehmen() is True
    erste.freigeben()
    zweite = startwache.Startwache(tmp_path)
    assert zweite.nehmen() is True
    zweite.freigeben()


def test_stale_lockdatei_blockiert_nicht(tmp_path) -> None:
    # Nach einem Crash/Kill liegengebliebene Datei darf NIE blockieren:
    # das Gate ist der OS-Lock, nicht die Datei-Existenz (kein O_EXCL,
    # kein Alters-Verwurf — das OS gibt den Lock bei Prozessende frei).
    (tmp_path / "start.lock").write_text("99999", encoding="utf-8")
    wache = startwache.Startwache(tmp_path)
    assert wache.nehmen() is True
    wache.freigeben()


def test_lockdatei_traegt_halter_pid(tmp_path) -> None:
    wache = startwache.Startwache(tmp_path)
    assert wache.nehmen() is True
    wache.freigeben()
    assert (tmp_path / "start.lock").read_text(
        encoding="utf-8") == str(os.getpid())


def test_wache_exklusiv_ueber_prozessgrenze_und_frei_nach_ende(
        tmp_path) -> None:
    kind = subprocess.Popen(
        [sys.executable, "-c", KIND_SNIPPET, str(tmp_path)],
        cwd=str(REPO_ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    try:
        assert kind.stdout.readline().strip() == "GEHALTEN", (
            kind.stderr.read())
        # Solange das Kind lebt, ist die Wache belegt ...
        assert startwache.Startwache(tmp_path).nehmen() is False
        # ... nach Prozessende gibt das OS sie frei (ohne Aufraeumen).
        kind.stdin.close()
        kind.wait(timeout=30)
        nach = startwache.Startwache(tmp_path)
        assert nach.nehmen() is True
        nach.freigeben()
    finally:
        if kind.poll() is None:
            kind.kill()


# ------------------------------------------- wache_nehmen: Wache + bot.pid


def test_wache_nehmen_schreibt_bot_pid_atomar(tmp_path) -> None:
    assert startwache.wache_nehmen(tmp_path) is True
    assert (tmp_path / "bot.pid").read_text(
        encoding="utf-8") == str(os.getpid())
    # Kein Temp-Rest des atomaren Writes (tmp + os.replace).
    reste = [p.name for p in tmp_path.iterdir()
             if p.name not in ("bot.pid", "start.lock")]
    assert reste == []


def test_wache_nehmen_ueberschreibt_alte_bot_pid(tmp_path) -> None:
    # bot.pid einer frueheren (toten) Instanz wird nach Wache-Gewinn
    # ueberschrieben — die Wache entscheidet, nicht die Datei.
    (tmp_path / "bot.pid").write_text("4711", encoding="utf-8")
    assert startwache.wache_nehmen(tmp_path) is True
    assert (tmp_path / "bot.pid").read_text(
        encoding="utf-8") == str(os.getpid())


def test_wache_nehmen_verlierer_schreibt_keine_bot_pid(tmp_path) -> None:
    # Der Verlierer darf bot.pid des Gewinners nicht anfassen.
    halter = startwache.Startwache(tmp_path)
    assert halter.nehmen() is True
    (tmp_path / "bot.pid").write_text("111", encoding="utf-8")
    assert startwache.wache_nehmen(tmp_path) is False
    assert (tmp_path / "bot.pid").read_text(encoding="utf-8") == "111"
    halter.freigeben()


def test_wache_nehmen_legt_live_dir_an(tmp_path) -> None:
    ziel = tmp_path / "profil"
    assert startwache.wache_nehmen(ziel) is True
    assert (ziel / "bot.pid").exists()


# --------------------------------- Integration: lauf() aller drei Module
#
# Abbruchpfad: haelt ein anderer die Wache, kehrt lauf() zurueck, BEVOR
# irgendein Trading-Setup laeuft (Bombe im Rules-Loader darf nie zuenden)
# — und hinterlaesst ein doppelstart_abgebrochen-Event als Forensik.
# Erfolgspfad: bot.pid steht, BEVOR das Trading-Setup beginnt (Bombe im
# Rules-Loader zuendet erst NACH dem PID-Write).


def _events(live_dir: Path) -> list[dict]:
    pfad = live_dir / "bot_events.jsonl"
    if not pfad.exists():
        return []
    return [json.loads(z) for z in
            pfad.read_text(encoding="utf-8").splitlines() if z.strip()]


def _bombe(*_a, **_kw):
    raise AssertionError("Trading-Setup erreicht — Wache hat nicht gegriffen")


@pytest.fixture()
def _live_dir(tmp_path, monkeypatch):
    live = tmp_path / "profil"
    monkeypatch.setattr(config, "LIVE_DIR", live)
    return live


@pytest.mark.parametrize("modulname, rules_loader", [
    ("bot", "lade_snapshot_rules"),
    ("elon_bot", "baue_elon_rules"),
    ("trump_bot", "baue_elon_rules"),
])
def test_lauf_bricht_bei_belegter_wache_vor_setup_ab(
        modulname, rules_loader, _live_dir, monkeypatch) -> None:
    import importlib

    modul = importlib.import_module(f"operations.pipeline.{modulname}")
    monkeypatch.setattr(modul, rules_loader, _bombe)
    if modulname == "bot":
        monkeypatch.setattr(config, "ZIELSPRECHER_REFERENZ", None)
    halter = startwache.Startwache(_live_dir)
    assert halter.nehmen() is True
    try:
        modul.lauf(live=False)  # muss still zurueckkehren, nichts starten
    finally:
        halter.freigeben()
    arten = [e["art"] for e in _events(_live_dir)]
    assert arten == ["doppelstart_abgebrochen"]
    assert not (_live_dir / "bot.pid").exists()


class _SetupBombe(Exception):
    pass


def _setup_bombe(*_a, **_kw):
    raise _SetupBombe()


@pytest.mark.parametrize("modulname, rules_loader", [
    ("bot", "lade_snapshot_rules"),
    ("elon_bot", "baue_elon_rules"),
    ("trump_bot", "baue_elon_rules"),
])
def test_lauf_schreibt_bot_pid_vor_trading_setup(
        modulname, rules_loader, _live_dir, monkeypatch) -> None:
    import importlib

    modul = importlib.import_module(f"operations.pipeline.{modulname}")
    monkeypatch.setattr(modul, rules_loader, _setup_bombe)
    if modulname == "bot":
        monkeypatch.setattr(config, "ZIELSPRECHER_REFERENZ", None)
    with pytest.raises(_SetupBombe):
        modul.lauf(live=False)
    # bot.pid stand schon VOR dem (hier gesprengten) Trading-Setup.
    assert (_live_dir / "bot.pid").read_text(
        encoding="utf-8") == str(os.getpid())
