from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_feedback_log import (
    FEEDBACK_COLUMNS,
    generate_advisor_feedback_log,
)


def test_generate_advisor_feedback_log_writes_pending_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_feedback_log(repo_root=tmp_path)

    feedback = pd.read_csv(result.feedback_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(feedback.columns) == FEEDBACK_COLUMNS
    assert result.feedback_rows == 8
    assert feedback["advisor_feedback_status"].eq("pending_advisor_feedback").all()
    assert feedback["advisor_feedback_de"].eq("pending").all()
    assert "Dozenten-Feedback-Log" in doc
    assert "Feedback rows: 8" in doc
    assert chr(223) not in doc


def test_advisor_feedback_log_keeps_feedback_from_changing_scope(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_feedback_log(repo_root=tmp_path)

    feedback = pd.read_csv(result.feedback_path)
    joined = "\n".join(feedback.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "pending_advisor_feedback" in joined
    assert "nach feedback in kleinen commit-plan" in joined
    assert "review-access" in joined
    assert "keine runtime-agenten" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "question_id": f"advisor_q{index:02d}_{suffix}",
                "topic": suffix,
                "advisor_question_de": f"Frage {index}?",
                "current_project_position_de": "Aktueller Stand bleibt bounded.",
                "decision_needed_de": "Dozent soll Scope bestaetigen.",
                "guardrail": guardrail,
            }
            for index, suffix, guardrail in [
                (1, "h1_wording", "Keine Universalclaims."),
                (2, "source_depth", "Quellenstatus nicht automatisch hochstufen."),
                (3, "h2_h3_scope", "Keine Kausalitaetsclaims."),
                (4, "table_figure_package", "Keine Rohartefakt-Dumps."),
                (5, "monitor_appendix", "Review-Access bleibt pausiert."),
                (6, "swiss_gate", "Kein finales Swiss-Wording vor Resultat."),
                (7, "agent_outlook", "Keine Runtime-Agenten, kein MCP."),
                (8, "final_qa", "Finale Checks vor Abgabe."),
            ]
        ]
    ).to_csv(results / "thesis_advisor_alignment_checklist.csv", index=False)
