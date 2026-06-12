from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_agent_pipeline_control_audit import (
    CONTROL_COLUMNS,
    generate_agent_pipeline_control_audit,
)


def test_generate_agent_pipeline_control_audit_writes_guarded_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_pipeline_control_audit(repo_root=tmp_path)

    control = pd.read_csv(result.control_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(control.columns) == CONTROL_COLUMNS
    assert result.control_rows == 2
    assert result.documentation_only_rows == 1
    assert result.deferred_rows == 1
    assert result.active_rows == 0
    assert "Thesis Agent Pipeline Control Audit" in doc
    assert "Active rows: 0" in doc
    assert "keine Runtime-Agenten" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_agent_pipeline_control_audit_preserves_activation_barriers(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_agent_pipeline_control_audit(repo_root=tmp_path)

    control = pd.read_csv(result.control_path)
    joined = "\n".join(control.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert set(control["current_activation_state"]) == {
        "future_documentation_only",
        "future_deferred",
    }
    assert "separates genehmigtes goal" in joined
    assert "llm_audit_log" in joined
    assert "max 50 rows" in joined
    assert "keine runtime-agenten" in joined
    assert "kein mcp" in joined
    assert "kein model routing" in joined
    assert "keine llm-metriken" in joined
    assert "kein roh" in joined
    assert "keine trading-pfade" in joined
    assert "deferred_future_work_only" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "protocol_id": "agent_protocol_01_source_review",
                "pipeline_step": "Manual source review",
                "current_artifact_boundary": "source_review.csv",
                "future_agent_help": "Prepare missing page-note checklist.",
                "allowed_inputs": "source_id; evidence_id",
                "allowed_outputs": "bounded checklist",
                "audit_gate": "llm_audit_log entry with source_ids and prompt hash",
                "blocked_behaviour": "promoting source status",
                "activation_status": "future_documentation_only",
                "thesis_value": "Keeps citation approval human-owned.",
            },
            {
                "protocol_id": "agent_protocol_07_bounded_mcp",
                "pipeline_step": "Bounded MCP summary interface",
                "current_artifact_boundary": "reviewed summaries only",
                "future_agent_help": "Expose reviewed summaries.",
                "allowed_inputs": "reviewed summary artifacts",
                "allowed_outputs": "bounded read-only summaries",
                "audit_gate": "separate approved goal and llm_audit_log integration",
                "blocked_behaviour": "raw table access; SELECT star",
                "activation_status": "future_deferred",
                "thesis_value": "Provides later safe interface.",
            },
        ]
    ).to_csv(results / "thesis_agent_assistance_protocol.csv", index=False)
    pd.DataFrame(
        [
            {
                "handoff_id": "agent_handoff_01",
                "protocol_id": "agent_protocol_01_source_review",
                "future_assistance_role": "Manual source review",
                "current_pipeline_gap_de": "Quellen brauchen Page Notes.",
                "allowed_inputs": "source_id; evidence_id",
                "allowed_outputs": "bounded checklist",
                "activation_gate_de": "separates genehmigtes Goal, bounded inputs, Tests, und llm_audit_log.",
                "blocked_actions_de": "Blockiert: Quellenstatus automatisch hochstufen.",
                "status": "future_documentation_only",
            },
            {
                "handoff_id": "agent_handoff_07",
                "protocol_id": "agent_protocol_07_bounded_mcp",
                "future_assistance_role": "Bounded MCP summary interface",
                "current_pipeline_gap_de": "Tool-Interface braucht Access-Contracts.",
                "allowed_inputs": "reviewed summary artifacts",
                "allowed_outputs": "bounded read-only summaries",
                "activation_gate_de": "separates genehmigtes Goal, bounded inputs, Tests, und llm_audit_log.",
                "blocked_actions_de": "Blockiert: Rohdatenzugriff und SELECT star.",
                "status": "future_deferred",
            },
        ]
    ).to_csv(results / "thesis_agent_future_work_handoff.csv", index=False)
    pd.DataFrame(
        [
            {
                "gate_area": "agent_future_work",
                "current_status": "deferred_future_work_only",
            }
        ]
    ).to_csv(results / "thesis_submission_readiness_board.csv", index=False)
