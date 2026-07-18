"""Gap-Verify: Transkript-Luecken vor der NO-Runde nachpruefen.

Die Silero-VAD verwirft musikunterlegte Sprache (Intro/Outro-Jingles,
eingespielte Clips) — im Transkript entstehen unsichtbare Loecher.
E281-Beleg (18.07.): "tension" fiel genau einmal, bei 5371s im Outro;
das Transkript endete bei 5330s von 5394s, der Zaehler stand auf 0,
die NO @0.88 verlor. Nachgemessen: small findet das Outro auch OHNE
VAD nicht zuverlaessig (0/3 Laeufen), large-v3 ohne VAD 2/2 — darum
transkribiert der Nachpass die Luecken mit GAP_MODELL (large-v3).

Funde fliessen ausschliesslich in den erweiterten Zaehler
(StreamingCounter.ingest_nur_erweitert): sie blocken NO-Kaeufe, loesen
aber nie YES aus. Ohne-VAD-Decodes koennen in Musik halluzinieren; ein
halluziniertes Wort kostet so hoechstens eine NO-Chance, nie Geld.
"""

from __future__ import annotations

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter

SAMPLE_RATE = 16_000


def finde_luecken(
    intervalle: list[tuple[float, float]],
    gesamt_dauer_s: float,
    min_luecke_s: float,
) -> list[tuple[float, float]]:
    """Unabgedeckte Fenster >= min_luecke_s, inkl. Kopf und Schwanz.

    intervalle sind (start_s, ende_s) der transkribierten Segmente in
    beliebiger Reihenfolge; sie werden gemerged (2s Toleranz fuer
    Segment-Grenzen).
    """
    if gesamt_dauer_s <= 0:
        return []
    if not intervalle:
        return [(0.0, gesamt_dauer_s)]
    sortiert = sorted(intervalle)
    gemerged: list[list[float]] = [list(sortiert[0])]
    for a, b in sortiert[1:]:
        if a <= gemerged[-1][1] + 2.0:
            gemerged[-1][1] = max(gemerged[-1][1], b)
        else:
            gemerged.append([a, b])
    luecken: list[tuple[float, float]] = []
    cursor = 0.0
    for a, b in gemerged:
        if a - cursor >= min_luecke_s:
            luecken.append((cursor, a))
        cursor = max(cursor, b)
    if gesamt_dauer_s - cursor >= min_luecke_s:
        luecken.append((cursor, gesamt_dauer_s))
    return luecken


def _transkribiere_luecken(audio, luecken: list[tuple[float, float]]):
    """Laedt GAP_MODELL einmalig und transkribiert die Fenster ohne VAD."""
    import math

    from faster_whisper import WhisperModel

    from operations.pipeline.transcription import _cuda_dlls_einbinden

    _cuda_dlls_einbinden()
    try:
        model = WhisperModel(config.GAP_MODELL, device="cuda",
                             compute_type="float16")
    except Exception:  # noqa: BLE001 - CPU-Fallback wie im Haupt-Transcriber
        model = WhisperModel(config.GAP_MODELL, device="cpu",
                             compute_type="int8")
    segmente: list[Segment] = []
    try:
        for a, b in luecken:
            start = max(0.0, a - config.GAP_RAND_S)
            ende = min(len(audio) / SAMPLE_RATE, b + config.GAP_RAND_S)
            ausschnitt = audio[int(start * SAMPLE_RATE):int(ende * SAMPLE_RATE)]
            if len(ausschnitt) < SAMPLE_RATE:
                continue
            segs, _ = model.transcribe(
                ausschnitt, language="en", beam_size=1,
                vad_filter=False, word_timestamps=False,
            )
            for s in segs:
                konf = math.exp(s.avg_logprob) if s.avg_logprob is not None else 0.0
                segmente.append(Segment(
                    text=s.text, confidence=max(0.0, min(1.0, konf)),
                    start_s=start + s.start, end_s=start + s.end,
                ))
    finally:
        del model
    return segmente


def gap_verify(
    audio,
    abgedeckt: list[tuple[float, float]],
    gesamt_dauer_s: float,
    counters: dict[str, StreamingCounter],
    transkribiere_fn=None,
) -> dict:
    """Luecken finden, nachtranskribieren, Funde in erweiterte Zaehler.

    Liefert einen Bericht fuer das Event-Log: gefundene Luecken,
    Segment-Anzahl und Zaehler-Deltas je Markt-Slug. transkribiere_fn
    ist fuer Tests injizierbar (audio, luecken) -> list[Segment].
    """
    luecken = finde_luecken(abgedeckt, gesamt_dauer_s, config.GAP_MIN_LUECKE_S)
    if not luecken:
        return {"luecken": [], "segmente": 0, "deltas": {}}
    if transkribiere_fn is None:
        transkribiere_fn = _transkribiere_luecken
    segmente = transkribiere_fn(audio, luecken)
    deltas: dict[str, int] = {}
    for c in counters.values():
        delta = c.ingest_nur_erweitert(segmente)
        if delta:
            deltas[c.rule.slug] = delta
    return {
        "luecken": [(round(a, 1), round(b, 1)) for a, b in luecken],
        "segmente": len(segmente),
        "deltas": deltas,
    }
