"""Validate curated wallet reference cases for neutral pattern review."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR


REFERENCE_CASES_INPUT = Path("data/reference_cases/wallet_reference_cases.csv")
AUDIT_OUTPUT = RESULTS_DIR / "wallet_reference_case_audit.csv"
AUDIT_METADATA_OUTPUT = RESULTS_DIR / "wallet_reference_case_audit_metadata.json"

REQUIRED_COLUMNS = (
    "case_id",
    "case_type",
    "source_url",
    "source_name",
    "handle",
    "wallet_address",
    "market_title",
    "side",
    "amount_usd",
    "price",
    "shares",
    "observed_at_utc",
    "reported_pnl",
    "reported_win_rate",
    "linked_accounts_count",
    "evidence_status",
    "claim_scope",
    "notes",
)

ALLOWED_REVIEW_STATES = {
    "candidate",
    "source_checked",
    "market_mapped",
    "wallet_verified",
    "pattern_computed",
    "accepted_reference_case",
    "rejected_or_unverifiable",
}

ALLOWED_CLAIM_SCOPES = {
    "reported_reference_case_only",
    "large_flow_reference_only",
    "descriptive_reference_only",
}

WALLET_PATTERN = re.compile(r"^0x[a-f0-9]{40}$")


@dataclass(frozen=True)
class ReferenceCaseAuditResult:
    """Summary of a reference-case audit run."""

    audit_path: Path
    metadata_path: Path
    case_count: int
    failed_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly audit summary."""

        return {
            "audit_path": str(self.audit_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "failed_count": self.failed_count,
        }


def audit_reference_cases(cases: pd.DataFrame) -> pd.DataFrame:
    """Return compact validation rows for curated reference cases."""

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in cases.columns]
    if missing_columns:
        raise ValueError("missing required columns: " + ", ".join(missing_columns))

    rows: list[dict[str, object]] = []
    for raw_case in cases.loc[:, list(REQUIRED_COLUMNS)].to_dict(orient="records"):
        errors = _case_errors(raw_case)
        rows.append(
            {
                "case_id": str(raw_case["case_id"]),
                "case_type": str(raw_case["case_type"]),
                "evidence_status": str(raw_case["evidence_status"]),
                "claim_scope": str(raw_case["claim_scope"]),
                "audit_status": "fail" if errors else "pass",
                "error_count": len(errors),
                "errors": "; ".join(errors),
                "contains_wallet_address": bool(_clean(raw_case.get("wallet_address"))),
            }
        )
    return pd.DataFrame(rows)


def generate_wallet_reference_case_audit(
    *,
    input_path: Path = REFERENCE_CASES_INPUT,
    audit_path: Path = AUDIT_OUTPUT,
    metadata_path: Path = AUDIT_METADATA_OUTPUT,
) -> ReferenceCaseAuditResult:
    """Validate reference cases and write compact audit artifacts."""

    if not input_path.exists():
        raise FileNotFoundError(f"reference case file not found: {input_path}")
    cases = pd.read_csv(input_path, keep_default_na=False)
    audit = audit_reference_cases(cases)

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(audit_path, index=False)
    failed_count = int((audit["audit_status"] == "fail").sum())
    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "wallet_reference_case_audit",
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
            "audit_path": str(audit_path),
            "failed_count": failed_count,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "reported_facts_are_not_computed_facts": True,
            "reference_cases_are_not_misconduct_claims": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ReferenceCaseAuditResult(
        audit_path=audit_path,
        metadata_path=metadata_path,
        case_count=int(len(cases)),
        failed_count=failed_count,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=REFERENCE_CASES_INPUT)
    parser.add_argument("--audit-output", type=Path, default=AUDIT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=AUDIT_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_wallet_reference_case_audit(
            input_path=args.input,
            audit_path=args.audit_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.failed_count == 0 else 1


def _case_errors(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require_text(case, "case_id", errors)
    _require_text(case, "case_type", errors)
    _require_text(case, "source_name", errors)
    _require_url(case, "source_url", errors)
    _require_text(case, "evidence_status", errors)
    _require_text(case, "claim_scope", errors)

    wallet = _clean(case.get("wallet_address"))
    if wallet and WALLET_PATTERN.fullmatch(wallet) is None:
        errors.append("wallet_address must be lowercase 42-character 0x hex if present")

    observed_at = _clean(case.get("observed_at_utc"))
    if observed_at:
        _parse_datetime(observed_at, "observed_at_utc", errors)

    evidence_status = _clean(case.get("evidence_status"))
    if evidence_status and evidence_status not in ALLOWED_REVIEW_STATES:
        errors.append("evidence_status is not an allowed review state")

    claim_scope = _clean(case.get("claim_scope"))
    if claim_scope and claim_scope not in ALLOWED_CLAIM_SCOPES:
        errors.append("claim_scope is not allowed")

    _optional_nonnegative_number(case, "amount_usd", errors)
    _optional_nonnegative_number(case, "shares", errors)
    _optional_nonnegative_number(case, "reported_pnl", errors)
    _optional_int_at_least(case, "linked_accounts_count", 1, errors)
    _optional_probability(case, "price", errors)
    _optional_probability(case, "reported_win_rate", errors)
    return errors


def _require_text(case: dict[str, Any], column: str, errors: list[str]) -> None:
    if not _clean(case.get(column)):
        errors.append(f"{column} is required")


def _require_url(case: dict[str, Any], column: str, errors: list[str]) -> None:
    value = _clean(case.get(column))
    if not value:
        errors.append(f"{column} is required")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"{column} must be an http(s) URL")


def _optional_nonnegative_number(
    case: dict[str, Any],
    column: str,
    errors: list[str],
) -> None:
    value = _clean(case.get(column))
    if not value:
        return
    try:
        if float(value) < 0:
            errors.append(f"{column} must be >= 0")
    except ValueError:
        errors.append(f"{column} must be numeric if present")


def _optional_probability(case: dict[str, Any], column: str, errors: list[str]) -> None:
    value = _clean(case.get(column))
    if not value:
        return
    try:
        number = float(value)
    except ValueError:
        errors.append(f"{column} must be numeric if present")
        return
    if number < 0 or number > 1:
        errors.append(f"{column} must be between 0 and 1")


def _optional_int_at_least(
    case: dict[str, Any],
    column: str,
    minimum: int,
    errors: list[str],
) -> None:
    value = _clean(case.get(column))
    if not value:
        return
    try:
        number = int(value)
    except ValueError:
        errors.append(f"{column} must be an integer if present")
        return
    if number < minimum:
        errors.append(f"{column} must be >= {minimum}")


def _parse_datetime(value: str, column: str, errors: list[str]) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{column} must parse as ISO datetime")


def _clean(value: object) -> str:
    return str(value).strip()


if __name__ == "__main__":
    raise SystemExit(main())
