from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from operations.project.build_h1_h2_h3_worksheet_drafting_bridge import (
    BRIDGE_COLUMNS,
    generate_h1_h2_h3_worksheet_drafting_bridge,
)


def test_generate_h1_h2_h3_worksheet_drafting_bridge_writes_control_rows(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_worksheet_drafting_bridge(repo_root=tmp_path)

    bridge = pd.read_csv(result.bridge_path)
    doc = result.docs_path.read_text(encoding="utf-8")

    assert tuple(bridge.columns) == BRIDGE_COLUMNS
    assert result.bridge_rows == 4
    assert result.worksheet_rows == 23
    assert result.drafting_steps == 15
    assert result.source_artifact_gap_rows == 0
    assert result.final_release_ready_rows == 0
    assert bridge["bridge_order"].tolist() == [1, 2, 3, 4]
    assert bridge["thesis_area"].tolist() == ["H1", "H2", "H3", "TOTAL"]
    assert bridge["worksheet_rows"].tolist() == [10, 5, 8, 23]
    assert bridge["method_rows"].tolist() == [4, 3, 5, 12]
    assert bridge["interpretation_rows"].tolist() == [6, 2, 3, 11]
    assert bridge["unique_sources"].tolist() == [4, 3, 4, 9]
    assert bridge["pending_citation_rows"].tolist() == [10, 5, 8, 23]
    assert bridge["drafting_steps"].tolist() == [5, 5, 5, 15]
    assert bridge["bounded_draft_ready_steps"].tolist() == [5, 5, 5, 15]
    assert bridge["final_submission_ready_steps"].tolist() == [0, 0, 0, 0]
    assert bridge["selected_tables"].tolist() == ["T2", "T3", "T4", "T2, T3, T4"]
    assert bridge["selected_figures"].tolist() == ["F1", "F2", "F3", "F1, F2, F3"]
    assert bridge["ready_for_bounded_drafting"].map(_as_bool).all()
    assert not bridge["ready_for_final_release"].map(_as_bool).any()
    assert "H1-H2-H3 Worksheet Drafting Bridge" in doc
    assert "Worksheet rows: 23" in doc
    assert "Drafting steps: 15" in doc
    assert "Final release ready rows: 0" in doc
    assert chr(223) not in doc


def test_worksheet_drafting_bridge_keeps_source_artifact_boundaries(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)

    result = generate_h1_h2_h3_worksheet_drafting_bridge(repo_root=tmp_path)

    bridge = pd.read_csv(result.bridge_path)
    doc = result.docs_path.read_text(encoding="utf-8")
    joined = "\n".join(bridge.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    control_text = f"{joined}\n{doc}"

    assert "Jede Methode" in control_text
    assert "jede Interpretation" in control_text
    assert "Source ID" in control_text
    assert "Evidence ID" in control_text
    assert "deterministisches Artefakt" in control_text
    assert "wenige gute Tabellen" in control_text
    assert "Page-/Section-Note" in control_text
    assert "Claim-Support" in control_text
    assert "Blocked-Wording" in control_text
    assert "Citation-Use" in control_text
    assert "Keine finale Zitation" in control_text
    assert "keine Quellenstatus-Hochstufung" in control_text
    assert "keine Runtime-Agenten" in control_text
    assert "llm_audit_log" in control_text
    assert "max 50 rows" in control_text


def test_worksheet_drafting_bridge_rejects_missing_artifact_mapping(
    tmp_path: Path,
) -> None:
    _write_fixture(tmp_path)
    h2_path = tmp_path / "data/results/thesis_h2_source_review_batch_worksheet.csv"
    h2 = pd.read_csv(h2_path)
    h2.loc[0, "deterministic_artifact"] = ""
    h2.to_csv(h2_path, index=False)

    with pytest.raises(ValueError, match="source and artifact coverage"):
        generate_h1_h2_h3_worksheet_drafting_bridge(repo_root=tmp_path)


def _write_fixture(root: Path) -> None:
    results = root / "data/results"
    results.mkdir(parents=True)

    artifact_paths = [
        "data/results/h1.csv",
        "data/results/h2.csv",
        "data/results/h3.csv",
    ]
    for relative in artifact_paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    _write_worksheet(
        results / "thesis_h1_source_review_batch_worksheet.csv",
        "H1",
        "T2",
        "F1",
        "data/results/h1.csv",
        [
            ("lit_brier_001", "method", "method_h1_brier_dm"),
            ("lit_brier_001", "interpretation", "interpretation_h1_bounded_advantage"),
            ("lit_brier_001", "interpretation", "interpretation_h1_broad_claim_not_proven"),
            ("lit_dm_001", "method", "method_h1_brier_dm"),
            ("lit_dm_001", "interpretation", "interpretation_h1_bounded_advantage"),
            ("lit_emh_001", "method", "method_h1_brier_dm"),
            ("lit_emh_001", "interpretation", "interpretation_h1_broad_claim_not_proven"),
            ("zotero_poly_002", "method", "method_h1_brier_dm"),
            ("zotero_poly_002", "interpretation", "interpretation_h1_bounded_advantage"),
            ("zotero_poly_002", "interpretation", "interpretation_h1_broad_claim_not_proven"),
        ],
    )
    _write_worksheet(
        results / "thesis_h2_source_review_batch_worksheet.csv",
        "H2",
        "T3",
        "F2",
        "data/results/h2.csv",
        [
            ("lit_emh_001", "method", "method_h2_event_window"),
            ("lit_emh_001", "interpretation", "interpretation_h2_daily_response"),
            ("lit_eventstudy_001", "method", "method_h2_event_window"),
            ("lit_eventstudy_001", "interpretation", "interpretation_h2_daily_response"),
            ("zotero_poly_001", "method", "method_h2_event_window"),
        ],
    )
    _write_worksheet(
        results / "thesis_h3_source_review_batch_worksheet.csv",
        "H3",
        "T4",
        "F3",
        "data/results/h3.csv",
        [
            ("lit_granger_001", "method", "method_h3_granger_timing"),
            ("lit_granger_001", "interpretation", "interpretation_h3_top_tier_signal"),
            ("zotero_poly_001", "method", "method_h3_wallet_tiers"),
            ("zotero_poly_001", "interpretation", "interpretation_h3_top_tier_signal"),
            ("zotero_poly_005", "method", "method_h3_wallet_tiers"),
            ("zotero_poly_005", "method", "method_h3_granger_timing"),
            ("zotero_poly_005", "interpretation", "interpretation_h3_top_tier_signal"),
            ("zotero_poly_007", "method", "method_h3_wallet_tiers"),
        ],
    )
    _write_drafting_pass(results / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv")
    _write_core_sections(results / "thesis_h1_h2_h3_core_sections.csv")
    _write_overview(results / "thesis_source_review_worksheet_overview.csv")


def _write_worksheet(
    path: Path,
    thesis_area: str,
    selected_table: str,
    selected_figure: str,
    artifact: str,
    rows: list[tuple[str, str, str]],
) -> None:
    pd.DataFrame(
        [
            {
                "worksheet_id": f"{thesis_area.lower()}_{index}",
                "thesis_area": thesis_area,
                "source_id": source_id,
                "evidence_id": evidence_id,
                "item_type": item_type,
                "deterministic_artifact": artifact,
                "selected_table": selected_table,
                "selected_figure": selected_figure,
                "current_citation_use_decision": "blocked_pending_manual_review",
                "required_manual_fields_de": (
                    "Page-/Section-Note; Claim-Support; Blocked-Wording; "
                    "Citation-Use; reviewed_by; reviewed_at; review_comment_de"
                ),
                "ready_for_manual_entry": True,
                "ready_for_final_release": False,
            }
            for index, (source_id, item_type, evidence_id) in enumerate(rows, start=1)
        ]
    ).to_csv(path, index=False)


def _write_drafting_pass(path: Path) -> None:
    rows = []
    for area in ("H1", "H2", "H3"):
        for index in range(1, 6):
            rows.append(
                {
                    "drafting_pass_id": f"draft_{area.lower()}_{index}",
                    "thesis_area": area,
                    "chapter_title_de": f"{area}: Kapitel",
                    "draft_sequence_order": len(rows) + 1,
                    "ready_for_bounded_draft": True,
                    "ready_for_final_submission": False,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_core_sections(path: Path) -> None:
    pd.DataFrame(
        [
            _core("H1", "H1: Prognosequalitaet", "method_h1_brier_dm", "interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven", "lit_brier_001; lit_dm_001; lit_emh_001; zotero_poly_002", "data/results/h1.csv", "T2", "F1"),
            _core("H2", "H2: Tagesbasierte Ereignisfenster", "method_h2_event_window", "interpretation_h2_daily_response", "lit_eventstudy_001; lit_emh_001; zotero_poly_001", "data/results/h2.csv", "T3", "F2"),
            _core("H3", "H3: Wallet-Timing-Diagnostik", "method_h3_wallet_tiers; method_h3_granger_timing", "interpretation_h3_top_tier_signal", "zotero_poly_001; zotero_poly_005; zotero_poly_007; lit_granger_001", "data/results/h3.csv", "T4", "F3"),
        ]
    ).to_csv(path, index=False)


def _core(
    hypothesis: str,
    chapter_title: str,
    methods: str,
    interpretations: str,
    sources: str,
    artifacts: str,
    tables: str,
    figures: str,
) -> dict[str, object]:
    return {
        "hypothesis": hypothesis,
        "chapter_title_de": chapter_title,
        "method_evidence_ids": methods,
        "interpretation_evidence_ids": interpretations,
        "literature_source_ids": sources,
        "deterministic_artifacts": artifacts,
        "selected_tables": tables,
        "selected_figures": figures,
        "source_review_gate_de": "Draft ja; finale Zitation nach Source Review.",
    }


def _write_overview(path: Path) -> None:
    pd.DataFrame(
        [
            _overview("H1", 10, 4, 4, 6, 10, 0, "T2", "F1"),
            _overview("H2", 5, 3, 3, 2, 5, 0, "T3", "F2"),
            _overview("H3", 8, 4, 5, 3, 8, 0, "T4", "F3"),
            _overview("TOTAL", 23, 9, 12, 11, 23, 0, "T2, T3, T4", "F1, F2, F3"),
        ]
    ).to_csv(path, index=False)


def _overview(
    area: str,
    worksheet_rows: int,
    unique_sources: int,
    method_rows: int,
    interpretation_rows: int,
    pending_rows: int,
    final_rows: int,
    tables: str,
    figures: str,
) -> dict[str, object]:
    return {
        "thesis_area": area,
        "worksheet_rows": worksheet_rows,
        "unique_sources": unique_sources,
        "method_rows": method_rows,
        "interpretation_rows": interpretation_rows,
        "pending_citation_rows": pending_rows,
        "final_release_ready_rows": final_rows,
        "selected_tables": tables,
        "selected_figures": figures,
    }


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
