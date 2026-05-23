from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.wallet_reference_similarity import (
    build_reference_similarity_scores,
    build_reference_similarity_summary,
    generate_wallet_reference_similarity,
)


def test_similarity_scores_include_self_and_partial_overlap() -> None:
    features = _features()

    scores = build_reference_similarity_scores(features, features)

    self_score = scores[
        (scores["candidate_id"] == "large_flow_case")
        & (scores["reference_case_id"] == "large_flow_case")
    ].iloc[0]
    partial_score = scores[
        (scores["candidate_id"] == "large_flow_case")
        & (scores["reference_case_id"] == "cluster_case")
    ].iloc[0]
    assert self_score["similarity_score"] == 1.0
    assert self_score["match_label"] == "reference_self_profile"
    assert partial_score["similarity_score"] == pytest.approx(0.5)
    assert partial_score["match_label"] == "partial_reference_overlap"


def test_similarity_summary_selects_best_reference() -> None:
    scores = build_reference_similarity_scores(_features(), _features())

    summary = build_reference_similarity_summary(scores)

    row = summary[summary["candidate_id"] == "cluster_case"].iloc[0]
    assert row["best_reference_case_id"] == "cluster_case"
    assert row["best_similarity_score"] == 1.0


def test_similarity_rejects_wallet_address_columns() -> None:
    features = _features()
    features["wallet_address"] = "0x123"

    with pytest.raises(ValueError, match="wallet-address columns"):
        build_reference_similarity_scores(features, _features())


def test_similarity_rejects_missing_columns() -> None:
    features = _features().drop(columns=["claim_scope"])

    with pytest.raises(ValueError, match="missing required columns"):
        build_reference_similarity_scores(features, _features())


def test_generate_similarity_outputs_and_dashboard(tmp_path: Path) -> None:
    features_path = tmp_path / "features.csv"
    _features().to_csv(features_path, index=False)

    result = generate_wallet_reference_similarity(
        candidate_features_path=features_path,
        reference_features_path=features_path,
        scores_path=tmp_path / "scores.csv",
        summary_path=tmp_path / "summary.csv",
        figure_path=tmp_path / "matrix.png",
        dashboard_path=tmp_path / "dashboard.html",
        metadata_path=tmp_path / "metadata.json",
    )

    scores = pd.read_csv(result.scores_path)
    summary = pd.read_csv(result.summary_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dashboard = result.dashboard_path.read_text(encoding="utf-8")
    assert result.candidate_count == 2
    assert result.comparison_count == 4
    assert result.max_non_self_similarity == pytest.approx(0.5)
    assert len(scores) == 4
    assert len(summary) == 2
    assert result.figure_path.exists()
    assert "Wallet Reference Similarity" in dashboard
    assert metadata["outputs"]["contains_wallet_addresses"] is False


def _features() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case_id, case_type, triggered_patterns in (
        ("cluster_case", "reported_cluster", ("market_concentration", "event_proximity")),
        ("large_flow_case", "large_flow_reference", ("market_concentration", "large_trade_flow")),
    ):
        for pattern in (
            "market_concentration",
            "event_proximity",
            "large_trade_flow",
        ):
            rows.append(
                {
                    "case_id": case_id,
                    "case_type": case_type,
                    "pattern_label": pattern,
                    "feature_status": "triggered"
                    if pattern in triggered_patterns
                    else "unknown",
                    "fact_source": "reported" if pattern in triggered_patterns else "unknown",
                    "reason": "toy feature",
                    "evidence_status": "source_checked",
                    "claim_scope": "descriptive_reference_only",
                    "requires_human_review": True,
                }
            )
    return pd.DataFrame(rows)
