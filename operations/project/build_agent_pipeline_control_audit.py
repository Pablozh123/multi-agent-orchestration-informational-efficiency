"""Build a documentation-only control audit for future agent pipeline ideas."""

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

CONTROL_OUTPUT = "thesis_agent_pipeline_control_audit.csv"
CONTROL_DOC_OUTPUT = "THESIS_AGENT_PIPELINE_CONTROL_AUDIT.md"

CONTROL_COLUMNS: tuple[str, ...] = (
    "control_id",
    "protocol_id",
    "future_assistance_role",
    "current_activation_state",
    "pipeline_improvement_de",
    "allowed_input_boundary",
    "allowed_output_boundary",
    "mandatory_audit_gate",
    "blocked_actions_de",
    "required_preconditions_de",
    "current_decision_de",
    "next_safe_step_de",
)


@dataclass(frozen=True)
class AgentPipelineControlAuditResult:
    """Generated agent-pipeline control audit paths and counts."""

    control_path: Path
    docs_path: Path
    control_rows: int
    documentation_only_rows: int
    deferred_rows: int
    active_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "control_path": str(self.control_path),
            "docs_path": str(self.docs_path),
            "control_rows": self.control_rows,
            "documentation_only_rows": self.documentation_only_rows,
            "deferred_rows": self.deferred_rows,
            "active_rows": self.active_rows,
        }


def generate_agent_pipeline_control_audit(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AgentPipelineControlAuditResult:
    """Generate the future-agent pipeline control audit."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    protocol = _read_csv(results_dir / "thesis_agent_assistance_protocol.csv")
    handoff = _read_csv(results_dir / "thesis_agent_future_work_handoff.csv")
    readiness = _read_csv(results_dir / "thesis_submission_readiness_board.csv")

    control = build_agent_pipeline_control_audit(
        protocol=protocol,
        handoff=handoff,
        readiness=readiness,
    )
    _validate_control_audit(control)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    control_path = results_dir / CONTROL_OUTPUT
    docs_path = docs_dir / CONTROL_DOC_OUTPUT
    control.to_csv(control_path, index=False)
    docs_path.write_text(_render_control_doc(control), encoding="utf-8")

    return AgentPipelineControlAuditResult(
        control_path=control_path,
        docs_path=docs_path,
        control_rows=len(control),
        documentation_only_rows=int(
            (control["current_activation_state"] == "future_documentation_only").sum()
        ),
        deferred_rows=int((control["current_activation_state"] == "future_deferred").sum()),
        active_rows=int(control["current_activation_state"].astype(str).str.contains("active").sum()),
    )


def build_agent_pipeline_control_audit(
    *,
    protocol: pd.DataFrame,
    handoff: pd.DataFrame,
    readiness: pd.DataFrame,
) -> pd.DataFrame:
    """Return documentation-only control rows for later agent assistance."""

    _require_columns(
        protocol,
        (
            "protocol_id",
            "pipeline_step",
            "future_agent_help",
            "allowed_inputs",
            "allowed_outputs",
            "audit_gate",
            "blocked_behaviour",
            "activation_status",
            "thesis_value",
        ),
        "agent assistance protocol",
    )
    _require_columns(
        handoff,
        (
            "protocol_id",
            "future_assistance_role",
            "current_pipeline_gap_de",
            "activation_gate_de",
            "blocked_actions_de",
            "status",
        ),
        "agent future-work handoff",
    )
    _require_columns(readiness, ("gate_area", "current_status"), "submission readiness")

    handoff_by_protocol = handoff.set_index("protocol_id").to_dict(orient="index")
    agent_gate_status = _readiness_status(readiness)
    rows: list[dict[str, object]] = []
    for index, row in enumerate(protocol.sort_values("protocol_id").to_dict(orient="records"), start=1):
        protocol_id = str(row["protocol_id"])
        handoff_row = handoff_by_protocol.get(protocol_id)
        if handoff_row is None:
            raise ValueError(f"Agent control audit missing handoff for protocol_id: {protocol_id}")
        state = str(row["activation_status"])
        rows.append(
            {
                "control_id": f"agent_control_{index:02d}_{protocol_id.removeprefix('agent_protocol_')}",
                "protocol_id": protocol_id,
                "future_assistance_role": str(handoff_row["future_assistance_role"]),
                "current_activation_state": state,
                "pipeline_improvement_de": _pipeline_improvement(
                    protocol_id=protocol_id,
                    thesis_value=str(row["thesis_value"]),
                    current_gap=str(handoff_row["current_pipeline_gap_de"]),
                ),
                "allowed_input_boundary": _boundary_text(str(row["allowed_inputs"])),
                "allowed_output_boundary": _boundary_text(str(row["allowed_outputs"])),
                "mandatory_audit_gate": _audit_gate(str(row["audit_gate"])),
                "blocked_actions_de": _blocked_actions(str(handoff_row["blocked_actions_de"])),
                "required_preconditions_de": _required_preconditions(
                    activation_gate=str(handoff_row["activation_gate_de"]),
                    agent_gate_status=agent_gate_status,
                ),
                "current_decision_de": _current_decision(state),
                "next_safe_step_de": _next_safe_step(protocol_id),
            }
        )
    return pd.DataFrame(rows, columns=CONTROL_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_agent_pipeline_control_audit(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_control_audit(control: pd.DataFrame) -> None:
    _require_columns(control, CONTROL_COLUMNS, "agent pipeline control audit")
    if control["control_id"].duplicated().any():
        raise ValueError("Agent pipeline control audit contains duplicate control_id values.")
    if control.empty:
        raise ValueError("Agent pipeline control audit must not be empty.")
    allowed_states = {"future_documentation_only", "future_deferred"}
    unknown_states = sorted(set(control["current_activation_state"]).difference(allowed_states))
    if unknown_states:
        raise ValueError(f"Agent pipeline control audit contains active or unknown states: {unknown_states}")
    for column in CONTROL_COLUMNS:
        if control[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Agent pipeline control audit contains empty {column}.")
    joined = "\n".join(control.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Agent pipeline control audit must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "keine runtime-agenten",
        "kein mcp",
        "kein model routing",
        "keine llm-metriken",
        "kein roh",
        "llm_audit_log",
        "max 50 rows",
        "separates genehmigtes goal",
        "keine trading-pfade",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Agent pipeline control audit missing required guardrails: " + ", ".join(missing))


def _render_control_doc(control: pd.DataFrame) -> str:
    display = control[
        [
            "control_id",
            "future_assistance_role",
            "current_activation_state",
            "pipeline_improvement_de",
            "mandatory_audit_gate",
            "current_decision_de",
            "next_safe_step_de",
        ]
    ]
    state_counts = control["current_activation_state"].value_counts().to_dict()
    return (
        "# Thesis Agent Pipeline Control Audit\n\n"
        "Dieses Audit konkretisiert, wie Assistenz-Agenten die Thesis-Pipeline "
        "spaeter verbessern koennten. Es implementiert, startet und nutzt keine "
        "Runtime-Agenten, MCP-Tools, Model Router oder LLM-Interpretationen.\n\n"
        "## Counts\n\n"
        f"- Control rows: {len(control)}\n"
        f"- Documentation-only rows: {int(state_counts.get('future_documentation_only', 0))}\n"
        f"- Deferred rows: {int(state_counts.get('future_deferred', 0))}\n"
        "- Active rows: 0\n\n"
        "## Control Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Audit nur als Future-Work-Kontrolle. Vor Aktivierung braucht "
        "jede Rolle ein separates genehmigtes Goal, bounded inputs, Tests, "
        "`llm_audit_log`, max 50 rows by default und eine erneute Review der "
        "blockierten Aktionen. Bis dahin gelten: keine Runtime-Agenten, kein MCP, "
        "kein Model Routing, keine LLM-Metriken, kein Rohdaten-Prompt, keine "
        "Wallet-Adress-Exposition by default und keine Trading-Pfade.\n"
    )


def _pipeline_improvement(*, protocol_id: str, thesis_value: str, current_gap: str) -> str:
    return (
        f"{current_gap} Nutzen spaeter: {thesis_value} "
        f"Kontrollpunkt: {protocol_id} bleibt documentation-only."
    )


def _boundary_text(value: str) -> str:
    return f"Nur bounded inputs/outputs: {value}; max 50 rows by default; kein Rohdaten-Prompt."


def _audit_gate(value: str) -> str:
    return f"Pflichtgate: separates genehmigtes Goal, Tests, bounded inputs und {value}."


def _blocked_actions(value: str) -> str:
    return (
        f"{value} Zusaetzlich keine Runtime-Agenten, kein MCP, kein Model Routing, "
        "keine LLM-Metriken, kein Rohdaten-Prompt, keine Wallet-Adress-Exposition "
        "by default und keine Trading-Pfade."
    )


def _required_preconditions(*, activation_gate: str, agent_gate_status: str) -> str:
    return (
        f"Aktueller Agent-Gate-Status: {agent_gate_status}. "
        f"Vor Aktivierung: {activation_gate} "
        "Zusaetzlich Source Review, Swiss Resultat-Gate und finaler QA-Status pruefen."
    )


def _current_decision(state: str) -> str:
    if state == "future_deferred":
        return "Bleibt vollstaendig deferred; keine Nutzung im aktuellen Thesis-Kern."
    return "Bleibt documentation-only; keine Nutzung im aktuellen Thesis-Kern."


def _next_safe_step(protocol_id: str) -> str:
    steps = {
        "agent_protocol_01_source_review": "Nach manueller Quellenreview ein separates Prompt-/Audit-Design fuer fehlende Page Notes schreiben.",
        "agent_protocol_02_evidence_reader": "Nach stabiler Traceability kurze evidence_id-bezogene Draft-Notes spezifizieren.",
        "agent_protocol_03_wording_guard": "Nach erstem BA-Draft eine paragraphenweise Wording-Review-Spezifikation schreiben.",
        "agent_protocol_04_table_figure_checker": "Nach Tabellen-/Figurenintegration Caption-Checks gegen das kuratierte Paket spezifizieren.",
        "agent_protocol_05_advisor_update": "Nach Dozentenfeedback eine bounded Meeting-Summary-Spezifikation schreiben.",
        "agent_protocol_06_monitor_review_helper": "Erst nach Human Review der Monitor-Cases Appendix-Summary-Spezifikation schreiben.",
        "agent_protocol_07_bounded_mcp": "Erst nach separatem Access-Goal ein read-only Summary-Interface mit Tests spezifizieren.",
    }
    return steps.get(protocol_id, "Naechsten Schritt nur nach separatem Goal und Guardrail-Review spezifizieren.")


def _readiness_status(readiness: pd.DataFrame) -> str:
    match = readiness[readiness["gate_area"] == "agent_future_work"]
    if match.empty:
        return "missing_agent_future_work_gate"
    return str(match.iloc[0]["current_status"])


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required agent pipeline control input missing: {path}")
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
