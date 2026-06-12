"""Build a H1-H2-H3 drafting checklist from deterministic thesis artifacts."""

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

DRAFTING_OUTPUT = "thesis_h1_h2_h3_drafting_checklist.csv"
DRAFTING_DOC_OUTPUT = "THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md"

DRAFTING_COLUMNS: tuple[str, ...] = (
    "draft_check_id",
    "thesis_area",
    "section_id",
    "chapter_title_de",
    "draft_order",
    "draft_step",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "result_package_items",
    "caption_labels",
    "source_review_gate",
    "draft_instruction_de",
    "thesis_ready_text_seed_de",
    "mandatory_limitation_de",
    "blocked_wording_de",
    "completion_status",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
    "future_agent_boundary_de",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")
DRAFT_STEPS: tuple[str, ...] = (
    "method_setup",
    "result_statement",
    "interpretation_boundary",
    "table_figure_integration",
    "source_review_and_citation_gate",
    "future_agent_boundary",
)


@dataclass(frozen=True)
class H1H2H3DraftingChecklistResult:
    """Generated H1-H2-H3 drafting checklist paths and counts."""

    checklist_path: Path
    docs_path: Path
    checklist_rows: int
    bounded_draft_ready_rows: int
    final_submission_ready_rows: int
    final_blocked_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "checklist_path": str(self.checklist_path),
            "docs_path": str(self.docs_path),
            "checklist_rows": self.checklist_rows,
            "bounded_draft_ready_rows": self.bounded_draft_ready_rows,
            "final_submission_ready_rows": self.final_submission_ready_rows,
            "final_blocked_rows": self.final_blocked_rows,
        }


def generate_h1_h2_h3_drafting_checklist(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3DraftingChecklistResult:
    """Generate the drafting checklist CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    handoff = _read_csv(results_dir / "thesis_source_review_chapter_handoff.csv")
    source_checklist = _read_csv(results_dir / "thesis_chapter_source_review_checklist.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")

    checklist = build_h1_h2_h3_drafting_checklist(
        core_sections=core_sections,
        handoff=handoff,
        source_checklist=source_checklist,
        captions=captions,
    )
    _validate_drafting_checklist(checklist)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = results_dir / DRAFTING_OUTPUT
    docs_path = docs_dir / DRAFTING_DOC_OUTPUT
    checklist.to_csv(checklist_path, index=False)
    docs_path.write_text(_render_drafting_doc(checklist), encoding="utf-8")

    return H1H2H3DraftingChecklistResult(
        checklist_path=checklist_path,
        docs_path=docs_path,
        checklist_rows=len(checklist),
        bounded_draft_ready_rows=int(checklist["ready_for_bounded_draft"].map(_bool_value).sum()),
        final_submission_ready_rows=int(
            checklist["ready_for_final_submission"].map(_bool_value).sum()
        ),
        final_blocked_rows=int(
            checklist["completion_status"].astype(str).str.startswith("final_blocked").sum()
        ),
    )


def build_h1_h2_h3_drafting_checklist(
    *,
    core_sections: pd.DataFrame,
    handoff: pd.DataFrame,
    source_checklist: pd.DataFrame,
    captions: pd.DataFrame,
) -> pd.DataFrame:
    """Return six drafting steps per H1-H2-H3 core chapter."""

    _require_columns(
        core_sections,
        (
            "section_id",
            "hypothesis",
            "chapter_title_de",
            "method_evidence_ids",
            "interpretation_evidence_ids",
            "literature_source_ids",
            "deterministic_artifacts",
            "selected_tables",
            "selected_figures",
            "draft_text_de",
            "thesis_ready_result_de",
            "bounded_interpretation_de",
            "mandatory_limitation_de",
            "blocked_wording_de",
        ),
        "H1-H2-H3 core sections",
    )
    _require_columns(
        handoff,
        (
            "handoff_id",
            "thesis_area",
            "result_package_items",
            "required_source_review_de",
            "future_agent_boundary_de",
        ),
        "source review chapter handoff",
    )
    _require_columns(
        source_checklist,
        (
            "thesis_area",
            "check_area",
            "source_artifact",
            "completion_status",
            "required_evidence_de",
            "manual_action_de",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
        ),
        "chapter source review checklist",
    )
    _require_columns(
        captions,
        (
            "package_id",
            "thesis_label",
            "caption_de",
            "source_note_de",
            "limitation_note_de",
            "include_in_core_package",
        ),
        "table figure captions",
    )

    handoff_by_area = handoff.set_index("thesis_area").to_dict(orient="index")
    captions_by_package = captions.set_index("package_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []

    for core in core_sections.sort_values("hypothesis").to_dict(orient="records"):
        area = str(core["hypothesis"])
        if area not in CORE_AREAS:
            raise ValueError(f"Unexpected H1-H2-H3 drafting area: {area}")
        handoff_row = handoff_by_area.get(area)
        if handoff_row is None:
            raise ValueError(f"Missing chapter handoff row for {area}.")
        area_checks = source_checklist[source_checklist["thesis_area"] == area]
        _validate_area_checks(area=area, area_checks=area_checks)
        overview_gate = _overview_gate_text(area=area, area_checks=area_checks)
        package_ids = _split_semicolon(str(handoff_row["result_package_items"]))
        caption_labels = _caption_labels(captions_by_package=captions_by_package, package_ids=package_ids)
        source_gate = f"{handoff_row['required_source_review_de']} {overview_gate}"
        final_ready = bool(area_checks["ready_for_final_submission"].map(_bool_value).all())
        rows.extend(
            [
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=1,
                    draft_step="method_setup",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Methodenabschnitt schreiben: Methode, Frequenz, Datenbasis, "
                        "deterministische Artefakte und Evidence IDs nennen."
                    ),
                    text_seed=str(core["draft_text_de"]),
                    completion_status="bounded_draft_ready_method_setup",
                    ready_for_final_submission=False,
                ),
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=2,
                    draft_step="result_statement",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Resultatabschnitt schreiben: nur das thesis-ready Resultat "
                        "aus dem Core-Section-Artefakt nutzen und keine neue Kennzahl einfuehren."
                    ),
                    text_seed=str(core["thesis_ready_result_de"]),
                    completion_status="bounded_draft_ready_result_statement",
                    ready_for_final_submission=False,
                ),
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=3,
                    draft_step="interpretation_boundary",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Interpretation schreiben: Aussage an deterministische Artefakte, "
                        "Literatur IDs, Limitation und allowed wording binden."
                    ),
                    text_seed=str(core["bounded_interpretation_de"]),
                    completion_status="bounded_draft_ready_interpretation_boundary",
                    ready_for_final_submission=False,
                ),
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=4,
                    draft_step="table_figure_integration",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Tabelle/Figur einbauen: nur kuratierte Package-Items, Caption, "
                        "Source Note und Limitation aus der Caption Registry verwenden."
                    ),
                    text_seed=_caption_seed(captions_by_package=captions_by_package, package_ids=package_ids),
                    completion_status="bounded_draft_ready_table_figure_integration",
                    ready_for_final_submission=False,
                ),
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=5,
                    draft_step="source_review_and_citation_gate",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Source-Gate im Kapitel sichtbar halten: finale Zitation erst "
                        "nach Manual Source Review Follow-up Overview, "
                        "Overview-/Ledger-Abgleich, Page-/Section-Note, "
                        "Claim-Support, Blocked-Wording und Citation-Use."
                    ),
                    text_seed=source_gate,
                    completion_status=(
                        "final_citation_ready" if final_ready else "final_blocked_source_review_pending"
                    ),
                    ready_for_final_submission=final_ready,
                ),
                _draft_row(
                    core=core,
                    handoff_row=handoff_row,
                    draft_order=6,
                    draft_step="future_agent_boundary",
                    result_package_items=package_ids,
                    caption_labels=caption_labels,
                    source_review_gate=source_gate,
                    draft_instruction_de=(
                        "Falls Agenten erwaehnt werden: nur als Future-Work-Pipeline "
                        "mit bounded inputs, Tests und llm_audit_log formulieren; "
                        "keine Runtime-Agenten aktivieren."
                    ),
                    text_seed=str(handoff_row["future_agent_boundary_de"]),
                    completion_status="future_documentation_only_no_runtime_activation",
                    ready_for_final_submission=False,
                ),
            ]
        )
    return pd.DataFrame(rows, columns=DRAFTING_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_drafting_checklist(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _draft_row(
    *,
    core: dict[str, object],
    handoff_row: dict[str, object],
    draft_order: int,
    draft_step: str,
    result_package_items: list[str],
    caption_labels: str,
    source_review_gate: str,
    draft_instruction_de: str,
    text_seed: str,
    completion_status: str,
    ready_for_final_submission: bool,
) -> dict[str, object]:
    area = str(core["hypothesis"])
    return {
        "draft_check_id": f"draft_{area.lower()}_{draft_order:02d}_{draft_step}",
        "thesis_area": area,
        "section_id": str(core["section_id"]),
        "chapter_title_de": str(core["chapter_title_de"]),
        "draft_order": draft_order,
        "draft_step": draft_step,
        "method_evidence_ids": str(core["method_evidence_ids"]),
        "interpretation_evidence_ids": str(core["interpretation_evidence_ids"]),
        "literature_source_ids": str(core["literature_source_ids"]),
        "deterministic_artifacts": str(core["deterministic_artifacts"]),
        "result_package_items": "; ".join(result_package_items),
        "caption_labels": caption_labels,
        "source_review_gate": source_review_gate,
        "draft_instruction_de": draft_instruction_de,
        "thesis_ready_text_seed_de": text_seed,
        "mandatory_limitation_de": str(core["mandatory_limitation_de"]),
        "blocked_wording_de": str(core["blocked_wording_de"]),
        "completion_status": completion_status,
        "ready_for_bounded_draft": True,
        "ready_for_final_submission": ready_for_final_submission,
        "future_agent_boundary_de": str(handoff_row["future_agent_boundary_de"]),
    }


def _validate_drafting_checklist(checklist: pd.DataFrame) -> None:
    _require_columns(checklist, DRAFTING_COLUMNS, "H1-H2-H3 drafting checklist")
    if len(checklist) != len(CORE_AREAS) * len(DRAFT_STEPS):
        raise ValueError("H1-H2-H3 drafting checklist must contain 18 rows.")
    if checklist["draft_check_id"].duplicated().any():
        raise ValueError("H1-H2-H3 drafting checklist contains duplicate draft_check_id values.")
    if set(checklist["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("H1-H2-H3 drafting checklist must cover H1, H2, and H3.")
    for area, group in checklist.groupby("thesis_area"):
        if tuple(group.sort_values("draft_order")["draft_step"]) != DRAFT_STEPS:
            raise ValueError(f"H1-H2-H3 drafting checklist has wrong steps for {area}.")
    for column in DRAFTING_COLUMNS:
        if checklist[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"H1-H2-H3 drafting checklist contains empty {column}.")
    if not checklist["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("Every H1-H2-H3 drafting checklist row must be bounded-draft-ready.")
    final_ready = checklist["ready_for_final_submission"].map(_bool_value)
    if final_ready.any() and not checklist.loc[final_ready, "completion_status"].eq("final_citation_ready").all():
        raise ValueError("Final-ready drafting rows must have final_citation_ready status.")
    joined = "\n".join(checklist.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H1-H2-H3 drafting checklist must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "evidence ids",
        "literatur ids",
        "deterministische artefakte",
        "keine neue kennzahl",
        "keine finale zitation",
        "source-gate",
        "manual source review follow-up overview",
        "overview-/ledger-abgleich",
        "keine runtime-agenten",
        "llm_audit_log",
        "bounded inputs",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("H1-H2-H3 drafting checklist missing required terms: " + ", ".join(missing))


def _validate_area_checks(*, area: str, area_checks: pd.DataFrame) -> None:
    if area_checks.empty:
        raise ValueError(f"Missing chapter source-review checklist rows for {area}.")
    if len(area_checks) != 6:
        raise ValueError(f"Expected 6 chapter source-review checklist rows for {area}.")
    if not area_checks["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError(f"Not all source-review checklist rows are bounded-draft-ready for {area}.")
    overview_checks = area_checks[
        area_checks["check_area"].isin(("literature_source_review", "final_citation_gate"))
    ]
    if len(overview_checks) != 2:
        raise ValueError(f"Missing overview-bound source-review checks for {area}.")
    joined = "\n".join(overview_checks.astype(str).agg(" ".join, axis=1).tolist()).lower()
    required_terms = (
        "thesis_manual_source_review_followup_overview",
        "manual source review follow-up overview",
        "overview-/ledger-abgleich",
    )
    missing = [term for term in required_terms if term not in joined]
    if missing:
        raise ValueError(f"{area} source-review checks missing overview terms: {', '.join(missing)}")


def _overview_gate_text(*, area: str, area_checks: pd.DataFrame) -> str:
    rows = area_checks[
        area_checks["check_area"].isin(("literature_source_review", "final_citation_gate"))
    ].sort_values("check_area")
    if rows.empty:
        raise ValueError(f"Missing overview-bound source-review rows for {area}.")
    evidence = " ".join(rows["required_evidence_de"].astype(str).tolist())
    actions = " ".join(rows["manual_action_de"].astype(str).tolist())
    return (
        "Manual Source Review Follow-up Overview und Overview-/Ledger-Abgleich "
        f"fuer {area}: {evidence} {actions}"
    )


def _caption_labels(*, captions_by_package: dict[str, dict[str, object]], package_ids: list[str]) -> str:
    labels: list[str] = []
    for package_id in package_ids:
        caption = captions_by_package.get(package_id)
        if caption is None:
            raise ValueError(f"Missing table/figure caption row for {package_id}.")
        if not _bool_value(caption["include_in_core_package"]):
            raise ValueError(f"Caption package is not in core package: {package_id}.")
        labels.append(str(caption["thesis_label"]))
    return "; ".join(labels)


def _caption_seed(*, captions_by_package: dict[str, dict[str, object]], package_ids: list[str]) -> str:
    parts: list[str] = []
    for package_id in package_ids:
        caption = captions_by_package[package_id]
        parts.append(
            f"{package_id} ({caption['thesis_label']}): {caption['caption_de']} "
            f"Quelle/Note: {caption['source_note_de']} Limitation: {caption['limitation_note_de']}"
        )
    return " | ".join(parts)


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H1-H2-H3 drafting checklist input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _render_drafting_doc(checklist: pd.DataFrame) -> str:
    status_counts = checklist["completion_status"].value_counts().to_dict()
    display = checklist[
        [
            "draft_check_id",
            "thesis_area",
            "draft_order",
            "draft_step",
            "result_package_items",
            "caption_labels",
            "completion_status",
            "draft_instruction_de",
        ]
    ]
    return (
        "# H1-H2-H3 Drafting Checklist\n\n"
        "Diese Checkliste macht aus Core Sections, Chapter Handoff, Source-"
        "Review-Checklist und Caption Registry konkrete Schreibschritte fuer "
        "die empirischen BA-Kapitel. Sie berechnet keine Kennzahlen, liest keine "
        "Quelleninhalte, promotet keinen Quellenstatus und aktiviert keine "
        "Runtime-Agenten.\n\n"
        "Die Source-Review- und Zitationsschritte uebernehmen den Manual "
        "Source Review Follow-up Overview-/Ledger-Abgleich aus der Chapter "
        "Source Review Checklist.\n\n"
        "## Counts\n\n"
        f"- Drafting rows: {len(checklist)}\n"
        f"- Bounded draft ready rows: {int(checklist['ready_for_bounded_draft'].map(_bool_value).sum())}\n"
        f"- Final submission ready rows: {int(checklist['ready_for_final_submission'].map(_bool_value).sum())}\n"
        f"- Final blocked source review rows: {int(status_counts.get('final_blocked_source_review_pending', 0))}\n"
        f"- Future documentation-only rows: {int(status_counts.get('future_documentation_only_no_runtime_activation', 0))}\n\n"
        "## Drafting Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Datei als Schreibreihenfolge fuer H1, H2 und H3. Jeder "
        "Abschnitt muss Evidence IDs, Literatur IDs, deterministische Artefakte, "
        "kuratierte Tabellen/Figuren, Limitationen, blockiertes Wording und "
        "Source-Gate sichtbar halten. Keine neue Kennzahl, keine Rohartefakt-"
        "Dumps und keine finale Zitation, solange Source Review offen ist. "
        "Vor dem Citation Gate muss der Manual Source Review Follow-up "
        "Overview-/Ledger-Abgleich sichtbar bleiben. "
        "Agenten bleiben Future Work: keine Runtime-Agenten, kein MCP, kein "
        "Model Routing, keine LLM-Metriken, keine Wallet-Adress-Exposition und "
        "keine Trading-Pfade.\n"
    )


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
