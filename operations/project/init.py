"""Shared helpers for goal-driven project automation.

The helpers in this module are intentionally standard-library only. They are
used by the project-control CLIs and by tests that exercise those CLIs in
temporary repositories.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable, Sequence


STATUS_BLOCK_START = "<!-- PROJECT_STATUS:START -->"
STATUS_BLOCK_END = "<!-- PROJECT_STATUS:END -->"

GOAL_FIELDS = {
    "goal_id",
    "title",
    "status",
    "phase",
    "why",
    "deliverables",
    "scope",
    "out_of_scope",
    "acceptance_criteria",
    "next_commit",
}


@dataclass(frozen=True)
class CommandResult:
    """Result from a local command."""

    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class ActiveGoal:
    """Structured representation of the single active goal."""

    goal_id: str
    title: str
    status: str
    phase: str
    why: tuple[str, ...]
    deliverables: tuple[str, ...]
    scope: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    next_commit: str


def find_repo_root(start: Path | None = None) -> Path:
    """Return the nearest parent that contains .git, or the current path."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def run_command(
    args: Sequence[str],
    cwd: Path,
    timeout_seconds: int = 120,
) -> CommandResult:
    """Run a command and capture text output without raising."""

    try:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return CommandResult(tuple(args), 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CommandResult(tuple(args), 124, stdout, stderr or "command timed out")

    return CommandResult(
        tuple(args),
        completed.returncode,
        completed.stdout.rstrip(),
        completed.stderr.rstrip(),
    )


def read_text(path: Path) -> str:
    """Read UTF-8 text from a project file."""

    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text, creating parents when needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_active_goal_section(goal_text: str) -> str:
    """Return the body of the Active Goal section, if present."""

    match = re.search(
        r"(?ms)^##\s+Active Goal\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        goal_text,
    )
    return match.group("body").strip() if match else ""


def _append_field_value(fields: dict[str, object], key: str, value: str) -> None:
    current = fields.get(key)
    if isinstance(current, list):
        current.append(value)
    elif isinstance(current, str) and current:
        fields[key] = [current, value]
    else:
        fields[key] = [value]


def parse_active_goal(goal_text: str) -> ActiveGoal:
    """Parse GOAL.md and return the active goal.

    The preferred format is a single ``## Active Goal`` section with scalar
    fields and bullet-list fields. A small legacy fallback keeps older files
    readable until they are migrated.
    """

    section = extract_active_goal_section(goal_text)
    if not section:
        raise ValueError("GOAL.md must contain a '## Active Goal' section")

    fields: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in section.splitlines():
        line = raw_line.rstrip()
        scalar_match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if scalar_match and scalar_match.group(1) in GOAL_FIELDS:
            current_key = scalar_match.group(1)
            value = scalar_match.group(2).strip()
            if value:
                fields[current_key] = value
            else:
                fields[current_key] = []
            continue

        if current_key and line.strip().startswith("- "):
            _append_field_value(fields, current_key, line.strip()[2:].strip())

    if not fields:
        title = section.splitlines()[0].strip()
        return ActiveGoal(
            goal_id="legacy-active-goal",
            title=title,
            status="active",
            phase="undetected",
            why=(),
            deliverables=(),
            scope=(),
            out_of_scope=(),
            acceptance_criteria=(),
            next_commit="undetected",
        )

    def scalar(name: str, default: str = "") -> str:
        value = fields.get(name, default)
        if isinstance(value, list):
            return value[0] if value else default
        return str(value)

    def values(name: str) -> tuple[str, ...]:
        value = fields.get(name, [])
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        if value:
            return (str(value),)
        return ()

    missing = [
        name
        for name in ("goal_id", "title", "status", "phase", "next_commit")
        if not scalar(name)
    ]
    if missing:
        raise ValueError(f"GOAL.md active goal is missing fields: {', '.join(missing)}")

    return ActiveGoal(
        goal_id=scalar("goal_id"),
        title=scalar("title"),
        status=scalar("status"),
        phase=scalar("phase"),
        why=values("why"),
        deliverables=values("deliverables"),
        scope=values("scope"),
        out_of_scope=values("out_of_scope"),
        acceptance_criteria=values("acceptance_criteria"),
        next_commit=scalar("next_commit"),
    )


def count_active_goals(goal_text: str) -> int:
    """Count active goals in GOAL.md."""

    sections = re.findall(
        r"(?ms)^##\s+Active Goal\s*$\n(.*?)(?=^##\s+|\Z)",
        goal_text,
    )
    if not sections:
        return 0

    count = 0
    for section in sections:
        status_match = re.search(r"(?im)^status:\s*active\s*$", section)
        if status_match:
            count += 1
        elif not re.search(r"(?im)^status:\s*", section):
            count += 1
    return count


def detect_roadmap_phase(roadmap_text: str, goal: ActiveGoal | None = None) -> str:
    """Detect the current roadmap phase from GOAL.md or ROADMAP.md."""

    if goal and goal.phase and goal.phase != "undetected":
        return goal.phase

    phase_matches = re.finditer(
        r"(?ms)^##\s+(Phase\s+\d+:[^\n]+)\n(?P<body>.*?)(?=^##\s+|\Z)",
        roadmap_text,
    )
    for match in phase_matches:
        body = match.group("body")
        if re.search(r"(?im)^Status:\s*(in progress|started)\s*$", body):
            return match.group(1).strip()
    return "undetected"


def replace_generated_block(markdown: str, block: str) -> str:
    """Replace or insert the generated STATUS.md automation block."""

    generated = f"{STATUS_BLOCK_START}\n{block.rstrip()}\n{STATUS_BLOCK_END}"
    if STATUS_BLOCK_START in markdown and STATUS_BLOCK_END in markdown:
        pattern = re.compile(
            re.escape(STATUS_BLOCK_START)
            + r".*?"
            + re.escape(STATUS_BLOCK_END),
            re.DOTALL,
        )
        return pattern.sub(lambda _match: generated, markdown, count=1)

    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join([lines[0], "", generated, *lines[1:]]).rstrip() + "\n"
    return markdown.rstrip() + "\n\n" + generated + "\n"


def format_bullet_list(items: Iterable[str]) -> str:
    """Format a list as Markdown bullets."""

    values = [item for item in items if item]
    if not values:
        return "- None detected."
    return "\n".join(f"- {item}" for item in values)


def parse_name_status(name_status: str) -> list[str]:
    """Extract paths from git diff --name-status output."""

    paths: list[str] = []
    for line in name_status.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            paths.append(parts[-1])
    return paths


def parse_status_paths(status_short: str) -> list[str]:
    """Extract changed paths from git status --short output."""

    paths: list[str] = []
    for line in status_short.splitlines():
        if not line.strip() or len(line) < 4:
            continue
        path = line[3:].strip() if line[2:3] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path.strip('"'))
    return paths


def expand_directory_paths(repo_root: Path, paths: Iterable[str]) -> list[str]:
    """Expand changed directories into file paths for clearer commit plans."""

    expanded: list[str] = []
    for path in paths:
        absolute = repo_root / path
        if absolute.is_dir():
            children = sorted(
                child
                for child in absolute.rglob("*")
                if child.is_file()
                and "__pycache__" not in child.parts
                and child.suffix != ".pyc"
            )
            expanded.extend(
                str(child.relative_to(repo_root)).replace("\\", "/")
                for child in children
            )
        else:
            expanded.append(path.replace("\\", "/"))
    return unique_paths(expanded)


def unique_paths(paths: Iterable[str]) -> list[str]:
    """Return paths in first-seen order without duplicates."""

    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def classify_changed_path(path: str) -> str:
    """Classify a changed path into a commit-plan group."""

    normalized = path.replace("\\", "/")
    if normalized.startswith("operations/project/") or normalized.startswith(
        "tests/test_project_automation"
    ):
        return "project automation"
    if normalized in {"AGENTS.md", "GOAL.md", "STATUS.md", "ROADMAP.md"}:
        return "project control docs"
    if normalized.startswith("docs/project/"):
        return "project control docs"
    if normalized.startswith("operations/agents/") or normalized.startswith(
        "operations/mcp/"
    ):
        return "agent or mcp guardrails"
    if normalized.startswith("operations/db/") or normalized == "init_db.py":
        return "database schema or migrations"
    if normalized.startswith("operations/analysis/"):
        return "deterministic analysis"
    if normalized.startswith("operations/validation/"):
        return "validation"
    if normalized.startswith("data/"):
        return "data files"
    if normalized.startswith("docs/research/"):
        return "research docs"
    return "other"


def group_changed_paths(paths: Sequence[str]) -> OrderedDict[str, list[str]]:
    """Group changed files in a stable order."""

    groups: OrderedDict[str, list[str]] = OrderedDict()
    for path in paths:
        group = classify_changed_path(path)
        groups.setdefault(group, []).append(path)
    return groups


def suggest_commit_message(group: str) -> str:
    """Return a conventional commit message for a group."""

    messages = {
        "project automation": "chore: add goal-driven project automation",
        "project control docs": "docs: update project control workflow",
        "agent or mcp guardrails": "chore: keep agent and mcp guardrails deferred",
        "database schema or migrations": "feat: update deterministic schema support",
        "deterministic analysis": "feat: update deterministic analysis module",
        "validation": "feat: update validation foundation",
        "data files": "data: update curated project data",
        "research docs": "docs: update empirical research controls",
        "other": "chore: update project files",
    }
    return messages[group]


def detect_risky_mixed_changes(groups: OrderedDict[str, list[str]]) -> list[str]:
    """Return warnings about commit groups that deserve manual review."""

    warnings: list[str] = []
    if "data files" in groups:
        warnings.append("Data files changed; confirm no database or invented event data is included.")
    if "agent or mcp guardrails" in groups:
        warnings.append("Agent/MCP paths changed; confirm deferred guards still block execution.")
    if "database schema or migrations" in groups and len(groups) > 1:
        warnings.append("Database changes are mixed with other files; consider a separate commit.")
    code_groups = {
        "project automation",
        "deterministic analysis",
        "validation",
        "database schema or migrations",
    }
    docs_groups = {"project control docs", "research docs"}
    if code_groups.intersection(groups) and docs_groups.intersection(groups):
        warnings.append("Code and docs changed together; split only if they are not one coherent workflow.")
    if len(groups) > 3:
        warnings.append("More than three logical groups changed; inspect before staging.")
    return warnings
