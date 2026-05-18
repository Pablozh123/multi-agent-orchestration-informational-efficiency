"""Run deterministic-core project guardrail checks."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
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
    matches: list[str] = []
    for path in _python_files(repo_root / "operations"):
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if pattern.search(line):
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")
    if matches:
        return CheckResult("restricted claim wording", False, "; ".join(matches))
    return CheckResult("restricted claim wording", True, "no restricted claim wording in operations")


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


def _check_pytest(repo_root: Path, skip_reason: str | None) -> CheckResult:
    if skip_reason:
        return CheckResult("pytest", True, f"skipped with reason: {skip_reason}")
    result = run_command((sys.executable, "-m", "pytest", "-q"), repo_root, 180)
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
