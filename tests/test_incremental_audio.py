"""Offline MP3 streaming: growth, exact samples, EOF and resource cleanup."""
import io
import time
from threading import Event, Thread

import av
import numpy as np
import pytest
from faster_whisper.audio import decode_audio

from operations.pipeline.transcription import ChunkTranscriber, SAMPLE_RATE


@pytest.fixture
def mp3_bytes():
    target = io.BytesIO()
    with av.open(target, "w", format="mp3") as container:
        stream = container.add_stream("mp3", rate=44100)
        stream.layout = "stereo"
        t = np.arange(44100 * 12) / 44100
        signal = np.stack([np.sin(t * 997 * 2 * np.pi),
                           np.sin(t * 351 * 2 * np.pi)]).astype("float32") * 0.3
        frame = av.AudioFrame.from_ndarray(signal, format="fltp", layout="stereo")
        frame.sample_rate = 44100
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return target.getvalue()


def wait_until(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        assert time.monotonic() < deadline, "decoder did not make progress"
        Event().wait(0.005)


def test_growing_mp3_reads_each_byte_once_and_matches_complete_decode(tmp_path, mp3_bytes):
    from operations.pipeline.incremental_audio import IncrementalMp3Decoder

    path = tmp_path / "episode.mp3"
    expected = decode_audio(io.BytesIO(mp3_bytes), sampling_rate=SAMPLE_RATE)
    first = len(mp3_bytes) // 2 + 137  # deliberately split an MP3 packet
    path.write_bytes(mp3_bytes[:first])
    decoder = IncrementalMp3Decoder(path, sampling_rate=SAMPLE_RATE)
    try:
        wait_until(lambda: len(decoder.audio()) > SAMPLE_RATE)
        partial = decoder.audio()
        assert 0 < len(partial) < len(expected)
        np.testing.assert_array_equal(partial, expected[:len(partial)])
        wait_until(lambda: decoder.bytes_read == first)
        with path.open("ab") as target:
            target.write(mp3_bytes[first:first + 1237])
            target.flush()
        decoder.audio()
        wait_until(lambda: decoder.bytes_read == first + 1237)
        with path.open("ab") as target:
            target.write(mp3_bytes[first + 1237:])
        actual = decoder.audio(final=True, wait=True)
        assert decoder.finished
        assert decoder.bytes_read == len(mp3_bytes)
        np.testing.assert_array_equal(actual, expected)
        # Previously handed out views remain stable while the buffer grows.
        np.testing.assert_array_equal(partial, expected[:len(partial)])
    finally:
        decoder.close()
    assert not decoder._thread.is_alive()


def test_close_interrupts_decoder_waiting_for_initial_mp3_probe(tmp_path, mp3_bytes):
    from operations.pipeline.incremental_audio import IncrementalMp3Decoder

    path = tmp_path / "incomplete.mp3"
    path.write_bytes(mp3_bytes[:16])
    decoder = IncrementalMp3Decoder(path, sampling_rate=SAMPLE_RATE)
    decoder.close()
    decoder.close()
    assert not decoder._thread.is_alive()
    path.unlink()


def bare_transcriber():
    transcriber = object.__new__(ChunkTranscriber)
    transcriber.verarbeitete_samples = 0
    transcriber.verifier = None
    transcriber.inkrementell_audio = True
    transcriber.inkrementell_final = True
    transcriber._audio_cache = None
    transcriber._cache_groesse = -1
    transcriber._pending = None
    return transcriber


def test_final_does_not_report_eof_before_worker_and_resampler_finish(tmp_path, mp3_bytes,
                                                                   monkeypatch):
    from operations.pipeline import incremental_audio

    path = tmp_path / "episode.mp3"
    path.write_bytes(mp3_bytes)
    release = Event()
    run = incremental_audio.IncrementalMp3Decoder._run

    def delayed(decoder):
        assert release.wait(5)
        run(decoder)

    monkeypatch.setattr(incremental_audio.IncrementalMp3Decoder, "_run", delayed)
    transcriber = bare_transcriber()
    chunks = []
    transcriber._transkribiere = lambda audio, batched: chunks.append(audio.copy()) or iter([])
    try:
        assert transcriber.naechster_chunk(path, final=True) == []
        assert transcriber.verarbeitete_samples == 0
        release.set()
        wait_until(lambda: transcriber.naechster_chunk(path, final=True) is None)
        expected = decode_audio(io.BytesIO(mp3_bytes), sampling_rate=SAMPLE_RATE)
        assert transcriber.verarbeitete_samples == len(expected)
        np.testing.assert_array_equal(transcriber.dekodiertes_audio(path), expected)
        assert chunks
    finally:
        release.set()
        transcriber.close()


def test_new_source_closes_decoder_and_pending_generator(tmp_path, mp3_bytes):
    path = tmp_path / "episode.mp3"
    path.write_bytes(mp3_bytes[:65536])
    transcriber = bare_transcriber()
    transcriber._decode(path)
    decoder = transcriber._decoder
    closed = []

    def pending():
        try:
            yield []
        finally:
            closed.append(True)

    transcriber._pending = pending()
    next(transcriber._pending)
    transcriber.neue_quelle()
    assert closed == [True]
    assert not decoder._thread.is_alive()
    assert transcriber._decoder is None
    assert transcriber.verarbeitete_samples == 0


def test_final_snapshot_includes_samples_published_just_before_finished(tmp_path, mp3_bytes,
                                                                     monkeypatch):
    from operations.pipeline import incremental_audio

    path = tmp_path / "episode.mp3"
    path.write_bytes(mp3_bytes)
    release = Event()
    run = incremental_audio.IncrementalMp3Decoder._run
    original_audio = incremental_audio.IncrementalMp3Decoder.audio

    def delayed(decoder):
        assert release.wait(5)
        run(decoder)

    def finish_after_snapshot(decoder, *, final=False, wait=False):
        snapshot = original_audio(decoder, final=final, wait=wait)
        if final and not release.is_set():
            release.set()
            assert decoder._finished.wait(5)
        return snapshot

    monkeypatch.setattr(incremental_audio.IncrementalMp3Decoder, "_run", delayed)
    monkeypatch.setattr(incremental_audio.IncrementalMp3Decoder, "audio", finish_after_snapshot)
    transcriber = bare_transcriber()
    transcriber._transkribiere = lambda audio, batched: iter([])
    try:
        assert transcriber.naechster_chunk(path, final=True) == []
        assert transcriber.verarbeitete_samples == 12 * SAMPLE_RATE
        assert transcriber.naechster_chunk(path, final=True) is None
    finally:
        release.set()
        transcriber.close()


def test_wait_for_current_audio_returns_at_temporary_eof(tmp_path, mp3_bytes):
    from operations.pipeline.incremental_audio import IncrementalMp3Decoder

    path = tmp_path / "episode.mp3"
    prefix = len(mp3_bytes) // 2
    path.write_bytes(mp3_bytes[:prefix])
    decoder = IncrementalMp3Decoder(path)
    returned = Event()
    worker = Thread(target=lambda: (decoder.audio(wait=True), returned.set()))
    worker.start()
    try:
        assert returned.wait(2), "wait must return at temporary EOF without finalising"
        assert not decoder.finished
        assert decoder.bytes_read == prefix
        assert len(decoder.audio()) > SAMPLE_RATE
    finally:
        decoder.close()
        worker.join()
