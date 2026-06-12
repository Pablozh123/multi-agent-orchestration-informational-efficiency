"""Build a compact advisor handoff package from current project artifacts."""

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

PACKAGE_OUTPUT = "thesis_advisor_handoff_package.csv"
PACKAGE_DOC_OUTPUT = "THESIS_ADVISOR_HANDOFF_PACKAGE.md"

PACKAGE_COLUMNS: tuple[str, ...] = (
    "package_order",
    "deliverable_id",
    "path",
    "handoff_use_de",
    "advisor_decision_de",
    "boundary_de",
)


@dataclass(frozen=True)
class AdvisorHandoffPackageResult:
    """Generated advisor handoff package paths and counts."""

    package_path: Path
    docs_path: Path
    package_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "package_path": str(self.package_path),
            "docs_path": str(self.docs_path),
            "package_rows": self.package_rows,
        }


def generate_advisor_handoff_package(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AdvisorHandoffPackageResult:
    """Generate advisor handoff package CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    index = _read_csv(results_dir / "thesis_consolidation_index.csv")
    package = build_advisor_handoff_package(index=index)
    _validate_package(package=package, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    package_path = results_dir / PACKAGE_OUTPUT
    docs_path = docs_dir / PACKAGE_DOC_OUTPUT
    package.to_csv(package_path, index=False)
    docs_path.write_text(_render_package_doc(package), encoding="utf-8")

    return AdvisorHandoffPackageResult(
        package_path=package_path,
        docs_path=docs_path,
        package_rows=len(package),
    )


def build_advisor_handoff_package(*, index: pd.DataFrame) -> pd.DataFrame:
    """Return the ordered package that can be sent or discussed with the advisor."""

    _require_columns(index, ("path", "artifact_id"), "thesis consolidation index")
    indexed_paths = set()
    for value in index["path"].astype(str):
        indexed_paths.update(path.strip() for path in value.split(";") if path.strip())

    rows = [
        _package_row(
            package_order=1,
            deliverable_id="advisor_handoff_note",
            path="docs/project/DOZENTEN_UEBERGABE_TEXT.md",
            handoff_use_de="Als kurze Mail- oder Chat-Vorlage fuer die Uebergabe nutzen.",
            advisor_decision_de="Keine Entscheidung; eroeffnet die Betreuung mit klarer Datei- und Fragenordnung.",
            boundary_de="Zwischenstand, kein finales Abgabe- oder Quellenreview-Signal.",
        ),
        _package_row(
            package_order=2,
            deliverable_id="advisor_report_docx",
            path="docs/project/dozentenbericht_ba_thesis.docx",
            handoff_use_de="Als schriftliches Word-Update an den Dozenten geben.",
            advisor_decision_de="Projektstand, Aufbau, H1-H3-Kern, Grenzen und naechste Schritte abstimmen.",
            boundary_de="DOCX-Render-QA bleibt lokal blockiert, wenn LibreOffice/soffice fehlt.",
        ),
        _package_row(
            package_order=3,
            deliverable_id="advisor_questions",
            path="docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md",
            handoff_use_de="Als Gespraechsagenda fuer die naechste Betreuung nutzen.",
            advisor_decision_de="H1-Wording, Source-Review-Tiefe, H2/H3-Scope, Swiss und Appendix-Scope klaeren.",
            boundary_de="Fragen klaeren Scope; sie aktivieren keine Empirie-Erweiterung.",
        ),
        _package_row(
            package_order=4,
            deliverable_id="submission_readiness",
            path="docs/project/THESIS_SUBMISSION_READINESS_BOARD.md",
            handoff_use_de="Als Gate-Uebersicht fuer draft-ready, final-blocked und deferred Schritte nutzen.",
            advisor_decision_de="Klaeren, welche finalen Gates vor Abgabe zwingend geloest werden muessen.",
            boundary_de="Source Review, Swiss-Gate und DOCX-Render-QA bleiben final blockiert.",
        ),
        _package_row(
            package_order=5,
            deliverable_id="drafting_sequence",
            path="docs/project/THESIS_DRAFTING_SEQUENCE.md",
            handoff_use_de="Als naechste Schreibreihenfolge fuer den BA-Entwurf nutzen.",
            advisor_decision_de="Bestaetigen, ob diese Reihenfolge fuer den naechsten Entwurf sinnvoll ist.",
            boundary_de="Trennt bounded Draft-Arbeit von finalen Blockern und Future Work.",
        ),
        _package_row(
            package_order=6,
            deliverable_id="execution_checklist",
            path="docs/project/THESIS_EXECUTION_CHECKLIST.md",
            handoff_use_de="Nach Feedback als Kapitel- und Abnahme-Checkliste nutzen.",
            advisor_decision_de="Reihenfolge und Done-Kriterien fuer die BA-Kapitel bestaetigen.",
            boundary_de="Review-Access bleibt pausiert; keine Runtime-Agenten oder Rohartefakt-Dumps.",
        ),
        _package_row(
            package_order=7,
            deliverable_id="chapter_source_bindings",
            path="docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md",
            handoff_use_de="Beim Schreiben je Kapitel Quellen, Artefakte und Gates pruefen.",
            advisor_decision_de="Klaeren, ob diese Kapitel-zu-Quelle-Bindung fuer die Abgabe reicht.",
            boundary_de="Keine thesis-facing Claims ohne Human Review, Artefaktverweis, Limitation und Wording Guard.",
        ),
        _package_row(
            package_order=8,
            deliverable_id="source_review_execution",
            path="docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md",
            handoff_use_de="Als manuelle Reihenfolge fuer die Quellenpruefung nutzen.",
            advisor_decision_de="Prioritaet der 11 Priority-1-Quellen und blocked/future-only Quellen bestaetigen.",
            boundary_de="Quellenstatus nicht automatisch hochstufen.",
        ),
        _package_row(
            package_order=9,
            deliverable_id="agent_future_handoff",
            path="docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md",
            handoff_use_de="Nur als Future-Work-Ausblick fuer spaetere Pipeline-Verbesserungen nutzen.",
            advisor_decision_de="Bestaetigen, dass Agenten nicht Teil des empirischen Kerns werden.",
            boundary_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
        ),
        _package_row(
            package_order=10,
            deliverable_id="advisor_feedback_log",
            path="docs/project/DOZENTEN_FEEDBACK_LOG.md",
            handoff_use_de="Nach der Betreuung Feedback und Folgeaktionen eintragen.",
            advisor_decision_de="Keine Entscheidung im Voraus; dient als pending Feedback-Log.",
            boundary_de="Alle Eintraege bleiben pending, bis der Dozent Feedback gegeben hat.",
        ),
        _package_row(
            package_order=11,
            deliverable_id="consolidation_index",
            path="docs/project/THESIS_CONSOLIDATION_INDEX.md",
            handoff_use_de="Als Navigationsindex fuer alle aktuellen Projektartefakte nutzen.",
            advisor_decision_de="Keine Entscheidung; dient Orientierung und Nachvollziehbarkeit.",
            boundary_de="Nicht als neues empirisches Resultat verwenden.",
        ),
    ]
    package = pd.DataFrame(rows, columns=PACKAGE_COLUMNS)
    allowed_self_references = {"docs/project/THESIS_CONSOLIDATION_INDEX.md"}
    missing = sorted(set(package["path"]).difference(indexed_paths).difference(allowed_self_references))
    if missing:
        raise ValueError("Advisor package paths missing from consolidation index: " + ", ".join(missing))
    return package


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_advisor_handoff_package(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _package_row(
    *,
    package_order: int,
    deliverable_id: str,
    path: str,
    handoff_use_de: str,
    advisor_decision_de: str,
    boundary_de: str,
) -> dict[str, object]:
    return {
        "package_order": package_order,
        "deliverable_id": deliverable_id,
        "path": path,
        "handoff_use_de": handoff_use_de,
        "advisor_decision_de": advisor_decision_de,
        "boundary_de": boundary_de,
    }


def _validate_package(*, package: pd.DataFrame, repo_root: Path) -> None:
    _require_columns(package, PACKAGE_COLUMNS, "advisor handoff package")
    if package["deliverable_id"].duplicated().any():
        raise ValueError("Advisor handoff package contains duplicate deliverable_id values.")
    if len(package) != 11:
        raise ValueError("Advisor handoff package must contain exactly 11 deliverables.")
    for path in package["path"].astype(str):
        if not (repo_root / path).exists():
            raise FileNotFoundError(f"Advisor handoff package path missing: {path}")
    joined = "\n".join(package.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Advisor handoff package must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "dozentenbericht_ba_thesis.docx",
        "dozenten_uebergabe_text.md",
        "dozenten_feedback_log.md",
        "review-access bleibt pausiert",
        "quellenstatus nicht automatisch hochstufen",
        "keine runtime-agenten",
        "thesis-facing claims",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Advisor handoff package missing required terms: " + ", ".join(missing))


def _render_package_doc(package: pd.DataFrame) -> str:
    return (
        "# Thesis Advisor Handoff Package\n\n"
        "Dieses Paket sagt, welche Dateien dem Dozenten zuerst gezeigt oder "
        "mitgegeben werden sollten. Es ist eine Handoff-Uebersicht und erzeugt "
        "keine neuen empirischen Resultate.\n\n"
        "## Counts\n\n"
        f"- Package deliverables: {len(package)}\n"
        f"- First deliverable: {package.iloc[0]['deliverable_id']}\n"
        f"- Final deliverable: {package.iloc[-1]['deliverable_id']}\n\n"
        "## Deliverables\n\n"
        + _markdown_table(package)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze zuerst Uebergabetext, Dozentenbericht und Absprache-Checklist. "
        "Danach kommen Submission Readiness Board, Drafting Sequence, Execution "
        "Checklist, Chapter Source Bindings und Source Review Execution fuer "
        "die eigentliche Schreibarbeit. Das Feedback-Log wird nach der "
        "Betreuung ausgefuellt. Agent Future-Work Handoff bleibt Ausblick; "
        "Runtime-Agenten, MCP, Model Routing, LLM-Metriken und Trading-Pfade "
        "bleiben deaktiviert.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required advisor handoff input missing: {path}")
    return pd.read_csv(path)


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
