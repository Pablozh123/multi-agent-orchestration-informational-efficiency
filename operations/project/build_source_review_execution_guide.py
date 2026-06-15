"""Build a manual source-review execution guide from existing review artifacts."""

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

EXECUTION_OUTPUT = "thesis_source_review_execution.csv"
EXECUTION_DOC_OUTPUT = "THESIS_SOURCE_REVIEW_EXECUTION.md"

EXECUTION_COLUMNS: tuple[str, ...] = (
    "review_task_id",
    "priority_order",
    "source_id",
    "source_title",
    "review_stage",
    "thesis_area_focus",
    "evidence_packet_count",
    "method_packet_count",
    "interpretation_packet_count",
    "local_file_registered",
    "review_source_locator",
    "review_focus_de",
    "required_output_de",
    "completion_gate_de",
    "do_not_use_for_de",
)


@dataclass(frozen=True)
class SourceReviewExecutionGuideResult:
    """Generated source-review execution paths and counts."""

    guide_path: Path
    docs_path: Path
    guide_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "guide_path": str(self.guide_path),
            "docs_path": str(self.docs_path),
            "guide_rows": self.guide_rows,
        }


def generate_source_review_execution_guide(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> SourceReviewExecutionGuideResult:
    """Generate source-review execution CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    worksheet = _read_csv(results_dir / "thesis_source_review_worksheet.csv")
    packets = _read_csv(results_dir / "thesis_citation_review_packets.csv")

    guide = build_source_review_execution_guide(worksheet=worksheet, packets=packets)
    _validate_guide(guide)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    guide_path = results_dir / EXECUTION_OUTPUT
    docs_path = docs_dir / EXECUTION_DOC_OUTPUT
    guide.to_csv(guide_path, index=False)
    docs_path.write_text(_render_guide_doc(guide), encoding="utf-8")

    return SourceReviewExecutionGuideResult(
        guide_path=guide_path,
        docs_path=docs_path,
        guide_rows=len(guide),
    )


def build_source_review_execution_guide(
    *,
    worksheet: pd.DataFrame,
    packets: pd.DataFrame,
) -> pd.DataFrame:
    """Return one manual execution row per source-review worksheet row."""

    _require_columns(
        worksheet,
        (
            "source_id",
            "priority_order",
            "source_title",
            "priority_band",
            "thesis_area_focus",
            "local_file_registered",
            "review_source_locator",
            "reviewer_decision",
        ),
        "source review worksheet",
    )
    _require_columns(
        packets,
        ("source_id", "item_type", "evidence_id", "final_citation_gate"),
        "citation review packets",
    )

    packet_summary = _packet_summary(packets)
    rows: list[dict[str, object]] = []
    for row in worksheet.sort_values("priority_order").to_dict(orient="records"):
        source_id = str(row["source_id"])
        counts = packet_summary.get(source_id, _empty_counts())
        priority_band = str(row["priority_band"])
        review_stage = _review_stage(priority_band)
        rows.append(
            {
                "review_task_id": f"source_task_{int(row['priority_order']):02d}_{source_id}",
                "priority_order": int(row["priority_order"]),
                "source_id": source_id,
                "source_title": str(row["source_title"]),
                "review_stage": review_stage,
                "thesis_area_focus": str(row["thesis_area_focus"]),
                "evidence_packet_count": counts["evidence_packet_count"],
                "method_packet_count": counts["method_packet_count"],
                "interpretation_packet_count": counts["interpretation_packet_count"],
                "local_file_registered": _bool_value(row["local_file_registered"]),
                "review_source_locator": str(row["review_source_locator"]),
                "review_focus_de": _review_focus_de(str(row["thesis_area_focus"]), priority_band),
                "required_output_de": _required_output_de(priority_band),
                "completion_gate_de": _completion_gate_de(priority_band),
                "do_not_use_for_de": _do_not_use_for_de(priority_band),
            }
        )
    return pd.DataFrame(rows, columns=EXECUTION_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_source_review_execution_guide(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _packet_summary(packets: pd.DataFrame) -> dict[str, dict[str, int]]:
    summaries: dict[str, dict[str, int]] = {}
    for source_id, group in packets.groupby("source_id"):
        item_types = group["item_type"].astype(str)
        summaries[str(source_id)] = {
            "evidence_packet_count": int(group["evidence_id"].nunique()),
            "method_packet_count": int((item_types == "method").sum()),
            "interpretation_packet_count": int((item_types == "interpretation").sum()),
        }
    return summaries


def _empty_counts() -> dict[str, int]:
    return {
        "evidence_packet_count": 0,
        "method_packet_count": 0,
        "interpretation_packet_count": 0,
    }


def _review_stage(priority_band: str) -> str:
    if priority_band == "priority_1_method_foundation_review":
        return "review_now_priority_1"
    if priority_band == "blocked_or_future_work_only":
        return "metadata_only_blocked"
    if priority_band == "not_currently_needed":
        return "defer_until_mapped"
    return "review_later"


def _review_focus_de(thesis_area_focus: str, priority_band: str) -> str:
    if priority_band == "blocked_or_future_work_only":
        return "Nur Metadaten und Ausschlussgrund pruefen; nicht fuer Thesis-Claims verwenden."
    if priority_band == "not_currently_needed":
        return "Nicht aktiv reviewen, solange die Quelle keiner Evidence-ID zugeordnet ist."

    parts = []
    areas = set(_split_list(thesis_area_focus))
    if "H1" in areas:
        parts.append("H1: Forecast-Qualitaet, Brier/DM und bounded Poll-Vergleich.")
    if "H2" in areas:
        parts.append("H2: Event-Window-Design und Tagesdaten-Limitation.")
    if "H3" in areas:
        parts.append("H3: Wallet-Tiers, Timingdiagnostik und keine Kausalclaims.")
    if "swiss_referendum" in areas:
        parts.append("Swiss: begrenzte Post-Resultat-Fallstudie; Source Review und Poll-Proxy-Limitation pruefen.")
    if "monitor_prototype" in areas:
        parts.append("Monitor: nur Review-Workflow oder Appendix-Prototyp.")
    if "future_agents" in areas:
        parts.append("Agenten: nur Future-Work-Ausblick mit Audit-Gates.")
    return " ".join(parts) if parts else "Review-Fokus aus Evidence-Packets pruefen."


def _required_output_de(priority_band: str) -> str:
    if priority_band == "priority_1_method_foundation_review":
        return "Seiten- oder Abschnittsnotiz, Claim-Support-Entscheid und Blocked-Wording-Check eintragen."
    if priority_band == "blocked_or_future_work_only":
        return "Metadata-Notiz und Begruendung fuer Nicht-Verwendung dokumentieren."
    if priority_band == "not_currently_needed":
        return "Kein Output noetig, bis die Quelle spaeter gemappt wird."
    return "Review-Notiz und Thesis-use-Entscheid eintragen."


def _completion_gate_de(priority_band: str) -> str:
    if priority_band == "priority_1_method_foundation_review":
        return "Erst nach Human Review darf die Quelle final zitiert oder als reviewed/cited markiert werden."
    if priority_band == "blocked_or_future_work_only":
        return "Bleibt fuer thesis-facing Claims gesperrt, bis ein separates Source-Status-Review erfolgt."
    if priority_band == "not_currently_needed":
        return "Bleibt ausserhalb der Thesis, solange keine Evidence-Zuordnung existiert."
    return "Keine Statusaenderung ohne manuelle Entscheidung."


def _do_not_use_for_de(priority_band: str) -> str:
    base = "Nicht fuer automatische Quellenstatus-Hochstufung oder neue empirische Claims nutzen."
    if priority_band == "blocked_or_future_work_only":
        return base + " Nicht fuer thesis-facing Claims nutzen."
    if priority_band == "not_currently_needed":
        return base + " Nicht zitieren, solange die Quelle nicht gemappt und reviewt ist."
    return base + " Nicht als Beleg fuer Kausalitaet, Profitabilitaet oder universelle Effizienz nutzen."


def _validate_guide(guide: pd.DataFrame) -> None:
    _require_columns(guide, EXECUTION_COLUMNS, "source review execution guide")
    if guide["review_task_id"].duplicated().any():
        raise ValueError("Source review execution guide contains duplicate review_task_id values.")
    if len(guide) == 0:
        raise ValueError("Source review execution guide is empty.")
    if not (guide["review_stage"] == "review_now_priority_1").any():
        raise ValueError("Source review execution guide must include active priority-1 rows.")
    joined = "\n".join(guide.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Source review execution guide must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "quellenstatus-hochstufung",
        "human review",
        "nicht fuer thesis-facing claims",
        "keine kausalclaims",
        "post-resultat",
        "poll-proxy-limitation",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Source review execution guide missing required terms: " + ", ".join(missing))


def _render_guide_doc(guide: pd.DataFrame) -> str:
    counts = guide["review_stage"].value_counts().to_dict()
    display = guide[
        [
            "priority_order",
            "source_id",
            "review_stage",
            "thesis_area_focus",
            "evidence_packet_count",
            "review_focus_de",
            "required_output_de",
            "completion_gate_de",
        ]
    ]
    return (
        "# Thesis Source Review Execution\n\n"
        "Diese Ausfuehrungsliste macht aus dem Source-Review-Worksheet eine "
        "konkrete manuelle Review-Reihenfolge. Sie aendert keinen "
        "Quellenstatus und macht keine Quelle automatisch zitierfaehig.\n\n"
        "## Counts\n\n"
        f"- Source review tasks: {len(guide)}\n"
        f"- Review now priority 1: {int(counts.get('review_now_priority_1', 0))}\n"
        f"- Metadata only blocked: {int(counts.get('metadata_only_blocked', 0))}\n"
        f"- Defer until mapped: {int(counts.get('defer_until_mapped', 0))}\n\n"
        "## Manual Review Tasks\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Trage Seiten- oder Abschnittsnotizen, Reviewer-Entscheid und "
        "Reviewer-Notes manuell im Worksheet ein. Quellenstatus nicht "
        "automatisch hochstufen. Blocked/future-only Quellen nicht fuer "
        "thesis-facing Claims verwenden. Diese Liste erzeugt keine neuen "
        "empirischen Metriken.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source review execution input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _split_list(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


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
