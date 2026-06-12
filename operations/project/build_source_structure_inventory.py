"""Build a deterministic local-source structure inventory for manual review."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/project")

INVENTORY_OUTPUT = "thesis_source_structure_inventory.csv"
INVENTORY_DOC_OUTPUT = "THESIS_SOURCE_STRUCTURE_INVENTORY.md"

INVENTORY_COLUMNS: tuple[str, ...] = (
    "source_id",
    "priority_order",
    "priority_band",
    "local_file_type",
    "local_file_exists",
    "local_file_size_bytes",
    "pdf_page_count_estimate",
    "html_title_present",
    "html_heading_count",
    "html_word_count",
    "structure_inventory_status",
    "manual_review_instruction_de",
    "do_not_claim_de",
)


@dataclass(frozen=True)
class SourceStructureInventoryResult:
    """Generated source-structure inventory paths and counts."""

    inventory_path: Path
    docs_path: Path
    inventory_rows: int
    local_pdf_rows: int
    local_html_rows: int
    external_only_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "inventory_path": str(self.inventory_path),
            "docs_path": str(self.docs_path),
            "inventory_rows": self.inventory_rows,
            "local_pdf_rows": self.local_pdf_rows,
            "local_html_rows": self.local_html_rows,
            "external_only_rows": self.external_only_rows,
        }


def generate_source_structure_inventory(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceStructureInventoryResult:
    """Generate local-source structure inventory CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    literature = _read_csv(repo_root / "data/literature/literature_index.csv")
    access = _read_csv(results_dir / "thesis_source_access_audit.csv")

    inventory = build_source_structure_inventory(literature=literature, access_audit=access)
    _validate_inventory(inventory)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = results_dir / INVENTORY_OUTPUT
    docs_path = docs_dir / INVENTORY_DOC_OUTPUT
    inventory.to_csv(inventory_path, index=False)
    docs_path.write_text(_render_inventory_doc(inventory), encoding="utf-8")

    return SourceStructureInventoryResult(
        inventory_path=inventory_path,
        docs_path=docs_path,
        inventory_rows=len(inventory),
        local_pdf_rows=int((inventory["structure_inventory_status"] == "local_pdf_structure_available").sum()),
        local_html_rows=int(
            (inventory["structure_inventory_status"] == "local_html_structure_available").sum()
        ),
        external_only_rows=int((inventory["structure_inventory_status"] == "external_only").sum()),
    )


def build_source_structure_inventory(
    *,
    literature: pd.DataFrame,
    access_audit: pd.DataFrame,
) -> pd.DataFrame:
    """Return source-structure rows without interpreting source contents."""

    _require_columns(literature, ("source_id", "local_file"), "literature index")
    _require_columns(
        access_audit,
        (
            "source_id",
            "priority_order",
            "priority_band",
            "local_file_exists",
            "local_file_type",
            "local_file_size_bytes",
            "access_route",
        ),
        "source access audit",
    )
    local_by_source = literature.set_index("source_id")["local_file"].to_dict()
    rows: list[dict[str, object]] = []
    for row in access_audit.sort_values("priority_order").to_dict(orient="records"):
        source_id = str(row["source_id"])
        local_file = _clean_value(local_by_source.get(source_id, ""))
        local_path = Path(local_file) if _registered_local_file(local_file) else None
        local_exists = bool(local_path and local_path.exists())
        local_type = str(row["local_file_type"])
        html_stats = _html_stats(local_path) if local_exists and local_type in {"htm", "html"} else {}
        pdf_pages = _pdf_page_count_estimate(local_path) if local_exists and local_type == "pdf" else 0
        status = _inventory_status(
            local_exists=local_exists,
            local_type=local_type,
            access_route=str(row["access_route"]),
        )
        rows.append(
            {
                "source_id": source_id,
                "priority_order": int(row["priority_order"]),
                "priority_band": str(row["priority_band"]),
                "local_file_type": local_type,
                "local_file_exists": local_exists,
                "local_file_size_bytes": int(row["local_file_size_bytes"]),
                "pdf_page_count_estimate": pdf_pages,
                "html_title_present": bool(html_stats.get("title_present", False)),
                "html_heading_count": int(html_stats.get("heading_count", 0)),
                "html_word_count": int(html_stats.get("word_count", 0)),
                "structure_inventory_status": status,
                "manual_review_instruction_de": _manual_instruction(status),
                "do_not_claim_de": _do_not_claim(str(row["priority_band"])),
            }
        )
    return pd.DataFrame(rows, columns=INVENTORY_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_structure_inventory(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_inventory(inventory: pd.DataFrame) -> None:
    _require_columns(inventory, INVENTORY_COLUMNS, "source structure inventory")
    if inventory["source_id"].duplicated().any():
        raise ValueError("Source structure inventory contains duplicate source_id values.")
    if inventory["priority_order"].astype(int).tolist() != list(range(1, len(inventory) + 1)):
        raise ValueError("Source structure inventory priority_order is not contiguous.")
    joined = "\n".join(inventory.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source structure inventory must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "keine inhaltsinterpretation",
        "keine quellenstatus-hochstufung",
        "keine thesis-facing claims",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source structure inventory missing required terms: " + ", ".join(missing))


def _render_inventory_doc(inventory: pd.DataFrame) -> str:
    status_counts = inventory["structure_inventory_status"].value_counts().to_dict()
    display = inventory[
        [
            "priority_order",
            "source_id",
            "priority_band",
            "local_file_type",
            "local_file_exists",
            "pdf_page_count_estimate",
            "html_heading_count",
            "html_word_count",
            "structure_inventory_status",
            "manual_review_instruction_de",
        ]
    ]
    return (
        "# Thesis Source Structure Inventory\n\n"
        "Dieses Inventar prueft nur lokale Dateistruktur fuer die manuelle "
        "Quellenpruefung. Es extrahiert keine PDF-Inhalte, macht keine "
        "Inhaltsinterpretation, erzeugt keine Page Notes und stuft keine Quelle "
        "hoch.\n\n"
        "## Counts\n\n"
        f"- Inventory rows: {len(inventory)}\n"
        f"- Local PDF structure rows: {int(status_counts.get('local_pdf_structure_available', 0))}\n"
        f"- Local HTML structure rows: {int(status_counts.get('local_html_structure_available', 0))}\n"
        f"- External-only rows: {int(status_counts.get('external_only', 0))}\n\n"
        "## Structure Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Inventar nur, um die manuelle Quellenpruefung vorzubereiten. "
        "Keine Inhaltsinterpretation, keine Quellenstatus-Hochstufung, keine "
        "automatischen Page Notes und keine thesis-facing Claims aus Candidate "
        "oder blocked Quellen.\n"
    )


class _TextStatsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.heading_count = 0
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        clean = tag.lower()
        if clean == "title":
            self.in_title = True
        if clean in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.text_parts.append(text)
        if self.in_title:
            self.title_parts.append(text)


def _html_stats(path: Path | None) -> dict[str, int | bool]:
    if path is None or not path.exists():
        return {"title_present": False, "heading_count": 0, "word_count": 0}
    html = path.read_text(encoding="utf-8", errors="ignore")
    parser = _TextStatsParser()
    parser.feed(html)
    text = " ".join(parser.text_parts)
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_'-]*", text)
    return {
        "title_present": bool(" ".join(parser.title_parts).strip()),
        "heading_count": parser.heading_count,
        "word_count": len(words),
    }


def _pdf_page_count_estimate(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    data = path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", data))


def _inventory_status(*, local_exists: bool, local_type: str, access_route: str) -> str:
    if local_exists and local_type == "pdf":
        return "local_pdf_structure_available"
    if local_exists and local_type in {"htm", "html"}:
        return "local_html_structure_available"
    if access_route == "external_locator_review":
        return "external_only"
    return "structure_not_available"


def _manual_instruction(status: str) -> str:
    if status == "local_pdf_structure_available":
        return "PDF manuell oeffnen; Page-/Section-Note im Source Worksheet eintragen."
    if status == "local_html_structure_available":
        return "HTML manuell pruefen; nur Kontext nutzen, wenn Quelle nicht akademisch ist."
    if status == "external_only":
        return "Externe DOI/JSTOR/URL manuell oeffnen; Page-/Section-Note eintragen."
    return "Zugriff klaeren, bevor die Quelle fuer finale Zitation genutzt wird."


def _do_not_claim(priority_band: str) -> str:
    if priority_band in {"blocked_or_future_work_only", "not_currently_needed"}:
        return "Keine thesis-facing Claims; keine Quellenstatus-Hochstufung; keine Inhaltsinterpretation."
    return "Keine thesis-facing Claims ohne manuelle Review-Note; keine Quellenstatus-Hochstufung; keine Inhaltsinterpretation."


def _clean_value(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _registered_local_file(local_file: str) -> bool:
    return bool(local_file and local_file not in {"not_local", "not_verified"})


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source structure inventory input missing: {path}")
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
