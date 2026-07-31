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
    assert entscheide_no(r, 7, config.NO_ASK_OBERGRENZE + 0.001).action == "NONE"


def test_no_deckel_niedriger_als_yes() -> None:
    # E281-Lehre: teure NO (Wort verpasst -> Falschkauf) meiden. Der
    # NO-Deckel (0.80) ist niedriger als der YES-Deckel (0.90).
    assert config.NO_ASK_OBERGRENZE < config.ASK_OBERGRENZE
    r = rule_mit_schwelle(1)
    # Tension-Fall: NO @0.88 wird jetzt abgelehnt (frueher gekauft, verloren)
    assert entscheide_no(r, 0, 0.88).action == "NONE"
    # billige NO (grosser Puffer) wird weiter gekauft
    assert entscheide_no(r, 0, 0.44).action == "NO"
    assert entscheide_no(r, 0, config.NO_ASK_OBERGRENZE).action == "NO"


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


# ------------------------------------------------------------ Sprecher-Verifikation


def test_dual_zaehler_mit_zurechnung() -> None:
    r = build_rule(gamma_markt('Will "Cheat" be said during the episode?'))
    c = StreamingCounter(r)
    log = c.ingest_chunk(1, [
        Segment("no cheating but cheat", confidence=0.9, ist_ziel=True),
        Segment("cheat cheat", confidence=0.9, ist_ziel=False),  # Fremdstimme
    ], "t1")
    assert c.count == 3          # alle Stimmen
    assert c.ziel_count == 1     # nur Zielsprecher
    assert log.ziel_count_total == 1


def test_dual_zaehler_ohne_verifikation_identisch() -> None:
    r = build_rule(gamma_markt('Will "Cheat" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("cheat cheat", confidence=0.9)], "t1")
    assert c.count == c.ziel_count == 2


# ------------------------------------- Event-Mentions-PDF / Lemonade Stand


def test_negationsmarkt_mit_showname() -> None:
    r = build_rule(gamma_markt("Will no Lemonade Stand episode air?"))
    assert r.status == "skip"
    assert r.skip_grund == "negationsmarkt_ohne_wortzaehlung"


def test_zitiertes_no_ist_kein_negationsmarkt() -> None:
    r = build_rule(gamma_markt(
        'Will "No" be said during the next episode of the podcast?'
    ))
    assert r.status == "active"


def test_ai_expandiert_nicht_zur_langform() -> None:
    # PDF "Expanded Acronyms": Langform zaehlt nur, wenn selbst zitiert.
    r = build_rule(gamma_markt('Will "AI" be said 35+ times during the episode?'))
    assert not any("intelligence" in v.lower() for v in r.varianten)
    assert "A.I." in r.varianten


def test_mehrwort_world_cup_mit_plural() -> None:
    p = compile_patterns(["World Cup"])
    assert count_in_text("the World Cup! world  cup. World Cups", p) == 3
    assert count_in_text("worldcup chatter", p) == 0


def test_erweiterter_zaehler_komposita_verdacht() -> None:
    # "evergreen" ist strikt kein Treffer fuer "Green", zaehlt aber als
    # Komposita-Verdacht in den erweiterten Zaehler (nur NO-Absicherung).
    r = build_rule(gamma_markt('Will "Green" be said during the episode?'))
    c = StreamingCounter(r)
    log = c.ingest_chunk(1, [Segment("an evergreen topic, green light",
                                     confidence=0.9)], "t1")
    assert c.count == 1
    assert c.erweitert_count == 2
    assert log.erweitert_count_total == 2


def test_erweiterter_zaehler_kurze_woerter_ohne_verdacht() -> None:
    # len<4 ("Red"): Substring-Verdacht aus, sonst zaehlt "hundred".
    r = build_rule(gamma_markt('Will "Red" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("a hundred times", confidence=0.95)], "t1")
    assert c.count == 0
    assert c.erweitert_count == 0


def test_erweiterter_zaehler_zaehlt_strikte_nur_einmal() -> None:
    r = build_rule(gamma_markt('Will "Money" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("money money moneymaker", confidence=0.9)], "t1")
    assert c.count == 2
    assert c.erweitert_count == 3


def test_jre_profil_titel_und_verbotsmuster() -> None:
    import re as _re

    p = config.PROFILE["jre_july13"]
    pflicht, verboten = p["titel_muster"], p["titel_verboten"]

    def qualifiziert(titel: str) -> bool:
        return bool(_re.search(pflicht, titel, _re.IGNORECASE)) and not bool(
            _re.search(verboten, titel, _re.IGNORECASE))

    # RSS-Format und YouTube-Format der Hauptepisoden
    assert qualifiziert("#2524 - Rupert Lowe")
    assert qualifiziert("Joe Rogan Experience #2523 - Ali Siddiq")
    # MMA-Show traegt #<n>, zaehlt laut Marktregel aber nicht
    assert not qualifiziert("JRE MMA Show #182 - Protect Ya Neck")
    assert not qualifiziert("JRE MMA Show #181 with Justin Gaethje & Trevor Wittman")
    # Nebenformate ohne Episodennummer scheitern am Pflichtmuster
    assert not qualifiziert("Fight Companion - June 2026")
    assert not qualifiziert("JRE Toon - The Best Trip Ever")


def test_elon_matcher_strikt_und_verdacht() -> None:
    from operations.pipeline.elon_bot import ElonMatcher
    from operations.pipeline.market_rules import MarketRule

    def rule(*begriffe):
        return MarketRule("m1", "s", "q", list(begriffe), 1, "y", "n", False)

    m = ElonMatcher(rule("Tesla"))
    # Strikt: exakt, Plural, Possessiv, Case, Sigils davor
    for t in ("Tesla rules", "two Teslas", "Tesla's plan", "$TESLA up",
              "#tesla", "@Tesla hi"):
        assert m.pruefe(t) == (True, False), t
    # Streckung: kein Auto-Kauf (zaehlt laut Regel nicht), aber Verdacht
    # (Regex kann Streckung nicht von Compound trennen -> manuell)
    assert m.pruefe("Teslaaa!") == (False, True)
    # Symbol im Wort: strikt nein, und auch kein Substring -> gar nichts
    assert m.pruefe("T3sla") == (False, False)
    # Compound/Handle-Rest -> nur Verdacht (kein Auto-Kauf)
    assert m.pruefe("the Teslabot cometh") == (False, True)
    assert m.pruefe("@tesla_fan yes") == (False, True)

    m2 = ElonMatcher(rule("Video game", "Videogame"))
    for t in ("a video game", "video-game night", "videogames forever"):
        assert m2.pruefe(t)[0] is True, t

    m3 = ElonMatcher(rule("Never"))
    assert m3.pruefe("Never give up") == (True, False)
    assert m3.pruefe("nevertheless") == (False, True)

    m4 = ElonMatcher(rule("IPO"))
    assert m4.pruefe("the IPO is on") == (True, False)
    assert m4.pruefe("three IPOs") == (True, False)


def test_nach_edge_sortiert_billigster_ask_zuerst() -> None:
    from operations.pipeline.decision import nach_edge_sortiert

    kand = [
        {"slug": "teuer", "best_ask": 0.88},
        {"slug": "billig", "best_ask": 0.12},
        {"slug": "kein_ask", "best_ask": None},
        {"slug": "mittel", "best_ask": 0.45},
    ]
    reihenfolge = [k["slug"] for k in nach_edge_sortiert(kand)]
    # billigster Ask zuerst (hoechster Grenzgewinn/Dollar), None ans Ende
    assert reihenfolge == ["billig", "mittel", "teuer", "kein_ask"]


def test_nach_edge_sortiert_stabil_bei_gleichheit() -> None:
    from operations.pipeline.decision import nach_edge_sortiert

    kand = [{"slug": "a", "best_ask": 0.5}, {"slug": "b", "best_ask": 0.5}]
    assert [k["slug"] for k in nach_edge_sortiert(kand)] == ["a", "b"]


def test_ev_deckel_ableitung() -> None:
    # ASK_OBERGRENZE = min(HARD_ASK_DECKEL, p_win - min_edge), gerundet.
    assert config.ASK_OBERGRENZE <= config.HARD_ASK_DECKEL + 1e-9
    erwartet = round(min(config.HARD_ASK_DECKEL,
                         config.EV_P_WIN - config.EV_MIN_EDGE), 4)
    assert config.ASK_OBERGRENZE == pytest.approx(erwartet)


def test_sizing_kauf_walk_und_kennzahlen() -> None:
    from operations.pipeline.sizing_analyse import (
        asks_aufsteigend,
        kauf_walk,
        kennzahlen,
    )

    # Bimodales Buch: billige Tranche 0.12/0.13, Luecke, Wall 0.80-0.90
    book = {"asks": [
        {"price": "0.90", "size": "10"}, {"price": "0.80", "size": "5"},
        {"price": "0.13", "size": "200"}, {"price": "0.12", "size": "50"},
    ]}
    asks = asks_aufsteigend(book)
    assert asks[0] == (0.12, 50.0)  # aufsteigend sortiert

    # EV-Grenze 0.97-0.03=... hier min_edge gross -> nur billige Tranche.
    # max_preis 0.20: nimmt 0.12 (6 USD) + 0.13 (26 USD) = 32 USD.
    opt = kauf_walk(asks, max_preis=0.20, budget=1000)
    assert opt["usd"] == pytest.approx(0.12 * 50 + 0.13 * 200)  # 32.0
    assert opt["n_level"] == 2

    # Deckel 0.90: nimmt zusaetzlich Wall 0.80 (4 USD) + 0.90 (9 USD).
    deck = kauf_walk(asks, max_preis=0.90, budget=1000)
    assert deck["usd"] == pytest.approx(32.0 + 0.80 * 5 + 0.90 * 10)  # 45.0
    assert deck["n_level"] == 4

    # Budget-Deckelung: nur 10 USD -> stoppt in der billigen Tranche.
    knapp = kauf_walk(asks, max_preis=0.90, budget=10.0)
    assert knapp["usd"] == pytest.approx(10.0)

    # Kennzahlen: EV = p_win*shares - usd; Worst = -usd.
    k = kennzahlen(opt, p_win=0.98)
    assert k["payout_gewinn"] == opt["shares"]
    assert k["ev"] == pytest.approx(round(0.98 * opt["shares"] - opt["usd"], 2))
    assert k["worst"] == pytest.approx(-opt["usd"])


def test_mrbeast_gaming_profil_konfiguration() -> None:
    p = config.PROFILE["mrbeast_gaming"]
    haupt = config.PROFILE["mrbeast"]
    # Eigener Gaming-Kanal, nicht der Hauptkanal
    assert p["yt_channel_id"] != haupt["yt_channel_id"]
    # Marktregel: Shorts/Previews zaehlen nicht -> 900s-Gate
    assert p["yt_min_dauer_s"] == 900
    # Sprecher-Verifikation zwingend, eigene Referenz-Kopie, Schwelle 0.50
    # (kalibriert 16.7.: MrBeast 0.52-0.64, Crew <=0.35)
    assert p["zielsprecher_referenz"].endswith(
        "mrbeast_gaming/referenz_stimme.npy")
    assert p["sprecher_schwelle"] == pytest.approx(0.50)
    # Hauptkanal-Profil bleibt beim Default (0.40 aus speaker.py)
    assert "sprecher_schwelle" not in haupt
    # Armierung 18.07.: Vollbudget + Basisraten-Serie (3 aufgeloeste
    # Vorwochen -> min_n 3), bewusst KEIN Boilerplate-Lexikon (Captions-
    # Check: Gaming-Videos haben keinen festen Intro/Outro-Rahmen).
    assert p["max_usd_gesamt"] == pytest.approx(510.0)
    assert p["serie_id"] == "11933"
    assert p["basisrate_min_n"] == 3
    assert "boilerplate_begriffe" not in p


def test_sprecher_schwelle_default_ableitung() -> None:
    # Aktives Testprofil (Default) definiert keine sprecher_schwelle ->
    # config leitet den speaker.py-Standard 0.40 ab.
    assert config.SPRECHER_SCHWELLE == pytest.approx(0.40)


def test_discovery_filter_mrbeast_profile_disjunkt() -> None:
    haupt = config.PROFILE["mrbeast"]
    gaming = config.PROFILE["mrbeast_gaming"]
    # Auto-Discovery (Event zu -> neuestes offenes Event mit Filter im
    # Slug) darf nie das Event des jeweils anderen Profils uebernehmen.
    assert haupt["discovery_slug_filter"] in haupt["event_slug"]
    assert gaming["discovery_slug_filter"] in gaming["event_slug"]
    assert haupt["discovery_slug_filter"] not in gaming["event_slug"]
    assert gaming["discovery_slug_filter"] not in haupt["event_slug"]


def test_lemonade_profil_titel_muster() -> None:
    import re as _re

    muster = config.PROFILE["lemonade_july15"]["titel_muster"]
    assert _re.search(muster, "We Made A World Cup of News Stories | "
                              "Lemonade Stand \U0001f34b", _re.IGNORECASE)
    assert _re.search(muster, "This Week Was Crazy | Lemonade Stand\U0001f34b",
                      _re.IGNORECASE)
    # Daily-Clips des Kanals tragen das Muster nicht:
    assert not _re.search(muster, "France VS Morocco | World Cup News",
                          _re.IGNORECASE)
    assert not _re.search(muster, "There's beef about beef", _re.IGNORECASE)


def test_fill_aus_antwort_bevorzugt_exakte_post_werte() -> None:
    from operations.pipeline.execution import fill_aus_antwort

    # BUY-FAK: taking = Shares, making = USDC — exakt, kein Deckel-Ansatz.
    shares, usd, quelle = fill_aus_antwort(
        {"takingAmount": "179.8", "makingAmount": "123.84"}, None, 0.9
    )
    assert (shares, usd, quelle) == (179.8, 123.84, "post_antwort")


def test_fill_aus_antwort_fallback_nutzt_entscheidungspreis() -> None:
    from operations.pipeline.execution import fill_aus_antwort

    # Kein Post-Match: size_matched zum besten Ask am Entscheid bewerten —
    # NICHT zum Order-Deckel (Wallet-Abgleich 18.07.).
    shares, usd, quelle = fill_aus_antwort(
        {}, {"size_matched": "50", "price": "0.9"}, 0.689
    )
    assert quelle == "status_geschaetzt"
    assert shares == 50.0
    assert usd == pytest.approx(34.45)


def test_fill_aus_antwort_kaputte_werte_fail_safe() -> None:
    from operations.pipeline.execution import fill_aus_antwort

    shares, usd, quelle = fill_aus_antwort(
        {"takingAmount": "x"}, {"size_matched": None}, None
    )
    assert (shares, usd) == (0.0, 0.0)
    assert quelle == "status_geschaetzt"


# ------------------------------------ NO-Absicherung (Review 18.07.2026)


def test_homophon_niedrige_konfidenz_zaehlt_im_erweiterten() -> None:
    # Befund: Homophon-Treffer mit Konfidenz <= 0.8 fielen aus ALLEN
    # Zaehlern — auch aus dem erweiterten, der NO absichert. Das Wort
    # koennte aber gefallen sein: fuer YES weiter nicht zaehlen (Praezision),
    # fuer NO konservativ schon (kein NO auf moeglicherweise Gesagtes).
    r = build_rule(gamma_markt('Will "Red" be said during the episode?'))
    c = StreamingCounter(r)
    log = c.ingest_chunk(1, [Segment("the red one", confidence=0.5)], "t1")
    assert c.count == 0
    assert c.ziel_count == 0
    assert c.erweitert_count == 1
    assert log.uebersprungen_homophon == 1
    assert entscheide_no(r, c.erweitert_count, 0.5).action == "NONE"


def test_homophon_hohe_konfidenz_unveraendert() -> None:
    r = build_rule(gamma_markt('Will "Red" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("red and red", confidence=0.95)], "t1")
    assert c.count == 2
    assert c.erweitert_count == 2


def test_homophon_skip_nimmt_auch_komposita_verdacht_mit() -> None:
    # Der Substring-Verdacht (Komposita) darf im Niedrig-Konfidenz-Segment
    # ebenfalls nicht verloren gehen: "blue" strikt + "blueberries" Verdacht.
    r = build_rule(gamma_markt('Will "Blue" be said during the episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("blue blueberries", confidence=0.3)], "t1")
    assert c.count == 0
    assert c.erweitert_count == 2


def test_homophon_segment_ohne_treffer_bleibt_null() -> None:
    r = build_rule(gamma_markt('Will "Red" be said during the episode?'))
    c = StreamingCounter(r)
    log = c.ingest_chunk(1, [Segment("nothing here", confidence=0.2)], "t1")
    assert c.count == 0
    assert c.erweitert_count == 0
    assert log.uebersprungen_homophon == 0


def test_preis_deckel_fuer_seite() -> None:
    from operations.pipeline.execution import preis_deckel_fuer

    assert preis_deckel_fuer("No") == config.NO_ASK_OBERGRENZE
    assert preis_deckel_fuer("no") == config.NO_ASK_OBERGRENZE
    assert preis_deckel_fuer("Yes") == config.ASK_OBERGRENZE
    assert preis_deckel_fuer(None) == config.ASK_OBERGRENZE


def _sweep_executor(tmp_path):
    """LiveExecutor ohne Client/Netz fuer Sweep-Tests."""
    from operations.pipeline.execution import LiveExecutor

    ex = object.__new__(LiveExecutor)
    ex.log_pfad = tmp_path / "decisions_log.jsonl"
    ex.ausgegeben_usd = 0.0
    ex._start_balance = None
    return ex


def test_sweep_no_stoppt_am_no_deckel(monkeypatch, tmp_path) -> None:
    # Befund: der Level-Sweep prueft das naechste Level und den FAK-Deckel
    # gegen ASK_OBERGRENZE (0.90) — NO-Sweeps fuellten so Level ueber dem
    # NO-Deckel (0.80) nach, obwohl entscheide_no nur den Einstieg gated.
    from operations.pipeline import orderbook
    from operations.pipeline.decision import Decision

    deckel_gesehen: list[float] = []

    def fake_bestell(token_id, usd, preis_deckel):
        deckel_gesehen.append(preis_deckel)
        return {"takingAmount": "10", "makingAmount": "5", "orderID": "o1"}

    ex = _sweep_executor(tmp_path)
    monkeypatch.setattr(ex, "_bestell", fake_bestell)
    monkeypatch.setattr(config, "MAX_CLIPS_PRO_MARKT", 3)
    monkeypatch.setattr(config, "MAX_USD_GESAMT", 100.0)
    # Hermetisch: der ECHTE globale Kill-Switch (data/live/STOP) darf den
    # Test nicht beeinflussen (Befund 18.07.: gesetztes STOP -> gave_up).
    monkeypatch.setattr(config, "STOP_FILE", tmp_path / "STOP")
    # Nach jedem Clip liegt der naechste Ask bei 0.85: unter dem YES-,
    # aber ueber dem NO-Deckel.
    monkeypatch.setattr(
        orderbook, "fetch_book",
        lambda tok: {"asks": [{"price": "0.85", "size": "100"}]},
    )

    d_no = Decision("m1", "NO", "tok_no", "No", 0.79, "test")
    res = ex._platziere(d_no, usd=15.0, shares=19.0)
    assert res.status == "live_fill"
    assert deckel_gesehen == [config.NO_ASK_OBERGRENZE]  # 1 Clip, dann Stopp

    deckel_gesehen.clear()
    d_yes = Decision("m2", "YES", "tok_yes", "Yes", 0.79, "test")
    res = ex._platziere(d_yes, usd=15.0, shares=19.0)
    assert res.status == "live_fill"
    # YES darf bei 0.85 weiterkaufen, bis MAX_CLIPS_PRO_MARKT greift.
    assert deckel_gesehen == [config.ASK_OBERGRENZE] * 3


# ------------------------------------ JRE july-20 Armierung (18.07.2026)


def test_jre_july20_profil_konfiguration() -> None:
    p = config.PROFILE["jre_july20"]
    alt = config.PROFILE["jre_july13"]
    # Quellen und Titel-Gates unveraendert zur Vorwoche
    assert p["rss_feed_url"] == alt["rss_feed_url"]
    assert p["yt_channel_id"] == alt["yt_channel_id"]
    assert p["titel_muster"] == alt["titel_muster"]
    assert p["titel_verboten"] == alt["titel_verboten"]
    assert p["event_id"] == "704429"
    # Vollpool + Sweep wie mrbeast/trump
    assert p["max_usd_gesamt"] == pytest.approx(510.0)
    assert p["max_clips_pro_markt"] == 40
    # NO-Schutzschichten: Serie rogan-mentions + Intro-Jingle-Lexikon
    assert p["serie_id"] == "11275"
    for wort in ("train", "night", "rogan", "podcast", "day"):
        assert wort in p["boilerplate_begriffe"]
    # Nachlauf verlaengert (duenne Buecher, traege MMs)
    assert p["nachlauf_minuten"] == 90


def test_nachlauf_default_bleibt_45() -> None:
    # Aktives Testprofil (Default) hat keinen Override -> 45.
    assert config.NACHLAUF_MINUTEN == pytest.approx(45.0)


def test_jre_boilerplate_blockt_no_der_intro_woerter(monkeypatch) -> None:
    monkeypatch.setattr(config, "BOILERPLATE_BEGRIFFE",
                        frozenset(config.JRE_BOILERPLATE))
    r = build_rule(gamma_markt('Will "Train" be said during the episode?'))
    assert r.boilerplate_sensitiv
    d = entscheide_no(r, 0, 0.44)
    assert d.action == "NONE"
    assert "boilerplate" in d.reason
    # Nicht-Intro-Wort bleibt als NO handelbar
    r2 = build_rule(gamma_markt('Will "Alien" be said during the episode?'))
    assert not r2.boilerplate_sensitiv
    assert entscheide_no(r2, 0, 0.44).action == "NO"


# --------------------------------- Lemonade july-22 Armierung (22.07.2026)


def test_lemonade_july22_profil_konfiguration() -> None:
    p = config.PROFILE["lemonade_july22"]
    alt = config.PROFILE["lemonade_july15"]
    # Quellen und Titel-Gate unveraendert zur Vorwoche
    assert p["rss_feed_url"] == alt["rss_feed_url"]
    assert p["yt_channel_id"] == alt["yt_channel_id"]
    assert p["titel_muster"] == alt["titel_muster"]
    assert p["yt_min_dauer_s"] == 900
    assert p["event_id"] == "708407"
    # Vollpool + Sweep + langer Nachlauf (duenne Buecher)
    assert p["max_usd_gesamt"] == pytest.approx(510.0)
    assert p["max_clips_pro_markt"] == 40
    assert p["nachlauf_minuten"] == 90
    # Basisraten-Serie mit 7 aufgeloesten Vorwochen; bewusst KEIN
    # Boilerplate-Lexikon (kein festes Jingle, Captions-Check 22.07.)
    assert p["serie_id"] == "11828"
    assert "boilerplate_begriffe" not in p


# ----------------------------------- All-In july-24 / E282 (23.07.2026)


def test_allin_july24_profil_konfiguration() -> None:
    p = config.PROFILE["allin_july24"]
    alt = config.PROFILE["allin_july17"]
    # Quellen und Gates identisch zur bewiesenen E281-Woche
    assert p["mp3_probe_muster"] == alt["mp3_probe_muster"]
    assert p["yt_playlist_id"] == alt["yt_playlist_id"]
    assert p["rss_nur_muster"] == alt["rss_nur_muster"]
    assert p["event_id"] == "715508"
    # NO-Schutzschild komplett: Boilerplate + Basisraten-Serie
    assert "tension" in p["boilerplate_begriffe"]
    assert p["serie_id"] == "11300"
    # Volles Kapital, grosser Sweep, langes Nachlauf-Fenster
    assert p["max_usd_gesamt"] == pytest.approx(500.0)
    assert p["max_usd_pro_markt"] == pytest.approx(50.0)
    assert p["max_clips_pro_markt"] == 40
    assert p["nachlauf_minuten"] == 90
    # NO-Deckel bleibt beim Default 0.80 (kein Override — die E281-Lehre)
    assert "no_ask_obergrenze" not in p


# ----------------------------------- All-In july-31 / E283 (31.07.2026)


def test_allin_july31_profil_konfiguration() -> None:
    p = config.PROFILE["allin_july31"]
    alt = config.PROFILE["allin_july24"]
    # Quellen und Gates identisch zur gelaufenen E282-Woche
    assert p["mp3_probe_muster"] == alt["mp3_probe_muster"]
    assert p["yt_playlist_id"] == alt["yt_playlist_id"]
    assert p["rss_nur_muster"] == alt["rss_nur_muster"]
    assert p["rss_feed_url"] == alt["rss_feed_url"]
    assert p["yt_channel_id"] == alt["yt_channel_id"]
    assert p["discovery_slug_filter"] == alt["discovery_slug_filter"]
    # Eigenes Event und eigener Lauf-Ordner (kein Ueberschreiben von E282)
    assert p["event_id"] == "758791"
    assert p["event_slug"].startswith(
        "what-will-be-said-on-the-next-all-in-podcast-july-31-")
    assert p["live_dir"] == "allin_july31"
    assert p["live_dir"] != alt["live_dir"]
    # NO-Schutzschild komplett und unveraendert: Boilerplate + Basisraten
    assert p["boilerplate_begriffe"] == alt["boilerplate_begriffe"]
    assert "tension" in p["boilerplate_begriffe"]
    assert p["serie_id"] == "11300"
    # NO-Deckel bleibt beim Default 0.80 (kein Override — die E281-Lehre)
    assert "no_ask_obergrenze" not in p
    # Volles Budget (User 31.07.), Clip-Groesse und Sweep wie july24
    assert p["max_usd_gesamt"] == pytest.approx(620.0)
    assert p["max_usd_pro_markt"] == alt["max_usd_pro_markt"]
    assert p["max_clips_pro_markt"] == alt["max_clips_pro_markt"]
    assert p["nachlauf_minuten"] == alt["nachlauf_minuten"]
