"""Tests fuer Parser, Zaehler und Entscheidungsregeln des All-In-Bots."""

from __future__ import annotations

import json

import pytest

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter, compile_patterns, count_in_text
from operations.pipeline.decision import entscheide_no, entscheide_yes
from operations.pipeline.execution import berechne_groesse
from operations.pipeline.market_rules import (
    build_rule,
    parse_schwelle,
    parse_zitierte_begriffe,
)


def gamma_markt(question: str, description: str = "Standard resolution.") -> dict:
    return {
        "id": "111",
        "slug": "test-markt",
        "question": question,
        "description": description,
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(["tok_yes", "tok_no"]),
    }


# ------------------------------------------------------------ Parser


def test_parse_zitierte_begriffe_und_or() -> None:
    q = 'Will "Elon" or "Musk" be said during the next episode of the All-In Podcast?'
    assert parse_zitierte_begriffe(q) == ["Elon", "Musk"]


def test_parse_schwelle_default_und_n_plus() -> None:
    assert parse_schwelle('Will "Blue" be said during the next episode?') == 1
    assert parse_schwelle('Will "Trump" be said 10+ times during the episode?') == 10
    assert parse_schwelle('Will "AI" be said 40+ times during the episode?') == 40


def test_build_rule_ai_varianten() -> None:
    r = build_rule(gamma_markt(
        'Will "AI" or "Artificial Intelligence" be said 40+ times during the next episode?'
    ))
    assert r.status == "active"
    assert r.schwelle == 40
    assert "A.I." in r.varianten
    assert any(v.lower() == "artificial intelligence" for v in r.varianten)


def test_build_rule_homophon_markiert() -> None:
    assert build_rule(gamma_markt('Will "Red" be said during the episode?')).homophon_sensitiv
    assert not build_rule(gamma_markt('Will "Stock" be said during the episode?')).homophon_sensitiv


def test_build_rule_skip_negationsmarkt() -> None:
    r = build_rule(gamma_markt("Will no episode air?"))
    assert r.status == "skip"
    assert r.skip_grund == "negationsmarkt_ohne_wortzaehlung"


def test_build_rule_skip_ohne_zitat() -> None:
    r = build_rule(gamma_markt("Will the hosts talk for two hours?"))
    assert r.status == "skip"


def test_build_rule_skip_bei_ausnahmebedingung() -> None:
    r = build_rule(gamma_markt(
        'Will "Stock" be said during the episode?',
        description="Resolves Yes unless the episode is a rerun.",
    ))
    assert r.status == "skip"
    assert r.skip_grund == "aufloesungsregel_mit_ausnahmebedingung"


# ------------------------------------------------------------ Zaehler


def test_count_wortgrenzen_und_case() -> None:
    p = compile_patterns(["First"])
    assert count_in_text("First things first. FIRST!", p) == 3
    assert count_in_text("firstly, the firstborn", p) == 0


def test_count_plural_und_possessiv() -> None:
    p = compile_patterns(["Trump"])
    assert count_in_text("Trump, Trumps, Trump's", p) == 3


def test_count_ai_punktvariante_und_mehrwort() -> None:
    p = compile_patterns(["AI", "A.I.", "artificial intelligence"])
    assert count_in_text("AI is here. A.I. wins. artificial  intelligence!", p) == 3
    # 'aim' oder 'said' duerfen nicht matchen
    assert count_in_text("we aim to say said", p) == 0


def test_streaming_counter_homophon_gating() -> None:
    r = build_rule(gamma_markt('Will "Red" be said during the episode?'))
    c = StreamingCounter(r)
    # Niedrige Konfidenz: Treffer wird uebersprungen und geflaggt
    log1 = c.ingest_chunk(1, [Segment("the red one", confidence=0.5)], "t1")
    assert c.count == 0
    assert log1.uebersprungen_homophon == 1
    # Hohe Konfidenz: zaehlt
    c.ingest_chunk(2, [Segment("red again", confidence=0.95)], "t2")
    assert c.count == 1


def test_streaming_counter_nicht_homophon_ignoriert_konfidenz() -> None:
    r = build_rule(gamma_markt('Will "Stock" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("stock stock", confidence=0.1)], "t1")
    assert c.count == 2


# ------------------------------------------------------------ Entscheidung


def rule_mit_schwelle(n: int):
    q = ('Will "Trump" be said during the episode?' if n <= 1
         else f'Will "Trump" be said {n}+ times during the episode?')
    return build_rule(gamma_markt(q))


def test_yes_bei_schwelle_1_reicht_ein_treffer() -> None:
    r = rule_mit_schwelle(1)
    assert entscheide_yes(r, 0, 0.5).action == "NONE"
    d = entscheide_yes(r, 1, 0.5)
    assert d.action == "YES"
    assert d.token_id == "tok_yes"


def test_yes_braucht_schwelle_plus_2() -> None:
    r = rule_mit_schwelle(10)
    assert entscheide_yes(r, 11, 0.5).action == "NONE"
    assert entscheide_yes(r, 12, 0.5).action == "YES"


def test_yes_ask_grenze() -> None:
    r = rule_mit_schwelle(1)
    g = config.ASK_OBERGRENZE
    assert entscheide_yes(r, 1, g).action == "YES"
    assert entscheide_yes(r, 1, g + 0.001).action == "NONE"
    assert entscheide_yes(r, 1, None).action == "NONE"


def test_no_erst_unter_70_prozent() -> None:
    r = rule_mit_schwelle(10)
    assert entscheide_no(r, 7, 0.5).action == "NO"     # 7 <= 7.0
    assert entscheide_no(r, 8, 0.5).action == "NONE"   # 8 > 7.0
    assert entscheide_no(r, 7, config.ASK_OBERGRENZE + 0.001).action == "NONE"


def test_no_bei_schwelle_1_nur_null_treffer() -> None:
    r = rule_mit_schwelle(1)
    assert entscheide_no(r, 0, 0.5).action == "NO"
    assert entscheide_no(r, 1, 0.5).action == "NONE"


def test_skip_markt_nie_handeln() -> None:
    r = build_rule(gamma_markt("Will no episode air?"))
    assert entscheide_yes(r, 99, 0.1).action == "NONE"
    assert entscheide_no(r, 0, 0.1).action == "NONE"


# ------------------------------------------------------------ Sizing


def buch(asks):
    return {"asks": [{"price": str(p), "size": str(s)} for p, s in asks]}


def test_groesse_min_aus_tiefe_und_limits() -> None:
    b = buch([(0.80, 2.0), (0.84, 2.0), (0.90, 100.0)])  # Tiefe bis 0.85: 3.28
    usd, shares = berechne_groesse(b, 0.85, budget_rest=25.0)
    assert usd == pytest.approx(3.28)
    assert shares == pytest.approx(round(3.28 / 0.85, 2))


def test_groesse_kappt_auf_max_pro_markt_und_budget() -> None:
    b = buch([(0.80, 1000.0)])
    usd, _ = berechne_groesse(b, 0.85, budget_rest=25.0)
    assert usd == config.MAX_USD_PRO_MARKT
    usd2, _ = berechne_groesse(b, 0.85, budget_rest=1.5)
    assert usd2 == pytest.approx(1.5)
    usd3, _ = berechne_groesse(b, 0.85, budget_rest=0.0)
    assert usd3 == 0.0


# ------------------------------------------------------------ Overlap-Dedup


class FakeWort:
    def __init__(self, word, start, end=None):
        self.word, self.start, self.end = word, start, end or start + 0.3


class FakeSeg:
    def __init__(self, words, avg_logprob=-0.1):
        self.words = words
        self.avg_logprob = avg_logprob
        self.text = "".join(w.word for w in words)
        self.start = words[0].start
        self.end = words[-1].end


def test_wort_dedup_zaehlt_nur_ab_grenze() -> None:
    from operations.pipeline.transcription import segmente_mit_wort_dedup

    seg = FakeSeg([FakeWort(" Trump", 58.5), FakeWort(" wins", 59.2),
                   FakeWort(" Trump", 60.4)])
    out = segmente_mit_wort_dedup([seg], grenze_s=60.0)
    assert len(out) == 1
    assert out[0].text == " Trump"
    assert out[0].start_s == 60.4


def test_wort_dedup_leeres_ergebnis_wenn_alles_vor_grenze() -> None:
    from operations.pipeline.transcription import segmente_mit_wort_dedup

    seg = FakeSeg([FakeWort(" alt", 10.0)])
    assert segmente_mit_wort_dedup([seg], grenze_s=60.0) == []


# ------------------------------------------------------------ YouTube-Watcher


def test_parse_yt_feed() -> None:
    from operations.pipeline.rss_watch import parse_yt_feed

    xml = """<feed><entry><yt:videoId>abc123</yt:videoId>
    <title>Episode X</title><published>2026-07-03T14:00:00+00:00</published>
    </entry><entry><yt:videoId>def456</yt:videoId><title>Clip Y</title>
    <published>2026-07-02T10:00:00+00:00</published></entry></feed>"""
    videos = parse_yt_feed(xml)
    assert [v.video_id for v in videos] == ["abc123", "def456"]
    assert videos[0].url.endswith("abc123")


def test_ist_voll_episode_regeln() -> None:
    from operations.pipeline.transcription import ist_voll_episode

    assert ist_voll_episode({"dauer_s": 3600, "is_live": False})[0] is True
    assert ist_voll_episode({"dauer_s": 600, "is_live": False})[0] is False
    assert ist_voll_episode({"dauer_s": None, "is_live": False})[0] is False
    assert ist_voll_episode({"dauer_s": 3600, "is_live": True})[0] is False
    assert ist_voll_episode(
        {"dauer_s": 3600, "is_live": False, "live_status": "is_upcoming"}
    )[0] is False


# ------------------------------------------------------------ MP3-URL-Prober


def test_naechste_episoden_nummer() -> None:
    from operations.pipeline.rss_watch import FeedItem, naechste_episoden_nummer

    items = [
        FeedItem("g1", "E279", "", "https://x/ALLIN-E279_Ch.mp3?d=1"),
        FeedItem("g2", "Special", "", "https://x/FINAL_PASS_NATE.mp3"),
        FeedItem("g3", "E278", "", "https://x/ALLIN-E278_Ch.mp3"),
    ]
    assert naechste_episoden_nummer(items) == 280


def test_prober_feuert_erst_bei_stabiler_laenge() -> None:
    from operations.pipeline.rss_watch import Mp3UrlProber

    antworten = {"status": 404, "laenge": None}

    def head(url):
        return antworten["status"], antworten["laenge"]

    p = Mp3UrlProber(
        280, head_fn=head,
        muster="https://x/ALLIN-E{n}_Ch.mp3")
    assert p.poll() is None                       # 404
    antworten.update(status=200, laenge="1000")
    assert p.poll() is None                       # erster 200: noch instabil
    antworten.update(laenge="2000")
    assert p.poll() is None                       # waechst noch
    assert p.poll() == p.urls[0]                  # stabil -> feuert


def test_parse_yt_kanalseite_dedupliziert() -> None:
    from operations.pipeline.rss_watch import parse_yt_kanalseite

    html = ('x"videoId":"abcdefghijk"y'
            '"videoId":"abcdefghijk"z'
            '"videoId":"LMNOPQRSTUV"w')
    videos = parse_yt_kanalseite(html)
    assert [v.video_id for v in videos] == ["abcdefghijk", "LMNOPQRSTUV"]
