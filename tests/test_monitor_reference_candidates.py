from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_reference_candidates import (
    FEATURE_COLUMNS,
    build_monitor_reference_candidate_features,
    generate_monitor_reference_candidates,
)


def test_build_candidate_features_from_non_none_monitor_rows() -> None:
    features = build_monitor_reference_candidate_features(_alert_rows_with_candidate())

    triggered = features[features["feature_status"] == "triggered"]

    assert features["case_id"].nunique() == 1
    assert set(triggered["pattern_label"]) == {
        "large_trade_flow",
        "market_concentration",
        "event_proximity",
    }
    assert "wallet_address" not in features.columns
    assert set(triggered["fact_source"]) == {"computed"}


def test_no_non_none_monitor_rows_returns_empty_features() -> None:
    rows = _alert_rows_with_candidate()
    rows["severity"] = "none"

    features = build_monitor_reference_candidate_features(rows)

    assert tuple(features.columns) == FEATURE_COLUMNS
    assert features.empty


def test_repeated_market_alerts_trigger_same_theme_candidate_label() -> None:
    rows = pd.concat(
        [
            _alert_rows_with_candidate(),
            _alert_rows_with_candidate().assign(timestamp_utc="2026-05-20T00:20:00Z"),
        ],
        ignore_index=True,
    )

    features = build_monitor_reference_candidate_features(rows)

    same_theme = features[
        features["pattern_label"] == "same_theme_repeated_positions"
    ]
    assert set(same_theme["feature_status"]) == {"triggered"}


def test_candidate_generation_rejects_wallet_address_columns() -> None:
    rows = _alert_rows_with_candidate()
    rows["wallet_address"] = "0x" + "1" * 40

    with pytest.raises(ValueError, match="wallet-address columns"):
        build_monitor_reference_candidate_features(rows)


def test_generate_monitor_reference_candidates_outputs_similarity(tmp_path: Path) -> None:
    alert_rows_path = tmp_path / "alert_rows.csv"
    reference_features_path = tmp_path / "reference_features.csv"
    _alert_rows_with_candidate().to_csv(alert_rows_path, index=False)
    _reference_features().to_csv(reference_features_path, index=False)

    result = generate_monitor_reference_candidates(
        alert_rows_path=alert_rows_path,
        reference_features_path=reference_features_path,
        candidate_features_path=tmp_path / "candidate_features.csv",
        candidate_summary_path=tmp_path / "candidate_summary.csv",
        similarity_scores_path=tmp_path / "similarity_scores.csv",
        similarity_summary_path=tmp_path / "similarity_summary.csv",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    candidate_summary = pd.read_csv(result.candidate_summary_path)
    similarity = pd.read_csv(result.similarity_scores_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    assert result.candidate_count == 1
    assert result.triggered_feature_rows == 3
    assert result.similarity_comparison_rows == 2
    assert result.max_similarity_score == pytest.approx(1.0)
    assert int(candidate_summary.loc[0, "candidate_count"]) == 1
    assert similarity["similarity_score"].max() == pytest.approx(1.0)
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert "Monitor Reference Candidates" in dashboard


def test_generate_monitor_reference_candidates_handles_no_candidates(tmp_path: Path) -> None:
    rows = _alert_rows_with_candidate()
    rows["severity"] = "none"
    alert_rows_path = tmp_path / "alert_rows.csv"
    reference_features_path = tmp_path / "reference_features.csv"
    rows.to_csv(alert_rows_path, index=False)
    _reference_features().to_csv(reference_features_path, index=False)

    result = generate_monitor_reference_candidates(
        alert_rows_path=alert_rows_path,
        reference_features_path=reference_features_path,
        candidate_features_path=tmp_path / "candidate_features.csv",
        candidate_summary_path=tmp_path / "candidate_summary.csv",
        similarity_scores_path=tmp_path / "similarity_scores.csv",
        similarity_summary_path=tmp_path / "similarity_summary.csv",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    candidate_features = pd.read_csv(result.candidate_features_path)
    summary = pd.read_csv(result.candidate_summary_path)
    assert result.candidate_count == 0
    assert result.similarity_comparison_rows == 0
    assert candidate_features.empty
    assert int(summary.loc[0, "source_non_none_rows"]) == 0


def _alert_rows_with_candidate() -> pd.DataFrame:
    base = {
        "timestamp_utc": "2026-05-20T00:15:00Z",
        "market_id": "mock_market_iran",
        "tier": "all_tiers",
        "observed_value": 1.0,
        "baseline_window": "last_30_completed_observations",
        "baseline_observations": 30,
        "rolling_median": 0.1,
        "rolling_mad": 0.1,
        "robust_z": 3.0,
        "rolling_percentile_rank": 1.0,
        "severity": "watch",
        "status": "ok",
        "event_candidate_id": "event_iran_001",
        "event_review_status": "accepted",
        "evidence_refs": "toy",
        "limitation": "toy aggregate monitor row",
        "review_status": "candidate",
        "claim_scope": "descriptive_monitor_alert_only",
    }
    rows = []
    for family, metric in (
        ("wallet_tier_activity", "log1p_total_observed_amount_usd"),
        ("concentration", "top_tier_share"),
        ("market_move", "absolute_midpoint_change"),
    ):
        row = dict(base)
        row["anomaly_family"] = family
        row["metric_name"] = metric
        rows.append(row)
    return pd.DataFrame(rows)


def _reference_features() -> pd.DataFrame:
    rows = []
    for case_id, patterns in (
        ("large_flow_reference", ("large_trade_flow", "market_concentration")),
        (
            "reported_cluster_reference",
            ("market_concentration", "event_proximity", "cluster_link_reported"),
        ),
    ):
        for pattern in (
            "large_trade_flow",
            "market_concentration",
            "event_proximity",
            "cluster_link_reported",
        ):
            rows.append(
                {
                    "case_id": case_id,
                    "case_type": "reference",
                    "pattern_label": pattern,
                    "feature_status": "triggered" if pattern in patterns else "unknown",
                    "fact_source": "reported" if pattern in patterns else "unknown",
                    "reason": "toy reference",
                    "evidence_status": "source_checked",
                    "claim_scope": "descriptive_reference_only",
                    "requires_human_review": True,
                }
            )
    return pd.DataFrame(rows)
