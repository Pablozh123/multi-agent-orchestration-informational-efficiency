"""Evaluate the read-only agent review queue against curated reference cases.

Deterministic and mock-LLM. Measures how well the agent layer's triage
(priority + review recommendation) aligns with the curated reference cases
(``reference_context`` carried in the bounded queue packets), plus safety and
determinism. Calculates NO market metric and emits no wallet addresses or trade
instructions. The case set is intentionally small and bounded; metrics are
illustrative, not a significance test.
"""
from __future__ import annotations

import datetime as _dt
if not hasattr(_dt, "UTC"):  # Python < 3.11 backport-compat (no-op on >=3.11)
    _dt.UTC = _dt.timezone.utc

import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from operations.agents.review_queue import (
    ALLOWED_PRIORITIES,
    ALLOWED_RECOMMENDATIONS,
    FORBIDDEN_OUTPUT_KEY_FRAGMENTS,
)
from operations.agents.review_queue.orchestrator import build_review_queue

RESULTS_DIR = Path("data/results")
PACKETS_CSV = RESULTS_DIR / "monitor_anomaly_case_review_packets.csv"
METRICS_CSV = RESULTS_DIR / "agent_review_queue_eval_metrics.csv"
SUMMARY_JSON = RESULTS_DIR / "agent_review_queue_eval_summary.json"

#: reference_context values that count as "overlaps a curated reference case".
POSITIVE_REFERENCE = ("reference_hit", "partial_reference_overlap")
#: agent recommendations that count as "flagged for review" (predicted positive).
FLAG_RECOMMENDATIONS = ("check_source", "escalate_human")

_WALLET_RE = re.compile(r"0x[0-9a-fA-F]{40}")
_REF_RE = re.compile(r"reference_context=([a-z_]+)")


def load_reference_contexts(packets_csv: Path = PACKETS_CSV) -> Dict[str, str]:
    """Map case_id -> reference_context from the bounded queue packets (ground truth)."""
    out: Dict[str, str] = {}
    if not packets_csv.exists():
        return out
    text = packets_csv.read_text(encoding="utf-8")
    for row in csv.DictReader(io.StringIO(text)):
        cid = str(row.get("case_id", "")).strip()
        if not cid:
            continue
        blob = " ".join(str(v) for v in row.values())
        m = _REF_RE.search(blob)
        out[cid] = m.group(1) if m else "unknown"
    return out


def _walk_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_keys(value)


def check_safety(queue: Dict[str, Any]) -> Dict[str, Any]:
    """Hard guardrail check on the queue output (no metric, no wallet, review-only)."""
    blob = json.dumps(queue)
    wallet = bool(_WALLET_RE.search(blob))
    forbidden = sorted({
        key for key in _walk_keys(queue)
        if any(frag in key.lower() for frag in FORBIDDEN_OUTPUT_KEY_FRAGMENTS)
    })
    cases = queue.get("ranked_cases", [])
    bad_rec = sorted({
        str(c.get("recommendation")) for c in cases
        if c.get("recommendation") not in ALLOWED_RECOMMENDATIONS
    })
    bad_prio = sorted({
        str(c.get("priority")) for c in cases
        if c.get("priority") not in ALLOWED_PRIORITIES
    })
    return {
        "wallet_leak": wallet,
        "forbidden_keys": forbidden,
        "invalid_recommendations": bad_rec,
        "invalid_priorities": bad_prio,
        "passed": (not wallet) and (not forbidden) and (not bad_rec) and (not bad_prio),
    }


def check_determinism() -> bool:
    """Two independent builds must yield the same (case_id, priority, recommendation)."""
    def sig(q: Dict[str, Any]):
        return [
            (c.get("case_id"), c.get("priority"), c.get("recommendation"))
            for c in q.get("ranked_cases", [])
        ]
    return sig(build_review_queue()) == sig(build_review_queue())


def _distribution(rows: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    dist: Dict[str, int] = {}
    for row in rows:
        key = str(row.get(field))
        dist[key] = dist.get(key, 0) + 1
    return dist


def evaluate(
    queue: Optional[Dict[str, Any]] = None,
    reference: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Join agent triage with reference ground truth and compute alignment metrics."""
    if queue is None:
        queue = build_review_queue()
    if reference is None:
        reference = load_reference_contexts()

    rows: List[Dict[str, Any]] = []
    for case in queue.get("ranked_cases", []):
        cid = str(case.get("case_id", ""))
        ref = reference.get(cid, "unknown")
        rows.append({
            "case_id": cid,
            "priority": case.get("priority"),
            "recommendation": case.get("recommendation"),
            "confidence_adjustment": case.get("confidence_adjustment"),
            "reference_context": ref,
            "ground_truth_positive": ref in POSITIVE_REFERENCE,
            "predicted_positive": case.get("recommendation") in FLAG_RECOMMENDATIONS,
        })

    tp = sum(1 for r in rows if r["predicted_positive"] and r["ground_truth_positive"])
    fp = sum(1 for r in rows if r["predicted_positive"] and not r["ground_truth_positive"])
    fn = sum(1 for r in rows if not r["predicted_positive"] and r["ground_truth_positive"])
    tn = sum(1 for r in rows if not r["predicted_positive"] and not r["ground_truth_positive"])
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    elif precision is not None and recall is not None:
        f1 = 0.0
    else:
        f1 = None

    summary = {
        "n_cases": len(rows),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1,
        "reference_distribution": _distribution(rows, "reference_context"),
        "priority_distribution": _distribution(rows, "priority"),
        "recommendation_distribution": _distribution(rows, "recommendation"),
        "skeptic_derated_cases": sum(
            1 for r in rows if (r["confidence_adjustment"] or 0) < 0
        ),
        "safety": check_safety(queue),
        "small_sample_caveat": len(rows) < 10,
    }
    return {"rows": rows, "summary": summary}


def main() -> int:
    result = evaluate()
    result["summary"]["deterministic"] = check_determinism()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = result["rows"]
    if rows:
        with METRICS_CSV.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    SUMMARY_JSON.write_text(
        json.dumps(result["summary"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
