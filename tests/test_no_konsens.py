"""Tests fuer den NO-Konsens-Vollpass (Auftrag 25.07.2026, E282-Lehre).

Zweiter NO-Verlust durch einen small-Verhoerer: "innovation" fiel in
E282 genau einmal, bei 3470.2s im Crosstalk. small transkribierte
"Master virtue signaling", der Zaehler blieb 0, die NO @0.13 verlor
20.86 USD — large-v3 hoert das Wort (Forensik E281+E282). Diese
Verhoerer-Klasse liegt INNERHALB abgedeckter Fenster; Gap-Verify
(VAD-Loecher, E281 "tension") sieht sie per Konstruktion nicht.

Der Vollpass hoert die ganze Episode vor der NO-Runde noch einmal mit
NO_KONSENS_MODELL (large-v3, batched). Funde fliessen ausschliesslich
ueber StreamingCounter.ingest_nur_erweitert in den erweiterten Zaehler:
sie blocken NO, loesen nie YES aus (Konsens-Asymmetrie wie Gap-Verify).
"""

from __future__ import annotations

import json

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter
from operations.pipeline.decision import entscheide_no, entscheide_yes
from operations.pipeline.market_rules import build_rule
from operations.pipeline.no_konsens import no_konsens_pass


def gamma_markt(question: str, market_id: str = "111") -> dict:
    return {
        "id": market_id,
        "slug": f"test-markt-{market_id}",
        "question": question,
        "description": "Standard resolution.",
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps(["tok_yes", "tok_no"]),
    }


def test_e282_verhoerer_blockt_no_aber_nie_yes() -> None:
    # E282-Szenario: der Streaming-Zaehler (small) verhoerte das Wort im
    # Crosstalk — Endstand 0, die NO waere kaufbar gewesen. Der Vollpass
    # (large-v3) hoert es und blockt die NO; YES bleibt unberuehrt.
    r = build_rule(gamma_markt(
        'Will "Innovation" be said during the next episode?'))
    c = StreamingCounter(r)
    c.ingest_chunk(1, [Segment("Master virtue signaling", confidence=0.6,
                               start_s=3468.0, end_s=3472.4)], "t0")
    assert c.count == 0
    assert c.erweitert_count == 0

    def large_v3(audio):
        assert audio == "AUDIO"
        return [Segment("the pace of innovation is incredible",
                        confidence=0.9, start_s=3468.9, end_s=3474.1)]

    bericht = no_konsens_pass("AUDIO", {r.market_id: c},
                              transkribiere_fn=large_v3)
    assert bericht["deltas"] == {r.slug: 1}
    assert c.erweitert_count == 1
    # NO geblockt: erweiterter Endstand 1 > 70% der Schwelle 1.
    assert entscheide_no(r, c.erweitert_count, 0.44).action == "NONE"
    # YES nie aus dem Vollpass: strikter und Ziel-Zaehler unveraendert.
    assert c.count == 0
    assert c.ziel_count == 0
    assert entscheide_yes(r, c.ziel_count, 0.5).action == "NONE"


def test_unbeteiligter_markt_bleibt_no_kaufbar() -> None:
    r1 = build_rule(gamma_markt('Will "Innovation" be said?', "111"))
    r2 = build_rule(gamma_markt('Will "Stock" be said?', "222"))
    counters = {r1.market_id: StreamingCounter(r1),
                r2.market_id: StreamingCounter(r2)}

    bericht = no_konsens_pass(None, counters, transkribiere_fn=lambda a: [
        Segment("innovation everywhere, twice: innovation", confidence=0.9),
    ])
    assert bericht["deltas"] == {r1.slug: 2}
    assert counters["111"].erweitert_count == 2
    assert counters["222"].erweitert_count == 0
    assert entscheide_no(r2, counters["222"].erweitert_count,
                         0.44).action == "NO"


def test_bericht_traegt_modell_dauer_und_segmente() -> None:
    # Event "no_konsens" soll Dauer + Deltas loggen (Auftrag 25.07.).
    bericht = no_konsens_pass(None, {}, transkribiere_fn=lambda a: [])
    assert bericht["modell"] == config.NO_KONSENS_MODELL
    assert bericht["dauer_s"] >= 0.0
    assert bericht["segmente"] == 0
    assert bericht["deltas"] == {}


def test_config_default_aktiv_und_modell_folgt_gap_modell() -> None:
    # Default aktiv: bot.py laeuft nur fuer Audio-Profile (Elon/Trump-
    # Textbots erreichen den Pfad nie). Modell folgt GAP_MODELL —
    # small ist als alleinige NO-Grundlage widerlegt (E281+E282).
    assert config.NO_KONSENS_AKTIV is True
    assert config.NO_KONSENS_MODELL == config.GAP_MODELL == "large-v3"
