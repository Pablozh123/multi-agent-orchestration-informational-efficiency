from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_handoff_note import (
    NOTE_COLUMNS,
    generate_advisor_handoff_note,
)


def test_generate_advisor_handoff_note_writes_mail_template(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_note(repo_root=tmp_path)

    note = pd.read_csv(result.note_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(note.columns) == NOTE_COLUMNS
    assert result.note_rows == 6
    assert "Dozenten-Uebergabetext" in doc
    assert "Betreff:" in doc
    assert "Hallo [Name des Dozenten]" in doc
    assert "docs/project/dozentenbericht_ba_thesis.docx" in doc
    assert chr(223) not in doc


def test_advisor_handoff_note_keeps_boundaries_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_note(repo_root=tmp_path)

    note = pd.read_csv(result.note_path)
    joined = "\n".join(note.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "review-access bleibt pausiert" in joined
    assert "final blockierte gates" in joined
    assert "keine runtime-agenten" in joined
    assert "keine llm-metriken" in joined
    assert "keine trading-pfade" in joined
    assert "offiziellen resultat" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_required_artifacts(root)

    pd.DataFrame(
        [
            {"deliverable_id": "advisor_report_docx", "path": "docs/project/dozentenbericht_ba_thesis.docx"},
            {"deliverable_id": "advisor_questions", "path": "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md"},
            {"deliverable_id": "consolidation_index", "path": "docs/project/THESIS_CONSOLIDATION_INDEX.md"},
        ]
    ).to_csv(results / "thesis_advisor_handoff_package.csv", index=False)

    pd.DataFrame(
        [
            _gate("advisor_handoff", "ready_for_advisor_discussion"),
            _gate("chapter_source_mapping", "ready_for_draft"),
            _gate("source_review", "final_blocked_source_review"),
            _gate("h1_h2_h3_results", "ready_for_bounded_result_draft"),
            _gate("table_figure_package", "ready_for_draft_integration"),
            _gate("monitor_appendix", "appendix_only_pending_human_review"),
            _gate("swiss_result_gate", "final_blocked_official_result"),
            _gate("agent_future_work", "deferred_future_work_only"),
            _gate("final_qa", "pending_after_draft"),
        ]
    ).to_csv(results / "thesis_submission_readiness_board.csv", index=False)

    pd.DataFrame(
        [
            {"sequence_id": "draft_01_01_source_review", "draft_permission": "review_now_final_blocked"},
            {"sequence_id": "draft_02_02_method_chapters", "draft_permission": "write_now_bounded"},
            {"sequence_id": "draft_08_08_agent_outlook", "draft_permission": "future_work_only"},
        ]
    ).to_csv(results / "thesis_drafting_sequence.csv", index=False)

    pd.DataFrame(
        [
            {
                "question_id": question_id,
                "advisor_question_de": f"Frage {question_id}?",
                "decision_needed_de": "Klaert Scope.",
            }
            for question_id in [
                "advisor_q01_h1_wording",
                "advisor_q02_source_depth",
                "advisor_q03_h2_h3_scope",
                "advisor_q06_swiss_gate",
                "advisor_q07_agent_outlook",
                "advisor_q08_final_qa",
            ]
        ]
    ).to_csv(results / "thesis_advisor_alignment_checklist.csv", index=False)


def _write_required_artifacts(root: Path) -> None:
    paths = [
        "GOAL.md",
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/project/THESIS_CONSOLIDATION_INDEX.md",
        "docs/project/THESIS_SUBMISSION_READINESS_BOARD.md",
        "docs/project/THESIS_DRAFTING_SEQUENCE.md",
        "data/results/thesis_project_highlevel_view.csv",
        "data/results/thesis_advisor_handoff_package.csv",
        "data/results/thesis_consolidation_index.csv",
        "data/results/thesis_submission_readiness_board.csv",
        "data/results/thesis_drafting_sequence.csv",
        "data/results/thesis_advisor_alignment_checklist.csv",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _gate(gate_area: str, current_status: str) -> dict[str, str]:
    return {
        "gate_area": gate_area,
        "current_status": current_status,
    }
