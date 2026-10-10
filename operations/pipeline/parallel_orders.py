"""One independent sweep per word; results are consumed by the audio loop."""
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Event

from operations.pipeline.execution import PlacementResult


class ParallelOrders:
    def __init__(self, executor, workers: int):
        self.executor = executor
        self._pool = ThreadPoolExecutor(max_workers=max(1, workers))
        self._futures = {}
        self._blocked = set()
        self._resolved = set()
        self.executor.abort_event = Event()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.executor.abort_event.set()
        self._pool.shutdown(wait=True, cancel_futures=True)

    @property
    def busy(self):
        return bool(self._futures)

    @property
    def has_pending(self):
        return bool(self._blocked)

    def contains(self, market_id):
        return market_id in self._blocked or any(d.market_id == market_id for d, _ in self._futures.values())

    def submit(self, decision, book, phase="yes") -> bool:
        if self.executor.abort_event.is_set() or self.contains(decision.market_id):
            return False
        self._resolved.discard(decision.market_id)
        future = self._pool.submit(self.executor.place, decision, book)
        self._futures[future] = (decision, phase)
        return True

    def resolve(self, market_id):
        self._blocked.discard(market_id)
        if self.contains(market_id):
            self._resolved.add(market_id)

    def wait(self):
        wait(self._futures)

    def poll(self):
        completed = []
        for future, (d, phase) in list(self._futures.items()):
            if not future.done():
                continue
            del self._futures[future]
            if future.cancelled():
                continue
            try:
                result = future.result()
            except Exception as exc:
                result = PlacementResult(d.market_id, d.action, d.token_id, d.limit_price,
                                         0, 0, "error", str(exc))
            if result.status == "pending_confirmation" and d.market_id not in self._resolved:
                self._blocked.add(d.market_id)
            self._resolved.discard(d.market_id)
            completed.append((d, result, phase))
        return completed
