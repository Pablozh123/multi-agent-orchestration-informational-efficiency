from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_source_review_progress_protocol import (
    PROTOCOL_COLUMNS,
    generate_source_review_progress_protocol,
)


def test_generate_source_review_progress_protocol_writes_protocol(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_progress_protocol(repo_root=tmp_path)

    protocol = pd.read_csv(result.protocol_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(protocol.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert tuple(protocol.columns) == PROTOCOL_COLUMNS
    assert result.protocol_rows == 6
    assert result.method_rows == 2
    assert result.interpretation_rows == 2
    assert result.core_table_rows == 2
    assert result.core_figure_rows == 1
    assert result.active_agent_rows == 0
    assert "Source Review Progress Protocol" in doc
    assert "Protocol rows: 6" in doc
    assert "Runtime-Agenten" in doc
    assert "methoden: 2/2" in joined
    assert "interpretationen: 2/2" in joined
    assert "kernpaket: 2 tabellen und 1 figuren" in joined
    assert "active: 0" in joined
    assert "llm_audit_log" in joined
    assert "max 50 rows" in joined
    assert chr(223) not in doc


def test_generate_source_review_progress_protocol_rejects_missing_method_source(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    traceability = pd.read_csv(tmp_path / "data/results/thesis_method_interpretation_traceability.csv")
    traceability.loc[traceability["evidence_id"] == "method_h1", "literature_source_count"] = 0
    traceability.to_csv(
        tmp_path / "data/results/thesis_method_interpretation_traceability.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="Not every thesis-facing method"):
        generate_source_review_progress_protocol(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(
        [
            _traceability("method_h1", "method"),
            _traceability("method_h2", "method"),
            _traceability("interpretation_h1", "interpretation"),
            _traceability("interpretation_h2", "interpretation"),
        ]
    ).to_csv(results / "thesis_method_interpretation_traceability.csv", index=False)
    pd.DataFrame(
        [
            _package("T1", "table", True, "core_package_ready_for_draft"),
            _package("T2", "table", True, "core_package_ready_for_draft"),
            _package("F1", "figure", True, "core_package_ready_for_draft"),
            _package("A1", "appendix_artifact", False, "deferred_package_documentation_only"),
        ]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)
    pd.DataFrame(
        [
            _ledger("ledger_h1"),
            _ledger("ledger_h2"),
            _ledger("ledger_h3"),
        ]
    ).to_csv(results / "thesis_source_review_progress_ledger.csv", index=False)
    pd.DataFrame(
        [
            _core_section("H1", "T2", "F1"),
            _core_section("H2", "T3", "F2"),
            _core_section("H3", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(
        [
            {"upgrade_id": "agent_upgrade_01", "current_status": "future_documentation_only"},
            {"upgrade_id": "agent_upgrade_02", "current_status": "future_deferred"},
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)


def _traceability(evidence_id: str, item_type: str) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "item_type": item_type,
        "thesis_readiness": "thesis_facing_ready",
        "primary_artifact_exists": True,
        "literature_source_count": 2,
        "known_literature_source_count": 2,
        "limitation_present": True,
        "traceability_status": "draft_traceable_final_source_review_pending",
    }


def _package(
    package_id: str,
    package_type: str,
    include: bool,
    status: str,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "include_in_core_package": include,
        "package_traceability_status": status,
    }


def _ledger(ledger_id: str) -> dict[str, object]:
    return {
        "ledger_id": ledger_id,
        "review_progress_state": "pending_manual_review",
        "source_status_change_allowed": False,
        "final_citation_ready": False,
        "preserved_manual_fields": False,
    }


def _core_section(hypothesis: str, table: str, figure: str) -> dict[str, str]:
    return {
        "hypothesis": hypothesis,
        "selected_tables": table,
        "selected_figures": figure,
    }
