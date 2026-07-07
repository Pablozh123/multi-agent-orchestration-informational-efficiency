"""Zaehler-Engine: Wortvarianten in Transkript-Segmenten zaehlen.

Case-insensitive, mit Wortgrenzen, optional Plural/Possessiv. Homophon-
anfaellige Begriffe werden nur gezaehlt, wenn die ASR-Konfidenz des
Segments oberhalb der Schwelle liegt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule


@dataclass
class Segment:
    text: str
    confidence: float
    start_s: float = 0.0
    end_s: float = 0.0


@dataclass
class ChunkLog:
    chunk_index: int
    wall_ts_utc: str
    count_total: int
    delta: int
    uebersprungen_homophon: int


def compile_patterns(varianten: list[str]) -> list[re.Pattern]:
    """Ein Regex je Variante: Wortgrenzen plus optional Possessiv/Plural.

    Fuer Varianten mit Punkten (A.I.) oder Leerzeichen (artificial
    intelligence) werden Nicht-Buchstaben-Grenzen statt \\b genutzt und
    interne Leerzeichen flexibel gematcht.
    """
    patterns = []
    for variante in varianten:
        kern = re.escape(variante.strip())
        kern = kern.replace(r"\ ", r"\s+")  # flexible interne Leerzeichen
        # Possessiv/Plural am Wortende (nur diese Formen zaehlen laut Regeln)
        suffix = r"(?:['’]s|s|['’])?"
        muster = rf"(?<![A-Za-z]){kern}{suffix}(?![A-Za-z])"
        patterns.append(re.compile(muster, re.IGNORECASE))
    return patterns


def count_in_text(text: str, patterns: list[re.Pattern]) -> int:
    """Gesamtzahl der Treffer aller Varianten-Patterns im Text."""
    return sum(len(p.findall(text)) for p in patterns)


class StreamingCounter:
    """Laufender Zaehler je Markt ueber eintreffende Chunk-Segmente."""

    def __init__(self, rule: MarketRule) -> None:
        self.rule = rule
        self.patterns = compile_patterns(rule.varianten)
        self.count = 0
        self.logs: list[ChunkLog] = []

    def _zaehle_segment(self, seg: Segment) -> tuple[int, bool]:
        """Treffer eines Segments; bool = wegen Homophon uebersprungen."""
        if (
            self.rule.homophon_sensitiv
            and seg.confidence <= config.ASR_KONFIDENZ_HOMOPHON
        ):
            treffer = count_in_text(seg.text, self.patterns)
            if treffer:
                return 0, True
            return 0, False
        return count_in_text(seg.text, self.patterns), False

    def ingest_chunk(
        self, chunk_index: int, segmente: list[Segment], wall_ts_utc: str
    ) -> ChunkLog:
        delta = 0
        uebersprungen = 0
        for seg in segmente:
            treffer, skip = self._zaehle_segment(seg)
            delta += treffer
            if skip:
                uebersprungen += 1
        self.count += delta
        log = ChunkLog(
            chunk_index=chunk_index,
            wall_ts_utc=wall_ts_utc,
            count_total=self.count,
            delta=delta,
            uebersprungen_homophon=uebersprungen,
        )
        self.logs.append(log)
        return log
