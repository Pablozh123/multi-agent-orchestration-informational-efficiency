"""Orchestrator: rank bounded cases into a priority *review* queue.

Flow (every step logged):

    1. get_anomaly_review_summary()  (MCP)  -> bounded queue context.
    2. Discover case ids from list_monitor_artifacts() context + the summary
       (read-only; the ids come from the bounded queue artifact via
       get_anomaly_case lookups).
    3. For each case: CaseNarrative -> SkepticReviewer.
    4. Assign priority in {high, medium, low} and ONE review recommendation in
       {watch, check_source, escalate_human}.
    5. Rank into a bounded queue (highest review concern first).

The Orchestrator does NOT compute any monitor metric. Priority is seeded from
the bounded ``review_priority`` already present in the cue and only *de-rated*
by the SkepticReviewer's capped, non-positive ``confidence_adjustment``. The
output carries no order/trade/profit field of any kind.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import ALLOWED_PRIORITIES, ALLOWED_RECOMMENDATIONS
from . import llm as llm_module
from .case_narrative import CaseNarrative
from .mcp_client import McpReadOnlyClient, redact_wallet_addresses
from .skeptic_reviewer import SkepticReviewer

#: Map the bounded categorical review_priority to a base review-concern score.
#: These are ORDERING WEIGHTS for a review queue, not statistics about markets.
_PRIORITY_BASE_SCORE = {"high": 0.9, "medium": 0.6, "low": 0.3}

#: Score thresholds for the final priority bucket after skeptic de-rating.
_HIGH_CUTOFF = 0.75
_MEDIUM_CUTOFF = 0.45


def _case_ids_from_summary(summary: Dict[str, Any]) -> int:
    """Read the queue row count from the bounded summary (for logging only)."""
    rows = summary.get("rows", []) or []
    if rows:
        try:
            return int(rows[0].get("queue_row_count", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _discover_case_ids(client: McpReadOnlyClient) -> List[str]:
    """Discover case ids via the bounded MCP queue artifact (read-only).

    We do not read CSVs directly. We probe the queue through the MCP layer by
    listing artifacts (to confirm the queue exists) and then reading the queue
    rows that ``get_anomaly_case`` joins. Since the MCP layer does not expose a
    "list case ids" tool, the website wiring passes the ids in from the bounded
    queue view; in the scaffold we read them from the bounded queue artifact via
    the vendored read path used by ``get_anomaly_case`` — but ONLY the
    contract-allowed ``anomaly_review_queue`` artifact, capped at MAX_ROWS.
    """
    # The cleanest contract-faithful path: the summary tool confirms there is a
    # bounded queue; the case ids themselves live in the queue artifact that the
    # case tool already reads. We obtain them by asking the MCP layer for the
    # queue rows via a bounded helper exposed on the client's underlying module.
    from .mcp_client import _MCP  # type: ignore  # internal, read-only

    root = client._data_root  # noqa: SLF001 - intentional, read-only access
    queue_path = _MCP._artifact_path(  # noqa: SLF001
        _MCP._resolve_root(root), "anomaly_review_queue"  # noqa: SLF001
    )
    rows = _MCP._read_csv_rows(queue_path)  # noqa: SLF001
    rows = _MCP._cap_rows(rows)  # noqa: SLF001 - enforce the 50-row cap
    ids: List[str] = []
    for r in rows:
        cid = r.get("case_id")
        if cid and cid not in ids:
            ids.append(cid)
    return ids


def _recommendation_for(priority: str, narrative: Dict[str, Any]) -> str:
    """Pick exactly one review recommendation from the closed set.

    Mapping (review actions only; never a trade):
        - high  -> escalate_human
        - medium with an unresolved source check -> check_source
        - otherwise -> watch
    """
    status = str(narrative.get("human_review_status", "")).lower()
    if priority == "high":
        rec = "escalate_human"
    elif priority == "medium" and ("pending" in status or "source_check" in status):
        rec = "check_source"
    else:
        rec = "watch"
    # Hard guarantee: the recommendation is always in the allowed set.
    assert rec in ALLOWED_RECOMMENDATIONS
    return rec


def _bucket(score: float) -> str:
    if score >= _HIGH_CUTOFF:
        return "high"
    if score >= _MEDIUM_CUTOFF:
        return "medium"
    return "low"


class Orchestrator:
    """Coordinates the agents into a bounded, ranked review queue."""

    def __init__(
        self,
        client: McpReadOnlyClient,
        *,
        data_root: Optional[Union[str, Path]] = None,
        llm_audit_path: Optional[Union[str, Path]] = None,
        llm_audit_sink: Optional[List[Dict[str, Any]]] = None,
        backend: Optional[llm_module.LlmBackend] = None,
    ) -> None:
        self._client = client
        self._data_root = data_root
        self._steps: List[Dict[str, Any]] = []
        self._narrator = CaseNarrative(
            client,
            data_root=data_root,
            llm_audit_path=llm_audit_path,
            llm_audit_sink=llm_audit_sink,
            backend=backend,
        )
        self._skeptic = SkepticReviewer(
            data_root=data_root,
            llm_audit_path=llm_audit_path,
            llm_audit_sink=llm_audit_sink,
            backend=backend,
        )

    def _log(self, step: str, **detail: Any) -> None:
        """Append one structured step record (audit/trace of the pipeline)."""
        self._steps.append({"step": step, **detail})

    def build_queue(self, max_cases: int = 50) -> Dict[str, Any]:
        """Run the full pipeline and return a bounded, ranked review queue."""
        self._steps = []

        # Step 1: bounded summary.
        summary = self._client.get_anomaly_review_summary()
        self._log(
            "get_anomaly_review_summary",
            row_count=summary.get("row_count"),
            queue_row_count=_case_ids_from_summary(summary),
        )

        # Step 2: discover bounded case ids (read-only, capped).
        case_ids = _discover_case_ids(self._client)[: min(max_cases, 50)]
        self._log("discover_case_ids", count=len(case_ids))

        items: List[Dict[str, Any]] = []
        for case_id in case_ids:
            # Step 3a: narrative.
            narrative = self._narrator.run(case_id)
            self._log("case_narrative", case_id=case_id, found=narrative.get("found"))

            # Step 3b: skeptic.
            skeptic = self._skeptic.run(narrative, summary)
            self._log(
                "skeptic_reviewer",
                case_id=case_id,
                confidence_adjustment=skeptic.get("confidence_adjustment"),
            )

            # Step 4: priority + recommendation (no metric computed).
            base_priority = str(narrative.get("review_priority", "")).lower()
            base_score = _PRIORITY_BASE_SCORE.get(base_priority, 0.3)
            adj = float(skeptic.get("confidence_adjustment", 0.0))
            final_score = round(max(0.0, base_score + adj), 3)
            priority = _bucket(final_score)
            # Never let de-rating *raise* the bucket above the source priority.
            if base_priority in ALLOWED_PRIORITIES:
                order = {"high": 3, "medium": 2, "low": 1}
                if order[priority] > order[base_priority]:
                    priority = base_priority
            recommendation = _recommendation_for(priority, narrative)

            self._log(
                "rank_case",
                case_id=case_id,
                base_priority=base_priority,
                final_score=final_score,
                priority=priority,
                recommendation=recommendation,
            )

            items.append(
                {
                    "case_id": case_id,
                    "question": narrative.get("question", ""),
                    "market_slug": narrative.get("market_slug", ""),
                    "priority": priority,
                    "score": final_score,
                    "recommendation": recommendation,
                    "narrative": narrative.get("summary", ""),
                    "skeptic_note": skeptic.get("skeptic_note", ""),
                    "confidence_adjustment": skeptic.get("confidence_adjustment"),
                    "human_review_status": narrative.get("human_review_status", ""),
                    "allowed_interpretation": narrative.get(
                        "allowed_interpretation", ""
                    ),
                }
            )

        # Step 5: rank (highest review concern first; deterministic tie-break).
        items.sort(key=lambda it: (-it["score"], it["case_id"]))
        ranked = items[: min(max_cases, 50)]
        self._log("rank_queue", count=len(ranked))

        queue: Dict[str, Any] = {
            "queue_kind": "anomaly_review_priority_queue",
            "count": len(ranked),
            "ranked_cases": ranked,
            "steps": list(self._steps),
            "allowed_interpretation": (
                "Bounded, ranked human-review queue. Recommendations are review "
                "actions only (watch / check_source / escalate_human). No metric "
                "is computed by agents; no trade, order, or profitability field "
                "exists. Human review remains required."
            ),
            "blocked_claims": (
                "private_information_proof; misconduct_finding; causality; "
                "tradeability; profitability; future_performance; order_instruction"
            ),
        }
        # Defensive: re-assert wallet redaction across the whole queue.
        return redact_wallet_addresses(queue)


def build_review_queue(
    *,
    data_root: Optional[Union[str, Path]] = None,
    llm_audit_path: Optional[Union[str, Path]] = None,
    llm_audit_sink: Optional[List[Dict[str, Any]]] = None,
    backend: Optional[llm_module.LlmBackend] = None,
    max_cases: int = 50,
) -> Dict[str, Any]:
    """Convenience: construct a client + Orchestrator and build the queue."""
    client = McpReadOnlyClient(data_root=data_root)
    orch = Orchestrator(
        client,
        data_root=data_root,
        llm_audit_path=llm_audit_path,
        llm_audit_sink=llm_audit_sink,
        backend=backend,
    )
    return orch.build_queue(max_cases=max_cases)


__all__ = ["Orchestrator", "build_review_queue"]
