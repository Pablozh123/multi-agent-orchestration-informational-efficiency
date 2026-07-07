# -*- coding: utf-8 -*-
"""Echter LLM-Lauf der Review-Schicht (Backend: Anthropic, Temperatur 0).
Schreibt NUR neue Artefakte (_real/_llm), ueberschreibt nichts. Key wird nie ausgegeben."""
import os, sys, json

REPO = "/sessions/compassionate-gracious-babbage/mnt/ba-thesis"
os.chdir(REPO)
sys.path.insert(0, REPO)

for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY fehlt"

import anthropic
client = anthropic.Anthropic()
MODEL = "claude-sonnet-5"
CALLS = {"n": 0}

def backend(system: str, user: str) -> str:
    CALLS["n"] += 1
    r = client.messages.create(model=MODEL, max_tokens=800,
                               system=system, messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")

from operations.agents.review_queue.orchestrator import build_review_queue
from operations.analysis.agent_review_queue_eval import check_safety, load_reference_contexts, POSITIVE_REFERENCE, FLAG_RECOMMENDATIONS

q_mock = build_review_queue()
q_llm = build_review_queue(backend=backend,
                           llm_audit_path="data/results/agent_review_queue_llm_audit_log_real.jsonl")

ref = load_reference_contexts()
rows = []
for case in q_llm.get("ranked_cases", []):
    cid = str(case.get("case_id", ""))
    rc = ref.get(cid, "unknown")
    rows.append({
        "case_id": cid,
        "priority": case.get("priority"),
        "recommendation": case.get("recommendation"),
        "confidence_adjustment": case.get("confidence_adjustment"),
        "reference_context": rc,
        "ground_truth_positive": rc in POSITIVE_REFERENCE,
        "predicted_positive": case.get("recommendation") in FLAG_RECOMMENDATIONS,
    })
tp = sum(1 for r in rows if r["predicted_positive"] and r["ground_truth_positive"])
fp = sum(1 for r in rows if r["predicted_positive"] and not r["ground_truth_positive"])
fn = sum(1 for r in rows if not r["predicted_positive"] and r["ground_truth_positive"])
tn = sum(1 for r in rows if not r["predicted_positive"] and not r["ground_truth_positive"])
prec = tp / (tp + fp) if tp + fp else None
rec = tp / (tp + fn) if tp + fn else None
f1 = (2 * prec * rec / (prec + rec)) if prec and rec else 0.0

def sig(q):
    return [(c.get("case_id"), c.get("priority"), c.get("recommendation"),
             c.get("confidence_adjustment")) for c in q.get("ranked_cases", [])]

safety = check_safety(q_llm)
out = {
    "backend": f"anthropic:{MODEL}", "llm_calls": CALLS["n"],
    "n_cases": len(rows), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    "precision": prec, "recall": rec, "f1": f1,
    "safety": safety,
    "ranking_identisch_mit_mock": sig(q_mock) == sig(q_llm),
    "mock_signature": sig(q_mock), "llm_signature": sig(q_llm), "rows": rows,
}
with open("data/results/agent_review_queue_eval_summary_llm.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)
print(json.dumps({k: out[k] for k in ("backend", "llm_calls", "precision", "recall", "f1",
      "ranking_identisch_mit_mock")}, default=str))
print("safety_passed:", safety["passed"])
print("llm_signature:", sig(q_llm))
