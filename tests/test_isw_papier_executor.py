"""Papier-Executor: simulierte Kaeufe aus Feuerbefehlen, ohne Kauffaehigkeit.

Die Zusicherungen hier tragen die Korrektheit des Papier-Journals:

* Ein Befehl wird genau einmal verarbeitet, ueber Neustarts hinweg.
* Abgelaufene Befehle werden nie gebucht — sonst simuliert das Papier
  Fills, die der echte Executor nie bekommen haette.
* Der Wochendeckel gilt auch fuer Papier, rollend ueber 7 Tage.
* Das Modul hat strukturell keine Kauf-Faehigkeit: keine Order-API,
  keine Signatur, kein Key. Ein Test liest den Quelltext und prueft das.
"""

from __future__ import annotations

import ast
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from operations.pipeline import isw_papier_executor as px

JETZT = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


def befehl(*, slug="wird-krasnoiarske-fallen-july-31", zeit="2026-08-07T11:58:00Z",
           gueltig="2026-08-07T12:05:00Z", best_ask=0.40, max_preis=0.60,
           einsatz=100.0, art="feuerbefehl") -> str:
    return json.dumps({
        "art": art, "zeit_utc": zeit, "gueltig_bis_utc": gueltig,
        "markt_slug": slug, "token_id": "tok-1", "seite": "BUY_YES",
        "max_preis": max_preis, "einsatz_usdc": einsatz,
        "shares_bei_deckel": 166.67, "best_ask": best_ask,
        "ende_utc": "2026-08-31T00:00:00Z", "siedlung": "Krasnoiarske",
        "layer": "assessed", "vorlauf_s": 1123.0,
        "nach_ausfall_s": 0.0, "geschwister_maerkte": [],
    })


def kauf_zeile(*, slug="alt-markt", befehl_zeit="2026-08-06T10:00:00Z",
               zeit="2026-08-06T10:00:05Z", einsatz=100.0) -> str:
    return json.dumps({
        "art": "papier_kauf", "zeit_utc": zeit, "befehl_zeit_utc": befehl_zeit,
        "markt_slug": slug, "token_id": "tok-x", "seite": "BUY_YES",
        "preis": 0.5, "shares": 200.0, "einsatz_usdc": einsatz,
        "siedlung": "Irgendwo",
    })


def test_gueltiger_befehl_wird_papier_gekauft():
    neu, statistik = px.verarbeite([befehl()], [], jetzt=JETZT)
    assert statistik == {"kaeufe": 1, "ablehnungen": 0, "bekannt": 0,
                         "unlesbar": 0}
    kauf = neu[0]
    assert kauf.art == "papier_kauf"
    assert kauf.preis == 0.40          # der Ask aus dem Befehl, nie erfunden
    assert kauf.shares == 250.0        # 100 USDC / 0.40
    assert kauf.einsatz_usdc == 100.0
    assert kauf.befehl_zeit_utc == "2026-08-07T11:58:00Z"


def test_ablehnungen_der_kette_sind_protokoll_kein_auftrag():
    zeile = json.dumps({"art": "ablehnung", "zeit_utc": "2026-08-07T11:58:00Z",
                        "markt_slug": "x", "grund": "ask_ueber_deckel",
                        "detail": ""})
    neu, statistik = px.verarbeite([zeile], [], jetzt=JETZT)
    assert neu == []
    assert statistik["kaeufe"] == 0 and statistik["ablehnungen"] == 0


def test_abgelaufener_befehl_wird_abgelehnt_nicht_gebucht():
    alt = befehl(gueltig="2026-08-07T11:00:00Z")   # 60 min vor JETZT
    neu, statistik = px.verarbeite([alt], [], jetzt=JETZT)
    assert statistik["kaeufe"] == 0 and statistik["ablehnungen"] == 1
    assert neu[0].grund == "abgelaufen"


def test_derselbe_befehl_wird_nie_zweimal_gebucht():
    erste, _ = px.verarbeite([befehl()], [], jetzt=JETZT)
    journal = [json.dumps(asdict(e)) for e in erste]
    zweite, statistik = px.verarbeite([befehl()], journal, jetzt=JETZT)
    assert zweite == []
    assert statistik["bekannt"] == 1


def test_auch_ein_abgelehnter_befehl_gilt_als_verarbeitet():
    alt = befehl(gueltig="2026-08-07T11:00:00Z")
    erste, _ = px.verarbeite([alt], [], jetzt=JETZT)
    journal = [json.dumps(asdict(e)) for e in erste]
    zweite, statistik = px.verarbeite([alt], journal, jetzt=JETZT)
    assert zweite == []
    assert statistik["bekannt"] == 1


def test_wochendeckel_stoppt_den_fuenften_kauf():
    journal = [kauf_zeile(slug=f"markt-{i}",
                          zeit=f"2026-08-0{i + 1}T10:00:00Z",
                          befehl_zeit=f"2026-08-0{i + 1}T09:59:00Z")
               for i in range(4)]                      # 400 USDC diese Woche
    neu, statistik = px.verarbeite([befehl()], journal, jetzt=JETZT)
    assert statistik["kaeufe"] == 0 and statistik["ablehnungen"] == 1
    assert neu[0].grund == "wochendeckel_papier"


def test_alte_kaeufe_fallen_aus_dem_rollenden_fenster():
    vor_acht_tagen = px._iso(JETZT - timedelta(days=8))
    journal = [kauf_zeile(slug=f"markt-{i}", zeit=vor_acht_tagen,
                          befehl_zeit=vor_acht_tagen) for i in range(4)]
    neu, statistik = px.verarbeite([befehl()], journal, jetzt=JETZT)
    assert statistik["kaeufe"] == 1


def test_deckel_gilt_auch_innerhalb_eines_durchlaufs():
    befehle = [befehl(slug=f"markt-{i}", einsatz=100.0) for i in range(5)]
    neu, statistik = px.verarbeite(befehle, [], jetzt=JETZT)
    assert statistik["kaeufe"] == 4
    assert statistik["ablehnungen"] == 1
    assert [e.grund for e in neu if e.art == "papier_ablehnung"] == [
        "wochendeckel_papier"]


def test_ask_ueber_max_preis_wird_abgelehnt():
    neu, _ = px.verarbeite([befehl(best_ask=0.65, max_preis=0.60)], [],
                           jetzt=JETZT)
    assert neu[0].grund == "ask_ueber_max"


def test_unplausibler_preis_wird_abgelehnt():
    neu, _ = px.verarbeite([befehl(best_ask=0.0)], [], jetzt=JETZT)
    assert neu[0].grund == "preis_unplausibel"


def test_unlesbare_zeilen_stoppen_die_verarbeitung_nicht():
    zeilen = ['{"kaputt', "", befehl()]
    neu, statistik = px.verarbeite(zeilen, ['auch kaputt'], jetzt=JETZT)
    assert statistik["kaeufe"] == 1
    assert statistik["unlesbar"] == 2


def test_leere_befehlsdatei_ergibt_leeren_durchlauf(tmp_path: Path):
    statistik = px.durchlauf(tmp_path / "gibt-es-nicht.jsonl",
                             tmp_path / "journal.jsonl", jetzt=JETZT)
    assert statistik == {"kaeufe": 0, "ablehnungen": 0, "bekannt": 0,
                         "unlesbar": 0}
    assert not (tmp_path / "journal.jsonl").exists()   # nichts zu schreiben


def test_durchlauf_ist_idempotent_ueber_dateien(tmp_path: Path):
    quelle = tmp_path / "feuerbefehle.jsonl"
    journal = tmp_path / "papier_journal.jsonl"
    quelle.write_text(befehl() + "\n", encoding="utf-8")

    erste = px.durchlauf(quelle, journal, jetzt=JETZT)
    zweite = px.durchlauf(quelle, journal, jetzt=JETZT)
    assert erste["kaeufe"] == 1
    assert zweite == {"kaeufe": 0, "ablehnungen": 0, "bekannt": 1,
                      "unlesbar": 0}
    zeilen = journal.read_text(encoding="utf-8").strip().splitlines()
    assert len(zeilen) == 1
    eintrag = json.loads(zeilen[0])
    assert eintrag["art"] == "papier_kauf"
    assert eintrag["shares"] == 250.0


def test_modul_hat_strukturell_keine_kauffaehigkeit():
    """Kein Netz, keine Signatur, kein Key — als Import-Invariante.

    Dieselbe Idee wie der GET-only-Riegel in kalshi_auth: die Eigenschaft
    steht nicht nur in der Doku, sie ist zugesichert. Geprueft wird der
    Syntaxbaum, nicht der Text — der Docstring DARF das Wort Wallet
    enthalten, ein Import von web3 nicht.
    """
    baum = ast.parse(Path(px.__file__).read_text(encoding="utf-8"))
    importiert: set[str] = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            importiert.update(alias.name.split(".")[0]
                              for alias in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.module:
            importiert.add(knoten.module.split(".")[0])
    verboten = {"requests", "httpx", "urllib", "socket", "http",
                "websocket", "websockets", "web3", "py_clob_client",
                "eth_account", "aiohttp"}
    assert not (importiert & verboten), importiert & verboten
    # Erlaubte Aussenwelt: nur stdlib-Werkzeuge und die eigene Pipeline
    # (Feuerkette fuer den Deckel, config fuer STOP, watchdog fuer den
    # Not-Aus-Grund).
    assert importiert <= {"argparse", "json", "os", "sys", "time",
                          "dataclasses", "datetime", "pathlib",
                          "operations", "__future__"}, importiert

    quelle = Path(px.__file__).read_text(encoding="utf-8").lower()
    for token in ("private_key", "passphrase", "api_key"):
        assert token not in quelle, f"Key-Material-Token im Modul: {token}"


# ------------------------------------------------------ Watchdog-Betrieb

def test_live_lauf_schreibt_start_und_herzschlag(tmp_path: Path):
    quelle = tmp_path / "feuerbefehle.jsonl"
    quelle.write_text(befehl() + "\n", encoding="utf-8")
    live_dir = tmp_path / "isw_papier"

    px.live_lauf(quelle, tmp_path / "journal.jsonl", live_dir,
                 stop_datei=tmp_path / "STOP", max_zyklen=2,
                 schlaf=lambda s: None, jetzt_fn=lambda: JETZT)

    events = [json.loads(z) for z in
              (live_dir / "bot_events.jsonl").read_text(
                  encoding="utf-8").splitlines()]
    assert [e["art"] for e in events] == ["start", "herzschlag", "herzschlag"]
    assert events[1]["neu"] == 1     # der Kauf des ersten Zyklus
    assert events[2]["neu"] == 0     # zweiter Zyklus: schon verarbeitet


def test_live_lauf_gehorcht_der_stop_datei(tmp_path: Path):
    stop = tmp_path / "STOP"
    stop.write_text("halt", encoding="utf-8")
    live_dir = tmp_path / "isw_papier"

    rc = px.live_lauf(tmp_path / "leer.jsonl", tmp_path / "journal.jsonl",
                      live_dir, stop_datei=stop, max_zyklen=5,
                      schlaf=lambda s: None, jetzt_fn=lambda: JETZT)

    assert rc == 0
    events = [json.loads(z) for z in
              (live_dir / "bot_events.jsonl").read_text(
                  encoding="utf-8").splitlines()]
    assert [e["art"] for e in events] == ["start", "stop"]
    assert events[-1]["grund"] == "STOP-Datei"
    assert not (tmp_path / "journal.jsonl").exists()


def test_stop_waehrend_des_laufs_beendet_vor_dem_naechsten_durchlauf(
        tmp_path: Path):
    stop = tmp_path / "STOP"
    live_dir = tmp_path / "isw_papier"

    def schlaf_und_stop(_s: float) -> None:
        stop.write_text("halt", encoding="utf-8")

    px.live_lauf(tmp_path / "leer.jsonl", tmp_path / "journal.jsonl",
                 live_dir, stop_datei=stop, max_zyklen=5,
                 schlaf=schlaf_und_stop, jetzt_fn=lambda: JETZT)

    arten = [json.loads(z)["art"] for z in
             (live_dir / "bot_events.jsonl").read_text(
                 encoding="utf-8").splitlines()]
    assert arten == ["start", "herzschlag", "stop"]


def test_stop_grund_ist_der_notaus_grund_des_watchdogs():
    """Der Watchdog unterscheidet Not-Aus von regulaerem Ende am Grund.

    Schreibt der Executor einen anderen String, gilt sein STOP-Ende als
    "korrekt beendet" und er wird nach Aufheben der STOP-Datei nie wieder
    gestartet — der stille Ausfall von trump_july27 (29.-31.7.), nur
    andersherum.
    """
    from operations.pipeline.watchdog import NOTAUS_GRUND
    assert px.NOTAUS_GRUND == NOTAUS_GRUND == "STOP-Datei"
