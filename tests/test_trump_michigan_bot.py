"""Trump-Michigan-Bot: sprechergebundenes Live-Event — 27.07.2026.

Profil `trump_michigan_july27` (Event 745732, Rede am GM Proving Ground
Milford). Die Tests laufen offline gegen synthetische Gamma-Maerkte mit
den echten market_ids und Fragen des Events. Sie belegen die drei
Besonderheiten gegenueber den Earnings-Profilen: (1) das Klausel-Gate
"if Trump says the listed term" ERSETZT das Anyone-Gate, (2) der
Operator-Marker sperrt den Kaufpfad (Vorprogramm/Vorredner), (3) die
ECAPA-Zurechnung traegt die YES-Entscheidung (ziel_count) — dazu die
ASR-Zaehlfallen "%" fuer "Percent" und "Drill, baby, drill".
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter

PROFIL = "trump_michigan_july27"


def _beschreibung(sprecher: bool = True) -> str:
    """Gekuerzte Original-Description des Events (eine je Event).

    sprecher=False simuliert eine Anyone-Description (Earnings-Template)
    im selben Snapshot — die darf bei diesem Profil NICHT aktiv werden.
    """
    kern = ("if Trump says the listed term during remarks in Michigan "
            "scheduled for July 27, 2026" if sprecher
            else "if the listed term is mentioned by anyone during this "
                 "event")
    return (
        "Trump is scheduled to deliver remarks in Michigan on July 27, "
        "2026.\n\n"
        f'This market will resolve to "Yes" {kern}. Otherwise, the '
        'market will resolve to "No".\n\n'
        "If this event is definitively cancelled, or otherwise is not "
        'aired by July 28, 2026, 11:59 PM ET, "-No Qualifying Event-" '
        'will resolve to "Yes" and all other brackets will resolve to '
        '"No".\n\n'
        "The resolution source will be audio/video of the event."
    )


def _markt(mid: str, frage: str, *, closed: bool = False,
           sprecher: bool = True) -> dict:
    return {
        "id": mid,
        "slug": f"will-trump-say-{mid}",
        "question": frage,
        "description": _beschreibung(sprecher),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
        "outcomePrices": json.dumps(["0.5", "0.5"]),
        "closed": closed,
        "groupItemThreshold": 0,
    }


# Echte market_ids/Fragen des Events (Gamma, 27.07.2026, Auszug).
EVENT_MARKETS = [
    _markt("3094188",
           'Will Trump say "Percent" 15+ times during Michigan remarks?'),
    _markt("3094189",
           'Will Trump say "Joe" or "Biden" 12+ times during Michigan remarks?'),
    _markt("3094190",
           'Will Trump say "Oil" or "Gas" 10+ times during Michigan remarks?'),
    _markt("3094191",
           'Will Trump say "Hell" 7+ times during Michigan remarks?'),
    _markt("3094192",
           'Will Trump say "Trump" 5+ times during Michigan remarks?'),
    _markt("3114660",
           'Will Trump say "Job" 20+ times during Michigan remarks?'),
    _markt("3094193", 'Will Trump say "Loan" during Michigan remarks?'),
    _markt("3094194", 'Will Trump say "Motor City" during Michigan remarks?'),
    _markt("3094204",
           'Will Trump say "Drill Baby Drill" during Michigan remarks?'),
    _markt("3114659",
           'Will Trump say "USMCA" or "NAFTA" during Michigan remarks?'),
    _markt("3094211", "Will Trump’s remarks not air?"),
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
        {"event_id": "745732", "slug": config.PROFILE[PROFIL]["event_slug"],
         "markets": EVENT_MARKETS}), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    return pfad


def _rules(snapshot):
    from operations.pipeline.earnings_bot import baue_earnings_rules

    return {r.market_id: r for r in baue_earnings_rules()}


# ------------------------------------------------ Profil-Grundwerte


def test_profil_grunddaten(profil) -> None:
    p = config.PROFILE[PROFIL]
    assert p["event_id"] == "745732"
    assert p["discovery_slug_filter"] in p["event_slug"]
    assert p["rss_feed_url"] is None
    assert p["yt_channel_id"] is None
    assert p["live_dir"] == PROFIL
    andere = [q["live_dir"] for name, q in config.PROFILE.items()
              if name != PROFIL]
    assert p["live_dir"] not in andere
    # 27.07.2026 15:00 ET = 19:00 UTC (Juli = EDT).
    assert config.CALL_START_UTC == "2026-07-27T19:00:00Z"
    # NO-Seite zu, Trigger-Verify an, kurze Chunks — wie Earnings.
    assert config.NO_ASK_OBERGRENZE == 0.0
    assert config.TRIGGER_VERIFY_AKTIV is True
    assert config.CHUNK_SEKUNDEN == 10
    assert config.ASK_OBERGRENZE == 0.90


def test_discovery_filter_disjunkt_zu_anderen_profilen(profil) -> None:
    # Insbesondere disjunkt zu den Truth-Social-Profilen
    # ("what-will-trump-post") und deren Filtern.
    for name, q in config.PROFILE.items():
        if name == PROFIL:
            continue
        assert config.PROFILE[PROFIL]["discovery_slug_filter"] not in q["event_slug"]
        assert q["discovery_slug_filter"] not in config.PROFILE[PROFIL]["event_slug"]


def test_sprecher_konstanten(profil) -> None:
    assert config.SPRECHER_KLAUSEL_MUSTER is not None
    assert config.SPRECHER_MARKER.name == "SPRECHER_AKTIV"
    assert config.SPRECHER_MARKER.parent == config.LIVE_DIR
    # ECAPA-Referenz konfiguriert, Schwelle 0.50 (Praezision vor Recall).
    assert config.ZIELSPRECHER_REFERENZ is not None
    assert config.SPRECHER_SCHWELLE == 0.50


def test_earnings_profile_bleiben_anyone_gebunden(monkeypatch) -> None:
    # Regression: Die Earnings-Profile setzen KEIN Klausel-Muster —
    # deren Anyone-Gate bleibt unveraendert wirksam.
    monkeypatch.setenv("BOT_PROFIL", "earnings_pg_july29")
    importlib.reload(config)
    try:
        assert config.SPRECHER_KLAUSEL_MUSTER is None
    finally:
        monkeypatch.delenv("BOT_PROFIL", raising=False)
        importlib.reload(config)


# ------------------------------------------------ Klausel-Gate


def test_sprecher_klausel_ersetzt_anyone_gate(snapshot) -> None:
    rules = _rules(snapshot)
    # Maerkte mit der Trump-Klausel sind aktiv, obwohl "mentioned by
    # anyone" nirgends steht.
    assert rules["3094193"].status == "active"
    assert rules["3094188"].status == "active"


def test_anyone_description_wird_geskippt(snapshot, tmp_path,
                                          monkeypatch) -> None:
    # Ein Markt mit Earnings-Anyone-Description im selben Snapshot
    # (Event-/Profil-Mix nach Slug-Roll) darf NICHT aktiv werden.
    maerkte = EVENT_MARKETS + [
        _markt("999003", 'Will Trump say "Economy" during Michigan remarks?',
               sprecher=False),
    ]
    pfad = tmp_path / "snapshot_mix.json"
    pfad.write_text(json.dumps({"event_id": "x", "markets": maerkte}),
                    encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    rules = _rules(pfad)
    assert rules["999003"].status == "skip"
    assert rules["999003"].skip_grund == "sprecher_klausel_fehlt"


def test_not_air_markt_bleibt_negationsskip(snapshot) -> None:
    rules = _rules(snapshot)
    assert rules["3094211"].status == "skip"
    assert rules["3094211"].skip_grund == "negationsmarkt_ohne_wortzaehlung"


# ------------------------------------------------ Schwellen und Varianten


def test_schwellen_aus_fragetext(snapshot) -> None:
    rules = _rules(snapshot)
    assert rules["3094188"].schwelle == 15
    assert rules["3094189"].schwelle == 12
    assert rules["3094190"].schwelle == 10
    assert rules["3094191"].schwelle == 7
    assert rules["3094192"].schwelle == 5
    assert rules["3114660"].schwelle == 20
    assert rules["3094193"].schwelle == 1


def test_oder_brackets_summieren_beide_begriffe(snapshot) -> None:
    # "Joe" or "Biden" 12+: beide Begriffe zaehlen in EINEN Zaehler.
    rules = _rules(snapshot)
    assert rules["3094189"].varianten == ["Joe", "Biden"]
    z = StreamingCounter(rules["3094189"])
    z.ingest_chunk(1, [Segment(text="Joe Biden and Biden's plan, Joe.",
                               confidence=0.95)], "t")
    assert z.count == 4


def test_percent_zaehlt_prozentzeichen(snapshot) -> None:
    # Whisper schreibt "fifty percent" im Zahlenkontext als "50%" — die
    # "%"-Variante schliesst die Luecke; keine Doppelzaehlung, weil nie
    # beides im selben Token steht.
    rules = _rules(snapshot)
    assert "%" in rules["3094188"].varianten
    z = StreamingCounter(rules["3094188"])
    z.ingest_chunk(1, [Segment(
        text="Inflation hit 50% then 20 percent, some say ten per cent.",
        confidence=0.95)], "t")
    assert z.count == 3
    z.ingest_chunk(2, [Segment(text="We are up 300%.", confidence=0.95)], "t")
    assert z.count == 4
    # "percentage" ist KEINE Erwaehnung von "percent" (strikte Grenze).
    z.ingest_chunk(3, [Segment(text="a large percentage of voters",
                               confidence=0.95)], "t")
    assert z.count == 4


def test_drill_baby_drill_mit_asr_kommas(snapshot) -> None:
    rules = _rules(snapshot)
    z = StreamingCounter(rules["3094204"])
    z.ingest_chunk(1, [Segment(text="We will drill, baby, drill!",
                               confidence=0.95)], "t")
    assert z.count == 1
    z.ingest_chunk(2, [Segment(text="drill baby drill", confidence=0.95)], "t")
    assert z.count == 2


def test_motor_city_phrase_nativ(snapshot) -> None:
    rules = _rules(snapshot)
    z = StreamingCounter(rules["3094194"])
    z.ingest_chunk(1, [Segment(text="Welcome back to the Motor City!",
                               confidence=0.95)], "t")
    assert z.count == 1


def test_usmca_asr_varianten(snapshot) -> None:
    rules = _rules(snapshot)
    z = StreamingCounter(rules["3114659"])
    z.ingest_chunk(1, [Segment(text="U.S.M.C.A. replaced NAFTA.",
                               confidence=0.95)], "t")
    assert z.count == 2


# ------------------------------------------------ Sprecher-Gates


def _seg(text: str, ist_ziel: bool | None = None,
         start: float = 10.0, ende: float = 12.0) -> Segment:
    return Segment(text=text, confidence=0.95, start_s=start, end_s=ende,
                   ist_ziel=ist_ziel)


class _MerkExecutor:
    ausgegeben_usd = 0.0

    def __init__(self) -> None:
        self.aufrufe: list = []

    def place(self, decision, book):
        from operations.pipeline.execution import PlacementResult

        self.aufrufe.append(decision)
        status = "dry_run_fill" if decision.action != "NONE" else "no_action"
        return PlacementResult(
            decision.market_id, decision.action, decision.token_id,
            decision.limit_price, 0.0, 0.0, status, "test",
        )


def test_kauf_gesperrt_zaehlt_aber_kauft_nie(snapshot, tmp_path,
                                             monkeypatch) -> None:
    # Vorprogramm-Phase (Marker fehlt): Zaehler laufen, aber es gibt
    # weder Buch-Roundtrips noch Kaeufe — auch nicht bei Treffern.
    from operations.pipeline import earnings_bot

    monkeypatch.setattr(config, "LIVE_DIR", tmp_path)
    rules = _rules(snapshot)
    loan = rules["3094193"]
    counters = {loan.market_id: StreamingCounter(loan)}
    fetches: list[str] = []
    monkeypatch.setattr(
        earnings_bot, "fetch_book",
        lambda tok: fetches.append(tok) or {
            "asks": [{"price": "0.5", "size": "100"}], "bids": []})
    ex = _MerkExecutor()
    staende = earnings_bot._yes_phase(
        [loan], counters, [_seg("a loan for every family")], 1, "t1",
        ex, set(), {}, kauf_gesperrt=True)
    assert staende[loan.slug] == 1
    assert fetches == []
    assert ex.aufrufe == []
    # Marker gesetzt: derselbe Zaehlerstand loest jetzt den Kauf aus.
    earnings_bot._yes_phase(
        [loan], counters, [_seg("nothing new")], 2, "t2",
        ex, set(), {}, kauf_gesperrt=False)
    assert len(fetches) == 1
    assert [d.action for d in ex.aufrufe] == ["YES"]


def test_fremdsprecher_treffer_loesen_keinen_kauf_aus(snapshot, tmp_path,
                                                      monkeypatch) -> None:
    # ECAPA aktiv (ist_ziel gesetzt): Treffer von Vorrednern/Chants
    # (ist_ziel=False) erhoehen count, aber nicht ziel_count — kein
    # Kauf. Erst ein Trump-zugerechneter Treffer kauft.
    from operations.pipeline import earnings_bot

    monkeypatch.setattr(config, "LIVE_DIR", tmp_path)
    rules = _rules(snapshot)
    loan = rules["3094193"]
    counters = {loan.market_id: StreamingCounter(loan)}
    monkeypatch.setattr(
        earnings_bot, "fetch_book",
        lambda tok: {"asks": [{"price": "0.5", "size": "100"}], "bids": []})
    ex = _MerkExecutor()
    earnings_bot._yes_phase(
        [loan], counters, [_seg("the loan programs", ist_ziel=False)],
        1, "t1", ex, set(), {})
    assert counters[loan.market_id].count == 1
    assert counters[loan.market_id].ziel_count == 0
    assert ex.aufrufe == []
    earnings_bot._yes_phase(
        [loan], counters, [_seg("we fixed the loan crisis", ist_ziel=True)],
        2, "t2", ex, set(), {})
    assert counters[loan.market_id].ziel_count == 1
    assert [d.action for d in ex.aufrufe] == ["YES"]


def test_status_bericht_nennt_sprecher_gates(snapshot, tmp_path,
                                             monkeypatch) -> None:
    from operations.pipeline import earnings_bot

    monkeypatch.setattr(config, "LIVE_DIR", tmp_path)
    monkeypatch.setattr(
        earnings_bot, "fetch_book", lambda tok: {"asks": [], "bids": []})
    bericht = earnings_bot.status_bericht()
    assert bericht["sprecher_gebunden"] is True
    assert bericht["sprecher_referenz_vorhanden"] is False
    assert bericht["sprecher_marker"].endswith("SPRECHER_AKTIV")
    # Alle 6 Brackets im Bericht.
    assert len(bericht["zaehl_brackets"]) == 6
