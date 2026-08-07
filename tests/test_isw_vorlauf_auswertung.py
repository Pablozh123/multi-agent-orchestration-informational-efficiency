"""Tests fuer die ISW-Vorlauf-Auswertung: Verknuepfung, Dedupe, Klassen."""
from __future__ import annotations

import json

from operations.analysis import isw_vorlauf_auswertung as ava


def _kandidat(slug="m1", layer="infiltration", zeit="2026-07-29T22:09:43Z",
              preis=0.89, auswertbar=True, buch=None):
    return {
        "art": "kandidat_treffer", "zeit_utc": zeit, "slug": slug,
        "layer": layer, "siedlung": "Testort", "objectid": 1,
        "feature_zeit_utc": "2026-07-29T22:07:43Z", "vorlauf_s": 120.1,
        "polaritaet": "russisch", "kriterium": "beruehrung",
        "auswertbar": auswertbar, "markt_bereits_qualifiziert": False,
        "preis_yes": preis, "preis_uebersprungen": False,
        "buch": buch if buch is not None else
        {"best_bid": 0.87, "best_ask": 0.91,
         "usd_bis_030": 150.0, "usd_bis_050": 400.0},
    }


def _bestaetigt(slug="m1", layer="infiltration",
                sichtung="2026-07-29T22:09:43Z"):
    return {"art": "treffer_bestaetigt", "zeit_utc": "2026-07-29T23:10:14Z",
            "slug": slug, "layer": layer, "siedlung": "Testort",
            "auswertbar": True, "erste_sichtung_utc": sichtung,
            "dauer_s": 3631.1, "preis_yes_jetzt": 0.9555}


def _nachfassung(minute, preis, slug="m1", layer="infiltration",
                 zeit="2026-07-29T22:10:51Z", real_s=67.9):
    return {"art": "nachfassung", "zeit_utc": zeit, "slug": slug,
            "layer": layer, "geplante_minute": minute, "real_s": real_s,
            "preis_yes": preis}


def _schreibe(pfad, zeilen):
    pfad.write_text("\n".join(json.dumps(z) for z in zeilen) + "\n",
                    encoding="utf-8")
    return pfad


# ------------------------------------------------------------- Verknuepfung

def test_bestaetigter_kandidat_wird_zeile_mit_nachfassungen():
    zeilen = [
        _kandidat(),
        _nachfassung(1, 0.895),
        _nachfassung(5, 0.895, zeit="2026-07-29T22:14:49Z", real_s=305.6),
        _nachfassung(30, 0.955, zeit="2026-07-29T22:39:57Z", real_s=1813.6),
        _bestaetigt(),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert len(ereignisse) == 1
    e = ereignisse[0]
    assert e.status == "bestaetigt"
    assert e.preis_t0 == 0.89
    assert e.preis_t1 == 0.895
    assert e.preis_t30 == 0.955
    assert e.delta_t30 == 0.065
    assert e.best_ask_t0 == 0.91
    assert e.klasse == "antizipiert"
    assert zaehler["kandidat_treffer"] == 1


def test_verworfener_kandidat_liefert_keine_zeile():
    zeilen = [
        _kandidat(),
        {"art": "treffer_verworfen", "zeit_utc": "2026-07-29T22:30:00Z",
         "slug": "m1", "layer": "infiltration",
         "erste_sichtung_utc": "2026-07-29T22:09:43Z", "dauer_s": 1217.0},
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert ereignisse == []
    assert zaehler["treffer_verworfen"] == 1


def test_offener_kandidat_liefert_keine_zeile():
    """Noch im Beruhigungsfenster -> gehoert nicht in die Verteilung."""
    ereignisse, _ = ava.baue_ereignisse([_kandidat()])
    assert ereignisse == []


def test_markt_geschlossen_ist_eigener_status():
    zeilen = [
        _kandidat(),
        {"art": "treffer_markt_geschlossen",
         "zeit_utc": "2026-07-29T22:40:00Z", "slug": "m1",
         "layer": "infiltration",
         "erste_sichtung_utc": "2026-07-29T22:09:43Z"},
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    assert len(ereignisse) == 1
    assert ereignisse[0].status == "markt_geschlossen"


def test_nicht_auswertbare_kandidaten_werden_nur_gezaehlt():
    zeilen = [_kandidat(auswertbar=False), _bestaetigt()]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert ereignisse == []
    assert zaehler["nicht_auswertbar"] == 1


def test_doppelte_kandidatenzeile_wird_dedupliziert():
    """Restluecke des Rekorders: Absturz zwischen Protokoll und Zustand."""
    zeilen = [_kandidat(), _kandidat(), _bestaetigt()]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert len(ereignisse) == 1
    assert zaehler["kandidat_treffer_dupliziert"] == 1


def test_nachfassung_ordnet_ueber_reale_zeit_zu():
    """Zwei Kandidaten desselben Markts, verschiedene Sichtungen: die
    Nachfassung gehoert zum zeitlich passenden."""
    zeilen = [
        _kandidat(zeit="2026-07-29T22:09:43Z"),
        _kandidat(zeit="2026-07-29T23:30:00Z", preis=0.4),
        _nachfassung(30, 0.955, zeit="2026-07-29T22:39:57Z", real_s=1813.6),
        _bestaetigt(sichtung="2026-07-29T22:09:43Z"),
        _bestaetigt(sichtung="2026-07-29T23:30:00Z"),
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    assert len(ereignisse) == 2
    frueh = [e for e in ereignisse if e.erkannt_utc == "2026-07-29T22:09:43Z"][0]
    spaet = [e for e in ereignisse if e.erkannt_utc == "2026-07-29T23:30:00Z"][0]
    assert frueh.preis_t30 == 0.955
    assert spaet.preis_t30 is None


def test_unzuordenbare_nachfassung_wird_gezaehlt():
    zeilen = [
        _kandidat(),
        _nachfassung(30, 0.9, zeit="2026-07-30T10:00:00Z", real_s=60.0),
        _bestaetigt(),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert ereignisse[0].preis_t30 is None
    assert zaehler["nachfassung_unzuordenbar"] == 1


# ------------------------------------------------------------ Klassifikation

def test_klassifikation_schwellen():
    assert ava.klassifiziere(0.046) == "ueberraschung"
    assert ava.klassifiziere(0.49) == "ueberraschung"
    assert ava.klassifiziere(0.50) == "teilweise"
    assert ava.klassifiziere(0.85) == "teilweise"
    assert ava.klassifiziere(0.89) == "antizipiert"
    assert ava.klassifiziere(None) == "unbekannt"


def test_ereignis_nach_ausfall_wird_unsicher():
    """Regression 31.07.: War der Rekorder beim ISW-Edit unten, stammt der
    'T+0'-Preis von nach dem Neustart. Eine Ueberraschung saehe dann wie
    ein antizipierter Fall aus — genau die Richtung, die den
    Ueberraschungsanteil und damit die Go-Entscheidung druecken wuerde."""
    k = _kandidat(preis=0.92)
    k["nach_ausfall_s"] = 910.5
    ereignisse, _ = ava.baue_ereignisse([k, _bestaetigt()])
    assert ereignisse[0].klasse == "unsicher"
    assert ereignisse[0].nach_ausfall_s == 910.5


def test_unsichere_ereignisse_zaehlen_nicht_im_nenner():
    def _e(slug, siedlung, preis, ausfall=0.0):
        return ava.Ereignis(slug=slug, siedlung=siedlung, layer="infiltration",
                            quelle="rekorder", status="bestaetigt",
                            feature_zeit_utc=None,
                            erkannt_utc=f"2026-07-29T{siedlung}:00:00Z",
                            vorlauf_s=None, preis_t0=preis, best_ask_t0=None,
                            buch_usd_030=None, buch_usd_050=None,
                            preis_t1=None, preis_t5=None, preis_t30=None,
                            delta_t30=None,
                            klasse=ava.klassifiziere(preis, ausfall),
                            nach_ausfall_s=ausfall)
    ereignisse = [_e("a", "10", 0.10), _e("b", "11", 0.90),
                  _e("c", "12", 0.95, ausfall=900.0)]
    z = ava.fasse_zusammen(ereignisse)
    assert z["n_siedlungsereignisse"] == 3
    assert z["n_klassifizierbar"] == 2
    assert z["anteil_ueberraschung"] == 0.5   # nicht 0.333
    assert z["klassen_siedlungsereignisse"]["unsicher"] == 1


def test_klassifiziere_ausfall_schlaegt_preis():
    assert ava.klassifiziere(0.95, 900.0) == "unsicher"
    assert ava.klassifiziere(0.05, 900.0) == "unsicher"
    assert ava.klassifiziere(0.95, 0.0) == "antizipiert"
    assert ava.klassifiziere(0.95, None) == "antizipiert"


def test_kandidat_ohne_preis_wird_unbekannt():
    k = _kandidat(preis=None)
    k["preis_uebersprungen"] = True
    ereignisse, _ = ava.baue_ereignisse([k, _bestaetigt()])
    assert ereignisse[0].klasse == "unbekannt"
    assert ereignisse[0].delta_t30 is None


# ------------------------------------------------------------- Zusammenfassung

def test_zusammenfassung_anteil_ueberraschung():
    zeilen = [
        _kandidat(slug="a", preis=0.10),
        _bestaetigt(slug="a"),
        _kandidat(slug="b", preis=0.90),
        _bestaetigt(slug="b"),
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    # verschiedene Siedlungen simulieren (Standard-Attrappe teilt "Testort")
    ereignisse[0].siedlung = "Ort A"
    ereignisse[1].siedlung = "Ort B"
    z = ava.fasse_zusammen(ereignisse)
    assert z["n_marktzeilen"] == 2
    assert z["n_siedlungsereignisse"] == 2
    assert z["anteil_ueberraschung"] == 0.5
    assert z["je_klasse_marktzeilen"]["ueberraschung"]["n"] == 1
    assert z["je_klasse_marktzeilen"]["antizipiert"]["n"] == 1


def test_zusammenfassung_gruppiert_maerkte_derselben_siedlung():
    """Zwei Deadlines derselben Siedlung = EIN Siedlungsereignis; der
    Anteil Ueberraschung darf korrelierte Instanzen nicht doppelt zaehlen
    (Fall Oleksiyevo-Druzhkivka 29.07.: zwei enter-Maerkte, ein Ereignis)."""
    zeilen = [
        _kandidat(slug="enter-sep", preis=0.89),
        _bestaetigt(slug="enter-sep"),
        _kandidat(slug="enter-dez", preis=0.915),
        _bestaetigt(slug="enter-dez"),
    ]
    ereignisse, _ = ava.baue_ereignisse(zeilen)
    z = ava.fasse_zusammen(ereignisse)
    assert z["n_marktzeilen"] == 2
    assert z["n_siedlungsereignisse"] == 1
    assert z["klassen_siedlungsereignisse"] == {"antizipiert": 1}
    assert z["anteil_ueberraschung"] == 0.0


def test_referenzfall_ist_ueberraschung_mit_vorlauf():
    e = ava.REFERENZ_KRASNOIARSKE
    assert e.quelle == "rekonstruiert"
    assert e.klasse == "ueberraschung"
    assert e.vorlauf_s == 1123.0
    assert ava.klassifiziere(e.preis_t0) == "ueberraschung"


# --------------------------------------------------------------- Ein/Ausgabe

def test_lies_protokoll_zaehlt_defekte_zeilen(tmp_path):
    pfad = tmp_path / "p.jsonl"
    pfad.write_text(json.dumps(_kandidat()) + "\n{kaputt\n\n",
                    encoding="utf-8")
    zeilen = ava.lies_protokoll(pfad)
    _, zaehler = ava.baue_ereignisse(zeilen)
    assert zaehler["defekte_zeilen"] == 1
    assert zaehler["kandidat_treffer"] == 1


def test_main_ende_zu_ende_mit_json(tmp_path, capsys):
    pfad = _schreibe(tmp_path / "p.jsonl", [
        _kandidat(),
        _nachfassung(30, 0.955, zeit="2026-07-29T22:39:57Z", real_s=1813.6),
        _bestaetigt(),
    ])
    json_pfad = tmp_path / "out.json"
    code = ava.main(["--protokoll", str(pfad), "--json", str(json_pfad),
                     "--mit-referenz"])
    assert code == 0
    ausgabe = capsys.readouterr().out
    assert "Krasnoyarske" in ausgabe          # Referenzzeile drin
    assert "ueberraschung*" in ausgabe        # als rekonstruiert markiert
    ergebnis = json.loads(json_pfad.read_text(encoding="utf-8"))
    assert ergebnis["zusammenfassung"]["n_marktzeilen"] == 2
    assert ergebnis["zusammenfassung"]["n_siedlungsereignisse"] == 2
    assert ergebnis["zusammenfassung"]["anteil_ueberraschung"] == 0.5


def test_verspaetete_nachfassung_wird_verworfen():
    """Review-Befund: nach Absturz + Watchdog-Neustart feuert eine
    30-min-Nachfassung Stunden spaeter. Ihr Preis darf nicht als T+30
    in delta_t30 landen (hebt Go-Kriterium 3 kuenstlich)."""
    zeilen = [
        _kandidat(preis=0.05),
        _nachfassung(30, 0.95, zeit="2026-07-29T23:20:00Z", real_s=4217.0),
        _bestaetigt(),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert ereignisse[0].preis_t30 is None
    assert ereignisse[0].delta_t30 is None
    assert zaehler["nachfassung_verspaetet"] == 1


def test_leicht_verspaetete_nachfassung_zaehlt_noch():
    """Ein Poll-Zyklus Verzug (Ruhe-Takt 120 s) ist normal, kein Fehler."""
    zeilen = [
        _kandidat(preis=0.05),
        # Sichtung 22:09:43 + real_s 1900 s -> Messung 22:41:23
        _nachfassung(30, 0.4, zeit="2026-07-29T22:41:23Z", real_s=1900.0),
        _bestaetigt(),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert ereignisse[0].preis_t30 == 0.4
    assert zaehler["nachfassung_verspaetet"] == 0


def test_abschluss_ohne_kandidat_wird_gezaehlt():
    """Ging die Kandidatenzeile beim Schreiben verloren, fehlt das
    Ereignis still in der Verteilung — das muss sichtbar sein."""
    _, zaehler = ava.baue_ereignisse([_bestaetigt(slug="verwaist")])
    assert zaehler["abschluss_ohne_kandidat"] == 1


def test_wiederholte_kandidaten_desselben_markts_werden_ausgewiesen():
    """Doppelerkennung nach Absturz hat verschiedene zeit_utc — der
    Dedupe greift dort nicht, also wenigstens ausweisen."""
    zeilen = [
        _kandidat(zeit="2026-07-29T22:09:43Z"),
        _kandidat(zeit="2026-07-29T22:15:00Z"),
        _bestaetigt(sichtung="2026-07-29T22:09:43Z"),
        _bestaetigt(sichtung="2026-07-29T22:15:00Z"),
    ]
    ereignisse, zaehler = ava.baue_ereignisse(zeilen)
    assert len(ereignisse) == 2
    assert zaehler["kandidat_treffer_wiederholt"] == 1


# ------------------------------------------------------------- Go-Pruefung

def test_go_kriterien_rechnen_ueber_ueberraschungs_ereignisse():
    """Review-Befund: Kriterien 2/3 gelten 'in den Ueberraschungsfaellen'
    — also ueber Siedlungsereignisse, nicht ueber einzeln klassifizierte
    Marktzeilen. Ereignis A (Gruppenmedian 0.425) ist Ueberraschung, B
    (Gruppenmedian 0.60) nicht; Bs 0.48er-Zeile darf den Median nicht
    verunreinigen."""
    ereignisse = [
        ava.Ereignis(slug="a1", siedlung="A", layer="infiltration",
                     quelle="rekorder", status="bestaetigt",
                     feature_zeit_utc=None, erkannt_utc="2026-07-29T10:00:00Z",
                     vorlauf_s=100.0, preis_t0=0.40, best_ask_t0=None,
                     buch_usd_030=None, buch_usd_050=200.0, preis_t1=None,
                     preis_t5=None, preis_t30=0.70, delta_t30=0.30,
                     klasse="ueberraschung"),
        ava.Ereignis(slug="a2", siedlung="A", layer="infiltration",
                     quelle="rekorder", status="bestaetigt",
                     feature_zeit_utc=None, erkannt_utc="2026-07-29T10:00:00Z",
                     vorlauf_s=100.0, preis_t0=0.45, best_ask_t0=None,
                     buch_usd_030=None, buch_usd_050=200.0, preis_t1=None,
                     preis_t5=None, preis_t30=0.75, delta_t30=0.30,
                     klasse="ueberraschung"),
        ava.Ereignis(slug="b1", siedlung="B", layer="infiltration",
                     quelle="rekorder", status="bestaetigt",
                     feature_zeit_utc=None, erkannt_utc="2026-07-29T11:00:00Z",
                     vorlauf_s=100.0, preis_t0=0.48, best_ask_t0=None,
                     buch_usd_030=None, buch_usd_050=50.0, preis_t1=None,
                     preis_t5=None, preis_t30=0.49, delta_t30=0.01,
                     klasse="ueberraschung"),
        ava.Ereignis(slug="b2", siedlung="B", layer="infiltration",
                     quelle="rekorder", status="bestaetigt",
                     feature_zeit_utc=None, erkannt_utc="2026-07-29T11:00:00Z",
                     vorlauf_s=100.0, preis_t0=0.72, best_ask_t0=None,
                     buch_usd_030=None, buch_usd_050=50.0, preis_t1=None,
                     preis_t5=None, preis_t30=0.73, delta_t30=0.01,
                     klasse="teilweise"),
    ]
    z = ava.fasse_zusammen(ereignisse)
    assert z["n_siedlungsereignisse"] == 2
    assert z["klassen_siedlungsereignisse"] == {"ueberraschung": 1,
                                                "teilweise": 1}
    kriterien = z["go_pruefung"]["kriterien"]
    # nur Ereignis A zaehlt: delta 0.30, Tiefe 200 USD
    assert kriterien["3_median_delta_t30"]["wert"] == 0.30
    assert kriterien["2_median_tiefe_usd_050"]["wert"] == 200.0


def test_unbekannte_ereignisse_verwaessern_den_anteil_nicht():
    """Budget erschoepft -> kein T+0-Preis. Das ist keine Aussage
    'war eingepreist' und darf die 20-%-Schwelle nicht kippen."""
    def _e(slug, preis, siedlung):
        return ava.Ereignis(slug=slug, siedlung=siedlung, layer="infiltration",
                            quelle="rekorder", status="bestaetigt",
                            feature_zeit_utc=None,
                            erkannt_utc=f"2026-07-29T{siedlung}:00:00Z",
                            vorlauf_s=None, preis_t0=preis, best_ask_t0=None,
                            buch_usd_030=None, buch_usd_050=None,
                            preis_t1=None, preis_t5=None, preis_t30=None,
                            delta_t30=None, klasse=ava.klassifiziere(preis))
    ereignisse = [_e("a", 0.10, "10"), _e("b", 0.90, "11"),
                  _e("c", None, "12"), _e("d", None, "13")]
    z = ava.fasse_zusammen(ereignisse)
    assert z["n_siedlungsereignisse"] == 4
    assert z["n_klassifizierbar"] == 2
    assert z["anteil_ueberraschung"] == 0.5   # nicht 0.25
    assert z["klassen_siedlungsereignisse"]["unbekannt"] == 2


def test_go_entscheidung_weiter_messen_bei_zu_kleinem_n():
    ereignisse = [ava.REFERENZ_KRASNOIARSKE]
    z = ava.fasse_zusammen(ereignisse)
    assert z["go_pruefung"]["entscheidung"] == "weiter_messen"


def test_go_entscheidung_go_paper_bei_erfuellten_kriterien():
    schwellen = {"min_n_ereignisse": 2, "min_anteil_ueberraschung": 0.20,
                 "min_median_tiefe_usd": 100.0, "min_median_delta_t30": 0.10}
    def _e(slug, siedlung, preis, delta, tiefe):
        return ava.Ereignis(slug=slug, siedlung=siedlung, layer="infiltration",
                            quelle="rekorder", status="bestaetigt",
                            feature_zeit_utc=None,
                            erkannt_utc=f"2026-07-29T{siedlung}:00:00Z",
                            vorlauf_s=600.0, preis_t0=preis, best_ask_t0=None,
                            buch_usd_030=None, buch_usd_050=tiefe,
                            preis_t1=None, preis_t5=None, preis_t30=None,
                            delta_t30=delta, klasse=ava.klassifiziere(preis))
    ereignisse = [_e("a", "10", 0.10, 0.50, 300.0),
                  _e("b", "11", 0.90, 0.02, 300.0)]
    z = ava.fasse_zusammen(ereignisse, schwellen)
    assert z["go_pruefung"]["entscheidung"] == "go_paper"
    assert all(k["erfuellt"] for k in z["go_pruefung"]["kriterien"].values())


def test_go_entscheidung_no_go_bei_duennem_buch():
    schwellen = {"min_n_ereignisse": 1, "min_anteil_ueberraschung": 0.20,
                 "min_median_tiefe_usd": 100.0, "min_median_delta_t30": 0.10}
    e = ava.Ereignis(slug="a", siedlung="A", layer="infiltration",
                     quelle="rekorder", status="bestaetigt",
                     feature_zeit_utc=None, erkannt_utc="2026-07-29T10:00:00Z",
                     vorlauf_s=600.0, preis_t0=0.10, best_ask_t0=None,
                     buch_usd_030=None, buch_usd_050=20.0, preis_t1=None,
                     preis_t5=None, preis_t30=None, delta_t30=0.50,
                     klasse="ueberraschung")
    z = ava.fasse_zusammen([e], schwellen)
    assert z["go_pruefung"]["entscheidung"] == "no_go"
    assert z["go_pruefung"]["kriterien"]["2_median_tiefe_usd_050"]["erfuellt"] is False


def test_kandidat_ohne_zeitstempel_crasht_nicht():
    kaputt = _kandidat()
    del kaputt["zeit_utc"]
    ereignisse, zaehler = ava.baue_ereignisse([kaputt])
    assert ereignisse == []
    assert zaehler["defekte_zeilen"] == 1


def test_main_fehlendes_protokoll(tmp_path):
    assert ava.main(["--protokoll", str(tmp_path / "fehlt.jsonl")]) == 1
