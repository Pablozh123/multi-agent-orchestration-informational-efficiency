"""Tests fuer den DeepState-Rekorder: Parsing, Deckung, Uebergaenge, Sperre.

Kein Netzzugriff — DeepState und Polymarket sind Attrappen. Die
Polymarket-Attrappe und die Marktziel-Fabrik stammen aus den
ISW-Rekorder-Tests (gleiche Marktziele, gleicher Geometrie-Cache).
"""
from __future__ import annotations

import json

from operations.pipeline import deepstate_rekorder as ds
from tests.test_isw_rekorder import FERN, QUADRAT, _LeserAttrappe, _ziel

BESETZT = "Окуповано /// Occupied /// geoJSON.status.occupied"
GRAUZONE = "Статус невідомий /// Unknown status /// geoJSON.status.unknown\n"
BEFREIT = "Звільнено /// Liberated /// geoJSON.status.liberated"


def _feature(name, ringe, typ="Polygon"):
    # GeoJSON traegt [lon, lat, alt]-Tripel
    koord = [[[x, y, 0] for x, y in ring] for ring in ringe]
    if typ == "MultiPolygon":
        koord = [koord]
    return {"type": "Feature", "properties": {"name": name},
            "geometry": {"type": typ, "coordinates": koord}}


def _karte_json(karte_id, features, datetime="01.09 o 20:45"):
    return {"id": karte_id, "datetime": datetime,
            "map": {"type": "FeatureCollection", "features": features}}


class _DSAttrappe:
    """Liefert je Aufruf das naechste Element: DSKarte, None (304) oder
    eine Exception-Instanz (wird geworfen)."""

    def __init__(self, folge, eintraege=None):
        self._folge = list(folge)
        self._eintraege = eintraege or {}
        self.aufrufe = 0
        self.eintrag_aufrufe = 0

    def letzte_karte(self, etag):
        self.aufrufe += 1
        naechste = self._folge.pop(0)
        if isinstance(naechste, Exception):
            raise naechste
        return naechste

    def eintrag(self, karte_id):
        self.eintrag_aufrufe += 1
        return self._eintraege.get(karte_id)


def _zustand(**overrides):
    zustand = ds._leerer_zustand()
    zustand.update(overrides)
    return zustand


def _zeilen(pfad):
    return [json.loads(z) for z in
            pfad.read_text(encoding="utf-8").strip().splitlines()]


def _karte(karte_id, *polygone, etag=None):
    return ds.parse_karte(_karte_json(karte_id, list(polygone)), etag=etag)


# ------------------------------------------------------------------ Parsing

def test_klasse_aus_dem_dreisprachigen_namen():
    assert ds.klasse_aus_name(BESETZT) == "besetzt"
    assert ds.klasse_aus_name(GRAUZONE) == "grauzone"
    assert ds.klasse_aus_name(BEFREIT) is None
    assert ds.klasse_aus_name("Окупований Крим /// geoJSON.territories.crimea") is None
    assert ds.klasse_aus_name(None) is None


def test_parse_karte_nimmt_nur_klassifizierte_polygone_und_kappt_die_hoehe():
    karte = ds.parse_karte(_karte_json(7, [
        _feature(BESETZT, QUADRAT),
        _feature(GRAUZONE, FERN),
        _feature(BEFREIT, QUADRAT),
        {"type": "Feature", "properties": {"name": BESETZT},
         "geometry": {"type": "Point", "coordinates": [1, 2, 0]}},
    ]), etag='W/"abc"')
    assert karte.id == 7 and karte.etag == 'W/"abc"'
    assert karte.n_features == 4
    assert [k for k, _ in karte.polygone] == ["besetzt", "grauzone"]
    assert karte.polygone[0][1] == QUADRAT          # 2-D, kein Hoehenwert


def test_parse_karte_zerlegt_multipolygone():
    karte = ds.parse_karte(_karte_json(1, [
        _feature(BESETZT, QUADRAT, typ="MultiPolygon")]))
    assert len(karte.polygone) == 1
    assert karte.polygone[0] == ("besetzt", QUADRAT)


def test_erwaehnungen_aus_dem_beschreibungs_html():
    text = ('The enemy has advanced near '
            '<a href="https://deepstatemap.live/en#13/48.3585352/37.1725898">'
            'Rodynske</a>, <a href="https://deepstatemap.live/en#14/'
            '47.5353484/36.0410831">Luhivske</a>.\n')
    assert ds.erwaehnungen(text) == [
        {"name": "Rodynske", "lat": 48.3585352, "lon": 37.1725898},
        {"name": "Luhivske", "lat": 47.5353484, "lon": 36.0410831},
    ]
    assert ds.erwaehnungen(None) == []
    assert ds.erwaehnungen("kein Link") == []


def test_maerkte_nahe_ordnet_im_umkreis_zu():
    ziel = _ziel()                          # 48.4 N, 37.1 E
    punkte = [{"name": "Nah", "lat": 48.41, "lon": 37.12},
              {"name": "Fern", "lat": 49.0, "lon": 37.1}]
    heraus = ds.maerkte_nahe(punkte, [ziel], radius_km=5.0)
    assert heraus[0]["maerkte_nahe"][0]["slug"] == ziel.slug
    assert 0 < heraus[0]["maerkte_nahe"][0]["km"] < 5
    assert heraus[1]["maerkte_nahe"] == []


# ----------------------------------------------------------------- Deckung

def test_deckung_liefert_klassen_je_siedlung():
    karte = _karte(1, _feature(BESETZT, QUADRAT), _feature(GRAUZONE, QUADRAT),
                   _feature(BESETZT, FERN))
    ziel = _ziel()
    assert ds.deckung(karte.polygone, [ziel]) == {ziel.slug: {"besetzt", "grauzone"}}
    assert ds.deckung(karte.polygone, [_ziel(ringe=[[[50, 50], [50, 60],
                                                     [60, 60], [60, 50],
                                                     [50, 50]]])]) == {}


# ------------------------------------------------------------- Durchlauf

def test_erster_lauf_grundiert_ohne_ereignisse(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    zustand = _zustand()
    leser = _DSAttrappe([_karte(1, _feature(BESETZT, QUADRAT), etag="e1")])
    meldungen = ds.durchlauf(leser, _LeserAttrappe(), [_ziel()], zustand,
                             protokoll)
    assert meldungen == []
    arten = [z["art"] for z in _zeilen(protokoll)]
    assert arten == ["karte_neu", "grundierung"]
    assert zustand["beobachtet"][_ziel().slug] == ["besetzt"]
    assert zustand["karte_id"] == 1 and zustand["etag"] == "e1"
    assert leser.eintrag_aufrufe == 0, "Grundierung liest keine Historie"


def test_304_macht_nichts_ausser_zyklus_fortschreiben(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    zustand = _zustand(karte_id=1, etag="e1")
    ds.durchlauf(_DSAttrappe([None]), _LeserAttrappe(), [_ziel()], zustand,
                 protokoll)
    assert not protokoll.exists()
    assert zustand["letzter_zyklus_ts"] is not None


def test_neue_karte_erzeugt_treffer_mit_t0_messung(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel()
    zustand = _zustand(karte_id=1, etag="e1", beobachtet={ziel.slug: []})
    eintrag = {"id": 2, "createdAt": "2026-09-01T18:45:04.000Z",
               "updatedAt": "2026-09-02T19:56:09.420Z",
               "descriptionEn": 'near <a href="x#13/48.41/37.12">Testort</a>'}
    leser = _DSAttrappe([_karte(2, _feature(GRAUZONE, QUADRAT), etag="e2")],
                        eintraege={2: eintrag})
    pm = _LeserAttrappe(preis=0.31)
    meldungen = ds.durchlauf(leser, pm, [ziel], zustand, protokoll)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["karte_neu", "ds_treffer"]
    kopf = zeilen[0]
    assert kopf["karte_id"] == 2 and kopf["created_at"] == eintrag["createdAt"]
    assert kopf["vorlauf_s"] is not None and kopf["vorlauf_s"] > 0
    assert kopf["erwaehnt"][0]["maerkte_nahe"][0]["slug"] == ziel.slug
    treffer = zeilen[1]
    assert treffer["klasse"] == "grauzone"
    assert treffer["siedlung"] == "Testort"
    assert treffer["auswertbar"] is True
    assert treffer["preis_yes"] == 0.31
    assert treffer["buch"]["best_ask"] == 0.05
    assert treffer["erwaehnt"] is True
    assert treffer["nach_ausfall_s"] == 0.0
    assert meldungen == [treffer]
    assert zustand["beobachtet"][ziel.slug] == ["grauzone"]
    assert [a["minute"] for a in zustand["offene_nachfassungen"]] == [1, 5, 30]
    assert zustand["offene_nachfassungen"][0]["layer"] == "grauzone"
    assert pm.buch_aufrufe == 1


def test_verlust_wird_gemeldet_und_zustand_bereinigt(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel()
    zustand = _zustand(karte_id=1, etag="e1",
                       beobachtet={ziel.slug: ["besetzt", "grauzone"]})
    leser = _DSAttrappe([_karte(2, _feature(BESETZT, QUADRAT), etag="e2")])
    ds.durchlauf(leser, _LeserAttrappe(), [ziel], zustand, protokoll)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["karte_neu", "ds_verlust"]
    assert zeilen[1]["klasse"] == "grauzone"
    assert zeilen[1]["restliche_klassen"] == ["besetzt"]
    assert zustand["beobachtet"][ziel.slug] == ["besetzt"]


def test_gleiche_karte_mit_neuem_etag_ist_nachbearbeitung(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel()
    zustand = _zustand(karte_id=2, etag="e2", beobachtet={ziel.slug: []})
    leser = _DSAttrappe([_karte(2, _feature(BESETZT, QUADRAT), etag="e3")])
    ds.durchlauf(leser, _LeserAttrappe(), [ziel], zustand, protokoll)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["nachbearbeitung", "ds_treffer"]
    assert zeilen[1]["vorlauf_s"] is None
    assert leser.eintrag_aufrufe == 0
    assert zustand["etag"] == "e3"


def test_nicht_auswertbarer_markt_bekommt_preis_aber_kein_buch(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel("will-russia-capture-all-of-testort-by-december-31")
    zustand = _zustand(karte_id=1, etag="e1", beobachtet={ziel.slug: []})
    pm = _LeserAttrappe(preis=0.5)
    ds.durchlauf(_DSAttrappe([_karte(2, _feature(BESETZT, QUADRAT))]), pm,
                 [ziel], zustand, protokoll)
    treffer = [z for z in _zeilen(protokoll) if z["art"] == "ds_treffer"][0]
    assert treffer["auswertbar"] is False
    assert treffer["preis_yes"] == 0.5 and treffer["buch"] is None
    assert pm.buch_aufrufe == 0


def test_ausfall_markiert_das_erste_ereignis_danach(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel()
    zustand = _zustand(karte_id=1, etag="e1", beobachtet={ziel.slug: []},
                       letzter_zyklus_ts=ds._jetzt_utc().timestamp() - 3600)
    ds.durchlauf(_DSAttrappe([_karte(2, _feature(BESETZT, QUADRAT))]),
                 _LeserAttrappe(), [ziel], zustand, protokoll)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["ausfall_erkannt", "karte_neu",
                                          "ds_treffer"]
    assert zeilen[2]["nach_ausfall_s"] >= 3590.0


# -------------------------------------------------------------------- Sperre

def test_abweisung_geht_in_die_sperre_und_friert_den_zyklus_ein(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    vorher = ds._jetzt_utc().timestamp() - 30.0
    zustand = _zustand(karte_id=1, etag="e1", letzter_zyklus_ts=vorher)
    sperre = ds.Sperre()
    leser = _DSAttrappe([ds.DSFehler(429, "slow down"),
                         ds.DSFehler(429, "slow down"), None])
    for _ in range(2):
        ds.durchlauf(leser, _LeserAttrappe(), [_ziel()], zustand, protokoll,
                     sperre=sperre)
    assert [z["art"] for z in _zeilen(protokoll)] == ["sperre"]
    assert sperre.aktiv and sperre.versuche == 2
    assert zustand["letzter_zyklus_ts"] == vorher
    ds.durchlauf(leser, _LeserAttrappe(), [_ziel()], zustand, protokoll,
                 sperre=sperre)
    arten = [z["art"] for z in _zeilen(protokoll)]
    assert arten == ["sperre", "sperre_ende"]
    assert not sperre.aktiv
    assert zustand["letzter_zyklus_ts"] > vorher


def test_ohne_sperre_objekt_ist_eine_abweisung_ein_fehler(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ds.durchlauf(_DSAttrappe([ds.DSFehler(503)]), _LeserAttrappe(), [_ziel()],
                 _zustand(), protokoll)
    zeilen = _zeilen(protokoll)
    assert [z["art"] for z in zeilen] == ["fehler"]
    assert zeilen[0]["status"] == 503


# ---------------------------------------------------- Marktlisten-Refresh

def test_neue_slugs_werden_mit_der_letzten_karte_grundiert():
    karte = _karte(1, _feature(BESETZT, QUADRAT))
    alt = _ziel("will-russia-enter-altort-by-september-30")
    neu = _ziel("will-russia-enter-neuort-by-december-31")
    zustand = _zustand(karte_id=1, beobachtet={alt.slug: ["besetzt"]})
    grundiert = ds.grundiere_neue_ziele(zustand, [alt, neu], karte.polygone)
    assert grundiert == [neu.slug]
    assert zustand["beobachtet"][neu.slug] == ["besetzt"]
    assert zustand["beobachtet"][alt.slug] == ["besetzt"]   # unveraendert


def test_bereinigung_entfernt_geschlossene_maerkte():
    zustand = _zustand(beobachtet={"a": ["besetzt"], "b": []},
                       offene_nachfassungen=[{"slug": "a"}, {"slug": "b"}])
    ds._bereinige_zustand(zustand, {"a"})
    assert list(zustand["beobachtet"]) == ["a"]
    assert zustand["offene_nachfassungen"] == [{"slug": "a"}]


# ------------------------------------------------------------ Zustand/Live

def test_zustand_rundlauf_und_schemawechsel(tmp_path):
    pfad = tmp_path / "z.json"
    zustand = _zustand(karte_id=5, etag="x", beobachtet={"s": ["grauzone"]})
    ds._schreibe_zustand(pfad, zustand)
    assert ds._lade_zustand(pfad)["beobachtet"] == {"s": ["grauzone"]}
    pfad.write_text(json.dumps({"schema": 0, "karte_id": 5}), encoding="utf-8")
    assert ds._lade_zustand(pfad)["karte_id"] is None
    assert ds._lade_zustand(tmp_path / "fehlt.json")["karte_id"] is None


def test_live_modus_erfuellt_den_watchdog_vertrag(tmp_path, monkeypatch):
    import os as _os

    from operations.pipeline import startwache

    monkeypatch.setenv("BOT_PROFIL", "deepstate_test_vertrag")
    monkeypatch.setenv("THESIS_LIVE_ROOT", str(tmp_path))
    monkeypatch.setattr(ds, "ISWKarte", lambda *a, **k: type(
        "K", (), {"schliessen": lambda self: None})())
    monkeypatch.setattr(ds, "PolymarktLeser", lambda *a, **k: _LeserAttrappe())
    monkeypatch.setattr(_LeserAttrappe, "schliessen", lambda self: None,
                        raising=False)
    attrappe = _DSAttrappe([_karte(1, _feature(BESETZT, QUADRAT))])
    attrappe.schliessen = lambda: None
    monkeypatch.setattr(ds, "DeepStateLeser", lambda *a, **k: attrappe)
    monkeypatch.setattr(ds, "lade_marktziele", lambda *a, **k: [_ziel()])
    try:
        code = ds.main(["--live", "--einmal"])
    finally:
        startwache.wache_freigeben()
    assert code == 0
    live = tmp_path / "deepstate_test_vertrag"
    assert (live / "bot.pid").read_text(encoding="utf-8") == str(_os.getpid())
    events = [json.loads(z) for z in
              (live / "bot_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[0]["art"] == "start"
    assert any(e["art"] == "herzschlag" for e in events)
    assert (live / "zustand.json").exists()
    assert [z["art"] for z in _zeilen(live / "ereignisse.jsonl")] == [
        "karte_neu", "grundierung"]


def test_main_schleife_ueberlebt_unerwarteten_fehler(tmp_path, monkeypatch):
    protokoll = tmp_path / "p.jsonl"
    monkeypatch.setattr(ds, "ISWKarte", lambda *a, **k: type(
        "K", (), {"schliessen": lambda self: None})())
    monkeypatch.setattr(ds, "PolymarktLeser", lambda *a, **k: _LeserAttrappe())
    monkeypatch.setattr(_LeserAttrappe, "schliessen", lambda self: None,
                        raising=False)
    attrappe = _DSAttrappe([])
    attrappe.schliessen = lambda: None
    monkeypatch.setattr(ds, "DeepStateLeser", lambda *a, **k: attrappe)
    monkeypatch.setattr(ds, "lade_marktziele", lambda *a, **k: [_ziel()])

    def _kracht(*args, **kwargs):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(ds, "durchlauf", _kracht)
    code = ds.main(["--einmal", "--zustand", str(tmp_path / "z.json"),
                    "--protokoll", str(protokoll),
                    "--geometrie-cache", str(tmp_path / "geo.json")])
    assert code == 0
    assert _zeilen(protokoll)[0]["art"] == "lauf_fehler"
