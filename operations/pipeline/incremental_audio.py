"""One PyAV pass over a growing MP3, including its final resampler flush."""
from __future__ import annotations

import io
import os
import threading
from pathlib import Path

import av
import numpy as np


class _GrowingReader(io.RawIOBase):
    """Temporary file EOF blocks; only final or cancellation is real EOF."""

    def __init__(self, path: Path, decoder: IncrementalMp3Decoder) -> None:
        super().__init__()
        self._file = path.open("rb", buffering=0)
        self._decoder = decoder
        self.bytes_read = 0
        self._size_query_position: int | None = None
        self.waiting = False

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        # FFmpeg's Xing parser needs avio_size for correct encoder-padding
        # removal. Permit size queries, never rereading compressed bytes.
        return True

    def tell(self) -> int:
        return (self._file.tell() if self._size_query_position is None
                else self._size_query_position)

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_END and offset == -1:
            self._size_query_position = os.fstat(self._file.fileno()).st_size - 1
        elif whence == io.SEEK_SET and offset == self._file.tell():
            self._size_query_position = None
        else:
            raise io.UnsupportedOperation("MP3 compressed reads must remain sequential")
        return self.tell()

    def read(self, size: int = -1) -> bytes:
        if self._size_query_position is not None:
            raise io.UnsupportedOperation("only the MP3 size query may seek")
        decoder = self._decoder
        with decoder._condition:
            while not decoder._cancelled:
                block = self._file.read(size if size >= 0 else 65536)
                if block:
                    self.waiting = False
                    self.bytes_read += len(block)
                    return block
                if decoder._final:
                    return b""
                self.waiting = True
                decoder._condition.notify_all()
                decoder._condition.wait(0.1)
        return b""

    def close(self) -> None:
        self._file.close()
        super().close()


class IncrementalMp3Decoder:
    """Decode every compressed byte once, exposing stable float32 audio views.

    The worker keeps MP3 codec/resampler state across temporary EOFs. ``final``
    releases EOF and flushes the decoder and resampler. Only ``finished`` permits
    the caller to treat a short remainder as the complete recording.
    """

    def __init__(self, path: Path, sampling_rate: int = 16000) -> None:
        self.path = Path(path)
        self.sampling_rate = sampling_rate
        self._condition = threading.Condition()
        self._final = False
        self._cancelled = False
        self._finished = threading.Event()
        self._error: Exception | None = None
        self._samples = np.empty(sampling_rate, dtype="float32")
        self._length = 0
        self._reader = _GrowingReader(self.path, self)
        self._thread = threading.Thread(target=self._run, name="mp3-decoder", daemon=True)
        self._thread.start()

    @property
    def finished(self) -> bool:
        return self._finished.is_set()

    @property
    def bytes_read(self) -> int:
        return self._reader.bytes_read

    def audio(self, *, final: bool = False, wait: bool = False) -> np.ndarray:
        """Current samples; wait drains current bytes, final also flushes EOF."""
        with self._condition:
            self._final |= final
            self._condition.notify_all()
            if wait and not final:
                size = self.path.stat().st_size
                self._condition.wait_for(lambda: self.finished or (
                    self._reader.waiting and self.bytes_read >= size))
        if wait and final:
            self._thread.join()
        with self._condition:
            if self._error is not None:
                raise RuntimeError(f"MP3 decoding failed: {self.path}") from self._error
            return self._samples[:self._length]

    def _append(self, frame: av.AudioFrame) -> None:
        source = frame.to_ndarray().reshape(-1)
        with self._condition:
            end = self._length + len(source)
            if end > len(self._samples):
                grown = np.empty(max(end, len(self._samples) * 2), dtype="float32")
                grown[:self._length] = self._samples[:self._length]
                self._samples = grown
            np.multiply(source, 1 / 32768.0,
                        out=self._samples[self._length:end], casting="unsafe")
            self._length = end

    def _run(self) -> None:
        try:
            resampler = av.AudioResampler(format="s16", layout="mono",
                                          rate=self.sampling_rate)
            fifo = av.AudioFifo()
            with av.open(self._reader, mode="r", format="mp3",
                         metadata_errors="ignore") as container:
                frames = iter(container.decode(audio=0))
                while not self._cancelled:
                    try:
                        frame = next(frames)
                    except StopIteration:
                        break
                    except av.error.InvalidDataError:
                        continue  # same corrupt-frame handling as faster-whisper
                    frame.pts = None
                    fifo.write(frame)
                    # Amortise ndarray/resampling overhead while withholding
                    # less than 0.8 s at the usual MP3 source sample rates.
                    if fifo.samples >= 32000:
                        for output in resampler.resample(fifo.read()):
                            self._append(output)
                if not self._cancelled:
                    if fifo.samples:
                        for output in resampler.resample(fifo.read()):
                            self._append(output)
                    for output in resampler.resample(None):
                        self._append(output)
        except Exception as error:  # surfaced in audio(), never an early clean EOF
            if not self._cancelled:
                self._error = error
        finally:
            with self._condition:
                self._reader.close()
                self._finished.set()
                self._condition.notify_all()

    def close(self) -> None:
        """Interrupt a temporary EOF and release the worker and its file handle."""
        with self._condition:
            self._cancelled = True
            self._condition.notify_all()
        self._thread.join()
