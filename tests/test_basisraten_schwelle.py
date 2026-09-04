"""Basisraten-Schluessel: Wort PLUS Schwelle (Befund 04.09.2026).

Bracket-Maerkte derselben Serie fuehren dasselbe Wort mit verschiedenen
Schwellen (All-In: "AI" 35+ und 50+; JRE: "People" 100+ und 200+). Der
Slug traegt die Schwelle hinter "-be-said-" ("will-ai-be-said-50-times-
during-..."); `wort_schluessel` schnitt sie ab, und die Historie fuer das
NO-Veto (decision.no_sperre) mischte damit Ereignisse verschiedener
Schwellen — Live-Snapshot allin_september4: "ai" n=17 = 35+, 50+, 45+,
15+, 20+, 5+ zusammen; das Analyse-Modul (PR #63) weist sie getrennt aus.
"""

from __future__ import annotations

import json

import httpx
import pytest

from operations.pipeline import config
from operations.pipeline.basisraten import (
    SNAPSHOT_SCHEMA,
    basis_schluessel,
    historie_aus_events,
    hole_serien_historie,
    reichere_mit_basisraten,
    wort_schluessel,
)
from operations.pipeline.decision import entscheide_no, no_sperre
from operations.pipeline.market_rules import build_rule

ALLIN = "during-the-next-episode-of-the-all-in-podcast"
JRE = "during-the-first-joe-rogan-experience-of-the-week-of"


def _markt(slug: str, question: str, erg: str | None) -> dict:
    """Gamma-Markt-Fixture; erg 'YES'/'NO'/None (offen)."""
    preise = {"YES": ["1", "0"], "NO": ["0", "1"], None: ["0.4", "0.6"]}[erg]
    return {"slug": slug, "question": question,
            "outcomePrices": json.dumps(preise)}


def _allin_ai(schwelle: int, woche: str, erg: str | None) -> dict:
    return _markt(
        f"will-ai-be-said-{schwelle}-times-{ALLIN}-{woche}",
        f'Will "AI" be said {schwelle}+ times during the next episode '
        "of the All-In Podcast?", erg)


def _jre_people(schwelle: int, woche: str, erg: str | None) -> dict:
    return _markt(
        f"will-people-be-said-{schwelle}-times-{JRE}-{woche}",
        f'Will "People" be said {schwelle}+ times during the first Joe '
        "Rogan Experience of the week of July 6?", erg)


def _regel(slug: str, question: str):
    return build_rule({
        "id": "1", "slug": slug, "question": question,
        "description": "Standard resolution.",
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(["tok_yes", "tok_no"]),
    })


# ------------------------------------------------- Reproduktion (Befund)


def test_zwei_schwellen_desselben_worts_bleiben_getrennt() -> None:
    # AI 35+ fiel in drei Wochen, AI 50+ in einer von drei — verschiedene
    # Ereignisse, die nicht unter "ai" zusammenlaufen duerfen.
    events = [{"markets": [_allin_ai(35, f"2026070{i}", "YES")]}
              for i in range(1, 4)]
    events += [{"markets": [_allin_ai(50, f"2026080{i}", erg)]}
               for i, erg in enumerate(("YES", "NO", "NO"), 1)]
    h = historie_aus_events(events)
    assert h["ai-35-times"] == ["YES", "YES", "YES"]
    assert h["ai-50-times"] == ["YES", "NO", "NO"]
    assert "ai" not in h


def test_veto_nutzt_nur_die_historie_der_eigenen_schwelle(monkeypatch) -> None:
    # JRE-Muster (Analyse 04.09.: People 100+ 16/18, People 200+ 5/13):
    # gemischt laege "people" unter dem Veto, obwohl 100+ ein Dauerbrenner
    # ist — und 200+ eine echte NO-Wette bleibt.
    monkeypatch.setattr(config, "BASISRATE_VETO", 0.8)
    monkeypatch.setattr(config, "BASISRATE_MIN_N", 4)
    events = [{"markets": [_jre_people(100, f"2026060{i}", "YES"),
                           _jre_people(200, f"2026060{i}", "NO")]}
              for i in range(1, 5)]
    events.append({"markets": [_jre_people(100, "20260605", "YES"),
                               _jre_people(200, "20260605", "YES")]})
    r100 = _regel(f"will-people-be-said-100-times-{JRE}-20260706",
                  'Will "People" be said 100+ times during the first Joe '
                  "Rogan Experience of the week of July 6?")
    r200 = _regel(f"will-people-be-said-200-times-{JRE}-20260706",
                  'Will "People" be said 200+ times during the first Joe '
                  "Rogan Experience of the week of July 6?")
    reichere_mit_basisraten([r100, r200], historie_aus_events(events))
    assert (r100.basis_n, r100.basisrate) == (5, 1.0)
    assert (r200.basis_n, r200.basisrate) == (5, 0.2)
    sperre = no_sperre(r100)
    assert sperre is not None and "basisrate_veto" in sperre
    assert no_sperre(r200) is None
    assert entscheide_no(r200, 0, 0.44).action == "NO"


# ------------------------------------------------- Schluessel-Form


def test_basis_schluessel_ohne_schwelle_bleibt_das_wort() -> None:
    # Rueckwaertskompatibel: Slugs ohne Schwelle behalten den v1-Schluessel.
    assert basis_schluessel(
        f"will-anthropic-be-said-{ALLIN}-20260831",
        'Will "Anthropic" be said during the next episode of the All-In '
        "Podcast?") == "anthropic"
    assert basis_schluessel(
        f"will-stock-market-be-said-{ALLIN}-20260831") == "stock-market"
    assert basis_schluessel(
        "will-trump-post-gold-or-golden-on-truth-social-this-week-"
        "20260710155725225") == "gold-or-golden"


def test_basis_schluessel_mit_schwelle_be_said_schema() -> None:
    assert basis_schluessel(
        f"will-ai-be-said-50-times-{ALLIN}-20260831",
        'Will "AI" be said 50+ times during the next episode of the All-In '
        "Podcast?") == "ai-50-times"
    assert basis_schluessel(
        f"will-hundred-or-thousand-or-million-be-said-10-times-{ALLIN}-"
        "20260831") == "hundred-or-thousand-or-million-10-times"


def test_basis_schluessel_say_schema_unveraendert_zu_v1() -> None:
    # MrBeast/Earnings tragen die Schwelle IM Wort-Teil des Slugs; der
    # Basis-Schluessel bleibt dort wie bisher, das reine Wort ist neu.
    slug = ("will-mrbeast-say-hundred-or-thousand-or-million-10-times-during-"
            "his-next-gaming-youtube-video-20260604155409590")
    assert basis_schluessel(slug) == "hundred-or-thousand-or-million-10-times"
    assert wort_schluessel(slug) == "hundred-or-thousand-or-million"
    assert basis_schluessel(
        "will-american-express-say-income-10-times-during-earnings-call-"
        "20260717164416059",
        'Will American Express say "Income" 10+ times during earnings call?'
    ) == "income-10-times"


def test_schwelle_aus_fragetext_vor_slug_und_slug_als_fallback() -> None:
    # Fragetext ist die Quelle (wie build_rule); ohne Fragetext der Slug.
    slug = f"will-ai-be-said-50-times-{ALLIN}-20260831"
    assert basis_schluessel(slug, None) == "ai-50-times"
    assert basis_schluessel(slug, "") == "ai-50-times"
    assert basis_schluessel(
        slug, 'Will "AI" be said 40+ times during the episode?') == "ai-40-times"


# ------------------------------------------------- Fail-safe


def test_ohne_passende_historie_bleibt_alles_unveraendert() -> None:
    r = _regel(f"will-ai-be-said-50-times-{ALLIN}-20260831",
               'Will "AI" be said 50+ times during the next episode of the '
               "All-In Podcast?")
    reichere_mit_basisraten([r], {})
    assert (r.basisrate, r.basis_n) == (None, 0)
    assert no_sperre(r) is None
    assert entscheide_no(r, 0, 0.44).action == "NO"


def test_v1_historie_ohne_schwelle_liefert_kein_veto_fuer_bracket() -> None:
    # Ein alter Schluessel ("ai" = alle Brackets gemischt) darf eine
    # Bracket-Regel nicht anreichern: lieber keine Basisrate als eine
    # gemischte — fail-safe in Richtung "kein Veto".
    r = _regel(f"will-ai-be-said-50-times-{ALLIN}-20260831",
               'Will "AI" be said 50+ times during the next episode of the '
               "All-In Podcast?")
    reichere_mit_basisraten([r], {"ai": ["YES"] * 17})
    assert (r.basisrate, r.basis_n) == (None, 0)
    assert no_sperre(r) is None


def test_skip_regel_wird_angereichert_ohne_zu_brechen() -> None:
    r = _regel("will-no-episode-air-20260831", "Will no episode air?")
    assert r.status == "skip" and r.schwelle == 0
    reichere_mit_basisraten([r], {"no-episode-air-20260831": ["NO"]})
    assert (r.basis_n, r.basisrate) == (1, 0.0)
    assert no_sperre(r) is None


# ------------------------------------------------- Snapshot-Schema


def test_snapshot_traegt_schema_und_schwellen_schluessel(
        tmp_path, monkeypatch) -> None:
    events = [{"markets": [_allin_ai(35, "20260701", "YES"),
                           _allin_ai(50, "20260701", "NO")]}]

    class _Antwort:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[dict]:
            return events

    aufrufe: list[dict] = []

    def fake_get(url, params=None, headers=None, timeout=None):
        aufrufe.append(params)
        return _Antwort()

    monkeypatch.setattr(httpx, "get", fake_get)
    pfad = tmp_path / "basisraten_snapshot.json"
    historie = hole_serien_historie("11300", snapshot_pfad=pfad)
    assert historie == {"ai-35-times": ["YES"], "ai-50-times": ["NO"]}
    snap = json.loads(pfad.read_text(encoding="utf-8"))
    assert snap["schema"] == SNAPSHOT_SCHEMA == 2
    assert snap["serie_id"] == "11300"
    assert snap["events"] == 1
    assert snap["historie"] == historie
    assert aufrufe == [{"series_id": "11300", "limit": 100, "offset": 0}]


@pytest.mark.parametrize("slug, erwartet", [
    (f"will-ai-be-said-50-times-{ALLIN}-20260831", "ai"),
    (f"will-people-be-said-200-times-{JRE}-20260706", "people"),
    (f"will-ipo-be-said-{ALLIN}-20260831", "ipo"),
])
def test_wort_schluessel_ist_das_reine_wort(slug: str, erwartet: str) -> None:
    assert wort_schluessel(slug) == erwartet
