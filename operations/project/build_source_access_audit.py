"""Build a deterministic source-access audit for manual thesis source review."""

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

AUDIT_OUTPUT = "thesis_source_access_audit.csv"
AUDIT_DOC_OUTPUT = "THESIS_SOURCE_ACCESS_AUDIT.md"

AUDIT_COLUMNS: tuple[str, ...] = (
    "source_id",
    "priority_order",
    "source_title",
    "source_status",
    "priority_band",
    "final_citation_readiness",
    "review_source_locator",
    "local_file_registered",
    "local_file_exists",
    "local_file_type",
    "local_file_size_bytes",
    "access_route",
    "review_action_de",
    "do_not_claim_de",
)


@dataclass(frozen=True)
class SourceAccessAuditResult:
    """Generated source-access audit paths and counts."""

    audit_path: Path
    docs_path: Path
    audit_rows: int
    priority_1_rows: int
    local_available_rows: int
    external_review_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "audit_path": str(self.audit_path),
            "docs_path": str(self.docs_path),
            "audit_rows": self.audit_rows,
            "priority_1_rows": self.priority_1_rows,
            "local_available_rows": self.local_available_rows,
            "external_review_rows": self.external_review_rows,
        }


def generate_source_access_audit(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceAccessAuditResult:
    """Generate source-access audit CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")
    source_review_plan = _read_csv(results_dir / "thesis_source_review_plan.csv")

    audit = build_source_access_audit(
        literature=literature,
        source_review_plan=source_review_plan,
    )
    _validate_audit(audit)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    audit_path = results_dir / AUDIT_OUTPUT
    docs_path = docs_dir / AUDIT_DOC_OUTPUT
    audit.to_csv(audit_path, index=False)
    docs_path.write_text(_render_audit_doc(audit), encoding="utf-8")

    return SourceAccessAuditResult(
        audit_path=audit_path,
        docs_path=docs_path,
        audit_rows=len(audit),
        priority_1_rows=int((audit["priority_band"] == "priority_1_method_foundation_review").sum()),
        local_available_rows=int(audit["local_file_exists"].astype(bool).sum()),
        external_review_rows=int((audit["access_route"] == "external_locator_review").sum()),
    )


def build_source_access_audit(
    *,
    literature: pd.DataFrame,
    source_review_plan: pd.DataFrame,
) -> pd.DataFrame:
    """Return one deterministic source-access row per source-review-plan row."""

    _require_columns(
        literature,
        ("source_id", "title", "status", "url", "local_file"),
        "literature index",
    )
    _require_columns(
        source_review_plan,
        (
            "source_id",
            "source_title",
            "source_status",
            "final_citation_readiness",
            "priority_band",
            "next_action",
        ),
        "source review plan",
    )

    literature_by_id = literature.set_index("source_id").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    ordered = source_review_plan.assign(
        _priority_rank=source_review_plan["priority_band"].map(_priority_rank).fillna(99),
    ).sort_values(["_priority_rank", "source_id"], ascending=[True, True])
    for priority_order, row in enumerate(ordered.to_dict(orient="records"), start=1):
        source_id = str(row["source_id"])
        source = literature_by_id.get(source_id, {})
        local_file = _clean_value(source.get("local_file", ""))
        url = _clean_value(source.get("url", ""))
        local_registered = _is_registered_local_file(local_file)
        local_path = Path(local_file) if local_registered else None
        local_exists = bool(local_path and local_path.exists())
        local_type = _local_file_type(local_path) if local_path else "not_local"
        local_size = int(local_path.stat().st_size) if local_path and local_exists else 0
        access_route = _access_route(
            local_registered=local_registered,
            local_exists=local_exists,
            local_type=local_type,
            url=url,
        )
        rows.append(
            {
                "source_id": source_id,
                "priority_order": priority_order,
                "source_title": str(row["source_title"]),
                "source_status": str(row["source_status"]),
                "priority_band": str(row["priority_band"]),
                "final_citation_readiness": str(row["final_citation_readiness"]),
                "review_source_locator": url or local_file or "locator_missing_review_metadata",
                "local_file_registered": local_registered,
                "local_file_exists": local_exists,
                "local_file_type": local_type,
                "local_file_size_bytes": local_size,
                "access_route": access_route,
                "review_action_de": _review_action(access_route, str(row["priority_band"])),
                "do_not_claim_de": _do_not_claim(str(row["priority_band"])),
            }
        )
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_access_audit(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_audit(audit: pd.DataFrame) -> None:
    _require_columns(audit, AUDIT_COLUMNS, "source access audit")
    if audit["source_id"].duplicated().any():
        raise ValueError("Source access audit contains duplicate source_id values.")
    if audit["priority_order"].astype(int).tolist() != list(range(1, len(audit) + 1)):
        raise ValueError("Source access audit priority_order is not contiguous.")
    for column in (
        "source_title",
        "priority_band",
        "final_citation_readiness",
        "review_source_locator",
        "access_route",
        "review_action_de",
        "do_not_claim_de",
    ):
        if audit[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Source access audit contains empty {column}.")
    joined = "\n".join(audit.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source access audit must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "priority_1_method_foundation_review",
        "external_locator_review",
        "keine quellenstatus-hochstufung",
        "keine thesis-facing claims",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source access audit missing required terms: " + ", ".join(missing))


def _render_audit_doc(audit: pd.DataFrame) -> str:
    route_counts = audit["access_route"].value_counts().to_dict()
    priority_1 = int((audit["priority_band"] == "priority_1_method_foundation_review").sum())
    display = audit[
        [
            "priority_order",
            "source_id",
            "priority_band",
            "final_citation_readiness",
            "local_file_exists",
            "local_file_type",
            "access_route",
            "review_action_de",
            "do_not_claim_de",
        ]
    ]
    return (
        "# Thesis Source Access Audit\n\n"
        "Dieses Audit prueft nur den Zugriffspfad fuer die manuelle Quellenpruefung. "
        "Es liest keine Quelleninhalte, stuft keinen Quellenstatus hoch und macht "
        "keine Quelle final zitierfaehig.\n\n"
        "## Counts\n\n"
        f"- Source rows: {len(audit)}\n"
        f"- Priority-1 method-foundation rows: {priority_1}\n"
        f"- Local files available: {int(audit['local_file_exists'].astype(bool).sum())}\n"
        f"- External locator review rows: {int(route_counts.get('external_locator_review', 0))}\n\n"
        "## Access Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Audit, um die manuelle Quellenpruefung vorzubereiten. "
        "Keine Quellenstatus-Hochstufung, keine automatischen Page Notes, keine "
        "thesis-facing Claims aus Candidate/blocked Quellen und keine neuen "
        "empirischen Kennzahlen.\n"
    )


def _priority_rank(priority_band: str) -> int:
    return {
        "priority_1_method_foundation_review": 1,
        "priority_2_core_interpretation_review": 2,
        "priority_3_context_or_appendix_review": 3,
        "blocked_or_future_work_only": 4,
        "not_currently_needed": 5,
    }.get(str(priority_band), 99)


def _clean_value(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _is_registered_local_file(local_file: str) -> bool:
    return bool(local_file and local_file not in {"not_local", "not_verified"})


def _local_file_type(path: Path | None) -> str:
    if path is None:
        return "not_local"
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"pdf", "htm", "html"}:
        return suffix
    return suffix or "unknown"


def _access_route(
    *,
    local_registered: bool,
    local_exists: bool,
    local_type: str,
    url: str,
) -> str:
    if local_exists and local_type == "pdf":
        return "local_pdf_review"
    if local_exists and local_type in {"htm", "html"}:
        return "local_html_context_review"
    if local_registered and not local_exists:
        return "registered_local_file_missing"
    if url:
        return "external_locator_review"
    return "missing_locator_review"


def _review_action(access_route: str, priority_band: str) -> str:
    if priority_band == "blocked_or_future_work_only":
        return "Nur Metadaten und Relevanz pruefen; keine thesis-facing Claims."
    if priority_band == "not_currently_needed":
        return "Keine Aktion, solange die Quelle keinem Evidence Row zugeordnet ist."
    if access_route == "local_pdf_review":
        return "Lokale PDF oeffnen und Seiten-/Abschnittsnotiz in Source Worksheet eintragen."
    if access_route == "local_html_context_review":
        return "Lokale HTML als Kontext pruefen und nicht als akademische Kernquelle verwenden."
    if access_route == "external_locator_review":
        return "Externe DOI/JSTOR/URL pruefen und Seiten-/Abschnittsnotiz manuell eintragen."
    return "Zugriffspfad klaeren, bevor die Quelle fuer finale Zitation genutzt wird."


def _do_not_claim(priority_band: str) -> str:
    if priority_band == "blocked_or_future_work_only":
        return "Keine thesis-facing Claims und keine Quellenstatus-Hochstufung."
    if priority_band == "not_currently_needed":
        return "Nicht zitieren, solange keine Evidence-Zuordnung und kein Review vorliegt."
    return "Keine Quellenstatus-Hochstufung und keine finale Zitation ohne manuelle Page-/Section-Note."


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source access audit input missing: {path}")
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
