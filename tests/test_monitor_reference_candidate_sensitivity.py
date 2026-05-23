from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_reference_candidate_sensitivity import (
    CANDIDATE_ROW_COLUMNS,
    build_monitor_reference_candidate_sensitivity_features,
    build_monitor_reference_candidate_sensitivity_rows,
    generate_monitor_reference_candidate_sensitivity,
)


def test_strict_candidates_keep_existing_feature_mapping() -> None:
    features = build_monitor_reference_candidate_sensitivity_features(
        _alert_rows_with_strict_candidate()
    )

    triggered = features[features["feature_status"] == "triggered"]

    assert features["case_id"].nunique() == 1
    assert set(triggered["pattern_label"]) == {
        "large_trade_flow",
        "market_concentration",
        "event_proximity",
    }
    assert set(triggered["fact_source"]) == {"computed"}
    assert "wallet_address" not in features.columns


def test_zero_mad_high_percentile_rows_create_shadow_candidate() -> None:
    candidates = build_monitor_reference_candidate_sensitivity_rows(
        _shadow_row("market_move", "absolute_midpoint_change")
    )

    assert tuple(candidates.columns) == CANDIDATE_ROW_COLUMNS
    assert len(candidates) == 1
    assert candidates.loc[0, "candidate_kind"] == "shadow_percentile_candidate"
    assert bool(candidates.loc[0, "market_only_diagnostic"]) is True


def test_market_only_shadow_candidate_has_no_wallet_labels_and_zero_similarity(
    tmp_path: Path,
) -> None:
    alert_rows_path = tmp_path / "alert_rows.csv"
    reference_features_path = tmp_path / "reference_features.csv"
    _shadow_row("market_move", "absolute_midpoint_change").to_csv(
        alert_rows_path,
        index=False,
    )
    _reference_features().to_csv(reference_features_path, index=False)

    result = generate_monitor_reference_candidate_sensitivity(
        alert_rows_path=alert_rows_path,
        reference_features_path=reference_features_path,
        candidate_rows_path=tmp_path / "candidate_rows.csv",
        candidate_features_path=tmp_path / "candidate_features.csv",
        candidate_summary_path=tmp_path / "candidate_summary.csv",
        similarity_scores_path=tmp_path / "similarity_scores.csv",
        similarity_summary_path=tmp_path / "similarity_summary.csv",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    features = pd.read_csv(result.candidate_features_path)
    similarity = pd.read_csv(result.similarity_scores_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")

    assert result.candidate_count == 1
    assert result.shadow_candidate_count == 1
    assert result.market_only_shadow_candidate_count == 1
    assert set(features["feature_status"]) == {"unknown"}
    assert similarity["similarity_score"].max() == pytest.approx(0.0)
    assert metadata["method"]["default_rule_c_unchanged"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert "Diagnostic Monitor Candidate Sensitivity" in dashboard


def test_wallet_tier_shadow_candidate_triggers_large_trade_flow() -> None:
    features = build_monitor_reference_candidate_sensitivity_features(
        _shadow_row("wallet_tier_activity", "log1p_total_observed_amount_usd")
    )

    triggered = features[features["feature_status"] == "triggered"]

    assert set(triggered["pattern_label"]) == {"large_trade_flow"}


def test_concentration_shadow_with_event_context_triggers_expected_labels() -> None:
    features = build_monitor_reference_candidate_sensitivity_features(
        _shadow_row(
            "concentration",
            "top_tier_share",
            event_candidate_id="event_iran_001",
            event_review_status="accepted",
        )
    )

    triggered = features[features["feature_status"] == "triggered"]

    assert set(triggered["pattern_label"]) == {
        "market_concentration",
        "event_proximity",
    }


def test_rows_below_shadow_threshold_do_not_become_candidates() -> None:
    rows = _shadow_row("market_move", "absolute_midpoint_change")
    rows["rolling_percentile_rank"] = 0.94

    candidates = build_monitor_reference_candidate_sensitivity_rows(rows)

    assert candidates.empty


def _alert_rows_with_strict_candidate() -> pd.DataFrame:
    rows = []
    for family, metric in (
        ("wallet_tier_activity", "log1p_total_observed_amount_usd"),
        ("concentration", "top_tier_share"),
        ("market_move", "absolute_midpoint_change"),
    ):
        row = _base_alert_row()
        row["anomaly_family"] = family
        row["metric_name"] = metric
        row["severity"] = "watch"
        row["status"] = "ok"
        row["event_candidate_id"] = "event_iran_001"
        row["event_review_status"] = "accepted"
        rows.append(row)
    return pd.DataFrame(rows)


def _shadow_row(
    anomaly_family: str,
    metric_name: str,
    *,
    event_candidate_id: str = "",
    event_review_status: str = "",
) -> pd.DataFrame:
    row = _base_alert_row()
    row["anomaly_family"] = anomaly_family
    row["metric_name"] = metric_name
    row["severity"] = "none"
    row["status"] = "zero_mad"
    row["baseline_observations"] = 20
    row["rolling_percentile_rank"] = 0.99
    row["event_candidate_id"] = event_candidate_id
    row["event_review_status"] = event_review_status
    return pd.DataFrame([row])


def _base_alert_row() -> dict[str, object]:
    return {
        "timestamp_utc": "2026-05-20T00:15:00Z",
        "market_id": "mock_market_iran",
        "tier": "all_tiers",
        "anomaly_family": "market_move",
        "metric_name": "absolute_midpoint_change",
        "observed_value": 1.0,
        "baseline_window": "last_30_completed_observations",
        "baseline_observations": 30,
        "rolling_median": 0.1,
        "rolling_mad": 0.0,
        "robust_z": 0.0,
        "rolling_percentile_rank": 1.0,
        "severity": "none",
        "status": "zero_mad",
        "event_candidate_id": "",
        "event_review_status": "",
        "evidence_refs": "toy",
        "limitation": "toy aggregate monitor row",
        "review_status": "candidate",
        "claim_scope": "descriptive_monitor_alert_only",
    }


def _reference_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "large_flow_reference",
                "case_type": "reference",
                "pattern_label": "large_trade_flow",
                "feature_status": "triggered",
                "fact_source": "reported",
                "reason": "toy reference",
                "evidence_status": "source_checked",
                "claim_scope": "descriptive_reference_only",
                "requires_human_review": True,
            },
            {
                "case_id": "reported_cluster_reference",
                "case_type": "reference",
                "pattern_label": "market_concentration",
                "feature_status": "triggered",
                "fact_source": "reported",
                "reason": "toy reference",
                "evidence_status": "source_checked",
                "claim_scope": "descriptive_reference_only",
                "requires_human_review": True,
            },
        ]
    )
