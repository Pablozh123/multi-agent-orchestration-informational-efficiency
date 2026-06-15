from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_agent_pipeline_safety_case import (
    SAFETY_CASE_COLUMNS,
    generate_agent_pipeline_safety_case,
)


def test_generate_agent_pipeline_safety_case_writes_guarded_artifacts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_pipeline_safety_case(repo_root=tmp_path)

    safety = pd.read_csv(result.safety_case_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(safety.columns) == SAFETY_CASE_COLUMNS
    assert result.safety_case_rows == 7
    assert result.documentation_only_rows == 6
    assert result.deferred_rows == 1
    assert result.active_rows == 0
    assert "Thesis Agent Pipeline Safety Case" in doc
    assert "23 H1-H2-H3 Review-Zeilen" in doc
    assert "5 Tabellen und 4 Figuren" in doc
    assert "0 aktive Rows" in doc
    assert "max 50 rows" in doc
    assert "llm_audit_log" in doc
    assert "keine Runtime-Agenten" in doc
    assert "kein MCP" in doc
    assert "kein Model Routing" in doc
    assert "keine LLM-Metriken" in doc
    assert "keine Trading-Pfade" in doc
    assert chr(223) not in doc


def test_agent_pipeline_safety_case_binds_mapping_package_and_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_pipeline_safety_case(repo_root=tmp_path)

    safety = pd.read_csv(result.safety_case_path)
    rows = {row["safety_case_id"]: row for row in safety.to_dict(orient="records")}

    evidence_lock = rows["agent_safety_01_evidence_lock"]
    package_guard = rows["agent_safety_03_result_package_guard"]
    swiss_boundary = rows["agent_safety_06_monitor_swiss_boundary"]
    access_contract = rows["agent_safety_07_bounded_access_contract"]

    assert "4 thesis-facing Methoden" in evidence_lock["current_evidence_anchor_de"]
    assert "4 thesis-facing Interpretationen" in evidence_lock["current_evidence_anchor_de"]
    assert "23 H1-H2-H3 Source-Links" in evidence_lock["current_evidence_anchor_de"]
    assert "31 Methode-/Interpretation-Source-Links" in evidence_lock["current_evidence_anchor_de"]
    assert "Coverage-Gaps: 0" in evidence_lock["current_evidence_anchor_de"]
    assert "5 Tabellen und 4 Figuren" in package_guard["current_evidence_anchor_de"]
    assert "Package-Gaps: 0" in package_guard["current_evidence_anchor_de"]
    assert "post_result_mapped_source_review_pending" in swiss_boundary["current_evidence_anchor_de"]
    assert "45 Final-Case-Live-Zeilen" in swiss_boundary["current_evidence_anchor_de"]
    assert access_contract["current_status"] == "future_deferred"
    assert "no SELECT star" in access_contract["proof_before_activation_de"]


def test_agent_pipeline_safety_case_rejects_active_agent_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    pd.DataFrame(
        [
            {
                "upgrade_id": "agent_upgrade_01",
                "future_assistance_role": "Manual source review",
                "current_status": "active_runtime_agent",
            }
        ]
    ).to_csv(tmp_path / "data/results/thesis_agent_pipeline_upgrade_plan.csv", index=False)

    with pytest.raises(ValueError, match="must not include active runtime agent rows"):
        generate_agent_pipeline_safety_case(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(_coverage_rows()).to_csv(
        results / "thesis_method_interpretation_source_coverage.csv",
        index=False,
    )
    pd.DataFrame(
        [
            _package_row("T1", "table"),
            _package_row("T2", "table"),
            _package_row("T3", "table"),
            _package_row("T4", "table"),
            _package_row("T5", "table"),
            _package_row("F1", "figure"),
            _package_row("F2", "figure"),
            _package_row("F3", "figure"),
            _package_row("F4", "figure"),
            {
                "package_id": "A1",
                "package_type": "appendix_artifact",
                "include_in_core_package": False,
                "package_traceability_status": "deferred_package_documentation_only",
            },
        ]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)
    pd.DataFrame(
        [
            _overview_row("H1", 10, 4),
            _overview_row("H2", 5, 3),
            _overview_row("H3", 8, 4),
        ]
    ).to_csv(results / "thesis_manual_source_review_followup_overview.csv", index=False)
    pd.DataFrame(
        [
            {
                "gate_area": "swiss_result_gate",
                "current_status": "post_result_mapped_source_review_pending",
                "final_submission_ready": False,
                "evidence_count": 45,
            },
            {
                "gate_area": "future_agents",
                "current_status": "deferred_future_work_only",
                "final_submission_ready": True,
                "evidence_count": 7,
            },
        ]
    ).to_csv(results / "thesis_final_gate_board.csv", index=False)
    pd.DataFrame(
        [
            {
                "upgrade_id": f"agent_upgrade_{idx:02d}",
                "future_assistance_role": role,
                "current_status": status,
            }
            for idx, (role, status) in enumerate(
                [
                    ("Manual source review", "future_documentation_only"),
                    ("Evidence-to-prose drafting", "future_documentation_only"),
                    ("Claim and wording review", "future_documentation_only"),
                    ("Table and figure package review", "future_documentation_only"),
                    ("Advisor update summarisation", "future_documentation_only"),
                    ("Monitor appendix review", "future_documentation_only"),
                    ("Bounded MCP summary interface", "future_deferred"),
                ],
                start=1,
            )
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)
    pd.DataFrame(
        [
            {
                "future_assistance_role": f"role_{idx}",
                "current_activation_state": "future_documentation_only",
            }
            for idx in range(1, 8)
        ]
    ).to_csv(results / "thesis_agent_pipeline_control_audit.csv", index=False)


def _coverage_rows() -> list[dict[str, object]]:
    evidence = [
        ("method_h1", "H1", "method", "thesis_facing_ready", ["lit_a", "lit_b", "lit_c", "lit_d"]),
        ("method_h2", "H2", "method", "thesis_facing_ready", ["lit_a", "lit_e", "lit_f"]),
        ("method_h3_wallet", "H3", "method", "thesis_facing_ready", ["lit_a", "lit_g", "lit_h"]),
        ("method_h3_granger", "H3", "method", "thesis_facing_ready", ["lit_g", "lit_h"]),
        ("interpretation_h1_a", "H1", "interpretation", "thesis_facing_ready", ["lit_b", "lit_c", "lit_d"]),
        ("interpretation_h1_b", "H1", "interpretation", "thesis_facing_ready", ["lit_b", "lit_d"]),
        ("interpretation_h2", "H2", "interpretation", "thesis_facing_ready", ["lit_a", "lit_e"]),
        ("interpretation_h3", "H3", "interpretation", "thesis_facing_ready", ["lit_a", "lit_g", "lit_i", "lit_h"]),
        ("method_monitor", "monitor_prototype", "method", "appendix_prototype_only", ["lit_a", "lit_i", "lit_e"]),
        ("interpretation_monitor", "monitor_prototype", "interpretation", "appendix_prototype_only", ["lit_i", "lit_e"]),
        ("method_swiss", "swiss_referendum", "method", "post_result_mapped_bounded", ["lit_b", "lit_c"]),
        ("interpretation_swiss", "swiss_referendum", "interpretation", "post_result_mapped_bounded", ["lit_b"]),
    ]
    rows: list[dict[str, object]] = []
    idx = 1
    for evidence_id, area, item_type, readiness, sources in evidence:
        for source in sources:
            rows.append(
                {
                    "coverage_id": f"coverage_{idx:03d}",
                    "evidence_id": evidence_id,
                    "thesis_area": area,
                    "item_type": item_type,
                    "thesis_readiness": readiness,
                    "source_id": source,
                    "primary_artifact_exists": True,
                    "coverage_status": "source_mapped_final_review_pending",
                }
            )
            idx += 1
    assert len(rows) == 31
    return rows


def _package_row(package_id: str, package_type: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "include_in_core_package": True,
        "package_traceability_status": "core_package_ready_for_draft",
    }


def _overview_row(slice_id: str, rows: int, unique_sources: int) -> dict[str, object]:
    return {
        "slice_id": slice_id,
        "review_rows": rows,
        "pending_rows": rows,
        "final_ready_rows": 0,
        "unique_sources": unique_sources,
    }
