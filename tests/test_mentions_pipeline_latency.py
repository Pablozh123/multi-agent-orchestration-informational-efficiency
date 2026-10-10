"""Offline regressions for early mentions and independent public-data work."""
from types import SimpleNamespace

import numpy as np
import pytest

from operations.pipeline import config
from operations.pipeline.transcription import ChunkTranscriber, SAMPLE_RATE


def transcriber_for(tmp_path, monkeypatch, seconds=45):
    monkeypatch.setattr(config, "CHUNK_SEKUNDEN", 20)
    monkeypatch.setattr(config, "OVERLAP_S", 2)
    path = tmp_path / "episode.mp3"
    path.write_bytes(bytes(65536))
    transcriber = object.__new__(ChunkTranscriber)
    transcriber.verarbeitete_samples = 0
    transcriber.verifier = None
    transcriber.inkrementell_final = True
    audio = np.zeros(seconds * SAMPLE_RATE, dtype="float32")
    transcriber._decode = lambda _: audio
    return transcriber, path


def test_finished_download_returns_first_twenty_seconds_before_rest(tmp_path, monkeypatch):
    transcriber, path = transcriber_for(tmp_path, monkeypatch)
    transcriber._transkribiere = lambda audio, batched: iter([
        SimpleNamespace(text="Microsoft", start=1.0, end=2.0,
                        avg_logprob=-0.1, words=None),
    ])
    first = transcriber.naechster_chunk(path, final=True)
    assert first[0].text == "Microsoft"
    assert transcriber.verarbeitete_samples == 20 * SAMPLE_RATE
    second = transcriber.naechster_chunk(path, final=True)
    assert second == []  # fake word at 19 s falls inside the overlap
    assert transcriber.verarbeitete_samples == 40 * SAMPLE_RATE
    transcriber.naechster_chunk(path, final=True)
    assert transcriber.verarbeitete_samples == 45 * SAMPLE_RATE
    assert transcriber.naechster_chunk(path, final=True) is None


def test_legacy_callers_still_flush_complete_final_audio(tmp_path, monkeypatch):
    transcriber, path = transcriber_for(tmp_path, monkeypatch)
    transcriber.inkrementell_final = False
    consumed = []

    def asr(audio, batched):
        assert len(audio) == 45*SAMPLE_RATE
        for end in (20, 40, 45):
            consumed.append(end)
            yield SimpleNamespace(text="Microsoft", start=end-1, end=end,
                                  avg_logprob=-0.1, words=None)

    transcriber._transkribiere = asr
    assert len(transcriber.naechster_chunk(path, final=True)) == 3
    assert consumed == [20, 40, 45]
    assert transcriber.verarbeitete_samples == 45*SAMPLE_RATE


def test_failed_asr_does_not_skip_unprocessed_audio(tmp_path, monkeypatch):
    transcriber, path = transcriber_for(tmp_path, monkeypatch)

    def failing(audio, batched):
        raise RuntimeError("ASR failed")

    transcriber._transkribiere = failing
    with pytest.raises(RuntimeError, match="ASR failed"):
        transcriber.naechster_chunk(path, final=True)
    assert transcriber.verarbeitete_samples == 0


def test_gpu_final_yields_before_consuming_rest_and_commits_only_success(tmp_path, monkeypatch):
    transcriber, path = transcriber_for(tmp_path, monkeypatch, seconds=100)
    transcriber.geraet = "cuda/float16"
    consumed = []

    def asr(audio, batched):
        assert batched
        for end in (20, 40):
            consumed.append(end)
            yield SimpleNamespace(text="Microsoft", start=end-1, end=end,
                                  avg_logprob=-0.1, words=None)
        raise RuntimeError("later GPU batch failed")

    transcriber._transkribiere = asr
    assert transcriber.naechster_chunk(path, final=True)[0].text == "Microsoft"
    assert consumed == [20]
    assert transcriber.verarbeitete_samples == 20*SAMPLE_RATE
    transcriber.naechster_chunk(path, final=True)
    assert consumed == [20, 40]
    with pytest.raises(RuntimeError, match="later GPU batch failed"):
        transcriber.naechster_chunk(path, final=True)
    assert transcriber.verarbeitete_samples == 40*SAMPLE_RATE
    assert transcriber._pending is None


def test_overlap_counts_each_word_once_across_finished_chunks(tmp_path, monkeypatch):
    transcriber, path = transcriber_for(tmp_path, monkeypatch)
    words = [(19.0, " Microsoft"), (21.0, " Nvidia")]

    def asr(audio, batched):
        start = max(0, transcriber.verarbeitete_samples / SAMPLE_RATE - 2)
        end = start + len(audio) / SAMPLE_RATE
        matching = [SimpleNamespace(word=w, start=t-start, end=t-start+0.5)
                    for t, w in words if start <= t < end]
        return iter([SimpleNamespace(text="ignored", start=0, end=1,
                                     avg_logprob=-0.1, words=matching)])

    transcriber._transkribiere = asr
    text = []
    while (segments := transcriber.naechster_chunk(path, final=True)) is not None:
        text.extend(s.text for s in segments)
    assert "".join(text) == " Microsoft Nvidia"


def test_slow_fallback_cannot_block_ready_primary():
    from threading import Event
    from operations.pipeline.background import BackgroundPoller

    release, started = Event(), Event()

    def slow():
        started.set()
        release.wait(2)
        return "fallback"

    try:
        with BackgroundPoller(slow, 5) as fallback, BackgroundPoller(lambda: "MP3", 5) as primary:
            assert started.wait(1)
            assert primary.ready.wait(1)
            assert primary.poll() == "MP3"
            assert fallback.poll() is None
    finally:
        release.set()


def test_book_snapshot_deltas_removal_and_disconnect():
    from operations.pipeline.orderbook import MarketBooks, best_ask

    books = MarketBooks(["yes", "no"])
    with pytest.raises(LookupError):
        books.get("yes")
    books.apply({"event_type": "book", "asset_id": "yes", "timestamp": "1000",
                 "bids": [], "asks": [{"price": "0.50", "size": "10"}]})
    books.apply({"event_type": "price_change", "timestamp": "1001", "price_changes": [
        {"asset_id": "yes", "side": "SELL", "price": "0.40", "size": "5"},
    ]})
    first = books.get("yes")
    assert best_ask(first) == 0.4
    first["asks"].clear()  # readers cannot mutate the shared book
    assert best_ask(books.get("yes")) == 0.4
    books.apply({"event_type": "price_change", "timestamp": "1002", "price_changes": [
        {"asset_id": "yes", "side": "SELL", "price": "0.40", "size": "0"},
    ]})
    assert best_ask(books.get("yes")) == 0.5
    books.disconnect()
    with pytest.raises(LookupError):
        books.get("yes")
    books.apply({"event_type": "price_change", "price_changes": [
        {"asset_id": "yes", "side": "SELL", "price": "0.10", "size": "5"},
    ]})
    with pytest.raises(LookupError):
        books.get("yes")  # a reconnect needs a full snapshot first


def test_book_rejects_invalid_prices_and_expired_connection(monkeypatch):
    from operations.pipeline import orderbook
    books = orderbook.MarketBooks(["yes"])
    monkeypatch.setattr(orderbook.time, "monotonic", lambda: 100.0)
    books.apply({"event_type": "book", "asset_id": "yes", "timestamp": "1000",
                 "bids": [], "asks": [{"price": "0.50", "size": "10"}]})
    monkeypatch.setattr(orderbook.time, "monotonic", lambda: 121.0)
    with pytest.raises(LookupError):
        books.get("yes")
    with pytest.raises(ValueError):
        books.apply({"event_type": "book", "asset_id": "yes", "timestamp": "1001",
                     "bids": [], "asks": [{"price": "NaN", "size": "10"}]})


@pytest.mark.parametrize("book_outage", [False, True])
@pytest.mark.parametrize("parallel_words", [False, True])
def test_bot_fires_from_cached_book_while_fallback_is_slow(tmp_path, monkeypatch, book_outage, parallel_words,
                                                        live_case=None):
    import json
    from threading import Barrier, Event, Lock
    from operations.pipeline import bot, execution, transcription
    from operations.pipeline.counter_engine import Segment
    from operations.pipeline.market_rules import build_rule

    rule = build_rule({"id": "1", "slug": "microsoft", "question": 'Will "Microsoft" be said?',
                       "description": "", "outcomes": json.dumps(["Yes", "No"]),
                       "clobTokenIds": json.dumps(["yes", "no"])})
    rules = [rule]
    if parallel_words:
        rules.append(build_rule({"id": "2", "slug": "nvidia", "question": 'Will "Nvidia" be said?',
                                 "description": "", "outcomes": json.dumps(["Yes", "No"]),
                                 "clobTokenIds": json.dumps(["yes2", "no2"])}))
    for name, value in {"LIVE_DIR": tmp_path, "STOP_FILE": tmp_path/"STOP", "SERIE_ID": None,
                        "ZIELSPRECHER_REFERENZEN": [], "RSS_FEED_URL": "https://example.com/rss",
                        "YT_PLAYLIST_ID": None, "MP3_PROBE_MUSTER": "https://example.com/E{n}.mp3",
                        "ASK_OBERGRENZE": 0.95, "NO_KONSENS_AKTIV": False,
                        "GAP_VERIFY_AKTIV": False, "NACHLAUF_MINUTEN": 1,
                        "NACHLAUF_POLL_S": 0.01}.items():
        monkeypatch.setattr(config, name, value)
    monkeypatch.setattr(bot.startwache, "wache_nehmen", lambda _: True)
    monkeypatch.setattr(bot, "lade_snapshot_rules", lambda: rules)
    if parallel_words:
        from operations.pipeline import basisraten
        monkeypatch.setattr(config, "SERIE_ID", "11300")
        monkeypatch.setattr(basisraten, "hole_serien_historie", lambda *a, **kw: {})
    monkeypatch.setattr(bot, "naechste_episoden_nummer", lambda: 292)
    monkeypatch.setattr(bot, "Mp3UrlProber", lambda _: SimpleNamespace(poll=lambda: "https://example.com/E292.mp3"))
    release = Event()

    class SlowWatcher:
        def initialisiere(self):
            return None

        def poll(self):
            release.wait(2)
            return None

    monkeypatch.setattr(bot, "RssWatcher", SlowWatcher)
    monkeypatch.setattr(bot, "YouTubeWatcher", SlowWatcher)

    class LocalBooks:
        def __init__(self, tokens):
            self.last_error = None
            self.yes_requests = 0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def get(self, token):
            if live_case == "delayed_expensive" and token in {"yes2", "no2"}:
                return {"asks": [{"price": "0.99", "size": "100"}], "bids": []}
            if token == "yes":
                self.yes_requests += 1
                if book_outage and self.yes_requests < 4:
                    raise LookupError("reconnecting")
            return {"asks": [{"price": "0.5", "size": "100"}], "bids": []}

    monkeypatch.setattr(bot, "MarketBooks", LocalBooks, raising=False)
    monkeypatch.setattr(bot, "fetch_book", lambda _: pytest.fail("REST book on audio path"))
    monkeypatch.setattr(bot, "log_snapshots", lambda *a, **kw: [])
    monkeypatch.setattr(transcription, "ProgressiveDownloader", lambda *args: SimpleNamespace(
        start=lambda: None, fertig=SimpleNamespace(is_set=lambda: True), fehler=None))
    chunks = iter([[Segment("Microsoft", 0.99)],
                   *([[Segment("Nvidia", 0.99)]] if parallel_words else []), None])
    monkeypatch.setattr(transcription, "ChunkTranscriber", lambda **kw: SimpleNamespace(
        geraet="fake", naechster_chunk=lambda *args, **kw: next(chunks)))
    original_place = execution.DryRunExecutor.place
    simultaneous = Barrier(2)
    fill_lock, filled = Lock(), []

    def place(executor, decision, book):
        if parallel_words and decision.action == "YES":
            simultaneous.wait(timeout=2)
        result = original_place(executor, decision, book)
        if result.status == "dry_run_fill":
            with fill_lock:
                filled.append(decision.market_id)
                if len(filled) == (2 if parallel_words else 1):
                    config.STOP_FILE.touch()
        return result

    monkeypatch.setattr(execution.DryRunExecutor, "place", place)
    live_calls = []
    if live_case and live_case != "paper_empty":
        class FakeLive(execution.DryRunExecutor):
            def __init__(self):
                super().__init__()
                self.wallet_budget = SimpleNamespace(available=100)
                self.confirmed = False

            def enable_wallet_budget(self):
                pass

            def prepare_markets(self, rules):
                return {}

            def place(self, d, book):
                live_calls.append(d.market_id)
                status = "live_fill"
                if live_case == "nofill":
                    status = "gave_up"
                elif live_case.startswith("delayed") and d.market_id == "1" and live_calls.count("1") == 1:
                    status = "pending_confirmation"
                elif live_case == "empty" or live_calls.count("1") > 1:
                    self.wallet_budget.available = 0
                    if live_case == "empty":
                        status = "skipped_budget"
                result = execution.PlacementResult(d.market_id, d.action, d.token_id,
                                                   d.limit_price, 1, 2, status)
                self._log(d, book, result)
                return result

            def reconcile_wallet(self):
                if live_case.startswith("delayed") and "1" in live_calls and not self.confirmed:
                    self.confirmed = True
                    zero = live_case == "delayed_zero"
                    return [execution.PlacementResult("1", "YES", "yes", 0.95, 0 if zero else 1,
                                                       0 if zero else 2, "gave_up" if zero else "live_fill")]
                return []

        original_poller = bot.BackgroundPoller
        monkeypatch.setattr(bot, "BackgroundPoller", lambda fn, interval: original_poller(
            fn, 0.01 if fn.__name__ == "reconcile_wallet" else interval))
        monkeypatch.setattr(execution, "LiveExecutor", FakeLive)
        monkeypatch.setattr(config, "NACHLAUF_MINUTEN", 0.005)
        if live_case == "nofill":
            monkeypatch.setattr(config, "NACHLAUF_POLL_S", 0.2)
        if live_case == "delayed_expensive":
            monkeypatch.setattr(config, "NACHLAUF_POLL_S", 0.2)
            original_sleep = bot.time.sleep

            def checked_sleep(seconds):
                if seconds >= 0.2 and live_calls:
                    events = [json.loads(line) for line in (tmp_path/"bot_events.jsonl").read_text().splitlines()]
                    assert any(e.get("art") == "wallet_reconciled" for e in events), "long sleep before confirmation"
                original_sleep(seconds)

            monkeypatch.setattr(bot.time, "sleep", checked_sleep)
    if live_case == "paper_empty":
        monkeypatch.setattr(config, "MAX_USD_GESAMT", 0)
        monkeypatch.setattr(config, "NACHLAUF_MINUTEN", 0.005)
    try:
        bot.lauf(bool(live_case) and live_case != "paper_empty")
    finally:
        release.set()
    decisions = [json.loads(line) for line in (tmp_path/"decisions_log.jsonl").read_text().splitlines()]
    fills = [d for d in decisions if d["result"]["status"] == "dry_run_fill"]
    if live_case in {"delayed", "delayed_expensive"}:
        assert live_calls.count("1") == 2  # resume the remaining sweep after confirmation
    elif live_case == "delayed_zero":
        events = [json.loads(line) for line in (tmp_path/"bot_events.jsonl").read_text().splitlines()]
        assert not any(e.get("art") == "order_fortgesetzt" for e in events)
    elif live_case in {"empty", "paper_empty"}:
        events = [json.loads(line) for line in (tmp_path/"bot_events.jsonl").read_text().splitlines()]
        assert any(e.get("art") == "nachlauf_ende" and e.get("grund") == "budget" for e in events)
    elif live_case == "nofill":
        events = [json.loads(line) for line in (tmp_path/"bot_events.jsonl").read_text().splitlines()]
        attempts = [e for e in events if e.get("art") == "order_result" and e.get("phase") == "nachlauf"]
        assert 1 <= len(attempts) <= 4
    else:
        assert len(fills) == (2 if parallel_words else 1)


@pytest.mark.parametrize("live_case", ["delayed", "empty", "nofill", "delayed_expensive", "delayed_zero", "paper_empty"])
def test_bot_resumes_delayed_sweep_and_stops_after_wallet_exhaustion(tmp_path, monkeypatch, live_case):
    test_bot_fires_from_cached_book_while_fallback_is_slow(tmp_path, monkeypatch, False, True, live_case)


def test_live_sweep_uses_supplied_connected_books(monkeypatch):
    from operations.pipeline import execution, orderbook
    from operations.pipeline.decision import Decision

    ex = object.__new__(execution.LiveExecutor)
    ex.ausgegeben_usd = 0
    ex._stop_aktiv = lambda: False
    ex._ein_clip = lambda *_: (2.0, 1.0, "order", "post_antwort")
    ex.book_source = lambda token: {"asks": []}
    monkeypatch.setattr(orderbook, "fetch_book", lambda _: pytest.fail("REST sweep book"))
    result = ex._platziere(Decision("1", "YES", "yes", "Yes", 0.5, "threshold"), 1, 2)
    assert result.status == "live_fill"
    assert result.size_usd == 1.0


def test_sdk_warmup_populates_both_token_contexts_without_orders(monkeypatch):
    from py_clob_client_v2 import ClobClient
    from operations.pipeline.execution import LiveExecutor
    client = ClobClient("https://clob.polymarket.com", chain_id=137)

    def public_get(url, **kwargs):
        if "markets-by-token" in url:
            return {"condition_id": "condition"}
        return {"t": [{"t": "yes"}, {"t": "no"}], "mts": "0.01", "nr": False,
                "fd": {"r": 0, "e": 0}}

    monkeypatch.setattr(client, "_get", public_get)
    ex = object.__new__(LiveExecutor)
    ex.client = client
    result = ex.prepare_markets([SimpleNamespace(yes_token_id="yes", no_token_id="no")])
    monkeypatch.setattr(client, "_get", lambda *a, **kw: pytest.fail("context still requires network"))
    assert result["prepared_tokens"] == 2
    assert result["errors"] == []
    assert client.get_tick_size("yes") == "0.01"
    assert client.get_neg_risk("no") is False
    assert client.get_fee_exponent("yes") == 0
