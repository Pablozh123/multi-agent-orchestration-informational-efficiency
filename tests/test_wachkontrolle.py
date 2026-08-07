"""Tests für die Wachkontrolle: erkennt sie einen unbesetzten Messposten?

Der Leitfall ist der Ausfall vom 05.-07.08.2026: `isw_ukraine` verschwand
aus `watchdog.json`, der Watchdog meldete weiter „alle betreuten Bots
leben", 26,7 h Messdaten waren verloren. Genau dieser Zustand muss hier
einen kritischen Befund erzeugen.

Kein Netz, kein echtes `data/live` — alles läuft gegen `tmp_path`.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from operations.pipeline import wachkontrolle as wk

SOLL = {
    "isw_ukraine": {
        "modul": "isw_rekorder",
        "ende_utc": "2026-12-31T23:59:59Z",
        "max_herzschlag_s": 1800,
    }
}


def _live(tmp_path: Path, managed: dict | None = None,
          herzschlag_alter_s: float | None = 60.0,
          art: str = "herzschlag") -> Path:
    """Baut ein data/live-Verzeichnis mit watchdog.json und Herzschlag."""
    live = tmp_path / "live"
    (live / "isw_ukraine").mkdir(parents=True, exist_ok=True)
    if managed is not None:
        (live / "watchdog.json").write_text(
            json.dumps({"managed": managed}), encoding="utf-8")
    if herzschlag_alter_s is not None:
        zeit = datetime.now(UTC) - timedelta(seconds=herzschlag_alter_s)
        (live / "isw_ukraine" / "bot_events.jsonl").write_text(
            json.dumps({"wall_ts_utc": zeit.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "art": art}) + "\n", encoding="utf-8")
    return live


def _pruefe(live: Path, soll: dict | None = None) -> list[wk.Befund]:
    return wk.pruefe(soll if soll is not None else SOLL,
                     watchdog_json=live / "watchdog.json", live_root=live)


def _codes(befunde: list[wk.Befund]) -> set[str]:
    return {b.code for b in befunde}


# --------------------------------------------------------- der gesunde Fall


def test_besetzter_und_wacher_posten_erzeugt_keinen_befund(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}})
    assert _pruefe(live) == []


def test_ohne_sollbesetzung_wird_nichts_geprueft(tmp_path) -> None:
    # Ein Repo ohne Messposten darf keine Befunde erfinden.
    live = _live(tmp_path, managed={})
    assert wk.pruefe({}, watchdog_json=live / "watchdog.json",
                     live_root=live) == []


# ------------------------------------------------------ der Leitfall 05.08.


def test_fehlender_posten_ist_kritisch(tmp_path) -> None:
    # Genau der Zustand vom 5.8.: watchdog.json auf Juli-Stand
    # zurueckgesetzt, isw_ukraine nicht mehr enthalten.
    live = _live(tmp_path, managed={
        "elon_july13": {"modul": "elon_bot",
                        "ende_utc": "2026-07-20T04:00:00Z", "aktiv": True}})
    befunde = _pruefe(live)
    assert _codes(befunde) == {"posten_fehlt"}
    assert befunde[0].schwere == wk.KRITISCH
    assert befunde[0].posten == "isw_ukraine"


def test_fehlender_posten_schlaegt_auch_bei_frischem_herzschlag_an(
        tmp_path) -> None:
    # Der Rekorder lief am 5.8. noch zwei Stunden weiter, bevor er starb.
    # In diesem Fenster war der Herzschlag frisch UND der Posten schon
    # unbesetzt — genau dann muss die Kontrolle bereits anschlagen.
    live = _live(tmp_path, managed={}, herzschlag_alter_s=10.0)
    assert _codes(_pruefe(live)) == {"posten_fehlt"}


def test_rueckgabecode_meldet_kritische_befunde(tmp_path) -> None:
    live = _live(tmp_path, managed={})
    assert wk.rueckgabecode(_pruefe(live)) == 1
    assert wk.rueckgabecode([]) == 0


# ------------------------------------------------ weitere stille Ausfaelle


def test_deaktivierter_posten_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": False}})
    assert _codes(_pruefe(live)) == {"posten_deaktiviert"}


def test_abgelaufenes_fenster_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-01-01T00:00:00Z", "aktiv": True}})
    assert _codes(_pruefe(live)) == {"fenster_abgelaufen"}


def test_zu_kurzes_fenster_warnt_vor_kuenftigem_stillstand(tmp_path) -> None:
    # Betreuung endet frueher als die Messung geplant ist: noch laeuft
    # alles, aber der Stillstand steht fest. Warnung, nicht kritisch.
    ende = (datetime.now(UTC) + timedelta(days=3)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder", "ende_utc": ende,
                        "aktiv": True}})
    befunde = _pruefe(live)
    assert _codes(befunde) == {"fenster_zu_kurz"}
    assert befunde[0].schwere == wk.WARNUNG
    assert wk.rueckgabecode(befunde) == 2


def test_falsches_modul_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "bot",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}})
    assert _codes(_pruefe(live)) == {"modul_abweichung"}


def test_unlesbares_fenster_warnt(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder", "ende_utc": "irgendwann",
                        "aktiv": True}})
    befunde = _pruefe(live)
    assert _codes(befunde) == {"fenster_unlesbar"}
    assert befunde[0].schwere == wk.WARNUNG


# ------------------------------------------------------------- Herzschlag


def test_alter_herzschlag_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}},
        herzschlag_alter_s=95952.0)  # die 26,7 h des Ausfalls
    befunde = _pruefe(live)
    assert _codes(befunde) == {"herzschlag_alt"}
    assert "26.7 h" in befunde[0].text


def test_neustart_innerhalb_der_toleranz_ist_kein_befund(tmp_path) -> None:
    # 15 min Stille: der Watchdog gilt als tot (STALE_S 600 s) und startet
    # gerade neu. Die Kontrolle darf da noch nicht anschlagen, sonst
    # meldet sie jeden regulaeren Neustart.
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}},
        herzschlag_alter_s=900.0)
    assert _pruefe(live) == []


def test_fehlender_herzschlag_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}},
        herzschlag_alter_s=None)
    assert _codes(_pruefe(live)) == {"herzschlag_fehlt"}


def test_beendeter_posten_ist_kritisch(tmp_path) -> None:
    # "stop"/"fertig" heisst fuer den Watchdog: nicht neu starten. Fuer
    # einen Dauer-Messposten ist das ein stiller Tod.
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}},
        art="stop")
    assert _codes(_pruefe(live)) == {"posten_beendet"}


# ------------------------------------------------------ watchdog.json selbst


def test_fehlende_watchdog_json_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed=None)
    befunde = _pruefe(live)
    assert "watchdog_json_fehlt" in _codes(befunde)
    assert any(b.posten == "*" for b in befunde)


def test_kaputte_watchdog_json_ist_kritisch(tmp_path) -> None:
    # Der Watchdog faellt dann auf DEFAULT_MANAGED zurueck, in dem kein
    # Messposten steht — der Posten ist unbesetzt, nicht nur "unklar".
    live = _live(tmp_path, managed={})
    (live / "watchdog.json").write_text("{kein json", encoding="utf-8")
    assert "watchdog_json_unlesbar" in _codes(_pruefe(live))


def test_stop_datei_ist_kritisch(tmp_path) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}})
    (live / "STOP").write_text("", encoding="utf-8")
    assert _codes(_pruefe(live)) == {"stop_datei"}


# ------------------------------------------------------------ Sollbesetzung


def test_sollbesetzung_wird_gelesen(tmp_path) -> None:
    pfad = tmp_path / "wachposten.json"
    pfad.write_text(json.dumps({"posten": SOLL}), encoding="utf-8")
    assert wk.lade_wachposten(pfad)["isw_ukraine"]["modul"] == "isw_rekorder"


def test_nicht_erwartete_posten_werden_uebersprungen(tmp_path) -> None:
    # Ein pensionierter Posten bleibt als Beleg stehen, ohne zu alarmieren.
    pfad = tmp_path / "wachposten.json"
    pfad.write_text(json.dumps({"posten": {
        "isw_ukraine": SOLL["isw_ukraine"],
        "alt_july13": {"modul": "elon_bot", "erwartet": False},
    }}), encoding="utf-8")
    assert set(wk.lade_wachposten(pfad)) == {"isw_ukraine"}


def test_fehlende_sollbesetzung_ist_leer(tmp_path) -> None:
    assert wk.lade_wachposten(tmp_path / "gibtsnicht.json") == {}


def test_echte_sollbesetzung_des_repos_ist_lesbar() -> None:
    # Die versionierte Datei ist der Zweck der ganzen Uebung: eine kaputte
    # Sollbesetzung entwertet die Kontrolle still.
    posten = wk.lade_wachposten(wk.STANDARD_WACHPOSTEN)
    assert "isw_ukraine" in posten
    assert posten["isw_ukraine"]["modul"] == "isw_rekorder"


# -------------------------------------------------------------------- CLI


def test_cli_meldet_fehlenden_posten_mit_code_1(tmp_path, capsys) -> None:
    live = _live(tmp_path, managed={})
    soll = tmp_path / "wachposten.json"
    soll.write_text(json.dumps({"posten": SOLL}), encoding="utf-8")
    code = wk.main(["--wachposten", str(soll), "--live-root", str(live)])
    assert code == 1
    assert "KRITISCH isw_ukraine" in capsys.readouterr().out


def test_cli_json_liefert_maschinenlesbare_befunde(tmp_path, capsys) -> None:
    live = _live(tmp_path, managed={})
    soll = tmp_path / "wachposten.json"
    soll.write_text(json.dumps({"posten": SOLL}), encoding="utf-8")
    wk.main(["--wachposten", str(soll), "--live-root", str(live), "--json"])
    befunde = json.loads(capsys.readouterr().out)
    assert [b["code"] for b in befunde] == ["posten_fehlt"]


def test_cli_ohne_sollbesetzung_meldet_aufrufproblem(tmp_path) -> None:
    # Tippfehler im Pfad darf nicht als "alles in Ordnung" durchgehen.
    live = _live(tmp_path, managed={})
    assert wk.main(["--wachposten", str(tmp_path / "weg.json"),
                    "--live-root", str(live)]) == 3


def test_cli_meldet_besetzte_posten_mit_code_0(tmp_path, capsys) -> None:
    live = _live(tmp_path, managed={
        "isw_ukraine": {"modul": "isw_rekorder",
                        "ende_utc": "2026-12-31T23:59:59Z", "aktiv": True}})
    soll = tmp_path / "wachposten.json"
    soll.write_text(json.dumps({"posten": SOLL}), encoding="utf-8")
    assert wk.main(["--wachposten", str(soll),
                    "--live-root", str(live)]) == 0
    assert "besetzt" in capsys.readouterr().out


# ------------------------------------------- Einbindung in den Watchdog
# Die Kontrolle muss dort laufen, wo der Ausfall unsichtbar blieb: im
# 5-Minuten-Durchlauf des Watchdogs selbst. Der Task lief am 5.8. korrekt
# durch — nur seine Liste war falsch.


def _watchdog_auf_tmp(tmp_path, monkeypatch, live: Path, soll: Path):
    from operations.pipeline import watchdog

    monkeypatch.setattr(watchdog, "LIVE_ROOT", live)
    monkeypatch.setattr(watchdog, "WATCHDOG_JSON", live / "watchdog.json")
    monkeypatch.setattr(watchdog, "WATCHDOG_LOG", live / "watchdog.log")
    monkeypatch.setattr(watchdog, "STOP_FILE", live / "STOP")
    monkeypatch.setattr(watchdog, "WACHPOSTEN_JSON", soll)
    return watchdog


def _soll_datei(tmp_path: Path) -> Path:
    pfad = tmp_path / "wachposten.json"
    pfad.write_text(json.dumps({"posten": SOLL}), encoding="utf-8")
    return pfad


def test_watchdog_durchlauf_meldet_fehlenden_posten(
        tmp_path, monkeypatch) -> None:
    live = _live(tmp_path, managed={})  # isw_ukraine ist herausgefallen
    watchdog = _watchdog_auf_tmp(tmp_path, monkeypatch, live,
                                 _soll_datei(tmp_path))
    watchdog.durchlauf(dry_run=True)
    log = (live / "watchdog.log").read_text(encoding="utf-8")
    assert "alle betreuten Bots leben" in log  # die alte, wahre Meldung
    assert "WACHKONTROLLE KRITISCH isw_ukraine" in log  # die neue Warnung


def test_watchdog_meldet_auch_bei_gesetzter_stop_datei(
        tmp_path, monkeypatch) -> None:
    live = _live(tmp_path, managed={})
    (live / "STOP").write_text("", encoding="utf-8")
    watchdog = _watchdog_auf_tmp(tmp_path, monkeypatch, live,
                                 _soll_datei(tmp_path))
    watchdog.durchlauf(dry_run=True)
    assert "WACHKONTROLLE" in (live / "watchdog.log").read_text(
        encoding="utf-8")


def test_kaputte_wachkontrolle_stoert_den_watchdog_nicht(
        tmp_path, monkeypatch) -> None:
    # Die Kontrolle ist reine Meldung: sie darf einen Neustart nie
    # verhindern, auch wenn ihre eigene Datei Schrott ist.
    live = _live(tmp_path, managed={})
    soll = tmp_path / "wachposten.json"
    soll.write_text("{kaputt", encoding="utf-8")
    watchdog = _watchdog_auf_tmp(tmp_path, monkeypatch, live, soll)
    watchdog.durchlauf(dry_run=True)
    log = (live / "watchdog.log").read_text(encoding="utf-8")
    assert "Wachkontrolle uebersprungen" in log
