"""Guardrail smoke test for the agent review-queue dashboard (separate site part).

Runs the read-only review-agent pipeline + static dashboard generator against a
throwaway copy of the real bounded monitor artifacts (deterministic mock LLM)
and asserts the hard boundaries: ranked review queue, no wallet address, audited
LLM calls, review-only recommendations, and no order/trade/profit field.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from operations.agents.review_queue import (  # noqa: E402
    ALLOWED_RECOMMENDATIONS,
    FORBIDDEN_OUTPUT_KEY_FRAGMENTS,
)
from operations.agents.review_queue.orchestrator import build_review_queue  # noqa: E402
from operations.analysis.agent_review_queue_dashboard import (  # noqa: E402
    RESULTS_DIR,
    generate_agent_review_queue_dashboard,
)

_WALLET_RE = re.compile(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")


def _isolated_root(tmp_path: Path) -> Path:
    """Copy the real bounded monitor artifacts into a writable throwaway root."""
    dst = tmp_path / "data" / "results"
    dst.mkdir(parents=True, exist_ok=True)
    for artifact in sorted(RESULTS_DIR.glob("monitor_anomaly_*")):
        shutil.copy(artifact, dst / artifact.name)
    return tmp_path


def _generate(tmp_path: Path):
    root = _isolated_root(tmp_path)
    res = generate_agent_review_queue_dashboard(
        data_root=root,
        dashboard_path=root / "data" / "results" / "agent_review_queue_dashboard.html",
        metadata_path=root / "data" / "results" / "agent_review_queue_dashboard_metadata.json",
        llm_audit_path=root / "data" / "results" / "agent_review_queue_llm_audit_log.jsonl",
    )
    return root, res


def _keys(value):
    if isinstance(value, dict):
        for key, sub in value.items():
            yield key
            yield from _keys(sub)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _keys(item)


def test_dashboard_generates_ranked_cases(tmp_path):
    _, res = _generate(tmp_path)
    assert res.case_count >= 1
    assert res.dashboard_path.exists()
    html = res.dashboard_path.read_text(encoding="utf-8")
    assert "Agenten-Review-Queue" in html
    assert res.backend == "mock"


def test_no_wallet_addresses_in_html(tmp_path):
    _, res = _generate(tmp_path)
    html = res.dashboard_path.read_text(encoding="utf-8")
    assert not _WALLET_RE.search(html), "wallet address leaked into rendered HTML"


def test_recommendations_review_only(tmp_path):
    root, _ = _generate(tmp_path)
    queue = build_review_queue(data_root=root, llm_audit_path=tmp_path / "rec.jsonl")
    assert queue["ranked_cases"], "expected at least one ranked case"
    for item in queue["ranked_cases"]:
        assert item["recommendation"] in ALLOWED_RECOMMENDATIONS, item["recommendation"]


def test_no_order_trade_profit_keys(tmp_path):
    root, _ = _generate(tmp_path)
    queue = build_review_queue(data_root=root, llm_audit_path=tmp_path / "frag.jsonl")
    for key in _keys(queue):
        low = str(key).lower()
        for frag in FORBIDDEN_OUTPUT_KEY_FRAGMENTS:
            assert frag not in low, f"forbidden key fragment '{frag}' in '{key}'"


def test_every_llm_call_audited(tmp_path):
    root, res = _generate(tmp_path)
    audit = root / "data" / "results" / "agent_review_queue_llm_audit_log.jsonl"
    lines = [ln for ln in audit.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2 * res.case_count, "expect 2 LLM calls per case"
    for line in lines:
        entry = json.loads(line)
        assert set(entry) >= {"role", "prompt_hash", "ts_utc", "backend", "output_hash"}
        assert entry["backend"] == "mock"
        assert len(entry["prompt_hash"]) == 64


def test_metadata_flags_are_safe(tmp_path):
    _, res = _generate(tmp_path)
    meta = json.loads(res.metadata_path.read_text(encoding="utf-8"))
    assert meta["outputs"]["contains_wallet_addresses"] is False
    assert meta["outputs"]["contains_order_instructions"] is False
    assert meta["method"]["agents_compute_no_metric"] is True
    assert meta["method"]["read_only"] is True
    assert list(meta["method"]["recommendations_allowed"]) == list(ALLOWED_RECOMMENDATIONS)
