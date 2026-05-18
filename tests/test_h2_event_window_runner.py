from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.event_study import (
    PRIMARY_DAILY_WINDOW,
    SECONDARY_DAILY_WINDOW,
)
from operations.analysis.run_h2_event_windows import (
    generate_h2_event_window_outputs,
    load_curated_events,
    load_daily_polymarket_prices,
    main,
)


def test_generate_h2_outputs_from_seed_and_prices(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    seed_path = tmp_path / "events.csv"
    output_dir = tmp_path / "results"
    _write_price_db(db_path)
    _write_event_seed(seed_path)

    result = generate_h2_event_window_outputs(
        db_path=db_path,
        events_csv_path=seed_path,
        output_dir=output_dir,
    )

    rows = pd.read_csv(result.rows_path)
    summary = pd.read_csv(result.summary_path)
    assert result.event_count == 1
    assert result.event_window_row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert set(rows["window_label"]) == {
        PRIMARY_DAILY_WINDOW.label,
        SECONDARY_DAILY_WINDOW.label,
    }
    assert set(summary["event_id"]) == {"evt_test"}
    assert "Test event" in set(summary["title"])
    assert {"final_cumulative_abnormal_change", "observed_days"}.issubset(
        summary.columns
    )


def test_runner_uses_seed_events_not_legacy_database_events(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    seed_path = tmp_path / "events.csv"
    output_dir = tmp_path / "results"
    _write_price_db(db_path, include_legacy_events=True)
    _write_event_seed(seed_path)

    generate_h2_event_window_outputs(
        db_path=db_path,
        events_csv_path=seed_path,
        output_dir=output_dir,
    )

    summary = pd.read_csv(output_dir / "h2_event_window_summary.csv")
    assert set(summary["event_id"]) == {"evt_test"}


def test_missing_database_returns_clear_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seed_path = tmp_path / "events.csv"
    _write_event_seed(seed_path)

    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--events",
            str(seed_path),
            "--output-dir",
            str(tmp_path / "results"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def test_invalid_seed_fields_fail_clearly(tmp_path: Path) -> None:
    seed_path = tmp_path / "events.csv"
    seed_path.write_text(
        "\n".join(
            [
                "event_id,event_date,event_time_utc,title,description,event_type,source_url,expected_direction,relevance_score",
                "evt_bad,2024-01-20,00:00:00,Missing source,Description,major_news,,neutral,0.5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing canonical fields"):
        load_curated_events(seed_path)


def test_load_daily_prices_rejects_ambiguous_series(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    _write_price_db(db_path, second_series=True)

    with pytest.raises(ValueError, match="Multiple Polymarket price series"):
        load_daily_polymarket_prices(
            db_path,
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 25),
        )


def test_h2_outputs_are_deterministic(tmp_path: Path) -> None:
    db_path = tmp_path / "thesis.db"
    seed_path = tmp_path / "events.csv"
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    _write_price_db(db_path)
    _write_event_seed(seed_path)

    generate_h2_event_window_outputs(
        db_path=db_path,
        events_csv_path=seed_path,
        output_dir=first_output,
    )
    generate_h2_event_window_outputs(
        db_path=db_path,
        events_csv_path=seed_path,
        output_dir=second_output,
    )

    assert (first_output / "h2_event_window_rows.csv").read_text(
        encoding="utf-8"
    ) == (second_output / "h2_event_window_rows.csv").read_text(encoding="utf-8")
    assert (first_output / "h2_event_window_summary.csv").read_text(
        encoding="utf-8"
    ) == (second_output / "h2_event_window_summary.csv").read_text(encoding="utf-8")


def _write_event_seed(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "event_id,event_date,event_time_utc,title,description,event_type,source_url,expected_direction,relevance_score",
                "evt_test,2024-01-20,00:00:00,Test event,Description,major_news,https://example.com,neutral,0.8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_price_db(
    path: Path,
    *,
    include_legacy_events: bool = False,
    second_series: bool = False,
) -> None:
    conn = sqlite3.connect(path)
    try:
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
        start = date(2024, 1, 1)
        rows = []
        for index in range(30):
            current_date = start + timedelta(days=index)
            price = 0.40 + (index * 0.003)
            if current_date == date(2024, 1, 20):
                price += 0.04
            rows.append(
                (
                    f"{current_date.isoformat()}T00:00:00Z",
                    "market-a",
                    "token-a",
                    price,
                )
            )
            if second_series:
                rows.append(
                    (
                        f"{current_date.isoformat()}T00:00:00Z",
                        "market-b",
                        "token-b",
                        0.60,
                    )
                )
        conn.executemany(
            """
            INSERT INTO polymarket_prices
                (price_timestamp, market_id, token_id, price)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        if include_legacy_events:
            conn.execute(
                """
                CREATE TABLE events_timeline (
                    event_id TEXT,
                    event_date TEXT,
                    title TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO events_timeline (event_id, event_date, title)
                VALUES ('legacy_event', '2024-01-19', 'Legacy DB event')
                """
            )
        conn.commit()
    finally:
        conn.close()
