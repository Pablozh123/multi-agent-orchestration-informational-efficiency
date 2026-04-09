"""Pre-Computation Layer fuer die Iceberg-Architektur (CLAUDE.md v2.1 §8.2).

Berechnet deterministische Aggregate aus data/thesis.db, persistiert die
Resultate in analysis_summaries und exportiert einen kompakten JSON-Snapshot
nach data/summaries.json fuer den Prompt-Kontext der Agenten.

Keine LLM-Calls, keine HTTP-Requests — reines numpy/pandas/sqlite.

Aufruf:
    python -m operations.analysis.generate_summaries
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DB_PATH = Path("data/thesis.db")
JSON_EXPORT_PATH = Path("data/summaries.json")


@dataclass(frozen=True)
class SummaryRow:
    """Eine Zeile fuer analysis_summaries."""

    table_name: str
    metric_name: str
    date_range_start: str | None
    date_range_end: str | None
    value_json: str  # serialized JSON payload
    computed_at: str  # ISO 8601 UTC


# --- DB helpers ----------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_df(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    """Lies eine komplette Tabelle als DataFrame."""
    return pd.read_sql(f"SELECT * FROM {table}", conn)


def _safe_parse_ts(series: pd.Series) -> pd.Series:
    """Parse timestamps permissively (fallback to dateutil for messy formats).

    Some rows in whale_trades have 'YYYY-MM-DD HH:MM:SS.000 UTCZ' which is
    not strict ISO 8601; pandas handles it if we strip the literal 'UTCZ'.
    """
    cleaned = series.astype(str).str.replace(" UTCZ", "Z", regex=False)
    return pd.to_datetime(cleaned, utc=True, errors="coerce")


# --- Metric computations -------------------------------------------------


def compute_weekly_avg_price(conn: sqlite3.Connection) -> list[SummaryRow]:
    """AVG(price) pro ISO-Kalenderwoche aus polymarket_prices."""
    df = _load_df(conn, "polymarket_prices")
    if df.empty:
        return []
    df["ts"] = _safe_parse_ts(df["price_timestamp"])
    df = df.dropna(subset=["ts"])
    df["iso_week"] = df["ts"].dt.strftime("%G-W%V")
    grouped = (
        df.groupby(["market_id", "token_id", "iso_week"])
        .agg(avg_price=("price", "mean"), samples=("price", "size"))
        .reset_index()
    )
    now = _now_utc()
    rows: list[SummaryRow] = []
    for market, group in grouped.groupby(["market_id", "token_id"]):
        payload = group[["iso_week", "avg_price", "samples"]].to_dict(orient="records")
        rows.append(
            SummaryRow(
                table_name="polymarket_prices",
                metric_name="weekly_avg_price",
                date_range_start=df["ts"].min().isoformat(),
                date_range_end=df["ts"].max().isoformat(),
                value_json=json.dumps(
                    {"market_id": market[0], "token_id": market[1], "weeks": payload}
                ),
                computed_at=now,
            )
        )
    return rows


def compute_price_volatility(conn: sqlite3.Connection) -> list[SummaryRow]:
    """Rolling 7-Tage-StdDev des Preises pro Markt/Token."""
    df = _load_df(conn, "polymarket_prices")
    if df.empty:
        return []
    df["ts"] = _safe_parse_ts(df["price_timestamp"])
    df = df.dropna(subset=["ts"]).sort_values("ts")

    rows: list[SummaryRow] = []
    now = _now_utc()
    for (market_id, token_id), group in df.groupby(["market_id", "token_id"]):
        # Daily mean first, then 7-day rolling std
        daily = (
            group.set_index("ts")["price"].resample("D").mean().dropna()
        )
        if len(daily) < 2:
            continue
        rolling_std = daily.rolling(window=7, min_periods=2).std().dropna()
        payload = [
            {"date": idx.date().isoformat(), "volatility": float(val)}
            for idx, val in rolling_std.items()
        ]
        rows.append(
            SummaryRow(
                table_name="polymarket_prices",
                metric_name="price_volatility",
                date_range_start=daily.index.min().isoformat(),
                date_range_end=daily.index.max().isoformat(),
                value_json=json.dumps(
                    {
                        "market_id": market_id,
                        "token_id": token_id,
                        "window_days": 7,
                        "series": payload,
                    }
                ),
                computed_at=now,
            )
        )
    return rows


def compute_whale_net_volume(conn: sqlite3.Connection) -> list[SummaryRow]:
    """Tagliches Netto-Volumen (BUY - SELL) aus whale_trades."""
    df = _load_df(conn, "whale_trades")
    if df.empty:
        return []
    df["ts"] = _safe_parse_ts(df["price_timestamp"])
    df = df.dropna(subset=["ts"])
    df["day"] = df["ts"].dt.date
    df["signed"] = np.where(df["direction"] == "BUY", df["amount_usd"], -df["amount_usd"])
    daily = df.groupby("day")["signed"].agg(["sum", "count"]).reset_index()
    daily.columns = ["day", "net_usd", "trade_count"]
    payload = [
        {
            "day": row["day"].isoformat(),
            "net_usd": float(row["net_usd"]),
            "trade_count": int(row["trade_count"]),
        }
        for _, row in daily.iterrows()
    ]
    return [
        SummaryRow(
            table_name="whale_trades",
            metric_name="whale_net_volume",
            date_range_start=daily["day"].min().isoformat(),
            date_range_end=daily["day"].max().isoformat(),
            value_json=json.dumps({"days": payload}),
            computed_at=_now_utc(),
        )
    ]


def compute_whale_anomaly_flags(conn: sqlite3.Connection) -> list[SummaryRow]:
    """Z-Score ueber 30-Tage-Rolling-Mean des taglichen Netto-Volumens.

    Flagt Tage mit |z| > 2 als Anomalie.
    """
    df = _load_df(conn, "whale_trades")
    if df.empty:
        return []
    df["ts"] = _safe_parse_ts(df["price_timestamp"])
    df = df.dropna(subset=["ts"])
    df["day"] = df["ts"].dt.date
    df["signed"] = np.where(df["direction"] == "BUY", df["amount_usd"], -df["amount_usd"])
    daily = (
        df.groupby("day")["signed"]
        .sum()
        .sort_index()
        .rename("net_usd")
        .to_frame()
    )
    daily.index = pd.to_datetime(daily.index)

    rolling_mean = daily["net_usd"].rolling(window=30, min_periods=5).mean()
    rolling_std = daily["net_usd"].rolling(window=30, min_periods=5).std()
    daily["z_score"] = (daily["net_usd"] - rolling_mean) / rolling_std
    anomalies = daily[daily["z_score"].abs() > 2].dropna()

    payload = [
        {
            "day": idx.date().isoformat(),
            "net_usd": float(row["net_usd"]),
            "z_score": float(row["z_score"]),
        }
        for idx, row in anomalies.iterrows()
    ]
    return [
        SummaryRow(
            table_name="whale_trades",
            metric_name="whale_anomaly",
            date_range_start=daily.index.min().date().isoformat(),
            date_range_end=daily.index.max().date().isoformat(),
            value_json=json.dumps(
                {"window_days": 30, "threshold_sigma": 2, "flagged": payload}
            ),
            computed_at=_now_utc(),
        )
    ]


def compute_sentiment_daily(conn: sqlite3.Connection) -> list[SummaryRow]:
    """AVG(sentiment), COUNT pro Tag aus sentiment_scores."""
    df = _load_df(conn, "sentiment_scores")
    if df.empty:
        return []
    df["ts"] = _safe_parse_ts(df["timestamp"])
    df = df.dropna(subset=["ts"])
    df["day"] = df["ts"].dt.date
    daily = df.groupby("day").agg(
        avg_sentiment=("sentiment", "mean"),
        source_count=("sentiment", "size"),
    ).reset_index()
    payload = [
        {
            "day": row["day"].isoformat(),
            "avg_sentiment": float(row["avg_sentiment"]),
            "source_count": int(row["source_count"]),
        }
        for _, row in daily.iterrows()
    ]
    return [
        SummaryRow(
            table_name="sentiment_scores",
            metric_name="sentiment_daily",
            date_range_start=daily["day"].min().isoformat(),
            date_range_end=daily["day"].max().isoformat(),
            value_json=json.dumps({"days": payload}),
            computed_at=_now_utc(),
        )
    ]


def compute_brier_score_windows(conn: sqlite3.Connection) -> list[SummaryRow]:
    """Brier Score pro Zeitfenster — blockiert solange poll_forecasts leer ist."""
    polls = _load_df(conn, "poll_forecasts")
    if polls.empty:
        print("  [SKIP] compute_brier_score_windows: poll_forecasts is empty "
              "(DATA-03/04 gap closure pending)")
        return []
    # poll_forecasts has data; compute Brier per source per month against market
    prices = _load_df(conn, "polymarket_prices")
    if prices.empty:
        print("  [SKIP] compute_brier_score_windows: polymarket_prices empty")
        return []

    prices["ts"] = _safe_parse_ts(prices["price_timestamp"])
    prices = prices.dropna(subset=["ts"])
    polls["ts"] = pd.to_datetime(polls["date"], errors="coerce", utc=True)
    polls = polls.dropna(subset=["ts"])

    # Market daily close (last known price per day)
    market_daily = (
        prices.sort_values("ts")
        .set_index("ts")["price"]
        .resample("D")
        .last()
        .dropna()
    )

    rows: list[SummaryRow] = []
    # Simplified: assume outcome = 1 if Trump won (historical fact for 2024);
    # placeholder until we have an outcomes table
    outcome = 1.0
    for source, group in polls.groupby("source"):
        group = group.sort_values("ts")
        brier = float(np.mean((group["probability"] - outcome) ** 2))
        rows.append(
            SummaryRow(
                table_name="poll_forecasts",
                metric_name="brier_score",
                date_range_start=group["ts"].min().isoformat(),
                date_range_end=group["ts"].max().isoformat(),
                value_json=json.dumps(
                    {"source": source, "brier": brier, "n": int(len(group))}
                ),
                computed_at=_now_utc(),
            )
        )
    return rows


def compute_poll_market_delta(conn: sqlite3.Connection) -> list[SummaryRow]:
    """Logit-Differenz zwischen Poll-Forecast und Markt-Preis — blockiert wenn polls leer."""
    polls = _load_df(conn, "poll_forecasts")
    if polls.empty:
        print("  [SKIP] compute_poll_market_delta: poll_forecasts is empty")
        return []
    # Compute real logit delta once polls are populated; stub for now
    return []


# --- Persistence ---------------------------------------------------------


def persist_summaries(conn: sqlite3.Connection, rows: list[SummaryRow]) -> int:
    """Schreibt alle SummaryRows nach analysis_summaries. Idempotent per Metrik+Range."""
    if not rows:
        return 0
    # Delete existing summaries for the same (table_name, metric_name) pairs
    # so re-runs don't accumulate duplicates.
    pairs = {(r.table_name, r.metric_name) for r in rows}
    for table, metric in pairs:
        conn.execute(
            "DELETE FROM analysis_summaries WHERE table_name = ? AND metric_name = ?",
            (table, metric),
        )
    conn.executemany(
        """
        INSERT INTO analysis_summaries
            (table_name, metric_name, date_range_start, date_range_end,
             value_json, computed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r.table_name,
                r.metric_name,
                r.date_range_start,
                r.date_range_end,
                r.value_json,
                r.computed_at,
            )
            for r in rows
        ],
    )
    conn.commit()
    return len(rows)


def export_json(conn: sqlite3.Connection, path: Path = JSON_EXPORT_PATH) -> dict[str, Any]:
    """Exportiert die letzten Summaries pro Metrik als JSON-Snapshot."""
    df = pd.read_sql(
        """
        SELECT table_name, metric_name, date_range_start, date_range_end,
               value_json, computed_at
        FROM analysis_summaries
        ORDER BY computed_at DESC
        """,
        conn,
    )
    snapshot: dict[str, list[dict[str, Any]]] = {}
    for _, row in df.iterrows():
        key = f"{row['table_name']}.{row['metric_name']}"
        snapshot.setdefault(key, []).append(
            {
                "date_range_start": row["date_range_start"],
                "date_range_end": row["date_range_end"],
                "computed_at": row["computed_at"],
                "value": json.loads(row["value_json"]),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return snapshot


# --- Orchestration -------------------------------------------------------


def main() -> int:
    if not DB_PATH.exists():
        print(f"FATAL: {DB_PATH} not found")
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    all_rows: list[SummaryRow] = []

    metric_funcs = [
        ("weekly_avg_price", compute_weekly_avg_price),
        ("price_volatility", compute_price_volatility),
        ("whale_net_volume", compute_whale_net_volume),
        ("whale_anomaly", compute_whale_anomaly_flags),
        ("sentiment_daily", compute_sentiment_daily),
        ("brier_score", compute_brier_score_windows),
        ("poll_market_delta", compute_poll_market_delta),
    ]

    print(f"Generating pre-computed summaries from {DB_PATH}\n")
    for name, fn in metric_funcs:
        try:
            rows = fn(conn)
            print(f"  [OK]   {name}: {len(rows)} summary row(s)")
            all_rows.extend(rows)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")

    written = persist_summaries(conn, all_rows)
    print(f"\nPersisted {written} rows to analysis_summaries")

    snapshot = export_json(conn)
    print(f"Exported {JSON_EXPORT_PATH} with {len(snapshot)} metric keys")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
