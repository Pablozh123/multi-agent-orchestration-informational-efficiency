"""Deterministic H2 event-window helpers for daily Polymarket prices.

The functions operate on in-memory pandas DataFrames so they remain testable
and independent from external APIs or LLM interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd


@dataclass(frozen=True)
class EventWindow:
    """Calendar-day event window relative to an event date."""

    start_day: int
    end_day: int
    label: str

    def __post_init__(self) -> None:
        if self.start_day > self.end_day:
            raise ValueError("EventWindow start_day must be <= end_day")


PRIMARY_DAILY_WINDOW = EventWindow(0, 1, "primary_0d_to_1d")
SECONDARY_DAILY_WINDOW = EventWindow(-1, 3, "secondary_minus_1d_to_3d")
DEFAULT_ESTIMATION_WINDOW = (-14, -2)


def compute_daily_price_changes(
    prices: pd.DataFrame,
    *,
    date_col: str = "date",
    price_col: str = "price",
) -> pd.DataFrame:
    """Return sorted daily price changes for probability prices.

    Prices must be in the inclusive range [0, 1]. The first row has no previous
    observation and is removed from the returned frame.
    """

    _require_columns(prices, (date_col, price_col), "prices")
    frame = prices[[date_col, price_col]].copy()
    frame[date_col] = _to_dates(frame[date_col], date_col)
    frame[price_col] = pd.to_numeric(frame[price_col], errors="raise")
    if not frame[price_col].between(0.0, 1.0).all():
        raise ValueError(f"{price_col} must be between 0 and 1")

    frame = frame.sort_values(date_col).drop_duplicates(date_col, keep="last")
    frame["price_change"] = frame[price_col].diff()
    return frame.dropna(subset=["price_change"]).reset_index(drop=True)


def compute_event_window_car(
    prices: pd.DataFrame,
    events: pd.DataFrame,
    *,
    window: EventWindow = PRIMARY_DAILY_WINDOW,
    estimation_window_days: tuple[int, int] = DEFAULT_ESTIMATION_WINDOW,
    date_col: str = "date",
    price_col: str = "price",
    event_id_col: str = "event_id",
    event_date_col: str = "event_date",
) -> pd.DataFrame:
    """Compute cumulative abnormal price changes for each event.

    Expected daily change is the mean daily price change in the pre-event
    estimation window. If no pre-event observations exist, expected change is
    set to 0.0 and the row is marked with `estimation_observations = 0`.
    """

    _require_columns(events, (event_id_col, event_date_col), "events")
    if estimation_window_days[0] > estimation_window_days[1]:
        raise ValueError("estimation_window_days start must be <= end")

    changes = compute_daily_price_changes(
        prices,
        date_col=date_col,
        price_col=price_col,
    )
    event_frame = events[[event_id_col, event_date_col]].copy()
    event_frame[event_date_col] = _to_dates(event_frame[event_date_col], event_date_col)

    rows: list[dict[str, object]] = []
    for event in event_frame.itertuples(index=False):
        event_id = getattr(event, event_id_col)
        event_date = getattr(event, event_date_col)
        expected_change, estimation_observations = _expected_change(
            changes,
            event_date=event_date,
            estimation_window_days=estimation_window_days,
            date_col=date_col,
        )
        cumulative = 0.0
        for offset in range(window.start_day, window.end_day + 1):
            target_date = event_date + timedelta(days=offset)
            day_row = changes.loc[changes[date_col] == target_date]
            if day_row.empty:
                continue
            observed_change = float(day_row.iloc[0]["price_change"])
            abnormal_change = observed_change - expected_change
            cumulative += abnormal_change
            rows.append(
                {
                    "event_id": event_id,
                    "window_label": window.label,
                    "event_date": event_date.isoformat(),
                    "date": target_date.isoformat(),
                    "relative_day": offset,
                    "price_change": observed_change,
                    "expected_change": expected_change,
                    "abnormal_change": abnormal_change,
                    "cumulative_abnormal_change": cumulative,
                    "estimation_observations": estimation_observations,
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "window_label",
            "event_date",
            "date",
            "relative_day",
            "price_change",
            "expected_change",
            "abnormal_change",
            "cumulative_abnormal_change",
            "estimation_observations",
        ],
    )


def summarize_event_window_car(event_rows: pd.DataFrame) -> pd.DataFrame:
    """Return one final CAR row per event and window."""

    _require_columns(
        event_rows,
        (
            "event_id",
            "window_label",
            "relative_day",
            "cumulative_abnormal_change",
            "estimation_observations",
        ),
        "event_rows",
    )
    if event_rows.empty:
        return pd.DataFrame(
            columns=[
                "event_id",
                "window_label",
                "observed_days",
                "final_cumulative_abnormal_change",
                "estimation_observations",
            ]
        )

    sorted_rows = event_rows.sort_values(["event_id", "window_label", "relative_day"])
    final_rows = sorted_rows.groupby(["event_id", "window_label"], as_index=False).tail(1)
    observed_days = (
        sorted_rows.groupby(["event_id", "window_label"], as_index=False)
        .size()
        .rename(columns={"size": "observed_days"})
    )
    summary = final_rows[
        [
            "event_id",
            "window_label",
            "cumulative_abnormal_change",
            "estimation_observations",
        ]
    ].rename(
        columns={"cumulative_abnormal_change": "final_cumulative_abnormal_change"}
    )
    return observed_days.merge(summary, on=["event_id", "window_label"], how="left")


def _expected_change(
    changes: pd.DataFrame,
    *,
    event_date: date,
    estimation_window_days: tuple[int, int],
    date_col: str,
) -> tuple[float, int]:
    start = event_date + timedelta(days=estimation_window_days[0])
    end = event_date + timedelta(days=estimation_window_days[1])
    estimation_rows = changes[
        (changes[date_col] >= start) & (changes[date_col] <= end)
    ]
    if estimation_rows.empty:
        return 0.0, 0
    return float(estimation_rows["price_change"].mean()), int(len(estimation_rows))


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _to_dates(values: pd.Series, column_name: str) -> pd.Series:
    parsed = pd.to_datetime(values, errors="raise", utc=False)
    if parsed.isna().any():
        raise ValueError(f"{column_name} must parse to dates")
    return parsed.dt.date
