"""Tests für die Feuerkette: Gate, Marktwahl, Wochendeckel, Ablehnungen.

Kein Netz, keine Uhr — `pruefe()` bekommt `jetzt` übergeben und ist rein.

Der Leitfall ist Krasnoiarske 22.07.: Midpoint 0.046, billigster echter
Fill 0.395. Ein Gate auf dem Midpoint hätte in dem Glauben gefeuert, zum
Midpoint kaufen zu können.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from operations.pipeline import isw_feuerkette as fk
from operations.pipeline.isw_rekorder import Marktziel

JETZT = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


def _ziel(slug="will-russia-enter-testort-by-august-31",
          ende="2026-08-31T12:00:00Z", objectid=1, token="token-1"):
    return Marktziel(
        slug=slug, frage="?", lat=48.4, lon=37.1, token_yes=token,
        polaritaet="russisch", kriterium="beruehrung",
        siedlung_name="Testort", siedlung_objectid=objectid,
        ringe=[], ende_utc=ende,
    )


def _meldung(slug="will-russia-enter-testort-by-august-31",
             best_ask=0.40, auswertbar=True, qualifiziert=False,
             layer="infiltration", nach_ausfall_s=0.0, buch=True):
    return {
        "art": "kandidat_treffer",
        "slug": slug,
        "layer": layer,
        "siedlung": "Testort",
        "auswertbar": auswertbar,
        "markt_bereits_qualifiziert": qualifiziert,
        "polaritaet": "russisch",
        "kriterium": "beruehrung",
        "preis_yes": 0.046,
        "vorlauf_s": 118.5,
        "nach_ausfall_s": nach_ausfall_s,
        "buch": ({"best_bid": 0.02, "best_ask": best_ask,
                  "usd_bis_030": 10.0, "usd_bis_050": 50.0}
                 if buch else None),
    }


def _pruefe(meldungen, ziele, **kw):
    return fk.pruefe(meldungen, {z.slug: z for z in ziele}, jetzt=JETZT, **kw)


# ------------------------------------------------------------------ Gate


def test_niedriger_ask_feuert():
    befehle, ablehnungen = _pruefe([_meldung()], [_ziel()])
    assert len(befehle) == 1
    assert ablehnungen == []
    b = befehle[0]
    assert b.seite == "BUY_YES"
    assert b.max_preis == 0.60
    assert b.einsatz_usdc == 200.0
    assert b.best_ask == 0.40


def test_ask_ueber_deckel_feuert_nicht():
    befehle, ablehnungen = _pruefe([_meldung(best_ask=0.93)], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "ask_ueber_deckel"


def test_ask_genau_auf_dem_deckel_feuert():
    befehle, _ = _pruefe([_meldung(best_ask=0.60)], [_ziel()])
    assert len(befehle) == 1


def test_gate_nutzt_ask_nicht_den_midpoint():
    """Krasnoiarske: Midpoint 0.046, billigster Fill 0.395.

    Der Midpoint liegt unter jedem denkbaren Deckel. Entscheidend ist,
    dass ein Ask ÜBER dem Deckel trotz Traum-Midpoint nicht feuert.
    """
    meldung = _meldung(best_ask=0.72)
    meldung["preis_yes"] = 0.046
    befehle, ablehnungen = _pruefe([meldung], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "ask_ueber_deckel"


def test_krasnoiarske_realwerte_feuern():
    # Midpoint 0.046, billigster echter Fill 0.395 -> unter 0.60.
    meldung = _meldung(best_ask=0.395)
    meldung["preis_yes"] = 0.046
    befehle, _ = _pruefe([meldung], [_ziel()])
    assert len(befehle) == 1
    assert befehle[0].best_ask == 0.395


def test_fehlendes_orderbuch_feuert_nicht():
    # Preisbudget je Zyklus erschoepft: unbekannter Ask ist kein
    # niedriger Ask.
    befehle, ablehnungen = _pruefe([_meldung(buch=False)], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "kein_orderbuch"


# --------------------------------------------------------- Vorfilterung


def test_nicht_auswertbarer_markt_feuert_nicht():
    befehle, ablehnungen = _pruefe([_meldung(auswertbar=False)], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "nicht_auswertbar"


def test_bereits_qualifizierter_markt_feuert_nicht():
    befehle, ablehnungen = _pruefe([_meldung(qualifiziert=True)], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "bereits_qualifiziert"


def test_unbekannter_slug_feuert_nicht():
    befehle, ablehnungen = _pruefe([_meldung(slug="fremd")], [_ziel()])
    assert befehle == []
    assert ablehnungen[0].grund == "markt_unbekannt"


def test_jeder_kandidat_erzeugt_befehl_oder_ablehnung():
    # Schweigen ohne Grund ist der Fehler, den dieses Projekt schon
    # dreimal gemacht hat.
    meldungen = [_meldung(slug="a"), _meldung(slug="b", best_ask=0.93),
                 _meldung(slug="c", auswertbar=False)]
    ziele = [_ziel(slug="a", objectid=1), _ziel(slug="b", objectid=2),
             _ziel(slug="c", objectid=3)]
    befehle, ablehnungen = _pruefe(meldungen, ziele)
    assert len(befehle) + len(ablehnungen) == 3


# ------------------------------------------------------------ Marktwahl


def test_ein_siedlungsereignis_erzeugt_genau_einen_befehl():
    # Krasnoiarske traf 3 Maerkte gleichzeitig. Ohne Gruppierung waere
    # das dreifaches Exposure.
    meldungen = [_meldung(slug="s-july-31"), _meldung(slug="s-september-30"),
                 _meldung(slug="s-december-31")]
    ziele = [_ziel(slug="s-july-31", ende="2026-07-31T12:00:00Z"),
             _ziel(slug="s-september-30", ende="2026-09-30T12:00:00Z"),
             _ziel(slug="s-december-31", ende="2026-12-31T12:00:00Z")]
    befehle, _ = _pruefe(meldungen, ziele)
    assert len(befehle) == 1
    assert befehle[0].markt_slug == "s-july-31"
    assert befehle[0].geschwister_maerkte == ["s-december-31",
                                              "s-september-30"]


def test_markt_ohne_enddatum_verdraengt_keinen_kurzdatierten():
    meldungen = [_meldung(slug="ohne"), _meldung(slug="mit")]
    ziele = [_ziel(slug="ohne", ende=None),
             _ziel(slug="mit", ende="2026-12-31T12:00:00Z")]
    befehle, _ = _pruefe(meldungen, ziele)
    assert befehle[0].markt_slug == "mit"


def test_verschiedene_siedlungen_feuern_getrennt():
    meldungen = [_meldung(slug="a"), _meldung(slug="b")]
    ziele = [_ziel(slug="a", objectid=1), _ziel(slug="b", objectid=2)]
    befehle, _ = _pruefe(meldungen, ziele)
    assert len(befehle) == 2


def test_marktwahl_ist_deterministisch_bei_gleichem_enddatum():
    meldungen = [_meldung(slug="z"), _meldung(slug="a")]
    ziele = [_ziel(slug="z"), _ziel(slug="a")]
    erst, _ = _pruefe(meldungen, ziele)
    zweit, _ = _pruefe(list(reversed(meldungen)), ziele)
    assert erst[0].markt_slug == zweit[0].markt_slug == "a"


# --------------------------------------------------------- Wochendeckel


def test_wochendeckel_laesst_genau_zwei_ereignisse_zu():
    meldungen = [_meldung(slug="a"), _meldung(slug="b"), _meldung(slug="c")]
    ziele = [_ziel(slug="a", objectid=1), _ziel(slug="b", objectid=2),
             _ziel(slug="c", objectid=3)]
    befehle, ablehnungen = _pruefe(meldungen, ziele)
    assert len(befehle) == 2                      # 2 x 200 = 400 USDC
    assert [a.grund for a in ablehnungen] == ["wochendeckel"]


def test_bereits_verbrauchtes_budget_bremst():
    befehle, ablehnungen = _pruefe([_meldung()], [_ziel()],
                                   verbraucht_usdc=250.0)
    assert befehle == []
    assert ablehnungen[0].grund == "wochendeckel"


def test_teilbudget_laesst_noch_ein_ereignis_zu():
    meldungen = [_meldung(slug="a"), _meldung(slug="b")]
    ziele = [_ziel(slug="a", objectid=1), _ziel(slug="b", objectid=2)]
    befehle, _ = _pruefe(meldungen, ziele, verbraucht_usdc=200.0)
    assert len(befehle) == 1


def test_wochenverbrauch_zaehlt_nur_die_letzten_sieben_tage(tmp_path):
    pfad = tmp_path / "feuerbefehle.jsonl"
    alt = (JETZT - timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
    neu = (JETZT - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pfad.write_text(
        json.dumps({"art": "feuerbefehl", "zeit_utc": alt,
                    "einsatz_usdc": 200}) + "\n"
        + json.dumps({"art": "feuerbefehl", "zeit_utc": neu,
                      "einsatz_usdc": 200}) + "\n",
        encoding="utf-8")
    assert fk.wochenverbrauch(pfad, JETZT) == 200.0


def test_wochenverbrauch_ignoriert_ablehnungen(tmp_path):
    pfad = tmp_path / "feuerbefehle.jsonl"
    zeit = JETZT.strftime("%Y-%m-%dT%H:%M:%SZ")
    pfad.write_text(
        json.dumps({"art": "ablehnung", "zeit_utc": zeit,
                    "einsatz_usdc": 200}) + "\n", encoding="utf-8")
    assert fk.wochenverbrauch(pfad, JETZT) == 0.0


def test_wochenverbrauch_ohne_datei_ist_null(tmp_path):
    assert fk.wochenverbrauch(tmp_path / "weg.jsonl", JETZT) == 0.0


def test_wochenverbrauch_ueberspringt_kaputte_zeilen(tmp_path):
    pfad = tmp_path / "feuerbefehle.jsonl"
    zeit = JETZT.strftime("%Y-%m-%dT%H:%M:%SZ")
    pfad.write_text(
        "{kaputt\n"
        + json.dumps({"art": "feuerbefehl", "zeit_utc": zeit,
                      "einsatz_usdc": 200}) + "\n", encoding="utf-8")
    assert fk.wochenverbrauch(pfad, JETZT) == 200.0


# -------------------------------------------------------- Befehlsinhalt


def test_befehl_traegt_alles_zur_ausfuehrung_noetige():
    befehle, _ = _pruefe([_meldung()], [_ziel(token="tok-42")])
    b = befehle[0]
    assert b.token_id == "tok-42"
    assert b.ende_utc == "2026-08-31T12:00:00Z"
    assert b.shares_bei_deckel == round(200.0 / 0.60, 2)
    assert b.vorlauf_s == 118.5


def test_befehl_verfaellt_nach_zehn_minuten():
    befehle, _ = _pruefe([_meldung()], [_ziel()])
    assert befehle[0].zeit_utc == "2026-08-07T12:00:00Z"
    assert befehle[0].gueltig_bis_utc == "2026-08-07T12:10:00Z"


def test_ausfallmarkierung_bleibt_am_befehl_sichtbar():
    # Nach einem Rekorder-Ausfall ist unklar, wie alt die Nachricht ist.
    # Gefeuert wird trotzdem (der Ask wird JETZT gemessen), aber der
    # Befehl traegt die Markierung.
    befehle, _ = _pruefe([_meldung(nach_ausfall_s=95952.0)], [_ziel()])
    assert befehle[0].nach_ausfall_s == 95952.0


def test_schreibe_haengt_an_und_ist_lesbar(tmp_path):
    pfad = tmp_path / "feuerbefehle.jsonl"
    befehle, ablehnungen = _pruefe(
        [_meldung(slug="a"), _meldung(slug="b", best_ask=0.99)],
        [_ziel(slug="a", objectid=1), _ziel(slug="b", objectid=2)])
    fk.schreibe(pfad, befehle + ablehnungen)
    zeilen = [json.loads(z) for z in
              pfad.read_text(encoding="utf-8").splitlines()]
    assert [z["art"] for z in zeilen] == ["feuerbefehl", "ablehnung"]
    assert fk.wochenverbrauch(pfad, JETZT) == 200.0


def test_leere_meldungsliste_erzeugt_nichts():
    assert _pruefe([], [_ziel()]) == ([], [])


# ------------------------------------------- Einbindung in den Rekorder


def test_rekorder_schreibt_befehl_und_haelt_messpfad_frei(tmp_path):
    from operations.pipeline import isw_rekorder as rek

    pfad = tmp_path / "feuerbefehle.jsonl"
    rek._feuern([_meldung()], [_ziel()], pfad)
    zeilen = [json.loads(z) for z in
              pfad.read_text(encoding="utf-8").splitlines()]
    assert [z["art"] for z in zeilen] == ["feuerbefehl"]
    assert zeilen[0]["seite"] == "BUY_YES"


def test_rekorder_ueberlebt_kaputte_feuerkette(tmp_path, monkeypatch, capsys):
    # Die Messreihe ist das Fundament: sie darf nie an der Feuerkette
    # sterben.
    from operations.pipeline import isw_rekorder as rek

    def kaputt(*a, **kw):
        raise RuntimeError("Testfehler")

    monkeypatch.setattr(fk, "pruefe", kaputt)
    rek._feuern([_meldung()], [_ziel()], tmp_path / "f.jsonl")
    assert "Feuerkette uebersprungen" in capsys.readouterr().out


def test_wochendeckel_wirkt_ueber_neustarts_hinweg(tmp_path):
    # Der Deckel liest die eigene Spur zurueck statt einen Zaehler zu
    # halten - ein Neustart darf ihn nicht zuruecksetzen.
    from operations.pipeline import isw_rekorder as rek

    pfad = tmp_path / "feuerbefehle.jsonl"
    for slug, oid in (("a", 1), ("b", 2), ("c", 3)):
        rek._feuern([_meldung(slug=slug)], [_ziel(slug=slug, objectid=oid)],
                    pfad)
    zeilen = [json.loads(z) for z in
              pfad.read_text(encoding="utf-8").splitlines()]
    befehle = [z for z in zeilen if z["art"] == "feuerbefehl"]
    assert len(befehle) == 2
    assert [z["grund"] for z in zeilen if z["art"] == "ablehnung"] \
        == ["wochendeckel"]
