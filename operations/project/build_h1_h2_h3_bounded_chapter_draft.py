"""Build a bounded H1-H2-H3 chapter draft from deterministic thesis controls."""

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
DEFAULT_DOCS_DIR = Path("docs/research")

DRAFT_OUTPUT = "thesis_h1_h2_h3_bounded_chapter_draft.csv"
DRAFT_DOC_OUTPUT = "THESIS_H1_H2_H3_BOUNDED_CHAPTER_DRAFT.md"

DRAFT_COLUMNS: tuple[str, ...] = (
    "chapter_draft_id",
    "thesis_area",
    "section_id",
    "chapter_title_de",
    "draft_order",
    "draft_step",
    "draft_subsection_de",
    "method_evidence_ids",
    "interpretation_evidence_ids",
    "literature_source_ids",
    "deterministic_artifacts",
    "selected_tables",
    "selected_figures",
    "selected_result_package_items",
    "source_review_gate_de",
    "chapter_paragraph_de",
    "mandatory_limitation_de",
    "blocked_wording_de",
    "future_agent_boundary_de",
    "draft_status",
    "ready_for_bounded_draft",
    "ready_for_final_submission",
)

STEP_LABELS: dict[str, str] = {
    "method_setup": "Methodischer Ansatz",
    "result_statement": "Resultatabschnitt",
    "interpretation_boundary": "Interpretationsgrenze",
    "table_figure_integration": "Tabellen- und Figurenintegration",
    "source_review_and_citation_gate": "Source-Review- und Zitationsgate",
    "future_agent_boundary": "Future-Agent-Grenze",
}


@dataclass(frozen=True)
class H1H2H3BoundedChapterDraftResult:
    """Generated bounded chapter draft paths and counts."""

    draft_path: Path
    docs_path: Path
    draft_rows: int
    bounded_ready_rows: int
    final_ready_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "draft_path": str(self.draft_path),
            "docs_path": str(self.docs_path),
            "draft_rows": self.draft_rows,
            "bounded_ready_rows": self.bounded_ready_rows,
            "final_ready_rows": self.final_ready_rows,
        }


def generate_h1_h2_h3_bounded_chapter_draft(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3BoundedChapterDraftResult:
    """Generate bounded H1-H2-H3 chapter draft CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    drafting = _read_csv(results_dir / "thesis_h1_h2_h3_drafting_checklist.csv")
    chapter_handoff = _read_csv(results_dir / "thesis_source_review_chapter_handoff.csv")
    captions = _read_csv(results_dir / "thesis_table_figure_captions.csv")

    draft = build_h1_h2_h3_bounded_chapter_draft(
        core_sections=core_sections,
        drafting=drafting,
        chapter_handoff=chapter_handoff,
        captions=captions,
    )
    _validate_draft(draft, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    draft_path = results_dir / DRAFT_OUTPUT
    docs_path = docs_dir / DRAFT_DOC_OUTPUT
    draft.to_csv(draft_path, index=False)
    docs_path.write_text(_render_draft_doc(draft), encoding="utf-8")

    return H1H2H3BoundedChapterDraftResult(
        draft_path=draft_path,
        docs_path=docs_path,
        draft_rows=len(draft),
        bounded_ready_rows=int(draft["ready_for_bounded_draft"].map(_bool_value).sum()),
        final_ready_rows=int(draft["ready_for_final_submission"].map(_bool_value).sum()),
    )


def build_h1_h2_h3_bounded_chapter_draft(
    *,
    core_sections: pd.DataFrame,
    drafting: pd.DataFrame,
    chapter_handoff: pd.DataFrame,
    captions: pd.DataFrame,
) -> pd.DataFrame:
    """Return ordered H1-H2-H3 chapter paragraphs from deterministic inputs."""

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
            "thesis_ready_result_de",
            "bounded_interpretation_de",
            "mandatory_limitation_de",
            "blocked_wording_de",
            "source_review_gate_de",
        ),
        "H1-H2-H3 core sections",
    )
    _require_columns(
        drafting,
        (
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
            "source_review_gate",
            "thesis_ready_text_seed_de",
            "mandatory_limitation_de",
            "blocked_wording_de",
            "completion_status",
            "ready_for_bounded_draft",
            "ready_for_final_submission",
            "future_agent_boundary_de",
        ),
        "H1-H2-H3 drafting checklist",
    )
    _require_columns(
        chapter_handoff,
        (
            "thesis_area",
            "source_review_rows",
            "pending_review_rows",
            "final_citation_ready_rows",
            "result_package_items",
            "required_source_review_de",
        ),
        "source review chapter handoff",
    )
    _require_columns(
        captions,
        ("package_id", "thesis_label", "caption_de", "primary_artifact", "limitation_note_de"),
        "table figure captions",
    )

    core_by_area = core_sections.set_index("hypothesis").to_dict(orient="index")
    handoff_by_area = chapter_handoff.set_index("thesis_area").to_dict(orient="index")
    caption_by_id = captions.set_index("package_id").to_dict(orient="index")
    ordered = drafting.sort_values(["thesis_area", "draft_order"]).reset_index(drop=True)
    rows: list[dict[str, object]] = []

    for draft_row in ordered.to_dict(orient="records"):
        area = str(draft_row["thesis_area"])
        if area not in core_by_area:
            raise ValueError(f"Drafting row references missing core section area: {area}")
        if area not in handoff_by_area:
            raise ValueError(f"Drafting row references missing chapter handoff area: {area}")
        core = core_by_area[area]
        handoff = handoff_by_area[area]
        package_items = _package_item_summary(str(draft_row["result_package_items"]), caption_by_id)
        paragraph = _paragraph_for_step(
            draft_row=draft_row,
            core=core,
            handoff=handoff,
            package_items=package_items,
        )
        rows.append(
            {
                "chapter_draft_id": str(draft_row["draft_check_id"]).replace("draft_", "chapter_draft_", 1),
                "thesis_area": area,
                "section_id": str(draft_row["section_id"]),
                "chapter_title_de": str(draft_row["chapter_title_de"]),
                "draft_order": int(draft_row["draft_order"]),
                "draft_step": str(draft_row["draft_step"]),
                "draft_subsection_de": STEP_LABELS.get(str(draft_row["draft_step"]), str(draft_row["draft_step"])),
                "method_evidence_ids": str(draft_row["method_evidence_ids"]),
                "interpretation_evidence_ids": str(draft_row["interpretation_evidence_ids"]),
                "literature_source_ids": str(draft_row["literature_source_ids"]),
                "deterministic_artifacts": str(draft_row["deterministic_artifacts"]),
                "selected_tables": str(core["selected_tables"]),
                "selected_figures": str(core["selected_figures"]),
                "selected_result_package_items": package_items,
                "source_review_gate_de": str(draft_row["source_review_gate"]),
                "chapter_paragraph_de": paragraph,
                "mandatory_limitation_de": str(draft_row["mandatory_limitation_de"]),
                "blocked_wording_de": str(draft_row["blocked_wording_de"]),
                "future_agent_boundary_de": str(draft_row["future_agent_boundary_de"]),
                "draft_status": str(draft_row["completion_status"]),
                "ready_for_bounded_draft": _bool_value(draft_row["ready_for_bounded_draft"]),
                "ready_for_final_submission": _bool_value(draft_row["ready_for_final_submission"]),
            }
        )
    return pd.DataFrame(rows, columns=DRAFT_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_bounded_chapter_draft(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _paragraph_for_step(
    *,
    draft_row: dict[str, object],
    core: dict[str, object],
    handoff: dict[str, object],
    package_items: str,
) -> str:
    step = str(draft_row["draft_step"])
    area = str(draft_row["thesis_area"])
    title = str(draft_row["chapter_title_de"])
    methods = str(draft_row["method_evidence_ids"])
    interpretations = str(draft_row["interpretation_evidence_ids"])
    literature = str(draft_row["literature_source_ids"])
    artifacts = _compact_artifacts(str(draft_row["deterministic_artifacts"]))
    source_gate = str(draft_row["source_review_gate"])
    limitation = _first_clause(str(draft_row["mandatory_limitation_de"]))

    if step == "method_setup":
        return (
            f"Im Abschnitt `{title}` wird {area} ueber die Methode `{methods}` "
            f"aufgebaut. Die Methode ist an die Literatur-IDs `{literature}` "
            f"und an deterministische Artefakte gebunden: {artifacts}. "
            "Die Interpretation wird noch nicht erweitert; sie bleibt an die "
            f"Evidence-IDs `{interpretations}` und an das Source-Review-Gate "
            "gebunden."
        )
    if step == "result_statement":
        return (
            f"Der Resultatabschnitt nutzt ausschliesslich den vorbereiteten "
            f"Textseed: {draft_row['thesis_ready_text_seed_de']} Diese Aussage "
            f"ist das thesis-ready Ergebnis fuer {area} und wird nicht durch "
            "neue Kennzahlen, Rohartefakt-Dumps oder zusaetzliche Tabellen "
            "erweitert."
        )
    if step == "interpretation_boundary":
        return (
            f"Die Interpretation fuer {area} lautet begrenzt: "
            f"{core['bounded_interpretation_de']} Die zentrale Limitation ist: "
            f"{limitation} Diese Grenze verhindert Universal-, Intraday-, "
            "Kausalitaets-, Private-Information-, Profitabilitaets- oder "
            "Tradeability-Claims."
        )
    if step == "table_figure_integration":
        return (
            f"Die Ergebnisdarstellung fuer {area} nutzt nur die kuratierten "
            f"Package-Items {package_items}. Caption, Artefaktpfad und "
            "Limitation werden aus der Caption Registry uebernommen. Damit "
            "bleibt die Darstellung kompakt: wenige gute Tabellen und Figuren "
            "statt vieler Rohartefakte."
        )
    if step == "source_review_and_citation_gate":
        return (
            f"Das Zitationsgate fuer {area} bleibt sichtbar: {source_gate} "
            f"Im Handoff stehen {int(handoff['source_review_rows'])} "
            f"Source-Review-Zeilen, davon {int(handoff['pending_review_rows'])} "
            f"pending und {int(handoff['final_citation_ready_rows'])} final-ready. "
            "Keine finale Zitation und keine Quellenstatus-Hochstufung erfolgen "
            "aus diesem Draft."
        )
    if step == "future_agent_boundary":
        return (
            f"Die Agenten-Grenze fuer {area} bleibt Future Work: "
            f"{draft_row['future_agent_boundary_de']} Der Abschnitt darf nur "
            "als Pipeline-Ausblick formuliert werden; keine Runtime-Agenten, "
            "kein MCP, kein Model Routing, keine LLM-Metriken, kein "
            "Rohdaten-Prompt und keine Trading-Pfade."
        )
    raise ValueError(f"Unsupported H1-H2-H3 draft step: {step}")


def _validate_draft(draft: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(draft, DRAFT_COLUMNS, "H1-H2-H3 bounded chapter draft")
    if len(draft) != 18:
        raise ValueError("H1-H2-H3 bounded chapter draft must contain exactly 18 rows.")
    if draft["chapter_draft_id"].duplicated().any():
        raise ValueError("H1-H2-H3 bounded chapter draft contains duplicate IDs.")
    area_counts = draft["thesis_area"].value_counts().to_dict()
    for area in ("H1", "H2", "H3"):
        if int(area_counts.get(area, 0)) != 6:
            raise ValueError(f"H1-H2-H3 bounded chapter draft must contain 6 rows for {area}.")
    for column in DRAFT_COLUMNS:
        if draft[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"H1-H2-H3 bounded chapter draft contains empty {column}.")
    required_mapping_columns = (
        "method_evidence_ids",
        "interpretation_evidence_ids",
        "literature_source_ids",
        "deterministic_artifacts",
    )
    for column in required_mapping_columns:
        if draft[column].astype(str).str.contains("nan", case=False, na=False).any():
            raise ValueError(f"H1-H2-H3 bounded chapter draft contains invalid {column}.")
    if not draft["ready_for_bounded_draft"].map(_bool_value).all():
        raise ValueError("All H1-H2-H3 draft rows must be bounded-draft-ready.")
    if draft["ready_for_final_submission"].map(_bool_value).any():
        raise ValueError("H1-H2-H3 draft rows must not be final-submission-ready.")
    for artifact_list in draft["deterministic_artifacts"].astype(str):
        for artifact in _split_semicolon(artifact_list):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"H1-H2-H3 draft artifact missing: {artifact}")
    joined = "\n".join(draft.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H1-H2-H3 bounded chapter draft must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "method_h1_brier_dm",
        "interpretation_h1_bounded_advantage",
        "lit_brier_001",
        "data/results/thesis_h1_summary.csv",
        "t2",
        "f1",
        "keine finale zitation",
        "keine runtime-agenten",
        "llm_audit_log",
        "wenige gute tabellen",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if "source review" not in lower_joined and "source-review" not in lower_joined:
        missing.append("source review")
    if missing:
        raise ValueError("H1-H2-H3 bounded chapter draft missing terms: " + ", ".join(missing))


def _render_draft_doc(draft: pd.DataFrame) -> str:
    bounded_ready = int(draft["ready_for_bounded_draft"].map(_bool_value).sum())
    final_ready = int(draft["ready_for_final_submission"].map(_bool_value).sum())
    sections = [
        "# H1-H2-H3 Bounded Chapter Draft\n",
        "Dieses Dokument ist ein BA-Schreibartefakt fuer den empirischen Kern. "
        "Es erzeugt keine neuen Kennzahlen, liest keine Quelleninhalte und "
        "ersetzt keine finale Quellenpruefung. Es uebersetzt bestehende "
        "Core-Sections, Drafting-Checks, Source-Review-Gates und Caption-"
        "Registry-Eintraege in geordnete Prosa-Bausteine.\n",
        "## Counts\n",
        f"- Draft rows: {len(draft)}\n",
        f"- Bounded draft ready rows: {bounded_ready}\n",
        f"- Final submission ready rows: {final_ready}\n",
        "- Chapters: H1, H2, H3\n",
        "- Steps per chapter: 6\n",
    ]
    for area in ("H1", "H2", "H3"):
        area_rows = draft[draft["thesis_area"] == area].sort_values("draft_order")
        first = area_rows.iloc[0]
        sections.extend(
            [
                f"## {first['chapter_title_de']}\n",
                f"Methoden: `{first['method_evidence_ids']}`\n",
                f"Interpretationen: `{first['interpretation_evidence_ids']}`\n",
                f"Literatur: `{first['literature_source_ids']}`\n",
                f"Deterministische Artefakte: `{first['deterministic_artifacts']}`\n",
                f"Ausgewaehlte Tabelle/Figur: `{first['selected_tables']}` / `{first['selected_figures']}`\n",
            ]
        )
        for record in area_rows.to_dict(orient="records"):
            sections.extend(
                [
                    f"### {int(record['draft_order'])}. {record['draft_subsection_de']}\n",
                    f"{record['chapter_paragraph_de']}\n",
                ]
            )
        sections.extend(
            [
                f"Source Review Gate: {first['source_review_gate_de']}\n",
                f"Nicht schreiben: {first['blocked_wording_de']}\n",
            ]
        )
    sections.extend(
        [
            "## Use Rule\n",
            "Nutze diese Bausteine als bounded BA-Entwurf fuer H1-H2-H3. Jede "
            "Methode und jede Interpretation bleibt an Evidence IDs, Literatur "
            "und deterministische Artefakte gebunden. Keine finale Zitation, "
            "keine Rohartefakt-Dumps, keine neuen Kennzahlen, keine "
            "Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein "
            "Model Routing und keine LLM-Metriken.\n",
        ]
    )
    return "\n".join(sections)


def _package_item_summary(value: str, captions_by_id: dict[str, dict[str, object]]) -> str:
    summaries: list[str] = []
    for package_id in _split_semicolon(value):
        if package_id not in captions_by_id:
            summaries.append(package_id)
            continue
        caption = captions_by_id[package_id]
        summaries.append(
            f"{package_id} ({caption['thesis_label']}): {caption['caption_de']} "
            f"-> {caption['primary_artifact']}; Limitation: {caption['limitation_note_de']}"
        )
    return " | ".join(summaries)


def _compact_artifacts(value: str, *, limit: int = 4) -> str:
    artifacts = _split_semicolon(value)
    shown = artifacts[:limit]
    suffix = ""
    if len(artifacts) > limit:
        remaining = len(artifacts) - limit
        suffix_word = "weiteres gemapptes Artefakt" if remaining == 1 else "weitere gemappte Artefakte"
        suffix = f"; plus {remaining} {suffix_word}"
    return "`" + "`; `".join(shown) + "`" + suffix


def _first_clause(value: str) -> str:
    return _split_pipe(value)[0] if _split_pipe(value) else value


def _split_pipe(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H1-H2-H3 bounded chapter draft input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
