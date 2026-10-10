"""Explicit offline ASR comparison. Reads local audio, never starts a bot."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import time


def run(audio_path: Path, snapshot_path: Path, mode: str) -> dict:
    import numpy as np
    from faster_whisper import WhisperModel, BatchedInferencePipeline
    from faster_whisper.audio import decode_audio

    from operations.pipeline import config
    from operations.pipeline.counter_engine import Segment, StreamingCounter
    from operations.pipeline.market_rules import build_rule
    from operations.pipeline.transcription import (
        ChunkTranscriber, SAMPLE_RATE, _cuda_dlls_einbinden,
    )

    _cuda_dlls_einbinden()
    before = time.monotonic()
    audio = decode_audio(str(audio_path), sampling_rate=SAMPLE_RATE)
    decode_s = time.monotonic() - before
    rules = [build_rule(m) for m in json.loads(snapshot_path.read_text(encoding="utf-8"))["markets"]]
    rules = [r for r in rules if r.status == "active"]

    def model(name, device):
        started = time.monotonic()
        instance = WhisperModel(name, device=device,
                                compute_type="float16" if device == "cuda" else "int8",
                                cpu_threads=4, num_workers=1, local_files_only=True)
        list(instance.transcribe(np.zeros(SAMPLE_RATE, dtype="float32"),
                                 language="en", beam_size=1)[0])
        return instance, time.monotonic() - started

    def chunks(instance, data, device, force_20=False):
        transcriber = object.__new__(ChunkTranscriber)
        transcriber.model = instance
        transcriber.geraet = "bounded-probe" if force_20 else device
        transcriber.verifier = None
        transcriber.inkrementell_final = True
        transcriber._batched = None
        transcriber.verarbeitete_samples = 0
        transcriber._audio_cache = data
        transcriber._cache_groesse = audio_path.stat().st_size
        while (segments := transcriber.naechster_chunk(audio_path, final=True)) is not None:
            yield segments

    def assess(groups):
        counters = {r.market_id: StreamingCounter(r) for r in rules}
        thresholds = {}
        first_segments_s = None
        started = time.monotonic()
        count = 0
        for index, segments in enumerate(groups, 1):
            elapsed = time.monotonic() - started
            if first_segments_s is None and segments:
                first_segments_s = elapsed
            count += len(segments)
            for r in rules:
                c = counters[r.market_id]
                c.ingest_chunk(index, segments, "offline")
                threshold = 1 if r.schwelle <= 1 else r.schwelle + config.YES_SCHWELLE_PUFFER
                if c.ziel_count >= threshold and r.slug not in thresholds:
                    thresholds[r.slug] = elapsed
        return {"elapsed_s": time.monotonic()-started, "first_segments_s": first_segments_s,
                "segment_count": count, "threshold_elapsed_s": thresholds,
                "counts": {r.slug: counters[r.market_id].count for r in rules}}

    def batch_groups(instance, data, incremental=False):
        segments, _ = BatchedInferencePipeline(instance).transcribe(
            data, language="en", beam_size=1, word_timestamps=True, batch_size=8)
        import math
        if incremental:
            for s in segments:
                yield [Segment(s.text, math.exp(s.avg_logprob), s.start, s.end)]
        else:
            # Reproduce the previous final path: return after consuming all segments.
            yield [Segment(s.text, math.exp(s.avg_logprob), s.start, s.end) for s in segments]

    if mode == "hybrid":
        # A bounded feasibility probe, not an end-to-end NO benchmark.
        sample = np.concatenate([audio[:120*SAMPLE_RATE],
                                 audio[2700*SAMPLE_RATE:2820*SAMPLE_RATE],
                                 audio[-120*SAMPLE_RATE:]])
        small, small_load = model("small", "cpu")
        large, large_load = model("large-v3", "cuda")
        serial_start = time.monotonic()
        cpu_serial = assess(chunks(small, sample, "cpu"))
        gpu_serial = assess(batch_groups(large, sample))
        serial_s = time.monotonic()-serial_start
        parallel_start = time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as pool:
            cpu = pool.submit(assess, chunks(small, sample, "cpu"))
            gpu = pool.submit(assess, batch_groups(large, sample))
            cpu_parallel, gpu_parallel = cpu.result(), gpu.result()
        result = {"probe_audio_s": len(sample)/SAMPLE_RATE,
                  "serial_s": serial_s, "parallel_s": time.monotonic()-parallel_start,
                  "cpu_serial": cpu_serial, "gpu_serial": gpu_serial,
                  "cpu_parallel": cpu_parallel, "gpu_parallel": gpu_parallel,
                  "load_s": {"small": small_load, "large": large_load}}
    else:
        device = "cpu" if mode == "cpu20" else "cuda"
        small, load_s = model("small", device)
        groups = (batch_groups(small, audio, incremental=mode == "streamed")
                  if mode in {"baseline", "streamed"}
                  else chunks(small, audio, device, force_20=mode in {"gpu20", "cpu20"}))
        result = {**assess(groups), "load_s": load_s}
    with audio_path.open("rb") as audio_file:
        digest = hashlib.file_digest(audio_file, "sha256").hexdigest()
    return {"mode": mode, "audio": str(audio_path),
            "audio_sha256": digest,
            "audio_s": len(audio)/SAMPLE_RATE, "decode_s": decode_s, "cpu_threads": 4,
            "versions": {p: version(p) for p in ("faster-whisper", "ctranslate2", "numpy")},
            "timing_scope": "warm ASR and counters; excludes source, download, decode, books and orders",
            **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--mode", choices=("baseline", "streamed", "gpu", "gpu20", "cpu20", "hybrid"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.audio.resolve(strict=True), args.snapshot.resolve(strict=True), args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k in (
        "mode", "elapsed_s", "first_segments_s", "serial_s", "parallel_s", "load_s", "decode_s")}), flush=True)


if __name__ == "__main__":
    main()
