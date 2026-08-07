"""Tests fuer den Neustart nach Not-Aus (Kill-Switch data/live/STOP).

Ausfall 29.-31.7.: trump_july27 stieg um 2026-07-29T14:05:20Z per
STOP-Datei aus (Not-Aus im Zuge des P&G-Laufs) und schrieb
{"art": "stop", "grund": "STOP-Datei"}. Der Watchdog unterdrueckte den
Neustart bei JEDEM stop-Event und lief deshalb auch nach dem Aufheben
des Kill-Switches (bot_stop_aufheben.cmd) nie wieder an — 48 h
Blindflug, obwohl die Handelsperiode bis 2026-08-03T03:59:59Z lief und
watchdog.json das Profil mit aktiv=true fuehrte. Zweiter Teil des
Schadens: das Log meldete waehrenddessen "alle betreuten Bots leben".

Unterscheidungsmerkmal ist der Grund im stop-Event: nur
grund="STOP-Datei" ist ein Not-Aus. Ein stop OHNE diesen Grund heisst
weiter "absichtlich beendet" (Ctrl+C-Ende des ISW-Rekorders) und bleibt
unterdrueckt.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

import pytest

from operations.pipeline import watchdog
# Die Entwarnung des Watchdogs, wortgenau. Der Teilstring allein reicht
# nicht: wachkontrolle.py zitiert denselben Satz in ihrer Erklaerung, warum
# ein herausgefallener Posten frueher unbemerkt blieb — ein Test, der nur
# auf das Zitat trifft, faellt beim ersten gemeinsamen Lauf beider Module.
ENTWARNUNG = "alle betreuten Bots leben (oder korrekt beendet)."

LEBT_S = 60      # frisch genug fuer den Heartbeat (< STALE_S)
STALE_TS = "2026-01-01T00:00:00Z"  # uralt -> stale


@pytest.fixture(autouse=True)
def _isolierte_pfade(tmp_path, monkeypatch):
    """Alle Watchdog-Pfade auf tmp umbiegen; nie echte Prozesse anfassen."""
    live = tmp_path / "live"
    monkeypatch.setattr(watchdog, "LIVE_ROOT", live)
    monkeypatch.setattr(watchdog, "WATCHDOG_JSON", live / "watchdog.json")
    monkeypatch.setattr(watchdog, "WATCHDOG_LOG", live / "watchdog.log")
    monkeypatch.setattr(watchdog, "WATCHDOG_LOCK", live / "watchdog.lock")
    monkeypatch.setattr(watchdog, "STOP_FILE", live / "STOP")
    monkeypatch.setattr(watchdog, "_pid_lebt", lambda pid: False)
    # Prozessliste ausser Betrieb: hier geht es nur um die Zustands-
    # erkennung, nicht um den Doppelstart-Gegencheck (eigene Datei).
    monkeypatch.setattr(watchdog, "_python_prozesse", lambda: [])
    yield
    watchdog.instanz_lock_freigeben()


def _schreibe_managed(cfg: dict) -> None:
    watchdog.WATCHDOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    watchdog.WATCHDOG_JSON.write_text(
        json.dumps({"managed": cfg}), encoding="utf-8")


def _schreibe_events(profil: str, events: list[dict]) -> None:
    d = watchdog.LIVE_ROOT / profil
    d.mkdir(parents=True, exist_ok=True)
    (d / "bot_events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")


def _vor_sekunden(sekunden: float) -> str:
    ts = datetime.now(timezone.utc) - timedelta(seconds=sekunden)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _sammle_starts(monkeypatch) -> list[tuple[str, str]]:
    starts: list[tuple[str, str]] = []
    monkeypatch.setattr(watchdog, "_starte",
                        lambda p, m: starts.append((p, m)))
    return starts


def _log_text() -> str:
    return watchdog.WATCHDOG_LOG.read_text(encoding="utf-8")


# ------------------------------------------- Klassifikation der Endzustaende


@pytest.mark.parametrize("art, grund, erwartet", [
    ("fertig", "periodenende", True),      # Marktperiode vorbei
    ("fertig", None, True),
    ("stop", None, True),                  # Ctrl+C (ISW-Rekorder)
    ("stop", "operator", True),            # anderer Stopp-Grund
    ("stop", "STOP-Datei", False),         # Not-Aus -> weiter betreuen
    ("buchlog", None, False),              # laufender Betrieb
    (None, None, False),                   # kein/unlesbares Log
])
def test_regulaer_beendet_trennt_notaus_vom_laufende(
        art, grund, erwartet) -> None:
    assert watchdog._regulaer_beendet(art, grund) is erwartet


def test_letztes_event_liefert_grund_mit() -> None:
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": _vor_sekunden(LEBT_S), "art": "buchlog"},
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"},
    ])
    art, alter, grund = watchdog._letztes_event("trump_july27")
    assert (art, grund) == ("stop", "STOP-Datei")
    assert alter is not None and alter > 0


def test_letztes_event_ohne_log_ist_dreimal_none() -> None:
    assert watchdog._letztes_event("nie_gelaufen") == (None, None, None)


# ------------------------------------------------------- Neustart nach Not-Aus


def test_notaus_gestoppter_bot_wird_neu_gestartet(monkeypatch) -> None:
    # Der Vorfall selbst: STOP-Datei aufgehoben, Handelsperiode laeuft
    # noch -> der Bot muss wieder anlaufen.
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == [("trump_july27", "trump_bot")]
    log = _log_text()
    assert "NOT-AUS-STOPP" in log
    assert ENTWARNUNG not in log


def test_notaus_stopp_zaehlt_nicht_als_heartbeat(monkeypatch) -> None:
    # Regression: ein FRISCHES Not-Aus-stop-Event darf den Bot nicht
    # bis STALE_S als lebend durchwinken — der Prozess ist bereits weg.
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": _vor_sekunden(LEBT_S), "art": "stop",
         "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == [("trump_july27", "trump_bot")]


def test_notaus_stopp_bleibt_liegen_solange_die_stop_datei_da_ist(
        monkeypatch) -> None:
    # Kill-Switch noch gesetzt: der Watchdog startet grundsaetzlich
    # nichts — und behauptet auch nicht, alles laufe.
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    watchdog.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    watchdog.STOP_FILE.write_text("", encoding="utf-8")
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    log = _log_text()
    assert "STOP-Datei aktiv" in log
    assert ENTWARNUNG not in log


def test_notaus_stopp_nach_periodenende_bleibt_unangetastet(
        monkeypatch) -> None:
    # ende_utc erreicht -> das Profil wird gar nicht mehr betreut.
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2026-07-30T04:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    assert "kein betreutes Profil im Zeitfenster." in _log_text()


def test_regulaeres_ende_startet_weiterhin_nicht_neu(monkeypatch) -> None:
    # Gegenprobe: das Verhalten fuer korrekt beendete Laeufe bleibt.
    # "stop" ohne Not-Aus-Grund ist das Ctrl+C-Ende des ISW-Rekorders.
    _schreibe_managed({
        "allin_july31": {"modul": "bot", "ende_utc": "2999-01-01T00:00:00Z",
                         "aktiv": True},
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2999-01-01T00:00:00Z", "aktiv": True},
    })
    _schreibe_events("allin_july31", [
        {"wall_ts_utc": STALE_TS, "art": "fertig", "grund": "periodenende"}])
    _schreibe_events("isw_ukraine", [{"wall_ts_utc": STALE_TS, "art": "stop"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    assert ENTWARNUNG in _log_text()


def test_notaus_stopp_im_dry_run_wird_nur_gemeldet(monkeypatch) -> None:
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=True)
    assert starts == []
    log = _log_text()
    assert "dry-run, kein Start" in log
    assert ENTWARNUNG not in log


# ---------------------------------------------------- Ehrlichkeit der Logzeile


def test_entwarnung_nur_wenn_jedes_profil_versorgt_ist(monkeypatch) -> None:
    # Ein lebendes Schwesterprofil darf die Entwarnung nicht ausloesen,
    # solange ein anderes betreutes Profil offen ist.
    _schreibe_managed({
        "elon_july27": {"modul": "elon_bot", "ende_utc": "2999-01-01T00:00:00Z",
                        "aktiv": True},
        "trump_july27": {"modul": "trump_bot",
                         "ende_utc": "2999-01-01T00:00:00Z", "aktiv": True},
    })
    _schreibe_events("elon_july27", [
        {"wall_ts_utc": _vor_sekunden(LEBT_S), "art": "buchlog"}])
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == [("trump_july27", "trump_bot")]
    assert ENTWARNUNG not in _log_text()


def test_keine_entwarnung_wenn_der_start_uebersprungen_wird(
        monkeypatch) -> None:
    # Doppelstart-Verdacht: der Bot laeuft danach immer noch nicht —
    # die Zeile darf trotzdem nicht behaupten, alles lebe.
    _schreibe_managed({"trump_july27": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": True}})
    _schreibe_events("trump_july27", [
        {"wall_ts_utc": "2026-07-29T14:05:20Z", "art": "stop",
         "grund": "STOP-Datei"}])
    monkeypatch.setattr(watchdog, "_python_prozesse", lambda: [
        (4242, 4000, '"python.exe" -m operations.pipeline.trump_bot --live')])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    log = _log_text()
    assert "DOPPELSTART-VERDACHT" in log
    assert ENTWARNUNG not in log


def test_entwarnung_bei_ausschliesslich_inaktiven_profilen(
        monkeypatch) -> None:
    # aktiv=false (abgelaufene Woche, Historie): nichts zu betreuen —
    # dann behauptet der Watchdog auch nicht, Bots wuerden leben.
    _schreibe_managed({"trump_july20": {
        "modul": "trump_bot", "ende_utc": "2999-01-01T00:00:00Z",
        "aktiv": False}})
    _schreibe_events("trump_july20", [
        {"wall_ts_utc": STALE_TS, "art": "stop", "grund": "STOP-Datei"}])
    starts = _sammle_starts(monkeypatch)
    watchdog.durchlauf(dry_run=False)
    assert starts == []
    log = _log_text()
    assert "kein betreutes Profil im Zeitfenster." in log
    assert ENTWARNUNG not in log


# ------------------------------------------------- Erzeuger des stop-Grundes


@pytest.mark.parametrize("modul", ["bot", "elon_bot", "trump_bot"])
def test_bots_schreiben_den_notaus_grund_ins_stop_event(modul) -> None:
    """Der Watchdog kann nur unterscheiden, was die Bots auch schreiben.

    Alle drei Kill-Switch-Ausstiege muessen `grund` gesetzt haben, sonst
    liefe der Not-Aus-Stopp wieder als regulaeres Laufende durch.
    """
    quelle = (watchdog.REPO_ROOT / "operations" / "pipeline"
              / f"{modul}.py").read_text(encoding="utf-8")
    stellen = re.findall(r'_schreibe_event\(\s*"stop"\s*,(.{0,80})',
                         quelle, re.S)
    assert stellen, f"{modul}.py schreibt gar kein stop-Event mehr"
    for daten in stellen:
        assert watchdog.NOTAUS_GRUND in daten, (
            f"{modul}.py schreibt ein stop-Event ohne Not-Aus-Grund — der "
            f"Watchdog haelt es dann faelschlich fuer ein regulaeres Ende")
