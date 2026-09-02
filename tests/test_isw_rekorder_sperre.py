"""Tests fuer die quellseitige Sperre des ISW-Rekorders (HTTP 403).

Leitfall ist der Betriebsvorfall vom 01.09.2026: der ArcGIS-Origin wies
20:00-21:01 UTC jede Anfrage mit 403 ab, der 1-s-Takt lief ungebremst
durch und schrieb 1674 Fehlerzeilen. Seither: EIN `sperre`-Ereignis beim
Beginn, eskalierende Abkuehlpause, EIN `sperre_ende` beim ersten Erfolg,
Herzschlaege waehrend der Pause, `letzter_zyklus_ts` friert ein.

Kein Netzzugriff — Karte und Polymarket sind Attrappen.
"""
from __future__ import annotations

import json

from operations.pipeline import isw_rekorder as rek
from operations.pipeline.isw_karten_watch import ISWFehler
from tests.test_isw_rekorder import (
    QUADRAT,
    _KarteAttrappe,
    _LeserAttrappe,
    _ziel,
    _zustand,
)


class _AbweisendeKarte(_KarteAttrappe):
    """Karte, die je nach Schalter mit einem festen HTTP-Status abweist."""

    def __init__(self, status: int | None = 403, **kw):
        super().__init__({"infiltration": 1, "advance": 1,
                          "control": 1, "gains24h": 1}, {}, **kw)
        self.status = status
        self.aufrufe = 0

    def layer_stand(self, layer):
        self.aufrufe += 1
        if self.status is not None:
            raise ISWFehler(self.status, "Forbidden")
        return super().layer_stand(layer)


def _zeilen(pfad):
    return [json.loads(z) for z in
            pfad.read_text(encoding="utf-8").strip().splitlines()]


# ------------------------------------------------------------------ Sperre

def test_sperre_eskaliert_und_deckelt():
    sperre = rek.Sperre()
    assert not sperre.aktiv
    assert sperre.treffer(403, 1000.0) is True      # Beginn
    assert sperre.aktiv and sperre.wartezeit_s == rek.SPERRE_START_S
    assert sperre.treffer(403, 1060.0) is False     # weiter, nicht neu
    assert sperre.wartezeit_s == 2 * rek.SPERRE_START_S
    for _ in range(10):
        sperre.treffer(403, 2000.0)
    assert sperre.wartezeit_s == rek.SPERRE_MAX_S
    info = sperre.ende(5000.0)
    assert info == {"status": 403, "dauer_s": 4000.0, "versuche": 12}
    assert not sperre.aktiv and sperre.wartezeit_s == rek.SPERRE_START_S


def test_403_erzeugt_genau_ein_sperre_ereignis(tmp_path):
    """Drei gesperrte Zyklen -> eine `sperre`-Zeile, keine `fehler`-Zeilen,
    Layer-Schleife bricht beim ersten 403 ab (nicht vier Treffer je Zyklus)."""
    protokoll = tmp_path / "p.jsonl"
    karte = _AbweisendeKarte(403)
    zustand = _zustand(letzter_zyklus_ts=rek._jetzt_utc().timestamp())
    sperre = rek.Sperre()
    for _ in range(3):
        rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                      protokoll, sperre=sperre)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["sperre"]
    assert zeilen[0]["status"] == 403
    assert zeilen[0]["wartezeit_s"] == rek.SPERRE_START_S
    assert karte.aufrufe == 3, "je gesperrtem Zyklus genau ein Versuch"
    assert sperre.versuche == 3
    assert sperre.wartezeit_s == 4 * rek.SPERRE_START_S


def test_letzter_zyklus_friert_waehrend_der_sperre_ein(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    vorher = rek._jetzt_utc().timestamp() - 30.0
    zustand = _zustand(letzter_zyklus_ts=vorher)
    rek.durchlauf(_AbweisendeKarte(403), _LeserAttrappe(), [_ziel()],
                  zustand, protokoll, sperre=rek.Sperre())
    assert zustand["letzter_zyklus_ts"] == vorher


def test_erfolg_beendet_sperre_und_meldet_die_luecke(tmp_path):
    """Nach der Sperre: `sperre_ende` mit Dauer/Versuchen, danach
    `ausfall_erkannt` ueber die GESAMTE Sperrdauer (nicht nur den letzten
    Schlaf), damit das erste Ereignis danach als unsicher markiert ist."""
    protokoll = tmp_path / "p.jsonl"
    karte = _AbweisendeKarte(403)
    lange_her = rek._jetzt_utc().timestamp() - 3600.0
    zustand = _zustand(letzter_zyklus_ts=lange_her)
    sperre = rek.Sperre()
    # Die Sperre begann VOR dem Zyklus (kein ausfall_erkannt am Zyklusstart)
    sperre.treffer(403, lange_her + 5.0)
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand, protokoll,
                  sperre=sperre)
    assert not protokoll.exists(), "gesperrter Zyklus schreibt nichts"
    karte.status = None                      # Quelle antwortet wieder
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand, protokoll,
                  sperre=sperre)
    zeilen = _zeilen(protokoll)
    arten = [z["art"] for z in zeilen]
    assert arten[:2] == ["sperre_ende", "ausfall_erkannt"]
    assert zeilen[0]["versuche"] == 2
    assert zeilen[0]["dauer_s"] >= 3590.0
    assert zeilen[1]["luecke_s"] >= 3590.0
    assert zeilen[1]["hinweis"].startswith("Nach Sperre:")
    assert not sperre.aktiv
    assert zustand["letzter_zyklus_ts"] > lange_her


def test_ereignis_direkt_nach_sperre_traegt_nach_ausfall_s(tmp_path):
    """Der T+0-Preis nach einer Sperre ist unsicher — genau wie nach
    jedem anderen Ausfall (Amendment A3)."""
    from operations.pipeline.isw_karten_watch import ISWFlaeche

    protokoll = tmp_path / "p.jsonl"
    lange_her = rek._jetzt_utc().timestamp() - 3600.0
    zustand = _zustand(letzter_zyklus_ts=lange_her,
                       layer_stand={"infiltration": 1, "advance": 1,
                                    "control": 1, "gains24h": 1})
    flaeche = ISWFlaeche("infiltration", 7, QUADRAT, creation_ms=1)
    karte = _AbweisendeKarte(None, )
    karte._staende["infiltration"] = 2
    karte._flaechen["infiltration"] = [flaeche]
    sperre = rek.Sperre()
    sperre.treffer(403, lange_her + 5.0)
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand, protokoll,
                  sperre=sperre)
    kandidaten = [z for z in _zeilen(protokoll) if z["art"] == "kandidat_treffer"]
    assert len(kandidaten) == 1
    assert kandidaten[0]["nach_ausfall_s"] >= 3590.0


def test_429_bleibt_ein_fehler_je_layer_ohne_sperre(tmp_path):
    """Drosselung (429) geht den alten Weg: Client-Backoff, dann eine
    `fehler`-Zeile je Layer — keine Sperre, alle vier Layer versucht."""
    protokoll = tmp_path / "p.jsonl"
    karte = _AbweisendeKarte(429)
    sperre = rek.Sperre()
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], _zustand(), protokoll,
                  sperre=sperre)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["fehler"] * 4
    assert {z["status"] for z in zeilen} == {429}
    assert not sperre.aktiv
    assert karte.aufrufe == 4


def test_ohne_sperre_objekt_bleibt_403_ein_fehler(tmp_path):
    """Rueckwaertskompatibel: Aufrufer ohne `sperre` (Tests, --einmal-
    Werkzeuge) sehen das alte Verhalten."""
    protokoll = tmp_path / "p.jsonl"
    rek.durchlauf(_AbweisendeKarte(403), _LeserAttrappe(), [_ziel()],
                  _zustand(), protokoll)
    assert [z["art"] for z in _zeilen(protokoll)] == ["fehler"] * 4


# --------------------------------------------------------------- Schlafen

def test_schlafe_schreibt_herzschlaege_zwischen_den_scheiben(monkeypatch):
    """600 s Pause in 60-s-Scheiben: 10 Schlaefe, 9 Herzschlaege dazwischen
    — der Watchdog (STALE_S 600) sieht den Rekorder nie als tot."""
    schlaefe: list[float] = []
    monkeypatch.setattr(rek.time, "sleep", schlaefe.append)
    herzen = []
    rek._schlafe(600.0, herzschlag=lambda: herzen.append(1), scheibe_s=60.0)
    assert schlaefe == [60.0] * 10
    assert len(herzen) == 9


def test_schlafe_kurze_pause_ohne_herzschlag(monkeypatch):
    schlaefe: list[float] = []
    monkeypatch.setattr(rek.time, "sleep", schlaefe.append)
    herzen = []
    rek._schlafe(45.0, herzschlag=lambda: herzen.append(1), scheibe_s=60.0)
    assert schlaefe == [45.0]
    assert herzen == []
