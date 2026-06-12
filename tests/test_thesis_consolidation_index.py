from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_consolidation_index import (
    INDEX_COLUMNS,
    generate_thesis_consolidation_index,
)


def test_generate_thesis_consolidation_index_writes_artifact_map(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation_index(repo_root=tmp_path)

    index = pd.read_csv(result.index_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(index.columns) == INDEX_COLUMNS
    assert result.index_rows == 14
    assert "Thesis Consolidation Index" in doc
    assert "Indexed artifacts: 14" in doc
    assert "dozentenbericht_ba_thesis.docx" in doc
    assert "THESIS_EXECUTION_CHECKLIST.md" in doc
    assert "THESIS_SOURCE_REVIEW_EXECUTION.md" in doc
    assert "THESIS_WORDING_GUARD.md" in doc
    assert chr(223) not in doc


def test_thesis_consolidation_index_keeps_deferred_boundaries(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_consolidation_index(repo_root=tmp_path)

    index = pd.read_csv(result.index_path)
    joined = "\n".join(index.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "review-access bleibt pausiert" in joined
    assert "keine runtime-agenten" in joined
    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "keine roh" in joined
    assert "trading-pfade" in joined


def _write_fixture(root: Path) -> None:
    paths = [
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/dozentenbericht_ba_thesis.md",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
        "docs/research/THESIS_NEXT_WORK_PLAN.md",
        "docs/project/THESIS_EXECUTION_CHECKLIST.md",
        "data/results/thesis_execution_checklist.csv",
        "docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md",
        "docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md",
        "data/results/thesis_source_review_execution.csv",
        "docs/research/THESIS_WORDING_GUARD.md",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/research/THESIS_CHAPTER_DRAFT.md",
        "docs/research/THESIS_SOURCE_REVIEW_PLAN.md",
        "docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
