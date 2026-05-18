from __future__ import annotations

import pandas as pd
import pytest

from operations.analysis.event_study import (
    EventWindow,
    compute_daily_price_changes,
    compute_event_window_car,
    summarize_event_window_car,
)


def test_compute_daily_price_changes_uses_probability_price_differences() -> None:
    prices = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "price": [0.50, 0.55, 0.53],
        }
    )

    result = compute_daily_price_changes(prices)

    assert list(result["date"].astype(str)) == ["2024-01-02", "2024-01-03"]
    assert list(result["price_change"]) == pytest.approx([0.05, -0.02])


def test_compute_event_window_car_matches_toy_example() -> None:
    prices = pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
            "price": [0.50, 0.51, 0.52, 0.57, 0.60],
        }
    )
    events = pd.DataFrame(
        {"event_id": ["event-a"], "event_date": ["2024-01-04"]}
    )

    result = compute_event_window_car(
        prices,
        events,
        window=EventWindow(0, 1, "toy_window"),
        estimation_window_days=(-2, -1),
    )

    assert list(result["relative_day"]) == [0, 1]
    assert list(result["price_change"]) == pytest.approx([0.05, 0.03])
    assert list(result["expected_change"]) == pytest.approx([0.01, 0.01])
    assert list(result["abnormal_change"]) == pytest.approx([0.04, 0.02])
    assert list(result["cumulative_abnormal_change"]) == pytest.approx([0.04, 0.06])
    assert list(result["estimation_observations"]) == [2, 2]


def test_summarize_event_window_car_returns_final_car() -> None:
    event_rows = pd.DataFrame(
        {
            "event_id": ["event-a", "event-a"],
            "window_label": ["toy", "toy"],
            "relative_day": [0, 1],
            "cumulative_abnormal_change": [0.04, 0.06],
            "estimation_observations": [2, 2],
        }
    )

    summary = summarize_event_window_car(event_rows)

    assert summary.iloc[0]["event_id"] == "event-a"
    assert summary.iloc[0]["observed_days"] == 2
    assert summary.iloc[0]["final_cumulative_abnormal_change"] == pytest.approx(0.06)
    assert summary.iloc[0]["estimation_observations"] == 2


def test_event_window_car_uses_zero_expected_change_without_estimation_rows() -> None:
    prices = pd.DataFrame(
        {"date": ["2024-01-01", "2024-01-02"], "price": [0.40, 0.45]}
    )
    events = pd.DataFrame(
        {"event_id": ["event-a"], "event_date": ["2024-01-02"]}
    )

    result = compute_event_window_car(
        prices,
        events,
        window=EventWindow(0, 0, "same_day"),
        estimation_window_days=(-14, -2),
    )

    assert result.iloc[0]["expected_change"] == pytest.approx(0.0)
    assert result.iloc[0]["cumulative_abnormal_change"] == pytest.approx(0.05)
    assert result.iloc[0]["estimation_observations"] == 0


def test_event_study_validates_inputs() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        compute_daily_price_changes(
            pd.DataFrame({"date": ["2024-01-01"], "price": [1.2]})
        )

    with pytest.raises(ValueError, match="missing required columns"):
        compute_event_window_car(
            pd.DataFrame({"date": ["2024-01-01"], "price": [0.5]}),
            pd.DataFrame({"event_date": ["2024-01-01"]}),
        )

    with pytest.raises(ValueError, match="start_day"):
        EventWindow(2, 1, "bad")
