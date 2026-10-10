"""Bounded offline MP3 decode benchmark. No Whisper model or network calls."""
from __future__ import annotations

import argparse
import json
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import av
import numpy as np
from faster_whisper.audio import decode_audio

from operations.pipeline.incremental_audio import IncrementalMp3Decoder


def compare_samples(actual: np.ndarray, expected: np.ndarray, *, guard: int = 0) -> dict:
    shared = max(0, min(len(actual), len(expected)) - guard)
    maximum = 0.0
    differing = 0
    for offset in range(0, shared, 1_000_000):
        end = min(offset + 1_000_000, shared)
        delta = np.abs(actual[offset:end] - expected[offset:end])
        maximum = max(maximum, float(delta.max(initial=0)))
        differing += int(np.count_nonzero(delta))
    return {"shared_samples": shared, "excluded_tail_samples": guard,
            "max_abs_error": maximum, "differing_samples": differing,
            "same_length": len(actual) == len(expected)}


def benchmark(source: Path, output: Path, *, steps: int = 10) -> dict:
    if not 8 <= steps <= 12:
        raise ValueError("use 8 to 12 prefix stages to keep this benchmark bounded")
    size = source.stat().st_size
    prefixes = [size * step // steps for step in range(1, steps + 1)]
    results = {"source": str(source.resolve()), "source_bytes": size,
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "python": platform.python_version(), "pyav": av.__version__,
               "sampling_rate": 16000, "prefix_stages": steps,
               "limitations": ["One local run; cached files and machine load affect timings.",
                               "No ASR, GPU, network or trading was invoked.",
                               "Prefix waveforms exclude 64 resampler-tail samples.",
                               "Streaming can withhold a subsecond source FIFO plus demux buffers."],
               "prefixes": []}
    with tempfile.TemporaryDirectory(prefix="mentions-decode-") as scratch:
        growing = Path(scratch) / "episode.mp3"
        # Measure the old behaviour on ten growing snapshots, not hundreds of
        # complete 93-minute files. Copy time stays outside the decode timings.
        with source.open("rb") as original, growing.open("wb") as target:
            for index, length in enumerate(prefixes):
                target.write(original.read(length - target.tell()))
                target.flush()
                start = perf_counter()
                baseline = decode_audio(str(growing), sampling_rate=16000)
                elapsed = perf_counter() - start
                results["prefixes"].append({"stage": index + 1, "bytes": length,
                                            "baseline_s": elapsed,
                                            "baseline_samples": len(baseline)})
                print(f"baseline {index + 1}/{steps}: {elapsed:.4f}s", flush=True)
        expected = baseline  # the final prefix is the original complete MP3
        with source.open("rb") as original, growing.open("wb") as target:
            decoder = None
            try:
                for index, length in enumerate(prefixes):
                    target.write(original.read(length - target.tell()))
                    target.flush()
                    start = perf_counter()
                    if decoder is None:
                        decoder = IncrementalMp3Decoder(growing, sampling_rate=16000)
                    final = index == steps - 1
                    audio = decoder.audio(final=final, wait=True)
                    elapsed = perf_counter() - start
                    row = results["prefixes"][index]
                    row.update({"incremental_s": elapsed, "incremental_samples": len(audio),
                                "compressed_bytes_read": decoder.bytes_read,
                                "vs_complete_audio": compare_samples(audio, expected,
                                                                     guard=0 if final else 64)})
                    print(f"incremental {index + 1}/{steps}: {elapsed:.4f}s", flush=True)
                results["growing"] = {
                    "baseline_total_s": sum(r["baseline_s"] for r in results["prefixes"]),
                    "incremental_total_s": sum(r["incremental_s"] for r in results["prefixes"]),
                    "baseline_decoded_prefix_bytes": sum(prefixes),
                    "incremental_compressed_bytes_read": decoder.bytes_read,
                    "final_samples": len(audio),
                    "final_comparison": compare_samples(audio, expected),
                }
            finally:
                if decoder is not None:
                    decoder.close()
        # A separate one-shot decode distinguishes growth savings from decoder
        # throughput. Only one additional complete decode per implementation.
        start = perf_counter()
        one_shot = decode_audio(str(source), sampling_rate=16000)
        baseline_s = perf_counter() - start
        start = perf_counter()
        decoder = IncrementalMp3Decoder(source, sampling_rate=16000)
        try:
            audio = decoder.audio(final=True, wait=True)
            incremental_s = perf_counter() - start
            results["complete_file"] = {"baseline_s": baseline_s,
                                        "incremental_s": incremental_s,
                                        "compressed_bytes_read": decoder.bytes_read,
                                        "samples": len(audio),
                                        "comparison": compare_samples(audio, one_shot)}
        finally:
            decoder.close()
    results["growing"]["speedup"] = (results["growing"]["baseline_total_s"]
                                       / results["growing"]["incremental_total_s"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()
    result = benchmark(args.source, args.output, steps=args.steps)
    print(json.dumps({"growing": result["growing"], "complete_file": result["complete_file"]},
                     indent=2))


if __name__ == "__main__":
    main()
