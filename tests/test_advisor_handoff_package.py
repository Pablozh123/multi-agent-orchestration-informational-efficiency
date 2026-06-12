from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_advisor_handoff_package import (
    PACKAGE_COLUMNS,
    generate_advisor_handoff_package,
)


def test_generate_advisor_handoff_package_writes_ordered_deliverables(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_package(repo_root=tmp_path)

    package = pd.read_csv(result.package_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(package.columns) == PACKAGE_COLUMNS
    assert result.package_rows == 7
    assert package["deliverable_id"].tolist()[0] == "advisor_report_docx"
    assert package["deliverable_id"].tolist()[-1] == "consolidation_index"
    assert "Thesis Advisor Handoff Package" in doc
    assert "Package deliverables: 7" in doc
    assert chr(223) not in doc


def test_advisor_handoff_package_preserves_boundaries(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_advisor_handoff_package(repo_root=tmp_path)

    package = pd.read_csv(result.package_path)
    joined = "\n".join(package.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "dozentenbericht_ba_thesis.docx" in joined
    assert "review-access bleibt pausiert" in joined
    assert "quellenstatus nicht automatisch hochstufen" in joined
    assert "keine runtime-agenten" in joined
    assert "thesis-facing claims" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    paths = [
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
        "docs/project/THESIS_EXECUTION_CHECKLIST.md",
        "docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md",
        "docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md",
        "docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md",
        "docs/project/THESIS_CONSOLIDATION_INDEX.md",
    ]
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"artifact_id": f"idx_{index:02d}", "path": path}
            for index, path in enumerate(paths, start=1)
        ]
    ).to_csv(results / "thesis_consolidation_index.csv", index=False)
