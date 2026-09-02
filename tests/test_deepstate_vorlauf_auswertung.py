"""Tests fuer die DeepState-Vorlauf-Auswertung: Verknuepfung je Siedlung,
Status-Logik (bestaetigt / fehlalarm / offen / isw_zuerst), Gegenrichtung.

Synthetische Protokolle, kein Netz.
"""
from __future__ import annotations

import json

from operations.analysis import deepstate_vorlauf_auswertung as aus

H = 3600.0


def _ds(siedlung, zeit, preis, klasse="grauzone", slug=None, **extra):
    return {"art": "ds_treffer", "zeit_utc": zeit, "siedlung": siedlung,
            "klasse": klasse, "slug": slug or f"will-russia-enter-{siedlung.lower()}",
            "polaritaet": "russisch", "auswertbar": True, "preis_yes": preis,
            "karte_id": 42, **extra}


def _isw(siedlung, zeit, preis, layer="infiltration"):
    return {"art": "kandidat_treffer", "zeit_utc": zeit, "siedlung": siedlung,
            "layer": layer, "slug": f"will-russia-enter-{siedlung.lower()}",
            "polaritaet": "russisch", "auswertbar": True, "preis_yes": preis}


JETZT = "2026-09-10T00:00:00Z"


def test_ds_ereignisse_werden_je_siedlung_aggregiert():
    zeilen = [
        _ds("Stinky", "2026-09-01T10:00:00Z", 0.30, slug="a"),
        _ds("Stinky", "2026-09-01T10:00:00Z", 0.40, slug="b",
            nach_ausfall_s=700.0),
        _ds("Stinky", "2026-09-01T10:00:00Z", 0.50, slug="c",
            auswertbar=False),
        {"art": "ds_treffer", "zeit_utc": "2026-09-01T11:00:00Z",
         "siedlung": "Myrne", "klasse": "besetzt", "polaritaet": "ukrainisch",
         "preis_yes": 0.9},
        {"art": "karte_neu", "zeit_utc": "2026-09-01T10:00:00Z"},
    ]
    ereignisse = aus.baue_ds_ereignisse(zeilen)
    assert len(ereignisse) == 1, "ukrainische Polaritaet zaehlt nicht"
    e = ereignisse[0]
    assert e.n_maerkte == 3 and e.preis_t0 == 0.40 and e.karte_id == 42
    assert e.auswertbar is True and e.nach_ausfall_s == 700.0


def test_isw_ereignisse_nehmen_auch_capture_all_of_mit():
    zeilen = [
        _isw("Kostyantynivka", "2026-09-02T14:00:00Z", 0.46),
        {**_isw("Kostyantynivka", "2026-09-02T14:00:00Z", 0.08),
         "slug": "will-russia-capture-all-of-kostyantynivka", "auswertbar": False},
    ]
    ereignisse = aus.baue_isw_ereignisse(zeilen)
    assert len(ereignisse) == 1 and ereignisse[0].n_maerkte == 2
    assert ereignisse[0].preis_t0 == 0.27


def test_verknuepfung_bestaetigt_mit_vorlauf_und_delta():
    ds = aus.baue_ds_ereignisse([_ds("Stinky", "2026-09-01T10:00:00Z", 0.40)])
    isw = aus.baue_isw_ereignisse([_isw("Stinky", "2026-09-02T14:06:00Z", 0.79)])
    v = aus.verknuepfe(ds, isw, 96 * H, aus._epoch(JETZT))[0]
    assert v.status == "bestaetigt"
    assert v.isw_layer == "infiltration"
    assert v.vorlauf_s == 28 * H + 360
    assert v.preis_ds_t0 == 0.40 and v.preis_isw_t0 == 0.79
    assert v.delta == 0.39


def test_verknuepfung_nimmt_das_erste_isw_ereignis_im_fenster():
    ds = aus.baue_ds_ereignisse([_ds("Lyman", "2026-09-01T10:00:00Z", 0.40)])
    isw = aus.baue_isw_ereignisse([
        _isw("Lyman", "2026-09-03T10:00:00Z", 0.70, layer="advance"),
        _isw("Lyman", "2026-09-02T10:00:00Z", 0.60),
    ])
    v = aus.verknuepfe(ds, isw, 96 * H, aus._epoch(JETZT))[0]
    assert v.isw_erkannt_utc == "2026-09-02T10:00:00Z"
    assert v.vorlauf_s == 24 * H


def test_isw_zuerst_wenn_isw_im_fenster_davor_lag():
    ds = aus.baue_ds_ereignisse([_ds("Hannivka", "2026-09-02T09:00:00Z", 0.95)])
    isw = aus.baue_isw_ereignisse([_isw("Hannivka", "2026-09-01T15:00:50Z", 0.885)])
    v = aus.verknuepfe(ds, isw, 96 * H, aus._epoch(JETZT))[0]
    assert v.status == "isw_zuerst"
    assert v.vorlauf_s is not None and v.vorlauf_s < 0
    assert v.delta is None


def test_fehlalarm_erst_nach_ablauf_des_fensters():
    ds = aus.baue_ds_ereignisse([_ds("Myrne", "2026-09-01T10:00:00Z", 0.40)])
    frueh = aus.verknuepfe(ds, [], 96 * H, aus._epoch("2026-09-03T00:00:00Z"))[0]
    spaet = aus.verknuepfe(ds, [], 96 * H, aus._epoch(JETZT))[0]
    assert frueh.status == "offen"
    assert spaet.status == "fehlalarm"


def test_isw_ohne_deepstate_ist_die_gegenrichtung():
    ds = aus.baue_ds_ereignisse([_ds("Stinky", "2026-09-01T10:00:00Z", 0.40)])
    isw = aus.baue_isw_ereignisse([
        _isw("Stinky", "2026-09-02T14:06:00Z", 0.79),
        _isw("Hannivka", "2026-09-01T15:00:50Z", 0.885),
    ])
    verpasst = aus.isw_ohne_deepstate(ds, isw, 96 * H)
    assert [i.siedlung for i in verpasst] == ["Hannivka"]


def test_zusammenfassung_rechnet_quote_und_mediane():
    ds = aus.baue_ds_ereignisse([
        _ds("A", "2026-09-01T10:00:00Z", 0.40),
        _ds("B", "2026-09-01T10:00:00Z", 0.20, klasse="besetzt"),
        _ds("C", "2026-09-01T10:00:00Z", 0.30),
        _ds("D", "2026-09-08T10:00:00Z", 0.30),
    ])
    isw = aus.baue_isw_ereignisse([
        _isw("A", "2026-09-02T10:00:00Z", 0.80),   # +24 h, delta +0.40
        _isw("B", "2026-09-03T10:00:00Z", 0.60),   # +48 h, delta +0.40
        _isw("E", "2026-09-05T10:00:00Z", 0.90),   # ohne DeepState
    ])
    verkn = aus.verknuepfe(ds, isw, 96 * H, aus._epoch(JETZT))
    verpasst = aus.isw_ohne_deepstate(ds, isw, 96 * H)
    z = aus.fasse_zusammen(verkn, isw, verpasst)
    assert z["n_deepstate"] == 4
    assert z["status"] == {"bestaetigt": 2, "fehlalarm": 1, "offen": 1,
                           "isw_zuerst": 0}
    assert z["trefferquote"] == round(2 / 3, 3)
    assert z["median_vorlauf_h"] == 36.0
    assert z["median_delta"] == 0.40
    assert z["n_isw"] == 3 and z["n_isw_verpasst"] == 1
    assert z["anteil_isw_mit_vorlauf"] == round(2 / 3, 3)
    assert z["je_klasse"]["besetzt"]["trefferquote"] == 1.0
    assert z["je_klasse"]["grauzone"]["n"] == 3


def test_main_schreibt_bericht_und_json(tmp_path, capsys):
    ds_pfad = tmp_path / "ds.jsonl"
    isw_pfad = tmp_path / "isw.jsonl"
    ds_pfad.write_text(json.dumps(_ds("Stinky", "2026-09-01T10:00:00Z", 0.40))
                       + "\nkaputt\n", encoding="utf-8")
    isw_pfad.write_text(json.dumps(_isw("Stinky", "2026-09-02T14:06:00Z", 0.79))
                        + "\n", encoding="utf-8")
    out = tmp_path / "aus" / "out.json"
    code = aus.main(["--deepstate", str(ds_pfad), "--isw", str(isw_pfad),
                     "--json", str(out), "--jetzt", JETZT])
    assert code == 0
    text = capsys.readouterr().out
    assert "Stinky" in text and "bestaetigt" in text
    daten = json.loads(out.read_text(encoding="utf-8"))
    assert daten["zusammenfassung"]["trefferquote"] == 1.0
    assert daten["verknuepfungen"][0]["vorlauf_s"] == 28 * H + 360


def test_fehlende_protokolle_geben_leeren_bericht(tmp_path, capsys):
    code = aus.main(["--deepstate", str(tmp_path / "x.jsonl"),
                     "--isw", str(tmp_path / "y.jsonl"), "--jetzt", JETZT])
    assert code == 0
    assert "DeepState-Siedlungsereignisse: 0" in capsys.readouterr().out
