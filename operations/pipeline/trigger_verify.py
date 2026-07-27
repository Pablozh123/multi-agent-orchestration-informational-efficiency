"""Trigger-Verifikation: YES-Kaeufe erst nach Bestaetigung durchs grosse Modell.

Der AXP-Lauf (24.07.) kaufte zweimal auf einen einzelnen small-Treffer
gegen einen zweifelnden Markt (Luxury @0.56, Fraud @0.52). Beide waren
richtig — aber ein einziger Hoerfehler (E281-Homophon-Klasse) haette den
vollen Einsatz gekostet. Darum wird der ausloesende Audio-Abschnitt vor
JEDEM Kauf mit TRIGGER_VERIFY_MODELL (Default: GAP_MODELL, large-v3)
ohne VAD nachtranskribiert und mit den strikten Wortgrenzen-Patterns
nachgezaehlt.

Fail-closed: keine Bestaetigung -> kein Kauf. Ein verpasster YES kostet
0, ein Falschkauf alles — dieselbe Asymmetrie wie beim NO-Deckel.

Das Modell wird beim Start EINMAL geladen und warm gehalten; die
Nachpruefung eines ~20-s-Fensters kostet damit ~1-3 s auf der GPU.
Fuer den Aufmerksamkeits-Kanal (mittelpreisige, von der Crowd nicht
mitgehoerte Woerter — Luxury stand minutenlang bei 0.56) ist das
irrelevant, und die Sekundenrennen der heissen Woerter sind laut
Messung (4-s-Repricing) ohnehin verloren.
"""

from __future__ import annotations

import time
from typing import Callable

from operations.pipeline import config
from operations.pipeline.counter_engine import compile_patterns, count_in_text
from operations.pipeline.market_rules import MarketRule

SAMPLE_RATE = 16_000
#: Fenster-Rand in Sekunden (wie GAP_RAND_S): faengt Woerter an der
#: Chunk-Grenze und ASR-Zeitstempel-Ungenauigkeit ab.
RAND_S = 5.0


class TriggerVerifikation:
    """Haelt das grosse Modell warm und prueft Trigger-Fenster nach."""

    def __init__(
        self,
        modell: str | None = None,
        transkribiere_fn: Callable | None = None,
    ) -> None:
        self.modell_name = str(modell or config.TRIGGER_VERIFY_MODELL)
        self.geraet = "injiziert"
        if transkribiere_fn is not None:
            # Testpfad: (audio_ausschnitt) -> str
            self._transkribiere = transkribiere_fn
            return
        from faster_whisper import WhisperModel

        from operations.pipeline.transcription import _cuda_dlls_einbinden

        _cuda_dlls_einbinden()
        try:
            self._model = WhisperModel(
                self.modell_name, device="cuda", compute_type="float16")
            self.geraet = "cuda/float16"
        except Exception:  # noqa: BLE001 - CPU-Fallback wie Haupt-Transcriber
            self._model = WhisperModel(
                self.modell_name, device="cpu", compute_type="int8")
            self.geraet = "cpu/int8"
        self._transkribiere = self._modell_transkribiere

    def _modell_transkribiere(self, ausschnitt) -> str:
        segs, _ = self._model.transcribe(
            ausschnitt, language="en", beam_size=1,
            vad_filter=False, word_timestamps=False,
        )
        return " ".join(s.text for s in segs).strip()

    def pruefe(
        self,
        rule: MarketRule,
        audio,
        fenster: tuple[float, float] | None,
    ) -> dict:
        """Zaehlt die Varianten der Rule im Fenster mit dem grossen Modell.

        ``audio`` ist das dekodierte Gesamtaudio (16 kHz mono), ``fenster``
        das (start_s, ende_s) der ausloesenden Segmente; None nimmt die
        letzten CHUNK_SEKUNDEN + 2*RAND_S (Fallback ohne Zeitstempel).
        """
        t0 = time.time()
        gesamt_s = len(audio) / SAMPLE_RATE
        if fenster is None:
            ende = gesamt_s
            start = max(0.0, ende - (config.CHUNK_SEKUNDEN + 2 * RAND_S))
        else:
            start = max(0.0, min(fenster) - RAND_S)
            ende = min(gesamt_s, max(fenster) + RAND_S)
        ausschnitt = audio[int(start * SAMPLE_RATE):int(ende * SAMPLE_RATE)]
        if len(ausschnitt) < SAMPLE_RATE // 2:
            return {
                "bestaetigt": False, "treffer": 0, "text": "",
                "fenster_s": [round(start, 1), round(ende, 1)],
                "grund": "fenster_leer", "modell": self.modell_name,
                "dauer_s": round(time.time() - t0, 2),
            }
        text = self._transkribiere(ausschnitt)
        treffer = count_in_text(text, compile_patterns(rule.varianten))
        return {
            "bestaetigt": treffer > 0,
            "treffer": treffer,
            "text": text[:200],
            "fenster_s": [round(start, 1), round(ende, 1)],
            "modell": self.modell_name,
            "dauer_s": round(time.time() - t0, 2),
        }
