from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_traceability_audit import (
    METHOD_TRACEABILITY_COLUMNS,
    RESULT_PACKAGE_TRACEABILITY_COLUMNS,
    generate_thesis_traceability_audit,
)


def test_generate_thesis_traceability_audit_writes_counts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_traceability_audit(repo_root=tmp_path)

    methods = pd.read_csv(result.method_traceability_path)
    packages = pd.read_csv(result.result_package_traceability_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(methods.columns) == METHOD_TRACEABILITY_COLUMNS
    assert tuple(packages.columns) == RESULT_PACKAGE_TRACEABILITY_COLUMNS
    assert result.method_traceability_rows == 4
    assert result.thesis_facing_method_rows == 1
    assert result.thesis_facing_interpretation_rows == 1
    assert result.core_table_rows == 1
    assert result.core_figure_rows == 1
    assert "Thesis Traceability Audit" in doc
    assert "keine neuen Kennzahlen" in doc
    assert "Core table rows: 1" in doc
    assert chr(223) not in doc


def test_thesis_traceability_audit_keeps_final_review_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_traceability_audit(repo_root=tmp_path)

    methods = pd.read_csv(result.method_traceability_path)
    packages = pd.read_csv(result.result_package_traceability_path)
    method = methods[methods["evidence_id"] == "method_h1_fixture"].iloc[0]
    interpretation = methods[methods["evidence_id"] == "interpretation_h1_fixture"].iloc[0]
    table = packages[packages["package_id"] == "T1"].iloc[0]
    figure = packages[packages["package_id"] == "F1"].iloc[0]
    future = packages[packages["package_id"] == "A1"].iloc[0]

    assert method["traceability_status"] == "draft_traceable_final_source_review_pending"
    assert interpretation["traceability_status"] == "draft_traceable_final_source_review_pending"
    assert int(method["literature_source_count"]) == int(method["known_literature_source_count"])
    assert int(method["sources_pending_full_review_count"]) == 2
    assert "keine finale Zitation" in method["thesis_use_gate_de"]
    assert table["package_traceability_status"] == "core_package_ready_for_draft"
    assert figure["package_traceability_status"] == "core_package_ready_for_draft"
    assert future["package_traceability_status"] == "deferred_package_documentation_only"
    assert "keine finale Zitation" in table["thesis_use_gate_de"]


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    literature_dir = root / "data/literature"
    docs = root / "docs/research"
    results.mkdir(parents=True)
    literature_dir.mkdir(parents=True)
    docs.mkdir(parents=True)

    for relative in [
        "data/results/method.csv",
        "data/results/support.csv",
        "data/results/interp.csv",
        "data/results/table.csv",
        "data/results/figure.png",
        "docs/research/FUTURE.md",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"source_id": "source_method", "status": "skimmed"},
            {"source_id": "source_interpretation", "status": "skimmed"},
            {"source_id": "source_appendix", "status": "skimmed"},
        ]
    ).to_csv(literature_dir / "literature_index.csv", index=False)
    pd.DataFrame(
        [
            {
                "source_id": "source_method",
                "final_citation_readiness": "needs_full_source_review_before_final_citation",
            },
            {
                "source_id": "source_interpretation",
                "final_citation_readiness": "needs_full_source_review_before_final_citation",
            },
            {
                "source_id": "source_appendix",
                "final_citation_readiness": "not_currently_needed",
            },
        ]
    ).to_csv(results / "thesis_citation_readiness.csv", index=False)
    pd.DataFrame(
        [
            _evidence_row(
                "method_h1_fixture",
                "H1",
                "method",
                "thesis_facing_ready",
                "data/results/method.csv",
                "data/results/support.csv",
                "source_method; source_interpretation",
            ),
            _evidence_row(
                "interpretation_h1_fixture",
                "H1",
                "interpretation",
                "thesis_facing_ready",
                "data/results/interp.csv",
                "data/results/support.csv",
                "source_interpretation",
            ),
            _evidence_row(
                "method_monitor_fixture",
                "monitor",
                "method",
                "appendix_prototype_only",
                "data/results/support.csv",
                "data/results/support.csv",
                "source_appendix",
            ),
            _evidence_row(
                "interpretation_swiss_fixture",
                "swiss",
                "interpretation",
                "post_result_mapped_bounded",
                "data/results/support.csv",
                "data/results/support.csv",
                "source_interpretation",
            ),
            _evidence_row(
                "future_agent_fixture",
                "future_agents",
                "future_work",
                "future_work_deferred",
                "docs/research/FUTURE.md",
                "data/results/support.csv",
                "source_appendix",
            ),
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)
    pd.DataFrame(
        [
            _package_row(
                "T1",
                "table",
                True,
                "data/results/table.csv",
                "method_h1_fixture; interpretation_h1_fixture",
            ),
            _package_row(
                "F1",
                "figure",
                True,
                "data/results/figure.png",
                "interpretation_h1_fixture",
            ),
            _package_row(
                "A1",
                "appendix_artifact",
                False,
                "docs/research/FUTURE.md",
                "future_agent_fixture",
            ),
        ]
    ).to_csv(results / "thesis_curated_result_package.csv", index=False)
    pd.DataFrame(
        [
            _caption_row("T1"),
            _caption_row("F1"),
            _caption_row("A1"),
        ]
    ).to_csv(results / "thesis_table_figure_captions.csv", index=False)


def _evidence_row(
    evidence_id: str,
    thesis_area: str,
    item_type: str,
    readiness: str,
    primary: str,
    supporting: str,
    sources: str,
) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "thesis_area": thesis_area,
        "item_type": item_type,
        "claim_or_decision": "Fixture claim",
        "primary_artifact": primary,
        "supporting_artifacts": supporting,
        "literature_sources": sources,
        "allowed_wording": "bounded wording",
        "blocked_wording": "overclaim",
        "main_limitation": "fixture limitation",
        "thesis_readiness": readiness,
    }


def _package_row(
    package_id: str,
    package_type: str,
    include: bool,
    primary: str,
    evidence_ids: str,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "thesis_section": "fixture",
        "include_in_core_package": include,
        "thesis_readiness": "thesis_facing_ready" if include else "future_work_deferred",
        "primary_artifact": primary,
        "supporting_artifacts": "data/results/support.csv",
        "evidence_ids": evidence_ids,
        "main_limitation": "fixture limitation",
        "recommended_placement": "fixture",
        "thesis_message": "fixture message",
        "title": "fixture title",
    }


def _caption_row(package_id: str) -> dict[str, str]:
    return {
        "package_id": package_id,
        "package_type": "table",
        "thesis_label": f"label:{package_id.lower()}",
        "caption_de": "Fixture caption",
        "source_note_de": "Fixture source note",
        "interpretation_note_de": "Fixture interpretation note",
        "limitation_note_de": "Fixture limitation note",
        "primary_artifact": "data/results/support.csv",
        "supporting_artifacts": "data/results/support.csv",
        "evidence_ids": "method_h1_fixture",
        "include_in_core_package": True,
        "thesis_readiness": "thesis_facing_ready",
        "recommended_placement": "fixture",
    }
