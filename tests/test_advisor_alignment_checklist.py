from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_alignment_checklist import (
    CHECKLIST_COLUMNS,
    generate_advisor_alignment_checklist,
)


def test_generate_advisor_alignment_checklist_writes_questions(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_alignment_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(checklist.columns) == CHECKLIST_COLUMNS
    assert result.checklist_rows == 8
    assert checklist["question_id"].tolist()[0] == "advisor_q01_h1_wording"
    assert "Dozenten-Absprache-Checklist" in doc
    assert "Advisor questions: 8" in doc
    assert "Empfohlene Gespraechsreihenfolge" in doc
    assert "Erst H1-H2-H3 Scope bestaetigen" in doc
    assert "Review-Access bleibt pausiert" in doc
    assert "llm_audit_log" in doc


def test_advisor_alignment_checklist_preserves_scope_guardrails(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_alignment_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    joined = "\n".join(checklist.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "keine runtime-agenten" in joined
    assert "keine wallet-adress-exposition" in joined
    assert "keine finale accuracy- oder effizienzbehauptung" in joined
    assert "source review" in joined
    assert "thesis_wording_guard.csv" in joined
    assert chr(223) not in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    pd.DataFrame(
        [
            {"view_id": "project_00_current_frame", "current_decision": "core", "next_gate": "draft"},
            {"view_id": "project_06_monitor_review_access", "current_decision": "paused", "next_gate": "review"},
            {"view_id": "project_08_future_agents", "current_decision": "deferred", "next_gate": "llm"},
        ]
    ).to_csv(results / "thesis_project_highlevel_view.csv", index=False)
    pd.DataFrame(
        [
            {
                "workstream_id": "work_01_source_review",
                "next_action": "review",
                "guardrail": "no promotion",
            }
        ]
    ).to_csv(results / "thesis_next_work_plan.csv", index=False)
    pd.DataFrame(
        [
            {"priority_band": "priority_1_method_foundation_review", "reviewer_decision": "pending"},
            {"priority_band": "priority_1_method_foundation_review", "reviewer_decision": "pending"},
            {"priority_band": "blocked_or_future_work_only", "reviewer_decision": "pending"},
        ]
    ).to_csv(results / "thesis_source_review_worksheet.csv", index=False)
    pd.DataFrame(
        [
            {"evidence_id": "method_h1", "final_use_gate": "thesis_text_allowed_after_source_review"},
            {"evidence_id": "method_h2", "final_use_gate": "thesis_text_allowed_after_source_review"},
            {"evidence_id": "future_agent", "final_use_gate": "future_work_or_appendix_only"},
        ]
    ).to_csv(results / "thesis_wording_guard.csv", index=False)
