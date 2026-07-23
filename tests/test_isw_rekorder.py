"""Tests fuer den ISW-Rekorder: Trefferlogik, Zustand, Takt.

Kein Netzzugriff — die Layer- und Marktzugriffe sind durch Attrappen ersetzt.
"""
from __future__ import annotations

import json

from operations.pipeline import isw_rekorder as rek
from operations.pipeline.isw_karten_watch import ISWFlaeche, Siedlung

QUADRAT = [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]]
FERN = [[[100, 100], [100, 110], [110, 110], [110, 100], [100, 100]]]


def _ziel(slug="will-russia-enter-testort-by-july-31", ringe=None):
    return rek.Marktziel(
        slug=slug,
        frage="Will Russia enter Testort?",
        lat=48.4,
        lon=37.1,
        token_yes="token-1",
        polaritaet=rek.markt_polaritaet(slug),
        kriterium=rek.markt_kriterium(slug),
        siedlung_name="Testort",
        siedlung_objectid=1,
        ringe=ringe if ringe is not None else QUADRAT,
    )


# -------------------------------------------------------------- Auswertbar

def test_russischer_enter_markt_ist_auswertbar():
    assert _ziel().auswertbar is True


def test_re_enter_markt_ist_nicht_auswertbar():
    ziel = _ziel("will-ukraine-re-enter-myrnohrad-by-december-31")
    assert ziel.polaritaet == "ukrainisch"
    assert ziel.auswertbar is False


def test_capture_all_of_ist_nicht_auswertbar():
    ziel = _ziel("will-russia-capture-all-of-chasiv-yar-by-december-31")
    assert ziel.kriterium == "vollstaendig"
    assert ziel.auswertbar is False


# ------------------------------------------------------------ Trefferlogik

def test_neue_treffer_findet_ueberdeckung():
    flaeche = ISWFlaeche("infiltration", 2104, QUADRAT, creation_ms=1000)
    treffer = rek.neue_treffer([flaeche], [_ziel()], {})
    assert len(treffer) == 1
    assert treffer[0][1].objectid == 2104


def test_neue_treffer_ignoriert_entfernte_flaeche():
    flaeche = ISWFlaeche("infiltration", 1, FERN, creation_ms=1000)
    assert rek.neue_treffer([flaeche], [_ziel()], {}) == []


def test_neue_treffer_feuert_nicht_zweimal_fuer_denselben_layer():
    flaeche = ISWFlaeche("infiltration", 2104, QUADRAT, creation_ms=1000)
    ziel = _ziel()
    bereits = {ziel.slug: ["infiltration"]}
    assert rek.neue_treffer([flaeche], [ziel], bereits) == []


def test_neue_treffer_feuert_fuer_zweiten_layer_erneut():
    """Control nach Infiltration ist ein eigenes, protokollwuerdiges Ereignis."""
    flaeche = ISWFlaeche("control", 7, QUADRAT, edit_ms=2000)
    ziel = _ziel()
    bereits = {ziel.slug: ["infiltration"]}
    treffer = rek.neue_treffer([flaeche], [ziel], bereits)
    assert len(treffer) == 1
    assert treffer[0][1].layer == "control"


def test_neue_treffer_meldet_je_ziel_nur_einmal_pro_durchlauf():
    flaechen = [
        ISWFlaeche("infiltration", 1, QUADRAT, creation_ms=1000),
        ISWFlaeche("infiltration", 2, QUADRAT, creation_ms=2000),
    ]
    assert len(rek.neue_treffer(flaechen, [_ziel()], {})) == 1


def test_neue_treffer_ohne_geometrie():
    flaeche = ISWFlaeche("infiltration", 1, [], creation_ms=1000)
    assert rek.neue_treffer([flaeche], [_ziel()], {}) == []


# -------------------------------------------------------------------- Takt

def test_takt_ist_dicht_im_isw_arbeitsfenster():
    from datetime import UTC, datetime
    dicht = datetime(2026, 7, 22, 20, 39, tzinfo=UTC)
    assert rek.takt_fuer(dicht) == rek.TAKT_AKTIV_S


def test_takt_ist_sparsam_nachts():
    from datetime import UTC, datetime
    ruhe = datetime(2026, 7, 22, 4, 0, tzinfo=UTC)
    assert rek.takt_fuer(ruhe) == rek.TAKT_RUHE_S


# ------------------------------------------------------------------ Zustand

def test_zustand_rundlauf(tmp_path):
    pfad = tmp_path / "zustand.json"
    zustand = {"layer_stand": {"infiltration": 123}, "gedeckt": {"a": ["infiltration"]},
               "offene_nachfassungen": []}
    rek._schreibe_zustand(pfad, zustand)
    assert rek._lade_zustand(pfad) == zustand


def test_zustand_fehlende_datei_gibt_leeren_zustand(tmp_path):
    zustand = rek._lade_zustand(tmp_path / "gibtsnicht.json")
    assert zustand == {"layer_stand": {}, "gedeckt": {}, "offene_nachfassungen": []}


def test_zustand_kaputte_datei_gibt_leeren_zustand(tmp_path):
    pfad = tmp_path / "kaputt.json"
    pfad.write_text("{nicht json", encoding="utf-8")
    assert rek._lade_zustand(pfad)["layer_stand"] == {}


def test_protokoll_haengt_zeilen_an(tmp_path):
    pfad = tmp_path / "ereignisse.jsonl"
    rek._protokolliere(pfad, {"art": "treffer", "slug": "a"})
    rek._protokolliere(pfad, {"art": "treffer", "slug": "b"})
    zeilen = pfad.read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(z)["slug"] for z in zeilen] == ["a", "b"]


# ------------------------------------------------------------- Durchlauf

class _KarteAttrappe:
    """Liefert feste Layer-Staende und Flaechen, ohne Netz."""

    def __init__(self, staende, flaechen):
        self._staende = staende
        self._flaechen = flaechen

    def layer_stand(self, layer):
        return self._staende.get(layer.name)

    def flaechen(self, layer, where="1=1", mit_geometrie=True):
        return self._flaechen.get(layer.name, [])


class _LeserAttrappe:
    def __init__(self, preis=0.046):
        self._preis = preis

    def preis_yes(self, token_id):
        return self._preis


def test_durchlauf_grundiert_beim_ersten_lauf_ohne_signal(tmp_path):
    """Der erste Lauf darf nicht fuer jede bereits gedeckte Siedlung feuern."""
    karte = _KarteAttrappe(
        {"infiltration": 111},
        {"infiltration": [ISWFlaeche("infiltration", 1, QUADRAT, creation_ms=1000)]},
    )
    zustand = {"layer_stand": {}, "gedeckt": {}, "offene_nachfassungen": []}
    ereignisse = rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                               tmp_path / "p.jsonl")
    assert ereignisse == []
    assert zustand["gedeckt"]["will-russia-enter-testort-by-july-31"] == ["infiltration"]


def test_durchlauf_meldet_neue_ueberdeckung_nach_grundierung(tmp_path):
    protokoll = tmp_path / "p.jsonl"
    ziel = _ziel()
    zustand = {"layer_stand": {"infiltration": 111}, "gedeckt": {},
               "offene_nachfassungen": []}
    karte = _KarteAttrappe(
        {"infiltration": 222},
        {"infiltration": [ISWFlaeche("infiltration", 2104, QUADRAT,
                                     creation_ms=1_784_752_740_759)]},
    )
    ereignisse = rek.durchlauf(karte, _LeserAttrappe(0.046), [ziel], zustand,
                               protokoll)
    assert len(ereignisse) == 1
    ereignis = ereignisse[0]
    assert ereignis.slug == ziel.slug
    assert ereignis.layer == "infiltration"
    assert ereignis.preis_yes_bei_erkennung == 0.046
    assert ereignis.auswertbar is True
    # Nachfassungen fuer T+1, T+5, T+30 eingeplant
    assert [a["minute"] for a in zustand["offene_nachfassungen"]] == [1, 5, 30]


def test_durchlauf_ohne_layer_aenderung_macht_nichts(tmp_path):
    karte = _KarteAttrappe({"infiltration": 111}, {})
    zustand = {"layer_stand": {"infiltration": 111}, "gedeckt": {},
               "offene_nachfassungen": []}
    assert rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                         tmp_path / "p.jsonl") == []


def test_durchlauf_signalisiert_bei_bulk_rebuild_nicht(tmp_path):
    """115 Features in 48 Minuten duerfen nicht 52 Signale ausloesen."""
    basis = 1_784_000_000_000
    viele = [ISWFlaeche("infiltration", i, QUADRAT, creation_ms=basis + i * 1000)
             for i in range(20)]
    zustand = {"layer_stand": {"infiltration": 111}, "gedeckt": {},
               "offene_nachfassungen": []}
    karte = _KarteAttrappe({"infiltration": 222}, {"infiltration": viele})
    protokoll = tmp_path / "p.jsonl"
    ereignisse = rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                               protokoll)
    assert ereignisse == []
    arten = [json.loads(z)["art"]
             for z in protokoll.read_text(encoding="utf-8").strip().splitlines()]
    assert "rebuild" in arten


def test_durchlauf_bremst_nicht_wegen_alter_historie(tmp_path):
    """Regression aus dem Probelauf: viele ALTE Features duerfen nicht bremsen.

    Der Layer enthaelt 20 dicht beieinanderliegende Altstempel und genau ein
    neues Feature. Vor dem Fix bewertete die Bremse alle 21 und blockierte
    dauerhaft jedes Signal.
    """
    basis = 1_784_000_000_000
    alt = [ISWFlaeche("infiltration", i, FERN, creation_ms=basis + i * 1000)
           for i in range(20)]
    neu = ISWFlaeche("infiltration", 999, QUADRAT,
                     creation_ms=basis + 86_400_000)
    zustand = {"layer_stand": {"infiltration": basis + 19_000}, "gedeckt": {},
               "offene_nachfassungen": []}
    karte = _KarteAttrappe({"infiltration": basis + 86_400_000},
                           {"infiltration": alt + [neu]})
    ereignisse = rek.durchlauf(karte, _LeserAttrappe(0.05), [_ziel()], zustand,
                               tmp_path / "p.jsonl")
    assert len(ereignisse) == 1
    assert ereignisse[0].objectid == 999


def test_baue_watchlist_ordnet_ueber_koordinate_zu():
    """Namen weichen ab — die Zuordnung muss ueber die Koordinate laufen."""

    class _LeserMitMaerkten(_LeserAttrappe):
        def maerkte(self, tag=rek.UKRAINE_TAG):
            return [{
                "id": "1",
                "slug": "will-russia-enter-krasnoiarske-by-july-31",
                "question": "Will Russia enter Krasnoiarske by July 31?",
                "description": "... Krasnoiarske, Donetsk Oblast, "
                               "(48.419117° N, 37.125165° E) ...",
                "clobTokenIds": json.dumps(["tok-yes", "tok-no"]),
                "closed": False,
                "acceptingOrders": True,
            }]

    class _KarteMitSiedlung(_KarteAttrappe):
        def __init__(self):
            super().__init__({}, {})

        def siedlung_an_punkt(self, lat, lon):
            # Layer-Schreibweise weicht bewusst vom Marktnamen ab.
            return Siedlung(objectid=6216, name="Krasnoyarske", ringe=QUADRAT)

    ziele = rek.baue_watchlist(_LeserMitMaerkten(), _KarteMitSiedlung())
    assert len(ziele) == 1
    assert ziele[0].siedlung_name == "Krasnoyarske"
    assert ziele[0].token_yes == "tok-yes"
    assert ziele[0].auswertbar is True
