"""Tests fuer die Fensterfilter-Logik von southpark_window_trades."""

from __future__ import annotations

import pytest

from operations.analysis import southpark_window_trades as sw

DROP = 2_000_000_000


def trade(ts: int, side: str = "BUY", outcome: str = "Yes",
          price: float = 0.5, size: float = 100.0) -> dict:
    return {"timestamp": ts, "side": side, "outcome": outcome,
            "price": price, "size": size}


# ------------------------------------------------------------ Fensterfilter


def test_filtere_fenster_grenzen_und_sortierung() -> None:
    ende = DROP + sw.FENSTER_STUNDEN * 3600
    trades = [
        trade(DROP - 1),      # vor Drop: raus
        trade(ende),          # Fensterende exklusiv: raus
        trade(ende - 1),      # letzter drin
        trade(DROP),          # Drop selbst inklusiv: drin
    ]
    gefiltert = sw.filtere_fenster(trades, DROP)
    assert [t["timestamp"] for t in gefiltert] == [DROP, ende - 1]


def test_filtere_fenster_akzeptiert_string_timestamps() -> None:
    trades = [trade(0) | {"timestamp": str(DROP + 60)}]
    assert len(sw.filtere_fenster(trades, DROP)) == 1


# ------------------------------------------------------------ Kennzahlen


def test_trade_usd() -> None:
    assert sw.trade_usd(trade(DROP, price=0.25, size=400)) == pytest.approx(100.0)


def test_usd_je_stunde_bucketing() -> None:
    trades = [
        trade(DROP, price=0.5, size=100),          # Stunde 0: 50 USD
        trade(DROP + 3599, price=0.5, size=100),   # Stunde 0: 50 USD
        trade(DROP + 3600, price=0.5, size=40),    # Stunde 1: 20 USD
    ]
    buckets = sw.usd_je_stunde(trades, DROP)
    assert len(buckets) == sw.FENSTER_STUNDEN
    assert buckets[0] == {"stunde_nach_drop": 0, "n_trades": 2, "usd": 100.0}
    assert buckets[1] == {"stunde_nach_drop": 1, "n_trades": 1, "usd": 20.0}
    assert buckets[2]["usd"] == 0.0


def test_yes_kaeufe_unter_schwelle() -> None:
    trades = [
        trade(DROP, side="BUY", outcome="Yes", price=0.69),   # drin
        trade(DROP, side="BUY", outcome="Yes", price=0.70),   # Schwelle exklusiv
        trade(DROP, side="SELL", outcome="Yes", price=0.50),  # kein Kauf
        trade(DROP, side="BUY", outcome="No", price=0.10),    # kein YES
    ]
    billig = sw.yes_kaeufe_unter(trades)
    assert len(billig) == 1
    assert billig[0]["price"] == pytest.approx(0.69)


def test_fasse_zusammen_leer() -> None:
    k = sw.fasse_zusammen([], DROP)
    assert k["n_trades"] == 0
    assert k["gesamt_usd"] == 0.0
    assert k["groesster_einzeltrade_usd"] == 0.0
    assert k["yes_kaeufe_preis_unter_0_7"]["n_trades"] == 0


def test_fasse_zusammen_deterministisch() -> None:
    trades = [trade(DROP + i * 60, price=0.4, size=10 + i) for i in range(5)]
    assert sw.fasse_zusammen(trades, DROP) == sw.fasse_zusammen(trades, DROP)


# ------------------------------------------------------------ Pagination


def test_lade_trades_paginiert_bis_cutoff(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sw, "RAW_DIR", tmp_path)
    cutoff = DROP - 3600

    seiten = {
        0: [trade(DROP + 100) for _ in range(sw.SEITENLIMIT)],
        sw.SEITENLIMIT: [trade(DROP - 7200)],  # aelter als Cutoff -> Stopp
        sw.SEITENLIMIT * 2: [trade(DROP - 9999)],  # darf nie abgerufen werden
    }
    abgerufen = []

    def fake_fetch(condition_id: str, offset: int) -> list[dict]:
        abgerufen.append(offset)
        return seiten.get(offset, [])

    alle = sw.lade_trades("0xabc", cutoff, fetch_seite=fake_fetch)
    assert abgerufen == [0, sw.SEITENLIMIT]
    assert len(alle) == sw.SEITENLIMIT + 1
    # Cache geschrieben; Zweitaufruf kommt ohne fetch aus
    nochmal = sw.lade_trades("0xabc", cutoff, fetch_seite=None)
    assert nochmal == alle
