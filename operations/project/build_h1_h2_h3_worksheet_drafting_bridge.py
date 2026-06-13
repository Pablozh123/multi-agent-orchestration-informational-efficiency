"""Build the H1-H2-H3 bridge from source-review worksheets to drafting."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/project")

BRIDGE_OUTPUT = "thesis_h1_h2_h3_worksheet_drafting_bridge.csv"
BRIDGE_DOC_OUTPUT = "THESIS_H1_H2_H3_WORKSHEET_DRAFTING_BRIDGE.md"

BRIDGE_COLUMNS: tuple[str, ...] = (
    "bridge_id",
    "bridge_order",
    "thesis_area",
    "chapter_title_de",
    "worksheet_artifact",
    "worksheet_rows",
    "method_rows",
    "interpretation_rows",
    "unique_sources",
    "method_interpretation_source_artifact_gap_rows",
    "pending_citation_rows",
    "final_release_ready_rows",
    "drafting_steps",
    "bounded_draft_ready_steps",
    "final_submission_ready_steps",
    "unique_method_evidence_ids",
    "unique_interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "compact_result_package_de",
    "required_manual_fields_de",
    "source_artifact_rule_de",
    "writing_bridge_action_de",
    "final_blocker_de",
    "future_agent_boundary_de",
    "ready_for_bounded_drafting",
    "ready_for_final_release",
)

WORKSHEET_REQUIRED_COLUMNS: tuple[str, ...] = (
    "worksheet_id",
    "thesis_area",
    "source_id",
    "evidence_id",
    "item_type",
    "deterministic_artifact",
    "selected_table",
    "selected_figure",
    "current_citation_use_decision",
    "required_manual_fields_de",
    "ready_for_manual_entry",
    "ready_for_final_release",
)

DRAFTING_REQUIRED_COLUMNS: tuple[str, ...] = (
    "drafting_pass_id",
    "thesis_area",
    "chapter_title_de",
    "draft_sequence_order",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
)

CORE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "hypothesis",
    "chapter_title_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "source_review_gate_de",
)

OVERVIEW_REQUIRED_COLUMNS: tuple[str, ...] = (
    "thesis_area",
    "worksheet_rows",
    "unique_sources",
    "method_rows",
    "interpretation_rows",
    "pending_citation_rows",
    "final_release_ready_rows",
    "selected_tables",
    "selected_figures",
)

AREA_INPUTS: tuple[tuple[str, str], ...] = (
    ("H1", "data/results/thesis_h1_source_review_batch_worksheet.csv"),
    ("H2", "data/results/thesis_h2_source_review_batch_worksheet.csv"),
    ("H3", "data/results/thesis_h3_source_review_batch_worksheet.csv"),
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")


@dataclass(frozen=True)
class H1H2H3WorksheetDraftingBridgeResult:
    """Generated worksheet-to-drafting bridge paths and counts."""

    bridge_path: Path
    docs_path: Path
    bridge_rows: int
    worksheet_rows: int
    drafting_steps: int
    source_artifact_gap_rows: int
    final_release_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "bridge_path": str(self.bridge_path),
            "docs_path": str(self.docs_path),
            "bridge_rows": self.bridge_rows,
            "worksheet_rows": self.worksheet_rows,
            "drafting_steps": self.drafting_steps,
            "source_artifact_gap_rows": self.source_artifact_gap_rows,
            "final_release_ready_rows": self.final_release_ready_rows,
        }


def generate_h1_h2_h3_worksheet_drafting_bridge(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3WorksheetDraftingBridgeResult:
    """Generate the worksheet-to-drafting bridge CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    worksheets = {
        area: _read_csv(_resolve_under(repo_root, Path(path)))
        for area, path in AREA_INPUTS
    }
    drafting_pass = _read_csv(results_dir / "thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    worksheet_overview = _read_csv(results_dir / "thesis_source_review_worksheet_overview.csv")

    bridge = build_h1_h2_h3_worksheet_drafting_bridge(
        worksheets=worksheets,
        drafting_pass=drafting_pass,
        core_sections=core_sections,
        worksheet_overview=worksheet_overview,
    )
    _validate_bridge(bridge=bridge, worksheets=worksheets, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    bridge_path = results_dir / BRIDGE_OUTPUT
    docs_path = docs_dir / BRIDGE_DOC_OUTPUT
    bridge.to_csv(bridge_path, index=False)
    docs_path.write_text(_render_bridge_doc(bridge), encoding="utf-8")

    total = _bridge_row(bridge, "TOTAL")
    return H1H2H3WorksheetDraftingBridgeResult(
        bridge_path=bridge_path,
        docs_path=docs_path,
        bridge_rows=len(bridge),
        worksheet_rows=int(total["worksheet_rows"]),
        drafting_steps=int(total["drafting_steps"]),
        source_artifact_gap_rows=int(total["method_interpretation_source_artifact_gap_rows"]),
        final_release_ready_rows=int(total["final_release_ready_rows"]),
    )


def build_h1_h2_h3_worksheet_drafting_bridge(
    *,
    worksheets: dict[str, pd.DataFrame],
    drafting_pass: pd.DataFrame,
    core_sections: pd.DataFrame,
    worksheet_overview: pd.DataFrame,
) -> pd.DataFrame:
    """Return one bridge row for H1, H2, H3, and TOTAL."""

    _require_columns(drafting_pass, DRAFTING_REQUIRED_COLUMNS, "source-gated thesis drafting pass")
    _require_columns(core_sections, CORE_REQUIRED_COLUMNS, "H1-H2-H3 core sections")
    _require_columns(worksheet_overview, OVERVIEW_REQUIRED_COLUMNS, "source-review worksheet overview")

    rows: list[dict[str, object]] = []
    ordered_worksheets: list[pd.DataFrame] = []
    for order, (area, worksheet_artifact) in enumerate(AREA_INPUTS, start=1):
        worksheet = worksheets.get(area)
        if worksheet is None:
            raise ValueError(f"Missing worksheet input for {area}.")
        _require_columns(worksheet, WORKSHEET_REQUIRED_COLUMNS, f"{area} worksheet")
        area_rows = worksheet.loc[worksheet["thesis_area"].astype(str) == area].copy()
        if len(area_rows) != len(worksheet):
            raise ValueError(f"{area} worksheet contains rows from another thesis area.")
        ordered_worksheets.append(area_rows)
        rows.append(
            _row(
                bridge_id=f"worksheet_drafting_bridge_{area.lower()}",
                bridge_order=order,
                thesis_area=area,
                worksheet_artifact=worksheet_artifact,
                worksheet=area_rows,
                drafting=_drafting_rows(drafting_pass, area),
                core=_core_row(core_sections, area),
                overview=_overview_row(worksheet_overview, area),
            )
        )

    total_worksheet = pd.concat(ordered_worksheets, ignore_index=True)
    rows.append(
        _row(
            bridge_id="worksheet_drafting_bridge_total",
            bridge_order=4,
            thesis_area="TOTAL",
            worksheet_artifact="; ".join(path for _area, path in AREA_INPUTS),
            worksheet=total_worksheet,
            drafting=drafting_pass.loc[drafting_pass["thesis_area"].astype(str).isin(CORE_AREAS)].copy(),
            core=core_sections.loc[core_sections["hypothesis"].astype(str).isin(CORE_AREAS)].copy(),
            overview=_overview_row(worksheet_overview, "TOTAL"),
        )
    )
    return pd.DataFrame(rows, columns=BRIDGE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_worksheet_drafting_bridge(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _row(
    *,
    bridge_id: str,
    bridge_order: int,
    thesis_area: str,
    worksheet_artifact: str,
    worksheet: pd.DataFrame,
    drafting: pd.DataFrame,
    core: pd.Series | pd.DataFrame,
    overview: pd.Series,
) -> dict[str, object]:
    method_interpretation = worksheet.loc[
        worksheet["item_type"].astype(str).isin(("method", "interpretation"))
    ].copy()
    gap_rows = method_interpretation[
        method_interpretation[["source_id", "evidence_id", "deterministic_artifact"]]
        .apply(lambda row: any(not _clean(value) for value in row), axis=1)
    ]
    method_evidence = _join_unique(
        method_interpretation.loc[
            method_interpretation["item_type"].astype(str) == "method", "evidence_id"
        ]
    )
    interpretation_evidence = _join_unique(
        method_interpretation.loc[
            method_interpretation["item_type"].astype(str) == "interpretation", "evidence_id"
        ]
    )
    core_frame = core if isinstance(core, pd.DataFrame) else pd.DataFrame([core])
    chapter_title = (
        "H1-H2-H3 empirischer Kern"
        if thesis_area == "TOTAL"
        else _first_clean(core_frame["chapter_title_de"])
    )
    selected_tables = _join_unique(worksheet["selected_table"])
    selected_figures = _join_unique(worksheet["selected_figure"])
    drafting_steps = int(len(drafting))
    bounded_steps = int(drafting["ready_for_bounded_draft"].map(_bool_value).sum())
    final_steps = int(drafting["ready_for_final_submission"].map(_bool_value).sum())
    _assert_overview_alignment(
        thesis_area=thesis_area,
        overview=overview,
        worksheet_rows=len(worksheet),
        method_rows=int((worksheet["item_type"].astype(str) == "method").sum()),
        interpretation_rows=int((worksheet["item_type"].astype(str) == "interpretation").sum()),
        unique_sources=int(worksheet["source_id"].astype(str).nunique()),
        pending_citation_rows=int(
            (
                worksheet["current_citation_use_decision"].astype(str)
                == "blocked_pending_manual_review"
            ).sum()
        ),
        final_release_ready_rows=int(worksheet["ready_for_final_release"].map(_bool_value).sum()),
        selected_tables=selected_tables,
        selected_figures=selected_figures,
    )

    return {
        "bridge_id": bridge_id,
        "bridge_order": bridge_order,
        "thesis_area": thesis_area,
        "chapter_title_de": chapter_title,
        "worksheet_artifact": worksheet_artifact,
        "worksheet_rows": int(len(worksheet)),
        "method_rows": int((worksheet["item_type"].astype(str) == "method").sum()),
        "interpretation_rows": int((worksheet["item_type"].astype(str) == "interpretation").sum()),
        "unique_sources": int(worksheet["source_id"].astype(str).nunique()),
        "method_interpretation_source_artifact_gap_rows": int(len(gap_rows)),
        "pending_citation_rows": int(
            (
                worksheet["current_citation_use_decision"].astype(str)
                == "blocked_pending_manual_review"
            ).sum()
        ),
        "final_release_ready_rows": int(worksheet["ready_for_final_release"].map(_bool_value).sum()),
        "drafting_steps": drafting_steps,
        "bounded_draft_ready_steps": bounded_steps,
        "final_submission_ready_steps": final_steps,
        "unique_method_evidence_ids": method_evidence,
        "unique_interpretation_evidence_ids": interpretation_evidence,
        "literature_source_ids": _join_unique(worksheet["source_id"]),
        "deterministic_artifacts": _join_unique_from_semicolon(core_frame["deterministic_artifacts"]),
        "selected_tables": selected_tables,
        "selected_figures": selected_figures,
        "compact_result_package_de": _compact_result_package(
            thesis_area=thesis_area,
            selected_tables=selected_tables,
            selected_figures=selected_figures,
        ),
        "required_manual_fields_de": _join_unique(worksheet["required_manual_fields_de"]),
        "source_artifact_rule_de": (
            "Jede Methode und jede Interpretation muss eine Source ID, eine Evidence ID, "
            "ein deterministisches Artefakt, eine Limitation und ein Source-Review-Gate behalten. "
            "Keine finale Zitation und keine Quellenstatus-Hochstufung ohne vollstaendige "
            "manuelle Source Review."
        ),
        "writing_bridge_action_de": _writing_bridge_action(
            thesis_area=thesis_area,
            drafting_steps=drafting_steps,
            selected_tables=selected_tables,
            selected_figures=selected_figures,
        ),
        "final_blocker_de": _final_blocker(thesis_area),
        "future_agent_boundary_de": (
            "Agenten bleiben documentation-only Future Work: keine Runtime-Agenten, kein MCP, "
            "kein Model Routing, keine LLM-Metriken, keine Rohdatenprompts, max 50 rows "
            "und llm_audit_log vor jeder spaeteren Nutzung."
        ),
        "ready_for_bounded_drafting": bool(
            len(gap_rows) == 0
            and worksheet["ready_for_manual_entry"].map(_bool_value).all()
            and bounded_steps == drafting_steps
        ),
        "ready_for_final_release": False,
    }


def _validate_bridge(
    *,
    bridge: pd.DataFrame,
    worksheets: dict[str, pd.DataFrame],
    repo_root: Path,
) -> None:
    _require_columns(bridge, BRIDGE_COLUMNS, "H1-H2-H3 worksheet drafting bridge")
    if len(bridge) != 4:
        raise ValueError("Worksheet drafting bridge must contain 4 rows.")
    if bridge["bridge_order"].astype(int).tolist() != [1, 2, 3, 4]:
        raise ValueError("Worksheet drafting bridge order must be H1, H2, H3, TOTAL.")
    if bridge["bridge_id"].duplicated().any():
        raise ValueError("Worksheet drafting bridge contains duplicate IDs.")
    if int(bridge["method_interpretation_source_artifact_gap_rows"].astype(int).sum()) != 0:
        raise ValueError("Every method and interpretation needs source and artifact coverage.")
    if not bridge["ready_for_bounded_drafting"].map(_bool_value).all():
        raise ValueError("Worksheet drafting bridge must be bounded-drafting-ready.")
    if bridge["ready_for_final_release"].map(_bool_value).any():
        raise ValueError("Worksheet drafting bridge must not be final-release-ready.")
    if int(bridge["final_release_ready_rows"].astype(int).sum()) != 0:
        raise ValueError("Worksheet drafting bridge must not contain final-release rows.")

    for _area, artifact in AREA_INPUTS:
        if not (repo_root / artifact).exists():
            raise FileNotFoundError(f"Worksheet drafting bridge artifact missing: {artifact}")
    for artifact in (
        "data/results/thesis_h1_h2_h3_source_gated_thesis_drafting_pass.csv",
        "data/results/thesis_h1_h2_h3_core_sections.csv",
        "data/results/thesis_source_review_worksheet_overview.csv",
    ):
        if not (repo_root / artifact).exists():
            raise FileNotFoundError(f"Worksheet drafting bridge input missing: {artifact}")

    expected = {
        "H1": (10, 4, 6, 4, 10, 0, 5, 5, 0, "T2", "F1"),
        "H2": (5, 3, 2, 3, 5, 0, 5, 5, 0, "T3", "F2"),
        "H3": (8, 5, 3, 4, 8, 0, 5, 5, 0, "T4", "F3"),
        "TOTAL": (23, 12, 11, 9, 23, 0, 15, 15, 0, "T2, T3, T4", "F1, F2, F3"),
    }
    for area, expected_values in expected.items():
        row = _bridge_row(bridge, area)
        actual_values = (
            int(row["worksheet_rows"]),
            int(row["method_rows"]),
            int(row["interpretation_rows"]),
            int(row["unique_sources"]),
            int(row["pending_citation_rows"]),
            int(row["final_release_ready_rows"]),
            int(row["drafting_steps"]),
            int(row["bounded_draft_ready_steps"]),
            int(row["final_submission_ready_steps"]),
            str(row["selected_tables"]),
            str(row["selected_figures"]),
        )
        if actual_values != expected_values:
            raise ValueError(
                f"Unexpected worksheet drafting bridge counts for {area}: "
                f"{actual_values} != {expected_values}."
            )

    all_worksheets = pd.concat(list(worksheets.values()), ignore_index=True)
    _require_columns(all_worksheets, WORKSHEET_REQUIRED_COLUMNS, "all source-review worksheets")
    method_interpretation = all_worksheets.loc[
        all_worksheets["item_type"].astype(str).isin(("method", "interpretation"))
    ]
    for column in ("source_id", "evidence_id", "deterministic_artifact", "selected_table", "selected_figure"):
        if method_interpretation[column].map(_clean).eq("").any():
            raise ValueError(f"Every method and interpretation needs non-empty {column}.")

    joined = "\n".join(bridge.fillna("").astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Worksheet drafting bridge must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "jede methode",
        "jede interpretation",
        "source id",
        "evidence id",
        "deterministisches artefakt",
        "wenige gute tabellen",
        "page-/section-note",
        "claim-support",
        "blocked-wording",
        "citation-use",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "keine runtime-agenten",
        "llm_audit_log",
        "max 50 rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Worksheet drafting bridge missing required terms: " + ", ".join(missing))


def _render_bridge_doc(bridge: pd.DataFrame) -> str:
    total = _bridge_row(bridge, "TOTAL")
    display = bridge[
        [
            "bridge_order",
            "thesis_area",
            "worksheet_rows",
            "method_rows",
            "interpretation_rows",
            "unique_sources",
            "pending_citation_rows",
            "drafting_steps",
            "selected_tables",
            "selected_figures",
            "ready_for_final_release",
        ]
    ]
    return (
        "# H1-H2-H3 Worksheet Drafting Bridge\n\n"
        "Diese Bridge verbindet die H1-, H2- und H3-Source-Review-Worksheets "
        "mit der source-gated BA-Schreibsequenz. Sie liest keine Quelleninhalte, "
        "berechnet keine Kennzahlen, promotet keinen Quellenstatus und erzeugt "
        "keine finale Zitation. Zweck ist eine kompakte Schreibkontrolle: Jede "
        "Methode und jede Interpretation muss Source ID, Evidence ID, "
        "deterministisches Artefakt, Tabelle/Figur und Source-Review-Gate behalten.\n\n"
        "## Counts\n\n"
        f"- Bridge rows: {len(bridge)}\n"
        f"- Worksheet rows: {int(total['worksheet_rows'])}\n"
        f"- Method rows: {int(total['method_rows'])}\n"
        f"- Interpretation rows: {int(total['interpretation_rows'])}\n"
        f"- Unique sources: {int(total['unique_sources'])}\n"
        f"- Source/artifact gap rows: {int(total['method_interpretation_source_artifact_gap_rows'])}\n"
        f"- Pending citation rows: {int(total['pending_citation_rows'])}\n"
        f"- Drafting steps: {int(total['drafting_steps'])}\n"
        f"- Final release ready rows: {int(total['final_release_ready_rows'])}\n\n"
        "## Bridge Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Bridge als unmittelbare Schreibsteuerung fuer den H1-H2-H3 "
        "Kern. H1 nutzt T2/F1, H2 nutzt T3/F2, H3 nutzt T4/F3; im Haupttext "
        "bleiben es wenige gute Tabellen und Figuren statt Rohartefakt-Dumps. "
        "Vor finaler Zitation muessen Page-/Section-Note, Claim-Support, "
        "Blocked-Wording, Citation-Use und Reviewer-Metadaten manuell gesetzt "
        "werden. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine "
        "Kausalclaims, keine Wallet-Adressen, keine Trading- oder "
        "Profitabilitaetsclaims und keine Runtime-Agenten. Spaetere Agentenhilfe "
        "bleibt bounded Future Work mit max 50 rows und llm_audit_log.\n"
    )


def _drafting_rows(drafting_pass: pd.DataFrame, area: str) -> pd.DataFrame:
    rows = drafting_pass.loc[drafting_pass["thesis_area"].astype(str) == area].copy()
    if rows.empty:
        raise ValueError(f"Worksheet drafting bridge missing drafting rows for {area}.")
    return rows


def _assert_overview_alignment(
    *,
    thesis_area: str,
    overview: pd.Series,
    worksheet_rows: int,
    method_rows: int,
    interpretation_rows: int,
    unique_sources: int,
    pending_citation_rows: int,
    final_release_ready_rows: int,
    selected_tables: str,
    selected_figures: str,
) -> None:
    expected = (
        worksheet_rows,
        method_rows,
        interpretation_rows,
        unique_sources,
        pending_citation_rows,
        final_release_ready_rows,
        selected_tables,
        selected_figures,
    )
    actual = (
        int(overview["worksheet_rows"]),
        int(overview["method_rows"]),
        int(overview["interpretation_rows"]),
        int(overview["unique_sources"]),
        int(overview["pending_citation_rows"]),
        int(overview["final_release_ready_rows"]),
        str(overview["selected_tables"]),
        str(overview["selected_figures"]),
    )
    if actual != expected:
        raise ValueError(
            f"Worksheet drafting bridge overview alignment mismatch for {thesis_area}: "
            f"{actual} != {expected}."
        )


def _core_row(core_sections: pd.DataFrame, area: str) -> pd.Series:
    rows = core_sections.loc[core_sections["hypothesis"].astype(str) == area]
    if len(rows) != 1:
        raise ValueError(f"Worksheet drafting bridge expected one core-section row for {area}.")
    return rows.iloc[0]


def _overview_row(worksheet_overview: pd.DataFrame, area: str) -> pd.Series:
    rows = worksheet_overview.loc[worksheet_overview["thesis_area"].astype(str) == area]
    if len(rows) != 1:
        raise ValueError(f"Worksheet drafting bridge expected one overview row for {area}.")
    return rows.iloc[0]


def _bridge_row(bridge: pd.DataFrame, thesis_area: str) -> pd.Series:
    rows = bridge.loc[bridge["thesis_area"] == thesis_area]
    if len(rows) != 1:
        raise ValueError(f"Expected one worksheet drafting bridge row for {thesis_area}.")
    return rows.iloc[0]


def _compact_result_package(
    *,
    thesis_area: str,
    selected_tables: str,
    selected_figures: str,
) -> str:
    if thesis_area == "TOTAL":
        return (
            "H1-H2-H3 nutzen zusammen nur T2, T3, T4 und F1, F2, F3 im "
            "empirischen Kern: wenige gute Tabellen und Figuren statt vieler Artefakte."
        )
    return (
        f"{thesis_area}: Ergebnisdarstellung auf {selected_tables}/{selected_figures} "
        "begrenzen; Caption, Artefaktpfad und Limitation aus dem kompakten Resultatpaket "
        "uebernehmen."
    )


def _writing_bridge_action(
    *,
    thesis_area: str,
    drafting_steps: int,
    selected_tables: str,
    selected_figures: str,
) -> str:
    if thesis_area == "TOTAL":
        return (
            f"H1-H2-H3: {drafting_steps} source-gated Drafting-Schritte in die BA "
            "uebernehmen, aber jeden Absatz zuerst gegen Worksheet, Evidence ID, "
            "Artefakt, Source Review Gate und kompaktes Tabellen-/Figurenpaket pruefen."
        )
    return (
        f"{thesis_area}: {drafting_steps} Drafting-Schritte nutzen und jeden Absatz "
        f"an Worksheet-Zeilen, Evidence IDs, deterministische Artefakte, {selected_tables}/"
        f"{selected_figures}, Limitation und Source-Review-Gate binden."
    )


def _final_blocker(thesis_area: str) -> str:
    if thesis_area == "H1":
        return (
            "H1 bleibt final blockiert, bis die 10 Worksheet-Zeilen manuell mit "
            "Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use "
            "entschieden sind; keine allgemeine Marktueberlegenheit behaupten."
        )
    if thesis_area == "H2":
        return (
            "H2 bleibt final blockiert, bis die 5 Worksheet-Zeilen inklusive "
            "Kausalclaim-Grenze entschieden sind; keine Intraday- oder Kausalclaims."
        )
    if thesis_area == "H3":
        return (
            "H3 bleibt final blockiert, bis die 8 Worksheet-Zeilen inklusive "
            "Granger-Grenze und Wallet-Grenze entschieden sind; keine Wallet-Adressen, "
            "Trading-Claims oder Profitabilitaetsclaims."
        )
    return (
        "TOTAL bleibt final blockiert, bis alle 23 H1-H2-H3 Worksheet-Zeilen "
        "manuell entschieden und Ledger, Citation Gate Summary, Batch Plan, "
        "Worksheet Overview und Index regeneriert sind."
    )


def _join_unique(values: Sequence[object] | pd.Series) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return ", ".join(sorted(result))


def _join_unique_from_semicolon(values: Sequence[object] | pd.Series) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in str(value).split(";"):
            text = _clean(item)
            if text and text.lower() != "nan" and text not in seen:
                seen.add(text)
                result.append(text)
    return "; ".join(result)


def _first_clean(values: Sequence[object] | pd.Series) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required worksheet drafting bridge input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "ja", "y"}


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(_escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for record in frame.to_dict(orient="records"):
        rows.append(
            "| "
            + " | ".join(_escape_markdown_cell(record.get(column, "")) for column in columns)
            + " |"
        )
    return "\n".join([header, separator, *rows])


def _escape_markdown_cell(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return text.replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
