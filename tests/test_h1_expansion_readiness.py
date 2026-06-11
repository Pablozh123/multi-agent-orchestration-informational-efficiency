from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd

from operations.analysis.h1_expansion_readiness import (
    build_readiness_rows,
    generate_h1_expansion_readiness_outputs,
    inspect_local_coverage,
)


def test_inspect_local_coverage_identifies_polymarket_tail(tmp_path: Path) -> None:
    db_path = _write_db(tmp_path)

    coverage = inspect_local_coverage(
        db_path=db_path,
        current_h1_end_date="2024-01-02",
    )

    assert coverage["polymarket_daily_rows"] == 3
    assert coverage["fivethirtyeight_probability_rows"] == 2
    assert coverage["polymarket_extra_daily_rows"] == 1
    assert coverage["fivethirtyeight_extra_probability_rows"] == 0


def test_build_readiness_rows_blocks_unpaired_tail() -> None:
    brier = pd.DataFrame(
        [
            {"date": "2024-01-01"},
            {"date": "2024-01-02"},
        ]
    )
    coverage = {
        "polymarket_extra_daily_rows": 1,
        "fivethirtyeight_extra_probability_rows": 0,
    }

    readiness = build_readiness_rows(
        brier=brier,
        coverage=coverage,
        swiss_poll_rows=2,
    )

    current = readiness[
        readiness["candidate_id"] == "current_us_2024_h1_overlap"
    ].iloc[0]
    pm_tail = readiness[
        readiness["candidate_id"] == "local_polymarket_tail_after_h1_end"
    ].iloc[0]
    raw_polls = readiness[
        readiness["candidate_id"] == "official_538_polling_averages_2024"
    ].iloc[0]

    assert bool(current["compatible_for_h1_brier_now"]) is True
    assert int(current["independent_resolved_outcomes_now"]) == 1
    assert int(pm_tail["local_available_rows"]) == 1
    assert int(pm_tail["additional_pair_rows_now"]) == 0
    assert bool(pm_tail["compatible_for_h1_brier_now"]) is False
    assert "probability_comparator" in str(pm_tail["status"])
    assert bool(raw_polls["compatible_for_h1_brier_now"]) is False
    assert "probability transformation" in str(raw_polls["required_next_step"])


def test_generate_h1_expansion_readiness_outputs(tmp_path: Path) -> None:
    db_path = _write_db(tmp_path)
    brier_path = tmp_path / "h1_brier_scores.csv"
    poll_path = tmp_path / "swiss_polls.csv"
    pd.DataFrame(
        [
            {"date": "2024-01-01", "bs_polymarket": 0.1},
            {"date": "2024-01-02", "bs_polymarket": 0.2},
        ]
    ).to_csv(brier_path, index=False)
    pd.DataFrame([{"poll_id": "poll_a"}, {"poll_id": "poll_b"}]).to_csv(
        poll_path,
        index=False,
    )

    result = generate_h1_expansion_readiness_outputs(
        db_path=db_path,
        brier_input=brier_path,
        swiss_poll_input=poll_path,
        readiness_output=tmp_path / "readiness.csv",
        figure_output=tmp_path / "readiness.png",
        metadata_output=tmp_path / "readiness.json",
    )

    metadata = json.loads((tmp_path / "readiness.json").read_text(encoding="utf-8"))
    readiness = pd.read_csv(tmp_path / "readiness.csv")
    image = mpimg.imread(tmp_path / "readiness.png")

    assert result.current_h1_pair_rows == 2
    assert result.polymarket_extra_daily_rows == 1
    assert result.fivethirtyeight_extra_probability_rows == 0
    assert result.additional_pair_rows_now == 0
    assert result.eligible_independent_outcome_count == 1
    assert len(readiness) == 6
    assert metadata["outputs"]["compatible_additional_h1_pair_rows_now"] == 0
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["limitations"]["raw_poll_shares_require_documented_probability_transform"]
    assert image.size > 0
    assert float(image.std()) > 0.0


def _write_db(root: Path) -> Path:
    db_path = root / "thesis.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE polymarket_prices (
                price_timestamp TEXT NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE poll_forecasts (
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                candidate TEXT NOT NULL,
                probability REAL NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO polymarket_prices (price_timestamp, price) VALUES (?, ?)",
            [
                ("2024-01-01T00:00:00.000000Z", 0.55),
                ("2024-01-02T00:00:00.000000Z", 0.56),
                ("2024-01-03T00:00:00.000000Z", 0.57),
            ],
        )
        conn.executemany(
            """
            INSERT INTO poll_forecasts (date, source, candidate, probability)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("2024-01-01", "fivethirtyeight", "trump", 0.48),
                ("2024-01-02", "fivethirtyeight", "trump", 0.49),
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return db_path
