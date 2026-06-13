from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_highlevel_thesis_writing_handoff import (
    HANDOFF_COLUMNS,
    generate_highlevel_thesis_writing_handoff,
)


def test_generate_highlevel_thesis_writing_handoff_writes_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_highlevel_thesis_writing_handoff(repo_root=tmp_path)

    handoff = pd.read_csv(result.handoff_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(handoff.columns) == HANDOFF_COLUMNS
    assert result.handoff_rows == 7
    assert result.bounded_draft_rows == 7
    assert result.final_submission_ready_rows == 0
    assert result.core_table_count == 5
    assert result.core_figure_count == 4
    assert result.active_runtime_agent_rows == 0
    assert handoff["handoff_order"].tolist() == list(range(1, 8))
    assert handoff["ready_for_bounded_draft"].map(_as_bool).all()
    assert not handoff["ready_for_final_submission"].map(_as_bool).any()
    assert "Highlevel Thesis Writing Handoff Ohne Review-Access" in doc
    assert "Handoff rows: 7" in doc
    assert "Final-submission ready rows: 0" in doc
    assert chr(223) not in doc


def test_highlevel_thesis_writing_handoff_keeps_source_and_agent_gates_visible(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_highlevel_thesis_writing_handoff(repo_root=tmp_path)

    handoff = pd.read_csv(result.handoff_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(handoff.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    boundary_text = f"{joined}\n{doc}".lower()

    assert "review-access bleibt pausiert" in boundary_text
    assert "jede methode" in boundary_text
    assert "jede interpretation" in boundary_text
    assert "source id" in boundary_text
    assert "evidence id" in boundary_text
    assert "deterministisches artefakt" in boundary_text
    assert "23 worksheet rows" in boundary_text
    assert "12 method rows" in boundary_text
    assert "11 interpretation rows" in boundary_text
    assert "0 source/artifact gaps" in boundary_text
    assert "15 drafting steps" in boundary_text
    assert "5 kern-tabellen" in boundary_text
    assert "4 kern-figuren" in boundary_text
    assert "t2/f1" in boundary_text
    assert "t3/f2" in boundary_text
    assert "t4/f3" in boundary_text
    assert "23 pending citation rows" in boundary_text
    assert "keine finale zitation" in boundary_text
    assert "keine runtime-agenten" in boundary_text
    assert "0 active runtime rows" in boundary_text
    assert "max 50 rows" in boundary_text
    assert "llm_audit_log" in boundary_text
    assert "swiss" in boundary_text
    assert "docx" in boundary_text


def test_highlevel_thesis_writing_handoff_rejects_active_agents(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    path = tmp_path / "data/results/thesis_agent_pipeline_upgrade_plan.csv"
    agent_plan = pd.read_csv(path)
    agent_plan.loc[0, "current_status"] = "active_runtime_agent"
    agent_plan.to_csv(path, index=False)

    with pytest.raises(ValueError, match="active runtime agents"):
        generate_highlevel_thesis_writing_handoff(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs_project = root / "docs/project"
    docs_research = root / "docs/research"
    results.mkdir(parents=True)
    docs_project.mkdir(parents=True)
    docs_research.mkdir(parents=True)

    pd.DataFrame(_highlevel_rows()).to_csv(
        results / "thesis_highlevel_next_step_control_summary.csv",
        index=False,
    )
    pd.DataFrame(_core_rows()).to_csv(
        results / "thesis_h1_h2_h3_core_sections.csv",
        index=False,
    )
    pd.DataFrame(_bridge_rows()).to_csv(
        results / "thesis_h1_h2_h3_worksheet_drafting_bridge.csv",
        index=False,
    )
    pd.DataFrame(_drafting_pass_rows()).to_csv(
        results / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
        index=False,
    )
    pd.DataFrame(_curated_package_rows()).to_csv(
        results / "thesis_curated_result_package.csv",
        index=False,
    )
    pd.DataFrame(_final_gate_rows()).to_csv(
        results / "thesis_final_gate_board.csv",
        index=False,
    )
    pd.DataFrame(_agent_rows()).to_csv(
        results / "thesis_agent_pipeline_upgrade_plan.csv",
        index=False,
    )

    for relative in [
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "data/results/thesis_source_review_batch_execution_plan.csv",
        "data/results/thesis_source_review_progress_ledger.csv",
        "data/results/thesis_ledger_citation_gate_summary.csv",
        "data/results/thesis_agent_pipeline_safety_case.csv",
        "data/results/artifact_h1.csv",
        "data/results/artifact_h2.csv",
        "data/results/artifact_h3.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _highlevel_rows() -> list[dict[str, object]]:
    return [
        {
            "control_id": f"next_step_{idx:02d}",
            "control_order": idx,
            "control_area": f"area_{idx}",
            "authoritative_inputs": "data/results/input.csv",
            "ready_for_bounded_draft": True,
            "ready_for_final_release": False,
        }
        for idx in range(1, 8)
    ]


def _core_rows() -> list[dict[str, object]]:
    return [
        _core_row("H1", "H1: Prognosequalitaet", "T2", "F1", "data/results/artifact_h1.csv"),
        _core_row("H2", "H2: Tagesbasierte Ereignisfenster", "T3", "F2", "data/results/artifact_h2.csv"),
        _core_row("H3", "H3: Wallet-Timing-Diagnostik", "T4", "F3", "data/results/artifact_h3.csv"),
    ]


def _core_row(
    area: str,
    title: str,
    table: str,
    figure: str,
    artifact: str,
) -> dict[str, object]:
    return {
        "section_id": f"core_section_{area.lower()}",
        "hypothesis": area,
        "chapter_title_de": title,
        "method_evidence_ids": f"method_{area.lower()}",
        "interpretation_evidence_ids": f"interpretation_{area.lower()}",
        "literature_source_ids": f"lit_{area.lower()}_001",
        "deterministic_artifacts": artifact,
        "selected_tables": table,
        "selected_figures": figure,
        "thesis_ready_result_de": f"{area} Resultatseed bleibt bounded.",
        "bounded_interpretation_de": f"{area} Interpretation bleibt begrenzt.",
        "mandatory_limitation_de": f"{area} Limitation bleibt sichtbar.",
        "source_review_gate_de": "Draft nutzbar; finale Zitation erst nach Source Review.",
    }


def _bridge_rows() -> list[dict[str, object]]:
    return [
        _bridge_row("H1", 10, 4, 6, 4, 10, 5, "T2", "F1"),
        _bridge_row("H2", 5, 3, 2, 3, 5, 5, "T3", "F2"),
        _bridge_row("H3", 8, 5, 3, 4, 8, 5, "T4", "F3"),
        _bridge_row("TOTAL", 23, 12, 11, 9, 23, 15, "T2, T3, T4", "F1, F2, F3"),
    ]


def _bridge_row(
    area: str,
    worksheet_rows: int,
    method_rows: int,
    interpretation_rows: int,
    unique_sources: int,
    pending_rows: int,
    drafting_steps: int,
    table: str,
    figure: str,
) -> dict[str, object]:
    return {
        "thesis_area": area,
        "worksheet_rows": worksheet_rows,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "unique_sources": unique_sources,
        "method_interpretation_source_artifact_gap_rows": 0,
        "pending_citation_rows": pending_rows,
        "final_release_ready_rows": 0,
        "drafting_steps": drafting_steps,
        "selected_tables": table,
        "selected_figures": figure,
        "source_artifact_rule_de": "Jede Methode und jede Interpretation muss Source ID, Evidence ID und Artefakt behalten.",
        "writing_bridge_action_de": f"{area}: Drafting-Schritte mit {table}/{figure} schreiben.",
        "final_blocker_de": f"{area}: final blockiert bis Manual Source Review abgeschlossen ist.",
        "future_agent_boundary_de": "Keine Runtime-Agenten; max 50 rows und llm_audit_log vor spaeterer Hilfe.",
        "ready_for_bounded_drafting": True,
        "ready_for_final_release": False,
    }


def _drafting_pass_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    order = 1
    for area in ("H1", "H2", "H3"):
        for section in range(1, 6):
            rows.append(
                {
                    "drafting_pass_id": f"draft_{area.lower()}_{section}",
                    "thesis_area": area,
                    "draft_sequence_order": order,
                    "ready_for_bounded_draft": True,
                    "ready_for_final_submission": False,
                    "draft_status": "source_gated_thesis_draft_ready_final_source_review_pending",
                }
            )
            order += 1
    return rows


def _curated_package_rows() -> list[dict[str, object]]:
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
                "include_in_core_package": include,
                "recommended_placement": "main_text" if include else "appendix",
                "thesis_readiness": "thesis_facing_ready" if include else "future_work_deferred",
            }
        )
    return rows


def _final_gate_rows() -> list[dict[str, object]]:
    rows = []
    for area in [
        "source_review",
        "swiss_result_gate",
        "docx_render_qa",
        "monitor_appendix",
        "future_agents",
    ]:
        rows.append(
            {
                "gate_area": area,
                "current_status": "final_blocked_pending",
                "draft_use_allowed": True,
                "final_submission_ready": False,
                "evidence_count": 23 if area == "source_review" else 1,
                "blocking_count": 1,
            }
        )
    return rows


def _agent_rows() -> list[dict[str, object]]:
    return [
        {
            "upgrade_id": f"agent_upgrade_{idx:02d}",
            "future_assistance_role": f"Role {idx}",
            "current_status": "future_documentation_only" if idx < 7 else "future_deferred",
        }
        for idx in range(1, 8)
    ]


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
