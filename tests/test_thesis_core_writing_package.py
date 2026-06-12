from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_thesis_core_writing_package import (
    AGENT_UPGRADE_COLUMNS,
    CORE_SECTION_COLUMNS,
    generate_thesis_core_writing_package,
)


def test_generate_thesis_core_writing_package_writes_core_sections(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_core_writing_package(repo_root=tmp_path)

    core = pd.read_csv(result.core_sections_path)
    agent = pd.read_csv(result.agent_upgrade_path)
    core_doc = result.core_sections_docs_path.read_text(encoding="utf-8")
    agent_doc = result.agent_upgrade_docs_path.read_text(encoding="utf-8")

    assert tuple(core.columns) == CORE_SECTION_COLUMNS
    assert tuple(agent.columns) == AGENT_UPGRADE_COLUMNS
    assert result.core_section_rows == 3
    assert result.agent_upgrade_rows == 2
    assert list(core["hypothesis"]) == ["H1", "H2", "H3"]
    assert "Thesis H1-H2-H3 Core Sections" in core_doc
    assert "Core sections: 3" in core_doc
    assert "T2/F1 fuer H1" in core_doc
    assert "Thesis Agent Pipeline Upgrade Plan" in agent_doc
    assert "Documentation-only rows: 1" in agent_doc
    assert "Deferred rows: 1" in agent_doc
    assert chr(223) not in core_doc
    assert chr(223) not in agent_doc


def test_core_sections_bind_methods_interpretations_sources_and_artifacts(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_core_writing_package(repo_root=tmp_path)

    core = pd.read_csv(result.core_sections_path)
    h1 = core[core["hypothesis"] == "H1"].iloc[0]
    h2 = core[core["hypothesis"] == "H2"].iloc[0]
    h3 = core[core["hypothesis"] == "H3"].iloc[0]
    joined = "\n".join(core.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "method_h1" in h1["method_evidence_ids"]
    assert "interpretation_h1" in h1["interpretation_evidence_ids"]
    assert "lit_brier_001" in h1["literature_source_ids"]
    assert "data/results/h1_result.csv" in h1["deterministic_artifacts"]
    assert h1["selected_tables"] == "T2"
    assert h1["selected_figures"] == "F1"
    assert h2["selected_tables"] == "T3"
    assert h2["selected_figures"] == "F2"
    assert h3["selected_tables"] == "T4"
    assert h3["selected_figures"] == "F3"
    assert "brier" in joined
    assert "tages" in joined
    assert "granger" in joined
    assert "source review" in joined
    assert "keine rohartefakt-dumps" in result.core_sections_docs_path.read_text(encoding="utf-8").lower()


def test_agent_upgrade_plan_stays_documentation_only(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_core_writing_package(repo_root=tmp_path)

    agent = pd.read_csv(result.agent_upgrade_path)
    joined = "\n".join(agent.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert set(agent["current_status"]) == {"future_documentation_only", "future_deferred"}
    assert "core_section_h1; core_section_h2; core_section_h3" in joined
    assert "llm_audit_log" in joined
    assert "bounded" in joined
    assert "keine runtime-agenten" in joined
    assert "keine llm-metriken" in joined
    assert "keine trading-pfade" in joined
    assert "keine rohartefakt-dumps" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    literature = root / "data/literature"
    docs = root / "docs/research"
    results.mkdir(parents=True)
    literature.mkdir(parents=True)
    docs.mkdir(parents=True)

    for relative in [
        "data/results/h1_method.csv",
        "data/results/h1_result.csv",
        "data/results/h1_support.csv",
        "data/results/h1_figure.png",
        "data/results/h2_method.csv",
        "data/results/h2_result.csv",
        "data/results/h2_support.csv",
        "data/results/h2_figure.png",
        "data/results/h3_method.csv",
        "data/results/h3_result.csv",
        "data/results/h3_support.csv",
        "data/results/h3_figure.png",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    pd.DataFrame(
        [
            {"source_id": "lit_brier_001"},
            {"source_id": "lit_dm_001"},
            {"source_id": "lit_eventstudy_001"},
            {"source_id": "lit_granger_001"},
            {"source_id": "zotero_poly_001"},
        ]
    ).to_csv(literature / "literature_index.csv", index=False)

    pd.DataFrame(
        [
            _evidence_row(
                "method_h1",
                "H1",
                "method",
                "data/results/h1_method.csv",
                "data/results/h1_support.csv",
                "lit_brier_001; lit_dm_001",
                "reaction speed proof",
                "H1 method limitation",
            ),
            _evidence_row(
                "interpretation_h1",
                "H1",
                "interpretation",
                "data/results/h1_result.csv",
                "data/results/h1_support.csv",
                "lit_brier_001",
                "general superiority",
                "H1 interpretation limitation",
            ),
            _evidence_row(
                "method_h2",
                "H2",
                "method",
                "data/results/h2_method.csv",
                "data/results/h2_support.csv",
                "lit_eventstudy_001",
                "intraday speed claim",
                "H2 method limitation",
            ),
            _evidence_row(
                "interpretation_h2",
                "H2",
                "interpretation",
                "data/results/h2_result.csv",
                "data/results/h2_support.csv",
                "lit_eventstudy_001",
                "causal event proof",
                "H2 interpretation limitation",
            ),
            _evidence_row(
                "method_h3_tiers",
                "H3",
                "method",
                "data/results/h3_method.csv",
                "data/results/h3_support.csv",
                "zotero_poly_001",
                "arbitrary whale threshold",
                "H3 tier limitation",
            ),
            _evidence_row(
                "method_h3_granger",
                "H3",
                "method",
                "data/results/h3_method.csv",
                "data/results/h3_support.csv",
                "lit_granger_001",
                "causality proof",
                "H3 Granger limitation",
            ),
            _evidence_row(
                "interpretation_h3",
                "H3",
                "interpretation",
                "data/results/h3_result.csv",
                "data/results/h3_support.csv",
                "lit_granger_001; zotero_poly_001",
                "private-information proof",
                "H3 interpretation limitation",
            ),
        ]
    ).to_csv(results / "thesis_evidence_map.csv", index=False)

    pd.DataFrame(
        [
            _core_result(
                "core_h1_bounded_poll_scope",
                "H1",
                "262/285 lower Brier loss",
                "method_h1; interpretation_h1",
                "data/results/h1_result.csv",
                "data/results/h1_support.csv",
            ),
            _core_result(
                "core_h1_broad_claim_boundary",
                "H1",
                "0/9 broad rows prove the claim",
                "interpretation_h1",
                "data/results/h1_result.csv",
                "data/results/h1_support.csv",
            ),
            _core_result(
                "core_h2_largest_daily_event_window",
                "H2",
                "event window 7.2 pp",
                "method_h2; interpretation_h2",
                "data/results/h2_result.csv",
                "data/results/h2_support.csv",
            ),
            _core_result(
                "core_h3_top_tier_timing",
                "H3",
                "lag 1 Granger p=0.0012",
                "method_h3_tiers; method_h3_granger; interpretation_h3",
                "data/results/h3_result.csv",
                "data/results/h3_support.csv",
            ),
        ]
    ).to_csv(results / "thesis_core_results_table.csv", index=False)

    pd.DataFrame(
        [
            _package_row("T2", "table", "H1", "data/results/h1_result.csv", "data/results/h1_support.csv"),
            _package_row("F1", "figure", "H1", "data/results/h1_figure.png", "data/results/h1_support.csv"),
            _package_row("T3", "table", "H2", "data/results/h2_result.csv", "data/results/h2_support.csv"),
            _package_row("F2", "figure", "H2", "data/results/h2_figure.png", "data/results/h2_support.csv"),
            _package_row("T4", "table", "H3", "data/results/h3_result.csv", "data/results/h3_support.csv"),
            _package_row("F3", "figure", "H3", "data/results/h3_figure.png", "data/results/h3_support.csv"),
        ]
    ).to_csv(results / "thesis_curated_result_package.csv", index=False)

    pd.DataFrame([_caption_row(pid) for pid in ["T2", "F1", "T3", "F2", "T4", "F3"]]).to_csv(
        results / "thesis_table_figure_captions.csv",
        index=False,
    )

    pd.DataFrame(
        [
            {
                "evidence_id": evidence_id,
                "traceability_status": "draft_traceable_final_source_review_pending",
                "thesis_readiness": "thesis_facing_ready",
            }
            for evidence_id in [
                "method_h1",
                "interpretation_h1",
                "method_h2",
                "interpretation_h2",
                "method_h3_tiers",
                "method_h3_granger",
                "interpretation_h3",
            ]
        ]
    ).to_csv(results / "thesis_method_interpretation_traceability.csv", index=False)

    pd.DataFrame(
        [
            _agent_row(
                "agent_control_01",
                "Evidence-to-prose drafting",
                "future_documentation_only",
            ),
            _agent_row(
                "agent_control_02",
                "Bounded MCP summary interface",
                "future_deferred",
            ),
        ]
    ).to_csv(results / "thesis_agent_pipeline_control_audit.csv", index=False)


def _evidence_row(
    evidence_id: str,
    area: str,
    item_type: str,
    primary: str,
    supporting: str,
    sources: str,
    blocked: str,
    limitation: str,
) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "thesis_area": area,
        "item_type": item_type,
        "claim_or_decision": "Fixture claim",
        "primary_artifact": primary,
        "supporting_artifacts": supporting,
        "literature_sources": sources,
        "allowed_wording": "bounded fixture wording",
        "blocked_wording": blocked,
        "main_limitation": limitation,
        "thesis_readiness": "thesis_facing_ready",
    }


def _core_result(
    result_id: str,
    area: str,
    key_value: str,
    evidence_ids: str,
    primary: str,
    supporting: str,
) -> dict[str, str]:
    return {
        "result_id": result_id,
        "thesis_area": area,
        "recommended_table": "Fixture table",
        "headline_result": "Fixture headline",
        "key_value": key_value,
        "primary_artifact": primary,
        "supporting_artifacts": supporting,
        "evidence_ids": evidence_ids,
        "bounded_interpretation": "Fixture bounded interpretation",
        "main_limitation": f"{area} result limitation",
        "thesis_readiness": "thesis_facing_ready",
    }


def _package_row(
    package_id: str,
    package_type: str,
    area: str,
    primary: str,
    supporting: str,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "package_type": package_type,
        "thesis_section": area,
        "title": "Fixture package",
        "primary_artifact": primary,
        "supporting_artifacts": supporting,
        "evidence_ids": "method_h1; interpretation_h1",
        "recommended_placement": "main_text",
        "include_in_core_package": True,
        "thesis_message": "Fixture package message",
        "main_limitation": "Fixture package limitation",
        "thesis_readiness": "thesis_facing_ready",
    }


def _caption_row(package_id: str) -> dict[str, str]:
    return {
        "package_id": package_id,
        "package_type": "table",
        "thesis_label": f"label:{package_id.lower()}",
        "caption_de": f"Caption {package_id}",
        "source_note_de": "Source note",
        "interpretation_note_de": "Interpretation note",
        "limitation_note_de": f"Limitation note {package_id}",
        "primary_artifact": "data/results/h1_result.csv",
        "supporting_artifacts": "data/results/h1_support.csv",
        "evidence_ids": "method_h1",
        "recommended_placement": "main_text",
        "include_in_core_package": True,
        "thesis_readiness": "thesis_facing_ready",
    }


def _agent_row(control_id: str, role: str, status: str) -> dict[str, str]:
    return {
        "control_id": control_id,
        "protocol_id": control_id.replace("control", "protocol"),
        "future_assistance_role": role,
        "current_activation_state": status,
        "pipeline_improvement_de": "Fixture improvement",
        "allowed_input_boundary": "Nur bounded inputs, max 50 rows by default; kein Rohdaten-Prompt.",
        "allowed_output_boundary": "Nur bounded outputs, max 50 rows by default; kein Rohdaten-Prompt.",
        "mandatory_audit_gate": "separates genehmigtes Goal, Tests, bounded inputs und llm_audit_log.",
        "blocked_actions_de": (
            "Blockiert: keine Runtime-Agenten, kein MCP, kein Model Routing, "
            "keine LLM-Metriken, keine Rohdaten-Prompts, keine Wallet-Adress-Exposition "
            "by default und keine Trading-Pfade."
        ),
        "required_preconditions_de": "Vor Aktivierung: separates genehmigtes Goal und llm_audit_log.",
        "current_decision_de": "Bleibt documentation-only.",
        "next_safe_step_de": "Nur Spezifikation schreiben.",
    }
