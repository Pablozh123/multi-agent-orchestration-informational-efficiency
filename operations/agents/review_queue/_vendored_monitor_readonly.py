"""Read-only MCP tool layer (Stage 2) over bounded monitor anomaly-review artifacts.

This module implements exactly the four tools defined by the binding
``future_mcp_contract`` in
``data/results/monitor_anomaly_review_metadata.json``:

    - get_anomaly_review_summary()
    - get_anomaly_case(case_id)
    - list_monitor_artifacts()
    - get_method_limits()

Hard boundaries enforced here (see AGENTS.md and ARCHITECTURE_DECISIONS 14, 21,
22, plus monitor_anomaly_review_access_contract.json):

    - Read-only over existing bounded artifacts. No raw SQL. No database writes.
    - The ONLY write performed is an append to the audit sink (JSONL).
    - Every return is hard-capped to MAX_ROWS (<= 50) rows.
    - Wallet addresses (``0x`` + 40 hex) are masked in every output by default.
    - No metric calculation, no causal / insider / profitability commentary.
      This layer reshapes precomputed deterministic outputs only.

The module uses the Python standard library only (csv, json, datetime, re,
pathlib) so it can be vendored into the thesis repo without new dependencies.

Every public tool accepts a ``data_root`` argument so tests can point it at a
fixture tree instead of the real ``data/`` directory.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Cross-cutting constants
# ---------------------------------------------------------------------------

#: Hard cap on rows returned by any tool. Mirrors the contract ``max_rows``.
MAX_ROWS: int = 50

#: Default relative location of the bounded monitor result artifacts.
RESULTS_SUBDIR: str = "data/results"

#: Default append-only audit sink, relative to the data root. The thesis
#: workflow later mirrors these JSONL entries into the ``llm_audit_log`` table
#: in ``data/thesis.db`` (see MERGE_HANDOFF.md).
DEFAULT_AUDIT_PATH: str = "data/results/monitor_mcp_audit_log.jsonl"

#: Placeholder substituted for any detected wallet address.
WALLET_REDACTION_PLACEHOLDER: str = "[REDACTED_WALLET_ADDRESS]"

#: Wallet-address pattern: ``0x`` followed by exactly 40 hex chars and NOT
#: followed by another hex char. The trailing negative lookahead is essential:
#: the monitor ``market_id`` column carries 64-hex ERC-1155 token ids
#: (e.g. ``0xe6bcc2f1...`` 64 nibbles). Without the lookahead, a naive
#: ``{40}`` match would clip and corrupt those legitimate market ids. With it,
#: only true 20-byte wallet addresses are masked while market token ids are
#: preserved intact.
_WALLET_RE = re.compile(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")

#: Artifact registry mirroring monitor_anomaly_review_access_contract.json.
#: Maps the contract ``artifact_id`` to a relative path under the data root.
#: Only bounded, contract-allowed artifacts are listed here; raw alert/wallet
#: rows and the database are intentionally absent.
_ARTIFACTS: Dict[str, str] = {
    "anomaly_review_summary": "data/results/monitor_anomaly_review_summary.csv",
    "anomaly_review_queue": "data/results/monitor_anomaly_review_queue.csv",
    "anomaly_case_review_packets_csv": "data/results/monitor_anomaly_case_review_packets.csv",
    "anomaly_review_status_transitions_csv": "data/results/monitor_anomaly_review_status_transitions.csv",
    "anomaly_review_decision_readiness_csv": "data/results/monitor_anomaly_review_decision_readiness.csv",
    "anomaly_review_metadata": "data/results/monitor_anomaly_review_metadata.json",
}

#: Per-tool allow lists (artifact ids the tool may read). Mirrors the
#: ``future_tool_contracts`` block in the access contract.
_TOOL_ARTIFACT_ALLOW: Dict[str, List[str]] = {
    "get_anomaly_review_summary": ["anomaly_review_summary"],
    "get_anomaly_case": [
        "anomaly_review_queue",
        "anomaly_case_review_packets_csv",
        "anomaly_review_status_transitions_csv",
        "anomaly_review_decision_readiness_csv",
    ],
    "list_monitor_artifacts": [
        "anomaly_review_summary",
        "anomaly_review_queue",
        "anomaly_case_review_packets_csv",
        "anomaly_review_status_transitions_csv",
        "anomaly_review_decision_readiness_csv",
    ],
    "get_method_limits": ["anomaly_review_metadata"],
}

#: Documented limit keys that get_method_limits must always surface. Tests
#: assert each of these is present so the contract cannot silently drift.
METHOD_LIMIT_KEYS: List[str] = [
    "max_rows",
    "raw_sql_allowed",
    "wallet_address_exposure_allowed_by_default",
    "order_or_trading_path_allowed",
    "llm_audit_log_required",
    "tools",
    "status",
]


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def redact_wallet_addresses(value: Any) -> Any:
    """Recursively mask any ``0x``+40-hex wallet address in ``value``.

    Operates on arbitrarily nested ``dict`` / ``list`` / ``str`` structures and
    returns a structurally identical copy with every wallet address replaced by
    ``WALLET_REDACTION_PLACEHOLDER``. Non-string scalars pass through unchanged.

    Market token ids (``0x`` + 64 hex) and other hex strings are intentionally
    left intact (see ``_WALLET_RE``). The default contract posture is that no
    wallet address is ever emitted, so every tool routes its payload through
    this function before returning.
    """
    if isinstance(value, str):
        return _WALLET_RE.sub(WALLET_REDACTION_PLACEHOLDER, value)
    if isinstance(value, dict):
        return {key: redact_wallet_addresses(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_wallet_addresses(item) for item in value]
    return value


def _contains_wallet_address(value: Any) -> bool:
    """Return True if any string anywhere in ``value`` still matches a wallet."""
    if isinstance(value, str):
        return bool(_WALLET_RE.search(value))
    if isinstance(value, dict):
        return any(_contains_wallet_address(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_wallet_address(item) for item in value)
    return False


# ---------------------------------------------------------------------------
# Path / IO helpers (read-only)
# ---------------------------------------------------------------------------

def _resolve_root(data_root: Optional[Union[str, Path]]) -> Path:
    """Resolve the data root. Defaults to the current working directory.

    ``data_root`` is the directory that *contains* the ``data/`` tree (i.e. the
    repo root for production, or a fixture root in tests). Defaulting to the
    current working directory keeps the production call site (``python -m`` from
    the repo root) working without arguments.
    """
    if data_root is None:
        return Path.cwd()
    return Path(data_root)


def _artifact_path(root: Path, artifact_id: str) -> Path:
    rel = _ARTIFACTS[artifact_id]
    return root / rel


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """Read a CSV into a list of dict rows. Returns [] if the file is absent.

    Reading is strictly local and read-only. No SQL, no network. Rows are
    returned in file order to preserve determinism.
    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _cap_rows(rows: List[Any], limit: int = MAX_ROWS) -> List[Any]:
    """Hard-cap a row list to ``min(limit, MAX_ROWS)`` (never above MAX_ROWS)."""
    effective = min(limit, MAX_ROWS)
    return rows[:effective]


# ---------------------------------------------------------------------------
# Audit sink (the only write path)
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    """Deterministic-format UTC timestamp, e.g. ``2026-06-16T12:00:00+00:00``."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_audit_entry(
    *,
    tool: str,
    args: Dict[str, Any],
    row_count: int,
    root: Path,
    audit_path: Optional[Union[str, Path]],
) -> Dict[str, Any]:
    """Append exactly one audit record and return it.

    The record shape is ``{tool, args, row_count, ts_utc}``. Arguments are
    redacted before logging so wallet addresses never leak into the audit
    trail either. This append is the sole write performed by the module; it is
    the bridge later mirrored into the ``llm_audit_log`` table.
    """
    if audit_path is None:
        resolved = root / DEFAULT_AUDIT_PATH
    else:
        candidate = Path(audit_path)
        resolved = candidate if candidate.is_absolute() else root / candidate

    entry = {
        "tool": tool,
        "args": redact_wallet_addresses(dict(args)),
        "row_count": int(row_count),
        "ts_utc": _utc_now_iso(),
    }
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


# ---------------------------------------------------------------------------
# Tool 1: get_anomaly_review_summary
# ---------------------------------------------------------------------------

def get_anomaly_review_summary(
    data_root: Optional[Union[str, Path]] = None,
    audit_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Return the single bounded anomaly-review summary row.

    Reads ``monitor_anomaly_review_summary.csv`` (contract row_count = 1) and
    returns it as a bounded, wallet-redacted payload. Calculates nothing; it
    only reshapes the precomputed summary row.
    """
    root = _resolve_root(data_root)
    rows = _read_csv_rows(_artifact_path(root, "anomaly_review_summary"))
    rows = _cap_rows(rows, limit=1)
    rows = redact_wallet_addresses(rows)
    payload: Dict[str, Any] = {
        "tool": "get_anomaly_review_summary",
        "artifact_id": "anomaly_review_summary",
        "row_count": len(rows),
        "rows": rows,
        "allowed_interpretation": (
            "Bounded deterministic human-review summary over existing monitor "
            "artifacts only."
        ),
    }
    _write_audit_entry(
        tool="get_anomaly_review_summary",
        args={},
        row_count=len(rows),
        root=root,
        audit_path=audit_path,
    )
    return payload


# ---------------------------------------------------------------------------
# Tool 2: get_anomaly_case
# ---------------------------------------------------------------------------

def get_anomaly_case(
    case_id: str,
    data_root: Optional[Union[str, Path]] = None,
    audit_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Return the bounded review record for a single ``case_id``.

    Joins the queue row, case-review packet, status-transition row, and
    decision-readiness row for the requested case across the contract-allowed
    artifacts. Matching is an exact string match on the ``case_id`` column.

    An unknown ``case_id`` is handled cleanly: the payload reports
    ``found = False`` with empty sections (never an exception, never a leak),
    and a single audit entry with ``row_count = 0`` is still written.
    """
    root = _resolve_root(data_root)
    requested = "" if case_id is None else str(case_id)

    section_artifacts = {
        "queue": "anomaly_review_queue",
        "case_review_packet": "anomaly_case_review_packets_csv",
        "status_transition": "anomaly_review_status_transitions_csv",
        "decision_readiness": "anomaly_review_decision_readiness_csv",
    }

    sections: Dict[str, List[Dict[str, str]]] = {}
    total_matched = 0
    for section, artifact_id in section_artifacts.items():
        all_rows = _read_csv_rows(_artifact_path(root, artifact_id))
        matched = [r for r in all_rows if r.get("case_id") == requested]
        matched = _cap_rows(matched)
        total_matched += len(matched)
        sections[section] = matched

    sections = redact_wallet_addresses(sections)
    found = total_matched > 0

    payload: Dict[str, Any] = {
        "tool": "get_anomaly_case",
        "case_id": requested,
        "found": found,
        "row_count": total_matched,
        "sections": sections,
        "allowed_interpretation": (
            "Bounded deterministic review cue for a single case; not a metric, "
            "not a misconduct or private-information finding."
        ),
    }
    if not found:
        payload["message"] = "No bounded review record found for the requested case_id."

    _write_audit_entry(
        tool="get_anomaly_case",
        args={"case_id": requested},
        row_count=total_matched,
        root=root,
        audit_path=audit_path,
    )
    return payload


# ---------------------------------------------------------------------------
# Tool 3: list_monitor_artifacts
# ---------------------------------------------------------------------------

def list_monitor_artifacts(
    data_root: Optional[Union[str, Path]] = None,
    audit_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """List the bounded artifacts this read-only layer may expose.

    Returns one bounded descriptor per contract-allowed artifact reachable by
    the summary/queue/packet/transition/readiness tools, with existence and
    observed row count. Reads only file metadata and headers; emits no wallet
    addresses and computes no statistics.
    """
    root = _resolve_root(data_root)
    artifact_ids = _TOOL_ARTIFACT_ALLOW["list_monitor_artifacts"]

    descriptors: List[Dict[str, Any]] = []
    for artifact_id in artifact_ids:
        path = _artifact_path(root, artifact_id)
        rows = _read_csv_rows(path)
        descriptors.append(
            {
                "artifact_id": artifact_id,
                "relative_path": _ARTIFACTS[artifact_id],
                "exists": path.exists(),
                "row_count": len(rows),
                "default_access": (
                    "allowed" if artifact_id == "anomaly_review_summary" else "allowed_bounded"
                ),
            }
        )

    descriptors = _cap_rows(descriptors)
    descriptors = redact_wallet_addresses(descriptors)
    payload: Dict[str, Any] = {
        "tool": "list_monitor_artifacts",
        "row_count": len(descriptors),
        "artifacts": descriptors,
        "allowed_interpretation": (
            "Inventory of bounded monitor review artifacts available to the "
            "read-only layer."
        ),
    }
    _write_audit_entry(
        tool="list_monitor_artifacts",
        args={},
        row_count=len(descriptors),
        root=root,
        audit_path=audit_path,
    )
    return payload


# ---------------------------------------------------------------------------
# Tool 4: get_method_limits
# ---------------------------------------------------------------------------

def get_method_limits(
    data_root: Optional[Union[str, Path]] = None,
    audit_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Return the documented method limits and tool boundaries.

    Sources the ``future_mcp_contract`` block from
    ``monitor_anomaly_review_metadata.json`` and re-exposes it as a flat
    ``limits`` mapping that always contains every key in ``METHOD_LIMIT_KEYS``.
    If the metadata file is unavailable, conservative module constants are used
    so the contract surface is always present (never a silent gap).
    """
    root = _resolve_root(data_root)
    metadata = _read_json(_artifact_path(root, "anomaly_review_metadata"))
    contract: Dict[str, Any] = {}
    if isinstance(metadata, dict):
        maybe = metadata.get("future_mcp_contract")
        if isinstance(maybe, dict):
            contract = maybe

    limits: Dict[str, Any] = {
        "max_rows": int(contract.get("max_rows", MAX_ROWS)),
        "raw_sql_allowed": bool(contract.get("raw_sql_allowed", False)),
        "wallet_address_exposure_allowed_by_default": bool(
            contract.get("wallet_address_exposure_allowed_by_default", False)
        ),
        "order_or_trading_path_allowed": bool(
            contract.get("order_or_trading_path_allowed", False)
        ),
        "llm_audit_log_required": bool(contract.get("llm_audit_log_required", True)),
        "tools": list(
            contract.get(
                "tools",
                [
                    "get_anomaly_review_summary",
                    "get_anomaly_case",
                    "list_monitor_artifacts",
                    "get_method_limits",
                ],
            )
        ),
        "status": str(contract.get("status", "contract_only_not_implemented")),
    }
    # The implementation never exceeds MAX_ROWS regardless of metadata drift.
    limits["max_rows"] = min(limits["max_rows"], MAX_ROWS)

    limits = redact_wallet_addresses(limits)
    payload: Dict[str, Any] = {
        "tool": "get_method_limits",
        "row_count": 1,
        "limits": limits,
        "blocked_claims": (
            "private_information_proof; misconduct_finding; causality; "
            "tradeability; profitability; future_performance; order_instruction"
        ),
        "allowed_interpretation": (
            "Documented read-only contract limits for the monitor MCP layer."
        ),
    }
    _write_audit_entry(
        tool="get_method_limits",
        args={},
        row_count=1,
        root=root,
        audit_path=audit_path,
    )
    return payload


# ---------------------------------------------------------------------------
# Tool registry (used by the thin server entry point)
# ---------------------------------------------------------------------------

#: Public tool name -> callable. Imported by server.py so registration stays a
#: single source of truth.
TOOLS = {
    "get_anomaly_review_summary": get_anomaly_review_summary,
    "get_anomaly_case": get_anomaly_case,
    "list_monitor_artifacts": list_monitor_artifacts,
    "get_method_limits": get_method_limits,
}


__all__ = [
    "MAX_ROWS",
    "METHOD_LIMIT_KEYS",
    "WALLET_REDACTION_PLACEHOLDER",
    "DEFAULT_AUDIT_PATH",
    "TOOLS",
    "redact_wallet_addresses",
    "get_anomaly_review_summary",
    "get_anomaly_case",
    "list_monitor_artifacts",
    "get_method_limits",
]
