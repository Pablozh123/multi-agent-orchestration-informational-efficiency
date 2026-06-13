from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_highlevel_next_step_control_summary import (
    SUMMARY_COLUMNS,
    generate_highlevel_next_step_control_summary,
)


def test_generate_highlevel_next_step_control_summary_writes_control_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_highlevel_next_step_control_summary(repo_root=tmp_path)

    summary = pd.read_csv(result.summary_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(summary.columns) == SUMMARY_COLUMNS
    assert result.summary_rows == 7
    assert result.thesis_facing_method_count == 4
    assert result.thesis_facing_interpretation_count == 4
    assert result.core_table_count == 5
    assert result.core_figure_count == 4
    assert result.final_release_ready_rows == 0
    assert result.active_runtime_agent_rows == 0
    assert summary["control_order"].tolist() == list(range(1, 8))
    assert summary["ready_for_bounded_draft"].map(_as_bool).all()
    assert not summary["ready_for_final_release"].map(_as_bool).any()
    assert "Highlevel Next-Step Control Summary" in doc
    assert "Summary rows: 7" in doc
    assert "Final-release ready rows: 0" in doc
    assert chr(223) not in doc


def test_highlevel_next_step_control_summary_keeps_requirements_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_highlevel_next_step_control_summary(repo_root=tmp_path)

    summary = pd.read_csv(result.summary_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(summary.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    boundary_text = f"{joined}\n{doc}"

    assert "4 thesis-facing Methoden" in boundary_text
    assert "4 thesis-facing Interpretationen" in boundary_text
    assert "23 H1-H2-H3 Source-Links" in boundary_text
    assert "31 total Methode-/Interpretation-Source-Links" in boundary_text
    assert "5 Kern-Tabellen" in boundary_text
    assert "4 Kern-Figuren" in boundary_text
    assert "4 Batch rows" in boundary_text
    assert "23 pending citation rows" in boundary_text
    assert "7 safety rows" in boundary_text
    assert "0 active runtime rows" in boundary_text
    assert "max 50 rows" in boundary_text
    assert "llm_audit_log" in boundary_text
    assert "keine Runtime-Agenten" in boundary_text
    assert "Keine finale Zitation" in boundary_text
    assert "Swiss" in boundary_text
    assert "DOCX" in boundary_text


def test_highlevel_next_step_control_summary_rejects_missing_artifact_coverage(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    coverage_path = tmp_path / "data/results/thesis_method_interpretation_source_coverage.csv"
    coverage = pd.read_csv(coverage_path)
    coverage.loc[0, "primary_artifact_exists"] = False
    coverage.to_csv(coverage_path, index=False)

    with pytest.raises(ValueError, match="source/artifact/limitation coverage"):
        generate_highlevel_next_step_control_summary(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs_project = root / "docs/project"
    docs_research = root / "docs/research"
    results.mkdir(parents=True)
    docs_project.mkdir(parents=True)
    docs_research.mkdir(parents=True)

    pd.DataFrame(_coverage_rows()).to_csv(
        results / "thesis_method_interpretation_source_coverage.csv",
        index=False,
    )
    pd.DataFrame(_traceability_rows()).to_csv(
        results / "thesis_result_package_traceability.csv",
        index=False,
    )
    pd.DataFrame(_curated_rows()).to_csv(
        results / "thesis_curated_result_package.csv",
        index=False,
    )
    pd.DataFrame(
        [
            _batch_row("batch_plan_h1", 10, 4, 4, 6, 10),
            _batch_row("batch_plan_h2", 5, 3, 3, 2, 5),
            _batch_row("batch_plan_h3", 8, 4, 5, 3, 8),
            _batch_row("batch_plan_total_rebuild_gate", 23, 9, 12, 11, 23),
        ]
    ).to_csv(results / "thesis_source_review_batch_execution_plan.csv", index=False)
    pd.DataFrame(
        [
            _core_section("core_section_h1", "H1", "T2", "F1"),
            _core_section("core_section_h2", "H2", "T3", "F2"),
            _core_section("core_section_h3", "H3", "T4", "F3"),
        ]
    ).to_csv(results / "thesis_h1_h2_h3_core_sections.csv", index=False)
    pd.DataFrame(_final_gate_rows()).to_csv(
        results / "thesis_final_gate_board.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "safety_case_id": f"agent_safety_{idx:02d}",
                "future_agent_scope": f"Scope {idx}",
                "current_status": "future_documentation_only" if idx < 7 else "future_deferred",
            }
            for idx in range(1, 8)
        ]
    ).to_csv(results / "thesis_agent_pipeline_safety_case.csv", index=False)
    pd.DataFrame(
        [
            {
                "upgrade_id": f"agent_upgrade_{idx:02d}",
                "future_assistance_role": f"Role {idx}",
                "current_status": "future_documentation_only" if idx < 7 else "future_deferred",
            }
            for idx in range(1, 8)
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)
    pd.DataFrame(
        [
            {
                "workstream_id": f"work_{idx:02d}",
                "priority_order": idx,
                "workstream": f"Work {idx}",
                "next_action": "Naechster Schritt.",
                "guardrail": "Keine Runtime-Agenten.",
            }
            for idx in range(1, 11)
        ]
    ).to_csv(results / "thesis_next_work_plan.csv", index=False)

    for relative in [
        "data/results/thesis_method_interpretation_traceability.csv",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/project/THESIS_SOURCE_REVIEW_BATCH_EXECUTION_PLAN.md",
        "data/results/swiss_referendum_10mio_running_status.json",
        "data/results/monitor_anomaly_review_summary.csv",
        "STATUS.md",
        "docs/project/WORK_LOG.md",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


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
        ("method_swiss", "swiss_referendum", "method", "descriptive_pending_result", ["lit_b", "lit_c"]),
        ("interpretation_swiss", "swiss_referendum", "interpretation", "descriptive_pending_result", ["lit_b"]),
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
                    "source_known_in_literature_index": True,
                    "primary_artifact_exists": True,
                    "limitation_present": True,
                    "coverage_status": "source_mapped_final_review_pending",
                }
            )
            idx += 1
    assert len(rows) == 31
    return rows


def _traceability_rows() -> list[dict[str, object]]:
    rows = []
    for package_id, package_type in [
        ("T1", "table"),
        ("T2", "table"),
        ("T3", "table"),
        ("T4", "table"),
        ("T5", "table"),
        ("F1", "figure"),
        ("F2", "figure"),
        ("F3", "figure"),
        ("F4", "figure"),
        ("A1", "appendix_artifact"),
    ]:
        include = package_id != "A1"
        rows.append(
            {
                "package_id": package_id,
                "package_type": package_type,
                "thesis_section": "section",
                "include_in_core_package": include,
                "primary_artifact_exists": True,
                "caption_present": True,
                "source_note_present": True,
                "limitation_note_present": True,
                "package_traceability_status": (
                    "core_package_ready_for_draft"
                    if include
                    else "deferred_package_documentation_only"
                ),
            }
        )
    return rows


def _curated_rows() -> list[dict[str, object]]:
    return [
        {
            "package_id": row["package_id"],
            "package_type": row["package_type"],
            "include_in_core_package": row["include_in_core_package"],
            "recommended_placement": "main_text" if row["include_in_core_package"] else "appendix_or_future_work",
            "thesis_readiness": "thesis_facing_ready" if row["include_in_core_package"] else "future_work_deferred",
        }
        for row in _traceability_rows()
    ]


def _batch_row(
    batch_plan_id: str,
    source_review_rows: int,
    unique_sources: int,
    method_rows: int,
    interpretation_rows: int,
    pending_rows: int,
) -> dict[str, object]:
    return {
        "batch_plan_id": batch_plan_id,
        "source_review_rows": source_review_rows,
        "unique_sources": unique_sources,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "pending_citation_rows": pending_rows,
        "final_ready_rows": 0,
        "source_status_change_rows": 0,
        "ready_for_manual_execution": True,
        "ready_for_final_release": False,
    }


def _core_section(section_id: str, hypothesis: str, table: str, figure: str) -> dict[str, object]:
    return {
        "section_id": section_id,
        "hypothesis": hypothesis,
        "method_evidence_ids": f"method_{hypothesis.lower()}",
        "interpretation_evidence_ids": f"interpretation_{hypothesis.lower()}",
        "deterministic_artifacts": "data/results/artifact.csv",
        "selected_tables": table,
        "selected_figures": figure,
        "source_review_gate_de": "Draft nutzbar; finale Zitation erst nach Source Review.",
    }


def _final_gate_rows() -> list[dict[str, object]]:
    rows = []
    for gate_area in [
        "source_review",
        "h1_h2_h3_drafting",
        "result_package",
        "swiss_result_gate",
        "monitor_appendix",
        "future_agents",
        "docx_render_qa",
        "project_control",
    ]:
        final_ready = gate_area == "future_agents"
        evidence_count = 50 if gate_area == "swiss_result_gate" else 1
        rows.append(
            {
                "gate_area": gate_area,
                "current_status": (
                    "final_blocked_official_result"
                    if gate_area == "swiss_result_gate"
                    else "deferred_future_work_only"
                    if gate_area == "future_agents"
                    else "final_blocked_pending"
                ),
                "draft_use_allowed": True,
                "final_submission_ready": final_ready,
                "evidence_count": evidence_count,
                "blocking_count": 0 if final_ready else 1,
                "required_next_action_de": "Naechster Schritt.",
            }
        )
    return rows


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
