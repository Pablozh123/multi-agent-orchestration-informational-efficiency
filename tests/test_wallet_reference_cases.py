from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.wallet_reference_case_audit import (
    audit_reference_cases,
    generate_wallet_reference_case_audit,
)
from operations.analysis.wallet_reference_pattern_features import (
    build_reference_pattern_features,
    generate_wallet_reference_pattern_features,
)


def test_valid_reference_cases_pass_audit(tmp_path: Path) -> None:
    input_path = tmp_path / "cases.csv"
    _valid_cases().to_csv(input_path, index=False)

    result = generate_wallet_reference_case_audit(
        input_path=input_path,
        audit_path=tmp_path / "audit.csv",
        metadata_path=tmp_path / "audit_metadata.json",
    )

    audit = pd.read_csv(result.audit_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert result.failed_count == 0
    assert audit["audit_status"].tolist() == ["pass", "pass"]
    assert "wallet_address" not in audit.columns
    assert metadata["outputs"]["contains_wallet_addresses"] is False


def test_invalid_wallet_address_fails_audit() -> None:
    cases = _valid_cases()
    cases.loc[1, "wallet_address"] = "0xBAD"

    audit = audit_reference_cases(cases)

    failed = audit[audit["audit_status"] == "fail"]
    assert len(failed) == 1
    assert "wallet_address must be lowercase" in failed.iloc[0]["errors"]


def test_missing_source_url_fails_audit() -> None:
    cases = _valid_cases()
    cases.loc[0, "source_url"] = ""

    audit = audit_reference_cases(cases)

    assert audit.loc[0, "audit_status"] == "fail"
    assert "source_url is required" in audit.loc[0, "errors"]


def test_reported_values_remain_reported_not_computed(tmp_path: Path) -> None:
    input_path = tmp_path / "cases.csv"
    _valid_cases().to_csv(input_path, index=False)

    result = generate_wallet_reference_pattern_features(
        input_path=input_path,
        features_path=tmp_path / "features.csv",
        metadata_path=tmp_path / "features_metadata.json",
    )

    features = pd.read_csv(result.features_path)
    assert result.feature_count == 16
    high_win = features[
        (features["case_id"] == "iran_cluster_2026_bubblemaps_reported")
        & (features["pattern_label"] == "high_reported_win_rate")
    ].iloc[0]
    assert high_win["feature_status"] == "triggered"
    assert high_win["fact_source"] == "reported"


def test_large_trade_and_theme_features_trigger() -> None:
    features = build_reference_pattern_features(_valid_cases())

    adrian_large = features[
        (features["case_id"] == "adriancronauer_large_iran_flow_2026_05_14")
        & (features["pattern_label"] == "large_trade_flow")
    ].iloc[0]
    adrian_theme = features[
        (features["case_id"] == "adriancronauer_large_iran_flow_2026_05_14")
        & (features["pattern_label"] == "market_concentration")
    ].iloc[0]
    assert adrian_large["feature_status"] == "triggered"
    assert "reported_amount_usd=103248" in adrian_large["reason"]
    assert adrian_theme["feature_status"] == "triggered"


def test_missing_funding_data_returns_unknown() -> None:
    features = build_reference_pattern_features(_valid_cases())

    adrian_funding = features[
        (features["case_id"] == "adriancronauer_large_iran_flow_2026_05_14")
        & (features["pattern_label"] == "shared_funding_reported")
    ].iloc[0]
    assert adrian_funding["feature_status"] == "unknown"
    assert adrian_funding["fact_source"] == "unknown"


def _valid_cases() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "case_id": "iran_cluster_2026_bubblemaps_reported",
                "case_type": "reported_cluster",
                "source_url": "https://www.cbsnews.com/example",
                "source_name": "CBS 60 Minutes",
                "handle": "reported_nine_account_cluster",
                "wallet_address": "",
                "market_title": "US military actions involving Iran",
                "side": "",
                "amount_usd": "",
                "price": "",
                "shares": "",
                "observed_at_utc": "",
                "reported_pnl": "2400000",
                "reported_win_rate": "0.98",
                "linked_accounts_count": "9",
                "evidence_status": "source_checked",
                "claim_scope": "reported_reference_case_only",
                "notes": (
                    "Reported more than 80 repeated military bets shortly before "
                    "developments with similar funding timing and CEX routing."
                ),
            },
            {
                "case_id": "adriancronauer_large_iran_flow_2026_05_14",
                "case_type": "large_flow_reference",
                "source_url": "https://x.com/PolymarketStory/status/2051659961260753294",
                "source_name": "PolymarketStory",
                "handle": "AdrianCronauer",
                "wallet_address": "0xf9c1190aa8184bcbe418e6f5321c53b0bfbc39e2",
                "market_title": "US x Iran permanent peace deal by May 31 2026?",
                "side": "NO",
                "amount_usd": "103248",
                "price": "0.87",
                "shares": "",
                "observed_at_utc": "2026-05-14T08:56:00Z",
                "reported_pnl": "",
                "reported_win_rate": "",
                "linked_accounts_count": "1",
                "evidence_status": "source_checked",
                "claim_scope": "large_flow_reference_only",
                "notes": "Reported large concentrated Iran flow example.",
            },
        ]
    )
