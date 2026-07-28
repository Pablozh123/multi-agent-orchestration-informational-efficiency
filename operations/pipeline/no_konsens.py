"""NO-Konsens-Vollpass: die Episode vor der NO-Runde mit large-v3 hoeren.

Der Streaming-Zaehler hoert mit small — schnell genug fuer Live-YES,
aber verhoerbar im Crosstalk. E282-Beleg (24.07.): "innovation" fiel
genau einmal, bei 3470.2s; small transkribierte "Master virtue
signaling", der Zaehler blieb 0, die NO @0.13 verlor 20.86 USD —
large-v3 hoert das Wort (Forensik E281+E282). Diese Verhoerer-Klasse
liegt INNERHALB abgedeckter Fenster; Gap-Verify (VAD-Loecher, E281
"tension") sieht sie per Konstruktion nicht.

Darum vor der NO-Runde ein zweites Gehoer: die GANZE Episode einmal mit
NO_KONSENS_MODELL (large-v3) batched nachtranskribieren. Funde fliessen
ausschliesslich in den erweiterten Zaehler
(StreamingCounter.ingest_nur_erweitert): sie blocken NO, loesen nie
YES aus — dieselbe Konsens-Asymmetrie wie beim Gap-Verify. Ein
large-v3-Fehlhoerer kostet so hoechstens eine NO-Chance, nie Geld.

Der batched-Pass segmentiert ueber VAD und endet daher wie der
Streaming-Pass vor musikunterlegten Outros — die VAD-Loch-Klasse bleibt
Domaene des Gap-Verify, der danach unveraendert laeuft.

Kosten: ~170s je 90-Min-Episode auf der RTX 3060 (batched, gemessen an
der E281+E282-Forensik). Vertretbar, weil NO-Asks nach dem Drop stabil
stehen (E280: 30+ Min unveraendert; E281/E282: Nachlauf-Buchlogs).
"""

from __future__ import annotations

import math
import time

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter


def _transkribiere_vollpass(audio) -> list[Segment]:
    """Laedt NO_KONSENS_MODELL und transkribiert die Episode batched.

    Bewusst NUR auf GPU: dort kostet der Vollpass ~170s, auf CPU
    Stunden — der Ladefehler landet als Warnung im Event-Log und der
    Bot laeuft ohne Konsens-Pass in Gap-Verify und NO-Runde weiter.
    """
    from faster_whisper import BatchedInferencePipeline, WhisperModel

    from operations.pipeline.transcription import _cuda_dlls_einbinden

    _cuda_dlls_einbinden()
    model = WhisperModel(config.NO_KONSENS_MODELL, device="cuda",
                         compute_type="float16")
    segmente: list[Segment] = []
    batched = None
    try:
        batched = BatchedInferencePipeline(model=model)
        segs, _ = batched.transcribe(
            audio, language="en", beam_size=1,
            word_timestamps=False, batch_size=8,
        )
        for s in segs:
            konf = math.exp(s.avg_logprob) if s.avg_logprob is not None else 0.0
            segmente.append(Segment(
                text=s.text, confidence=max(0.0, min(1.0, konf)),
                start_s=s.start, end_s=s.end,
            ))
    finally:
        # VRAM sofort freigeben — Gap-Verify laedt gleich sein eigenes
        # Modell (~3 GB fuer large-v3 auf der 3060 neben small).
        del batched, model
    return segmente


def no_konsens_pass(
    audio,
    counters: dict[str, StreamingCounter],
    transkribiere_fn=None,
) -> dict:
    """Vollpass ausfuehren, Funde in die erweiterten Zaehler mergen.

    Liefert den Bericht fuer das Event-Log ("no_konsens"): Modell,
    Dauer, Segment-Anzahl und Zaehler-Deltas je Markt-Slug.
    transkribiere_fn ist fuer Tests injizierbar: (audio) -> list[Segment].
    """
    start = time.monotonic()
    if transkribiere_fn is None:
        transkribiere_fn = _transkribiere_vollpass
    segmente = transkribiere_fn(audio)
    deltas: dict[str, int] = {}
    for c in counters.values():
        delta = c.ingest_nur_erweitert(segmente)
        if delta:
            deltas[c.rule.slug] = delta
    return {
        "modell": config.NO_KONSENS_MODELL,
        "dauer_s": round(time.monotonic() - start, 1),
        "segmente": len(segmente),
        "deltas": deltas,
    }
