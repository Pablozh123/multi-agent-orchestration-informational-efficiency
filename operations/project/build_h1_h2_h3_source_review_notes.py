"""Build bounded H1-H2-H3 source-review notes from pending decision packets."""

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

NOTES_OUTPUT = "thesis_h1_h2_h3_source_review_notes.csv"
NOTES_DOC_OUTPUT = "THESIS_H1_H2_H3_SOURCE_REVIEW_NOTES.md"

NOTE_COLUMNS: tuple[str, ...] = (
    "note_id",
    "thesis_area",
    "section_id",
    "source_id",
    "evidence_id",
    "item_type",
    "selected_table",
    "selected_figure",
    "deterministic_artifact",
    "access_route",
    "structure_inventory_status",
    "review_focus_de",
    "bounded_claim_check_de",
    "blocked_wording_check_de",
    "manual_locator_task_de",
    "reviewer_page_or_section_note",
    "reviewer_claim_support_decision",
    "reviewer_blocked_wording_check",
    "final_citation_gate",
    "note_status",
    "do_not_claim_de",
    "next_action_de",
)

CORE_AREAS: tuple[str, ...] = ("H1", "H2", "H3")


@dataclass(frozen=True)
class H1H2H3SourceReviewNotesResult:
    """Generated H1-H2-H3 source-review note paths and counts."""

    notes_path: Path
    docs_path: Path
    note_rows: int
    h1_rows: int
    h2_rows: int
    h3_rows: int
    pending_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "notes_path": str(self.notes_path),
            "docs_path": str(self.docs_path),
            "note_rows": self.note_rows,
            "h1_rows": self.h1_rows,
            "h2_rows": self.h2_rows,
            "h3_rows": self.h3_rows,
            "pending_rows": self.pending_rows,
        }


def generate_h1_h2_h3_source_review_notes(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> H1H2H3SourceReviewNotesResult:
    """Generate bounded H1-H2-H3 source-review notes and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    decision_packets = _read_csv(results_dir / "thesis_source_review_decision_packets.csv")
    core_sections = _read_csv(results_dir / "thesis_h1_h2_h3_core_sections.csv")
    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")

    notes = build_h1_h2_h3_source_review_notes(
        decision_packets=decision_packets,
        core_sections=core_sections,
        evidence_map=evidence_map,
    )
    _validate_notes(notes)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    notes_path = results_dir / NOTES_OUTPUT
    docs_path = docs_dir / NOTES_DOC_OUTPUT
    notes.to_csv(notes_path, index=False)
    docs_path.write_text(_render_notes_doc(notes), encoding="utf-8")

    return H1H2H3SourceReviewNotesResult(
        notes_path=notes_path,
        docs_path=docs_path,
        note_rows=len(notes),
        h1_rows=int((notes["thesis_area"] == "H1").sum()),
        h2_rows=int((notes["thesis_area"] == "H2").sum()),
        h3_rows=int((notes["thesis_area"] == "H3").sum()),
        pending_rows=int((notes["note_status"] == "pending_manual_source_review").sum()),
    )


def build_h1_h2_h3_source_review_notes(
    *,
    decision_packets: pd.DataFrame,
    core_sections: pd.DataFrame,
    evidence_map: pd.DataFrame,
) -> pd.DataFrame:
    """Return one bounded source-review note row per H1-H2-H3 decision packet."""

    _require_columns(
        decision_packets,
        (
            "decision_packet_id",
            "source_id",
            "evidence_id",
            "thesis_area",
            "item_type",
            "access_route",
            "structure_inventory_status",
            "primary_artifact",
            "reviewer_decision",
            "final_citation_gate",
            "do_not_claim_de",
        ),
        "source review decision packets",
    )
    _require_columns(
        core_sections,
        (
            "hypothesis",
            "section_id",
            "selected_tables",
            "selected_figures",
        ),
        "H1-H2-H3 core sections",
    )
    _require_columns(
        evidence_map,
        (
            "evidence_id",
            "claim_or_decision",
            "allowed_wording",
            "blocked_wording",
            "main_limitation",
        ),
        "evidence map",
    )

    core_by_area = core_sections.set_index("hypothesis").to_dict(orient="index")
    evidence_by_id = evidence_map.set_index("evidence_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    core_packets = decision_packets[
        decision_packets["thesis_area"].isin(CORE_AREAS)
        & (decision_packets["final_citation_gate"] == "full_source_review_required_before_final_citation")
    ].copy()

    for packet in core_packets.sort_values(
        ["thesis_area", "source_priority_order", "source_id", "evidence_id"]
    ).to_dict(orient="records"):
        area = str(packet["thesis_area"])
        evidence_id = str(packet["evidence_id"])
        source_id = str(packet["source_id"])
        evidence = evidence_by_id.get(evidence_id, {})
        core = core_by_area.get(area, {})
        blocked_wording = _translate_known_phrase(str(evidence.get("blocked_wording", "")))
        rows.append(
            {
                "note_id": f"note_{area.lower()}_{source_id}__{evidence_id}",
                "thesis_area": area,
                "section_id": str(core.get("section_id", "")),
                "source_id": source_id,
                "evidence_id": evidence_id,
                "item_type": str(packet["item_type"]),
                "selected_table": str(core.get("selected_tables", "")),
                "selected_figure": str(core.get("selected_figures", "")),
                "deterministic_artifact": str(packet["primary_artifact"]),
                "access_route": str(packet["access_route"]),
                "structure_inventory_status": str(packet["structure_inventory_status"]),
                "review_focus_de": _review_focus_de(
                    thesis_area=area,
                    item_type=str(packet["item_type"]),
                    evidence_id=evidence_id,
                ),
                "bounded_claim_check_de": _bounded_claim_check_de(
                    evidence_id=evidence_id,
                    claim=str(evidence.get("claim_or_decision", "")),
                    allowed=str(evidence.get("allowed_wording", "")),
                    limitation=str(evidence.get("main_limitation", "")),
                ),
                "blocked_wording_check_de": (
                    "Pruefen und dokumentieren, dass die Quelle nicht fuer dieses "
                    f"blockierte Wording genutzt wird: {blocked_wording}."
                ),
                "manual_locator_task_de": _manual_locator_task_de(
                    access_route=str(packet["access_route"]),
                    structure_status=str(packet["structure_inventory_status"]),
                ),
                "reviewer_page_or_section_note": "",
                "reviewer_claim_support_decision": "pending",
                "reviewer_blocked_wording_check": "pending",
                "final_citation_gate": str(packet["final_citation_gate"]),
                "note_status": "pending_manual_source_review",
                "do_not_claim_de": _do_not_claim_de(str(packet["do_not_claim_de"])),
                "next_action_de": (
                    "Source Review manuell ausfuehren: Quelle oeffnen, "
                    "Page-/Section-Note eintragen, Claim-Support auswaehlen "
                    "und Blocked-Wording-Check abschliessen."
                ),
            }
        )

    return pd.DataFrame(rows, columns=NOTE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_h1_h2_h3_source_review_notes(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_notes(notes: pd.DataFrame) -> None:
    _require_columns(notes, NOTE_COLUMNS, "H1-H2-H3 source review notes")
    if notes.empty:
        raise ValueError("H1-H2-H3 source review notes must not be empty.")
    if notes["note_id"].duplicated().any():
        raise ValueError("H1-H2-H3 source review notes contain duplicate note_id values.")
    if set(notes["thesis_area"]) != set(CORE_AREAS):
        raise ValueError("H1-H2-H3 source review notes must cover H1, H2, and H3.")
    for column in (
        "section_id",
        "source_id",
        "evidence_id",
        "selected_table",
        "selected_figure",
        "deterministic_artifact",
        "review_focus_de",
        "bounded_claim_check_de",
        "blocked_wording_check_de",
        "manual_locator_task_de",
        "do_not_claim_de",
        "next_action_de",
    ):
        if notes[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"H1-H2-H3 source review notes contain empty {column}.")
    if not (notes["note_status"] == "pending_manual_source_review").all():
        raise ValueError("All H1-H2-H3 source review notes must remain pending manual review.")
    if not (notes["reviewer_claim_support_decision"] == "pending").all():
        raise ValueError("Claim-support decisions must remain pending.")
    if not (notes["reviewer_blocked_wording_check"] == "pending").all():
        raise ValueError("Blocked-wording checks must remain pending.")
    joined = "\n".join(notes.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("H1-H2-H3 source review notes must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "keine quellenstatus-hochstufung",
        "keine finale zitation",
        "manual",
        "source review",
        "page-/section-note",
        "blocked-wording-check",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("H1-H2-H3 source review notes missing required terms: " + ", ".join(missing))


def _render_notes_doc(notes: pd.DataFrame) -> str:
    area_counts = notes["thesis_area"].value_counts().to_dict()
    access_counts = notes["access_route"].value_counts().to_dict()
    display = notes[
        [
            "note_id",
            "thesis_area",
            "source_id",
            "evidence_id",
            "item_type",
            "selected_table",
            "selected_figure",
            "manual_locator_task_de",
            "note_status",
        ]
    ]
    return (
        "# H1-H2-H3 Source Review Notes\n\n"
        "Diese Notizen fokussieren die manuelle Quellenreview auf den "
        "empirischen BA-Kern H1, H2 und H3. Sie lesen keine Quelleninhalte, "
        "promoten keinen Quellenstatus und ersetzen keine Page-/Section-Notes. "
        "Alle Zeilen bleiben pending, bis eine menschliche Review die Quelle "
        "gegen Evidence ID, Claim-Support und Blocked-Wording geprueft hat.\n\n"
        "## Counts\n\n"
        f"- Review note rows: {len(notes)}\n"
        f"- H1 rows: {int(area_counts.get('H1', 0))}\n"
        f"- H2 rows: {int(area_counts.get('H2', 0))}\n"
        f"- H3 rows: {int(area_counts.get('H3', 0))}\n"
        f"- Local PDF rows: {int(access_counts.get('local_pdf_review', 0))}\n"
        f"- External locator rows: {int(access_counts.get('external_locator_review', 0))}\n"
        "- Status: pending_manual_source_review for all rows\n\n"
        "## Review Note Queue\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Datei als bounded Source-Review-Arbeitsliste fuer den "
        "BA-Kern. Trage Page-/Section-Notes, Claim-Support-Entscheide und "
        "Blocked-Wording-Checks manuell ein. Keine Quellenstatus-Hochstufung, "
        "keine finale Zitation und keine neuen thesis-facing Claims aus "
        "Metadaten, Dateistruktur oder Agenten. Runtime-Agenten, MCP, Model "
        "Routing und LLM-Metriken bleiben deaktiviert.\n"
    )


def _review_focus_de(*, thesis_area: str, item_type: str, evidence_id: str) -> str:
    if item_type == "method":
        return (
            f"{thesis_area}: Pruefen, ob die Quelle die Methodenwahl `{evidence_id}` "
            "als Literaturanker tragen kann."
        )
    return (
        f"{thesis_area}: Pruefen, ob die Quelle die Interpretationsgrenze "
        f"`{evidence_id}` stuetzt, ohne ueber das deterministische Artefakt hinauszugehen."
    )


def _bounded_claim_check_de(*, evidence_id: str, claim: str, allowed: str, limitation: str) -> str:
    return (
        f"Nur bounded pruefen: Evidence ID `{evidence_id}`; Claim/Entscheid `{claim}`; "
        f"erlaubtes Wording `{allowed}`; zwingende Limitation `{_translate_known_phrase(limitation)}`. "
        "Die Quelle darf die lokale Kennzahl nicht ersetzen."
    )


def _manual_locator_task_de(*, access_route: str, structure_status: str) -> str:
    if access_route == "local_pdf_review":
        return (
            "Lokales PDF manuell oeffnen; passende Seite oder Abschnitt finden; "
            "Page-/Section-Note eintragen."
        )
    if access_route == "local_html_review":
        return (
            "Lokale HTML-Datei manuell oeffnen; passenden Abschnitt finden; "
            "Section-Note eintragen."
        )
    if structure_status == "external_only":
        return (
            "Externe DOI/JSTOR/URL manuell oeffnen; Locator, Seite oder Abschnitt "
            "eintragen."
        )
    return "Quelle manuell oeffnen und passende Page-/Section-Note eintragen."


def _do_not_claim_de(source_text: str) -> str:
    return (
        "Keine Quellenstatus-Hochstufung, keine finale Zitation und keine "
        "thesis-facing Claims ohne manuelle Entscheidung. "
        + _translate_known_phrase(source_text)
    )


def _translate_known_phrase(text: str) -> str:
    translations = {
        "reaction speed proof": "Reaktionsgeschwindigkeitsbeweis",
        "broad market superiority proof": "allgemeiner Marktueberlegenheitsbeweis",
        "RCP probability claim without transformation": (
            "RCP-Wahrscheinlichkeitsaussage ohne dokumentierte Transformation"
        ),
        "Polymarket is always better": "Polymarket ist immer besser",
        "many-election proof": "Mehrwahl-Beweis",
        "causal explanation": "kausale Erklaerung",
        "general superiority": "allgemeine Ueberlegenheit",
        "universal forecast dominance": "universelle Prognosedominanz",
        "intraday speed claim": "Intraday-Geschwindigkeitsaussage",
        "post-hoc event selection": "post-hoc Ereignisauswahl",
        "instant market reaction": "sofortige Marktreaktion",
        "causal event proof": "kausaler Ereignisbeweis",
        "arbitrary whale threshold": "willkuerliche Whale-Schwelle",
        "identified private-information wallets": "identifizierte Private-Information-Wallets",
        "causality proof": "Kausalitaetsbeweis",
        "private information proof": "Private-Information-Beweis",
        "profitability proof": "Profitabilitaetsbeweis",
        "private-information proof": "Private-Information-Beweis",
        "causal misconduct": "kausales Fehlverhalten",
        "tradable strategy": "handelbare Strategie",
        "Observed wallet data are BUY-only and source-filtered.": (
            "Die beobachteten Walletdaten sind BUY-only und quellengefiltert."
        ),
        "Daily alignment, multiple testing, and BUY-only extraction limit conclusion strength.": (
            "Taegliche Ausrichtung, Mehrfachtests und BUY-only-Extraktion begrenzen die Schlussstaerke."
        ),
        "Daily prices cannot identify intraday reaction timing.": (
            "Tagespreise koennen Intraday-Reaktionstiming nicht identifizieren."
        ),
    }
    result = text
    for old, new in translations.items():
        result = result.replace(old, new)
    return result


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required H1-H2-H3 source review notes input missing: {path}")
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
