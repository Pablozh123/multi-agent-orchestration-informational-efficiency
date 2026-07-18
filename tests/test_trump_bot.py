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
