"""Build a thesis submission-readiness board from consolidation artifacts."""

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

READINESS_OUTPUT = "thesis_submission_readiness_board.csv"
READINESS_DOC_OUTPUT = "THESIS_SUBMISSION_READINESS_BOARD.md"

READINESS_COLUMNS: tuple[str, ...] = (
    "gate_id",
    "gate_area",
    "current_status",
    "primary_artifact",
    "evidence_or_control_count",
    "next_action_de",
    "blocker_or_limit_de",
    "thesis_use_de",
)


@dataclass(frozen=True)
class SubmissionReadinessBoardResult:
    """Generated submission-readiness board paths and counts."""

    board_path: Path
    docs_path: Path
    board_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "board_path": str(self.board_path),
            "docs_path": str(self.docs_path),
            "board_rows": self.board_rows,
        }


def generate_submission_readiness_board(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SubmissionReadinessBoardResult:
    """Generate submission-readiness board CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    advisor_package = _read_csv(results_dir / "thesis_advisor_handoff_package.csv")
    source_review = _read_csv(results_dir / "thesis_source_review_execution.csv")
    chapter_bindings = _read_csv(results_dir / "thesis_chapter_source_bindings.csv")
    agent_handoff = _read_csv(results_dir / "thesis_agent_future_work_handoff.csv")

    board = build_submission_readiness_board(
        advisor_package=advisor_package,
        source_review=source_review,
        chapter_bindings=chapter_bindings,
        agent_handoff=agent_handoff,
    )
    _validate_board(board, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    board_path = results_dir / READINESS_OUTPUT
    docs_path = docs_dir / READINESS_DOC_OUTPUT
    board.to_csv(board_path, index=False)
    docs_path.write_text(_render_board_doc(board), encoding="utf-8")

    return SubmissionReadinessBoardResult(
        board_path=board_path,
        docs_path=docs_path,
        board_rows=len(board),
    )


def build_submission_readiness_board(
    *,
    advisor_package: pd.DataFrame,
    source_review: pd.DataFrame,
    chapter_bindings: pd.DataFrame,
    agent_handoff: pd.DataFrame,
) -> pd.DataFrame:
    """Return thesis readiness gates without changing any empirical artifact."""

    _require_columns(advisor_package, ("deliverable_id", "path"), "advisor package")
    _require_columns(source_review, ("review_stage",), "source review")
    _require_columns(chapter_bindings, ("chapter_id", "source_ids"), "chapter bindings")
    _require_columns(agent_handoff, ("status",), "agent handoff")

    advisor_rows = len(advisor_package)
    priority_sources = int((source_review["review_stage"] == "review_now_priority_1").sum())
    blocked_sources = int((source_review["review_stage"] == "metadata_only_blocked").sum())
    mapped_chapters = int((chapter_bindings["source_ids"].astype(str) != "none_mapped").sum())
    agent_deferred_rows = int(agent_handoff["status"].astype(str).str.startswith("future_").sum())

    rows = [
        _readiness_row(
            gate_id="readiness_01_advisor_handoff",
            gate_area="advisor_handoff",
            current_status="ready_for_advisor_discussion",
            primary_artifact="data/results/thesis_advisor_handoff_package.csv",
            evidence_or_control_count=advisor_rows,
            next_action_de="Dozentenbericht und Absprache-Checklist zuerst verwenden.",
            blocker_or_limit_de="DOCX-Render-QA bleibt lokal blockiert, wenn LibreOffice/soffice fehlt.",
            thesis_use_de="Projektstand schriftlich uebergeben und Scope-Feedback einholen.",
        ),
        _readiness_row(
            gate_id="readiness_02_chapter_source_mapping",
            gate_area="chapter_source_mapping",
            current_status="ready_for_draft",
            primary_artifact="data/results/thesis_chapter_source_bindings.csv",
            evidence_or_control_count=mapped_chapters,
            next_action_de="Kapitel entlang Evidence IDs, Quellen, Tabellen/Figuren und Gates schreiben.",
            blocker_or_limit_de="Finale Claims erst nach Human Review, Artefaktverweis, Limitation und Wording Guard.",
            thesis_use_de="Schreibstruktur fuer alle BA-Kapitel.",
        ),
        _readiness_row(
            gate_id="readiness_03_source_review",
            gate_area="source_review",
            current_status="final_blocked_source_review",
            primary_artifact="data/results/thesis_source_review_execution.csv",
            evidence_or_control_count=priority_sources,
            next_action_de="Priority-1-Quellen mit Seiten- oder Abschnittsnotizen reviewen.",
            blocker_or_limit_de=f"{priority_sources} Priority-1-Quellen und {blocked_sources} blocked/future-only Quelle bleiben Gate.",
            thesis_use_de="Draft-Struktur ja; finale Zitation erst nach Human Review.",
        ),
        _readiness_row(
            gate_id="readiness_04_h1_h2_h3_results",
            gate_area="h1_h2_h3_results",
            current_status="ready_for_bounded_result_draft",
            primary_artifact="data/results/thesis_core_results_table.csv",
            evidence_or_control_count=3,
            next_action_de="H1 bounded, H2 daily event-window, H3 timing diagnostics schreiben.",
            blocker_or_limit_de="Keine universelle Effizienz-, Intraday-, Kausalitaets- oder Profitabilitaetsclaims.",
            thesis_use_de="Empirischer Kern der BA-Arbeit.",
        ),
        _readiness_row(
            gate_id="readiness_05_table_figure_package",
            gate_area="table_figure_package",
            current_status="ready_for_draft_integration",
            primary_artifact="data/results/thesis_table_figure_captions.csv",
            evidence_or_control_count=9,
            next_action_de="5 Kern-Tabellen und 4 Kern-Figuren mit Captions integrieren.",
            blocker_or_limit_de="Keine Rohartefakt-Dumps in den Haupttext aufnehmen.",
            thesis_use_de="Kompakte Ergebnisdarstellung.",
        ),
        _readiness_row(
            gate_id="readiness_06_monitor_appendix",
            gate_area="monitor_appendix",
            current_status="appendix_only_pending_human_review",
            primary_artifact="data/results/monitor_anomaly_review_summary.csv",
            evidence_or_control_count=1,
            next_action_de="Monitor nur als read-only Prototyp und Review-Workflow erwaehnen.",
            blocker_or_limit_de="Keine Wallet-Adress-Exposition, keine Order-/Trading-Pfade, keine Kausalclaims.",
            thesis_use_de="Appendix oder Diskussion, nicht empirischer Kern.",
        ),
        _readiness_row(
            gate_id="readiness_07_swiss_result_gate",
            gate_area="swiss_result_gate",
            current_status="final_blocked_official_result",
            primary_artifact="data/results/swiss_referendum_10mio_latest_source_comparison.csv",
            evidence_or_control_count=1,
            next_action_de="Bis zum offiziellen 14. Juni 2026 Resultat beschreibend bleiben.",
            blocker_or_limit_de="Poll-Anteile sind keine Gewinnwahrscheinlichkeiten und tragen keine finale Effizienzaussage.",
            thesis_use_de="Diskussion oder Side-Track nach Resultat-Gate.",
        ),
        _readiness_row(
            gate_id="readiness_08_agent_future_work",
            gate_area="agent_future_work",
            current_status="deferred_future_work_only",
            primary_artifact="data/results/thesis_agent_future_work_handoff.csv",
            evidence_or_control_count=agent_deferred_rows,
            next_action_de="Nur als Future-Work-Ausblick verwenden.",
            blocker_or_limit_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.",
            thesis_use_de="Ausblick auf spaetere Pipeline-Verbesserung.",
        ),
        _readiness_row(
            gate_id="readiness_09_final_qa",
            gate_area="final_qa",
            current_status="pending_after_draft",
            primary_artifact="STATUS.md; docs/project/WORK_LOG.md",
            evidence_or_control_count=2,
            next_action_de="Nach Draft: Tests, review_check, citation review, spelling scan und DOCX render gate wiederholen.",
            blocker_or_limit_de="Repository nicht als final abgabebereit markieren, solange Source Review oder Render-QA offen sind.",
            thesis_use_de="Abgabe-Checkliste nach fertigem Entwurf.",
        ),
    ]
    return pd.DataFrame(rows, columns=READINESS_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_submission_readiness_board(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _readiness_row(
    *,
    gate_id: str,
    gate_area: str,
    current_status: str,
    primary_artifact: str,
    evidence_or_control_count: int,
    next_action_de: str,
    blocker_or_limit_de: str,
    thesis_use_de: str,
) -> dict[str, object]:
    return {
        "gate_id": gate_id,
        "gate_area": gate_area,
        "current_status": current_status,
        "primary_artifact": primary_artifact,
        "evidence_or_control_count": evidence_or_control_count,
        "next_action_de": next_action_de,
        "blocker_or_limit_de": blocker_or_limit_de,
        "thesis_use_de": thesis_use_de,
    }


def _validate_board(board: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(board, READINESS_COLUMNS, "submission readiness board")
    if board["gate_id"].duplicated().any():
        raise ValueError("Submission readiness board contains duplicate gate_id values.")
    if len(board) != 9:
        raise ValueError("Submission readiness board must contain exactly 9 gates.")
    for value in board["primary_artifact"].astype(str):
        for artifact in value.split(";"):
            clean = artifact.strip()
            if clean and not (repo_root / clean).exists():
                raise FileNotFoundError(f"Submission readiness artifact missing: {clean}")
    joined = "\n".join(board.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Submission readiness board must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "final_blocked_source_review",
        "final_blocked_official_result",
        "keine runtime-agenten",
        "soffice",
        "keine roh",
        "human review",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Submission readiness board missing required gates: " + ", ".join(missing))


def _render_board_doc(board: pd.DataFrame) -> str:
    status_counts = board["current_status"].value_counts().to_dict()
    return (
        "# Thesis Submission Readiness Board\n\n"
        "Dieses Board trennt draft-ready, final-blocked und deferred Gates. Es "
        "ist ein Projektsteuerungsartefakt und erzeugt keine neuen empirischen "
        "Resultate.\n\n"
        "## Counts\n\n"
        f"- Readiness gates: {len(board)}\n"
        f"- Final blocked source review: {int(status_counts.get('final_blocked_source_review', 0))}\n"
        f"- Final blocked official result: {int(status_counts.get('final_blocked_official_result', 0))}\n"
        f"- Deferred future-work only: {int(status_counts.get('deferred_future_work_only', 0))}\n\n"
        "## Readiness Gates\n\n"
        + _markdown_table(board)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Board vor einem finalen Thesis-Export. Drafts koennen "
        "weitergeschrieben werden; finale Abgabe bleibt blockiert, solange "
        "Source Review, Swiss Resultat-Gate oder DOCX-Render-QA offen sind.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required submission readiness input missing: {path}")
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
