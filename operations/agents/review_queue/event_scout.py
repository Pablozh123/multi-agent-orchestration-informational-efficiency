"""EventScout: normalize *sourced* event candidates. Never invents events.

The EventScout takes a caller-supplied list of evidenced event candidates and
returns a normalized candidate list. Each input candidate MUST carry a real
source: a ``source_url`` and a ``utc_timestamp`` (and an optional ``market_hint``
mapping it to a market slug / question). Candidates missing a usable source URL
or timestamp are dropped, never fabricated.

This agent is intentionally LLM-free and computes no metric: it only validates,
de-duplicates, redacts, and orders evidence the caller already collected from
public sources. In production the caller is a public-source collector (news /
event feeds); here the input is passed in directly so the scaffold needs no
network. (The ``future_agent_contract`` lists EventScout as interpretation-only;
keeping it deterministic is the safest reading of that contract.)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .mcp_client import redact_wallet_addresses

#: Minimal URL acceptance check. We only require an http(s) scheme + host; we do
#: NOT fetch the URL (no network). A missing/blank/non-http URL means "no
#: source" and the candidate is dropped.
_URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+", re.IGNORECASE)

#: Lenient ISO-8601 UTC timestamp check (``...Z`` or ``+00:00``). We validate
#: shape only; we never re-derive or "correct" timestamps.
_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)


def _looks_sourced(candidate: Dict[str, Any]) -> bool:
    """True only if the candidate carries a usable URL *and* a UTC timestamp."""
    url = str(candidate.get("source_url", "")).strip()
    ts = str(candidate.get("utc_timestamp", "")).strip()
    return bool(_URL_RE.match(url)) and bool(_TS_RE.match(ts))


def normalize_event_candidates(
    candidates: List[Dict[str, Any]],
    *,
    max_candidates: int = 50,
) -> Dict[str, Any]:
    """Validate, de-duplicate, redact, and order sourced event candidates.

    Parameters
    ----------
    candidates:
        Caller-supplied list. Each item should have ``source_url`` and
        ``utc_timestamp`` (str), optionally ``market_hint``. Anything else is
        ignored. No candidate is ever invented.
    max_candidates:
        Bound on the returned list (defaults to the MCP 50-row posture). Never
        exceeds it.

    Returns
    -------
    dict
        ``{"agent": "EventScout", "count": n, "candidates": [...],
        "dropped_unsourced": k, "allowed_interpretation": ...}`` — every value
        bounded and wallet-redacted. Contains no metric.
    """
    if candidates is None:
        candidates = []

    normalized: List[Dict[str, Any]] = []
    seen = set()
    dropped = 0

    for raw in candidates:
        if not isinstance(raw, dict) or not _looks_sourced(raw):
            dropped += 1
            continue

        source_url = str(raw["source_url"]).strip()
        utc_timestamp = str(raw["utc_timestamp"]).strip()
        market_hint = str(raw.get("market_hint", "")).strip() or None

        # Deduplicate on (url, timestamp, market_hint).
        key = (source_url, utc_timestamp, market_hint)
        if key in seen:
            continue
        seen.add(key)

        normalized.append(
            {
                "source_url": source_url,
                "utc_timestamp": utc_timestamp,
                "market_hint": market_hint,
                "evidence_basis": "caller_supplied_public_source",
            }
        )

    # Deterministic order: by timestamp, then url. Bound the result.
    normalized.sort(key=lambda c: (c["utc_timestamp"], c["source_url"]))
    bounded = normalized[: max(0, min(max_candidates, 50))]

    payload: Dict[str, Any] = {
        "agent": "EventScout",
        "count": len(bounded),
        "candidates": bounded,
        "dropped_unsourced": dropped,
        "allowed_interpretation": (
            "Normalized, sourced event candidates only. No event is invented; "
            "candidates without a public source URL and UTC timestamp are dropped. "
            "No metric is computed and no causality is asserted."
        ),
    }
    # Defensive: re-assert wallet redaction on agent-derived output.
    return redact_wallet_addresses(payload)


class EventScout:
    """Object wrapper so the Orchestrator can hold a configured instance."""

    def __init__(self, max_candidates: int = 50) -> None:
        self._max_candidates = max_candidates

    def run(self, candidates: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        return normalize_event_candidates(
            candidates or [], max_candidates=self._max_candidates
        )


__all__ = ["EventScout", "normalize_event_candidates"]
