"""Update STATUS.md with the current project automation snapshot."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Sequence

from operations.project.init import (
    ActiveGoal,
    CommandResult,
    detect_roadmap_phase,
    find_repo_root,
    format_bullet_list,
    parse_active_goal,
    read_text,
    replace_generated_block,
    run_command,
    write_text,
)


def _project_python() -> str:
    return sys.executable


def _git_value(repo_root: Path, *args: str) -> str:
    result = run_command(("git", *args), repo_root)
    return result.stdout if result.ok and result.stdout else "unavailable"


def _git_status(repo_root: Path) -> str:
    result = run_command(("git", "status", "--short"), repo_root)
    if not result.ok:
        return f"unavailable: {result.stderr or result.stdout}"
    return result.stdout or "clean"


def _git_diff_stat(repo_root: Path) -> str:
    result = run_command(("git", "diff", "--stat"), repo_root)
    if not result.ok:
        return f"unavailable: {result.stderr or result.stdout}"
    return result.stdout or "no unstaged diff"


def _pytest_result(repo_root: Path, skip_reason: str | None = None) -> CommandResult:
    if skip_reason:
        return CommandResult(("pytest", "skipped"), 0, f"skipped: {skip_reason}", "")
    return run_command((_project_python(), "-m", "pytest", "-q"), repo_root, 180)


def _derive_blockers(git_status: str, pytest_result: CommandResult, goal: ActiveGoal) -> list[str]:
    blockers: list[str] = []
    if git_status != "clean":
        blockers.append("Worktree has uncommitted changes that need review before commit.")
    if not pytest_result.ok:
        blockers.append("Pytest is failing; inspect output before continuing.")
    if goal.status.lower() not in {"active", "in progress"}:
        blockers.append(f"Active goal status is '{goal.status}', not active.")
    title = goal.title.lower()
    if "before h2" in title or "before h3" in title:
        blockers.append("Do not implement H2/H3 before the empirical scope deliverables are complete.")
    return blockers


def render_status_block(
    *,
    branch: str,
    latest_commit: str,
    git_status: str,
    diff_stat: str,
    pytest_result: CommandResult,
    goal: ActiveGoal,
    roadmap_phase: str,
) -> str:
    """Render the generated STATUS.md block."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    test_status = "PASS" if pytest_result.ok else "FAIL"
    blockers = _derive_blockers(git_status, pytest_result, goal)
    pytest_output = pytest_result.stdout.splitlines()[-1] if pytest_result.stdout else ""
    if not pytest_output and pytest_result.stderr:
        pytest_output = pytest_result.stderr.splitlines()[-1]

    return f"""## Automation Snapshot

Generated: {timestamp}

Current goal: `{goal.goal_id}` - {goal.title}

Current roadmap phase: {roadmap_phase}

Test status: {test_status}

Pytest summary: `{pytest_output or 'no pytest output'}`

Git branch: `{branch}`

Latest commit: `{latest_commit}`

Git status:

```text
{git_status}
```

Git diff stat:

```text
{diff_stat}
```

Blockers:

{format_bullet_list(blockers)}

Next recommended action:

- {goal.next_commit}
"""


def update_status(repo_root: Path, skip_pytest: str | None = None) -> str:
    """Update STATUS.md and return the generated block."""

    goal = parse_active_goal(read_text(repo_root / "GOAL.md"))
    roadmap_text = read_text(repo_root / "ROADMAP.md")
    roadmap_phase = detect_roadmap_phase(roadmap_text, goal)
    branch = _git_value(repo_root, "branch", "--show-current")
    latest_commit = _git_value(repo_root, "log", "-1", "--format=%h")
    git_status = _git_status(repo_root)
    diff_stat = _git_diff_stat(repo_root)
    pytest_result = _pytest_result(repo_root, skip_pytest)

    block = render_status_block(
        branch=branch,
        latest_commit=latest_commit,
        git_status=git_status,
        diff_stat=diff_stat,
        pytest_result=pytest_result,
        goal=goal,
        roadmap_phase=roadmap_phase,
    )
    status_path = repo_root / "STATUS.md"
    updated = replace_generated_block(read_text(status_path), block)
    write_text(status_path, updated)
    return block


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
    repo_root = find_repo_root(args.repo_root)
    if args.skip_pytest is not None and not args.skip_pytest.strip():
        parser.error("--skip-pytest requires a non-empty reason")
    try:
        block = update_status(repo_root, args.skip_pytest)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: STATUS.md updated")
    print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
