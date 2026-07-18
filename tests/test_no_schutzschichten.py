"""Tests fuer die drei NO-Schutzschichten (Auftrag 18.07.2026).

1. Boilerplate-Lexikon: Woerter aus dem festen Intro/Outro einer Show
   duerfen nie als NO gekauft werden (E281: "tension" fiel im Outro).
2. Gap-Verify: vom VAD verworfene Audio-Abschnitte werden vor der
   NO-Runde ohne VAD nachtranskribiert; Funde blocken NUR NO.
3. Basisraten: Woerter, die historisch fast jede Woche fallen, werden
   bei Zaehlerstand 0 nicht als NO gekauft (Zaehler-Misstrauen).
"""

from __future__ import annotations

import json

import pytest

from operations.pipeline import config
from operations.pipeline.basisraten import (
    historie_aus_events,
    reichere_mit_basisraten,
    wort_schluessel,
)
from operations.pipeline.counter_engine import Segment, StreamingCounter
from operations.pipeline.decision import entscheide_no, entscheide_yes, no_sperre
from operations.pipeline.gap_verify import finde_luecken, gap_verify
from operations.pipeline.market_rules import build_rule


def gamma_markt(question: str, description: str = "Standard resolution.") -> dict:
    return {
        "id": "111",
        "slug": "test-markt",
        "question": question,
        "description": description,
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(["tok_yes", "tok_no"]),
    }


# ------------------------------------------------- Boilerplate-Lexikon


def test_boilerplate_markiert(monkeypatch) -> None:
    monkeypatch.setattr(config, "BOILERPLATE_BEGRIFFE", frozenset({"tension"}))
    r = build_rule(gamma_markt('Will "Tension" be said during the episode?'))
    assert r.boilerplate_sensitiv
    r2 = build_rule(gamma_markt('Will "Stock" be said during the episode?'))
    assert not r2.boilerplate_sensitiv


def test_boilerplate_or_markt_reicht_ein_begriff(monkeypatch) -> None:
    monkeypatch.setattr(config, "BOILERPLATE_BEGRIFFE", frozenset({"tension"}))
    r = build_rule(gamma_markt('Will "Stress" or "Tension" be said?'))
    assert r.boilerplate_sensitiv


def test_boilerplate_blockt_no_aber_nie_yes(monkeypatch) -> None:
    monkeypatch.setattr(config, "BOILERPLATE_BEGRIFFE", frozenset({"tension"}))
    r = build_rule(gamma_markt('Will "Tension" be said during the episode?'))
    d = entscheide_no(r, 0, 0.44)
    assert d.action == "NONE"
    assert "boilerplate" in d.reason
    # YES bleibt unberuehrt: das Wort faellt ja (Outro) — YES ist korrekt.
    assert entscheide_yes(r, 1, 0.5).action == "YES"


def test_allin_lexikon_enthaelt_belegte_outro_woerter() -> None:
    # Kuratierte Liste aus E280+E281 (YT-Captions + large-v3, 18.07.).
    for wort in ("tension", "orgy", "useless", "winners", "besties",
                 "quinoa", "driveway"):
        assert wort in config.ALLIN_BOILERPLATE
    # und die All-In-Profile tragen Lexikon + Serie
    p = config.PROFILE["allin_july17"]
    assert p["serie_id"] == "11300"
    assert "tension" in p["boilerplate_begriffe"]


# ------------------------------------------------- Basisraten-Veto


def _events_mit(kurz_und_erg: list[tuple[str, str | None]]) -> list[dict]:
    """Fake-Serien-Events: je (wort-kurz, 'YES'/'NO'/None=offen) ein Event."""
    out = []
    for kurz, erg in kurz_und_erg:
        preise = {"YES": ["1", "0"], "NO": ["0", "1"], None: ["0.4", "0.6"]}[erg]
        out.append({"markets": [{
            "slug": f"will-{kurz}-be-said-during-the-next-episode-x",
            "outcomePrices": json.dumps(preise),
        }]})
    return out


def test_wort_schluessel_normalisiert_slug() -> None:
    assert wort_schluessel(
        "will-tension-be-said-during-the-next-episode-of-the-all-in-"
        "podcast-20260713144020212") == "tension"
    assert wort_schluessel(
        "will-midterm-or-midterms-be-said-during-x") == "midterm-or-midterms"


def test_historie_zaehlt_nur_aufgeloeste() -> None:
    h = historie_aus_events(_events_mit(
        [("anthropic", "YES"), ("anthropic", "YES"), ("anthropic", None),
         ("alignment", "NO")]))
    assert h["anthropic"] == ["YES", "YES"]
    assert h["alignment"] == ["NO"]


def test_basisrate_veto_blockt_dauerbrenner(monkeypatch) -> None:
    monkeypatch.setattr(config, "BASISRATE_VETO", 0.8)
    monkeypatch.setattr(config, "BASISRATE_MIN_N", 4)
    r = build_rule(gamma_markt('Will "Anthropic" be said during the episode?'))
    r.slug = "will-anthropic-be-said-during-the-next-episode-x"
    historie = {"anthropic": ["YES"] * 5}
    reichere_mit_basisraten([r], historie)
    assert r.basisrate == 1.0
    assert r.basis_n == 5
    d = entscheide_no(r, 0, 0.44)
    assert d.action == "NONE"
    assert "basisrate" in d.reason
    # YES unberuehrt
    assert entscheide_yes(r, 1, 0.5).action == "YES"


def test_basisrate_kein_veto_bei_wenig_historie_oder_niedriger_rate(
        monkeypatch) -> None:
    monkeypatch.setattr(config, "BASISRATE_VETO", 0.8)
    monkeypatch.setattr(config, "BASISRATE_MIN_N", 4)
    r = build_rule(gamma_markt('Will "Alignment" be said during the episode?'))
    r.slug = "will-alignment-be-said-during-x"
    # Fall 1: hohe Rate, aber nur 3 Wochen -> kein Veto
    reichere_mit_basisraten([r], {"alignment": ["YES"] * 3})
    assert no_sperre(r) is None
    # Fall 2: viel Historie, niedrige Rate (2/13) -> kein Veto
    reichere_mit_basisraten([r], {"alignment": ["YES"] * 2 + ["NO"] * 11})
    assert r.basis_n == 13
    assert no_sperre(r) is None
    assert entscheide_no(r, 0, 0.44).action == "NO"


def test_ohne_historie_alles_unveraendert() -> None:
    r = build_rule(gamma_markt('Will "Neuwort" be said during the episode?'))
    assert r.basisrate is None
    assert no_sperre(r) is None
    assert entscheide_no(r, 0, 0.44).action == "NO"


# ------------------------------------------------- Gap-Verify


def test_finde_luecken_merge_schwelle_und_raender() -> None:
    # Ueberlappende Abdeckung wird gemerged; Kopf- und Schwanzluecke zaehlen.
    luecken = finde_luecken([(50.0, 100.0), (90.0, 200.0)], 400.0, 15.0)
    assert luecken == [(0.0, 50.0), (200.0, 400.0)]
    # Kleine Luecken unter der Schwelle werden ignoriert.
    assert finde_luecken([(0.0, 100.0), (110.0, 200.0)], 200.0, 15.0) == []
    assert finde_luecken([], 100.0, 15.0) == [(0.0, 100.0)]


def test_finde_luecken_tension_szenario() -> None:
    # E281: Transkript endet 5330.77s, Audio 5394.14s -> Schwanzluecke.
    luecken = finde_luecken([(0.0, 5330.77)], 5394.14, 15.0)
    assert luecken == [(5330.77, 5394.14)]


def test_ingest_nur_erweitert_zaehlt_nicht_fuer_yes() -> None:
    r = build_rule(gamma_markt('Will "Tension" be said during the episode?'))
    c = StreamingCounter(r)
    delta = c.ingest_nur_erweitert(
        [Segment("sexual tension that they just need to release",
                 confidence=0.4)])
    assert delta == 1
    assert c.erweitert_count == 1
    assert c.count == 0
    assert c.ziel_count == 0


def test_gap_verify_funde_blocken_no(monkeypatch) -> None:
    r = build_rule(gamma_markt('Will "Tension" be said during the episode?'))
    r2 = build_rule(gamma_markt('Will "Stock" be said during the episode?'))
    r2.market_id = "222"
    counters = {r.market_id: StreamingCounter(r),
                "222": StreamingCounter(r2)}
    aufrufe: list[tuple[float, float]] = []

    def fake_transkribiere(audio, luecken):
        aufrufe.extend(luecken)
        return [Segment("it's like this sexual tension somehow", 0.4,
                        start_s=5366.0, end_s=5371.0)]

    bericht = gap_verify(None, [(0.0, 5330.0)], 5394.0, counters,
                         transkribiere_fn=fake_transkribiere)
    assert aufrufe == [(5330.0, 5394.0)]
    assert bericht["deltas"] == {"test-markt": 1}
    assert counters[r.market_id].erweitert_count == 1
    assert entscheide_no(r, counters[r.market_id].erweitert_count,
                         0.44).action == "NONE"
    # Unbeteiligter Markt bleibt kaufbar.
    assert entscheide_no(r2, counters["222"].erweitert_count,
                         0.44).action == "NO"


def test_gap_verify_ohne_luecken_laedt_kein_modell() -> None:
    def explodiert(audio, luecken):  # pragma: no cover - darf nie laufen
        raise AssertionError("transkribiere_fn darf nicht gerufen werden")

    bericht = gap_verify(None, [(0.0, 100.0)], 100.0, {},
                         transkribiere_fn=explodiert)
    assert bericht["luecken"] == []
    assert bericht["deltas"] == {}


# ------------------------------------------------- Zusammenspiel


def test_no_sperre_grund_prioritaet(monkeypatch) -> None:
    monkeypatch.setattr(config, "BOILERPLATE_BEGRIFFE", frozenset({"tension"}))
    r = build_rule(gamma_markt('Will "Tension" be said during the episode?'))
    r.basisrate, r.basis_n = 1.0, 10
    grund = no_sperre(r)
    assert grund is not None and "boilerplate" in grund
    d = entscheide_no(r, 0, 0.3)
    assert d.action == "NONE"
    assert pytest.approx(0.3) != d.limit_price  # kein Preis gesetzt
