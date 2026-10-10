"""Independent bounded polling; slow public sources never block the caller."""
from __future__ import annotations

from queue import Empty, Queue
from threading import Event, Thread
import time


class BackgroundPoller:
    def __init__(self, fetch, interval_s: float) -> None:
        self.fetch = fetch
        self.interval_s = interval_s
        self.ready = Event()
        self._stop = Event()
        self._results = Queue(maxsize=1)
        self._thread = Thread(target=self._run, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self.stop()
        self._thread.join(timeout=0.2)

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            if not self._results.full():
                try:
                    result = self.fetch()
                except Exception as exc:  # public-source failure is delivered to caller
                    result = exc
                if result is not None and result != [] and not self._stop.is_set():
                    self._results.put_nowait(result)
                    self.ready.set()
            self._stop.wait(max(0.01, self.interval_s-(time.monotonic()-started)))

    def poll(self):
        try:
            result = self._results.get_nowait()
        except Empty:
            return None
        self.ready.clear()
        if isinstance(result, Exception):
            raise result
        return result
