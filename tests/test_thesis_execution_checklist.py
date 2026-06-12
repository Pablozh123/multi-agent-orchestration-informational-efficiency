from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_execution_checklist import (
    EXECUTION_COLUMNS,
    generate_thesis_execution_checklist,
)


def test_generate_thesis_execution_checklist_writes_chapter_tasks(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_execution_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(checklist.columns) == EXECUTION_COLUMNS
    assert result.checklist_rows == 8
    assert checklist["chapter_id"].tolist()[0] == "ch_01_intro"
    assert checklist["chapter_id"].tolist()[-1] == "ch_08_discussion_conclusion"
    assert "Thesis Execution Checklist" in doc
    assert "Execution tasks: 8" in doc
    assert "tab:t2" in doc
    assert chr(223) not in doc


def test_thesis_execution_checklist_keeps_highlevel_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_execution_checklist(repo_root=tmp_path)

    checklist = pd.read_csv(result.checklist_path)
    joined = "\n".join(checklist.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "review-access bleibt pausiert" in joined
    assert "keine runtime-agenten" in joined
    assert "keine roh" in joined
    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "14. juni 2026" in joined
    assert "advisor_q06_swiss_gate" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    research = root / "docs/research"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)
    research.mkdir(parents=True)

    chapter_rows = [
        _chapter_row("ch_01_intro", "Einleitung und Forschungsfrage", "T1", ""),
        _chapter_row("ch_02_theory_literature", "Theorie und Literatur", "T1", ""),
        _chapter_row("ch_03_data_method", "Daten und Methodik", "T1", ""),
        _chapter_row("ch_04_h1_results", "H1: Prognosequalitaet", "T2", "F1"),
        _chapter_row("ch_05_h2_results", "H2: Ereignisfenster", "T3", "F2"),
        _chapter_row("ch_06_h3_results", "H3: Wallet-Timing", "T4", "F3"),
        _chapter_row("ch_07_extensions", "Erweiterungen", "T5", "F4"),
        _chapter_row("ch_08_discussion_conclusion", "Diskussion und Fazit", "", ""),
    ]
    pd.DataFrame(chapter_rows).to_csv(results / "thesis_chapter_plan.csv", index=False)

    for row in chapter_rows:
        for artifact in str(row["primary_artifacts"]).split(";"):
            path = root / artifact.strip()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"workstream_id": "work_01_source_review", "guardrail": "Do not promote sources automatically."},
            {"workstream_id": "work_02_method_chapters", "guardrail": "Keep method gates explicit."},
            {"workstream_id": "work_03_h1_results", "guardrail": "No broad H1 superiority claim."},
            {"workstream_id": "work_04_h2_h3_results", "guardrail": "No intraday or causality claim."},
            {"workstream_id": "work_06_monitor_appendix", "guardrail": "No wallet-address exposure."},
            {"workstream_id": "work_07_swiss_result_gate", "guardrail": "No final Swiss claim before result."},
            {"workstream_id": "work_08_agent_outlook", "guardrail": "No active agents."},
            {"workstream_id": "work_10_final_qa", "guardrail": "Run final checks."},
        ]
    ).to_csv(results / "thesis_next_work_plan.csv", index=False)

    pd.DataFrame(
        [
            {
                "priority_band": "priority_1_method_foundation_review",
                "final_citation_readiness": "needs_full_source_review_before_final_citation",
            },
            {
                "priority_band": "priority_1_method_foundation_review",
                "final_citation_readiness": "needs_full_source_review_before_final_citation",
            },
            {
                "priority_band": "blocked_or_future_work_only",
                "final_citation_readiness": "not_allowed_for_thesis_facing_claims",
            },
        ]
    ).to_csv(results / "thesis_source_review_plan.csv", index=False)

    pd.DataFrame(
        [
            {"package_id": "T1", "thesis_label": "tab:t1", "include_in_core_package": True},
            {"package_id": "T2", "thesis_label": "tab:t2", "include_in_core_package": True},
            {"package_id": "T3", "thesis_label": "tab:t3", "include_in_core_package": True},
            {"package_id": "T4", "thesis_label": "tab:t4", "include_in_core_package": True},
            {"package_id": "T5", "thesis_label": "tab:t5", "include_in_core_package": True},
            {"package_id": "F1", "thesis_label": "fig:f1", "include_in_core_package": True},
            {"package_id": "F2", "thesis_label": "fig:f2", "include_in_core_package": True},
            {"package_id": "F3", "thesis_label": "fig:f3", "include_in_core_package": True},
            {"package_id": "F4", "thesis_label": "fig:f4", "include_in_core_package": True},
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)

    pd.DataFrame(
        [
            {"question_id": f"advisor_q{index:02d}_{suffix}", "guardrail": "fixture"}
            for index, suffix in [
                (1, "h1_wording"),
                (2, "source_depth"),
                (3, "h2_h3_scope"),
                (4, "table_figure_package"),
                (5, "monitor_appendix"),
                (6, "swiss_gate"),
                (7, "agent_outlook"),
                (8, "final_qa"),
            ]
        ]
    ).to_csv(results / "thesis_advisor_alignment_checklist.csv", index=False)


def _chapter_row(
    chapter_id: str,
    chapter_title: str,
    recommended_tables: str,
    recommended_figures: str,
) -> dict[str, str]:
    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "primary_artifacts": "data/results/thesis_evidence_map.csv; docs/research/RESEARCH_SPEC.md",
        "recommended_tables": recommended_tables,
        "recommended_figures": recommended_figures,
    }
