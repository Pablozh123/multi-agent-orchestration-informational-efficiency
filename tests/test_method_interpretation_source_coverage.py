from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_method_interpretation_source_coverage import (
    COVERAGE_COLUMNS,
    generate_method_interpretation_source_coverage,
)


def test_generate_method_interpretation_source_coverage_writes_audit(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_method_interpretation_source_coverage(repo_root=tmp_path)

    coverage = pd.read_csv(result.coverage_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(coverage.columns) == COVERAGE_COLUMNS
    assert result.coverage_rows == 5
    assert result.thesis_facing_coverage_rows == 3
    assert result.source_ids == 3
    assert result.coverage_gap_rows == 0
    assert "Thesis Method/Interpretation Source Coverage" in doc
    assert "Coverage rows: 5" in doc
    assert "Thesis-facing coverage rows: 3" in doc
    assert "Coverage gap rows: 0" in doc
    assert chr(223) not in doc


def test_method_interpretation_source_coverage_keeps_final_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_method_interpretation_source_coverage(repo_root=tmp_path)

    coverage = pd.read_csv(result.coverage_path)
    joined = "\n".join(coverage.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()
    method_rows = coverage[coverage["evidence_id"] == "method_h1_fixture"]
    interpretation_rows = coverage[coverage["evidence_id"] == "interpretation_h1_fixture"]

    assert len(method_rows) == 2
    assert len(interpretation_rows) == 1
    assert method_rows["coverage_status"].eq("source_mapped_final_review_pending").all()
    assert interpretation_rows["coverage_status"].eq("source_mapped_final_review_pending").all()
    assert coverage["source_known_in_literature_index"].astype(bool).all()
    assert coverage["primary_artifact_exists"].astype(bool).all()
    assert "keine finale zitation" in joined
    assert "deterministische artefaktbindung" in joined
    assert "source review" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    literature_dir = root / "data/literature"
    results.mkdir(parents=True)
    literature_dir.mkdir(parents=True)

    for relative in [
        "data/results/method.csv",
        "data/results/support.csv",
        "data/results/interp.csv",
        "data/results/monitor.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            _source("source_method", "skimmed", "high"),
            _source("source_interpretation", "skimmed", "high"),
            _source("source_monitor", "candidate", "medium"),
        ]
    ).to_csv(literature_dir / "literature_index.csv", index=False)
    pd.DataFrame(
        [
            _readiness("source_method", "needs_full_source_review_before_final_citation"),
            _readiness("source_interpretation", "needs_full_source_review_before_final_citation"),
            _readiness("source_monitor", "not_currently_needed"),
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
                "data/results/monitor.csv",
                "data/results/support.csv",
                "source_monitor",
            ),
            _evidence_row(
                "interpretation_monitor_fixture",
                "monitor",
                "interpretation",
                "appendix_prototype_only",
                "data/results/monitor.csv",
                "data/results/support.csv",
                "source_monitor",
            ),
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)


def _source(source_id: str, status: str, relevance: str) -> dict[str, str]:
    return {
        "source_id": source_id,
        "title": f"Title {source_id}",
        "status": status,
        "relevance": relevance,
        "topic": "fixture_topic",
    }


def _readiness(source_id: str, readiness: str) -> dict[str, str]:
    return {
        "source_id": source_id,
        "final_citation_readiness": readiness,
    }


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
