"""Tests fuer den ISW-Karten-Watcher: Parsing und Geometrie.

Der Geometrieteil ersetzt shapely; er ist deshalb hier vollstaendig
abgedeckt (Enthaltung in beide Richtungen, Ueberlappung ohne enthaltene
Ecke, Loecher, disjunkte Faelle).
"""
from __future__ import annotations

from operations.pipeline import isw_karten_watch as ikw

# Quadrat (0,0)-(10,10), ArcGIS-Ringe sind geschlossen.
QUADRAT = [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]]


def _verschoben(ringe, dx, dy):
    return [[[x + dx, y + dy] for x, y in ring] for ring in ringe]


# ------------------------------------------------------------------ Parsing

def test_koordinate_aus_beschreibung_liest_marktformat():
    text = ("This market will resolve to Yes if, according to the ISW map, "
            "Russia captures any territory of Krasnoiarske, Donetsk Oblast, "
            "(48.419117° N, 37.125165° E) between market creation ...")
    assert ikw.koordinate_aus_beschreibung(text) == (48.419117, 37.125165)


def test_koordinate_ohne_treffer_gibt_none():
    assert ikw.koordinate_aus_beschreibung("kein Ort genannt") is None
    assert ikw.koordinate_aus_beschreibung(None) is None
    assert ikw.koordinate_aus_beschreibung("") is None


def test_polaritaet_trennt_re_enter_von_enter():
    """Der eigene Fehlerfall: "enter" im Slug faengt "re-enter" mit."""
    assert ikw.markt_polaritaet("will-russia-enter-krasnoiarske-by-july-31") == "russisch"
    assert ikw.markt_polaritaet("will-ukraine-re-enter-myrnohrad-by-december-31") == "ukrainisch"
    assert ikw.markt_polaritaet("will-ukraine-re-enter-hryshyne-by-september-30") == "ukrainisch"
    assert ikw.markt_polaritaet("will-russia-capture-all-of-lyman-by-december-31-2026") == "russisch"
    assert ikw.markt_polaritaet(None) == "unklar"
    assert ikw.markt_polaritaet("irgendein-anderer-markt") == "unklar"


def test_kriterium_trennt_beruehrung_von_vollueberdeckung():
    assert ikw.markt_kriterium("will-russia-enter-krasnoiarske-by-july-31") == "beruehrung"
    assert ikw.markt_kriterium("will-russia-capture-all-of-chasiv-yar-by-december-31") == "vollstaendig"
    assert ikw.markt_kriterium("will-russia-capture-kupiansk-by-september-30-2026") == "vollstaendig"


# ---------------------------------------------------------------- Geometrie

def test_punkt_in_polygon_innen_und_aussen():
    assert ikw.punkt_in_polygon(5, 5, QUADRAT) is True
    assert ikw.punkt_in_polygon(15, 5, QUADRAT) is False
    assert ikw.punkt_in_polygon(-1, -1, QUADRAT) is False


def test_punkt_in_polygon_beachtet_loch():
    mit_loch = [
        [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]],
        [[4, 4], [4, 6], [6, 6], [6, 4], [4, 4]],
    ]
    assert ikw.punkt_in_polygon(1, 1, mit_loch) is True
    assert ikw.punkt_in_polygon(5, 5, mit_loch) is False


def test_strecken_schneiden_kreuz_und_parallel():
    assert ikw.strecken_schneiden([0, 0], [10, 10], [0, 10], [10, 0]) is True
    assert ikw.strecken_schneiden([0, 0], [1, 1], [5, 5], [6, 6]) is False


def test_polygone_beruehren_disjunkt():
    assert ikw.polygone_beruehren(QUADRAT, _verschoben(QUADRAT, 100, 100)) is False


def test_polygone_beruehren_ueberlappung():
    assert ikw.polygone_beruehren(QUADRAT, _verschoben(QUADRAT, 5, 5)) is True


def test_polygone_beruehren_vollstaendige_enthaltung_in_beide_richtungen():
    klein = [[[4, 4], [4, 6], [6, 6], [6, 4], [4, 4]]]
    assert ikw.polygone_beruehren(QUADRAT, klein) is True
    assert ikw.polygone_beruehren(klein, QUADRAT) is True


def test_polygone_beruehren_kreuz_ohne_enthaltene_ecke():
    """Zwei Rechtecke im Kreuz: keine Ecke liegt im anderen Polygon."""
    waagerecht = [[[0, 4], [0, 6], [10, 6], [10, 4], [0, 4]]]
    senkrecht = [[[4, 0], [4, 10], [6, 10], [6, 0], [4, 0]]]
    assert ikw.polygone_beruehren(waagerecht, senkrecht) is True


def test_polygone_beruehren_leere_geometrie():
    assert ikw.polygone_beruehren([], QUADRAT) is False
    assert ikw.polygone_beruehren(QUADRAT, []) is False


def test_bounding_box():
    assert ikw.bounding_box(QUADRAT) == (0, 0, 10, 10)


# ------------------------------------------------------------ Rebuild-Bremse

def test_bulk_rebuild_erkennt_massenanlage():
    """Muster vom 21.07.: viele Features in kurzer Zeit."""
    basis = 1_784_000_000_000
    stempel = [basis + i * 1000 for i in range(20)]  # 20 Stueck in 20 s
    assert ikw.ist_bulk_rebuild(stempel) is True


def test_bulk_rebuild_ignoriert_einzelne_edits():
    """Muster vom 22.07.: fuenf Edits ueber Stunden verteilt."""
    basis = 1_784_000_000_000
    stunde = 3_600_000
    stempel = [basis, basis + stunde, basis + 2 * stunde,
               basis + 3 * stunde, basis + 4 * stunde]
    assert ikw.ist_bulk_rebuild(stempel) is False


def test_bulk_rebuild_unter_schwelle():
    basis = 1_784_000_000_000
    assert ikw.ist_bulk_rebuild([basis + i for i in range(5)], schwelle=10) is False


def test_bulk_rebuild_leere_liste():
    assert ikw.ist_bulk_rebuild([]) is False


def test_neue_zeitstempel_filtert_auf_den_letzten_stand():
    """Regression: die Bremse darf nur NEUE Features bewerten.

    Ungefiltert bewertet sie die gesamte Layer-Historie, die durch die
    periodischen ISW-Rebuilds immer geclustert ist — die Bremse greift dann
    dauerhaft und der Rekorder liefert nie ein Signal.
    """
    stempel = [100, 200, 300, 400]
    assert ikw.neue_zeitstempel(stempel, 250) == [300, 400]
    assert ikw.neue_zeitstempel(stempel, None) == stempel
    assert ikw.neue_zeitstempel(stempel, 400) == []


def test_neue_zeitstempel_wirft_none_weg():
    assert ikw.neue_zeitstempel([100, None, 300], 50) == [100, 300]


def test_historische_haeufung_bremst_nicht_wenn_nur_eines_neu_ist():
    """Der Fall aus dem Probelauf: 163 alte Features, ein neues."""
    basis = 1_784_000_000_000
    alt = [basis + i * 1000 for i in range(163)]
    letzter_stand = alt[-1]
    neu = alt + [letzter_stand + 86_400_000]
    frisch = ikw.neue_zeitstempel(neu, letzter_stand)
    assert frisch == [letzter_stand + 86_400_000]
    assert ikw.ist_bulk_rebuild(frisch) is False
    # ungefiltert haette die Bremse gegriffen
    assert ikw.ist_bulk_rebuild(neu) is True


def test_gains24h_nutzt_fid_als_id_feld():
    """Regression: harte OBJECTID-Annahme quittiert ArcGIS mit HTTP 400."""
    assert ikw.LAYER_NACH_NAME["gains24h"].id_feld == "FID"
    assert ikw.LAYER_NACH_NAME["infiltration"].id_feld == "OBJECTID"


# ------------------------------------------------------------- Layer-Wissen

def test_qualifizierende_layer_sind_die_vier_der_regel():
    assert {layer.name for layer in ikw.QUALIFIZIERENDE_LAYER} == {
        "infiltration", "gains24h", "advance", "control"
    }


def test_infiltration_steht_vor_control():
    """Niedrigste Beweisschwelle zuerst — sie schaltet frueher."""
    namen = [layer.name for layer in ikw.QUALIFIZIERENDE_LAYER]
    assert namen.index("infiltration") < namen.index("control")


def test_gains24h_ist_nicht_delta_faehig():
    """Ohne Edit-Felder bleibt nur der Geometrie-Diff."""
    assert ikw.LAYER_NACH_NAME["gains24h"].delta_faehig is False
    assert ikw.LAYER_NACH_NAME["infiltration"].delta_faehig is True


def test_flaeche_bevorzugt_creation_vor_edit():
    flaeche = ikw.ISWFlaeche("infiltration", 1, QUADRAT,
                             creation_ms=1000, edit_ms=2000)
    assert flaeche.zeitstempel_ms == 1000
    nur_edit = ikw.ISWFlaeche("control", 2, QUADRAT, creation_ms=None, edit_ms=2000)
    assert nur_edit.zeitstempel_ms == 2000
