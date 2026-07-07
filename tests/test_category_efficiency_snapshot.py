"""Tests fuer operations/analysis/category_efficiency_snapshot.py (Kernlogik)."""

from operations.analysis.category_efficiency_snapshot import (
    clip01,
    clob_price_before,
    outcome_y,
    p_close_estimate,
    parse_closed_time,
)


def test_outcome_y_eindeutig():
    assert outcome_y(["1", "0"]) == 1.0
    assert outcome_y(["0", "1"]) == 0.0


def test_outcome_y_ausschluss_bei_uneindeutig():
    assert outcome_y(["0.5", "0.5"]) is None
    assert outcome_y(None) is None
    assert outcome_y(["1"]) is None


def test_clip01():
    assert clip01(1.0025) == 1.0
    assert clip01(-0.01) == 0.0
    assert clip01(0.42) == 0.42


def test_p_close_mittelpunkt_bei_engem_buch():
    # TikTok-Fall: bid 0.994 / ask 0.996 -> Mittelpunkt, lastTrade ignoriert.
    m = {"best_bid": 0.994, "best_ask": 0.996, "last_trade_price": 1}
    assert abs(p_close_estimate(m) - 0.995) < 1e-9


def test_p_close_korrigiert_garbage_lasttrade():
    # Eleven-Fall: lastTrade=1 widerspricht bestAsk=0.001 -> Quote gewinnt.
    m = {"best_bid": None, "best_ask": 0.001, "last_trade_price": 1}
    assert p_close_estimate(m) == 0.001


def test_p_close_konsistenter_lasttrade_bleibt():
    m = {"best_bid": None, "best_ask": 0.001, "last_trade_price": 0.001}
    assert p_close_estimate(m) == 0.001


def test_p_close_ohne_preissignal_ist_none():
    assert p_close_estimate({"best_bid": None, "best_ask": None, "last_trade_price": None}) is None


def test_clob_price_before_nimmt_letzten_punkt_vor_deadline():
    hist = [{"t": 100, "p": 0.3}, {"t": 200, "p": 0.4}, {"t": 300, "p": 0.9}]
    assert clob_price_before(hist, 250) == 0.4
    assert clob_price_before(hist, 99) is None


def test_parse_closed_time_utc():
    dt = parse_closed_time("2025-01-22 00:31:19+00")
    assert int(dt.timestamp()) == 1737505879
