"""CaseNarrative: turn one bounded MCP case record into a readable narrative.

The CaseNarrative agent calls ``get_anomaly_case(case_id)`` through the MCP
client and, via ``call_llm``, assembles a structured, human-readable case
description. It calculates NOTHING: every field in the narrative is copied or
quoted from the bounded MCP payload (which itself only reshapes precomputed,
deterministic monitor outputs). The LLM is used only to phrase, not to derive
numbers, probabilities, or findings.

To stay robust and deterministic in the scaffold (mock LLM), the readable prose
is assembled deterministically from the bounded fields, and the LLM call is made
*and audited* alongside it. Swapping in a real model later changes only the
prose wording, never the underlying bounded facts (see STAGE3_HANDOFF.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import llm as llm_module
from .mcp_client import McpReadOnlyClient, redact_wallet_addresses

#: System prompt makes the boundaries explicit to any (real) model wired later.
_SYSTEM_PROMPT = (
    "You are CaseNarrative, a read-only summarizer for a market-anomaly review "
    "queue. You only rephrase bounded, precomputed review cues into readable "
    "prose. You must NOT compute or infer any metric, probability, profit, "
    "tradeability, causality, misconduct, or private-information claim. You must "
    "never output a wallet address. Output a short, neutral case description for "
    "a human reviewer."
)


def _first(section: List[Dict[str, str]]) -> Dict[str, str]:
    """Return the first row of an MCP section, or an empty dict."""
    return section[0] if section else {}


def build_case_narrative(
    case_id: str,
    *,
    client: Optional[McpReadOnlyClient] = None,
    data_root: Optional[Union[str, Path]] = None,
    llm_audit_path: Optional[Union[str, Path]] = None,
    llm_audit_sink: Optional[List[Dict[str, Any]]] = None,
    backend: Optional[llm_module.LlmBackend] = None,
) -> Dict[str, Any]:
    """Build a bounded, readable narrative for one case via the MCP layer.

    Returns a dict with quoted bounded fields plus a deterministic prose summary.
    Computes no metric; every fact is copied from the MCP payload.
    """
    mcp = client or McpReadOnlyClient(data_root=data_root)
    case = mcp.get_anomaly_case(case_id)

    found = bool(case.get("found"))
    sections: Dict[str, List[Dict[str, str]]] = case.get("sections", {}) or {}
    queue_row = _first(sections.get("queue", []))
    packet_row = _first(sections.get("case_review_packet", []))

    # All facts below are *quoted* from the bounded MCP payload. No derivation.
    question = queue_row.get("question") or packet_row.get("question") or ""
    market_slug = queue_row.get("market_slug") or packet_row.get("market_slug") or ""
    review_priority = (
        queue_row.get("review_priority") or packet_row.get("review_priority") or ""
    )
    review_label = queue_row.get("review_label", "")
    human_review_status = queue_row.get("human_review_status", "")
    event_context_status = queue_row.get("event_context_status", "")
    reference_overlap_status = queue_row.get("reference_overlap_status", "")
    review_note = queue_row.get("review_note", "")
    missing_evidence = queue_row.get("missing_evidence", "")
    allowed_interpretation = queue_row.get(
        "allowed_interpretation", case.get("allowed_interpretation", "")
    )

    # Deterministic readable summary (no numbers are invented; we only stitch
    # together quoted bounded strings).
    if found:
        prose = (
            f"Case {case_id} concerns the market '{question}' (slug: "
            f"{market_slug}). It is a bounded human-review cue labelled "
            f"'{review_label}' at review priority '{review_priority}'. "
            f"Event context: {event_context_status or 'n/a'}; reference overlap: "
            f"{reference_overlap_status or 'n/a'}; human-review status: "
            f"{human_review_status or 'n/a'}. This is a review prompt only, not a "
            f"finding, a metric, or any claim about private information."
        )
    else:
        prose = (
            f"No bounded review record was found for case {case_id}. Nothing is "
            f"asserted about it."
        )

    # The LLM call is made (mock by default) and AUDITED. Its raw output is
    # carried for traceability but the bounded facts above are authoritative.
    user_prompt = (
        "Rephrase the following bounded review cue into one neutral paragraph "
        "for a human reviewer. Do not add numbers, findings, or advice.\n\n"
        f"question={question}\nlabel={review_label}\npriority={review_priority}\n"
        f"event_context={event_context_status}\n"
        f"reference_overlap={reference_overlap_status}\n"
        f"review_note={review_note}"
    )
    llm_output = llm_module.call_llm(
        role="CaseNarrative",
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        audit_path=llm_audit_path,
        data_root=data_root,
        backend=backend,
        audit_sink=llm_audit_sink,
    )

    narrative: Dict[str, Any] = {
        "agent": "CaseNarrative",
        "case_id": case_id,
        "found": found,
        "question": question,
        "market_slug": market_slug,
        "review_priority": review_priority,
        "review_label": review_label,
        "human_review_status": human_review_status,
        "event_context_status": event_context_status,
        "reference_overlap_status": reference_overlap_status,
        "missing_evidence": missing_evidence,
        "review_note": review_note,
        "summary": prose,
        "allowed_interpretation": allowed_interpretation
        or (
            "Bounded deterministic review cue rephrased for human reading; not a "
            "metric, finding, or private-information claim."
        ),
        "llm_backend_output": llm_output,
    }
    # Defensive: re-assert wallet redaction on agent-derived text.
    return redact_wallet_addresses(narrative)


class CaseNarrative:
    """Object wrapper holding a configured MCP client and LLM settings."""

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
        self._llm_audit_path = llm_audit_path
        self._llm_audit_sink = llm_audit_sink
        self._backend = backend

    def run(self, case_id: str) -> Dict[str, Any]:
        return build_case_narrative(
            case_id,
            client=self._client,
            data_root=self._data_root,
            llm_audit_path=self._llm_audit_path,
            llm_audit_sink=self._llm_audit_sink,
            backend=self._backend,
        )


__all__ = ["CaseNarrative", "build_case_narrative"]
