from __future__ import annotations

from pathlib import Path

import pandas as pd

from operations.project.build_source_review_execution_guide import (
    EXECUTION_COLUMNS,
    generate_source_review_execution_guide,
)


def test_generate_source_review_execution_guide_writes_manual_tasks(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_execution_guide(repo_root=tmp_path)

    guide = pd.read_csv(result.guide_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(guide.columns) == EXECUTION_COLUMNS
    assert result.guide_rows == 3
    assert guide["review_stage"].tolist() == [
        "review_now_priority_1",
        "metadata_only_blocked",
        "defer_until_mapped",
    ]
    assert "Thesis Source Review Execution" in doc
    assert "Review now priority 1: 1" in doc
    assert chr(223) not in doc


def test_source_review_execution_guide_keeps_manual_review_gates(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = generate_source_review_execution_guide(repo_root=tmp_path)

    guide = pd.read_csv(result.guide_path)
    joined = "\n".join(guide.fillna("").astype(str).agg(" ".join, axis=1).tolist()).lower()

    assert "quellenstatus-hochstufung" in joined
    assert "human review" in joined
    assert "nicht fuer thesis-facing claims" in joined
    assert "keine kausalclaims" in joined
    assert "offiziellen resultat" in joined


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    docs = root / "docs/project"
    results.mkdir(parents=True)
    docs.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "source_id": "src_priority",
                "priority_order": 1,
                "source_title": "Priority Source",
                "priority_band": "priority_1_method_foundation_review",
                "thesis_area_focus": "H1; H3; swiss_referendum",
                "local_file_registered": True,
                "review_source_locator": "https://example.test/priority",
                "reviewer_decision": "pending",
            },
            {
                "source_id": "src_blocked",
                "priority_order": 2,
                "source_title": "Blocked Source",
                "priority_band": "blocked_or_future_work_only",
                "thesis_area_focus": "future_agents",
                "local_file_registered": False,
                "review_source_locator": "not_verified",
                "reviewer_decision": "pending",
            },
            {
                "source_id": "src_defer",
                "priority_order": 3,
                "source_title": "Deferred Source",
                "priority_band": "not_currently_needed",
                "thesis_area_focus": "not_currently_mapped",
                "local_file_registered": True,
                "review_source_locator": "https://example.test/defer",
                "reviewer_decision": "pending",
            },
        ]
    ).to_csv(results / "thesis_source_review_worksheet.csv", index=False)

    pd.DataFrame(
        [
            {
                "source_id": "src_priority",
                "item_type": "method",
                "evidence_id": "method_h1_brier_dm",
                "final_citation_gate": "full_source_review_required_before_final_citation",
            },
            {
                "source_id": "src_priority",
                "item_type": "interpretation",
                "evidence_id": "interpretation_h3_top_tier_signal",
                "final_citation_gate": "full_source_review_required_before_final_citation",
            },
            {
                "source_id": "src_blocked",
                "item_type": "future_work",
                "evidence_id": "future_agent_pipeline_guarded",
                "final_citation_gate": "not_allowed_for_thesis_facing_claims",
            },
        ]
    ).to_csv(results / "thesis_citation_review_packets.csv", index=False)
