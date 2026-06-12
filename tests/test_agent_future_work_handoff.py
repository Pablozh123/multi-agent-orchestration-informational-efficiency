from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_agent_future_work_handoff import (
    HANDOFF_COLUMNS,
    generate_agent_future_work_handoff,
)


def test_generate_agent_future_work_handoff_writes_future_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_future_work_handoff(repo_root=tmp_path)

    handoff = pd.read_csv(result.handoff_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(handoff.columns) == HANDOFF_COLUMNS
    assert result.handoff_rows == 2
    assert handoff["status"].tolist() == ["future_documentation_only", "future_deferred"]
    assert "Thesis Agent Future-Work Handoff" in doc
    assert "Documentation-only rows: 1" in doc
    assert "Deferred rows: 1" in doc
    assert chr(223) not in doc


def test_agent_future_work_handoff_preserves_deferred_guardrails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_future_work_handoff(repo_root=tmp_path)

    handoff = pd.read_csv(result.handoff_path)
    joined = "\n".join(handoff.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "keine runtime-agenten" in joined
    assert "llm_audit_log" in joined
    assert "keine llm-metriken" in joined
    assert "keine trading-pfade" in joined
    assert "separates genehmigtes goal" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "protocol_id": "agent_protocol_01_source_review",
                "pipeline_step": "Manual source review",
                "allowed_inputs": "source_id; evidence_id",
                "allowed_outputs": "bounded checklist",
                "audit_gate": "llm_audit_log entry with source_ids and prompt hash",
                "blocked_behaviour": "promoting source status",
                "activation_status": "future_documentation_only",
                "thesis_value": "keeps review bounded",
            },
            {
                "protocol_id": "agent_protocol_07_bounded_mcp",
                "pipeline_step": "Bounded MCP summary interface",
                "allowed_inputs": "reviewed summary artifacts",
                "allowed_outputs": "bounded read-only summaries",
                "audit_gate": "separate approved goal and llm_audit_log integration",
                "blocked_behaviour": "raw table access; order or trading paths",
                "activation_status": "future_deferred",
                "thesis_value": "safe interface later",
            },
        ]
    ).to_csv(results / "thesis_agent_assistance_protocol.csv", index=False)

    pd.DataFrame(
        [
            {"task_id": "exec_01_intro", "chapter_id": "ch_01_intro"},
            {"task_id": "exec_02_theory", "chapter_id": "ch_02_theory"},
        ]
    ).to_csv(results / "thesis_execution_checklist.csv", index=False)

    pd.DataFrame(
        [
            {"source_id": "src_1", "review_stage": "review_now_priority_1"},
            {"source_id": "src_2", "review_stage": "defer_until_mapped"},
        ]
    ).to_csv(results / "thesis_source_review_execution.csv", index=False)
