"""Build a final-gate board for thesis submission readiness."""

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

FINAL_GATE_OUTPUT = "thesis_final_gate_board.csv"
FINAL_GATE_DOC_OUTPUT = "THESIS_FINAL_GATE_BOARD.md"

FINAL_GATE_COLUMNS: tuple[str, ...] = (
    "final_gate_id",
    "gate_area",
    "current_status",
    "draft_use_allowed",
    "final_submission_ready",
    "blocking_scope",
    "evidence_count",
    "blocking_count",
    "evidence_artifacts",
    "key_evidence_de",
    "draft_permission_de",
    "final_submission_rule_de",
    "required_next_action_de",
    "blocked_actions_de",
)


@dataclass(frozen=True)
class ThesisFinalGateBoardResult:
    """Generated final-gate board paths and counts."""

    board_path: Path
    docs_path: Path
    board_rows: int
    final_not_ready_rows: int
    final_ready_rows: int
    draft_allowed_rows: int
    active_agent_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "board_path": str(self.board_path),
            "docs_path": str(self.docs_path),
            "board_rows": self.board_rows,
            "final_not_ready_rows": self.final_not_ready_rows,
            "final_ready_rows": self.final_ready_rows,
            "draft_allowed_rows": self.draft_allowed_rows,
            "active_agent_rows": self.active_agent_rows,
        }


def generate_thesis_final_gate_board(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> ThesisFinalGateBoardResult:
    """Generate the final-gate board CSV and Markdown."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)

    readiness = _read_csv(results_dir / "thesis_submission_readiness_board.csv")
    source_ledger = _read_csv(results_dir / "thesis_source_review_progress_ledger.csv")
    drafting = _read_csv(results_dir / "thesis_h1_h2_h3_drafting_checklist.csv")
    result_package = _read_csv(results_dir / "thesis_result_package_traceability.csv")
    swiss_latest = _read_csv(results_dir / "swiss_referendum_10mio_latest_source_comparison.csv")
    swiss_final_case = _read_csv(results_dir / "swiss_referendum_10mio_final_case_study.csv")
    swiss_status = _read_json(results_dir / "swiss_referendum_10mio_running_status.json")
    agent_upgrade = _read_csv(results_dir / "thesis_agent_pipeline_upgrade_plan.csv")

    board = build_thesis_final_gate_board(
        readiness=readiness,
        source_ledger=source_ledger,
        drafting=drafting,
        result_package=result_package,
        swiss_latest=swiss_latest,
        swiss_final_case=swiss_final_case,
        swiss_status=swiss_status,
        agent_upgrade=agent_upgrade,
        docx_exists=(repo_root / "docs/project/dozentenbericht_ba_thesis.docx").exists(),
    )
    _validate_board(board, repo_root=repo_root)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    board_path = results_dir / FINAL_GATE_OUTPUT
    docs_path = docs_dir / FINAL_GATE_DOC_OUTPUT
    board.to_csv(board_path, index=False)
    docs_path.write_text(_render_board_doc(board), encoding="utf-8")

    return ThesisFinalGateBoardResult(
        board_path=board_path,
        docs_path=docs_path,
        board_rows=len(board),
        final_not_ready_rows=int((~board["final_submission_ready"].map(_bool_value)).sum()),
        final_ready_rows=int(board["final_submission_ready"].map(_bool_value).sum()),
        draft_allowed_rows=int(board["draft_use_allowed"].map(_bool_value).sum()),
        active_agent_rows=_active_agent_rows(agent_upgrade),
    )


def build_thesis_final_gate_board(
    *,
    readiness: pd.DataFrame,
    source_ledger: pd.DataFrame,
    drafting: pd.DataFrame,
    result_package: pd.DataFrame,
    swiss_latest: pd.DataFrame,
    swiss_final_case: pd.DataFrame,
    swiss_status: dict[str, object],
    agent_upgrade: pd.DataFrame,
    docx_exists: bool = True,
) -> pd.DataFrame:
    """Return the final gate board for the current thesis consolidation state."""

    _require_columns(readiness, ("gate_area", "current_status"), "submission readiness board")
    _require_columns(
        source_ledger,
        ("review_progress_state", "final_citation_ready", "source_status_change_allowed"),
        "source review progress ledger",
    )
    _require_columns(
        drafting,
        ("completion_status", "ready_for_bounded_draft", "ready_for_final_submission"),
        "H1-H2-H3 drafting checklist",
    )
    _require_columns(
        result_package,
        ("package_type", "include_in_core_package", "package_traceability_status"),
        "result package traceability",
    )
    _require_columns(
        swiss_latest,
        ("polymarket_snapshot_at_utc", "polymarket_yes_probability", "valuation_scope"),
        "Swiss latest source comparison",
    )
    _require_columns(
        swiss_final_case,
        (
            "official_yes_share",
            "latest_live_polymarket_yes_probability",
            "live_observation_rows",
            "live_polymarket_beats_raw_vote_share_count",
            "live_polymarket_beats_raw_binary_proxy_count",
            "history_polymarket_beats_raw_vote_share_count",
            "history_observation_rows",
        ),
        "Swiss final case study",
    )
    _require_columns(agent_upgrade, ("current_status",), "agent pipeline upgrade plan")

    readiness_status = readiness.set_index("gate_area")["current_status"].to_dict()
    ledger_rows = int(len(source_ledger))
    ledger_pending = int((source_ledger["review_progress_state"] == "pending_manual_review").sum())
    ledger_final_ready = int(source_ledger["final_citation_ready"].map(_bool_value).sum())
    ledger_status_changes = int(source_ledger["source_status_change_allowed"].map(_bool_value).sum())
    drafting_rows = int(len(drafting))
    drafting_bounded_ready = int(drafting["ready_for_bounded_draft"].map(_bool_value).sum())
    drafting_final_ready = int(drafting["ready_for_final_submission"].map(_bool_value).sum())
    drafting_final_blocked = int(
        drafting["completion_status"].astype(str).str.startswith("final_blocked").sum()
    )
    core_package = result_package[result_package["include_in_core_package"].map(_bool_value)]
    core_tables = int((core_package["package_type"] == "table").sum())
    core_figures = int((core_package["package_type"] == "figure").sum())
    package_gaps = int(
        result_package["package_traceability_status"].astype(str).str.contains("gap", case=False, na=False).sum()
    )
    latest_snapshot = str(swiss_latest["polymarket_snapshot_at_utc"].iloc[0])
    # Bewusst berechnet, aber nicht ausgegeben: die Zugriffe validieren die
    # Spalten (fehlend oder unparsbar => Abbruch statt stiller Luecke).
    _latest_yes = float(swiss_latest["polymarket_yes_probability"].iloc[0])
    _valuation_scopes = "; ".join(sorted(set(swiss_latest["valuation_scope"].astype(str))))
    active_agents = _active_agent_rows(agent_upgrade)
    if active_agents:
        raise ValueError("Future agent upgrade plan must not activate runtime agents.")
    documentation_only_agents = int(
        agent_upgrade["current_status"].astype(str).str.contains("documentation", case=False, na=False).sum()
    )
    swiss_status_block = swiss_status.get("status", {})
    if not isinstance(swiss_status_block, dict):
        raise ValueError("Swiss running status JSON missing status object.")
    _snapshot_row_count = _int_from_mapping(
        swiss_status_block,
        "snapshot_row_count",
        default=len(swiss_latest),
    )
    snapshot_recency_status = str(swiss_status_block.get("snapshot_recency_status", "unknown"))
    docx_evidence_count = 1 if docx_exists else 0
    swiss_final_row = swiss_final_case.iloc[0]

    rows = [
        _gate_row(
            final_gate_id="final_gate_01_source_review",
            gate_area="source_review",
            current_status="final_blocked_source_review_pending",
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="final_submission",
            evidence_count=ledger_rows,
            blocking_count=ledger_pending,
            evidence_artifacts=(
                "data/results/thesis_source_review_progress_ledger.csv; "
                "docs/project/THESIS_SOURCE_REVIEW_PROGRESS_LEDGER.md"
            ),
            key_evidence_de=(
                f"Source Review Ledger: {ledger_rows} Zeilen; pending: {ledger_pending}; "
                f"final-ready: {ledger_final_ready}; Quellenstatus-Aenderungen erlaubt: {ledger_status_changes}."
            ),
            draft_permission_de="Draft erlaubt mit sichtbarem Pending-Gate.",
            final_submission_rule_de="Finale Zitation erst nach vollstaendigem manuellem Source Review.",
            required_next_action_de="Page-/Section-Notes, Claim-Support, Blocked-Wording und Citation-Use je Quelle erfassen.",
            blocked_actions_de="Keine finale Zitation, keine Quellenstatus-Hochstufung und keine automatische Page Note.",
        ),
        _gate_row(
            final_gate_id="final_gate_02_h1_h2_h3_drafting",
            gate_area="h1_h2_h3_drafting",
            current_status="draft_ready_final_source_review_pending",
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="final_submission",
            evidence_count=drafting_rows,
            blocking_count=drafting_final_blocked,
            evidence_artifacts=(
                "data/results/thesis_h1_h2_h3_drafting_checklist.csv; "
                "docs/project/THESIS_H1_H2_H3_DRAFTING_CHECKLIST.md"
            ),
            key_evidence_de=(
                f"Drafting Checklist: {drafting_rows} Checks; bounded-draft-ready: "
                f"{drafting_bounded_ready}; final-ready: {drafting_final_ready}; "
                f"final-blocked: {drafting_final_blocked}."
            ),
            draft_permission_de="Draft erlaubt entlang H1-H2-H3 Drafting Checklist.",
            final_submission_rule_de="Finale Kapitel erst nach Source Review, Wording Guard und finaler QA freigeben.",
            required_next_action_de="H1-H2-H3 Kapitel in der festen Reihenfolge schreiben und Gates sichtbar halten.",
            blocked_actions_de="Keine neue Kennzahl, keine Rohartefakt-Dumps und keine Ueberclaims.",
        ),
        _gate_row(
            final_gate_id="final_gate_03_result_package",
            gate_area="result_package",
            current_status="draft_ready_layout_and_citation_qa_pending",
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="layout_and_final_qa",
            evidence_count=core_tables + core_figures,
            blocking_count=package_gaps + 1,
            evidence_artifacts=(
                "data/results/thesis_result_package_traceability.csv; "
                "docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md"
            ),
            key_evidence_de=(
                f"Kernpaket: {core_tables} Tabellen und {core_figures} Figuren; Package gaps: {package_gaps}."
            ),
            draft_permission_de="Draft erlaubt mit kuratiertem Tabellen-/Figurenpaket.",
            final_submission_rule_de="Finale Nummerierung, Caption-Check und Layout-QA vor Export abschliessen.",
            required_next_action_de="Nur kuratierte Tabellen/Figuren integrieren und Caption/Limitation gegenpruefen.",
            blocked_actions_de="Keine Rohartefakt-Dumps und keine zusaetzlichen Tabellen/Figuren ohne Map-Update.",
        ),
        _gate_row(
            final_gate_id="final_gate_04_swiss_result_mapping",
            gate_area="swiss_result_gate",
            current_status=str(readiness_status.get("swiss_result_gate", "post_result_mapped_source_review_pending")),
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="final_submission_for_swiss_claims",
            evidence_count=int(swiss_final_row["live_observation_rows"]),
            blocking_count=1,
            evidence_artifacts=(
                "data/results/swiss_referendum_10mio_final_case_study.csv; "
                "data/results/swiss_referendum_10mio_final_case_study.png; "
                "docs/research/SWISS_REFERENDUM_FINAL_CASE_STUDY.md"
            ),
            key_evidence_de=(
                f"Offizielles Resultat vom 14. Juni 2026 gemappt: Ja-Anteil "
                f"{float(swiss_final_row['official_yes_share']):.3f}; latest live "
                f"Polymarket-Yes {float(swiss_final_row['latest_live_polymarket_yes_probability']):.3f}; "
                f"vote-share beats "
                f"{int(swiss_final_row['live_polymarket_beats_raw_vote_share_count'])}/"
                f"{int(swiss_final_row['live_observation_rows'])}; binary-proxy beats "
                f"{int(swiss_final_row['live_polymarket_beats_raw_binary_proxy_count'])}/"
                f"{int(swiss_final_row['live_observation_rows'])}; history raw beats "
                f"{int(swiss_final_row['history_polymarket_beats_raw_vote_share_count'])}/"
                f"{int(swiss_final_row['history_observation_rows'])}. "
                f"Latest running snapshot audit: {latest_snapshot}; recency: {snapshot_recency_status}."
            ),
            draft_permission_de="Draft erlaubt als bounded Post-Resultat-Side-Track.",
            final_submission_rule_de="Finale Swiss-Zitation erst nach Source Review und sichtbarer Poll-Proxy-Limitation.",
            required_next_action_de="Swiss-Abschnitt mit Stimmenanteils- und Binaer-Proxy-Trennung schreiben.",
            blocked_actions_de="Keine Swiss-Effizienz-, Mispricing-, Tradeability- oder Polymarket-Stimmenanteilsueberlegenheitsclaims.",
        ),
        _gate_row(
            final_gate_id="final_gate_05_monitor_appendix",
            gate_area="monitor_appendix",
            current_status=str(readiness_status.get("monitor_appendix", "appendix_only_pending_human_review")),
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="thesis_core_claims",
            evidence_count=1,
            blocking_count=1,
            evidence_artifacts=(
                "data/results/monitor_anomaly_review_summary.csv; "
                "data/results/thesis_submission_readiness_board.csv"
            ),
            key_evidence_de="Monitor bleibt Appendix/Prototype und pending human review.",
            draft_permission_de="Draft erlaubt nur als read-only Prototype oder Appendix-Grenze.",
            final_submission_rule_de="Keine thesis-facing Alert-Evidenz ohne Human Review und thesis-use Gate.",
            required_next_action_de="Monitor nur begrenzt erwaehnen oder aus dem Kern herauslassen.",
            blocked_actions_de="Keine Wallet-Adress-Exposition, keine Order-/Trading-Pfade und keine Kausalclaims.",
        ),
        _gate_row(
            final_gate_id="final_gate_06_future_agents",
            gate_area="future_agents",
            current_status=str(readiness_status.get("agent_future_work", "deferred_future_work_only")),
            draft_use_allowed=True,
            final_submission_ready=True,
            blocking_scope="runtime_activation",
            evidence_count=len(agent_upgrade),
            blocking_count=active_agents,
            evidence_artifacts=(
                "data/results/thesis_agent_pipeline_upgrade_plan.csv; "
                "docs/research/THESIS_AGENT_PIPELINE_UPGRADE_PLAN.md"
            ),
            key_evidence_de=(
                f"Agent upgrade rows: {len(agent_upgrade)}; documentation-only: "
                f"{documentation_only_agents}; aktive Agenten: {active_agents}."
            ),
            draft_permission_de="Draft erlaubt nur als Future-Work-Design.",
            final_submission_rule_de="Agenten nicht aktivieren; spaeter nur mit separatem Goal, Tests und llm_audit_log.",
            required_next_action_de="Agentenabschnitt als Pipeline-Ausblick schreiben, nicht implementieren.",
            blocked_actions_de="Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Rohdaten-Prompts.",
        ),
        _gate_row(
            final_gate_id="final_gate_07_docx_render_qa",
            gate_area="docx_render_qa",
            current_status=str(readiness_status.get("final_qa", "pending_after_draft")),
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="final_export",
            evidence_count=docx_evidence_count,
            blocking_count=1,
            evidence_artifacts="STATUS.md; docs/project/WORK_LOG.md; docs/project/dozentenbericht_ba_thesis.docx",
            key_evidence_de=(
                f"DOCX-Render-QA bleibt finaler Export- und Layout-Gate; DOCX exists: {docx_exists}."
            ),
            draft_permission_de="Draft erlaubt; finale Abgabe nicht ohne Render-/Layout-QA.",
            final_submission_rule_de="Vor finalem Export DOCX/PDF rendern und Layout visuell pruefen.",
            required_next_action_de="Nach Kapitel-Draft Render-QA, Caption-QA, Source Review und Swiss-Gate wiederholen.",
            blocked_actions_de="Keine finale Abgabebereitschaft behaupten, solange Render-QA offen ist.",
        ),
        _gate_row(
            final_gate_id="final_gate_08_project_control",
            gate_area="project_control",
            current_status="project_checks_pass_current_slice",
            draft_use_allowed=True,
            final_submission_ready=False,
            blocking_scope="stop_or_commit",
            evidence_count=2,
            blocking_count=1,
            evidence_artifacts="STATUS.md; docs/project/WORK_LOG.md",
            key_evidence_de="Project control requires update_status, WORK_LOG, review_check, commit_plan and clean diff.",
            draft_permission_de="Draft erlaubt, wenn Projektchecks gruen bleiben.",
            final_submission_rule_de="Vor finaler Abgabe alle Projektchecks und offenen Gates erneut pruefen.",
            required_next_action_de="Nach jedem Slice Status, Work Log, Review-Check und Commit-Plan ausfuehren.",
            blocked_actions_de="Nicht behaupten, dass die Thesis final abgabebereit ist, solange Finalgates offen sind.",
        ),
    ]
    return pd.DataFrame(rows, columns=FINAL_GATE_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_thesis_final_gate_board(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _validate_board(board: pd.DataFrame, *, repo_root: Path) -> None:
    _require_columns(board, FINAL_GATE_COLUMNS, "thesis final gate board")
    if len(board) != 8:
        raise ValueError("Thesis final gate board must contain 8 rows.")
    if board["final_gate_id"].duplicated().any():
        raise ValueError("Thesis final gate board contains duplicate final_gate_id values.")
    for column in FINAL_GATE_COLUMNS:
        if board[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Thesis final gate board contains empty {column}.")
    if not board["draft_use_allowed"].map(_bool_value).all():
        raise ValueError("Thesis final gate board currently expects all gates to allow bounded draft work.")
    final_ready = board["final_submission_ready"].map(_bool_value)
    if final_ready.all():
        raise ValueError("Thesis final gate board must keep final blockers visible.")
    mandatory_final_false = {
        "final_gate_01_source_review",
        "final_gate_04_swiss_result_mapping",
        "final_gate_07_docx_render_qa",
    }
    actual_final_true = set(board.loc[final_ready, "final_gate_id"].astype(str))
    wrongly_ready = sorted(mandatory_final_false.intersection(actual_final_true))
    if wrongly_ready:
        raise ValueError("Mandatory final gates must remain blocked: " + ", ".join(wrongly_ready))
    if not board["evidence_count"].map(_non_negative_int).all():
        raise ValueError("Thesis final gate board evidence_count must be non-negative integers.")
    if not board["blocking_count"].map(_non_negative_int).all():
        raise ValueError("Thesis final gate board blocking_count must be non-negative integers.")
    for artifacts in board["evidence_artifacts"].astype(str):
        for artifact in _split_semicolon(artifacts):
            if not (repo_root / artifact).exists():
                raise FileNotFoundError(f"Thesis final gate board artifact missing: {artifact}")
    joined = "\n".join(board.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Thesis final gate board must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "source review",
        "keine finale zitation",
        "swiss",
        "offizielles resultat",
        "docx",
        "review_check",
        "keine runtime-agenten",
        "llm_audit_log",
        "keine rohartefakt-dumps",
        "keine finale abgabebereitschaft",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Thesis final gate board missing required terms: " + ", ".join(missing))


def _render_board_doc(board: pd.DataFrame) -> str:
    final_ready = int(board["final_submission_ready"].map(_bool_value).sum())
    final_not_ready = int((~board["final_submission_ready"].map(_bool_value)).sum())
    draft_allowed = int(board["draft_use_allowed"].map(_bool_value).sum())
    total_blockers = int(board["blocking_count"].astype(int).sum())
    return (
        "# Thesis Final Gate Board\n\n"
        "Dieses Board ist die Stop-/Go-Kontrolle vor finaler BA-Abgabe. Es "
        "fasst die vorhandenen deterministischen Artefakte zusammen und macht "
        "sichtbar, dass Draft-Arbeit weitergehen darf, die finale Abgabe aber "
        "durch Source Review, Swiss Source-/Citation-Gate, DOCX-Render-QA und finale "
        "Projektchecks blockiert bleibt. Es liest keine Quelleninhalte, "
        "berechnet keine Kennzahlen und aktiviert keine Runtime-Agenten.\n\n"
        "## Counts\n\n"
        f"- Final gate rows: {len(board)}\n"
        f"- Draft allowed rows: {draft_allowed}\n"
        f"- Final ready rows: {final_ready}\n"
        f"- Final not ready rows: {final_not_ready}\n"
        f"- Blocking count total: {total_blockers}\n\n"
        "## Gate Rows\n\n"
        + _markdown_table(board)
        + "\n\n"
        "## Use Rule\n\n"
        "Nutze dieses Board vor jedem Claim zur Abgabebereitschaft. Solange "
        "Source Review, Swiss Source-/Citation-Gate, DOCX-Render-QA oder finale "
        "Projektchecks offen sind, darf nur bounded draft readiness behauptet "
        "werden. Keine finale Zitation, keine Rohartefakt-Dumps, keine "
        "Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein "
        "Model Routing, keine LLM-Metriken und keine Trading-Pfade.\n"
    )


def _gate_row(
    *,
    final_gate_id: str,
    gate_area: str,
    current_status: str,
    draft_use_allowed: bool,
    final_submission_ready: bool,
    blocking_scope: str,
    evidence_count: int,
    blocking_count: int,
    evidence_artifacts: str,
    key_evidence_de: str,
    draft_permission_de: str,
    final_submission_rule_de: str,
    required_next_action_de: str,
    blocked_actions_de: str,
) -> dict[str, object]:
    return {
        "final_gate_id": final_gate_id,
        "gate_area": gate_area,
        "current_status": current_status,
        "draft_use_allowed": draft_use_allowed,
        "final_submission_ready": final_submission_ready,
        "blocking_scope": blocking_scope,
        "evidence_count": evidence_count,
        "blocking_count": blocking_count,
        "evidence_artifacts": evidence_artifacts,
        "key_evidence_de": key_evidence_de,
        "draft_permission_de": draft_permission_de,
        "final_submission_rule_de": final_submission_rule_de,
        "required_next_action_de": required_next_action_de,
        "blocked_actions_de": blocked_actions_de,
    }


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ja"}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis final gate board input missing: {path}")
    return pd.read_csv(path)


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Required thesis final gate board input missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Required thesis final gate board JSON must be an object: {path}")
    return data


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _active_agent_rows(agent_upgrade: pd.DataFrame) -> int:
    allowed_statuses = {
        "future_documentation_only",
        "future_deferred",
        "deferred_future_work_only",
    }
    statuses = agent_upgrade["current_status"].astype(str).str.strip()
    return int((~statuses.isin(allowed_statuses)).sum())


def _int_from_mapping(mapping: dict[str, object], key: str, *, default: int) -> int:
    value = mapping.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Swiss running status {key} must be an integer.") from exc


def _non_negative_int(value: object) -> bool:
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def _split_semicolon(value: str) -> list[str]:
    if value.lower() == "nan":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


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
