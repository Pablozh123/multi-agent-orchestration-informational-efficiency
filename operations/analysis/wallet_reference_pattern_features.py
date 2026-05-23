"""Create neutral pattern features from curated wallet reference cases."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_reference_case_audit import (
    REFERENCE_CASES_INPUT,
    audit_reference_cases,
)


FEATURE_OUTPUT = RESULTS_DIR / "wallet_reference_pattern_features.csv"
FEATURE_METADATA_OUTPUT = RESULTS_DIR / "wallet_reference_pattern_features_metadata.json"

PATTERN_LABELS = (
    "large_trade_flow",
    "market_concentration",
    "event_proximity",
    "fresh_wallet_or_short_history",
    "cluster_link_reported",
    "shared_funding_reported",
    "high_reported_win_rate",
    "same_theme_repeated_positions",
)

THEME_TERMS = ("iran", "geopolitic", "military", "ceasefire", "hormuz", "airspace")


@dataclass(frozen=True)
class PatternFeatureResult:
    """Summary of reference-pattern feature generation."""

    features_path: Path
    metadata_path: Path
    case_count: int
    feature_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly feature summary."""

        return {
            "features_path": str(self.features_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "feature_count": self.feature_count,
        }


def build_reference_pattern_features(cases: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic, neutral pattern rows for reference cases."""

    audit = audit_reference_cases(cases)
    failures = audit[audit["audit_status"] == "fail"]
    if not failures.empty:
        failed_cases = ", ".join(failures["case_id"].astype(str).tolist())
        raise ValueError(f"reference cases failed audit: {failed_cases}")

    rows: list[dict[str, object]] = []
    for case in cases.to_dict(orient="records"):
        rows.extend(_feature_rows_for_case(case))
    return pd.DataFrame(rows)


def generate_wallet_reference_pattern_features(
    *,
    input_path: Path = REFERENCE_CASES_INPUT,
    features_path: Path = FEATURE_OUTPUT,
    metadata_path: Path = FEATURE_METADATA_OUTPUT,
) -> PatternFeatureResult:
    """Generate compact pattern features from curated reference cases."""

    if not input_path.exists():
        raise FileNotFoundError(f"reference case file not found: {input_path}")
    cases = pd.read_csv(input_path, keep_default_na=False)
    features = build_reference_pattern_features(cases)

    features_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(features_path, index=False)
    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "wallet_reference_pattern_features",
            "pattern_labels": list(PATTERN_LABELS),
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_llms": True,
        },
        "inputs": {
            "input_path": str(input_path),
            "case_count": int(len(cases)),
            "contains_wallet_addresses": bool(cases["wallet_address"].astype(str).str.len().gt(0).any()),
        },
        "outputs": {
            "features_path": str(features_path),
            "feature_count": int(len(features)),
            "triggered_count": int((features["feature_status"] == "triggered").sum()),
            "unknown_count": int((features["feature_status"] == "unknown").sum()),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "reported_features_are_not_computed_market_truth": True,
            "unknown_features_require_additional_data": True,
            "reference_features_are_not_misconduct_claims": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PatternFeatureResult(
        features_path=features_path,
        metadata_path=metadata_path,
        case_count=int(len(cases)),
        feature_count=int(len(features)),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=REFERENCE_CASES_INPUT)
    parser.add_argument("--features-output", type=Path, default=FEATURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=FEATURE_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_wallet_reference_pattern_features(
            input_path=args.input,
            features_path=args.features_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _feature_rows_for_case(case: dict[str, Any]) -> list[dict[str, object]]:
    text = _case_text(case)
    linked_accounts = _int_or_zero(case.get("linked_accounts_count"))
    reported_win_rate = _float_or_none(case.get("reported_win_rate"))
    amount = _float_or_none(case.get("amount_usd"))
    case_type = str(case.get("case_type", ""))
    large_flow_reported = amount is not None and "large_flow" in case_type
    rows = [
        _feature_row(
            case,
            "large_trade_flow",
            "triggered" if large_flow_reported else "unknown",
            "reported" if amount is not None else "unknown",
            f"reported_amount_usd={amount:g}"
            if large_flow_reported
            else "large-flow status requires explicit source label or relative volume computation",
        ),
        _feature_row(
            case,
            "market_concentration",
            "triggered" if any(term in text for term in THEME_TERMS) else "unknown",
            "reported" if any(term in text for term in THEME_TERMS) else "unknown",
            "reference text maps to politics/geopolitics theme"
            if any(term in text for term in THEME_TERMS)
            else "theme concentration requires additional market history",
        ),
        _feature_row(
            case,
            "event_proximity",
            "triggered" if "shortly before" in text or "before developments" in text else "unknown",
            "reported" if "shortly before" in text or "before developments" in text else "unknown",
            "public reporting describes timing before developments"
            if "shortly before" in text or "before developments" in text
            else "requires timestamped event mapping",
        ),
        _feature_row(
            case,
            "fresh_wallet_or_short_history",
            "triggered" if "fresh" in text or "created" in text else "unknown",
            "reported" if "fresh" in text or "created" in text else "unknown",
            "short-history language appears in reference text"
            if "fresh" in text or "created" in text
            else "requires wallet creation or first-seen data",
        ),
        _feature_row(
            case,
            "cluster_link_reported",
            "triggered" if linked_accounts > 1 else "unknown",
            "reported" if linked_accounts > 1 else "unknown",
            "" if linked_accounts <= 1 else f"reported_linked_accounts={linked_accounts}",
        ),
        _feature_row(
            case,
            "shared_funding_reported",
            "triggered" if "funding" in text or "cex" in text else "unknown",
            "reported" if "funding" in text or "cex" in text else "unknown",
            "reference text reports funding timing or CEX routing"
            if "funding" in text or "cex" in text
            else "requires funding graph data",
        ),
        _feature_row(
            case,
            "high_reported_win_rate",
            "triggered" if reported_win_rate is not None and reported_win_rate >= 0.9 else "unknown",
            "reported" if reported_win_rate is not None else "unknown",
            "" if reported_win_rate is None else f"reported_win_rate={reported_win_rate:g}",
        ),
        _feature_row(
            case,
            "same_theme_repeated_positions",
            "triggered" if "more than 80" in text or "repeated" in text else "unknown",
            "reported" if "more than 80" in text or "repeated" in text else "unknown",
            "reference text reports repeated same-theme positions"
            if "more than 80" in text or "repeated" in text
            else "requires full position history",
        ),
    ]
    return rows


def _feature_row(
    case: dict[str, Any],
    pattern_label: str,
    feature_status: str,
    fact_source: str,
    reason: str,
) -> dict[str, object]:
    return {
        "case_id": str(case.get("case_id", "")),
        "case_type": str(case.get("case_type", "")),
        "pattern_label": pattern_label,
        "feature_status": feature_status,
        "fact_source": fact_source,
        "reason": reason,
        "evidence_status": str(case.get("evidence_status", "")),
        "claim_scope": str(case.get("claim_scope", "")),
        "requires_human_review": True,
    }


def _case_text(case: dict[str, Any]) -> str:
    return " ".join(
        str(case.get(column, ""))
        for column in ("case_id", "case_type", "market_title", "notes")
    ).lower()


def _float_or_none(value: object) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _int_or_zero(value: object) -> int:
    text = str(value).strip()
    if not text:
        return 0
    return int(text)


if __name__ == "__main__":
    raise SystemExit(main())
