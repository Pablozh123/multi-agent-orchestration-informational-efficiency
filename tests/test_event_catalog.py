"""Tests for canonical event catalog audit and loader tools."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from operations.tools.event_catalog_audit import (
    audit_event_catalog_connection,
    main as audit_main,
)
from operations.tools.load_events import (
    read_event_seed,
    upsert_events,
    validate_event_row,
)


def test_event_audit_reports_missing_fields_invalid_dates_and_duplicates(
    in_memory_db: sqlite3.Connection,
) -> None:
    in_memory_db.executescript("""
        INSERT INTO events_timeline
            (event_timestamp, event_type, event_category, description, impact_score)
        VALUES
            ('2024-01-01T00:00:00.000000Z', 'legacy_event', 'legacy',
             'legacy row', 0.5);

        INSERT INTO events_timeline
            (event_id, event_date, event_time_utc, title, description, event_type,
             source_url, expected_direction, relevance_score)
        VALUES
            ('event-1', '2024-02-01', '12:00:00', 'Canonical Event',
             'curated row', 'debate', 'https://example.com/source',
             'trump_positive', 0.8),
            ('event-1', '2024-02-01', '12:00:00', 'Canonical Event',
             'duplicate row', 'debate', 'https://example.com/source-2',
             'trump_positive', 0.7),
            ('event-bad-date', 'not-a-date', '13:00:00', 'Bad Date Event',
             'bad date row', 'legal', 'https://example.com/bad-date',
             'trump_negative', 0.6);
    """)

    report = audit_event_catalog_connection(in_memory_db)

    assert report["row_count"] == 4
    assert report["missing_event_id_count"] == 1
    assert report["missing_event_date_count"] == 1
    assert report["missing_title_count"] == 1
    assert report["missing_source_url_count"] == 1
    assert report["missing_expected_direction_count"] == 1
    assert report["missing_relevance_score_count"] == 1
    assert report["invalid_dates"] == [
        {"id": 4, "column": "event_date", "value": "not-a-date"}
    ]
    assert report["duplicate_events"]["event_id"] == [
        {"key": "event-1", "count": 2}
    ]
    assert report["duplicate_events"]["canonical_key"] == [
        {"key": "2024-02-01|12:00:00|Canonical Event", "count": 2}
    ]


def test_event_audit_cli_outputs_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "events.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE events_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            event_date TEXT,
            event_time_utc TEXT,
            title TEXT,
            description TEXT,
            event_type TEXT,
            source_url TEXT,
            expected_direction TEXT,
            relevance_score REAL,
            event_timestamp TEXT,
            event_category TEXT,
            impact_score REAL,
            created_at TEXT
        );
    """)
    conn.close()

    exit_code = audit_main(["--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"row_count": 0' in captured.out


def test_event_seed_csv_contains_valid_curated_rows() -> None:
    rows = read_event_seed(Path("data/events_timeline_seed.csv"))

    assert len(rows) >= 1
    event_ids = [row["event_id"] for row in rows]
    assert len(event_ids) == len(set(event_ids))
    for index, row in enumerate(rows, start=1):
        validated = validate_event_row(row, index)
        assert validated["source_url"].startswith("https://")


def test_loader_upserts_canonical_events_and_preserves_legacy_rows(
    in_memory_db: sqlite3.Connection,
) -> None:
    in_memory_db.execute(
        """
        INSERT INTO events_timeline
            (event_timestamp, event_type, event_category, description, impact_score)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "2024-01-01T00:00:00.000000Z",
            "legacy_event",
            "legacy",
            "legacy row",
            0.5,
        ),
    )

    rows = [
        _event_row(event_id="event-1", title="Initial title"),
    ]
    first = upsert_events(in_memory_db, rows)
    second = upsert_events(
        in_memory_db,
        [_event_row(event_id="event-1", title="Updated title")],
    )

    total_rows = in_memory_db.execute(
        "SELECT COUNT(1) FROM events_timeline"
    ).fetchone()[0]
    legacy_rows = in_memory_db.execute(
        """
        SELECT COUNT(1)
        FROM events_timeline
        WHERE event_id IS NULL AND event_timestamp IS NOT NULL
        """
    ).fetchone()[0]
    title = in_memory_db.execute(
        """
        SELECT title, created_at
        FROM events_timeline
        WHERE event_id = ?
        LIMIT 1
        """,
        ("event-1",),
    ).fetchone()

    assert first.to_dict() == {"inserted": 1, "updated": 0, "input_rows": 1}
    assert second.to_dict() == {"inserted": 0, "updated": 1, "input_rows": 1}
    assert total_rows == 2
    assert legacy_rows == 1
    assert title[0] == "Updated title"
    assert title[1] is not None


def test_loader_rejects_missing_canonical_fields() -> None:
    row = _event_row(event_id="")

    with pytest.raises(ValueError, match="missing canonical fields"):
        validate_event_row(row)


def test_loader_rejects_invalid_date_and_relevance_score() -> None:
    with pytest.raises(ValueError, match="invalid event_date"):
        validate_event_row(_event_row(event_date="2024-99-99"))

    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_event_row(_event_row(relevance_score="1.5"))


def _event_row(**overrides: str) -> dict[str, str]:
    row = {
        "event_id": "event-1",
        "event_date": "2024-01-15",
        "event_time_utc": "12:00:00",
        "title": "TODO curated event title",
        "description": "TODO curated event description",
        "event_type": "TODO",
        "source_url": "https://example.com/todo-source",
        "expected_direction": "TODO",
        "relevance_score": "0.5",
    }
    row.update(overrides)
    return row
