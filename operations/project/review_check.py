"""Run deterministic-core project guardrail checks."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Callable, Sequence

from operations.project.init import (
    count_active_goals,
    find_repo_root,
    parse_active_goal,
    read_text,
    run_command,
)


@dataclass(frozen=True)
class CheckResult:
    """One review-check result."""

    name: str
    passed: bool
    message: str


def _python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _check_required_docs(repo_root: Path) -> CheckResult:
    required = ["GOAL.md", "AGENTS.md", "STATUS.md", "ROADMAP.md"]
    missing = [name for name in required if not (repo_root / name).exists()]
    if missing:
        return CheckResult("required docs", False, f"missing: {', '.join(missing)}")
    return CheckResult("required docs", True, "all required control docs exist")


def _check_single_goal(repo_root: Path) -> CheckResult:
    goal_path = repo_root / "GOAL.md"
    goal_text = read_text(goal_path)
    count = count_active_goals(goal_text)
    if count != 1:
        return CheckResult("active goal", False, f"expected exactly one active goal, found {count}")
    goal = parse_active_goal(goal_text)
    return CheckResult("active goal", True, f"{goal.goal_id}: {goal.title}")


def _check_no_select_star(repo_root: Path) -> CheckResult:
    pattern = re.compile(r"SELECT\s+\*", re.IGNORECASE)
    matches: list[str] = []
    for path in _python_files(repo_root / "operations"):
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if pattern.search(line):
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")
    if matches:
        return CheckResult("sql select star", False, "; ".join(matches))
    return CheckResult("sql select star", True, "no SELECT star pattern found in operations")


def _check_no_restricted_claim_wording(repo_root: Path) -> CheckResult:
    word = "inside" + "r"
    pattern = re.compile(rf"\b{word}\b", re.IGNORECASE)
    blocked_fragments = (
        f"confirmed {word}",
        f"{word} wallet",
        f"{word} trader",
        f"{word} trading",
        f"proof of {word}",
        f"proof, {word}",
    )
    allowed_fragments = (
        f"{word}-risk",
        f"{word}_risk",
        f"{word} risk",
        f"computed {word} label",
        f"not a computed {word} label",
        f"not_a_computed_{word}_label",
        f"contains_computed_{word}_label",
    )
    matches: list[str] = []
    for path in _python_files(repo_root / "operations"):
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            lowered = line.lower()
            if not pattern.search(line):
                continue
            blocked = any(fragment in lowered for fragment in blocked_fragments)
            allowed = any(fragment in lowered for fragment in allowed_fragments)
            if blocked or not allowed:
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")
    if matches:
        return CheckResult("restricted claim wording", False, "; ".join(matches))
    return CheckResult(
        "restricted claim wording",
        True,
        "restricted wording absent or limited to insider-risk review labels",
    )


def _check_rcp_guard(repo_root: Path) -> CheckResult:
    matches: list[str] = []
    analysis_root = repo_root / "operations" / "analysis"
    for path in _python_files(analysis_root):
        text = read_text(path)
        if re.search(r"include_rcp\s*:\s*bool\s*=\s*True", text):
            matches.append(f"{path.relative_to(repo_root)}: include_rcp defaults to True")
        if "RCP_SOURCE" in text and "rcp_transformation_documented" not in text:
            matches.append(f"{path.relative_to(repo_root)}: RCP source without documentation flag")
    if matches:
        return CheckResult("rcp guard", False, "; ".join(matches))
    return CheckResult("rcp guard", True, "RCP usage remains guarded in analysis modules")


def _check_no_fixed_whale_threshold(repo_root: Path) -> CheckResult:
    threshold = "10" + "000"
    threshold_with_underscore = "10_" + "000"
    threshold_with_comma = "10," + "000"
    pattern = re.compile(
        rf"({threshold}|{re.escape(threshold_with_underscore)}|{re.escape(threshold_with_comma)})",
        re.IGNORECASE,
    )
    matches: list[str] = []
    for path in _python_files(repo_root / "operations"):
        text = read_text(path)
        if "whale" not in text.lower():
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")
    if matches:
        return CheckResult("fixed whale threshold", False, "; ".join(matches))
    return CheckResult("fixed whale threshold", True, "no fixed numeric whale threshold in operations")


def _marker_value(text: str, marker: str) -> str | None:
    pattern = re.compile(
        rf"(?im)^\s*-\s*{re.escape(marker)}:\s*(?P<value>.+?)\s*$"
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group("value").strip().strip("`").lower()


def _read_research_doc(repo_root: Path, filename: str) -> tuple[Path, str | None]:
    path = repo_root / "docs" / "research" / filename
    if not path.exists():
        return path, None
    return path, read_text(path)


def _analysis_matches(
    repo_root: Path,
    *,
    filename_terms: tuple[str, ...],
    text_terms: tuple[str, ...],
) -> list[str]:
    matches: list[str] = []
    analysis_root = repo_root / "operations" / "analysis"
    if not analysis_root.exists():
        return matches

    for path in _python_files(analysis_root):
        normalized_name = path.name.lower().replace("-", "_")
        text = read_text(path).lower()
        if any(term in normalized_name for term in filename_terms) or any(
            term in text for term in text_terms
        ):
            matches.append(str(path.relative_to(repo_root)))
    return matches


def _operations_matches(
    repo_root: Path,
    *,
    filename_terms: tuple[str, ...],
    text_terms: tuple[str, ...],
) -> list[str]:
    matches: list[str] = []
    operations_root = repo_root / "operations"
    if not operations_root.exists():
        return matches

    for path in _python_files(operations_root):
        if "project" in path.relative_to(operations_root).parts:
            continue
        normalized_name = path.name.lower().replace("-", "_")
        text = read_text(path).lower()
        if any(term in normalized_name for term in filename_terms) or any(
            term in text for term in text_terms
        ):
            matches.append(str(path.relative_to(repo_root)))
    return matches


def _check_empirical_decision_markers(repo_root: Path) -> CheckResult:
    docs = {
        "EVENT_SELECTION.md": ("h2_window_status", {"blocked", "candidate", "selected"}),
        "WHALE_METHOD.md": ("h3_tier_status", {"blocked", "candidate", "selected"}),
        "RESEARCH_SPEC.md": ("ml_scope_status", {"deferred", "candidate", "selected"}),
    }
    missing_or_invalid: list[str] = []

    for filename, (marker, allowed_values) in docs.items():
        path, text = _read_research_doc(repo_root, filename)
        if text is None:
            missing_or_invalid.append(f"{path.relative_to(repo_root)} missing")
            continue
        value = _marker_value(text, marker)
        if value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            missing_or_invalid.append(
                f"{path.relative_to(repo_root)} {marker} must be one of: {allowed}"
            )

    if missing_or_invalid:
        return CheckResult("empirical decision markers", False, "; ".join(missing_or_invalid))
    return CheckResult("empirical decision markers", True, "H2, H3, and ML markers are present")


def _check_h2_window_guard(repo_root: Path) -> CheckResult:
    _, text = _read_research_doc(repo_root, "EVENT_SELECTION.md")
    h2_status = _marker_value(text or "", "h2_window_status")
    matches = _analysis_matches(
        repo_root,
        filename_terms=("car", "event_study", "eventstudy"),
        text_terms=("cumulative abnormal return", "event study"),
    )
    if matches and h2_status != "selected":
        return CheckResult(
            "h2 window guard",
            False,
            "H2 event-study code exists before h2_window_status is selected: "
            + "; ".join(matches),
        )
    return CheckResult("h2 window guard", True, f"h2_window_status={h2_status or 'missing'}")


def _check_h3_tier_guard(repo_root: Path) -> CheckResult:
    _, text = _read_research_doc(repo_root, "WHALE_METHOD.md")
    h3_status = _marker_value(text or "", "h3_tier_status")
    matches = _analysis_matches(
        repo_root,
        filename_terms=("granger", "lead_lag", "lead_time"),
        text_terms=("granger", "lead-lag", "lead lag", "lead-time", "lead time"),
    )
    if matches and h3_status != "selected":
        return CheckResult(
            "h3 tier guard",
            False,
            "H3 timing code exists before h3_tier_status is selected: "
            + "; ".join(matches),
        )
    return CheckResult("h3 tier guard", True, f"h3_tier_status={h3_status or 'missing'}")


def _deterministic_h1_h2_h3_outputs_exist(repo_root: Path) -> bool:
    result_root = repo_root / "data" / "results"
    if not result_root.exists():
        return False
    required_prefixes = ("h1", "h2", "h3")
    existing_names = [path.name.lower() for path in result_root.iterdir() if path.is_file()]
    return all(any(name.startswith(prefix) for name in existing_names) for prefix in required_prefixes)


def _check_ml_scope_guard(repo_root: Path) -> CheckResult:
    _, text = _read_research_doc(repo_root, "RESEARCH_SPEC.md")
    ml_status = _marker_value(text or "", "ml_scope_status")
    ml_matches = _operations_matches(
        repo_root,
        filename_terms=("ml", "machine_learning", "classifier", "model_training"),
        text_terms=(
            "machine learning",
            "sklearn",
            "tensorflow",
            "torch",
            "xgboost",
            "random forest",
        ),
    )

    if ml_matches and ml_status == "deferred":
        return CheckResult(
            "ml scope guard",
            False,
            "ML implementation exists while ml_scope_status is deferred: "
            + "; ".join(ml_matches),
        )
    if ml_status != "deferred" and not _deterministic_h1_h2_h3_outputs_exist(repo_root):
        return CheckResult(
            "ml scope guard",
            False,
            "ml_scope_status may only move beyond deferred after H1, H2, and H3 outputs exist",
        )
    return CheckResult("ml scope guard", True, f"ml_scope_status={ml_status or 'missing'}")


def _check_runtime_agent_guards(repo_root: Path) -> CheckResult:
    guarded_paths = [
        repo_root / "operations" / "agents" / "market_agent.py",
        repo_root / "operations" / "agents" / "sentiment_agent.py",
        repo_root / "operations" / "agents" / "whale_agent.py",
        repo_root / "operations" / "agents" / "orchestrator.py",
        repo_root / "operations" / "mcp" / "thesis_mcp_server.py",
    ]
    failures: list[str] = []
    for path in guarded_paths:
        if not path.exists():
            failures.append(f"{path.relative_to(repo_root)} missing")
            continue
        text = read_text(path)
        if "DEFERRED_MESSAGE" not in text or "RuntimeError" not in text:
            failures.append(f"{path.relative_to(repo_root)} missing deferred runtime guard")
    if failures:
        return CheckResult("runtime agent guards", False, "; ".join(failures))
    return CheckResult(
        "runtime agent guards",
        True,
        "agent and MCP entry points remain guarded",
    )


def _check_strategy_architecture_contract(repo_root: Path) -> CheckResult:
    path = repo_root / "docs" / "research" / "STRATEGY_AGENT_ARCHITECTURE.md"
    if not path.exists():
        return CheckResult(
            "strategy architecture",
            False,
            "docs/research/STRATEGY_AGENT_ARCHITECTURE.md missing",
        )
    text = read_text(path).lower()
    required_terms = (
        "signal generator",
        "signalspec",
        "backtestconfig",
        "backtestresult",
        "llm_audit_log",
        "raw table dumps",
        "autonomous trading",
    )
    missing = [term for term in required_terms if term not in text]
    if missing:
        return CheckResult(
            "strategy architecture",
            False,
            "missing required contract terms: " + ", ".join(missing),
        )
    return CheckResult(
        "strategy architecture",
        True,
        "strategy prototype is scoped as bounded signal generation and Python backtesting",
    )


def _extract_labelled_block(text: str, label: str, stop_labels: Sequence[str]) -> str:
    """Return a Markdown block after a label until the next known label."""

    lower_text = text.lower()
    start = lower_text.find(label.lower())
    if start == -1:
        return ""
    body_start = text.find("\n", start)
    if body_start == -1:
        return ""

    stops = [
        lower_text.find(stop.lower(), body_start + 1)
        for stop in stop_labels
        if lower_text.find(stop.lower(), body_start + 1) != -1
    ]
    body_end = min(stops) if stops else len(text)
    return text[body_start:body_end]


def _check_monitor_v2_read_only_access_contract(repo_root: Path) -> CheckResult:
    doc_path = repo_root / "docs" / "research" / "STRATEGY_AGENT_ARCHITECTURE.md"
    if not doc_path.exists():
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "docs/research/STRATEGY_AGENT_ARCHITECTURE.md missing",
        )

    text = read_text(doc_path)
    lower_text = text.lower()
    required_terms = (
        "read-only monitor v2 summary access contract",
        "read-only summary access contract review",
        "default allowed artifacts",
        "blocked by default",
        "conditional access",
        "future audit requirements",
        "monitor_v2_bounded_summary.csv",
        "monitor_v2_bounded_summary_metadata.json",
        "raw row-level alert dumps",
        "scoring snapshots",
        "direct reads from `data/thesis.db`",
        "wallet-address fields",
        "unrestricted sql",
        "at most 50 rows",
        "llm_audit_log",
        "implementation deferred",
    )
    missing_terms = [term for term in required_terms if term not in lower_text]
    if missing_terms:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "missing access-contract terms: " + ", ".join(missing_terms),
        )

    default_block = _extract_labelled_block(
        text,
        "Default allowed artifacts:",
        ("Allowed by default:", "Blocked by default:", "Conditional access:"),
    ).lower()
    blocked_default_terms = (
        "monitor_v2_alert_rows.csv",
        "monitor_v2_historical_replay_alert_rows.csv",
        "monitor_v2_historical_replay_snapshots.csv",
        "monitor_v2_recorded_alert_rows.csv",
        "monitor_v2_recorded_scoring_snapshots.csv",
        "monitor_v2_recorded_watchlist.csv",
        "monitor_v2_recorded_market_snapshots.csv",
        "monitor_v2_recorded_wallet_tier_snapshots.csv",
        "monitor_v2_recorded_event_candidates.csv",
        "data/thesis.db",
    )
    exposed_raw_terms = [term for term in blocked_default_terms if term in default_block]
    if exposed_raw_terms:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "raw or database artifacts appear in default allowed block: "
            + ", ".join(exposed_raw_terms),
        )

    allowed_artifacts = (
        repo_root / "data" / "results" / "monitor_v2_bounded_summary.csv",
        repo_root / "data" / "results" / "monitor_v2_bounded_summary_metadata.json",
        repo_root / "data" / "results" / "thesis_monitor_v2_recorded_scoring.png",
        repo_root / "data" / "results" / "thesis_figures_metadata.json",
    )
    missing_artifacts = [
        str(path.relative_to(repo_root))
        for path in allowed_artifacts
        if not path.exists()
    ]
    if missing_artifacts:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "missing bounded summary artifacts: " + ", ".join(missing_artifacts),
        )

    summary_path = allowed_artifacts[0]
    try:
        with summary_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except csv.Error as exc:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            f"bounded summary CSV is invalid: {exc}",
        )

    fieldnames = set(reader.fieldnames or [])
    required_columns = {
        "summary_id",
        "summary_type",
        "source_artifact",
        "allowed_interpretation",
        "limitation",
        "claim_scope",
    }
    missing_columns = sorted(required_columns - fieldnames)
    if missing_columns:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "bounded summary missing columns: " + ", ".join(missing_columns),
        )
    if len(rows) > 50:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            f"bounded summary has {len(rows)} rows; default prompt surface max is 50",
        )
    if any(column.lower() == "wallet_address" for column in fieldnames):
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "bounded summary exposes wallet_address column",
        )
    wallet_pattern = re.compile(r"\b0x[a-f0-9]{6,}", re.IGNORECASE)
    if any(
        wallet_pattern.search(str(value))
        for row in rows
        for value in row.values()
        if value is not None
    ):
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "bounded summary appears to expose wallet-address-like values",
        )

    metadata_path = allowed_artifacts[1]
    try:
        metadata = json.loads(read_text(metadata_path))
    except json.JSONDecodeError as exc:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            f"bounded summary metadata is invalid JSON: {exc}",
        )
    outputs = metadata.get("outputs", {})
    if outputs.get("contains_wallet_addresses") is not False:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "metadata must declare contains_wallet_addresses=false",
        )
    if outputs.get("contains_order_instructions") is not False:
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            "metadata must declare contains_order_instructions=false",
        )
    summary_rows = outputs.get("summary_rows")
    if isinstance(summary_rows, int) and summary_rows != len(rows):
        return CheckResult(
            "monitor v2 access guardrails",
            False,
            f"metadata summary_rows={summary_rows} does not match CSV rows={len(rows)}",
        )

    return CheckResult(
        "monitor v2 access guardrails",
        True,
        f"bounded summary access is enforced for {len(rows)} rows",
    )


def _check_no_live_trading_implementation(repo_root: Path) -> CheckResult:
    patterns = (
        "live_trading",
        "live trading",
        "place_order",
        "execute_order",
        "market_order",
        "limit_order",
        "autonomous trader",
        "guaranteed profitable",
        "profit guarantee",
    )
    matches: list[str] = []
    for path in _python_files(repo_root / "operations"):
        if "project" in path.relative_to(repo_root / "operations").parts:
            continue
        text = read_text(path).lower()
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(pattern in line for pattern in patterns):
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")
    if matches:
        return CheckResult("live trading guard", False, "; ".join(matches))
    return CheckResult(
        "live trading guard",
        True,
        "no active live-trading or order-execution implementation found",
    )


def _check_active_prompt_metric_scope(repo_root: Path) -> CheckResult:
    prompt_root = repo_root / "directives" / "roles"
    if not prompt_root.exists():
        return CheckResult("active prompt metric scope", True, "no active role prompts found")

    failures: list[str] = []
    for path in sorted(prompt_root.glob("*.md")):
        text = read_text(path).lower()
        if "status: active" not in text:
            continue
        if "allowed scope: interpretation only, no deterministic calculations" not in text:
            failures.append(f"{path.relative_to(repo_root)} missing allowed scope header")
        if "do not calculate" not in text and "must not calculate" not in text:
            failures.append(f"{path.relative_to(repo_root)} missing no-calculation rule")
    if failures:
        return CheckResult("active prompt metric scope", False, "; ".join(failures))
    return CheckResult(
        "active prompt metric scope",
        True,
        "active prompts remain interpretation-only",
    )


def _check_pytest(repo_root: Path, skip_reason: str | None) -> CheckResult:
    if skip_reason:
        return CheckResult("pytest", True, f"skipped with reason: {skip_reason}")
    basetemp = repo_root / ".tmp_project_pytest"
    shutil.rmtree(basetemp, ignore_errors=True)
    basetemp.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TEMP"] = str(basetemp)
    env["TMP"] = str(basetemp)
    try:
        result = run_command(
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                ".tmp_project_pytest",
            ),
            repo_root,
            180,
            env=env,
        )
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
    if not result.ok:
        output = result.stdout or result.stderr or "pytest failed without output"
        return CheckResult("pytest", False, output.splitlines()[-1])
    summary = result.stdout.splitlines()[-1] if result.stdout else "pytest passed"
    return CheckResult("pytest", True, summary)


def run_checks(repo_root: Path, skip_pytest: str | None = None) -> list[CheckResult]:
    checks: list[Callable[[Path], CheckResult]] = [
        _check_required_docs,
        _check_single_goal,
        _check_no_select_star,
        _check_no_restricted_claim_wording,
        _check_rcp_guard,
        _check_no_fixed_whale_threshold,
        _check_empirical_decision_markers,
        _check_h2_window_guard,
        _check_h3_tier_guard,
        _check_ml_scope_guard,
        _check_runtime_agent_guards,
        _check_strategy_architecture_contract,
        _check_monitor_v2_read_only_access_contract,
        _check_no_live_trading_implementation,
        _check_active_prompt_metric_scope,
    ]
    results = [check(repo_root) for check in checks]
    results.append(_check_pytest(repo_root, skip_pytest))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--skip-pytest",
        metavar="REASON",
        default=None,
        help="Skip pytest only with an explicit reason.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.skip_pytest is not None and not args.skip_pytest.strip():
        parser.error("--skip-pytest requires a non-empty reason")
    repo_root = find_repo_root(args.repo_root)
    results = run_checks(repo_root, args.skip_pytest)
    for result in results:
        prefix = "PASS" if result.passed else "FAIL"
        print(f"{prefix}: {result.name} - {result.message}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
