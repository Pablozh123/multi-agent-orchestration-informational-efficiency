"""Build manual source-review decision packets for thesis citation gates."""

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

DECISION_OUTPUT = "thesis_source_review_decision_packets.csv"
DECISION_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_DECISION_PACKETS.md"

DECISION_COLUMNS: tuple[str, ...] = (
    "decision_packet_id",
    "source_id",
    "evidence_id",
    "thesis_area",
    "item_type",
    "source_priority_order",
    "priority_band",
    "access_route",
    "structure_inventory_status",
    "primary_artifact",
    "primary_artifact_exists",
    "draft_use_allowed",
    "final_citation_gate",
    "reviewer_decision",
    "reviewer_page_or_section_note",
    "reviewer_claim_support_decision",
    "required_manual_decision_de",
    "decision_options_de",
    "final_thesis_use_status",
    "do_not_claim_de",
)


@dataclass(frozen=True)
class SourceReviewDecisionPacketResult:
    """Generated source-review decision packet paths and counts."""

    decision_path: Path
    docs_path: Path
    decision_rows: int
    full_review_rows: int
    metadata_only_rows: int
    pending_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "decision_path": str(self.decision_path),
            "docs_path": str(self.docs_path),
            "decision_rows": self.decision_rows,
            "full_review_rows": self.full_review_rows,
            "metadata_only_rows": self.metadata_only_rows,
            "pending_rows": self.pending_rows,
        }


def generate_source_review_decision_packets(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewDecisionPacketResult:
    """Generate source-review decision packet CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    packets = _read_csv(results_dir / "thesis_citation_review_packets.csv")
    access = _read_csv(results_dir / "thesis_source_access_audit.csv")
    structure = _read_csv(results_dir / "thesis_source_structure_inventory.csv")

    decisions = build_source_review_decision_packets(
        packets=packets,
        access=access,
        structure=structure,
        repo_root=repo_root,
    )
    _validate_decision_packets(decisions)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    decision_path = results_dir / DECISION_OUTPUT
    docs_path = docs_dir / DECISION_DOC_OUTPUT
    decisions.to_csv(decision_path, index=False)
    docs_path.write_text(_render_decision_doc(decisions), encoding="utf-8")

    return SourceReviewDecisionPacketResult(
        decision_path=decision_path,
        docs_path=docs_path,
        decision_rows=len(decisions),
        full_review_rows=int(
            (decisions["final_citation_gate"] == "full_source_review_required_before_final_citation").sum()
        ),
        metadata_only_rows=int(
            (decisions["final_citation_gate"] == "metadata_and_relevance_review_before_future_work_use").sum()
        ),
        pending_rows=int((decisions["reviewer_decision"] == "pending").sum()),
    )


def build_source_review_decision_packets(
    *,
    packets: pd.DataFrame,
    access: pd.DataFrame,
    structure: pd.DataFrame,
    repo_root: Path,
) -> pd.DataFrame:
    """Return one manual decision row per citation-review packet."""

    _require_columns(
        packets,
        (
            "packet_id",
            "source_id",
            "evidence_id",
            "thesis_area",
            "item_type",
            "primary_artifact",
            "draft_use_allowed",
            "final_citation_gate",
            "reviewer_decision",
            "required_check",
            "blocked_wording",
        ),
        "citation review packets",
    )
    _require_columns(
        access,
        (
            "source_id",
            "priority_order",
            "priority_band",
            "access_route",
            "do_not_claim_de",
        ),
        "source access audit",
    )
    _require_columns(
        structure,
        ("source_id", "structure_inventory_status", "manual_review_instruction_de"),
        "source structure inventory",
    )

    access_by_source = access.set_index("source_id").to_dict(orient="index")
    structure_by_source = structure.set_index("source_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    for row in packets.sort_values(["thesis_area", "source_id", "evidence_id"]).to_dict(orient="records"):
        source_id = str(row["source_id"])
        access_row = access_by_source.get(source_id)
        structure_row = structure_by_source.get(source_id)
        if access_row is None:
            raise ValueError(f"Decision packet source missing access audit row: {source_id}")
        if structure_row is None:
            raise ValueError(f"Decision packet source missing structure inventory row: {source_id}")
        final_gate = str(row["final_citation_gate"])
        draft_allowed = _bool_value(row["draft_use_allowed"])
        rows.append(
            {
                "decision_packet_id": "decision_" + str(row["packet_id"]),
                "source_id": source_id,
                "evidence_id": str(row["evidence_id"]),
                "thesis_area": str(row["thesis_area"]),
                "item_type": str(row["item_type"]),
                "source_priority_order": int(access_row["priority_order"]),
                "priority_band": str(access_row["priority_band"]),
                "access_route": str(access_row["access_route"]),
                "structure_inventory_status": str(structure_row["structure_inventory_status"]),
                "primary_artifact": str(row["primary_artifact"]),
                "primary_artifact_exists": _artifact_exists(repo_root, str(row["primary_artifact"])),
                "draft_use_allowed": draft_allowed,
                "final_citation_gate": final_gate,
                "reviewer_decision": "pending",
                "reviewer_page_or_section_note": "",
                "reviewer_claim_support_decision": "pending",
                "required_manual_decision_de": _required_manual_decision(
                    final_gate=final_gate,
                    required_check=str(row["required_check"]),
                    structure_instruction=str(structure_row["manual_review_instruction_de"]),
                ),
                "decision_options_de": _decision_options(final_gate=final_gate),
                "final_thesis_use_status": _final_use_status(
                    draft_allowed=draft_allowed,
                    final_gate=final_gate,
                ),
                "do_not_claim_de": _do_not_claim(
                    access_limit=str(access_row["do_not_claim_de"]),
                    blocked_wording=str(row["blocked_wording"]),
                ),
            }
        )
    return pd.DataFrame(rows, columns=DECISION_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_decision_packets(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_decision_packets(decisions: pd.DataFrame) -> None:
    _require_columns(decisions, DECISION_COLUMNS, "source review decision packets")
    if decisions["decision_packet_id"].duplicated().any():
        raise ValueError("Source review decision packets contain duplicate ids.")
    if decisions.empty:
        raise ValueError("Source review decision packets must not be empty.")
    if not decisions["reviewer_decision"].eq("pending").all():
        raise ValueError("All source review decision packets must start as pending.")
    if not decisions["reviewer_claim_support_decision"].eq("pending").all():
        raise ValueError("All source review claim-support decisions must start as pending.")
    if not decisions["final_thesis_use_status"].astype(str).str.startswith("blocked_").all():
        raise ValueError("All source review decision packets must block final thesis use.")
    if (decisions["primary_artifact_exists"] != True).any():  # noqa: E712
        raise ValueError("Source review decision packets reference missing primary artifacts.")
    joined = "\n".join(decisions.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review decision packets must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "manuelle",
        "page-/section-note",
        "keine finale zitation",
        "keine quellenstatus-hochstufung",
        "pending",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source review decision packets missing guardrail terms: " + ", ".join(missing))


def _render_decision_doc(decisions: pd.DataFrame) -> str:
    gate_counts = decisions["final_citation_gate"].value_counts().to_dict()
    display = decisions[
        [
            "decision_packet_id",
            "source_id",
            "evidence_id",
            "thesis_area",
            "item_type",
            "priority_band",
            "access_route",
            "structure_inventory_status",
            "reviewer_decision",
            "final_thesis_use_status",
        ]
    ]
    return (
        "# Thesis Source Review Decision Packets\n\n"
        "Diese Entscheidungspakete bereiten die manuelle Quellenreview vor. "
        "Sie pruefen keine Quelleninhalte, erzeugen keine Page Notes, treffen "
        "keine Support-Entscheidung und stufen keinen Quellenstatus hoch.\n\n"
        "## Counts\n\n"
        f"- Decision packets: {len(decisions)}\n"
        f"- Full source review rows: {int(gate_counts.get('full_source_review_required_before_final_citation', 0))}\n"
        f"- Metadata-only future-work rows: {int(gate_counts.get('metadata_and_relevance_review_before_future_work_use', 0))}\n"
        f"- Pending reviewer decisions: {int((decisions['reviewer_decision'] == 'pending').sum())}\n\n"
        "## Decision Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Datei als manuelle Source-Review-Arbeitsliste. Eine Quelle "
        "darf erst final zitiert werden, wenn eine Page-/Section-Note, eine "
        "Claim-Support-Entscheidung und ein Blocked-Wording-Check eingetragen "
        "sind. Keine finale Zitation, keine Quellenstatus-Hochstufung und keine "
        "neuen thesis-facing Claims aus diesen Pending-Zeilen.\n"
    )


def _required_manual_decision(
    *,
    final_gate: str,
    required_check: str,
    structure_instruction: str,
) -> str:
    if final_gate == "metadata_and_relevance_review_before_future_work_use":
        return (
            "Manuelle Metadata-/Relevance-Entscheidung eintragen; keine finale "
            "Zitation. Strukturhinweis: "
            + structure_instruction
        )
    return (
        "Manuelle Full-Source-Review eintragen: Page-/Section-Note, "
        "Claim-Support-Entscheidung und Blocked-Wording-Check. "
        + required_check
        + " Strukturhinweis: "
        + structure_instruction
    )


def _decision_options(*, final_gate: str) -> str:
    if final_gate == "metadata_and_relevance_review_before_future_work_use":
        return "pending; future_work_metadata_ok; future_work_reject; needs_locator_review"
    return "pending; supports_allowed_wording; supports_with_limitation; does_not_support; needs_more_review"


def _final_use_status(*, draft_allowed: bool, final_gate: str) -> str:
    if final_gate == "metadata_and_relevance_review_before_future_work_use":
        return "blocked_future_work_metadata_only"
    if draft_allowed:
        return "blocked_final_citation_pending_manual_review"
    return "blocked_not_allowed_for_thesis_claims"


def _do_not_claim(*, access_limit: str, blocked_wording: str) -> str:
    return (
        f"{access_limit} Keine finale Zitation, keine Quellenstatus-Hochstufung "
        f"und keine thesis-facing Claims ohne manuelle Entscheidung. Blocked wording: {blocked_wording}"
    )


def _artifact_exists(repo_root: Path, artifact: str) -> bool:
    if not artifact:
        return False
    if artifact.startswith(("http://", "https://")):
        return True
    return (repo_root / artifact).exists()


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review decision packet input missing: {path}")
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
