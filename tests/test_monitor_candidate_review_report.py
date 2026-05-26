from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.monitor_candidate_review_report import (
    REPORT_COLUMNS,
    build_human_review_report,
    generate_monitor_candidate_human_review_report,
)


def test_build_human_review_report_groups_strict_candidates() -> None:
    report = build_human_review_report(
        alert_rows=_alert_rows(),
        watchlist=_watchlist(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
        similarity_summary=_similarity_summary(),
        candidate_features=_candidate_features(),
        reference_cases=_reference_cases(),
        risk_score_summary=_risk_score_summary(),
    )

    assert tuple(report.columns) == REPORT_COLUMNS
    assert len(report) == 2
    high = report[report["review_priority"] == "high"].iloc[0]
    assert high["question"] == "Will a politics market resolve yes?"
    assert high["triggered_patterns"] == "large_trade_flow,market_concentration"
    assert high["best_similarity_score"] == pytest.approx(1.0)
    assert high["insider_risk_review_label"] == (
        "insider-risk review candidate: relative anomaly, low materiality"
    )
    assert high["materiality_label"] == "below_one_percent_of_reference"
    assert high["reference_amount_ratio"] == pytest.approx(250.0 / 103248.0)
    assert high["literature_wallet_risk_score"] == pytest.approx(2.7)
    assert high["literature_market_risk_flag"] == "literature_prior_flag"
    assert "human review only" in high["allowed_interpretation"]
    assert "wallet_address" not in report.columns


def test_market_only_candidate_stays_low_priority() -> None:
    report = build_human_review_report(
        alert_rows=_alert_rows(include_wallet_candidate=False),
        watchlist=_watchlist(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(),
        similarity_summary=_similarity_summary(),
        candidate_features=_candidate_features(),
        reference_cases=_reference_cases(),
    )

    assert set(report["review_priority"]) == {"low"}
    assert set(report["triggered_patterns"]) == {""}


def test_single_wallet_small_flow_is_not_coordination_candidate() -> None:
    report = build_human_review_report(
        alert_rows=_alert_rows(),
        watchlist=_watchlist(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(
            politics_active_wallets=1,
            politics_trade_count=1,
            politics_amount=64.28,
        ),
        similarity_summary=_similarity_summary(),
        candidate_features=_candidate_features(),
        reference_cases=_reference_cases(),
    )

    high = report[report["review_priority"] == "high"].iloc[0]
    assert high["coordination_label"] == "single_wallet_single_trade"
    assert "not a computed insider label" in high["allowed_interpretation"]


def test_multi_wallet_small_flow_is_coordination_candidate() -> None:
    report = build_human_review_report(
        alert_rows=_alert_rows(),
        watchlist=_watchlist(),
        market_snapshots=_market_snapshots(),
        wallet_tier_snapshots=_wallet_snapshots(
            politics_active_wallets=6,
            politics_trade_count=8,
            politics_amount=480.0,
        ),
        similarity_summary=_similarity_summary(),
        candidate_features=_candidate_features(),
        reference_cases=_reference_cases(),
    )

    high = report[report["review_priority"] == "high"].iloc[0]
    assert high["coordination_label"] == "coordinated_small_flow_candidate"
    assert high["insider_risk_review_label"] == (
        "insider-risk review candidate: coordinated small-flow hypothesis"
    )


def test_generate_human_review_report_writes_outputs(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    result = generate_monitor_candidate_human_review_report(
        alert_rows_path=paths["alert_rows_path"],
        watchlist_path=paths["watchlist_path"],
        market_snapshots_path=paths["market_snapshots_path"],
        wallet_tier_snapshots_path=paths["wallet_tier_snapshots_path"],
        similarity_summary_path=paths["similarity_summary_path"],
        candidate_features_path=paths["candidate_features_path"],
        reference_cases_path=paths["reference_cases_path"],
        risk_score_summary_path=paths["risk_score_summary_path"],
        report_path=tmp_path / "report.csv",
        dashboard_path=tmp_path / "report.html",
        metadata_path=tmp_path / "metadata.json",
        materiality_context_path=tmp_path / "materiality.csv",
    )

    report = pd.read_csv(result.report_path)
    materiality = pd.read_csv(result.materiality_context_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    assert result.candidate_count == 2
    assert result.high_priority_count == 1
    assert result.max_similarity_score == pytest.approx(1.0)
    assert len(report) == 2
    assert len(materiality) == 2
    assert "Insider-Risk Candidate Human Review" in dashboard
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["contains_computed_insider_label"] is False
    assert metadata["method"]["does_not_collect_external_data"] is True


def test_review_report_rejects_wallet_address_columns() -> None:
    rows = _alert_rows()
    rows["wallet_address"] = "0x" + "a" * 40

    with pytest.raises(ValueError, match="wallet-address columns"):
        build_human_review_report(
            alert_rows=rows,
            watchlist=_watchlist(),
            market_snapshots=_market_snapshots(),
            wallet_tier_snapshots=_wallet_snapshots(),
            similarity_summary=_similarity_summary(),
            candidate_features=_candidate_features(),
            reference_cases=_reference_cases(),
        )


def _write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "alert_rows_path": root / "alerts.csv",
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "similarity_summary_path": root / "similarity.csv",
        "candidate_features_path": root / "features.csv",
        "reference_cases_path": root / "reference_cases.csv",
        "risk_score_summary_path": root / "risk_scores.csv",
    }
    _alert_rows().to_csv(paths["alert_rows_path"], index=False)
    _watchlist().to_csv(paths["watchlist_path"], index=False)
    _market_snapshots().to_csv(paths["market_snapshots_path"], index=False)
    _wallet_snapshots().to_csv(paths["wallet_tier_snapshots_path"], index=False)
    _similarity_summary().to_csv(paths["similarity_summary_path"], index=False)
    _candidate_features().to_csv(paths["candidate_features_path"], index=False)
    _reference_cases().to_csv(paths["reference_cases_path"], index=False)
    _risk_score_summary().to_csv(paths["risk_score_summary_path"], index=False)
    return paths


def _alert_rows(*, include_wallet_candidate: bool = True) -> pd.DataFrame:
    rows = [_base_alert("market_a", "market_move", "absolute_midpoint_change", "info")]
    if include_wallet_candidate:
        rows.extend(
            [
                _base_alert(
                    "market_b",
                    "wallet_tier_activity",
                    "log1p_total_observed_amount_usd",
                    "high",
                ),
                _base_alert("market_b", "concentration", "top_tier_share", "watch"),
            ]
        )
    return pd.DataFrame(rows)


def _base_alert(
    market_id: str,
    family: str,
    metric: str,
    severity: str,
) -> dict[str, object]:
    return {
        "timestamp_utc": "2026-05-23T19:25:00Z",
        "market_id": market_id,
        "tier": "all_tiers",
        "anomaly_family": family,
        "metric_name": metric,
        "observed_value": 1.0,
        "baseline_window": "last_30_completed_observations",
        "baseline_observations": 20,
        "rolling_median": 0.2,
        "rolling_mad": 0.1,
        "robust_z": 2.0 if severity == "high" else 0.5,
        "rolling_percentile_rank": 1.0,
        "severity": severity,
        "status": "ok",
        "event_candidate_id": "",
        "event_review_status": "",
        "evidence_refs": "toy",
        "limitation": "toy aggregate row",
        "review_status": "candidate",
        "claim_scope": "descriptive_monitor_alert_only",
    }


def _watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "market_id": "market_a",
                "question": "Will a geopolitics market resolve yes?",
                "category": "geopolitics",
                "subcategory": "example-a",
            },
            {
                "market_id": "market_b",
                "question": "Will a politics market resolve yes?",
                "category": "politics",
                "subcategory": "example-b",
            },
        ]
    )


def _market_snapshots() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"bucket_end_utc": "2026-05-23T19:25:00Z", "market_id": "market_a", "midpoint": 0.1},
            {"bucket_end_utc": "2026-05-23T19:25:00Z", "market_id": "market_a", "midpoint": 0.9},
            {"bucket_end_utc": "2026-05-23T19:25:00Z", "market_id": "market_b", "midpoint": 0.2},
            {"bucket_end_utc": "2026-05-23T19:25:00Z", "market_id": "market_b", "midpoint": 0.8},
        ]
    )


def _wallet_snapshots(
    *,
    politics_active_wallets: int = 2,
    politics_trade_count: int = 3,
    politics_amount: float = 250.0,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "bucket_end_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_a",
                "active_wallets": 1,
                "trade_count": 1,
                "total_observed_amount_usd": 5.0,
            },
            {
                "bucket_end_utc": "2026-05-23T19:25:00Z",
                "market_id": "market_b",
                "active_wallets": politics_active_wallets,
                "trade_count": politics_trade_count,
                "total_observed_amount_usd": politics_amount,
            },
        ]
    )


def _similarity_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "monitor_candidate_20260523_192500_59eaabd2071a",
                "candidate_type": "monitor_alert_candidate",
                "best_reference_case_id": "reference_a",
                "best_reference_case_type": "large_flow_reference",
                "best_similarity_score": 0.0,
                "matched_patterns": "",
                "match_label": "no_reference_overlap",
                "allowed_interpretation": "review cue only",
                "limitation": "toy",
            },
            {
                "candidate_id": "monitor_candidate_20260523_192500_8100edf5ad39",
                "candidate_type": "monitor_alert_candidate",
                "best_reference_case_id": "reference_b",
                "best_reference_case_type": "large_flow_reference",
                "best_similarity_score": 1.0,
                "matched_patterns": "large_trade_flow,market_concentration",
                "match_label": "complete_reference_overlap",
                "allowed_interpretation": "review cue only",
                "limitation": "toy",
            },
        ]
    )


def _candidate_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "monitor_candidate_20260523_192500_8100edf5ad39",
                "case_type": "monitor_alert_candidate",
                "pattern_label": "large_trade_flow",
                "feature_status": "triggered",
                "fact_source": "computed",
                "reason": "toy",
                "evidence_status": "pattern_computed",
                "claim_scope": "monitor_reference_candidate_only",
                "requires_human_review": True,
            },
            {
                "case_id": "monitor_candidate_20260523_192500_8100edf5ad39",
                "case_type": "monitor_alert_candidate",
                "pattern_label": "market_concentration",
                "feature_status": "triggered",
                "fact_source": "computed",
                "reason": "toy",
                "evidence_status": "pattern_computed",
                "claim_scope": "monitor_reference_candidate_only",
                "requires_human_review": True,
            },
        ]
    )


def _reference_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "reference_a",
                "case_type": "reported_cluster",
                "handle": "reported_cluster",
                "amount_usd": "",
            },
            {
                "case_id": "reference_b",
                "case_type": "large_flow_reference",
                "handle": "AdrianCronauer",
                "amount_usd": 103248.0,
            },
        ]
    )


def _risk_score_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "monitor_candidate_20260523_192500_8100edf5ad39",
                "literature_wallet_risk_score": 2.7,
                "literature_wallet_risk_flag": "no_literature_prior_flag",
                "literature_market_risk_score": 1.1,
                "literature_market_risk_flag": "literature_prior_flag",
                "feature_status_summary": "computed_proxy=4; unavailable=3",
            }
        ]
    )
