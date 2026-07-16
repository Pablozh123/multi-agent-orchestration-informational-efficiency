from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_popular_vote_extension import (
    CLOB_BASE_URL,
    FIVETHIRTYEIGHT_SOURCE,
    TARGET_OUTCOME,
    build_cases,
    fetch_daily_prices,
    generate_h1_popular_vote_outputs,
    mock_gamma_event,
    poll_margin_to_probability,
    read_national_poll_shares,
    select_market,
    target_token_id,
    validate_cases,
)


def test_poll_margin_to_probability_is_centered_and_monotonic() -> None:
    assert poll_margin_to_probability(0.0) == pytest.approx(0.5)
    assert poll_margin_to_probability(4.0) > 0.5
    assert poll_margin_to_probability(-4.0) < 0.5
    assert poll_margin_to_probability(4.0) == pytest.approx(
        1.0 - poll_margin_to_probability(-4.0)
    )


def test_generate_h1_popular_vote_outputs_mock(tmp_path: Path) -> None:
    db_path = _write_poll_db(tmp_path)

    result = generate_h1_popular_vote_outputs(
        source="mock",
        db_path=db_path,
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    cases = pd.read_csv(tmp_path / "cases.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.case_count == 3
    assert len(cases) == 3
    assert len(summary) >= 8
    assert metadata["method"]["uses_raw_poll_shares_directly_as_probabilities"] is False
    assert metadata["outputs"]["independent_resolved_outcome_count"] == 1
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert set(cases["lower_loss_source"]).issubset({"polymarket", "poll_derived", "tie"})
    assert cases["poll_derived_probability"].between(0.0, 1.0).all()
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_read_national_poll_shares_requires_trump_harris_overlap(tmp_path: Path) -> None:
    db_path = tmp_path / "missing_harris.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE poll_forecasts (
                date TEXT,
                source TEXT,
                candidate TEXT,
                probability REAL
            )
            """
        )
        conn.execute(
            "INSERT INTO poll_forecasts VALUES (?, ?, ?, ?)",
            ("2024-07-24", FIVETHIRTYEIGHT_SOURCE, "trump", 0.45),
        )

    with pytest.raises(ValueError, match="overlapping"):
        read_national_poll_shares(db_path)


def test_fetch_daily_prices_uses_public_clob_endpoint() -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={
                    "history": [
                        {"t": 1721779200, "p": 0.30},
                        {"t": 1721862000, "p": 0.32},
                        {"t": 1721865600, "p": 0.31},
                    ]
                },
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        prices = fetch_daily_prices(
            client,
            token_id="token-popular-vote-trump-yes",
            start_date="2024-07-24",
            end_date="2024-07-24",
        )

    assert len(prices) == 2
    assert prices["polymarket_probability"].between(0.0, 1.0).all()
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_build_cases_rejects_invalid_probability() -> None:
    poll_rows = pd.DataFrame(
        [
            {"date": "2024-07-24", "trump": 0.45, "harris": 0.47},
        ]
    )
    prices = pd.DataFrame(
        [
            {
                "date": "2024-07-24",
                "polymarket_observed_at_utc": "2024-07-24T23:00:00Z",
                "polymarket_probability": 1.2,
            }
        ]
    )
    market = select_market(mock_gamma_event(), "will-donald-trump-win-the-popular-vote-in-the-2024-presidential-election")
    token_id = target_token_id(market, TARGET_OUTCOME)

    cases = build_cases(
        poll_rows=poll_rows,
        prices=prices,
        market=market,
        token_id=token_id,
    )

    with pytest.raises(ValueError, match="polymarket_probability"):
        validate_cases(cases)


def _write_poll_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "polls.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE poll_forecasts (
                date TEXT,
                source TEXT,
                candidate TEXT,
                probability REAL
            )
            """
        )
        conn.executemany(
            "INSERT INTO poll_forecasts VALUES (?, ?, ?, ?)",
            [
                ("2024-07-24", FIVETHIRTYEIGHT_SOURCE, "trump", 0.44),
                ("2024-07-24", FIVETHIRTYEIGHT_SOURCE, "harris", 0.48),
                ("2024-07-25", FIVETHIRTYEIGHT_SOURCE, "trump", 0.45),
                ("2024-07-25", FIVETHIRTYEIGHT_SOURCE, "harris", 0.47),
                ("2024-07-26", FIVETHIRTYEIGHT_SOURCE, "trump", 0.46),
                ("2024-07-26", FIVETHIRTYEIGHT_SOURCE, "harris", 0.46),
            ],
        )
    return db_path
