from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_literature_risk_scores import (
    RISK_ROW_COLUMNS,
    RISK_SUMMARY_COLUMNS,
    WALLET_SCORE_THRESHOLD,
    build_literature_risk_scores,
    generate_literature_risk_score_outputs,
)


def test_build_literature_scores_computes_price_velocity_and_concentration() -> None:
    rows, summary = build_literature_risk_scores(
        review_report=_review_report(),
        alert_rows=_alert_rows(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(top_tier_share=0.9, hhi=0.8),
    )

    assert tuple(rows.columns) == RISK_ROW_COLUMNS
    assert tuple(summary.columns) == RISK_SUMMARY_COLUMNS
    candidate = summary.iloc[0]
    assert candidate["literature_market_risk_score"] == pytest.approx(1.1)
    assert candidate["literature_market_risk_flag"] == "literature_prior_flag"
    velocity = rows[rows["feature_name"] == "price_velocity"].iloc[0]
    concentration = rows[rows["feature_name"] == "volume_concentration"].iloc[0]
    assert velocity["feature_value"] == pytest.approx(0.2)
    assert concentration["feature_value"] == pytest.approx(0.9)
    assert candidate["available_feature_count"] == 4
    assert candidate["unavailable_feature_count"] == 3


def test_missing_new_wallet_age_is_unavailable_not_zeroed_as_fact() -> None:
    rows, _summary = build_literature_risk_scores(
        review_report=_review_report(),
        alert_rows=_alert_rows(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
    )

    new_wallet = rows[rows["feature_name"] == "new_wallet_penalty"].iloc[0]
    assert new_wallet["feature_status"] == "unavailable"
    assert new_wallet["feature_value"] == ""
    assert new_wallet["weighted_value"] == pytest.approx(0.0)
    assert "Dune" in new_wallet["limitation"]


def test_cluster_proxy_distinguishes_many_small_flows_from_single_trade() -> None:
    many_rows, _many_summary = build_literature_risk_scores(
        review_report=_review_report(coordination_label="coordinated_small_flow_candidate"),
        alert_rows=_alert_rows(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
    )
    single_rows, _single_summary = build_literature_risk_scores(
        review_report=_review_report(coordination_label="single_wallet_single_trade"),
        alert_rows=_alert_rows(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
    )

    many_cluster = many_rows[many_rows["feature_name"] == "cluster_correlation_proxy"].iloc[0]
    single_cluster = single_rows[
        single_rows["feature_name"] == "cluster_correlation_proxy"
    ].iloc[0]
    assert many_cluster["feature_value"] == pytest.approx(1.0)
    assert single_cluster["feature_value"] == pytest.approx(0.0)


def test_literature_wallet_score_above_threshold_is_only_prior_flag() -> None:
    rows, summary = build_literature_risk_scores(
        review_report=_review_report(coordination_label="coordinated_small_flow_candidate"),
        alert_rows=_alert_rows(with_event=True),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
    )

    candidate = summary.iloc[0]
    assert candidate["literature_wallet_risk_score"] == pytest.approx(5.8)
    assert candidate["literature_wallet_risk_score"] < WALLET_SCORE_THRESHOLD
    assert candidate["literature_wallet_risk_flag"] == "no_literature_prior_flag"
    assert "not a Rule C replacement" in candidate["allowed_interpretation"]
    assert (rows["score_family"] == "wallet").sum() == 4


def test_generate_literature_risk_score_outputs_writes_metadata(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_literature_risk_score_outputs(
        review_report_path=paths["review_report"],
        alert_rows_path=paths["alert_rows"],
        market_snapshots_path=paths["market_snapshots"],
        wallet_tier_snapshots_path=paths["wallet_snapshots"],
        rows_path=tmp_path / "rows.csv",
        summary_path=tmp_path / "summary.csv",
        metadata_path=tmp_path / "metadata.json",
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    summary = pd.read_csv(result.summary_path)
    assert result.candidate_count == 1
    assert len(summary) == 1
    assert metadata["method"]["does_not_replace_rule_c"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_order_instructions"] is False


def test_literature_risk_scores_reject_wallet_address_columns() -> None:
    report = _review_report()
    report["wallet_address"] = "0x" + "a" * 40

    with pytest.raises(ValueError, match="wallet-address columns"):
        build_literature_risk_scores(
            review_report=report,
            alert_rows=_alert_rows(),
            market_snapshots=_market_snapshots(),
            wallet_tier_snapshots=_wallet_snapshots(),
        )


def _write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "review_report": root / "review.csv",
        "alert_rows": root / "alerts.csv",
        "market_snapshots": root / "market.csv",
        "wallet_snapshots": root / "wallet.csv",
    }
    _review_report().to_csv(paths["review_report"], index=False)
    _alert_rows().to_csv(paths["alert_rows"], index=False)
    _market_snapshots().to_csv(paths["market_snapshots"], index=False)
    _wallet_snapshots().to_csv(paths["wallet_snapshots"], index=False)
    return paths


def _review_report(
    *,
    coordination_label: str = "coordinated_small_flow_candidate",
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "candidate_a",
                "timestamp_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "question": "Will a politics market resolve yes?",
                "max_severity": "high",
                "review_priority": "high",
                "insider_risk_review_label": (
                    "insider-risk review candidate: relative anomaly, low materiality"
                ),
                "materiality_label": "below_one_percent_of_reference",
                "coordination_label": coordination_label,
            }
        ]
    )


def _alert_rows(*, with_event: bool = False) -> pd.DataFrame:
    base = {
        "timestamp_utc": "2026-05-23T19:25:00Z",
        "market_id": "market_a",
        "tier": "all_tiers",
        "baseline_window": "last_30_completed_observations",
        "baseline_observations": 20,
        "rolling_median": 0.2,
        "rolling_mad": 0.1,
        "robust_z": 3.1,
        "rolling_percentile_rank": 1.0,
        "severity": "high",
        "status": "ok",
        "event_candidate_id": "event_a" if with_event else "",
        "event_review_status": "accepted" if with_event else "",
        "evidence_refs": "toy",
        "limitation": "toy aggregate row",
        "review_status": "candidate",
        "claim_scope": "descriptive_monitor_alert_only",
    }
    return pd.DataFrame(
        [
            {
                **base,
                "anomaly_family": "wallet_tier_activity",
                "metric_name": "log1p_total_observed_amount_usd",
                "observed_value": 4.0,
            },
            {
                **base,
                "anomaly_family": "concentration",
                "metric_name": "top_tier_share",
                "observed_value": 0.9,
            },
        ]
    )


def _market_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "bucket_end_utc": "2026-05-23T19:20:00Z",
                "market_id": "market_a",
                "midpoint": 0.1,
            },
            {
                "bucket_end_utc": "2026-05-23T19:20:00Z",
                "market_id": "market_a",
                "midpoint": 0.9,
            },
            {
                "bucket_end_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "midpoint": 0.3,
            },
            {
                "bucket_end_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "midpoint": 0.7,
            },
        ]
    )


def _wallet_snapshots(*, top_tier_share: float = 0.4, hhi: float = 0.3) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "bucket_end_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "top_tier_share": top_tier_share,
                "hhi_concentration": hhi,
            }
        ]
    )
