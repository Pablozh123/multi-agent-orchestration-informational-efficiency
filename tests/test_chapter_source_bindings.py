from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_chapter_source_bindings import (
    BINDING_COLUMNS,
    generate_chapter_source_bindings,
)


def test_generate_chapter_source_bindings_writes_chapter_matrix(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_chapter_source_bindings(repo_root=tmp_path)

    bindings = pd.read_csv(result.bindings_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(bindings.columns) == BINDING_COLUMNS
    assert result.binding_rows == 2
    assert bindings["chapter_id"].tolist() == ["ch_01_intro", "ch_08_discussion_conclusion"]
    assert "Thesis Chapter Source Bindings" in doc
    assert "Chapter binding rows: 2" in doc
    assert "T1 (tab:t1)" in doc
    assert chr(223) not in doc


def test_chapter_source_bindings_keep_source_and_writing_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_chapter_source_bindings(repo_root=tmp_path)

    bindings = pd.read_csv(result.bindings_path)
    joined = "\n".join(bindings.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "human review" in joined
    assert "thesis-facing claims" in joined
    assert "limitation" in joined
    assert "source_task_01_src_priority" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    research = root / "docs/research"
    results.mkdir(parents=True)
    research.mkdir(parents=True)
    (results / "thesis_evidence_map.csv").write_text("fixture\n", encoding="utf-8")
    (research / "THESIS_AGENT_PIPELINE_ROADMAP.md").write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {
                "chapter_id": "ch_01_intro",
                "chapter_title": "Einleitung und Forschungsfrage",
                "core_evidence_ids": "method_h1_brier_dm",
                "recommended_tables": "T1",
                "recommended_figures": "",
                "primary_artifacts": "data/results/thesis_evidence_map.csv",
                "writing_status": "outline_ready",
            },
            {
                "chapter_id": "ch_08_discussion_conclusion",
                "chapter_title": "Diskussion und Fazit",
                "core_evidence_ids": "future_agent_pipeline_guarded",
                "recommended_tables": "",
                "recommended_figures": "",
                "primary_artifacts": "docs/research/THESIS_AGENT_PIPELINE_ROADMAP.md",
                "writing_status": "result_ready_with_limits",
            },
        ]
    ).to_csv(results / "thesis_chapter_plan.csv", index=False)

    pd.DataFrame(
        [
            {"source_id": "src_priority", "evidence_id": "method_h1_brier_dm"},
            {"source_id": "src_blocked", "evidence_id": "future_agent_pipeline_guarded"},
        ]
    ).to_csv(results / "thesis_citation_review_packets.csv", index=False)

    pd.DataFrame(
        [
            {
                "source_id": "src_priority",
                "review_task_id": "source_task_01_src_priority",
                "review_stage": "review_now_priority_1",
            },
            {
                "source_id": "src_blocked",
                "review_task_id": "source_task_02_src_blocked",
                "review_stage": "metadata_only_blocked",
            },
        ]
    ).to_csv(results / "thesis_source_review_execution.csv", index=False)

    pd.DataFrame(
        [
            {"package_id": "T1", "thesis_label": "tab:t1"},
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)
