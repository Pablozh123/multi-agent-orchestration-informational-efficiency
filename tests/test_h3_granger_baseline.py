from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.h3_granger_baseline import (
    CORRELATION_COLUMNS,
    GRANGER_COLUMNS,
    MODEL_SERIES_COLUMNS,
    build_h3_granger_series,
    compute_granger_results,
    compute_lead_lag_correlations,
    generate_h3_granger_baseline,
    main,
)


def test_build_h3_granger_series_aligns_price_and_activity_changes() -> None:
    series = build_h3_granger_series(_toy_prices(), _toy_activity())

    assert tuple(series.columns) == MODEL_SERIES_COLUMNS
    assert set(series["tier"]) == {"tier_1_top_1pct", "tier_2_top_5pct"}
    assert series["price_change"].notna().all()
    assert series["activity_change"].notna().all()
    assert series["date"].min() == "2024-01-02"


def test_compute_lead_lag_correlations_returns_selected_lags() -> None:
    series = build_h3_granger_series(_toy_prices(), _toy_activity())

    correlations = compute_lead_lag_correlations(series, max_lag_days=2)

    assert tuple(correlations.columns) == CORRELATION_COLUMNS
    assert len(correlations) == 2 * 3
    assert set(correlations["lag_days"]) == {0, 1, 2}
    assert set(correlations["status"]) == {"ok"}


def test_compute_granger_results_returns_rows_for_each_tier_and_lag() -> None:
    series = build_h3_granger_series(_toy_prices(), _toy_activity())

    granger = compute_granger_results(series, max_lag_days=2)

    assert tuple(granger.columns) == GRANGER_COLUMNS
    assert len(granger) == 2 * 2
    assert set(granger["lag_days"]) == {1, 2}
    assert granger["observation_count"].min() >= 9
    assert granger["status"].isin({"ok", "error:ValueError"}).all()


def test_compute_granger_results_marks_constant_activity() -> None:
    series = build_h3_granger_series(_toy_prices(), _constant_activity())

    granger = compute_granger_results(series, max_lag_days=1)

    assert set(granger["status"]) == {"insufficient_activity_variation"}
    assert granger["p_value"].isna().all()


def test_generate_h3_granger_baseline_writes_outputs(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    activity_path = tmp_path / "activity.csv"
    correlations_path = tmp_path / "correlations.csv"
    granger_path = tmp_path / "granger.csv"
    metadata_path = tmp_path / "metadata.json"
    _write_price_db(db_path, _toy_prices())
    _toy_activity().to_csv(activity_path, index=False)

    result = generate_h3_granger_baseline(
        db_path=db_path,
        activity_path=activity_path,
        correlations_path=correlations_path,
        granger_path=granger_path,
        metadata_path=metadata_path,
        max_lag_days=2,
    )

    correlations = pd.read_csv(correlations_path)
    granger = pd.read_csv(granger_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.model_row_count == 18
    assert len(correlations) == 6
    assert len(granger) == 4
    assert metadata["output"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["does_not_use_llms"] is True


def test_cli_returns_clear_error_for_missing_database(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity_path = tmp_path / "activity.csv"
    _toy_activity().to_csv(activity_path, index=False)

    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--activity",
            str(activity_path),
            "--correlations-output",
            str(tmp_path / "correlations.csv"),
            "--granger-output",
            str(tmp_path / "granger.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
            "--max-lag-days",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _toy_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    prices = [0.50, 0.51, 0.49, 0.53, 0.52, 0.56, 0.55, 0.57, 0.58, 0.56]
    return pd.DataFrame({"date": dates.date.astype(str), "price": prices})


def _toy_activity() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=10, freq="D").date.astype(str)
    rows: list[dict[str, object]] = []
    tier_values = {
        "tier_1_top_1pct": [10, 12, 9, 20, 11, 22, 13, 18, 17, 23],
        "tier_2_top_5pct": [4, 6, 5, 9, 7, 11, 8, 10, 9, 12],
    }
    for tier, values in tier_values.items():
        for day, value in zip(dates, values):
            rows.append(
                {
                    "date": day,
                    "tier": tier,
                    "trade_rows": int(value),
                    "active_wallets": max(1, int(value // 4)),
                    "total_amount_usd": float(value * 100.0),
                    "buy_amount_usd": float(value * 100.0),
                    "sell_amount_usd": 0.0,
                    "net_amount_usd": float(value * 100.0),
                }
            )
    return pd.DataFrame(rows)


def _constant_activity() -> pd.DataFrame:
    activity = _toy_activity()
    activity["total_amount_usd"] = 100.0
    activity["buy_amount_usd"] = 100.0
    activity["net_amount_usd"] = 100.0
    return activity


def _write_price_db(path: Path, prices: pd.DataFrame) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE polymarket_prices (
                price_timestamp TEXT NOT NULL,
                market_id TEXT NOT NULL,
                token_id TEXT NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, market_id, token_id, price)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    f"{row['date']}T00:00:00Z",
                    "market",
                    "token",
                    float(row["price"]),
                )
                for row in prices.to_dict(orient="records")
            ],
        )
        conn.commit()
    finally:
        conn.close()
