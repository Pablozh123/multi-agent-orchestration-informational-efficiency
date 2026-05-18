from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.persist_h2_summaries import (
    METRIC_NAME,
    RUN_ID,
    SUMMARY_TYPE,
    TABLE_NAME,
    build_h2_summary_records,
    load_h2_summary_csv,
    main,
    persist_h2_summaries,
)


def test_load_h2_summary_csv_validates_required_shape(tmp_path: Path) -> None:
    csv_path = tmp_path / "h2_summary.csv"
    _write_summary_csv(csv_path)

    frame = load_h2_summary_csv(csv_path)

    assert list(frame["event_id"]) == ["evt_a", "evt_a"]
    assert set(frame["window_label"]) == {
        "primary_0d_to_1d",
        "secondary_minus_1d_to_3d",
    }


def test_load_h2_summary_csv_rejects_missing_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad_summary.csv"
    pd.DataFrame({"event_id": ["evt_a"]}).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="missing columns"):
        load_h2_summary_csv(csv_path)


def test_build_records_are_compact_and_do_not_store_row_level_trace(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "h2_summary.csv"
    _write_summary_csv(csv_path)
    frame = load_h2_summary_csv(csv_path)

    records = build_h2_summary_records(
        frame,
        computed_at="2026-05-18T12:00:00+00:00",
    )

    assert len(records) == 2
    record = records[0]
    assert record["run_id"] == RUN_ID
    assert record["summary_type"] == SUMMARY_TYPE
    assert record["table_name"] == TABLE_NAME
    assert record["metric_name"] == METRIC_NAME
    payload = json.loads(record["summary_json"])
    assert set(payload) == {"run_id", "summary_type", "event", "metrics"}
    assert set(payload["metrics"]) == {
        "window_label",
        "observed_days",
        "final_cumulative_abnormal_change",
        "estimation_observations",
    }
    assert "relative_day" not in record["summary_json"]
    assert "price_change" not in record["summary_json"]
    assert "expected_change" not in record["summary_json"]


def test_persist_h2_summaries_is_idempotent_and_preserves_unrelated_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "thesis.db"
    csv_path = tmp_path / "h2_summary.csv"
    _create_analysis_summaries_db(db_path)
    _write_summary_csv(csv_path)

    first = persist_h2_summaries(
        db_path=db_path,
        summary_csv_path=csv_path,
        computed_at="2026-05-18T12:00:00+00:00",
    )
    second = persist_h2_summaries(
        db_path=db_path,
        summary_csv_path=csv_path,
        computed_at="2026-05-18T13:00:00+00:00",
    )

    conn = sqlite3.connect(db_path)
    try:
        h2_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM analysis_summaries
            WHERE run_id = ?
              AND summary_type = ?
            """,
            (RUN_ID, SUMMARY_TYPE),
        ).fetchone()[0]
        total_count = conn.execute(
            "SELECT COUNT(*) FROM analysis_summaries"
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT summary_id, metrics_json, value_json
            FROM analysis_summaries
            WHERE run_id = ?
              AND summary_type = ?
            ORDER BY summary_id
            """,
            (RUN_ID, SUMMARY_TYPE),
        ).fetchall()
    finally:
        conn.close()

    assert first.inserted == 2
    assert first.deleted == 0
    assert second.inserted == 2
    assert second.deleted == 2
    assert h2_count == 2
    assert total_count == 3
    assert {row[0] for row in rows} == {
        "h2_event_window_summary:evt_a:primary_0d_to_1d",
        "h2_event_window_summary:evt_a:secondary_minus_1d_to_3d",
    }
    metrics = json.loads(rows[0][1])
    value = json.loads(rows[0][2])
    assert "final_cumulative_abnormal_change" in metrics
    assert "event" in value
    assert "metrics" in value


def test_missing_database_returns_clear_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = tmp_path / "h2_summary.csv"
    _write_summary_csv(csv_path)

    exit_code = main(
        [
            "--db",
            str(tmp_path / "missing.db"),
            "--summary-csv",
            str(csv_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Database not found" in captured.err


def _create_analysis_summaries_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE analysis_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                date_range_start TEXT,
                date_range_end TEXT,
                value_json TEXT NOT NULL,
                computed_at TEXT NOT NULL,
                created_at TEXT,
                summary_id TEXT,
                run_id TEXT,
                summary_type TEXT,
                input_tables TEXT,
                metrics_json TEXT,
                summary_json TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO analysis_summaries
                (table_name, metric_name, value_json, computed_at)
            VALUES ('legacy_source', 'legacy_metric', '{}',
                    '2026-05-18T00:00:00+00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()


def _write_summary_csv(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "event_id": "evt_a",
                "event_date": "2024-01-20",
                "event_time_utc": "00:00:00",
                "title": "Test event",
                "description": "A curated test event",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
                "expected_direction": "neutral",
                "relevance_score": 0.8,
                "window_label": "primary_0d_to_1d",
                "observed_days": 2,
                "final_cumulative_abnormal_change": 0.05,
                "estimation_observations": 13,
            },
            {
                "event_id": "evt_a",
                "event_date": "2024-01-20",
                "event_time_utc": "00:00:00",
                "title": "Test event",
                "description": "A curated test event",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
                "expected_direction": "neutral",
                "relevance_score": 0.8,
                "window_label": "secondary_minus_1d_to_3d",
                "observed_days": 5,
                "final_cumulative_abnormal_change": 0.08,
                "estimation_observations": 13,
            },
        ]
    ).to_csv(path, index=False)
