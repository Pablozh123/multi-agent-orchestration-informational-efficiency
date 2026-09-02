"""Tests fuer den ISW-Karten-Watcher: Parsing, Geometrie, Client.

Der Geometrieteil ersetzt shapely; er ist deshalb hier vollstaendig
abgedeckt (Enthaltung in beide Richtungen, Ueberlappung ohne enthaltene
Ecke, Loecher, Multipart-Features, disjunkte Faelle).
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


def test_polaritaet_entscheidet_ueber_das_subjekt():
    assert ikw.markt_polaritaet("will-russia-enter-krasnoiarske-by-july-31") == "russisch"
    assert ikw.markt_polaritaet("will-russia-capture-all-of-lyman-by-december-31-2026") == "russisch"
    assert ikw.markt_polaritaet("will-ukraine-re-enter-myrnohrad-by-december-31") == "ukrainisch"
    assert ikw.markt_polaritaet("will-ukraine-recapture-crimean-territory-by-june-30") == "ukrainisch"
    assert ikw.markt_polaritaet(None) == "unklar"
    assert ikw.markt_polaritaet("untitled-market-1-20260630004444282") == "unklar"


def test_polaritaet_recapture_folgt_dem_subjekt():
    """Review-Befund: ein '-recapture-'-Substring-Filter haette
    will-russia-recapture-* faelschlich ukrainisch eingefaerbt."""
    assert ikw.markt_polaritaet("will-russia-recapture-kherson-by-december-31") == "russisch"
    assert ikw.markt_polaritaet("will-ukraine-recapture-bakhmut-by-december-31") == "ukrainisch"


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
    assert ikw.polygone_beruehren([[]], QUADRAT) is False


def test_polygone_beruehren_kleines_ganz_in_grossem():
    """Der haeufigste Fall: Siedlung liegt tief im besetzten Gebiet."""
    gross = [[[0, 0], [0, 1000], [1000, 1000], [1000, 0], [0, 0]]]
    klein = [[[500, 500], [500, 501], [501, 501], [501, 500], [500, 500]]]
    assert ikw.polygone_beruehren(gross, klein) is True
    assert ikw.polygone_beruehren(klein, gross) is True


def test_polygone_beruehren_siedlung_im_loch_ist_kein_treffer():
    """Ein Loch im Kontroll-Polygon ist NICHT besetzt."""
    mit_loch = [
        [[0, 0], [0, 100], [100, 100], [100, 0], [0, 0]],
        [[40, 40], [40, 60], [60, 60], [60, 40], [40, 40]],
    ]
    im_loch = [[[49, 49], [49, 51], [51, 51], [51, 49], [49, 49]]]
    assert ikw.polygone_beruehren(mit_loch, im_loch) is False
    ausserhalb_des_lochs = [[[10, 10], [10, 12], [12, 12], [12, 10], [10, 10]]]
    assert ikw.polygone_beruehren(mit_loch, ausserhalb_des_lochs) is True


def test_polygone_beruehren_multipart_teil_in_siedlung():
    """Review-Befund 24.07. (mit Repro belegt): ArcGIS-Features duerfen
    mehrere Aussenringe tragen. Liegt ein Teil ganz in der Siedlung,
    waehrend der erste Ring weit entfernt ist, muss das ein Treffer sein.
    Vor dem Fix pruefte Stufe 3 nur den ersten Punkt des ERSTEN Rings."""
    multipart = [
        [[100, 100], [100, 101], [101, 101], [101, 100], [100, 100]],
        [[4, 4], [4, 6], [6, 6], [6, 4], [4, 4]],
    ]
    assert ikw.polygone_beruehren(multipart, QUADRAT) is True
    # Spiegelfall: Siedlung mit Exklave, Exklave liegt im ISW-Polygon.
    assert ikw.polygone_beruehren(QUADRAT, multipart) is True


def test_polygone_beruehren_multipart_alle_teile_draussen():
    multipart = [
        [[100, 100], [100, 101], [101, 101], [101, 100], [100, 100]],
        [[200, 200], [200, 201], [201, 201], [201, 200], [200, 200]],
    ]
    assert ikw.polygone_beruehren(multipart, QUADRAT) is False


def test_bounding_box():
    assert ikw.bounding_box(QUADRAT) == (0, 0, 10, 10)


def test_polygone_beruehren_bleibt_bei_grossem_polygon_schnell():
    """Regression: das groesste ISW-Kontroll-Polygon hat 51'901 Stuetzpunkte.

    Der naive Test kostete dafuer 5.6 s je Siedlung; der Rekorder blieb im
    ersten Durchlauf haengen. Hier ein Ring vergleichbarer Groesse.
    """
    import math
    import time

    n = 50_000
    ring = [[math.cos(2 * math.pi * i / n) * 100,
             math.sin(2 * math.pi * i / n) * 100] for i in range(n)]
    ring.append(ring[0])
    gross = [ring]
    innen = [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
    draussen = [[[500, 500], [500, 501], [501, 501], [501, 500], [500, 500]]]

    start = time.perf_counter()
    assert ikw.polygone_beruehren(gross, innen) is True
    assert ikw.polygone_beruehren(gross, draussen) is False
    dauer = time.perf_counter() - start
    assert dauer < 1.0, f"zu langsam: {dauer:.2f}s fuer zwei Schnitte"


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


def test_gains24h_nutzt_fid_als_id_feld():
    """Regression: harte OBJECTID-Annahme quittiert ArcGIS mit HTTP 400."""
    assert ikw.LAYER_NACH_NAME["gains24h"].id_feld == "FID"
    assert ikw.LAYER_NACH_NAME["infiltration"].id_feld == "OBJECTID"


def test_juengste_aenderung_ist_maximum_aus_anlage_und_edit():
    """Review-Befund 24.07.: Anlage-vor-Edit mass bei erweiterten Polygonen
    Tage statt Sekunden. Die Ereigniszeit ist die JUENGSTE Aenderung."""
    beides = ikw.ISWFlaeche("infiltration", 1, QUADRAT,
                            creation_ms=1000, edit_ms=2000)
    assert beides.juengste_aenderung_ms == 2000
    nur_anlage = ikw.ISWFlaeche("infiltration", 2, QUADRAT, creation_ms=1000)
    assert nur_anlage.juengste_aenderung_ms == 1000
    nur_edit = ikw.ISWFlaeche("control", 3, QUADRAT, edit_ms=2000)
    assert nur_edit.juengste_aenderung_ms == 2000
    ohne = ikw.ISWFlaeche("gains24h", 4, QUADRAT)
    assert ohne.juengste_aenderung_ms is None


# ----------------------------------------------------------------- Client

def test_json_wiederholt_bei_drosselung(monkeypatch):
    """ArcGIS meldet 429 im error-Objekt einer 200-Antwort."""
    karte = ikw.ISWKarte(max_versuche=3, backoff_start_s=0)
    versuche = {"n": 0}

    def _antwort(url, daten):
        versuche["n"] += 1
        if versuche["n"] < 3:
            raise ikw.ISWFehler(429, "Too many requests")
        return {"ok": True}

    monkeypatch.setattr(karte, "_einmal", _antwort)
    assert karte._json("egal") == {"ok": True}
    assert versuche["n"] == 3


def test_json_gibt_nach_max_versuchen_auf(monkeypatch):
    karte = ikw.ISWKarte(max_versuche=2, backoff_start_s=0)

    def _immer_429(url, daten):
        raise ikw.ISWFehler(429, "Too many requests")

    monkeypatch.setattr(karte, "_einmal", _immer_429)
    try:
        karte._json("egal")
    except ikw.ISWFehler as fehler:
        assert fehler.status == 429
    else:
        raise AssertionError("haette ISWFehler werfen muessen")


def test_json_wiederholt_nicht_bei_dauerhaftem_fehler(monkeypatch):
    """HTTP 400 ist ein Programmfehler — Wiederholen hilft nicht."""
    karte = ikw.ISWKarte(max_versuche=4, backoff_start_s=0)
    versuche = {"n": 0}

    def _immer_400(url, daten):
        versuche["n"] += 1
        raise ikw.ISWFehler(400, "Invalid query parameters")

    monkeypatch.setattr(karte, "_einmal", _immer_400)
    try:
        karte._json("egal")
    except ikw.ISWFehler:
        pass
    assert versuche["n"] == 1


def test_transportfehler_wird_wiederholbarer_iswfehler(monkeypatch):
    """Regression: ein httpx.ReadTimeout riss den Rekorder ab."""
    import httpx

    karte = ikw.ISWKarte(max_versuche=3, backoff_start_s=0)
    versuche = {"n": 0}

    class _Sess:
        def get(self, url):
            versuche["n"] += 1
            if versuche["n"] < 3:
                raise httpx.ReadTimeout("The read operation timed out")
            return _Antwort()

    class _Antwort:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True}

    monkeypatch.setattr(karte, "_sess", lambda: _Sess())
    assert karte._json("egal") == {"ok": True}
    assert versuche["n"] == 3


def test_nicht_json_200_antwort_geht_in_den_backoff(monkeypatch):
    """Review-Befund 24.07.: eine 200-Antwort ohne JSON (Cloudflare-
    Fehlerseite) umging den Backoff und brach den Durchlauf ab."""
    karte = ikw.ISWKarte(max_versuche=3, backoff_start_s=0)
    versuche = {"n": 0}

    class _Kaputt:
        status_code = 200

        @staticmethod
        def json():
            raise ValueError("kein JSON")

    class _Heil:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True}

    class _Sess:
        def get(self, url):
            versuche["n"] += 1
            return _Kaputt() if versuche["n"] < 3 else _Heil()

    monkeypatch.setattr(karte, "_sess", lambda: _Sess())
    assert karte._json("egal") == {"ok": True}
    assert versuche["n"] == 3


def test_transport_status_ist_wiederholbar():
    assert ikw.TRANSPORT_STATUS in ikw.WIEDERHOLBAR
    assert 429 in ikw.WIEDERHOLBAR
    assert 400 not in ikw.WIEDERHOLBAR
    assert 403 not in ikw.WIEDERHOLBAR, "Sperre ist Sache des Rekorders"


def test_403_umgeht_den_backoff_ohne_zu_warten(monkeypatch):
    """Vorfall 01.09.: 403 ist eine Abweisung, kein transienter Fehler.
    Der Client wirft sofort (ein Versuch, kein 10-s-Schlaf); die
    Abkuehlpause gehoert dem Rekorder (isw_rekorder.Sperre), sonst
    haemmerte der Backoff weiter in die Sperre hinein."""
    karte = ikw.ISWKarte(max_versuche=5, backoff_start_s=10)
    versuche = {"n": 0}
    schlaefe: list[float] = []
    monkeypatch.setattr(ikw.time, "sleep", schlaefe.append)

    def _immer_403(url, daten):
        versuche["n"] += 1
        raise ikw.ISWFehler(403, "Forbidden")

    monkeypatch.setattr(karte, "_einmal", _immer_403)
    try:
        karte._json("egal")
    except ikw.ISWFehler as fehler:
        assert fehler.status == 403
    else:
        raise AssertionError("haette ISWFehler werfen muessen")
    assert versuche["n"] == 1
    assert schlaefe == []


def test_429_backoff_verdoppelt_die_wartezeit(monkeypatch):
    """Drosselung bleibt beim Client: 10 s, 20 s, 40 s zwischen vier
    Versuchen, dann Aufgabe mit dem letzten Status."""
    karte = ikw.ISWKarte(max_versuche=4, backoff_start_s=10)
    versuche = {"n": 0}
    schlaefe: list[float] = []
    monkeypatch.setattr(ikw.time, "sleep", schlaefe.append)

    def _immer_429(url, daten):
        versuche["n"] += 1
        raise ikw.ISWFehler(429, "Too many requests")

    monkeypatch.setattr(karte, "_einmal", _immer_429)
    try:
        karte._json("egal")
    except ikw.ISWFehler as fehler:
        assert fehler.status == 429
    else:
        raise AssertionError("haette ISWFehler werfen muessen")
    assert versuche["n"] == 4
    assert schlaefe == [10, 20, 40]


def test_layer_stand_umgeht_den_cdn_cache(monkeypatch):
    """Messung 27.08.: Der CDN cached die Layer-Metadaten 300 s (TCP_HIT).

    Ohne Cache-Buster liest ein 1-s-Poll fuenf Minuten lang denselben
    Stand — der Parameter muss also in JEDER Metadaten-URL stehen.
    """
    karte = ikw.ISWKarte()
    urls = []

    def _fake_json(url, daten=None):
        urls.append(url)
        return {"editingInfo": {"lastEditDate": 1787843556016}}

    monkeypatch.setattr(karte, "_json", _fake_json)
    stand = karte.layer_stand(ikw.QUALIFIZIERENDE_LAYER[0])
    assert stand == 1787843556016
    assert len(urls) == 1
    assert "f=json" in urls[0]
    assert "_cb=" in urls[0], "Cache-Buster fehlt — Poll liest nur den CDN"


def test_layer_stand_cache_buster_ist_je_abruf_eindeutig(monkeypatch):
    karte = ikw.ISWKarte()
    urls = []

    def _fake_json(url, daten=None):
        urls.append(url)
        return {"editingInfo": {"lastEditDate": 1}}

    zeiten = iter([1000.0, 1000.5])
    monkeypatch.setattr(ikw.time, "time", lambda: next(zeiten))
    monkeypatch.setattr(karte, "_json", _fake_json)
    karte.layer_stand(ikw.QUALIFIZIERENDE_LAYER[0])
    karte.layer_stand(ikw.QUALIFIZIERENDE_LAYER[0])
    assert urls[0] != urls[1], "gleicher Cache-Buster = gecachte Antwort"
