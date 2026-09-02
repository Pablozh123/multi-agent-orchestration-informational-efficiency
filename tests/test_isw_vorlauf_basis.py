"""Tests fuer die informative Zweitklassifikation der ISW-Auswertung
(Basis-Anker = Best Bid bei Erkennung, Amendment A2) und die
Vollueberdeckungs-Tabelle (capture-all-of).

Leitfall Hannivka 01.09.2026: T+0-Mid 0.885 = (bid 0.79 + ask 0.98) / 2
ist ein Artefakt der gezogenen Ask-Seite; der Markt stand vor der
Publikation bei 0.79.
"""
from __future__ import annotations

import json

from operations.analysis import isw_vorlauf_auswertung as ava
from tests.test_isw_vorlauf_auswertung import _bestaetigt, _kandidat, _nachfassung

HANNIVKA_BUCH = {"best_bid": 0.79, "best_ask": 0.98,
                 "usd_bis_030": 0, "usd_bis_050": 0}


def test_klasse_basis_nimmt_den_best_bid():
    assert ava.klasse_basis_aus(0.885, 0.79) == "teilweise"
    assert ava.klasse_basis_aus(0.885, None) == "antizipiert"   # kein Buch
    assert ava.klasse_basis_aus(0.885, 0.79, nach_ausfall_s=700) == "unsicher"
    assert ava.klasse_basis_aus(None, None) == "unbekannt"


def test_hannivka_ist_nach_mid_antizipiert_und_nach_basis_teilweise():
    zeilen = [_kandidat(slug="sep", preis=0.885, buch=HANNIVKA_BUCH),
              _bestaetigt(slug="sep")]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    e = ereignisse[0]
    assert e.klasse == "antizipiert"
    assert e.best_bid_t0 == 0.79
    assert e.klasse_basis == "teilweise"
    assert e.kriterium == "beruehrung"


def test_siedlungsereignis_traegt_median_basis():
    """Zwei Deadlines derselben Siedlung: Basis-Klasse ueber den Median der
    Best Bids — der Dezember-Markt (0.941) zieht Hannivka auf Siedlungs-
    ebene wieder ueber 0.85."""
    zeilen = [
        _kandidat(slug="sep", preis=0.885, buch=HANNIVKA_BUCH),
        _bestaetigt(slug="sep"),
        _kandidat(slug="dez", preis=0.949,
                  buch={"best_bid": 0.941, "best_ask": 0.957,
                        "usd_bis_030": 0, "usd_bis_050": 0}),
        _bestaetigt(slug="dez"),
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    physisch = ava.baue_siedlungsereignisse(ereignisse)
    assert len(physisch) == 1
    assert physisch[0].preis_basis_t0 == 0.8655
    assert physisch[0].klasse_basis == "antizipiert"
    assert physisch[0].klasse == "antizipiert"


def test_zusammenfassung_weist_basis_anteil_informativ_aus():
    zeilen = [
        _kandidat(slug="a", preis=0.60,
                  buch={"best_bid": 0.40, "best_ask": 0.80,
                        "usd_bis_030": 0, "usd_bis_050": 0}),
        _bestaetigt(slug="a"),
        _kandidat(slug="b", preis=0.90),
        _bestaetigt(slug="b"),
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    ereignisse[0].siedlung = "Ort A"
    ereignisse[1].siedlung = "Ort B"
    z = ava.fasse_zusammen(ereignisse)
    assert z["anteil_ueberraschung"] == 0.0          # Mid 0.60 = teilweise
    assert z["anteil_ueberraschung_basis"] == 0.5    # Bid 0.40 = ueberraschung
    assert z["klassen_siedlungsereignisse_basis"] == {"ueberraschung": 1,
                                                      "antizipiert": 1}
    # Die Go-Pruefung bleibt auf der vorregistrierten Klasse.
    assert z["go_pruefung"]["kriterien"]["1_anteil_ueberraschung"]["wert"] == 0.0


def _voll(slug, preis, zeit="2026-07-31T14:40:22Z"):
    k = _kandidat(slug=slug, preis=preis, zeit=zeit, auswertbar=False, buch={})
    k["kriterium"] = "vollstaendig"
    k["buch"] = None
    return k


def test_vollueberdeckung_wird_getrennt_gebaut():
    zeilen = [
        _voll("capture-all-sep", 0.195),
        _bestaetigt(slug="capture-all-sep", sichtung="2026-07-31T14:40:22Z"),
        _nachfassung(30, 0.20, slug="capture-all-sep",
                     zeit="2026-07-31T15:10:22Z", real_s=1800.0),
        _kandidat(slug="enter", preis=0.30),
        _bestaetigt(slug="enter"),
        {**_kandidat(slug="ukr", preis=0.5, auswertbar=False),
         "polaritaet": "ukrainisch", "kriterium": "vollstaendig"},
    ]
    auswertbar, zaehler = ava.baue_ereignisse(zeilen)
    voll = ava.baue_ereignisse_vollstaendig(zeilen)
    assert [e.slug for e in auswertbar] == ["enter"]
    assert [e.slug for e in voll] == ["capture-all-sep"]
    assert voll[0].kriterium == "vollstaendig"
    assert voll[0].klasse == "ueberraschung" and voll[0].best_bid_t0 is None
    assert voll[0].preis_t30 == 0.20 and voll[0].delta_t30 == 0.005
    assert zaehler["nicht_auswertbar"] == 2
    assert zaehler["nachfassung_unzuordenbar"] == 0


def test_bericht_zeigt_basis_spalte_und_vollueberdeckungstabelle():
    zeilen = [
        _kandidat(slug="sep", preis=0.885, buch=HANNIVKA_BUCH),
        _bestaetigt(slug="sep"),
        _voll("capture-all-sep", 0.195),
        _bestaetigt(slug="capture-all-sep", sichtung="2026-07-31T14:40:22Z"),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    voll = ava.baue_ereignisse_vollstaendig(zeilen)
    text = ava.formatiere_bericht(ereignisse, zaehler,
                                  ava.fasse_zusammen(ereignisse),
                                  vollstaendig=voll)
    assert "Klasse / Basis" in text
    assert "antizipiert  / teilweise" in text
    assert "Basis-Anker (A2" in text
    assert "Vollueberdeckungs-Klasse" in text
    assert "capture-all-of" in text
    assert "Median d30" in text


def test_main_json_enthaelt_vollstaendig(tmp_path, capsys):
    pfad = tmp_path / "p.jsonl"
    pfad.write_text("\n".join(json.dumps(z) for z in [
        _kandidat(slug="sep", preis=0.885, buch=HANNIVKA_BUCH),
        _bestaetigt(slug="sep"),
        _voll("capture-all-sep", 0.195),
        _bestaetigt(slug="capture-all-sep", sichtung="2026-07-31T14:40:22Z"),
    ]) + "\n", encoding="utf-8")
    out = tmp_path / "out.json"
    assert ava.main(["--protokoll", str(pfad), "--json", str(out)]) == 0
    daten = json.loads(out.read_text(encoding="utf-8"))
    assert daten["ereignisse"][0]["klasse_basis"] == "teilweise"
    assert daten["ereignisse_vollstaendig"][0]["slug"] == "capture-all-sep"
    assert daten["siedlungsereignisse"][0]["preis_basis_t0"] == 0.79
    assert "Vollueberdeckungs-Klasse" in capsys.readouterr().out
