"""Build a documentation-only handoff plan for future agent assistance."""

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

HANDOFF_OUTPUT = "thesis_agent_future_work_handoff.csv"
HANDOFF_DOC_OUTPUT = "THESIS_AGENT_FUTURE_WORK_HANDOFF.md"

HANDOFF_COLUMNS: tuple[str, ...] = (
    "handoff_id",
    "protocol_id",
    "future_assistance_role",
    "current_pipeline_gap_de",
    "allowed_inputs",
    "allowed_outputs",
    "activation_gate_de",
    "blocked_actions_de",
    "status",
)


@dataclass(frozen=True)
class AgentFutureWorkHandoffResult:
    """Generated future-agent handoff paths and counts."""

    handoff_path: Path
    docs_path: Path
    handoff_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "handoff_path": str(self.handoff_path),
            "docs_path": str(self.docs_path),
            "handoff_rows": self.handoff_rows,
        }


def generate_agent_future_work_handoff(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AgentFutureWorkHandoffResult:
    """Generate future-agent handoff CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    protocol = _read_csv(results_dir / "thesis_agent_assistance_protocol.csv")
    execution = _read_csv(results_dir / "thesis_execution_checklist.csv")
    source_review = _read_csv(results_dir / "thesis_source_review_execution.csv")

    handoff = build_agent_future_work_handoff(
        protocol=protocol,
        execution=execution,
        source_review=source_review,
    )
    _validate_handoff(handoff)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = results_dir / HANDOFF_OUTPUT
    docs_path = docs_dir / HANDOFF_DOC_OUTPUT
    handoff.to_csv(handoff_path, index=False)
    docs_path.write_text(_render_handoff_doc(handoff), encoding="utf-8")

    return AgentFutureWorkHandoffResult(
        handoff_path=handoff_path,
        docs_path=docs_path,
        handoff_rows=len(handoff),
    )


def build_agent_future_work_handoff(
    *,
    protocol: pd.DataFrame,
    execution: pd.DataFrame,
    source_review: pd.DataFrame,
) -> pd.DataFrame:
    """Return documentation-only future agent handoff rows."""

    _require_columns(
        protocol,
        (
            "protocol_id",
            "pipeline_step",
            "allowed_inputs",
            "allowed_outputs",
            "audit_gate",
            "blocked_behaviour",
            "activation_status",
            "thesis_value",
        ),
        "agent assistance protocol",
    )
    _require_columns(execution, ("task_id", "chapter_id"), "execution checklist")
    _require_columns(source_review, ("source_id", "review_stage"), "source review execution")

    source_review_now = int((source_review["review_stage"] == "review_now_priority_1").sum())
    chapter_tasks = int(len(execution))

    rows = []
    for index, row in enumerate(protocol.sort_values("protocol_id").to_dict(orient="records"), start=1):
        protocol_id = str(row["protocol_id"])
        rows.append(
            {
                "handoff_id": f"agent_handoff_{index:02d}_{protocol_id.removeprefix('agent_protocol_')}",
                "protocol_id": protocol_id,
                "future_assistance_role": str(row["pipeline_step"]),
                "current_pipeline_gap_de": _pipeline_gap_de(
                    protocol_id,
                    source_review_now=source_review_now,
                    chapter_tasks=chapter_tasks,
                ),
                "allowed_inputs": str(row["allowed_inputs"]),
                "allowed_outputs": str(row["allowed_outputs"]),
                "activation_gate_de": _activation_gate_de(str(row["audit_gate"])),
                "blocked_actions_de": _blocked_actions_de(str(row["blocked_behaviour"])),
                "status": str(row["activation_status"]),
            }
        )
    return pd.DataFrame(rows, columns=HANDOFF_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_agent_future_work_handoff(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _pipeline_gap_de(protocol_id: str, *, source_review_now: int, chapter_tasks: int) -> str:
    gaps = {
        "agent_protocol_01_source_review": (
            f"{source_review_now} Priority-1-Quellen brauchen manuelle Seiten- oder Abschnittsnotizen."
        ),
        "agent_protocol_02_evidence_reader": (
            "Evidence-IDs muessen spaeter in kurze, artefaktgebundene Entwurfsnotizen uebersetzt werden."
        ),
        "agent_protocol_03_wording_guard": (
            f"{chapter_tasks} Kapitelaufgaben brauchen spaeter Claim-Grenzen und Overclaim-Warnungen."
        ),
        "agent_protocol_04_table_figure_checker": (
            "Kern-Tabellen und Figuren muessen im Entwurf mit Artefakt, Interpretation und Limitation verbunden bleiben."
        ),
        "agent_protocol_05_advisor_update": (
            "Dozenten-Updates muessen aus bestehenden Status- und Berichtsdokumenten knapp zusammengefasst werden."
        ),
        "agent_protocol_06_monitor_review_helper": (
            "Monitor-Material darf nur nach Human Review als Appendix-Workflow zusammengefasst werden."
        ),
        "agent_protocol_07_bounded_mcp": (
            "Ein spaeteres Tool-Interface braucht separate Access-Contracts, Row-Limits und Audit-Logging."
        ),
    }
    return gaps.get(protocol_id, "Future-work gap nur nach separatem Goal klaeren.")


def _activation_gate_de(audit_gate: str) -> str:
    return (
        "Vor Aktivierung: separates genehmigtes Goal, bounded inputs, Tests, "
        f"und {audit_gate}. Keine Nutzung im aktuellen Thesis-Kern."
    )


def _blocked_actions_de(blocked_behaviour: str) -> str:
    return (
        f"Blockiert: {blocked_behaviour}. Zusaetzlich keine Runtime-Agenten, "
        "kein MCP, kein Model Routing, keine LLM-Metriken, keine Rohdaten-Prompts, "
        "keine Wallet-Adress-Exposition by default und keine Trading-Pfade."
    )


def _validate_handoff(handoff: pd.DataFrame) -> None:
    _require_columns(handoff, HANDOFF_COLUMNS, "agent future-work handoff")
    if handoff["handoff_id"].duplicated().any():
        raise ValueError("Agent future-work handoff contains duplicate handoff_id values.")
    if len(handoff) == 0:
        raise ValueError("Agent future-work handoff is empty.")
    active = handoff[~handoff["status"].astype(str).str.startswith("future_")]
    if not active.empty:
        raise ValueError("Agent future-work handoff must not contain active runtime rows.")
    joined = "\n".join(handoff.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Agent future-work handoff must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "keine runtime-agenten",
        "llm_audit_log",
        "keine llm-metriken",
        "keine trading-pfade",
        "separates genehmigtes goal",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Agent future-work handoff missing required guardrails: " + ", ".join(missing))


def _render_handoff_doc(handoff: pd.DataFrame) -> str:
    status_counts = handoff["status"].value_counts().to_dict()
    display = handoff[
        [
            "handoff_id",
            "future_assistance_role",
            "current_pipeline_gap_de",
            "activation_gate_de",
            "blocked_actions_de",
            "status",
        ]
    ]
    return (
        "# Thesis Agent Future-Work Handoff\n\n"
        "Dieses Dokument beschreibt, wie Assistenz-Agenten die Pipeline spaeter "
        "verbessern koennten. Es implementiert, aktiviert und ruft keine "
        "Runtime-Agenten, MCP-Tools, Model Router oder LLM-Interpretationen auf.\n\n"
        "## Counts\n\n"
        f"- Future handoff rows: {len(handoff)}\n"
        f"- Documentation-only rows: {int(status_counts.get('future_documentation_only', 0))}\n"
        f"- Deferred rows: {int(status_counts.get('future_deferred', 0))}\n\n"
        "## Handoff Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze diese Datei nur als Future-Work-Ausblick. Vor jeder Aktivierung "
        "braucht es ein separates genehmigtes Goal, Tests, bounded inputs und "
        "`llm_audit_log`. Bis dahin bleiben Runtime-Agenten, MCP, Model Routing, "
        "LLM-Metriken, Rohdaten-Prompts, Wallet-Adress-Exposition by default und "
        "Trading-Pfade deaktiviert.\n"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required agent future-work input missing: {path}")
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
