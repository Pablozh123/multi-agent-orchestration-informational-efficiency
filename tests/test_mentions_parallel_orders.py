"""Concurrent word triggers, one wallet, no real exchange or credentials."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

from operations.pipeline import config
from operations.pipeline.decision import Decision
from operations.pipeline.execution import ExecutorBase, LiveExecutor


def decision(market="a"):
    return Decision(market, "YES", market, "Yes", 0.5, "word threshold")


def executor(tmp_path, monkeypatch, balance=100):
    monkeypatch.setattr(config, "STOP_FILE", tmp_path/"STOP")
    monkeypatch.setattr(config, "MAX_USD_GESAMT", 1)
    monkeypatch.setattr(config, "MAX_USD_PRO_MARKT", 50)
    ex = object.__new__(LiveExecutor)
    ExecutorBase.__init__(ex, tmp_path/"orders.jsonl")
    ex._start_balance = balance
    ex.enable_wallet_budget()
    ex.book_source = lambda _: {"asks": [{"price": "0.5", "size": "1000"}]}
    return ex


def test_other_word_posts_while_first_order_waits_and_wallet_is_shared(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    posted = []
    barrier = Barrier(3)
    release = Event()

    def post(token, usd, price):
        posted.append((token, usd))
        barrier.wait(timeout=2)
        assert release.wait(2)
        return {"orderID": token, "success": True, "status": "matched",
                "takingAmount": str(usd*2), "makingAmount": str(usd)}

    ex._bestell = post
    # One matching round, then no more asks.
    seen = set()

    def book(token):
        if token in seen:
            return {"asks": []}
        seen.add(token)
        return {"asks": [{"price": "0.5", "size": "1000"}]}

    ex.book_source = book
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(ex.place, decision("a"), book("initial-a"))
            b = pool.submit(ex.place, decision("b"), book("initial-b"))
            barrier.wait(timeout=2)
            assert {token for token, _ in posted} == {"a", "b"}
            assert sum(usd for _, usd in posted) <= 97
            release.set()
            results = [a.result(timeout=2), b.result(timeout=2)]
    finally:
        release.set()
    assert all(r.status == "live_fill" for r in results)
    assert ex.ausgegeben_usd == pytest.approx(sum(r.size_usd for r in results))
    assert ex.ausgegeben_usd > config.MAX_USD_GESAMT


def test_stale_wallet_snapshot_cannot_erase_confirmed_spending(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch, balance=20)
    requests = []
    ex._bestell = lambda token, usd, price: (
        requests.append(usd) or {"success": True, "status": "matched", "orderID": token,
                                 "takingAmount": str(usd*2), "makingAmount": str(usd)})
    ex._wallet_balance = lambda: 20  # stale server cache
    first = ex.place(decision(), ex.book_source("a"))
    spent = ex.ausgegeben_usd
    ex.reconcile_wallet()
    second = ex.place(decision("b"), ex.book_source("b"))
    assert first.status == "live_fill"
    assert second.status == "skipped_budget"
    assert ex.ausgegeben_usd == spent
    assert sum(requests) <= 19.4


def test_unknown_post_keeps_reservation_and_is_not_counted_as_zero_fill(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch, balance=20)
    calls = []

    def timeout(*args):
        calls.append(args)
        raise TimeoutError("response lost after send")

    ex._bestell = timeout
    result = ex.place(decision(), ex.book_source("a"))
    assert result.status == "pending_confirmation"
    assert ex.place(decision("b"), ex.book_source("b")).status == "skipped_budget"
    assert len(calls) == 1


def test_pending_order_reconciles_without_reusing_unconfirmed_money(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch, balance=20)
    ex._bestell = lambda *a: {"success": True, "status": "delayed", "orderID": "pending"}
    ex._order_status = lambda _: {"status": "LIVE", "size_matched": "0"}
    ex._wallet_balance = lambda: 20
    assert ex.place(decision(), ex.book_source("a")).status == "pending_confirmation"
    ex._order_status = lambda _: {"status": "CANCELED", "size_matched": "10"}
    ex.reconcile_wallet()
    # Conservative fallback uses the price cap, never a zero/cheaper fill guess.
    assert ex.ausgegeben_usd == pytest.approx(10*config.ASK_OBERGRENZE)
    assert ex.wallet_budget.available < 20-ex.ausgegeben_usd


def test_stop_before_post_prevents_order_and_releases_unused_reservation(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    ex.client = SimpleNamespace(
        create_market_order=lambda _: config.STOP_FILE.touch(),
        post_order=lambda *a: pytest.fail("posted after STOP"))
    result = ex.place(decision(), ex.book_source("a"))
    assert result.status == "skipped_stop"
    assert ex.wallet_budget.available == 100


def test_dispatcher_does_not_block_audio_or_duplicate_active_market():
    from operations.pipeline.parallel_orders import ParallelOrders
    from operations.pipeline.execution import PlacementResult
    entered, release = Event(), Event()

    def place(d, book):
        entered.set()
        release.wait(2)
        return PlacementResult(d.market_id, d.action, d.token_id, d.limit_price,
                               1, 2, "live_fill")

    try:
        with ParallelOrders(SimpleNamespace(place=place), workers=2) as orders:
            assert orders.submit(decision(), {})
            assert entered.wait(1)
            assert orders.contains("a")
            assert not orders.submit(decision(), {})
            assert orders.poll() == []
            assert orders.submit(decision("b"), {})
            release.set()
            orders.wait()
            results = orders.poll()
            assert {d.market_id for d, _, _ in results} == {"a", "b"}
    finally:
        release.set()


def test_confirmation_before_future_finishes_does_not_block_market_forever():
    from operations.pipeline.parallel_orders import ParallelOrders
    from operations.pipeline.execution import PlacementResult
    entered, release = Event(), Event()

    def place(d, book):
        entered.set()
        assert release.wait(2)
        return PlacementResult(d.market_id, d.action, d.token_id, d.limit_price,
                               0, 0, "pending_confirmation")

    try:
        with ParallelOrders(SimpleNamespace(place=place), workers=1) as orders:
            assert orders.submit(decision(), {})
            assert entered.wait(1)
            orders.resolve("a")
            release.set()
            orders.wait()
            orders.poll()
            assert not orders.contains("a")
            assert orders.submit(decision(), {})
    finally:
        release.set()


def test_pending_confirmation_remains_visible_after_future_finishes():
    from operations.pipeline.parallel_orders import ParallelOrders
    from operations.pipeline.execution import PlacementResult
    ex = SimpleNamespace(place=lambda d, b: PlacementResult(
        d.market_id, d.action, d.token_id, d.limit_price, 0, 0, "pending_confirmation"))
    with ParallelOrders(ex, workers=1) as orders:
        orders.submit(decision(), {})
        orders.wait()
        orders.poll()
        assert not orders.busy
        assert orders.has_pending
        orders.resolve("a")
        assert not orders.has_pending


def test_wallet_funded_before_first_trade_uses_current_balance(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch, balance=0)
    ex._wallet_balance = lambda: 200
    ex.reconcile_wallet()
    assert ex.wallet_budget.available == 200
