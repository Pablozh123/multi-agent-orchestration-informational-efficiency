"""SkepticReviewer: adversarial counter-arguments + a bounded confidence cut.

Given a CaseNarrative and the bounded review summary, the SkepticReviewer uses
``call_llm`` to surface standard *benign* explanations that would weaken an
insider-risk reading, and returns a bounded, non-positive confidence adjustment
in ``[-0.3, 0.0]``. It never increases confidence and never makes a finding.

The four canonical skeptic angles (from the blueprint / contract) are:

    - attention_event: a public attention spike (news, hype) explains the bucket;
    - new_users_generally: generic new-user inflow, not informed flow;
    - two_sided_flow: both-sided / bidirectional flow, not a directional bet;
    - buy_only_filter: the cue may be a BUY-only artifact, not a real signal.

The adjustment is derived deterministically from bounded *categorical* context
fields already present in the cue (e.g. ``reference_overlap_status``,
``event_context_status``). This is NOT a metric calculation: there is no
statistic, no probability, no money — only a small, capped, rule-based
de-rating of a *review* confidence that a human can override. The LLM call is
made (mock by default) and audited to phrase the skeptic note.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import llm as llm_module
from .mcp_client import redact_wallet_addresses

#: Hard bounds on the confidence adjustment. Never positive, never below -0.3.
MIN_ADJUSTMENT: float = -0.3
MAX_ADJUSTMENT: float = 0.0

_SYSTEM_PROMPT = (
    "You are SkepticReviewer. Given a bounded market-anomaly review cue, you "
    "argue the BENIGN side: list ordinary explanations (public attention event, "
    "generic new-user inflow, two-sided/bidirectional flow, BUY-only filter "
    "artifact) that would weaken an insider-risk reading. You never confirm "
    "misconduct, never compute a metric, never give trading or investment "
    "advice, and never output a wallet address. Keep it to review caveats only."
)

#: The four canonical skeptic angles, with a small fixed de-rating weight each.
#: Weights are review heuristics (caveat strength), not statistics. Their sum is
#: clamped into [MIN_ADJUSTMENT, 0].
_ANGLES = (
    ("attention_event", -0.10,
     "A public attention spike (news/hype) around this market could explain the "
     "bucket without any private information."),
    ("new_users_generally", -0.05,
     "Generic new-user inflow can mimic concentrated activity; new wallets are "
     "not evidence of informed trading."),
    ("two_sided_flow", -0.10,
     "If flow is two-sided / bidirectional, it is a market-making or hedging "
     "pattern rather than a directional informed bet."),
    ("buy_only_filter", -0.05,
     "The cue may be a BUY-only filter artifact; without exit/position data it "
     "is not a directional signal."),
)


def _applicable_angles(narrative: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pick skeptic angles supported by bounded categorical context fields.

    Pure rule-based selection over *categorical* strings already in the cue. No
    number is computed; we only decide which standard caveats apply.
    """
    event_ctx = str(narrative.get("event_context_status", "")).lower()
    ref_overlap = str(narrative.get("reference_overlap_status", "")).lower()
    label = str(narrative.get("review_label", "")).lower()

    selected: List[Dict[str, Any]] = []
    for name, weight, text in _ANGLES:
        applies = False
        if name == "attention_event":
            # Any event-context linkage invites the attention-event caveat.
            applies = "event" in event_ctx or "nearest_event" in event_ctx
        elif name == "new_users_generally":
            # Watch-cue / weaker labels are most exposed to generic-inflow doubt.
            applies = "watch" in label or "candidate" in label
        elif name == "two_sided_flow":
            # Partial / absent reference overlap leaves room for two-sided flow.
            applies = ("partial" in ref_overlap) or ("no_reference_overlap" in ref_overlap)
        elif name == "buy_only_filter":
            # Always an applicable methodological caveat for these BUY-side cues.
            applies = True
        if applies:
            selected.append({"angle": name, "weight": weight, "argument": text})
    return selected


def review_case_skeptically(
    narrative: Dict[str, Any],
    summary: Optional[Dict[str, Any]] = None,
    *,
    data_root: Optional[Union[str, Path]] = None,
    llm_audit_path: Optional[Union[str, Path]] = None,
    llm_audit_sink: Optional[List[Dict[str, Any]]] = None,
    backend: Optional[llm_module.LlmBackend] = None,
) -> Dict[str, Any]:
    """Return bounded counter-arguments and a confidence adjustment in [-0.3,0].

    Parameters
    ----------
    narrative:
        A CaseNarrative payload (categorical bounded fields).
    summary:
        Optional bounded review summary (for context only; not required, never
        mined for metrics).
    """
    angles = _applicable_angles(narrative or {})
    raw_adjustment = sum(a["weight"] for a in angles)
    # Clamp into the documented bound. Never positive, never below -0.3.
    confidence_adjustment = max(MIN_ADJUSTMENT, min(MAX_ADJUSTMENT, raw_adjustment))

    user_prompt = (
        "Give benign-side review caveats for this cue. No findings, no numbers, "
        "no advice.\n\n"
        f"question={narrative.get('question', '')}\n"
        f"label={narrative.get('review_label', '')}\n"
        f"event_context={narrative.get('event_context_status', '')}\n"
        f"reference_overlap={narrative.get('reference_overlap_status', '')}\n"
        f"applicable_angles={[a['angle'] for a in angles]}"
    )
    llm_output = llm_module.call_llm(
        role="SkepticReviewer",
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        audit_path=llm_audit_path,
        data_root=data_root,
        backend=backend,
        audit_sink=llm_audit_sink,
    )

    note_bits = [a["argument"] for a in angles] or [
        "No specific benign angle flagged; default methodological caution applies."
    ]
    skeptic_note = " ".join(note_bits)

    payload: Dict[str, Any] = {
        "agent": "SkepticReviewer",
        "case_id": narrative.get("case_id", ""),
        "counter_arguments": angles,
        "confidence_adjustment": round(confidence_adjustment, 3),
        "adjustment_bounds": [MIN_ADJUSTMENT, MAX_ADJUSTMENT],
        "skeptic_note": skeptic_note,
        "allowed_interpretation": (
            "Adversarial review caveats and a bounded, non-positive confidence "
            "de-rating only. Not a metric, not a finding, not advice."
        ),
        "llm_backend_output": llm_output,
    }
    return redact_wallet_addresses(payload)


class SkepticReviewer:
    """Object wrapper holding LLM settings for repeated use by the Orchestrator."""

    def __init__(
        self,
        *,
        data_root: Optional[Union[str, Path]] = None,
        llm_audit_path: Optional[Union[str, Path]] = None,
        llm_audit_sink: Optional[List[Dict[str, Any]]] = None,
        backend: Optional[llm_module.LlmBackend] = None,
    ) -> None:
        self._data_root = data_root
        self._llm_audit_path = llm_audit_path
        self._llm_audit_sink = llm_audit_sink
        self._backend = backend

    def run(
        self,
        narrative: Dict[str, Any],
        summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return review_case_skeptically(
            narrative,
            summary,
            data_root=self._data_root,
            llm_audit_path=self._llm_audit_path,
            llm_audit_sink=self._llm_audit_sink,
            backend=self._backend,
        )


__all__ = [
    "SkepticReviewer",
    "review_case_skeptically",
    "MIN_ADJUSTMENT",
    "MAX_ADJUSTMENT",
]
