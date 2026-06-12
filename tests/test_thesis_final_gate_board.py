from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_thesis_final_gate_board import (
    FINAL_GATE_COLUMNS,
    generate_thesis_final_gate_board,
)


def test_generate_thesis_final_gate_board_writes_highlevel_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_final_gate_board(repo_root=tmp_path)

    board = pd.read_csv(result.board_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(board.columns) == FINAL_GATE_COLUMNS
    assert result.board_rows == 8
    assert result.draft_allowed_rows == 8
    assert result.final_ready_rows == 1
    assert result.final_not_ready_rows == 7
    assert result.active_agent_rows == 0
    assert "Thesis Final Gate Board" in doc
    assert "Final gate rows: 8" in doc
    assert "Draft allowed rows: 8" in doc
    assert "Final ready rows: 1" in doc
    assert "Final not ready rows: 7" in doc
    assert "Keine finale Zitation" in doc
    assert "keine Rohartefakt-Dumps" in doc
    assert "keine Runtime-Agenten" in doc
    assert "llm_audit_log" in doc
    assert chr(223) not in doc


def test_thesis_final_gate_board_keeps_final_blockers_visible(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_thesis_final_gate_board(repo_root=tmp_path)

    board = pd.read_csv(result.board_path)
    rows = {row["final_gate_id"]: row for row in board.to_dict(orient="records")}

    assert not bool(rows["final_gate_01_source_review"]["final_submission_ready"])
    assert rows["final_gate_01_source_review"]["evidence_count"] == 3
    assert rows["final_gate_01_source_review"]["blocking_count"] == 3
    assert not bool(rows["final_gate_04_swiss_result_mapping"]["final_submission_ready"])
    assert rows["final_gate_04_swiss_result_mapping"]["evidence_count"] == 4
    assert not bool(rows["final_gate_07_docx_render_qa"]["final_submission_ready"])
    assert bool(rows["final_gate_06_future_agents"]["final_submission_ready"])


def test_thesis_final_gate_board_rejects_active_runtime_agent_rows(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    pd.DataFrame([{"upgrade_id": "agent_upgrade_01", "current_status": "active_runtime_agent"}]).to_csv(
        tmp_path / "data/results/thesis_agent_pipeline_upgrade_plan.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="must not activate runtime agents"):
        generate_thesis_final_gate_board(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs_project = root / "docs/project"
    docs_research = root / "docs/research"
    results.mkdir(parents=True)
    docs_project.mkdir(parents=True)
    docs_research.mkdir(parents=True)

    pd.DataFrame(
        [
            {"gate_area": "swiss_result_gate", "current_status": "final_blocked_official_result"},
            {"gate_area": "monitor_appendix", "current_status": "appendix_only_pending_human_review"},
            {"gate_area": "agent_future_work", "current_status": "deferred_future_work_only"},
            {"gate_area": "final_qa", "current_status": "pending_after_draft"},
        ]
    ).to_csv(results / "thesis_submission_readiness_board.csv", index=False)

    pd.DataFrame([_ledger_row(idx) for idx in range(3)]).to_csv(
        results / "thesis_source_review_progress_ledger.csv",
        index=False,
    )
    pd.DataFrame(
        [_drafting_row(idx, is_final_gate=(idx % 6 == 4)) for idx in range(18)]
    ).to_csv(results / "thesis_h1_h2_h3_drafting_checklist.csv", index=False)
    pd.DataFrame(
        [{"package_type": "table", "include_in_core_package": True, "package_traceability_status": "ready"} for _ in range(5)]
        + [{"package_type": "figure", "include_in_core_package": True, "package_traceability_status": "ready"} for _ in range(4)]
        + [{"package_type": "appendix", "include_in_core_package": False, "package_traceability_status": "ready"}]
    ).to_csv(results / "thesis_result_package_traceability.csv", index=False)
    pd.DataFrame(
        [
            {
                "polymarket_snapshot_at_utc": "2026-06-12T07:04:17Z",
                "polymarket_yes_probability": 0.22,
                "valuation_scope": "descriptive_latest_source_poll_proxy_not_true_mispricing_or_trade_signal",
            },
            {
                "polymarket_snapshot_at_utc": "2026-06-12T07:04:17Z",
                "polymarket_yes_probability": 0.22,
                "valuation_scope": "descriptive_latest_source_poll_proxy_not_true_mispricing_or_trade_signal",
            },
        ]
    ).to_csv(results / "swiss_referendum_10mio_latest_source_comparison.csv", index=False)
    (results / "swiss_referendum_10mio_running_status.json").write_text(
        json.dumps(
            {
                "status": {
                    "snapshot_row_count": 4,
                    "snapshot_recency_status": "fresh",
                }
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"upgrade_id": "agent_upgrade_01", "current_status": "future_documentation_only"},
            {"upgrade_id": "agent_upgrade_02", "current_status": "future_deferred"},
        ]
    ).to_csv(results / "thesis_agent_pipeline_upgrade_plan.csv", index=False)

    for relative in [
        "STATUS.md",
        "docs/project/WORK_LOG.md",
        "docs/project/dozentenbericht_ba_thesis.docx",
        "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md",
        "docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md",
        "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
        "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md",
        "data/results/monitor_anomaly_review_summary.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def _ledger_row(idx: int) -> dict[str, object]:
    return {
        "review_progress_state": "pending_manual_review",
        "final_citation_ready": False,
        "source_status_change_allowed": False,
    }


def _drafting_row(idx: int, *, is_final_gate: bool) -> dict[str, object]:
    return {
        "completion_status": (
            "final_blocked_source_review_pending" if is_final_gate else "bounded_draft_ready"
        ),
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": False,
    }
