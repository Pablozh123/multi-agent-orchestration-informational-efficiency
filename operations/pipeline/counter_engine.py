"""Zaehler-Engine: Wortvarianten in Transkript-Segmenten zaehlen.

Case-insensitive, mit Wortgrenzen, optional Plural/Possessiv. Homophon-
anfaellige Begriffe werden im strikten Zaehler (YES) nur gezaehlt, wenn
die ASR-Konfidenz des Segments oberhalb der Schwelle liegt; im
erweiterten Zaehler (NO-Absicherung) zaehlen sie unabhaengig von der
Konfidenz mit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from operations.pipeline import config
from operations.pipeline.market_rules import MarketRule


@dataclass
class Segment:
    text: str
    confidence: float
    start_s: float = 0.0
    end_s: float = 0.0
    # None = keine Sprecher-Verifikation aktiv; True/False = Zurechnung
    # zum Zielsprecher (z.B. MrBeast) durch SpeakerVerifier.
    ist_ziel: bool | None = None


@dataclass
class ChunkLog:
    chunk_index: int
    wall_ts_utc: str
    count_total: int
    delta: int
    uebersprungen_homophon: int
    ziel_count_total: int = 0
    # Strikte Treffer plus Komposita-Verdacht (siehe unten). Nur fuer die
    # NO-Absicherung gedacht, nie fuer YES.
    erweitert_count_total: int = 0


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


def compile_verdacht_patterns(varianten: list[str]) -> list[re.Pattern]:
    """Substring-Patterns fuer Komposita-Verdacht (Event-Mentions-PDF:
    geschlossene Komposita wie "wildfire" zaehlen fuer "fire").

    Die strikten Wortgrenzen-Patterns sehen solche Treffer nicht (ASR
    schreibt "evergreen" als ein Token). Substring-Matching kann echte
    Komposita nicht von Ableitungen trennen ("trumpet" enthaelt "trump"),
    darum fliessen diese Treffer NUR konservativ in die NO-Entscheidung
    ein: kein NO-Kauf, wenn schon die grosszuegigste Lesart die Schwelle
    reissen koennte. Nur Ein-Wort-Varianten ab 4 Buchstaben — bei kurzen
    Woertern dominiert Substring-Muell ("red" in "hundred").
    """
    patterns = []
    for variante in varianten:
        v = variante.strip()
        if len(v) < 4 or not v.isalpha():
            continue
        patterns.append(re.compile(re.escape(v), re.IGNORECASE))
    return patterns


def count_in_text(text: str, patterns: list[re.Pattern]) -> int:
    """Gesamtzahl der Treffer aller Varianten-Patterns im Text."""
    return sum(len(p.findall(text)) for p in patterns)


class StreamingCounter:
    """Laufender Zaehler je Markt ueber eintreffende Chunk-Segmente."""

    def __init__(self, rule: MarketRule) -> None:
        self.rule = rule
        self.patterns = compile_patterns(rule.varianten)
        # Fuer den Komposita-Verdacht braucht es das strikte Gegenstueck
        # derselben Varianten-Teilmenge, sonst wuerde jeder normale Treffer
        # doppelt in den erweiterten Zaehler laufen.
        self._verdacht_varianten = [
            v.strip() for v in rule.varianten
            if len(v.strip()) >= 4 and v.strip().isalpha()
        ]
        self.verdacht_patterns = compile_verdacht_patterns(rule.varianten)
        self._strikt_fuer_verdacht = compile_patterns(self._verdacht_varianten)
        self.count = 0       # alle Stimmen, strikte Regeln
        self.ziel_count = 0  # nur Zielsprecher (== count ohne Verifikation)
        self.erweitert_count = 0  # strikt + Komposita-Verdacht (nur fuer NO)
        self.logs: list[ChunkLog] = []

    def _zaehle_segment(self, seg: Segment) -> tuple[int, int, bool]:
        """(strikte Treffer, Nur-erweitert-Treffer); bool = Homophon-Skip.

        Nur-erweitert-Treffer fliessen ausschliesslich in erweitert_count:
        regulaer der Komposita-Verdacht; bei Homophon-Skip zusaetzlich die
        strikten Treffer selbst. Ein Niedrig-Konfidenz-Treffer ist fuer
        YES zu unsicher (Homophon-Gefahr), fuer die NO-Absicherung zaehlt
        er konservativ MIT — das Wort koennte gefallen sein (Review 18.07.,
        vorher fiel er aus allen Zaehlern und NO blieb kaufbar).
        """
        strikt = count_in_text(seg.text, self.patterns)
        extra = 0
        if self.verdacht_patterns:
            substring = count_in_text(seg.text, self.verdacht_patterns)
            strikt_teilmenge = count_in_text(seg.text, self._strikt_fuer_verdacht)
            extra = max(0, substring - strikt_teilmenge)
        if (
            self.rule.homophon_sensitiv
            and seg.confidence <= config.ASR_KONFIDENZ_HOMOPHON
        ):
            return 0, strikt + extra, strikt > 0
        return strikt, extra, False

    def ingest_nur_erweitert(self, segmente: list[Segment]) -> int:
        """Zaehlt Segmente NUR in den erweiterten Zaehler (NO-Absicherung).

        Fuer Gap-Verify-Funde: Nachtranskription ohne VAD kann in Musik
        halluzinieren — ein halluziniertes Wort darf deshalb nie YES
        ausloesen, nur eine NO-Chance kosten. Konfidenz-Gates gelten hier
        nicht (der erweiterte Zaehler zaehlt jeden moeglichen Treffer).
        Liefert das Delta.
        """
        delta = 0
        for seg in segmente:
            delta += count_in_text(seg.text, self.patterns)
            if self.verdacht_patterns:
                substring = count_in_text(seg.text, self.verdacht_patterns)
                strikt = count_in_text(seg.text, self._strikt_fuer_verdacht)
                delta += max(0, substring - strikt)
        self.erweitert_count += delta
        return delta

    def ingest_chunk(
        self, chunk_index: int, segmente: list[Segment], wall_ts_utc: str
    ) -> ChunkLog:
        delta = 0
        ziel_delta = 0
        extra_delta = 0
        uebersprungen = 0
        for seg in segmente:
            treffer, extra, skip = self._zaehle_segment(seg)
            delta += treffer
            extra_delta += extra
            # ist_ziel None = Verifikation inaktiv -> Zielzaehler folgt Gesamt.
            if seg.ist_ziel is None or seg.ist_ziel:
                ziel_delta += treffer
            if skip:
                uebersprungen += 1
        self.count += delta
        self.ziel_count += ziel_delta
        self.erweitert_count += delta + extra_delta
        log = ChunkLog(
            chunk_index=chunk_index,
            wall_ts_utc=wall_ts_utc,
            count_total=self.count,
            delta=delta,
            uebersprungen_homophon=uebersprungen,
            ziel_count_total=self.ziel_count,
            erweitert_count_total=self.erweitert_count,
        )
        self.logs.append(log)
        return log
