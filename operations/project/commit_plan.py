"""Suggest logical commit groups from the current git diff."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from operations.project.init import (
    detect_risky_mixed_changes,
    expand_directory_paths,
    find_repo_root,
    group_changed_paths,
    parse_name_status,
    parse_status_paths,
    run_command,
    suggest_commit_message,
    unique_paths,
)


def render_commit_plan(repo_root: Path) -> str:
    """Return a commit-plan report without staging or committing."""

    if not (repo_root / ".git").exists():
        return f"FAIL: {repo_root} is not a git repository root"

    name_status = run_command(("git", "diff", "--name-status"), repo_root)
    status_short = run_command(("git", "status", "--short"), repo_root)
    stat = run_command(("git", "diff", "--stat"), repo_root)
    if not name_status.ok:
        return f"FAIL: could not inspect git diff: {name_status.stderr or name_status.stdout}"
    if not status_short.ok:
        return f"FAIL: could not inspect git status: {status_short.stderr or status_short.stdout}"

    paths = expand_directory_paths(
        repo_root,
        unique_paths(
            [
                *parse_name_status(name_status.stdout),
                *parse_status_paths(status_short.stdout),
            ]
        ),
    )
    if not paths:
        return "No unstaged file changes detected."

    groups = group_changed_paths(paths)
    lines: list[str] = ["File groups:"]
    for group, files in groups.items():
        lines.append(f"\n[{group}]")
        for file_path in files:
            lines.append(f"- {file_path}")

    lines.append("\nSuggested commit messages:")
    for group in groups:
        lines.append(f"- {suggest_commit_message(group)}")

    warnings = detect_risky_mixed_changes(groups)
    lines.append("\nRisky mixed changes:")
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None detected.")

    lines.append("\nGit diff stat:")
    lines.append("```text")
    lines.append(stat.stdout if stat.ok and stat.stdout else "no diff stat")
    lines.append("```")
    lines.append("\nNote: untracked files are grouped from git status and do not appear in git diff --stat until staged.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = find_repo_root(args.repo_root)
    report = render_commit_plan(repo_root)
    print(report)
    return 1 if report.startswith("FAIL:") else 0


if __name__ == "__main__":
    raise SystemExit(main())
