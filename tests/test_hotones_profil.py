"""Armierung Hot Ones (Event 731776, Bernthal ODER Holland) — 22.07.2026.

Der Markt wertet nur Aussagen von Jon Bernthal oder Tom Holland, waehrend
Host Sean Evans den groesseren Redeanteil hat. Das Profil braucht deshalb
zwei Zielsprecher (Union), eine enge Event-Bindung (monatliche Serie),
YouTube-only-Quellen und die profil-lokalen Zaehler-Korrekturen aus dem
Markt-Audit (Spider-Doppelzaehlung, Bindestrich-Komposita, Homophone).

Die Tests laufen offline gegen synthetische Gamma-Maerkte mit den echten
market_ids und Fragen des Events — sie belegen die Regel-Ableitung, nicht
den Live-Abruf.
"""

from __future__ import annotations

import json

import pytest

from operations.pipeline import config
from operations.pipeline import market_rules as mr
from operations.pipeline.counter_engine import Segment, StreamingCounter


def _markt(mid: str, frage: str) -> dict:
    """Minimaler Gamma-Markt mit YES/NO-Token und der echten Frage."""
    return {
        "id": mid,
        "slug": f"m-{mid}",
        "question": frage,
        "description": (
            "This market will resolve to \"Yes\" if Jon Bernthal or Tom "
            "Holland say the listed term during their appearance on Hot Ones."
        ),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
    }


# Echte market_ids/Fragen des Events (Gamma, 22.07.2026).
HOTONES_MARKETS = [
    _markt("3026024", 'Will Jon Bernthal or Tom Holland say "Spider" or '
                      '"Spider-man" 5+ times on Hot Ones?'),
    _markt("3026043", 'Will Jon Bernthal or Tom Holland say "Ice Cream" on Hot Ones?'),
    _markt("3026035", 'Will Jon Bernthal or Tom Holland say "World Cup" on Hot Ones?'),
    _markt("3026039", 'Will Jon Bernthal or Tom Holland say "Pitbull" on Hot Ones?'),
    _markt("3026036", 'Will Jon Bernthal or Tom Holland say "Morocco" on Hot Ones?'),
    _markt("3026022", 'Will Jon Bernthal or Tom Holland say "Brother" or '
                      '"Mate" 10+ times on Hot Ones?'),
    _markt("3026034", 'Will Jon Bernthal or Tom Holland say "Soccer" on Hot Ones?'),
    _markt("3026033", 'Will Jon Bernthal or Tom Holland say "Wedding" on Hot Ones?'),
    _markt("3026042", 'Will Jon Bernthal or Tom Holland say "Fire" on Hot Ones?'),
]


@pytest.fixture
def profil(monkeypatch):
    """Aktiviert das hotones-Profil fuer config-abgeleitete Werte."""
    import importlib

    monkeypatch.setenv("BOT_PROFIL", "hotones_july23")
    importlib.reload(config)
    importlib.reload(mr)
    yield
    monkeypatch.delenv("BOT_PROFIL", raising=False)
    importlib.reload(config)
    importlib.reload(mr)


# ------------------------------------------------ Profil-Grundwerte


def test_profil_grunddaten(profil) -> None:
    p = config.PROFILE["hotones_july23"]
    assert p["event_id"] == "731776"
    assert p["yt_channel_id"] == "UCPD_bxCRGpmmeQcbe2kpPaA"
    # Kein Audio-Feed, kein Prober, kein Playlist-Gate.
    assert p["rss_feed_url"] is None
    assert p["mp3_probe_muster"] is None
    assert p["yt_playlist_id"] is None
    # Enge Event-Bindung wegen monatlichem Auto-Roll.
    assert p["discovery_slug_filter"] == "jon-bernthal-or-tom-holland"
    assert p["discovery_slug_filter"] in p["event_slug"]
    # Dauer-Gate unter dem gemessenen Minimum echter Folgen (1244s).
    assert p["yt_min_dauer_s"] == 1000


def test_zwei_zielsprecher_union_konfiguriert(profil) -> None:
    assert len(config.ZIELSPRECHER_REFERENZEN) == 2
    namen = [p.name for p in config.ZIELSPRECHER_REFERENZEN]
    assert namen == ["referenz_bernthal.npy", "referenz_holland.npy"]
    # Rueckwaertskompatibler Einzelpfad = erstes Element.
    assert config.ZIELSPRECHER_REFERENZ == config.ZIELSPRECHER_REFERENZEN[0]
    # Union erhoeht die Falsch-Positiv-Rate -> hoehere Schwelle als 0.40.
    assert config.SPRECHER_SCHWELLE == pytest.approx(0.50)


def test_no_seite_ausgeschaltet(profil) -> None:
    # NO entscheidet auf dem Gesamtzaehler (alle Stimmen) — untauglich auf
    # einem Host-dominierten Gast-Markt. no_ask_obergrenze 0.0 = nur YES.
    assert config.NO_ASK_OBERGRENZE == pytest.approx(0.0)


def test_budget_und_standard_sweep(profil) -> None:
    # Budget 400 (User-Vorgabe 23.07.) mit Standard-Sweep wie allin_july17.
    assert config.MAX_USD_GESAMT == pytest.approx(400.0)
    assert config.MAX_USD_PRO_MARKT == pytest.approx(50.0)
    assert config.MAX_CLIPS_PRO_MARKT == 40
    assert config.PROFILE["hotones_july23"]["max_usd_pro_markt"] == pytest.approx(
        config.PROFILE["allin_july17"]["max_usd_pro_markt"])


def test_titel_muster_trifft_hauptfolge_nicht_nebenformate(profil) -> None:
    import re

    muster = config.TITEL_MUSTER
    treffer = [
        "Jon Bernthal and Tom Holland ... While Eating Spicy Wings | Hot Ones",
        "... Bond Over Spicy Wings | Hot Ones",  # Duo ohne "While Eating"
        "Tom Holland Takes On the Wings of Death | Hot Ones",  # Name-Redundanz
    ]
    for t in treffer:
        assert re.search(muster, t, re.IGNORECASE), t
    # Nebenformate tragen "Hot Ones", aber nicht "Spicy Wings"/Namen:
    verboten = config.TITEL_VERBOTEN
    for t in ["5 Seconds of Summer | Hot Ones Versus",
              "Jacob Batalon Taste Tests Spicy Fried Chicken | Heat Eaters",
              "Jackass Plays Hot Ones Wing Pong"]:
        matcht_muster = bool(re.search(muster, t, re.IGNORECASE))
        matcht_verbot = bool(re.search(verboten, t, re.IGNORECASE))
        # Entweder gar kein Pflichtmuster ODER vom Verbotsmuster gefangen.
        assert (not matcht_muster) or matcht_verbot, t


def test_discovery_filter_disjunkt_zu_bestehenden_profilen(profil) -> None:
    hot = config.PROFILE["hotones_july23"]["discovery_slug_filter"]
    for name, p in config.PROFILE.items():
        if name == "hotones_july23":
            continue
        assert hot not in p["event_slug"], name


# ------------------------------------------------ Homophon je Profil


def test_homophon_set_ist_profil_lokal(profil) -> None:
    # Hot-Ones-eigene Fallen, NICHT das globale red/read/blue-Set.
    assert config.HOMOPHON_BEGRIFFE == {"mate", "soccer", "wedding", "brother"}
    rules = {r.market_id: r for r in mr.build_rules(HOTONES_MARKETS)}
    assert rules["3026034"].homophon_sensitiv is True   # Soccer
    assert rules["3026033"].homophon_sensitiv is True   # Wedding
    assert rules["3026022"].homophon_sensitiv is True   # Brother/Mate
    assert rules["3026042"].homophon_sensitiv is False  # Fire


def test_globales_homophon_default_bleibt_ausserhalb_unveraendert() -> None:
    # Ohne Hot-Ones-Profil (Default-Testprofil) gilt das globale Set.
    assert config.HOMOPHON_BEGRIFFE == {"red", "read", "blue", "blew",
                                        "right", "write"}


# ------------------------------------------------ Varianten-Override


def test_spider_doppelzaehlung_behoben(profil) -> None:
    rules = {r.market_id: r for r in mr.build_rules(HOTONES_MARKETS)}
    r = rules["3026024"]
    assert r.varianten == ["Spider", "Spiderman"]
    c = StreamingCounter(r)
    c.ingest_chunk(0, [Segment(
        "I loved playing Spider-Man in the Spider-Man movies", 0.9)], "t")
    assert c.count == 2  # zwei echte Nennungen, nicht vier
    # "Spider" allein deckt "Spider-Man" ab, "Spiderman" die Zusammenschreibung
    for txt, erwartet in [("Spider-Man", 1), ("Spiderman", 1),
                          ("Spider Man", 1), ("a spider crawled", 1)]:
        cc = StreamingCounter(r)
        cc.ingest_chunk(0, [Segment(txt, 0.9)], "t")
        assert cc.count == erwartet, txt


def test_bindestrich_und_zusammenschreibung_zaehlen(profil) -> None:
    rules = {r.market_id: r for r in mr.build_rules(HOTONES_MARKETS)}
    faelle = {
        "3026043": ["ice cream", "ice-cream", "Ice  Cream", "icecream"],
        "3026035": ["world cup", "world-cup", "worldcup"],
        "3026039": ["pitbull", "pit bull", "pit-bull"],
    }
    for mid, texte in faelle.items():
        r = rules[mid]
        for txt in texte:
            c = StreamingCounter(r)
            c.ingest_chunk(0, [Segment(txt, 0.9)], "t")
            assert c.count == 1, f"{mid}:{txt}"


def test_override_keine_falschtreffer_in_laengeren_woertern(profil) -> None:
    rules = {r.market_id: r for r in mr.build_rules(HOTONES_MARKETS)}
    r = rules["3026043"]  # Ice Cream
    c = StreamingCounter(r)
    c.ingest_chunk(0, [Segment("icecreamsandwich anyone", 0.9)], "t")
    assert c.count == 0


def test_ohne_override_bleibt_frage_ableitung(profil) -> None:
    rules = {r.market_id: r for r in mr.build_rules(HOTONES_MARKETS)}
    # Fire hat keinen Override -> Variante aus der Frage.
    assert rules["3026042"].varianten == ["Fire"]
