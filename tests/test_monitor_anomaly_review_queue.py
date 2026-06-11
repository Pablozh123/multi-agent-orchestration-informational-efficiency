from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_anomaly_review_queue import (
    ALLOWED_REVIEW_STATUSES,
    QUEUE_COLUMNS,
    apply_review_status_updates,
    build_anomaly_review_queue,
    build_anomaly_review_summary,
    generate_monitor_anomaly_review_queue,
)
from operations.analysis.monitor_reference_candidates import monitor_candidate_id


def test_build_anomaly_review_queue_from_bounded_artifacts() -> None:
    queue = build_anomaly_review_queue(
        review_report=_review_report(),
        alert_rows=_alert_rows(),
        detection_cases=_detection_cases(),
        materiality_context=_materiality_context(),
        risk_summary=_risk_summary(),
    )

    high = queue[queue["case_id"] == _candidate_id("market_b")].iloc[0]
    assert tuple(queue.columns) == QUEUE_COLUMNS
    assert len(queue) == 2
    assert high["review_priority"] == "high"
    assert high["market_slug"] == "politics-market-b"
    assert high["trigger_family"] == "concentration,wallet_tier_activity"
    assert high["event_context_status"] == "pre_event_context"
    assert high["reference_overlap_status"] == "reference_hit"
    assert high["review_label"] == "insider_risk_review_candidate"
    assert "total_observed_amount_usd=250.0000" in high["wallet_flow_context"]
    assert "concentration_context=present" in high["concentration_context"]
    assert "private_information_proof" in high["blocked_claims"]
    assert "wallet_address" not in queue.columns


def test_build_anomaly_review_summary_counts_queue_labels() -> None:
    queue = build_anomaly_review_queue(
        review_report=_review_report(),
        detection_cases=_detection_cases(),
    )

    summary = build_anomaly_review_summary(queue)

    row = summary.iloc[0]
    assert int(row["queue_row_count"]) == 2
    assert int(row["high_priority_count"]) == 1
    assert "insider_risk_review_candidate=1" in row["review_label_counts"]
    assert bool(row["ready_for_future_agent_contract"]) is True
    assert bool(row["ready_for_future_mcp_contract"]) is True


def test_apply_review_status_updates_changes_only_known_cases() -> None:
    queue = build_anomaly_review_queue(review_report=_review_report())
    updates = pd.DataFrame(
        [
            {
                "case_id": _candidate_id("market_b"),
                "human_review_status": "source_check_pending",
                "review_status_updated_at_utc": "2026-06-11T12:00:00Z",
                "review_note": "manual source check opened",
            }
        ]
    )

    updated = apply_review_status_updates(queue, updates)

    high = updated[updated["case_id"] == _candidate_id("market_b")].iloc[0]
    assert high["human_review_status"] == "source_check_pending"
    assert high["review_status_updated_at_utc"] == "2026-06-11T12:00:00Z"
    assert high["review_note"] == "manual source check opened"
    assert set(updated["human_review_status"]).issubset(ALLOWED_REVIEW_STATUSES)


def test_apply_review_status_updates_rejects_unknown_status() -> None:
    queue = build_anomaly_review_queue(review_report=_review_report())
    updates = pd.DataFrame(
        [{"case_id": _candidate_id("market_b"), "human_review_status": "done"}]
    )

    with pytest.raises(ValueError, match="invalid human_review_status"):
        apply_review_status_updates(queue, updates)


def test_anomaly_review_queue_rejects_wallet_address_columns() -> None:
    report = _review_report()
    report["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="wallet-address columns"):
        build_anomaly_review_queue(review_report=report)


def test_generate_monitor_anomaly_review_queue_writes_outputs(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_monitor_anomaly_review_queue(
        review_report_path=paths["review_report"],
        alert_rows_path=paths["alert_rows"],
        detection_cases_path=paths["detection_cases"],
        materiality_context_path=paths["materiality_context"],
        risk_summary_path=paths["risk_summary"],
        queue_path=tmp_path / "queue.csv",
        summary_path=tmp_path / "summary.csv",
        metadata_path=tmp_path / "metadata.json",
        dashboard_path=tmp_path / "dashboard.html",
    )

    queue = pd.read_csv(result.queue_path)
    summary = pd.read_csv(result.summary_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    assert result.queue_row_count == 2
    assert result.high_priority_count == 1
    assert len(queue) == 2
    assert int(summary.loc[0, "queue_row_count"]) == 2
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False
    assert metadata["future_mcp_contract"]["max_rows"] == 50
    assert metadata["future_mcp_contract"]["raw_sql_allowed"] is False
    assert metadata["future_agent_contract"]["agent_metric_calculation_allowed"] is False
    assert "Monitor Anomaly Review Queue" in dashboard
    assert "Future agents and MCP may read summaries only" in dashboard


def _write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "review_report": root / "review_report.csv",
        "alert_rows": root / "alert_rows.csv",
        "detection_cases": root / "detection_cases.csv",
        "materiality_context": root / "materiality.csv",
        "risk_summary": root / "risk_summary.csv",
    }
    _review_report().to_csv(paths["review_report"], index=False)
    _alert_rows().to_csv(paths["alert_rows"], index=False)
    _detection_cases().to_csv(paths["detection_cases"], index=False)
    _materiality_context().to_csv(paths["materiality_context"], index=False)
    _risk_summary().to_csv(paths["risk_summary"], index=False)
    return paths


def _candidate_id(market_id: str) -> str:
    return monitor_candidate_id("2026-05-23T19:25:00Z", market_id)


def _review_report() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": _candidate_id("market_a"),
                "timestamp_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "question": "Will a geopolitics market resolve yes?",
                "subcategory": "geopolitics-market-a",
                "anomaly_row_count": 1,
                "max_severity": "info",
                "anomaly_families": "active_wallet_activity",
                "metric_names": "active_wallets",
                "max_percentile_rank": 0.90,
                "latest_midpoint_min": 0.1,
                "latest_midpoint_max": 0.9,
                "active_wallets": 3,
                "trade_count": 3,
                "total_observed_amount_usd": 69.44,
                "amount_per_wallet": 23.15,
                "amount_per_trade": 23.15,
                "materiality_label": "below_one_percent_of_reference",
                "coordination_label": "few_wallet_or_trade_context",
                "insider_risk_review_label": "insider-risk watch cue: weak or incomplete evidence",
                "triggered_patterns": "",
                "best_reference_case_id": "",
                "best_similarity_score": 0.0,
                "missing_evidence": "independent news/event timestamp check",
                "review_priority": "low",
                "human_review_status": "needs_human_review",
                "allowed_interpretation": "human review only",
                "limitation": "toy",
                "source_artifacts": "monitor_candidate_human_review_report.csv",
            },
            {
                "candidate_id": _candidate_id("market_b"),
                "timestamp_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_b",
                "question": "Will a politics market resolve yes?",
                "subcategory": "politics-market-b",
                "anomaly_row_count": 2,
                "max_severity": "high",
                "anomaly_families": "wallet_tier_activity,concentration",
                "metric_names": "log1p_total_observed_amount_usd,top_tier_share",
                "max_percentile_rank": 1.0,
                "latest_midpoint_min": 0.2,
                "latest_midpoint_max": 0.8,
                "active_wallets": 2,
                "trade_count": 3,
                "total_observed_amount_usd": 250.0,
                "amount_per_wallet": 125.0,
                "amount_per_trade": 83.33,
                "materiality_label": "below_one_percent_of_reference",
                "coordination_label": "few_wallet_or_trade_context",
                "insider_risk_review_label": "insider-risk review candidate: relative anomaly, low materiality",
                "triggered_patterns": "large_trade_flow,market_concentration",
                "best_reference_case_id": "reference_b",
                "best_similarity_score": 1.0,
                "missing_evidence": "manual Polymarket market page review",
                "review_priority": "high",
                "human_review_status": "needs_human_review",
                "allowed_interpretation": "human review only",
                "limitation": "toy",
                "source_artifacts": "monitor_candidate_human_review_report.csv",
            },
        ]
    )


def _alert_rows() -> pd.DataFrame:
    base = {
        "timestamp_utc": "2026-05-23T19:25:00Z",
        "tier": "all_tiers",
        "observed_value": 1.0,
        "baseline_window": "last_30_completed_observations",
        "baseline_observations": 20,
        "rolling_median": 0.2,
        "rolling_mad": 0.1,
        "robust_z": 2.0,
        "rolling_percentile_rank": 1.0,
        "status": "ok",
        "event_candidate_id": "",
        "event_review_status": "",
        "evidence_refs": "toy",
        "limitation": "toy aggregate row",
        "review_status": "candidate",
        "claim_scope": "descriptive_monitor_alert_only",
    }
    rows = []
    for market_id, family, metric, severity in (
        ("market_a", "active_wallet_activity", "active_wallets", "info"),
        ("market_b", "wallet_tier_activity", "log1p_total_observed_amount_usd", "high"),
        ("market_b", "concentration", "top_tier_share", "watch"),
    ):
        row = dict(base)
        row.update(
            {
                "market_id": market_id,
                "anomaly_family": family,
                "metric_name": metric,
                "severity": severity,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _detection_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": _candidate_id("market_a"),
                "event_hit": False,
                "pre_event_hit": False,
                "nearest_event_id": "",
                "reference_hit": False,
                "best_similarity_score": 0.0,
            },
            {
                "candidate_id": _candidate_id("market_b"),
                "event_hit": True,
                "pre_event_hit": True,
                "nearest_event_id": "event_b",
                "reference_hit": True,
                "best_reference_case_id": "reference_b",
                "best_similarity_score": 1.0,
            },
        ]
    )


def _materiality_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": _candidate_id("market_b"),
                "total_observed_amount_usd": 250.0,
                "amount_per_wallet": 125.0,
                "amount_per_trade": 83.33,
                "materiality_label": "below_one_percent_of_reference",
            }
        ]
    )


def _risk_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": _candidate_id("market_b"),
                "literature_wallet_risk_score": 2.7,
                "literature_wallet_risk_flag": "no_literature_prior_flag",
                "literature_market_risk_score": 1.1,
                "literature_market_risk_flag": "literature_prior_flag",
            }
        ]
    )
