from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from operations.analysis.monitor_detection_backtest import (
    build_detection_backtest,
    generate_detection_backtest_outputs,
)


def test_detection_backtest_marks_pre_event_hit() -> None:
    cases, summary = build_detection_backtest(
        review_report=_review_report("2026-05-26T10:00:00Z"),
        events=_events("2026-05-26", "20:00:00"),
        similarity_summary=_similarity(score=0.0),
        graph_metrics=_graph_metrics("isolated_wallet"),
    )

    case = cases.iloc[0]
    assert bool(case["event_hit"]) is True
    assert bool(case["pre_event_hit"]) is True
    assert case["lead_time_direction"] == "candidate_before_event"
    assert summary.iloc[0]["event_hit_count"] == 1


def test_detection_backtest_does_not_count_after_event_as_pre_event_hit() -> None:
    cases, _summary = build_detection_backtest(
        review_report=_review_report("2026-05-26T23:00:00Z"),
        events=_events("2026-05-26", "20:00:00"),
        similarity_summary=_similarity(score=0.0),
        graph_metrics=_graph_metrics("isolated_wallet"),
    )

    case = cases.iloc[0]
    assert bool(case["event_hit"]) is True
    assert bool(case["pre_event_hit"]) is False
    assert case["lead_time_direction"] == "candidate_after_event"


def test_detection_backtest_marks_reference_hit() -> None:
    cases, summary = build_detection_backtest(
        review_report=_review_report("2026-05-26T10:00:00Z"),
        events=_events("2024-01-01", "00:00:00"),
        similarity_summary=_similarity(score=1.0),
        graph_metrics=_graph_metrics("shared_bucket_cluster"),
    )

    case = cases.iloc[0]
    assert bool(case["reference_hit"]) is True
    assert case["best_reference_case_id"] == "adrian_reference"
    assert bool(case["false_context_flag"]) is False
    assert summary.iloc[0]["reference_hit_count"] == 1


def test_generate_detection_backtest_outputs_writes_dashboard(tmp_path: Path) -> None:
    review_path = tmp_path / "review.csv"
    events_path = tmp_path / "events.csv"
    similarity_path = tmp_path / "similarity.csv"
    graph_path = tmp_path / "graph.csv"
    _review_report("2026-05-26T10:00:00Z").to_csv(review_path, index=False)
    _events("2026-05-26", "20:00:00").to_csv(events_path, index=False)
    _similarity(score=1.0).to_csv(similarity_path, index=False)
    _graph_metrics("shared_bucket_cluster").to_csv(graph_path, index=False)

    result = generate_detection_backtest_outputs(
        review_report_path=review_path,
        events_path=events_path,
        similarity_summary_path=similarity_path,
        graph_metrics_path=graph_path,
        cases_path=tmp_path / "cases.csv",
        summary_path=tmp_path / "summary.csv",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    assert result.candidate_count == 1
    assert result.event_hit_count == 1
    assert result.reference_hit_count == 1
    assert "Monitor Detection Backtest" in dashboard
    assert metadata["limitations"]["not_a_return_backtest"] is True


def _review_report(timestamp: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "candidate_a",
                "timestamp_utc": timestamp,
                "market_id": "market_a",
                "question": "Will a politics market resolve yes?",
                "max_severity": "high",
                "review_priority": "high",
            }
        ]
    )


def _events(event_date: str, event_time: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "event_a",
                "event_date": event_date,
                "event_time_utc": event_time,
                "title": "Reviewed event",
            }
        ]
    )


def _similarity(*, score: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "candidate_a",
                "best_reference_case_id": "adrian_reference",
                "best_similarity_score": score,
            }
        ]
    )


def _graph_metrics(label: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "proxy_wallet": "0x" + "1" * 40,
                "cluster_label": label,
            }
        ]
    )
