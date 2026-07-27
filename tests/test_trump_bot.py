"""Tests fuer den Trump-Truth-Social-Bot (Event 690224, Serie trump-post-weekly).

Marktregeln sind wortgleich mit der Elon-Serie (Plural/Possessiv/Case/
Sigils zaehlen, Compounds zaehlen, Misspellings/Symbole-im-Wort nicht,
Quotes/RePosts zaehlen nicht, eigener Text in Quotes/Replies schon) —
der Matcher wird deshalb aus elon_bot wiederverwendet. Neu sind die
Truth-Social-Quelle (truth_watch, Cloudflare via curl_cffi-Impersonation)
und der Startscan seit Periodenstart.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from operations.pipeline.elon_bot import ElonMatcher, baue_elon_rules
from operations.pipeline.market_rules import MarketRule
from operations.pipeline.truth_watch import (
    TruthPost,
    _text_aus_html,
    parse_status,
)
from operations.pipeline.trump_bot import hole_startscan


def _rule(begriffe: list[str]) -> MarketRule:
    return MarketRule(
        market_id="1", slug="s", question="q", varianten=begriffe,
        schwelle=1, yes_token_id="y", no_token_id="n",
        homophon_sensitiv=False,
    )


# ------------------------------------------------- HTML -> Text


def test_text_aus_html_entfernt_links_und_entities() -> None:
    # Truth zerlegt URLs in <a>-Spans ("election-integrity" stuende sonst
    # als Klartext im Matching-Text) — Links fliegen KOMPLETT raus.
    html = ('<p>Great &amp; BIG news! <a href="https://x.gov/election-'
            'integrity"><span>https://www.</span><span>whitehouse.gov/'
            'election-integr</span><span>ity</span></a> Read it.</p>')
    text = _text_aus_html(html)
    assert "Great & BIG news!" in text
    assert "Read it." in text
    assert "election" not in text.lower()
    assert "whitehouse" not in text.lower()


def test_text_aus_html_absatz_und_bruch() -> None:
    assert _text_aus_html("<p>Zeile1<br>Zeile2</p><p>Zeile3</p>") == \
        "Zeile1 Zeile2 Zeile3"


# ------------------------------------------------- Status-Parsing


def _status(**kw) -> dict:
    basis = {
        "id": "116938579137506694",
        "created_at": "2026-07-18T02:18:32.394Z",
        "content": "<p>Tim Sheehy is GREAT. A Winner!!!</p>",
        "reblog": None,
        "quote": None,
        "quote_id": None,
        "in_reply_to_id": None,
        "media_attachments": [],
    }
    basis.update(kw)
    return basis


def test_parse_status_normalisiert_zeit_und_flags() -> None:
    p = parse_status(_status())
    assert p.post_id == 116938579137506694
    assert p.created_utc == "2026-07-18T02:18:32Z"  # Millis weg
    assert p.text == "Tim Sheehy is GREAT. A Winner!!!"
    assert (p.ist_repost, p.ist_reply, p.hat_medien, p.hat_quote) == (
        False, False, False, False)


def test_parse_status_retruth_wird_markiert() -> None:
    p = parse_status(_status(reblog={"id": "1", "content": "<p>Fremd</p>"}))
    assert p.ist_repost
    assert "Fremd" not in p.text


def test_parse_status_quote_eigener_text_zaehlt_fremder_nicht() -> None:
    p = parse_status(_status(
        content='<p>RT: <a href="https://truthsocial.com/x/1">link</a> '
                "My own GOAL comment</p>",
        quote={"id": "1", "content": "<p>Fremdes Uranium Statement</p>"},
        quote_id="1",
    ))
    assert p.hat_quote
    assert "GOAL" in p.text
    assert "Uranium" not in p.text


def test_parse_status_reply_und_medien() -> None:
    p = parse_status(_status(in_reply_to_id="5",
                             media_attachments=[{"type": "image"}]))
    assert p.ist_reply
    assert p.hat_medien


# ------------------------------------------------- Matching (Trump-Regeln)


def test_matcher_trump_regeln_wortgleich_zu_elon() -> None:
    m = ElonMatcher(_rule(["Goal"]))
    assert m.pruefe("GOAL!!!") == (True, False)          # Case egal
    assert m.pruefe("what a #goal today") == (True, False)  # Sigil ok
    assert m.pruefe("two goals scored") == (True, False)    # Plural
    assert m.pruefe("g0al") == (False, False)               # Symbol im Wort
    assert m.pruefe("gooooal") == (False, False)            # Streckung
    assert m.pruefe("supergoal") == (False, True)           # Compound-Verdacht


def test_matcher_mehrwort_wall_street() -> None:
    m = ElonMatcher(_rule(["Wall Street"]))
    assert m.pruefe("Wall Street is booming") == (True, False)
    assert m.pruefe("wall-street rally") == (True, False)
    assert m.pruefe("wallstreet") == (False, False)  # zusammengeschrieben


# ------------------------------------------------- Rules aus Snapshot


def test_trump_rules_aus_snapshot(tmp_path, monkeypatch) -> None:
    from operations.pipeline import config

    snap = {"markets": [
        {"id": "1", "slug": "will-trump-post-goal-on-truth-social",
         "question": 'Will Trump post "Goal" on Truth Social?',
         "outcomes": json.dumps(["Yes", "No"]),
         "clobTokenIds": json.dumps(["ty", "tn"]), "closed": False,
         "description": "boilerplate only if image text"},
        {"id": "2", "slug": "will-trump-post-china-on-truth-social",
         "question": 'Will Trump post "China" on Truth Social?',
         "outcomes": json.dumps(["Yes", "No"]),
         "clobTokenIds": json.dumps(["cy", "cn"]), "closed": True,
         "description": ""},
    ]}
    pfad = tmp_path / "snap.json"
    pfad.write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    rules = baue_elon_rules()
    assert len(rules) == 1  # geschlossene Maerkte fliegen raus
    assert rules[0].varianten == ["Goal"]
    assert rules[0].schwelle == 1


# ------------------------------------------------- Startscan


class _FakeWatcher:
    """Zwei Seiten Historie: neueste zuerst, wie die echte API."""

    def __init__(self) -> None:
        def p(pid, ts):
            return TruthPost(post_id=pid, created_utc=ts, text=f"post {pid}",
                             ist_repost=False, ist_reply=False,
                             hat_medien=False, hat_quote=False)

        self.seiten = [
            [p(30, "2026-07-18T02:00:00Z"), p(20, "2026-07-15T12:00:00Z")],
            [p(10, "2026-07-13T05:00:00Z"), p(5, "2026-07-12T23:00:00Z")],
            [],
        ]
        self.max_ids: list[int | None] = []

    def hole_posts(self, since_id=None, max_id=None, limit=40):
        self.max_ids.append(max_id)
        return self.seiten[len(self.max_ids) - 1]


def test_hole_startscan_paginiert_bis_periodenstart() -> None:
    w = _FakeWatcher()
    start = datetime(2026, 7, 13, 4, 0, tzinfo=timezone.utc)
    posts = hole_startscan(w, start, seiten_pause_s=0)
    # Post 5 (vor Periodenstart) beendet die Pagination und fliegt raus.
    assert sorted(p.post_id for p in posts) == [10, 20, 30]
    # Seite 2 wurde mit max_id des aeltesten Posts von Seite 1 geholt.
    assert w.max_ids == [None, 20]


# ------------------------------------ Wochen-Rollover (23.07.2026)


def test_trump_july20_profil_neue_woche() -> None:
    from operations.pipeline import config

    p = config.PROFILE["trump_july20"]
    alt = config.PROFILE["trump_july13"]
    # Quelle unveraendert (Truth Social, derselbe verifizierte Account)
    assert p["truth_user_id"] == alt["truth_user_id"]
    assert p["discovery_slug_filter"] == alt["discovery_slug_filter"]
    # Neues Event + Periode 20.-26.07. ET, luecken- und ueberlappungsfrei
    # zur Vorwoche (deren Ende ist der neue Start).
    assert p["event_id"] == "715499"
    assert p["periode_start_utc"] == "2026-07-20T04:00:00Z"
    assert p["periode_ende_utc"] == "2026-07-27T03:59:59Z"
    assert alt["periode_ende_utc"] < p["periode_start_utc"]
    # Budget an den realen Wallet-Stand angepasst (geteiltes Wallet)
    assert p["max_usd_gesamt"] == pytest.approx(400.0)


def test_trump_july27_profil_neue_woche() -> None:
    from operations.pipeline import config

    p = config.PROFILE["trump_july27"]
    alt = config.PROFILE["trump_july20"]
    # Quelle unveraendert (Truth Social, derselbe verifizierte Account,
    # gleicher Poll-Takt gegen die Cloudflare-Drosselung).
    assert p["truth_user_id"] == alt["truth_user_id"]
    assert p["truth_poll_s"] == alt["truth_poll_s"]
    assert p["discovery_slug_filter"] == alt["discovery_slug_filter"]
    # Neues Event + Periode 27.07.-02.08. ET, luecken- und
    # ueberlappungsfrei zur Vorwoche (deren Ende ist der neue Start).
    assert p["event_id"] == "745692"
    assert p["periode_start_utc"] == "2026-07-27T04:00:00Z"
    assert p["periode_ende_utc"] == "2026-08-03T03:59:59Z"
    assert alt["periode_ende_utc"] < p["periode_start_utc"]
    # Budget: Vorwochen-Wert uebernommen; Bestaetigung am realen
    # Wallet-Stand ist Runbook-Schritt vor dem Scharfschalten.
    assert p["max_usd_gesamt"] == pytest.approx(400.0)
    assert p["max_usd_pro_markt"] == pytest.approx(50.0)
    assert p["max_clips_pro_markt"] == 40


def test_trump_july27_oder_und_mehrwort_begriffe(tmp_path,
                                                 monkeypatch) -> None:
    # Echte Fragen des Events 745692 (Gamma, 27.07.): zwei Mehrwort-
    # Begriffe ("Wall Street", "President Xi") und zwei Oder-Maerkte in
    # einer Woche — die Ableitung muss alle Varianten tragen.
    from operations.pipeline import config

    def _m(mid: str, frage: str) -> dict:
        return {"id": mid, "slug": f"will-trump-post-{mid}",
                "question": frage, "outcomes": json.dumps(["Yes", "No"]),
                "clobTokenIds": json.dumps([f"y{mid}", f"n{mid}"]),
                "closed": False, "description": ""}

    snap = {"markets": [
        _m("3093886",
           'Will Trump post "Lindsey" or "Graham" on Truth Social '
           "this week?"),
        _m("3093887",
           'Will Trump post "Wall Street" on Truth Social this week?'),
        _m("3093888",
           'Will Trump post "President Xi" on Truth Social this week?'),
        _m("3093889",
           'Will Trump post "Gold" or "Golden" on Truth Social this week?'),
    ]}
    pfad = tmp_path / "snap.json"
    pfad.write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    nach_id = {r.market_id: r for r in baue_elon_rules()}
    assert nach_id["3093886"].varianten == ["Lindsey", "Graham"]
    assert nach_id["3093887"].varianten == ["Wall Street"]
    assert nach_id["3093888"].varianten == ["President Xi"]
    assert nach_id["3093889"].varianten == ["Gold", "Golden"]
    # Mehrwort-Matching: Leerzeichen/Bindestrich treffen, Teilwort nicht.
    m = ElonMatcher(nach_id["3093888"])
    assert m.pruefe("Just spoke with President Xi about trade")[0] is True
    assert m.pruefe("president-xi meeting")[0] is True
    assert m.pruefe("The President said")[0] is False


def test_trump_profile_nur_post_serie_kein_say_event() -> None:
    # Abgrenzung: "What will Trump SAY"-Maerkte werten NUR Gesprochenes
    # und duerfen nie mit dem Truth-Social-Textbot gehandelt werden.
    # TEXT-Profile (truth_user_id gesetzt) zeigen darum ausschliesslich
    # auf die Post-Serie. Say-Events sind seit 27.07. als eigene
    # AUDIO-Profile erlaubt (trump_michigan_july27, earnings_bot mit
    # ECAPA-Zurechnung und Operator-Marker) — die tragen dann zwingend
    # sprecher_klausel_muster, eine Call-Startzeit und KEINE Text-Quelle.
    from operations.pipeline import config

    for name, p in config.PROFILE.items():
        if not name.startswith("trump"):
            continue
        if p.get("truth_user_id"):
            assert p["event_id"] != "723717"
            assert "trump-say" not in (p.get("event_slug") or "")
            assert "-post-" in (p.get("event_slug") or "")
        else:
            assert p.get("sprecher_klausel_muster")
            assert p.get("call_start_utc")
            assert (p.get("zielsprecher_referenz")
                    or p.get("zielsprecher_referenzen"))
