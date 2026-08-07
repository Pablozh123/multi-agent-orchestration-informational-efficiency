"""Trump-Graham-Tribute: zweites sprechergebundenes Event — 28.07.2026.

Profil `trump_graham_july28` (Event 745731, Trauerfeier Washington
National Cathedral). Offline gegen die echten market_ids/Fragen; belegt
die Michigan-Lehren: Referenz-Union (PA + Studio), Reconnect-Kanaele
mit Funeral-Titel-Gate, Budget-Vorgabe, und dass die Regel-Ableitung
die Phrasen-/Oder-Maerkte des Events nativ traegt.
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter

PROFIL = "trump_graham_july28"


def _beschreibung() -> str:
    return (
        "Trump is scheduled to deliver a tribute to Lindsey Graham in "
        "the Washington National Cathedral on July 28, 2026 at 2 PM ET.\n\n"
        'This market will resolve to "Yes" if Trump says the listed term '
        "during the tribute scheduled for July 28, 2026. Otherwise, the "
        'market will resolve to "No".\n\n'
        "The resolution source will be audio/video of the event."
    )


def _markt(mid: str, frage: str) -> dict:
    return {
        "id": mid,
        "slug": f"will-trump-say-{mid}",
        "question": frage,
        "description": _beschreibung(),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
        "outcomePrices": json.dumps(["0.5", "0.5"]),
        "closed": False,
        "groupItemThreshold": 0,
    }


# Echte market_ids/Fragen (Gamma, 27.07.2026 abends, Auszug).
EVENT_MARKETS = [
    _markt("3094168",
           'Will Trump say "Hell" 2+ times during tribute to Lindsey Graham?'),
    _markt("3094170",
           'Will Trump say "Save America Act" during tribute to Lindsey Graham?'),
    _markt("3094172",
           'Will Trump say "Tough Cookie" during tribute to Lindsey Graham?'),
    _markt("3094176",
           'Will Trump say "Supreme Court" during tribute to Lindsey Graham?'),
    _markt("3094179",
           'Will Trump say "Golf" or "Golfer" during tribute to Lindsey Graham?'),
    _markt("3094185",
           'Will Trump say "Air Force" or "Space Force" during tribute to '
           "Lindsey Graham?"),
    _markt("3094187", "Will Trump’s remarks not air?"),
]


@pytest.fixture
def profil(monkeypatch):
    monkeypatch.setenv("BOT_PROFIL", PROFIL)
    importlib.reload(config)
    yield
    monkeypatch.delenv("BOT_PROFIL", raising=False)
    importlib.reload(config)


@pytest.fixture
def snapshot(profil, tmp_path, monkeypatch):
    pfad = tmp_path / "gamma_event_snapshot.json"
    pfad.write_text(json.dumps(
        {"event_id": "745731", "slug": config.PROFILE[PROFIL]["event_slug"],
         "markets": EVENT_MARKETS}), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    return pfad


def _rules(snapshot):
    from operations.pipeline.earnings_bot import baue_earnings_rules

    return {r.market_id: r for r in baue_earnings_rules()}


def test_profil_grunddaten(profil) -> None:
    p = config.PROFILE[PROFIL]
    assert p["event_id"] == "745731"
    assert p["discovery_slug_filter"] in p["event_slug"]
    assert p["live_dir"] == PROFIL
    andere = [q["live_dir"] for name, q in config.PROFILE.items()
              if name != PROFIL]
    assert p["live_dir"] not in andere
    # 28.07.2026 14:00 ET = 18:00 UTC (EDT); langes Fenster, Trumps
    # Slot liegt irgendwo in der Zeremonie.
    assert config.CALL_START_UTC == "2026-07-28T18:00:00Z"
    assert config.CALL_MAX_MINUTEN == 240.0
    assert config.NO_ASK_OBERGRENZE == 0.0
    assert config.TRIGGER_VERIFY_AKTIV is True
    assert config.ASK_OBERGRENZE == 0.90


def test_discovery_filter_disjunkt_zu_anderen_profilen(profil) -> None:
    for name, q in config.PROFILE.items():
        if name == PROFIL:
            continue
        assert config.PROFILE[PROFIL]["discovery_slug_filter"] not in q["event_slug"]
        assert q["discovery_slug_filter"] not in config.PROFILE[PROFIL]["event_slug"]


def test_referenz_union_und_reconnect(profil) -> None:
    # Michigan-Lehre 1: Union aus PA- und Studio-Referenz, Schwelle 0.50.
    assert len(config.ZIELSPRECHER_REFERENZEN) == 2
    namen = [p.name for p in config.ZIELSPRECHER_REFERENZEN]
    assert "referenz_stimme_pa.npy" in namen
    assert "referenz_stimme_studio.npy" in namen
    assert config.SPRECHER_SCHWELLE == 0.50
    # Michigan-Lehre 2: Selbstheilung mit Funeral-Titel-Gate; die
    # Kathedrale (kommentarfrei) steht vorn.
    assert len(config.RECONNECT_KANAELE) == 4
    assert "WNCathedral" in config.RECONNECT_KANAELE[0]
    assert "graham" in config.STREAM_TITEL_MUSTER
    assert config.STREAM_STALL_S == 25.0


def test_budget_vorgabe(profil) -> None:
    assert config.MAX_USD_GESAMT == pytest.approx(650.0)
    assert config.MAX_USD_PRO_MARKT * config.MAX_CLIPS_PRO_MARKT == 100.0


def test_klausel_gate_und_schwellen(snapshot) -> None:
    rules = _rules(snapshot)
    assert rules["3094176"].status == "active"
    assert rules["3094168"].schwelle == 2
    assert rules["3094170"].schwelle == 1
    assert rules["3094187"].status == "skip"
    assert rules["3094187"].skip_grund == "negationsmarkt_ohne_wortzaehlung"


def test_golf_golfer_ohne_doppelzaehlung(snapshot) -> None:
    # "Golfer" darf nicht zusaetzlich das "Golf"-Pattern treffen
    # (strikte Wortgrenze blockt), sonst zaehlte ein Wort doppelt.
    rules = _rules(snapshot)
    assert rules["3094179"].varianten == ["Golf", "Golfer"]
    z = StreamingCounter(rules["3094179"])
    z.ingest_chunk(1, [Segment(text="He was a great golfer and loved golf.",
                               confidence=0.95)], "t")
    assert z.count == 2


def test_phrasen_nativ(snapshot) -> None:
    rules = _rules(snapshot)
    z = StreamingCounter(rules["3094170"])
    z.ingest_chunk(1, [Segment(text="we will pass the Save America Act now",
                               confidence=0.95)], "t")
    assert z.count == 1
    z2 = StreamingCounter(rules["3094185"])
    z2.ingest_chunk(1, [Segment(
        text="He fought for the Air Force and for the Space Force.",
        confidence=0.95)], "t")
    assert z2.count == 2
    z3 = StreamingCounter(rules["3094172"])
    z3.ingest_chunk(1, [Segment(text="Lindsey was one tough cookie.",
                                confidence=0.95)], "t")
    assert z3.count == 1
