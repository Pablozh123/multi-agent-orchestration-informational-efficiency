"""Build a documentation-only safety case for future thesis agent upgrades."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/project")

SAFETY_CASE_OUTPUT = "thesis_agent_pipeline_safety_case.csv"
SAFETY_CASE_DOC_OUTPUT = "THESIS_AGENT_PIPELINE_SAFETY_CASE.md"

SAFETY_CASE_COLUMNS: tuple[str, ...] = (
    "safety_case_id",
    "future_agent_scope",
    "current_evidence_anchor_de",
    "allowed_later_help_de",
    "required_human_gate_de",
    "blocked_runtime_action_de",
    "proof_before_activation_de",
    "current_status",
)


@dataclass(frozen=True)
class AgentPipelineSafetyCaseResult:
    """Generated future-agent safety case paths and counts."""

    safety_case_path: Path
    docs_path: Path
    safety_case_rows: int
    documentation_only_rows: int
    deferred_rows: int
    active_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "safety_case_path": str(self.safety_case_path),
            "docs_path": str(self.docs_path),
            "safety_case_rows": self.safety_case_rows,
            "documentation_only_rows": self.documentation_only_rows,
            "deferred_rows": self.deferred_rows,
            "active_rows": self.active_rows,
        }


def generate_agent_pipeline_safety_case(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> AgentPipelineSafetyCaseResult:
    """Generate a bounded future-agent safety case from current control artifacts."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    coverage = _read_csv(results_dir / "thesis_method_interpretation_source_coverage.csv")
    result_package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    manual_overview = _read_csv(results_dir / "thesis_manual_source_review_followup_overview.csv")
    final_gates = _read_csv(results_dir / "thesis_final_gate_board.csv")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")
    agent_control = _read_csv(results_dir / "thesis_agent_pipeline_control_audit.csv")

    safety_case = build_agent_pipeline_safety_case(
        coverage=coverage,
        result_package=result_package,
        manual_overview=manual_overview,
        final_gates=final_gates,
        agent_upgrade=agent_upgrade,
        agent_control=agent_control,
    )
    _validate_safety_case(safety_case)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    safety_case_path = results_dir / SAFETY_CASE_OUTPUT
    docs_path = docs_dir / SAFETY_CASE_DOC_OUTPUT
    safety_case.to_csv(safety_case_path, index=False)
    docs_path.write_text(_render_doc(safety_case), encoding="utf-8")

    statuses = safety_case["current_status"].astype(str)
    active_rows = int(statuses.str.contains("active", case=False, na=False).sum())
    return AgentPipelineSafetyCaseResult(
        safety_case_path=safety_case_path,
        docs_path=docs_path,
        safety_case_rows=len(safety_case),
        documentation_only_rows=int((statuses == "future_documentation_only").sum()),
        deferred_rows=int((statuses == "future_deferred").sum()),
        active_rows=active_rows,
    )


def build_agent_pipeline_safety_case(
    *,
    coverage: pd.DataFrame,
    result_package: pd.DataFrame,
    manual_overview: pd.DataFrame,
    final_gates: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    agent_control: pd.DataFrame,
) -> pd.DataFrame:
    """Return a seven-row safety case for future agent-assisted work."""

    _require_columns(
        coverage,
        (
            "evidence_id",
            "thesis_area",
            "item_type",
            "thesis_readiness",
            "source_id",
            "primary_artifact_exists",
            "coverage_status",
        ),
        "method interpretation source coverage",
    )
    _require_columns(
        result_package,
        (
            "package_id",
            "package_type",
            "include_in_core_package",
            "package_traceability_status",
        ),
        "result package traceability",
    )
    _require_columns(
        manual_overview,
        ("review_rows", "pending_rows", "final_ready_rows", "unique_sources"),
        "manual source review follow-up overview",
    )
    _require_columns(
        final_gates,
        ("gate_area", "current_status", "final_submission_ready", "evidence_count"),
        "final gate board",
    )
    _require_columns(
        agent_upgrade,
        ("future_assistance_role", "current_status"),
        "agent pipeline upgrade plan",
    )
    _require_columns(
        agent_control,
        ("future_assistance_role", "current_activation_state"),
        "agent pipeline control audit",
    )

    context = _context(
        coverage=coverage,
        result_package=result_package,
        manual_overview=manual_overview,
        final_gates=final_gates,
        agent_upgrade=agent_upgrade,
        agent_control=agent_control,
    )
    rows = [
        _row(
            safety_case_id="agent_safety_01_evidence_lock",
            future_agent_scope="Evidence and source lock",
            current_evidence_anchor_de=(
                f"{context['method_count']} thesis-facing Methoden und "
                f"{context['interpretation_count']} thesis-facing Interpretationen "
                f"sind ueber {context['source_link_count']} H1-H2-H3 Source-Links, "
                f"{context['unique_source_count']} eindeutige Quellen und "
                f"{context['artifact_bound_count']} deterministische Artefaktbindungen "
                "abgesichert; Coverage-Gaps: 0. Insgesamt stehen "
                f"{context['total_source_link_count']} Methode-/Interpretation-"
                "Source-Links inklusive Monitor/Swiss im Audit."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent nur fehlende Mapping-Felder markieren "
                "oder Evidence-ID zu Artefakt/Quelle spiegeln."
            ),
            required_human_gate_de=(
                "Student bestaetigt jede Source- und Artefaktbindung; Dozent klaert "
                "strittige Methoden- oder Interpretationsgrenzen."
            ),
            blocked_runtime_action_de=(
                "Keine neuen Kennzahlen, keine Quellenstatus-Hochstufung, keine "
                "Erfindung von Quellen und keine LLM-Interpretation als Evidenz."
            ),
            proof_before_activation_de=(
                "Separates Goal, Tests, bounded input rows, llm_audit_log und "
                "Traceability-Diff gegen `thesis_method_interpretation_source_coverage.csv`."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_02_manual_source_review_helper",
            future_agent_scope="Manual source review helper",
            current_evidence_anchor_de=(
                f"Manual Source Review Overview: {context['manual_review_rows']} "
                f"H1-H2-H3 Review-Zeilen, {context['manual_pending_rows']} pending, "
                f"{context['manual_final_ready_rows']} final-ready; "
                f"kapitelweise eindeutige Quellen-Summe {context['manual_unique_source_sum']}."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent fehlende Page-/Section-Notes, Claim-Support "
                "und Citation-Use-Felder als Checkliste vorbereiten."
            ),
            required_human_gate_de=(
                "Jede Page-/Section-Note und jeder Claim-Support-Entscheid bleibt "
                "manuell; Ledger-Update erst nach Overview-/Ledger-Abgleich."
            ),
            blocked_runtime_action_de=(
                "Keine finale Zitation, keine automatische Page Note und keine "
                "Quellenstatus-Aenderung."
            ),
            proof_before_activation_de=(
                "Source-Review-Ledger-Zeile plus llm_audit_log mit source_id, "
                "evidence_id, Prompt-Hash, Modell und Output-Pfad."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_03_result_package_guard",
            future_agent_scope="Compact table and figure guard",
            current_evidence_anchor_de=(
                f"Kernpaket: {context['core_table_count']} Tabellen und "
                f"{context['core_figure_count']} Figuren; Package-Gaps: "
                f"{context['package_gap_count']}."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent Caption, Artefaktpfad, Limitation und "
                "Package-ID gegen das kuratierte Paket pruefen."
            ),
            required_human_gate_de=(
                "Student entscheidet Layout und Nummerierung; Dozent kann Umfang "
                "des Tabellen-/Figurenpakets absegnen."
            ),
            blocked_runtime_action_de=(
                "Keine Rohartefakt-Dumps und keine zusaetzlichen Tabellen/Figuren "
                "ohne Map-Update."
            ),
            proof_before_activation_de=(
                "Caption-Checkliste mit package_id, Artefaktpfad, Limitation, "
                "Draft-Hash und llm_audit_log."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_04_claim_wording_guard",
            future_agent_scope="Claim and wording guard",
            current_evidence_anchor_de=(
                "H1-H3 Drafting bleibt bounded: keine Kausalclaims aus H2/H3, "
                "keine private-information-, Profitabilitaets- oder "
                "Tradeability-Claims und keine breite H1-Ueberlegenheitsbehauptung."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent nur human-selected Absatztext gegen "
                "Evidence-IDs, Blocked-Wording und Limitationen pruefen."
            ),
            required_human_gate_de=(
                "Student bleibt Claim-Owner; Dozent validiert strittige "
                "Interpretationsgrenzen."
            ),
            blocked_runtime_action_de=(
                "Keine Relaxierung von Blocked-Wording und keine Erweiterung "
                "des Claims ueber deterministische Artefakte hinaus."
            ),
            proof_before_activation_de=(
                "Wording-Warning-Liste mit Absatz-Hash, Evidence-IDs, "
                "geblocktem Begriff und llm_audit_log."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_05_advisor_feedback_intake",
            future_agent_scope="Advisor feedback intake",
            current_evidence_anchor_de=(
                "Dozentenbericht, Feedback-Log, Final-Gate-Board und "
                "Source-Gated H1-H2-H3 Drafting Sequence bilden den aktuellen "
                "Handoff-Stand."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent Feedback in offene Entscheidungen, "
                "Artefaktchecks und kleine Folgecommit-Scope-Vorschlaege ordnen."
            ),
            required_human_gate_de=(
                "Feedback wird zuerst vom Studenten in `DOZENTEN_FEEDBACK_LOG.md` "
                "erfasst; fachliche Entscheidungen bleiben beim Dozenten/Studenten."
            ),
            blocked_runtime_action_de=(
                "Keine stillen Claim-Aenderungen und kein Wegkuerzen offener "
                "Source-, Swiss- oder DOCX-Gates."
            ),
            proof_before_activation_de=(
                "Feedback-Log-Zeile, Folgecommit-Scope, betroffene Artefakte "
                "und llm_audit_log."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_06_monitor_swiss_boundary",
            future_agent_scope="Monitor and Swiss boundary",
            current_evidence_anchor_de=(
                "Monitor bleibt Appendix/Prototype pending human review; Swiss "
                f"steht auf `{context['swiss_gate_status']}` mit "
                f"{context['swiss_evidence_count']} Final-Case-Live-Zeilen."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Agent nur bounded Statuszusammenfassungen fuer "
                "Appendix- oder Side-Track-Text vorbereiten."
            ),
            required_human_gate_de=(
                "Monitor-Cases brauchen Human Review; Swiss braucht Source Review "
                "und sichtbare Poll-Proxy-Limitation vor finaler Zitation."
            ),
            blocked_runtime_action_de=(
                "Keine Mispricing-, Effizienz-, Misconduct-, Wallet-Adress-, "
                "Trading- oder Profitabilitaetsclaims."
            ),
            proof_before_activation_de=(
                "Human-Review-Status oder Swiss-Source-Review plus "
                "neugenerierte deterministische Artefakte und llm_audit_log."
            ),
            current_status="future_documentation_only",
        ),
        _row(
            safety_case_id="agent_safety_07_bounded_access_contract",
            future_agent_scope="Bounded access contract",
            current_evidence_anchor_de=(
                f"Agent-Upgrade-Plan: {context['agent_upgrade_rows']} Rollen, "
                f"{context['active_agent_rows']} aktive Rows; Control-Audit: "
                f"{context['agent_control_rows']} Kontrollzeilen."
            ),
            allowed_later_help_de=(
                "Spaeter darf ein Interface nur read-only Summary-Artefakte mit "
                "maximal 50 Rows und ohne rohen SQL- oder Wallet-Defaultzugriff liefern."
            ),
            required_human_gate_de=(
                "Separates Access-Goal, Zugriffstests, Reviewer-Freigabe und "
                "Audit-Logging vor jeder Aktivierung."
            ),
            blocked_runtime_action_de=(
                "Kein MCP im aktuellen Goal, kein Model Routing, kein SELECT star, "
                "keine Schreibpfade, keine Order- oder Trading-Pfade."
            ),
            proof_before_activation_de=(
                "Access-Contract-Testbericht mit max 50 rows, no SELECT star, "
                "read-only Status und llm_audit_log-Integration."
            ),
            current_status="future_deferred",
        ),
    ]
    return pd.DataFrame(rows, columns=SAFETY_CASE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_agent_pipeline_safety_case(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _context(
    *,
    coverage: pd.DataFrame,
    result_package: pd.DataFrame,
    manual_overview: pd.DataFrame,
    final_gates: pd.DataFrame,
    agent_upgrade: pd.DataFrame,
    agent_control: pd.DataFrame,
) -> dict[str, int | str]:
    thesis_coverage = coverage[coverage["thesis_readiness"].astype(str) == "thesis_facing_ready"]
    method_count = int(
        thesis_coverage[thesis_coverage["item_type"].astype(str) == "method"]["evidence_id"].nunique()
    )
    interpretation_count = int(
        thesis_coverage[
            thesis_coverage["item_type"].astype(str) == "interpretation"
        ]["evidence_id"].nunique()
    )
    coverage_gaps = int(
        thesis_coverage["coverage_status"].astype(str).str.contains("gap", case=False, na=False).sum()
    )
    artifact_bound_count = int(thesis_coverage["primary_artifact_exists"].map(_bool_value).sum())
    if coverage_gaps:
        raise ValueError("Agent safety case requires zero thesis-facing coverage gaps.")

    core_package = result_package[result_package["include_in_core_package"].map(_bool_value)]
    package_gaps = int(
        core_package["package_traceability_status"].astype(str).str.contains("gap", case=False, na=False).sum()
    )
    if package_gaps:
        raise ValueError("Agent safety case requires zero core package traceability gaps.")

    gates = final_gates.set_index("gate_area").to_dict(orient="index")
    swiss_gate = gates.get("swiss_result_gate", {})
    active_agent_rows = int(
        agent_upgrade["current_status"].astype(str).str.contains("active", case=False, na=False).sum()
    )
    active_control_rows = int(
        agent_control["current_activation_state"].astype(str).str.contains("active", case=False, na=False).sum()
    )
    if active_agent_rows or active_control_rows:
        raise ValueError("Agent safety case must not include active runtime agent rows.")

    return {
        "method_count": method_count,
        "interpretation_count": interpretation_count,
        "source_link_count": int(len(thesis_coverage)),
        "total_source_link_count": int(len(coverage)),
        "unique_source_count": int(thesis_coverage["source_id"].nunique()),
        "artifact_bound_count": artifact_bound_count,
        "manual_review_rows": int(manual_overview["review_rows"].astype(int).sum()),
        "manual_pending_rows": int(manual_overview["pending_rows"].astype(int).sum()),
        "manual_final_ready_rows": int(manual_overview["final_ready_rows"].astype(int).sum()),
        "manual_unique_source_sum": int(manual_overview["unique_sources"].astype(int).sum()),
        "core_table_count": int((core_package["package_type"].astype(str) == "table").sum()),
        "core_figure_count": int((core_package["package_type"].astype(str) == "figure").sum()),
        "package_gap_count": package_gaps,
        "swiss_gate_status": str(swiss_gate.get("current_status", "unknown")),
        "swiss_evidence_count": int(swiss_gate.get("evidence_count", 0)),
        "agent_upgrade_rows": int(len(agent_upgrade)),
        "active_agent_rows": active_agent_rows,
        "agent_control_rows": int(len(agent_control)),
    }


def _row(
    *,
    safety_case_id: str,
    future_agent_scope: str,
    current_evidence_anchor_de: str,
    allowed_later_help_de: str,
    required_human_gate_de: str,
    blocked_runtime_action_de: str,
    proof_before_activation_de: str,
    current_status: str,
) -> dict[str, object]:
    return {
        "safety_case_id": safety_case_id,
        "future_agent_scope": future_agent_scope,
        "current_evidence_anchor_de": current_evidence_anchor_de,
        "allowed_later_help_de": allowed_later_help_de,
        "required_human_gate_de": required_human_gate_de,
        "blocked_runtime_action_de": (
            blocked_runtime_action_de
            + " Zusaetzlich: keine Runtime-Agenten, kein MCP, kein Model Routing, "
            "keine LLM-Metriken, keine Rohdaten-Prompts und keine Trading-Pfade."
        ),
        "proof_before_activation_de": proof_before_activation_de,
        "current_status": current_status,
    }


def _validate_safety_case(safety_case: pd.DataFrame) -> None:
    _require_columns(safety_case, SAFETY_CASE_COLUMNS, "agent pipeline safety case")
    if len(safety_case) != 7:
        raise ValueError("Agent pipeline safety case must contain seven rows.")
    if safety_case["safety_case_id"].duplicated().any():
        raise ValueError("Agent pipeline safety case contains duplicate IDs.")
    active = safety_case[
        safety_case["current_status"].astype(str).str.contains("active", case=False, na=False)
    ]
    if not active.empty:
        raise ValueError("Agent pipeline safety case must not activate runtime agents.")
    joined = "\n".join(safety_case.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Agent pipeline safety case must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "llm_audit_log",
        "bounded",
        "max 50 rows",
        "keine runtime-agenten",
        "kein mcp",
        "kein model routing",
        "keine llm-metriken",
        "keine rohdaten-prompts",
        "keine trading-pfade",
        "source review",
        "5 tabellen",
        "4 figuren",
        "23 h1-h2-h3 review-zeilen",
        "0 aktive rows",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Agent pipeline safety case missing guardrail terms: " + ", ".join(missing))


def _render_doc(safety_case: pd.DataFrame) -> str:
    status_counts = safety_case["current_status"].value_counts().to_dict()
    display = safety_case[
        [
            "safety_case_id",
            "future_agent_scope",
            "current_evidence_anchor_de",
            "allowed_later_help_de",
            "required_human_gate_de",
            "current_status",
        ]
    ]
    return (
        "# Thesis Agent Pipeline Safety Case\n\n"
        "Dieses Kontrollartefakt beantwortet, wie die Pipeline spaeter mit "
        "Agenten verbessert werden koennte, ohne im aktuellen BA-Kern Agenten "
        "zu aktivieren. Es liest nur bestehende deterministische Artefakte und "
        "setzt keine Source-Review-, Swiss- oder DOCX-Gates auf final-ready.\n\n"
        "## Counts\n\n"
        f"- Safety case rows: {len(safety_case)}\n"
        f"- Documentation-only rows: {int(status_counts.get('future_documentation_only', 0))}\n"
        f"- Deferred rows: {int(status_counts.get('future_deferred', 0))}\n"
        "- Active runtime rows: 0\n\n"
        "## Safety Sequence\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Full Guardrail Matrix\n\n"
        + _markdown_table(safety_case)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Artefakt nur als Future-Work-Sicherheitsfall. Spaetere "
        "Agenten duerfen erst mit separatem Goal, Tests, bounded inputs, "
        "max 50 rows, Proof-Artefakt und `llm_audit_log` spezifiziert werden. "
        "Bis dahin bleiben Runtime-Agenten, MCP, Model Routing, LLM-Metriken, "
        "Rohdaten-Prompts, Wallet-Adress-Exposition by default und Trading-Pfade "
        "deaktiviert.\n"
    )


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    headers = list(frame.columns)
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for record in frame.fillna("").to_dict(orient="records"):
        rows.append("| " + " | ".join(_escape_cell(record[column]) for column in headers) + " |")
    return "\n".join(rows)


def _escape_cell(value: object) -> str:
    return str(value).replace("|", ",").replace("\n", " ")


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required safety-case input missing: {path}")
    return pd.read_csv(path)


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


if __name__ == "__main__":
    raise SystemExit(main())
