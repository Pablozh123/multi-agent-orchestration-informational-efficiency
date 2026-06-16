from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from operations.analysis.informed_trading_signature import (
    SIGNATURE_COLUMNS,
    build_informed_trading_signature,
    generate_h3_informed_trading_signature,
)


def test_build_signature_has_expected_ranges() -> None:
    signature = build_informed_trading_signature(
        _events(),
        _trades(spike_multiplier=1.0),
        _prices(),
        baseline_window_days=(-10, -4),
        event_window_days=(-1, 1),
        min_baseline_windows=3,
        max_lag_days=1,
    )

    assert tuple(signature.columns) == SIGNATURE_COLUMNS
    assert len(signature) == 3
    assert "wallet_address" not in signature.columns
    assert signature["suspicion_score"].between(0, 1).all()
    assert signature["new_wallet_share"].between(0, 1).all()
    assert signature["top1_concentration"].between(0, 1).all()
    assert signature["hhi"].between(0, 1).all()
    assert signature["baseline_window_count"].eq(5).all()
    assert signature["score_feature_count"].ge(4).all()


def test_build_signature_is_deterministic() -> None:
    kwargs = {
        "baseline_window_days": (-10, -4),
        "event_window_days": (-1, 1),
        "min_baseline_windows": 3,
        "max_lag_days": 1,
    }

    first = build_informed_trading_signature(
        _events(),
        _trades(spike_multiplier=1.0),
        _prices(),
        **kwargs,
    )
    second = build_informed_trading_signature(
        _events(),
        _trades(spike_multiplier=1.0),
        _prices(),
        **kwargs,
    )

    assert_frame_equal(first, second)


def test_generate_signature_writes_no_wallet_addresses(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    events_path = tmp_path / "events.csv"
    output_path = tmp_path / "signature.csv"
    metadata_path = tmp_path / "signature_metadata.json"
    figure_path = tmp_path / "signature.png"
    _write_db(db_path, _trades(spike_multiplier=5.0), _prices())
    _write_event_seed(events_path)

    result = generate_h3_informed_trading_signature(
        db_path=db_path,
        events_csv_path=events_path,
        output_path=output_path,
        metadata_path=metadata_path,
        figure_path=figure_path,
        baseline_window_days=(-10, -4),
        event_window_days=(-1, 1),
        min_baseline_windows=3,
        max_lag_days=1,
    )

    output_text = output_path.read_text(encoding="utf-8")
    metadata_text = metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert result.row_count == 3
    assert "wallet_address" not in pd.read_csv(output_path).columns
    assert "0x" not in output_text
    assert "0x" not in metadata_text
    assert metadata["output"]["contains_wallet_addresses"] is False
    assert metadata["source_filter_metadata"]["minimum_observed_amount_note"].endswith(
        "threshold or whale definition."
    )
    assert figure_path.exists()
    assert figure_path.stat().st_size > 0


def test_suspicion_score_increases_for_synthetic_spike() -> None:
    kwargs = {
        "baseline_window_days": (-10, -4),
        "event_window_days": (-1, 1),
        "min_baseline_windows": 3,
        "max_lag_days": 1,
    }
    base = build_informed_trading_signature(
        _events(),
        _trades(spike_multiplier=1.0),
        _prices(),
        **kwargs,
    )
    spiked = build_informed_trading_signature(
        _events(),
        _trades(spike_multiplier=8.0),
        _prices(),
        **kwargs,
    )

    target = "evt_spike_target"
    base_score = float(base.loc[base["event_id"] == target, "suspicion_score"].iloc[0])
    spiked_score = float(
        spiked.loc[spiked["event_id"] == target, "suspicion_score"].iloc[0]
    )
    assert spiked_score > base_score
    for feature in ("abnormal_trade_size_z", "volume_z"):
        assert (
            float(spiked.loc[spiked["event_id"] == target, feature].iloc[0])
            >= float(base.loc[base["event_id"] == target, feature].iloc[0])
        )


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _event("evt_reference_low", "2024-02-01", "Reference low"),
            _event("evt_spike_target", "2024-02-20", "Synthetic target"),
            _event("evt_reference_high", "2024-03-10", "Reference high"),
        ]
    )


def _event(event_id: str, event_date: str, title: str) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_date": event_date,
        "title": title,
        "event_type": "synthetic",
        "source_url": f"https://example.com/{event_id}",
    }


def _trades(*, spike_multiplier: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    event_specs = [
        ("evt_reference_low", pd.Timestamp("2024-02-01"), 1.0),
        ("evt_spike_target", pd.Timestamp("2024-02-20"), spike_multiplier),
        ("evt_reference_high", pd.Timestamp("2024-03-10"), 2.0),
    ]
    for index, (_event_id, event_date, multiplier) in enumerate(event_specs, start=1):
        baseline_start = event_date - pd.Timedelta(days=10)
        for offset in range(7):
            day = baseline_start + pd.Timedelta(days=offset)
            amount = 90.0 + (offset * 11.0) + (index * 3.0)
            rows.append(
                _trade(
                    day,
                    wallet=f"0xbase{index:02d}{offset:04d}",
                    amount=amount,
                    suffix=f"base{index}{offset}",
                )
            )
            rows.append(
                _trade(
                    day,
                    wallet=f"0xsteady{index:02d}0001",
                    amount=55.0 + offset,
                    suffix=f"steady{index}{offset}",
                )
            )

        for relative_day in (-1, 0, 1):
            day = event_date + pd.Timedelta(days=relative_day)
            rows.append(
                _trade(
                    day,
                    wallet=f"0xtopwallet{index:02d}",
                    amount=220.0 * multiplier,
                    suffix=f"top{index}{relative_day}",
                )
            )
            extra_wallets = 1 if multiplier <= 2 else 5
            for extra in range(extra_wallets):
                rows.append(
                    _trade(
                        day,
                        wallet=f"0xnew{index:02d}{relative_day + 2:02d}{extra:04d}",
                        amount=(120.0 + extra * 7.0) * multiplier,
                        suffix=f"new{index}{relative_day}{extra}",
                    )
                )
    return pd.DataFrame(rows)


def _trade(day: pd.Timestamp, *, wallet: str, amount: float, suffix: str) -> dict[str, object]:
    return {
        "wallet_address": wallet,
        "direction": "BUY",
        "amount_usd": float(amount),
        "price_timestamp": f"{day.date()}T12:00:00Z",
        "tx_hash": f"0xhash{suffix}",
    }


def _prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-15", "2024-03-15", freq="D")
    prices = [0.45 + (index % 9) * 0.006 + index * 0.0005 for index in range(len(dates))]
    return pd.DataFrame({"date": dates.date.astype(str), "price": prices})


def _write_event_seed(path: Path) -> None:
    frame = _events().copy()
    frame["event_time_utc"] = "12:00:00"
    frame["description"] = frame["title"] + "."
    frame["expected_direction"] = "neutral"
    frame["relevance_score"] = "0.9"
    frame = frame[
        [
            "event_id",
            "event_date",
            "event_time_utc",
            "title",
            "description",
            "event_type",
            "source_url",
            "expected_direction",
            "relevance_score",
        ]
    ]
    frame.to_csv(path, index=False)


def _write_db(db_path: Path, trades: pd.DataFrame, prices: pd.DataFrame) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE whale_trades (
                price_timestamp TEXT NOT NULL,
                tx_hash TEXT,
                wallet_address TEXT NOT NULL,
                market_id TEXT,
                direction TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                token_id TEXT,
                price_at_trade REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE polymarket_prices (
                price_timestamp TEXT NOT NULL,
                market_id TEXT NOT NULL,
                token_id TEXT,
                price REAL NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO whale_trades
                (price_timestamp, tx_hash, wallet_address, market_id, direction,
                 amount_usd, token_id, price_at_trade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["price_timestamp"],
                    row["tx_hash"],
                    row["wallet_address"],
                    "market",
                    row["direction"],
                    row["amount_usd"],
                    "token",
                    0.5,
                )
                for row in trades.to_dict(orient="records")
            ],
        )
        conn.executemany(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, market_id, token_id, price)
            VALUES (?, ?, ?, ?)
            """,
            [
                (f"{row['date']}T00:00:00Z", "market", "token", float(row["price"]))
                for row in prices.to_dict(orient="records")
            ],
        )
        conn.commit()
    finally:
        conn.close()
