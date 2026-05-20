from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_v2_event_proximity_sensitivity import (
    SENSITIVITY_ROW_COLUMNS,
    SENSITIVITY_SUMMARY_COLUMNS,
    build_event_proximity_sensitivity,
    generate_event_proximity_sensitivity,
    main,
)


def test_event_proximity_detects_more_context_than_same_day() -> None:
    rows, summary = build_event_proximity_sensitivity(
        _toy_alert_rows(),
        _toy_events(),
        days_before=1,
        days_after=1,
    )

    assert tuple(rows.columns) == SENSITIVITY_ROW_COLUMNS
    assert tuple(summary.columns) == SENSITIVITY_SUMMARY_COLUMNS
    assert "wallet_address" not in rows.columns
    assert int(summary["same_day_critical_candidate"].sum()) == 0
    assert int(summary["proximity_critical_candidate"].sum()) == 1
    assert int(summary["event_watch_candidate"].sum()) == 1
    assert set(summary["suggested_context_label"]) >= {
        "critical_proximity_candidate",
        "event_watch_candidate",
    }


def test_event_proximity_requires_event_fields() -> None:
    with pytest.raises(ValueError, match="events missing required columns"):
        build_event_proximity_sensitivity(
            _toy_alert_rows(),
            _toy_events().drop(columns=["source_url"]),
        )


def test_event_proximity_rejects_wallet_address_inputs() -> None:
    alert_rows = _toy_alert_rows()
    alert_rows["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="must not receive wallet_address"):
        build_event_proximity_sensitivity(alert_rows, _toy_events())


def test_generate_event_proximity_sensitivity_writes_outputs(tmp_path: Path) -> None:
    alert_rows_path = tmp_path / "alerts.csv"
    events_path = tmp_path / "events.csv"
    rows_path = tmp_path / "rows.csv"
    summary_path = tmp_path / "summary.csv"
    metadata_path = tmp_path / "metadata.json"
    _toy_alert_rows().to_csv(alert_rows_path, index=False)
    _toy_events().to_csv(events_path, index=False)

    result = generate_event_proximity_sensitivity(
        alert_rows_path=alert_rows_path,
        events_csv_path=events_path,
        rows_path=rows_path,
        summary_path=summary_path,
        metadata_path=metadata_path,
    )

    rows = pd.read_csv(rows_path)
    summary = pd.read_csv(summary_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.row_count == len(rows)
    assert result.summary_row_count == len(summary)
    assert result.same_day_critical_candidates == 0
    assert result.proximity_critical_candidates == 1
    assert result.event_watch_candidates == 1
    assert metadata["decision"]["use_event_proximity_window"] is True
    assert metadata["decision"]["event_watch_decision"] == (
        "use_as_separate_descriptive_label_not_severity_upgrade"
    )
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False


def test_cli_returns_clear_error_for_missing_alert_rows(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events_path = tmp_path / "events.csv"
    _toy_events().to_csv(events_path, index=False)

    exit_code = main(
        [
            "--alert-rows",
            str(tmp_path / "missing.csv"),
            "--events",
            str(events_path),
            "--rows-output",
            str(tmp_path / "rows.csv"),
            "--summary-output",
            str(tmp_path / "summary.csv"),
            "--metadata-output",
            str(tmp_path / "metadata.json"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Monitor v2 replay alert rows not found" in captured.err


def _toy_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "evt_context",
                "event_date": "2024-01-02",
                "event_time_utc": "12:00:00",
                "title": "Toy context event",
                "description": "Toy context event.",
                "event_type": "major_news",
                "source_url": "https://example.com/event",
                "expected_direction": "neutral",
                "relevance_score": "0.9",
            }
        ]
    )


def _toy_alert_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    specs = (
        ("market", "market_move", "absolute_price_change"),
        ("tier_1_top_1pct", "wallet_tier_activity", "log1p_total_observed_amount_usd"),
        ("tier_1_top_1pct", "active_wallet_activity", "active_wallets"),
        ("all_tiers", "concentration", "tier_1_total_amount_share"),
    )
    for date, severities in {
        "2024-01-01": ("watch", "watch", "none", "none"),
        "2024-01-02": ("none", "high", "watch", "none"),
        "2024-01-03": ("none", "none", "none", "none"),
    }.items():
        for index, (tier, family, metric) in enumerate(specs):
            severity = severities[index]
            rows.append(
                {
                    "timestamp_utc": f"{date}T00:00:00Z",
                    "market_id": "toy_market",
                    "tier": tier,
                    "anomaly_family": family,
                    "metric_name": metric,
                    "observed_value": 1.0 + index,
                    "baseline_window": "last_5_completed_observations",
                    "baseline_observations": 5,
                    "rolling_median": 1.0,
                    "rolling_mad": 0.5,
                    "robust_z": 2.5 if severity in {"watch", "high"} else 0.0,
                    "rolling_percentile_rank": 1.0 if severity in {"watch", "high"} else 0.5,
                    "severity": severity,
                    "status": "ok",
                    "event_candidate_id": "evt_context" if date == "2024-01-02" else "",
                    "event_review_status": "accepted" if date == "2024-01-02" else "",
                    "evidence_refs": "toy",
                    "limitation": "toy rows",
                    "review_status": "candidate",
                    "claim_scope": "descriptive_monitor_alert_only",
                }
            )
    return pd.DataFrame(rows)
