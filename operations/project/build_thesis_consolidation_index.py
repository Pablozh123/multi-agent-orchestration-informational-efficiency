"""Build a compact index of thesis-consolidation deliverables."""

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

INDEX_OUTPUT = "thesis_consolidation_index.csv"
INDEX_DOC_OUTPUT = "THESIS_CONSOLIDATION_INDEX.md"

INDEX_COLUMNS: tuple[str, ...] = (
    "artifact_id",
    "artifact_type",
    "path",
    "purpose_de",
    "use_now_de",
    "gate_or_limit_de",
)


@dataclass(frozen=True)
class ThesisConsolidationIndexResult:
    """Generated index paths and counts."""

    index_path: Path
    docs_path: Path
    index_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "index_path": str(self.index_path),
            "docs_path": str(self.docs_path),
            "index_rows": self.index_rows,
        }


def generate_thesis_consolidation_index(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisConsolidationIndexResult:
    """Generate the thesis-consolidation index CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    index = build_thesis_consolidation_index()
    _validate_index(index, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    index_path = results_dir / INDEX_OUTPUT
    docs_path = docs_dir / INDEX_DOC_OUTPUT
    index.to_csv(index_path, index=False)
    docs_path.write_text(_render_index_doc(index), encoding="utf-8")

    return ThesisConsolidationIndexResult(
        index_path=index_path,
        docs_path=docs_path,
        index_rows=len(index),
    )


def build_thesis_consolidation_index() -> pd.DataFrame:
    """Return the curated index of current thesis-consolidation artifacts."""

    rows = [
        _index_row(
            artifact_id="index_01_advisor_report_docx",
            artifact_type="advisor_deliverable",
            path="docs/project/dozentenbericht_ba_thesis.docx",
            purpose_de="Schriftlicher Zwischenstand fuer den Dozenten.",
            use_now_de="Direkt als Word-Update geben.",
            gate_or_limit_de="DOCX-Render-QA lokal nur moeglich, wenn LibreOffice/soffice verfuegbar ist.",
        ),
        _index_row(
            artifact_id="index_02_advisor_report_md",
            artifact_type="advisor_review_source",
            path="docs/project/dozentenbericht_ba_thesis.md",
            purpose_de="Transparente Markdown-Quelle des Dozentenberichts.",
            use_now_de="Inhalt schnell pruefen oder nach Word uebertragen.",
            gate_or_limit_de="Keine neuen Claims ohne Update der deterministischen Artefakte.",
        ),
        _index_row(
            artifact_id="index_03_advisor_questions",
            artifact_type="advisor_alignment",
            path="docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
            purpose_de="Acht konkrete Fragen fuer die naechste Dozentenabstimmung.",
            use_now_de="Als Gespraechsagenda nutzen.",
            gate_or_limit_de="Dient Scope-Klaerung, nicht Empirie-Erweiterung.",
        ),
        _index_row(
            artifact_id="index_04_highlevel_view",
            artifact_type="project_status",
            path="docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md",
            purpose_de="Statusmatrix ueber Projektteile, Entscheidungen und Gates.",
            use_now_de="Highlevel-Orientierung fuer Projektfortschritt.",
            gate_or_limit_de="Review-Access bleibt pausiert; Agenten bleiben documentation-only.",
        ),
        _index_row(
            artifact_id="index_05_next_work_plan",
            artifact_type="work_plan",
            path="docs/research/THESIS_NEXT_WORK_PLAN.md",
            purpose_de="Priorisierte Workstreams von Source Review bis finaler QA.",
            use_now_de="Naechste Arbeitsschritte sequenzieren.",
            gate_or_limit_de="Kein Scope-Ausbau vor geschriebenem H1-H3-Kern.",
        ),
        _index_row(
            artifact_id="index_06_execution_checklist",
            artifact_type="execution_plan",
            path="docs/project/THESIS_EXECUTION_CHECKLIST.md; data/results/thesis_execution_checklist.csv",
            purpose_de="Kapitelweise Schreib- und Abnahmecheckliste aus der Highlevel-View.",
            use_now_de="Nach Dozentenfeedback Kapitel, Inputs, Gates und Done-Kriterien abarbeiten.",
            gate_or_limit_de="Review-Access bleibt pausiert; keine Runtime-Agenten oder Rohartefakt-Dumps.",
        ),
        _index_row(
            artifact_id="index_07_source_worksheet",
            artifact_type="source_review",
            path="docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md",
            purpose_de="Manuelle Quellenreview-Zeilen mit Evidence IDs und Pending-Feldern.",
            use_now_de="Quellen mit Seiten-/Abschnittsnotizen pruefen.",
            gate_or_limit_de="Quellenstatus nicht automatisch hochstufen.",
        ),
        _index_row(
            artifact_id="index_08_wording_guard",
            artifact_type="drafting_guard",
            path="docs/research/THESIS_WORDING_GUARD.md",
            purpose_de="Erlaubtes und blockiertes deutsches Thesis-Wording je Evidence ID.",
            use_now_de="Beim Schreiben der Kapitel als Claim-Grenze nutzen.",
            gate_or_limit_de="Keine Formulierung ohne Artefakt und Limitation uebernehmen.",
        ),
        _index_row(
            artifact_id="index_09_table_figure_captions",
            artifact_type="result_package",
            path="docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md",
            purpose_de="Beschriftungen, Quellen- und Limitationstexte fuer Tabellen/Figuren.",
            use_now_de="5 Kern-Tabellen und 4 Kern-Figuren in die Thesis einbauen.",
            gate_or_limit_de="Keine Rohartefakt-Dumps in den Haupttext.",
        ),
        _index_row(
            artifact_id="index_10_chapter_draft",
            artifact_type="chapter_draft",
            path="docs/research/THESIS_CHAPTER_DRAFT.md",
            purpose_de="Erster deutschsprachiger Kapitelentwurf aus der Konsolidierung.",
            use_now_de="Als Rohfassung fuer BA-Kapitel nutzen.",
            gate_or_limit_de="Vor finaler Abgabe Quellenreview und Wording Guard anwenden.",
        ),
        _index_row(
            artifact_id="index_11_source_review_plan",
            artifact_type="source_review",
            path="docs/research/THESIS_SOURCE_REVIEW_PLAN.md",
            purpose_de="Priorisierte Quellenreview-Planung nach Quelle.",
            use_now_de="Quelle-fuer-Quelle abarbeiten.",
            gate_or_limit_de="Candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen.",
        ),
        _index_row(
            artifact_id="index_12_agent_protocol",
            artifact_type="future_work",
            path="docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md",
            purpose_de="Dokumentations-only Agenten-Ausblick mit erlaubten Rollen und Gates.",
            use_now_de="Nur als Future-Work-Abschnitt nutzen.",
            gate_or_limit_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
        ),
        _index_row(
            artifact_id="index_13_status_and_log",
            artifact_type="project_control",
            path="STATUS.md; docs/project/WORK_LOG.md",
            purpose_de="Automatisierter Projektstatus und append-only Arbeitslog.",
            use_now_de="Vor jedem Stop und Commit pruefen.",
            gate_or_limit_de="Nicht behaupten, dass Phase bereit ist, wenn Checks fehlschlagen.",
        ),
    ]
    return pd.DataFrame(rows, columns=INDEX_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_consolidation_index(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _index_row(
    *,
    artifact_id: str,
    artifact_type: str,
    path: str,
    purpose_de: str,
    use_now_de: str,
    gate_or_limit_de: str,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "path": path,
        "purpose_de": purpose_de,
        "use_now_de": use_now_de,
        "gate_or_limit_de": gate_or_limit_de,
    }


def _validate_index(index: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(index, INDEX_COLUMNS, "thesis consolidation index")
    if index["artifact_id"].duplicated().any():
        raise ValueError("Thesis consolidation index contains duplicate artifact_id values.")
    for row in index.to_dict(orient="records"):
        for path in str(row["path"]).split(";"):
            clean_path = path.strip()
            if clean_path and not (repo_root / clean_path).exists():
                raise FileNotFoundError(f"Indexed artifact is missing: {clean_path}")
    joined = "\n".join(index.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Thesis consolidation index must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "dozentenbericht",
        "review-access bleibt pausiert",
        "keine runtime-agenten",
        "quellenstatus nicht automatisch hochstufen",
        "keine roh",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Thesis consolidation index missing required terms: " + ", ".join(missing))


def _render_index_doc(index: pd.DataFrame) -> str:
    return (
        "# Thesis Consolidation Index\n\n"
        "Dieser Index zeigt, welche Artefakte fuer den aktuellen Highlevel-"
        "Projektstand, den Dozentenbericht, Source Review, Wording Guard, "
        "Execution Checklist, Tabellen/Figuren und Future-Work-Agenten relevant "
        "sind.\n\n"
        "## Counts\n\n"
        f"- Indexed artifacts: {len(index)}\n\n"
        "## Artifact Index\n\n"
        + _markdown_table(index)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze zuerst den Dozentenbericht und die Absprache-Checklist fuer die "
        "Betreuung. Nutze danach Execution Checklist, Source Worksheet, Wording "
        "Guard und Next Work Plan fuer das Schreiben. Review-Access, "
        "Runtime-Agenten, MCP, Model Routing, Rohdatenzugriff und Trading-Pfade "
        "bleiben deaktiviert.\n"
    )


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


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
