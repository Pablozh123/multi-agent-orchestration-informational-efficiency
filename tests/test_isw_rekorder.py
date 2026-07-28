"""Tests fuer den ISW-Rekorder: Kandidaten, Beruhigungsfenster, Zustand.

Kein Netzzugriff — Karte und Polymarket sind durch Attrappen ersetzt.
"""
from __future__ import annotations

import json

from operations.pipeline import isw_rekorder as rek
from operations.pipeline.isw_karten_watch import ISWFehler, ISWFlaeche, Siedlung

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


def _zustand(**overrides):
    zustand = rek._leerer_zustand()
    zustand.update(overrides)
    return zustand


class _KarteAttrappe:
    """Feste Layer-Staende und Flaechen, ohne Netz."""

    def __init__(self, staende, flaechen, fehler_flaechen=(), siedlung=None):
        self._staende = staende
        self._flaechen = flaechen
        self._fehler = set(fehler_flaechen)
        self._siedlung = siedlung
        self.siedlungs_abfragen = 0

    def layer_stand(self, layer):
        return self._staende.get(layer.name)

    def flaechen(self, layer, where="1=1", mit_geometrie=True):
        if layer.name in self._fehler:
            raise ISWFehler(429, "Too many requests")
        return self._flaechen.get(layer.name, [])

    def siedlung_an_punkt(self, lat, lon):
        self.siedlungs_abfragen += 1
        return self._siedlung


class _LeserAttrappe:
    def __init__(self, preis=0.046):
        self._preis = preis
        self.preis_aufrufe = 0
        self.buch_aufrufe = 0

    def preis_yes(self, token_id):
        self.preis_aufrufe += 1
        return self._preis

    def buch_tiefe(self, token_id):
        self.buch_aufrufe += 1
        return {"best_bid": 0.03, "best_ask": 0.05,
                "usd_bis_030": 150.0, "usd_bis_050": 400.0}


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


# ---------------------------------------------------------------- Deckung

def test_deckung_findet_ueberdeckung():
    flaeche = ISWFlaeche("infiltration", 2104, QUADRAT, creation_ms=1000)
    d = rek.deckung([flaeche], [_ziel()])
    assert d["will-russia-enter-testort-by-july-31"].objectid == 2104


def test_deckung_ignoriert_entfernte_flaeche():
    assert rek.deckung([ISWFlaeche("infiltration", 1, FERN, creation_ms=1)],
                       [_ziel()]) == {}


def test_deckung_nimmt_die_juengste_schneidende_flaeche():
    """Review-Befund: die erste Flaeche in Server-Reihenfolge kann ein
    Alt-Polygon mit Randberuehrung sein — der Zeitstempel muss von der
    juengsten Aenderung stammen."""
    alt = ISWFlaeche("infiltration", 1, QUADRAT, creation_ms=1000)
    neu = ISWFlaeche("infiltration", 2, QUADRAT,
                     creation_ms=1000, edit_ms=99_000)
    d = rek.deckung([alt, neu], [_ziel()])
    assert d["will-russia-enter-testort-by-july-31"].objectid == 2


# ------------------------------------------------------------- Durchlauf

def test_durchlauf_grundiert_beim_ersten_lauf_ohne_kandidaten(tmp_path):
    karte = _KarteAttrappe(
        {"infiltration": 111},
        {"infiltration": [ISWFlaeche("infiltration", 1, QUADRAT,
                                     creation_ms=1000)]},
    )
    zustand = _zustand()
    meldungen = rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                              tmp_path / "p.jsonl")
    assert meldungen == []
    assert zustand["kandidaten"] == []
    assert zustand["beobachtet"]["will-russia-enter-testort-by-july-31"] == ["infiltration"]
    # Grundierungs-Deckung gilt als laengst eingepreist -> qualifiziert
    assert zustand["qualifiziert"]["will-russia-enter-testort-by-july-31"] == ["infiltration"]
    arten = [json.loads(z)["art"] for z in
             (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert arten == ["grundierung"]


def test_durchlauf_erzeugt_kandidat_mit_t0_messung(tmp_path):
    ziel = _ziel()
    zustand = _zustand(layer_stand={"infiltration": 111})
    flaeche = ISWFlaeche("infiltration", 2104, QUADRAT,
                         creation_ms=1_784_752_740_759,
                         edit_ms=1_784_754_173_609)
    karte = _KarteAttrappe({"infiltration": 222}, {"infiltration": [flaeche]})
    leser = _LeserAttrappe(0.046)
    meldungen = rek.durchlauf(karte, leser, [ziel], zustand,
                              tmp_path / "p.jsonl")
    assert len(meldungen) == 1
    eintrag = meldungen[0]
    assert eintrag["art"] == "kandidat_treffer"
    assert eintrag["preis_yes"] == 0.046
    assert eintrag["buch"]["usd_bis_030"] == 150.0
    # Vorlauf rechnet gegen die JUENGSTE Aenderung (Edit), nicht die Anlage
    assert eintrag["feature_zeit_utc"] == "2026-07-22T21:02:53Z"
    assert len(zustand["kandidaten"]) == 1
    assert [a["minute"] for a in zustand["offene_nachfassungen"]] == [1, 5, 30]
    assert all("erste_sichtung_ts" in a
               for a in zustand["offene_nachfassungen"])


def test_durchlauf_ohne_layer_aenderung_macht_nichts(tmp_path):
    karte = _KarteAttrappe({"infiltration": 111}, {})
    zustand = _zustand(layer_stand={"infiltration": 111})
    assert rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                         tmp_path / "p.jsonl") == []


def test_layer_stand_wird_bei_flaechen_fehler_nicht_fortgeschrieben(tmp_path):
    """Review-Befund: Stand-Commit vor der Auswertung verliert das Ereignis
    endgueltig, wenn der Flaechenabruf scheitert."""
    karte = _KarteAttrappe({"infiltration": 222}, {},
                           fehler_flaechen=("infiltration",))
    zustand = _zustand(layer_stand={"infiltration": 111})
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["layer_stand"]["infiltration"] == 111
    arten = [json.loads(z)["art"] for z in
             (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert arten == ["fehler"]


def test_stand_none_ueberschreibt_bekannten_stand_nicht(tmp_path):
    """Review-Befund: None als Stand schaltete den Folgelauf auf stille
    Grundierung und verschluckte das naechste echte Ereignis."""
    karte = _KarteAttrappe({"infiltration": None}, {})
    zustand = _zustand(layer_stand={"infiltration": 111})
    rek.durchlauf(karte, _LeserAttrappe(), [_ziel()], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["layer_stand"]["infiltration"] == 111


def test_verlust_erzeugt_kandidat(tmp_path):
    ziel = _ziel()
    zustand = _zustand(layer_stand={"infiltration": 111},
                       beobachtet={ziel.slug: ["infiltration"]})
    karte = _KarteAttrappe(
        {"infiltration": 222},
        {"infiltration": [ISWFlaeche("infiltration", 1, FERN,
                                     creation_ms=1000)]},
    )
    rek.durchlauf(karte, _LeserAttrappe(0.91), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["beobachtet"][ziel.slug] == []
    assert len(zustand["kandidaten"]) == 1
    assert zustand["kandidaten"][0]["art"] == "verlust"
    zeilen = [json.loads(z) for z in
              (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert zeilen[0]["art"] == "kandidat_verlust"
    assert zeilen[0]["preis_yes"] == 0.91


# ------------------------------------------------------------------- Flaps

def test_flap_treffer_dann_verlust_hebt_sich_auf(tmp_path):
    """Loesch-Phase eines Rebuilds: der frische Treffer-Kandidat wird
    verworfen statt einen Verlust-Kandidaten zu erzeugen."""
    ziel = _ziel()
    zustand = _zustand(
        layer_stand={"infiltration": 222},
        beobachtet={ziel.slug: ["infiltration"]},
        kandidaten=[{"art": "treffer", "slug": ziel.slug,
                     "layer": "infiltration", "siedlung": "Testort",
                     "token": "token-1", "auswertbar": True,
                     "erste_sichtung_ts": 1_784_800_000.0,
                     "erste_sichtung_utc": "2026-07-23T00:00:00Z"}],
    )
    karte = _KarteAttrappe({"infiltration": 333}, {"infiltration": []})
    rek.durchlauf(karte, _LeserAttrappe(), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["kandidaten"] == []
    arten = [json.loads(z)["art"] for z in
             (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert arten == ["treffer_verworfen"]


def test_flap_verlust_dann_rueckkehr_hebt_sich_auf(tmp_path):
    """Neuzeichnen-Phase: die Deckung kehrt zurueck, der Verlust-Kandidat
    wird verworfen, KEIN neuer Treffer-Kandidat (Deckung war durchgehend)."""
    ziel = _ziel()
    zustand = _zustand(
        layer_stand={"infiltration": 222},
        beobachtet={ziel.slug: []},
        kandidaten=[{"art": "verlust", "slug": ziel.slug,
                     "layer": "infiltration", "siedlung": "Testort",
                     "token": "token-1", "auswertbar": True,
                     "erste_sichtung_ts": 1_784_800_000.0,
                     "erste_sichtung_utc": "2026-07-23T00:00:00Z"}],
    )
    karte = _KarteAttrappe(
        {"infiltration": 333},
        {"infiltration": [ISWFlaeche("infiltration", 9, QUADRAT,
                                     creation_ms=2000)]},
    )
    rek.durchlauf(karte, _LeserAttrappe(), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["kandidaten"] == []
    assert zustand["beobachtet"][ziel.slug] == ["infiltration"]
    arten = [json.loads(z)["art"] for z in
             (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert arten == ["verlust_verworfen"]


# ------------------------------------------------------- Beruhigungsfenster

def _alter_kandidat(slug, art="treffer"):
    return {"art": art, "slug": slug, "layer": "infiltration",
            "siedlung": "Testort", "token": "token-1", "auswertbar": True,
            "erste_sichtung_ts": 1_000.0,
            "erste_sichtung_utc": "2026-07-01T00:00:00Z"}


def test_treffer_wird_nach_fenster_bestaetigt(tmp_path):
    ziel = _ziel()
    zustand = _zustand(layer_stand={"infiltration": 111},
                       beobachtet={ziel.slug: ["infiltration"]},
                       kandidaten=[_alter_kandidat(ziel.slug)])
    karte = _KarteAttrappe({"infiltration": 111}, {})
    rek.durchlauf(karte, _LeserAttrappe(0.93), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["kandidaten"] == []
    assert zustand["qualifiziert"][ziel.slug] == ["infiltration"]
    zeilen = [json.loads(z) for z in
              (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert zeilen[0]["art"] == "treffer_bestaetigt"
    assert zeilen[0]["preis_yes_jetzt"] == 0.93


def test_treffer_ohne_bestand_wird_verworfen(tmp_path):
    ziel = _ziel()
    zustand = _zustand(layer_stand={"infiltration": 111},
                       beobachtet={ziel.slug: []},
                       kandidaten=[_alter_kandidat(ziel.slug)])
    karte = _KarteAttrappe({"infiltration": 111}, {})
    rek.durchlauf(karte, _LeserAttrappe(), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert zustand["kandidaten"] == []
    assert ziel.slug not in zustand["qualifiziert"]
    arten = [json.loads(z)["art"] for z in
             (tmp_path / "p.jsonl").read_text(encoding="utf-8").splitlines()]
    assert arten == ["treffer_verworfen"]


def test_junger_kandidat_bleibt_offen(tmp_path):
    import time as _time
    ziel = _ziel()
    kandidat = _alter_kandidat(ziel.slug)
    kandidat["erste_sichtung_ts"] = _time.time()
    zustand = _zustand(layer_stand={"infiltration": 111},
                       beobachtet={ziel.slug: ["infiltration"]},
                       kandidaten=[kandidat])
    karte = _KarteAttrappe({"infiltration": 111}, {})
    rek.durchlauf(karte, _LeserAttrappe(), [ziel], zustand,
                  tmp_path / "p.jsonl")
    assert len(zustand["kandidaten"]) == 1


# ---------------------------------------------------------------- Budget

def test_preisbudget_deckelt_http_aufrufe_je_zyklus(tmp_path):
    """Ein Massenuebergang darf nicht Dutzende CLOB-Aufrufe ausloesen."""
    ziele = [_ziel(f"will-russia-enter-ort{i}-by-july-31") for i in range(20)]
    flaeche = ISWFlaeche("infiltration", 1, QUADRAT, creation_ms=1000)
    karte = _KarteAttrappe({"infiltration": 222}, {"infiltration": [flaeche]})
    zustand = _zustand(layer_stand={"infiltration": 111})
    leser = _LeserAttrappe()
    meldungen = rek.durchlauf(karte, leser, ziele, zustand,
                              tmp_path / "p.jsonl")
    assert len(meldungen) == 20
    assert leser.preis_aufrufe + leser.buch_aufrufe <= rek.PREISABRUFE_JE_ZYKLUS
    assert any(m["preis_uebersprungen"] for m in meldungen)


# ---------------------------------------------------------------- Zustand

def test_zustand_rundlauf(tmp_path):
    pfad = tmp_path / "zustand.json"
    zustand = _zustand(layer_stand={"infiltration": 123})
    rek._schreibe_zustand(pfad, zustand)
    assert rek._lade_zustand(pfad) == zustand


def test_zustand_altes_schema_wird_verworfen(tmp_path):
    """Schema-Wechsel erzwingt Neu-Grundierung (Multipart-Fix aendert die
    Deckung; ein v1-Zustand waere inkonsistent)."""
    pfad = tmp_path / "zustand.json"
    pfad.write_text(json.dumps({"layer_stand": {"infiltration": 1},
                                "gedeckt": {"a": ["infiltration"]}}),
                    encoding="utf-8")
    assert rek._lade_zustand(pfad) == rek._leerer_zustand()


def test_zustand_kaputte_datei_gibt_leeren_zustand(tmp_path):
    pfad = tmp_path / "kaputt.json"
    pfad.write_text("{nicht json", encoding="utf-8")
    assert rek._lade_zustand(pfad) == rek._leerer_zustand()


def test_protokoll_haengt_zeilen_an(tmp_path):
    pfad = tmp_path / "ereignisse.jsonl"
    rek._protokolliere(pfad, {"art": "treffer", "slug": "a"})
    rek._protokolliere(pfad, {"art": "treffer", "slug": "b"})
    zeilen = pfad.read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(z)["slug"] for z in zeilen] == ["a", "b"]


# ------------------------------------------------------------ Nachfassungen

def test_nachfassung_protokolliert_realen_abstand(tmp_path):
    """Review-Befund: die geplante Minute kann von der realen abweichen —
    die Auswertung braucht den echten Abstand."""
    zustand = _zustand(offene_nachfassungen=[{
        "slug": "s", "token": "t", "layer": "infiltration",
        "minute": 1, "erste_sichtung_ts": 1_000.0, "faellig_ts": 1_060.0,
    }])
    rek._faellige_nachfassungen(_LeserAttrappe(0.5), zustand,
                                tmp_path / "p.jsonl")
    assert zustand["offene_nachfassungen"] == []
    eintrag = json.loads(
        (tmp_path / "p.jsonl").read_text(encoding="utf-8").strip())
    assert eintrag["geplante_minute"] == 1
    assert eintrag["real_s"] is not None
    assert eintrag["real_s"] > 60  # laengst ueberfaellig -> real >> geplant


# --------------------------------------------------- Geometrie-Cache/Maerkte

class _LeserMitMaerkten(_LeserAttrappe):
    def __init__(self, slugs=("will-russia-enter-krasnoiarske-by-july-31",)):
        super().__init__()
        self._slugs = slugs

    def maerkte(self, tag=rek.UKRAINE_TAG):
        return [{
            "id": str(i),
            "slug": slug,
            "question": "?",
            "description": "... Ort, Donetsk Oblast, "
                           "(48.419117° N, 37.125165° E) ...",
            "clobTokenIds": json.dumps([f"tok-yes-{i}", f"tok-no-{i}"]),
            "closed": False,
            "acceptingOrders": True,
        } for i, slug in enumerate(self._slugs)]


def test_lade_marktziele_ordnet_ueber_koordinate_zu(tmp_path):
    karte = _KarteAttrappe({}, {}, siedlung=Siedlung(6216, "Krasnoyarske",
                                                     QUADRAT))
    cache = {}
    ziele = rek.lade_marktziele(_LeserMitMaerkten(), karte, cache,
                                tmp_path / "geo.json", pause_s=0)
    assert len(ziele) == 1
    assert ziele[0].siedlung_name == "Krasnoyarske"
    assert ziele[0].token_yes == "tok-yes-0"
    assert ziele[0].auswertbar is True
    assert (tmp_path / "geo.json").exists()


def test_geometrie_cache_verhindert_erneute_abfrage(tmp_path):
    karte = _KarteAttrappe({}, {}, siedlung=Siedlung(6216, "Krasnoyarske",
                                                     QUADRAT))
    cache = {}
    leser = _LeserMitMaerkten()
    rek.lade_marktziele(leser, karte, cache, tmp_path / "geo.json", pause_s=0)
    rek.lade_marktziele(leser, karte, cache, tmp_path / "geo.json", pause_s=0)
    assert karte.siedlungs_abfragen == 1


def test_geometrie_cache_merkt_sich_leere_ergebnisse(tmp_path):
    karte = _KarteAttrappe({}, {}, siedlung=None)
    cache = {}
    leser = _LeserMitMaerkten()
    assert rek.lade_marktziele(leser, karte, cache, tmp_path / "geo.json",
                               pause_s=0) == []
    rek.lade_marktziele(leser, karte, cache, tmp_path / "geo.json", pause_s=0)
    assert karte.siedlungs_abfragen == 1


def test_geometrie_cache_migriert_alte_watchlist(tmp_path):
    alt = tmp_path / "watchlist.json"
    alt.write_text(json.dumps([{
        "slug": "egal", "frage": "?", "lat": 48.419117, "lon": 37.125165,
        "token_yes": "t", "polaritaet": "russisch", "kriterium": "beruehrung",
        "siedlung_name": "Krasnoyarske", "siedlung_objectid": 6216,
        "ringe": QUADRAT,
    }]), encoding="utf-8")
    cache = rek.lade_geometrie_cache(tmp_path / "geo.json", alt_watchlist=alt)
    assert rek._cache_key(48.419117, 37.125165) in cache
    assert cache[rek._cache_key(48.419117, 37.125165)]["name"] == "Krasnoyarske"


def test_bereinigung_meldet_kandidaten_geschlossener_maerkte(tmp_path):
    zustand = _zustand(
        beobachtet={"toter-markt": ["infiltration"], "lebt": ["advance"]},
        kandidaten=[_alter_kandidat("toter-markt")],
        offene_nachfassungen=[{"slug": "toter-markt", "token": "t",
                               "layer": "infiltration", "minute": 5,
                               "erste_sichtung_ts": 1.0, "faellig_ts": 2.0}],
    )
    n = rek._bereinige_zustand(zustand, {"lebt"}, tmp_path / "p.jsonl")
    assert n == 1
    assert zustand["kandidaten"] == []
    assert "toter-markt" not in zustand["beobachtet"]
    assert zustand["offene_nachfassungen"] == []
    eintrag = json.loads(
        (tmp_path / "p.jsonl").read_text(encoding="utf-8").strip())
    assert eintrag["art"] == "treffer_markt_geschlossen"


# ------------------------------------------------------------- Live-Modus

def _live_attrappen(monkeypatch):
    monkeypatch.setattr(rek, "ISWKarte", lambda *a, **k: _KarteAttrappe({}, {}))
    monkeypatch.setattr(rek, "PolymarktLeser", lambda *a, **k: _LeserAttrappe())
    monkeypatch.setattr(rek, "lade_marktziele", lambda *a, **k: [_ziel()])
    monkeypatch.setattr(_KarteAttrappe, "schliessen", lambda self: None,
                        raising=False)
    monkeypatch.setattr(_LeserAttrappe, "schliessen", lambda self: None,
                        raising=False)


def test_live_modus_erfuellt_den_watchdog_vertrag(tmp_path, monkeypatch):
    """--live: Startwache, bot.pid, start-Event + Herzschlag, Pfade im
    Profilverzeichnis — exakt das, was watchdog.py erwartet."""
    import os as _os

    from operations.pipeline import startwache

    monkeypatch.setenv("BOT_PROFIL", "isw_test_vertrag")
    monkeypatch.setenv("THESIS_LIVE_ROOT", str(tmp_path))
    _live_attrappen(monkeypatch)
    try:
        code = rek.main(["--live", "--einmal"])
    finally:
        startwache.wache_freigeben()
    assert code == 0
    live = tmp_path / "isw_test_vertrag"
    assert (live / "bot.pid").read_text(encoding="utf-8") == str(_os.getpid())
    events = [json.loads(z) for z in
              (live / "bot_events.jsonl").read_text(
                  encoding="utf-8").splitlines()]
    assert events[0]["art"] == "start"
    assert any(e["art"] == "herzschlag" for e in events)
    assert all("wall_ts_utc" in e for e in events)
    # Pfade liegen im Profilverzeichnis, nicht im Standard-Pfad
    assert (live / "zustand.json").exists()


def test_live_modus_weicht_bei_belegter_wache_zurueck(tmp_path, monkeypatch):
    """Zweite Instanz desselben Profils beendet sich, ohne bot.pid oder
    Events anzufassen (Startwache-Semantik)."""
    from operations.pipeline.startwache import Startwache

    monkeypatch.setenv("BOT_PROFIL", "isw_test_belegt")
    monkeypatch.setenv("THESIS_LIVE_ROOT", str(tmp_path))
    _live_attrappen(monkeypatch)
    live = tmp_path / "isw_test_belegt"
    wache = Startwache(live)
    assert wache.nehmen() is True
    try:
        code = rek.main(["--live", "--einmal"])
    finally:
        wache.freigeben()
    assert code == 0
    assert not (live / "bot.pid").exists()
    assert not (live / "bot_events.jsonl").exists()


def test_herzschlag_ohne_live_dir_ist_stumm(tmp_path):
    rek._herzschlag(None, art="start")  # darf nichts werfen, nichts schreiben
    assert list(tmp_path.iterdir()) == []


# ------------------------------------------------------------------- main

def test_main_schleife_ueberlebt_unerwarteten_fehler(tmp_path, monkeypatch):
    """Regression: ein ReadTimeout beendete den Prozess nach dem 1. Durchlauf."""
    protokoll = tmp_path / "p.jsonl"
    zustand_pfad = tmp_path / "z.json"

    monkeypatch.setattr(rek, "ISWKarte", lambda *a, **k: _KarteAttrappe({}, {}))
    monkeypatch.setattr(rek, "PolymarktLeser", lambda *a, **k: _LeserAttrappe())
    monkeypatch.setattr(rek, "lade_marktziele", lambda *a, **k: [_ziel()])

    def _kracht(*args, **kwargs):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(rek, "durchlauf", _kracht)
    monkeypatch.setattr(_KarteAttrappe, "schliessen", lambda self: None,
                        raising=False)
    monkeypatch.setattr(_LeserAttrappe, "schliessen", lambda self: None,
                        raising=False)

    code = rek.main(["--einmal", "--zustand", str(zustand_pfad),
                     "--protokoll", str(protokoll),
                     "--geometrie-cache", str(tmp_path / "geo.json")])
    assert code == 0, "main haette den Fehler abfangen muessen"
    eintraege = [json.loads(z) for z in
                 protokoll.read_text(encoding="utf-8").strip().splitlines()]
    assert eintraege[0]["art"] == "lauf_fehler"
    assert eintraege[0]["typ"] == "TimeoutError"
    assert zustand_pfad.exists()
