"""Earnings-Doppeltag 28.07.: Profile PayPal (745733) und Boeing (745748).

Offline gegen die echten market_ids/Fragen beider Events (Gamma,
27.07.). Belegt: Zeiten (12:00/14:30 UTC, IR-verifiziert), Anyone-Gate
aktiv (kein Sprecher-Klauselmuster), Schwellen aus dem Fragetext, die
Oder-/Varianten-Faelle des PayPal-Events (Stable Coin, Cash Back,
AI/A.I.) und die Phrasen-Ableitung "Philippine Airlines" bei Boeing.
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter


def _anyone_beschreibung(firma: str) -> str:
    return (
        f"This market will resolve based on the next earnings announcement "
        f"of {firma}.\n\nThis market will resolve to \"Yes\" if the listed "
        "term is mentioned by anyone during this event. Otherwise, the "
        'market will resolve to "No".\n\n'
        "The resolution source will be audio of the event."
    )


def _markt(mid: str, frage: str, firma: str) -> dict:
    return {
        "id": mid,
        "slug": f"will-say-{mid}",
        "question": frage,
        "description": _anyone_beschreibung(firma),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
        "outcomePrices": json.dumps(["0.5", "0.5"]),
        "closed": False,
        "groupItemThreshold": 0,
    }


PYPL_MARKETS = [
    _markt("3094212",
           'Will PayPal say "Quarter" 15+ times during earnings call?',
           "PayPal"),
    _markt("3094214",
           'Will PayPal say "Transaction" 5+ times during earnings call?',
           "PayPal"),
    _markt("3094216",
           'Will PayPal say "Stablecoin" or "Stable Coin" during earnings call?',
           "PayPal"),
    _markt("3094217",
           'Will PayPal say "AI" or "Artificial Intelligence" during earnings '
           "call?", "PayPal"),
    _markt("3094223",
           'Will PayPal say "Cash Back" or "Cashback" during earnings call?',
           "PayPal"),
    _markt("3094227",
           'Will PayPal say "Anthropic" or "Claude" during earnings call?',
           "PayPal"),
    _markt("3094230", "Will the earnings call not air?", "PayPal"),
]

BA_MARKETS = [
    _markt("3094246",
           'Will Boeing say "Quarter" 15+ times during earnings call?',
           "Boeing"),
    _markt("3094249",
           'Will Boeing say "Customer" 3+ times during earnings call?',
           "Boeing"),
    _markt("3094250",
           'Will Boeing say "Guidance" during earnings call?', "Boeing"),
    _markt("3094257",
           'Will Boeing say "Philippine Airlines" during earnings call?',
           "Boeing"),
    _markt("3094265", "Will the earnings call not air?", "Boeing"),
]


def _profil_fixture(name: str):
    @pytest.fixture
    def fix(monkeypatch):
        monkeypatch.setenv("BOT_PROFIL", name)
        importlib.reload(config)
        yield
        monkeypatch.delenv("BOT_PROFIL", raising=False)
        importlib.reload(config)

    return fix


pypl = _profil_fixture("earnings_pypl_july28")
ba = _profil_fixture("earnings_ba_july28")


def _snapshot(tmp_path, monkeypatch, event_id, maerkte):
    pfad = tmp_path / "gamma_event_snapshot.json"
    pfad.write_text(json.dumps({"event_id": event_id, "markets": maerkte}),
                    encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    from operations.pipeline.earnings_bot import baue_earnings_rules

    return {r.market_id: r for r in baue_earnings_rules()}


# ------------------------------------------------ Grunddaten


def test_pypl_grunddaten(pypl) -> None:
    p = config.PROFILE["earnings_pypl_july28"]
    assert p["event_id"] == "745733"
    assert p["discovery_slug_filter"] in p["event_slug"]
    # 08:00 ET = 12:00 UTC (EDT) — IR-Eventseite 27.07.
    assert config.CALL_START_UTC == "2026-07-28T12:00:00Z"
    assert config.CALL_MAX_MINUTEN == 90.0
    # Anyone-Event: KEIN Sprecher-Klauselmuster, keine Selbstheilung
    # (statischer IR-Webcast), keine ECAPA-Referenz.
    assert config.SPRECHER_KLAUSEL_MUSTER is None
    assert config.RECONNECT_KANAELE == []
    assert config.ZIELSPRECHER_REFERENZEN == []
    assert config.NO_ASK_OBERGRENZE == 0.0
    assert config.TRIGGER_VERIFY_AKTIV is True
    # Volles Budget (User 28.07. frueh): Vollprofil-Sweep, budget-
    # statt clip-limitiert.
    assert config.MAX_USD_GESAMT == pytest.approx(650.0)
    assert (config.MAX_USD_PRO_MARKT, config.MAX_CLIPS_PRO_MARKT) == (50.0, 40)


def test_ba_grunddaten(ba) -> None:
    p = config.PROFILE["earnings_ba_july28"]
    assert p["event_id"] == "745748"
    assert p["discovery_slug_filter"] in p["event_slug"]
    # 10:30 ET = 14:30 UTC (EDT) — Boeing-PM 01.07.
    assert config.CALL_START_UTC == "2026-07-28T14:30:00Z"
    assert config.CALL_MAX_MINUTEN == 120.0
    assert config.SPRECHER_KLAUSEL_MUSTER is None
    assert config.TRIGGER_VERIFY_AKTIV is True
    # Erster large-v3-Hauptlauf (User 28.07.); Verify-Modell identisch
    # -> geteilte Instanz im Bot.
    assert config.TRANSCRIBER_MODELL == "large-v3"
    assert config.TRIGGER_VERIFY_MODELL == "large-v3"


def test_transcriber_modell_default_bleibt_small() -> None:
    importlib.reload(config)
    assert config.TRANSCRIBER_MODELL == "small"
    assert config.PROFILE["earnings_pypl_july28"].get(
        "transcriber_modell") is None
    assert config.PROFILE["earnings_pg_july29"].get(
        "transcriber_modell") is None


def test_filter_und_live_dirs_disjunkt() -> None:
    importlib.reload(config)
    for name in ("earnings_pypl_july28", "earnings_ba_july28"):
        p = config.PROFILE[name]
        for anderer, q in config.PROFILE.items():
            if anderer == name:
                continue
            assert p["discovery_slug_filter"] not in q["event_slug"], (
                name, anderer)
            assert q["discovery_slug_filter"] not in p["event_slug"], (
                name, anderer)
            assert p["live_dir"] != q["live_dir"]


# ------------------------------------------------ PayPal-Regeln


def test_pypl_schwellen_und_anyone_gate(pypl, tmp_path, monkeypatch) -> None:
    rules = _snapshot(tmp_path, monkeypatch, "745733", PYPL_MARKETS)
    assert rules["3094212"].schwelle == 15
    assert rules["3094214"].schwelle == 5
    assert rules["3094216"].status == "active"  # Anyone-Klausel traegt
    assert rules["3094230"].status == "skip"
    assert rules["3094230"].skip_grund == "negationsmarkt_ohne_wortzaehlung"


def test_pypl_stablecoin_und_cashback_varianten(pypl, tmp_path,
                                                monkeypatch) -> None:
    rules = _snapshot(tmp_path, monkeypatch, "745733", PYPL_MARKETS)
    assert rules["3094216"].varianten == [
        "Stablecoin", "Stable Coin", "Stable-Coin"]
    z = StreamingCounter(rules["3094216"])
    z.ingest_chunk(1, [Segment(
        text="Our stablecoin, the stable coin PYUSD, a stable-coin play.",
        confidence=0.95)], "t")
    assert z.count == 3
    z2 = StreamingCounter(rules["3094223"])
    z2.ingest_chunk(1, [Segment(
        text="cash back rewards, cashback growth, cash-back offers",
        confidence=0.95)], "t")
    assert z2.count == 3


def test_pypl_ai_akronym_map(pypl, tmp_path, monkeypatch) -> None:
    # VARIANTEN_MAP: "ai" -> AI/A.I. (ASR-Schreibvariante); die
    # Langform kommt als eigener zitierter Begriff dazu.
    rules = _snapshot(tmp_path, monkeypatch, "745733", PYPL_MARKETS)
    z = StreamingCounter(rules["3094217"])
    z.ingest_chunk(1, [Segment(
        text="A.I. is core, artificial intelligence everywhere, AI wins.",
        confidence=0.95)], "t")
    assert z.count == 3


def test_pypl_anthropic_claude(pypl, tmp_path, monkeypatch) -> None:
    rules = _snapshot(tmp_path, monkeypatch, "745733", PYPL_MARKETS)
    z = StreamingCounter(rules["3094227"])
    z.ingest_chunk(1, [Segment(text="We partner with Anthropic on Claude.",
                               confidence=0.95)], "t")
    assert z.count == 2


# ------------------------------------------------ Boeing-Regeln


def test_ba_schwellen_und_phrase(ba, tmp_path, monkeypatch) -> None:
    rules = _snapshot(tmp_path, monkeypatch, "745748", BA_MARKETS)
    assert rules["3094246"].schwelle == 15
    assert rules["3094249"].schwelle == 3
    assert rules["3094250"].schwelle == 1
    assert rules["3094265"].status == "skip"
    # Phrase nativ (flexible Leerzeichen im Pattern).
    z = StreamingCounter(rules["3094257"])
    z.ingest_chunk(1, [Segment(
        text="the Philippine Airlines order was historic",
        confidence=0.95)], "t")
    assert z.count == 1
