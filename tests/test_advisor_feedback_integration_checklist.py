from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_feedback_integration_checklist import (
    INTEGRATION_COLUMNS,
    generate_advisor_feedback_integration_checklist,
)


def test_generate_advisor_feedback_integration_checklist_writes_pending_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_feedback_integration_checklist(repo_root=tmp_path)

    integration = pd.read_csv(result.integration_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(integration.columns) == INTEGRATION_COLUMNS
    assert result.integration_rows == 8
    assert integration["feedback_status"].eq("pending_advisor_feedback").all()
    assert "Dozenten-Feedback-Integration-Checklist" in doc
    assert "Integration rows: 8" in doc
    assert "Active runtime agents: 0" in doc
    assert chr(223) not in doc


def test_advisor_feedback_integration_keeps_evidence_and_agent_boundaries(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_feedback_integration_checklist(repo_root=tmp_path)

    integration = pd.read_csv(result.integration_path)
    joined = "\n".join(integration.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "jede methode und jede interpretation" in joined
    assert "deterministische artefakte" in joined
    assert "source review" in joined
    assert "wenige gute tabellen" in joined
    assert "keine roh" in joined
    assert "review-access bleibt pausiert" in joined
    assert "keine runtime-agenten" in joined
    assert "llm_audit_log" in joined
    assert "docs: integrate advisor table figure feedback" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "feedback_id": f"feedback_{index:02d}_{question_id}",
                "advisor_question_id": question_id,
                "topic": topic,
                "advisor_question_de": f"Frage {index}?",
                "current_project_position_de": "Aktueller Stand bleibt bounded.",
                "decision_needed_de": "Dozent soll Scope bestaetigen.",
                "advisor_feedback_status": "pending_advisor_feedback",
                "advisor_feedback_de": "pending",
                "resulting_action_de": "pending",
                "commit_scope_de": "Nach Feedback in kleinen Commit-Plan uebersetzen.",
                "guardrail_de": "Keine Runtime-Agenten.",
            }
            for index, question_id, topic in [
                (1, "advisor_q01_h1_wording", "H1 bounded wording"),
                (2, "advisor_q02_source_depth", "Source review depth"),
                (3, "advisor_q03_h2_h3_scope", "H2/H3 scope"),
                (4, "advisor_q04_table_figure_package", "Tables and figures"),
                (5, "advisor_q05_monitor_appendix", "Monitor appendix"),
                (6, "advisor_q06_swiss_gate", "Swiss result gate"),
                (7, "advisor_q07_agent_outlook", "Agent outlook"),
                (8, "advisor_q08_final_qa", "Final QA"),
            ]
        ]
    ).to_csv(results / "thesis_advisor_feedback_log_template.csv", index=False)
