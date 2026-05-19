from __future__ import annotations

from pathlib import Path

from operations.project.commit_plan import render_commit_plan
from operations.project.init import (
    ActiveGoal,
    CommandResult,
    count_active_goals,
    detect_roadmap_phase,
    group_changed_paths,
    parse_active_goal,
    parse_status_paths,
    replace_generated_block,
)
from operations.project.review_check import run_checks
from operations.project.update_status import render_status_block, update_status


GOAL_TEXT = """# GOAL.md

## Active Goal

goal_id: goal-test
title: Keep automation focused
status: active
phase: Phase 1: Project Synchronization And Foundation
why:
- The project needs control scripts.
deliverables:
- A working status updater.
scope:
- Project automation only.
out_of_scope:
- H2 implementation.
acceptance_criteria:
- Checks pass.
next_commit: chore: add automation
"""


def _write_minimal_project(root: Path) -> None:
    (root / "operations" / "analysis").mkdir(parents=True)
    (root / "operations" / "agents").mkdir(parents=True)
    (root / "operations" / "mcp").mkdir(parents=True)
    (root / "docs" / "research").mkdir(parents=True)
    (root / "operations" / "analysis" / "safe.py").write_text(
        "include_rcp: bool = False\nrcp_transformation_documented = False\n",
        encoding="utf-8",
    )
    guard = (
        'DEFERRED_MESSAGE = "Deferred until deterministic analysis core is complete"\n'
        "def main():\n"
        "    raise RuntimeError(DEFERRED_MESSAGE)\n"
    )
    (root / "operations" / "agents" / "orchestrator.py").write_text(
        guard,
        encoding="utf-8",
    )
    (root / "operations" / "mcp" / "thesis_mcp_server.py").write_text(
        guard,
        encoding="utf-8",
    )
    (root / "docs" / "research" / "EVENT_SELECTION.md").write_text(
        "# EVENT_SELECTION.md\n\n## Decision Status\n\n- h2_window_status: blocked\n",
        encoding="utf-8",
    )
    (root / "docs" / "research" / "WHALE_METHOD.md").write_text(
        "# WHALE_METHOD.md\n\n## Decision Status\n\n- h3_tier_status: blocked\n",
        encoding="utf-8",
    )
    (root / "docs" / "research" / "RESEARCH_SPEC.md").write_text(
        "# RESEARCH_SPEC.md\n\n## ML Scope Rule\n\n- ml_scope_status: deferred\n",
        encoding="utf-8",
    )
    (root / "docs" / "research" / "STRATEGY_AGENT_ARCHITECTURE.md").write_text(
        "# STRATEGY_AGENT_ARCHITECTURE.md\n\n"
        "Signal generator contracts use SignalSpec, BacktestConfig, and "
        "BacktestResult. Calls are logged in llm_audit_log. No raw table dumps, "
        "autonomous trading, or live trading.\n",
        encoding="utf-8",
    )
    (root / "GOAL.md").write_text(GOAL_TEXT, encoding="utf-8")
    (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
    (root / "ROADMAP.md").write_text(
        "# ROADMAP.md\n\n## Phase 1: Project Synchronization And Foundation\n\nStatus: in progress\n",
        encoding="utf-8",
    )
    (root / "STATUS.md").write_text("# STATUS.md\n\nManual section.\n", encoding="utf-8")


def test_parse_active_goal_structured_template() -> None:
    goal = parse_active_goal(GOAL_TEXT)
    assert goal == ActiveGoal(
        goal_id="goal-test",
        title="Keep automation focused",
        status="active",
        phase="Phase 1: Project Synchronization And Foundation",
        why=("The project needs control scripts.",),
        deliverables=("A working status updater.",),
        scope=("Project automation only.",),
        out_of_scope=("H2 implementation.",),
        acceptance_criteria=("Checks pass.",),
        next_commit="chore: add automation",
    )
    assert count_active_goals(GOAL_TEXT) == 1


def test_replace_generated_block_preserves_manual_content() -> None:
    original = "# STATUS.md\n\nManual content.\n"
    updated = replace_generated_block(original, "## Automation Snapshot\n\nGenerated.")
    assert "Manual content." in updated
    assert "<!-- PROJECT_STATUS:START -->" in updated
    updated_again = replace_generated_block(updated, "## Automation Snapshot\n\nRegenerated.")
    assert "Generated." not in updated_again
    assert "Regenerated." in updated_again
    assert updated_again.count("<!-- PROJECT_STATUS:START -->") == 1


def test_replace_generated_block_treats_backslashes_literally() -> None:
    original = (
        "# STATUS.md\n\n"
        "<!-- PROJECT_STATUS:START -->\n"
        "old\n"
        "<!-- PROJECT_STATUS:END -->\n"
    )
    block = "## Automation Snapshot\n\n```text\n M C:\\Project\\GOAL.md\n```"

    updated = replace_generated_block(original, block)

    assert "C:\\Project\\GOAL.md" in updated


def test_detect_roadmap_phase_prefers_goal_phase() -> None:
    goal = parse_active_goal(GOAL_TEXT)
    assert detect_roadmap_phase("", goal) == "Phase 1: Project Synchronization And Foundation"


def test_update_status_cli_helper_updates_only_generated_block(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    update_status(tmp_path, skip_pytest="unit test")
    status = (tmp_path / "STATUS.md").read_text(encoding="utf-8")
    assert "Manual section." in status
    assert "Current goal: `goal-test` - Keep automation focused" in status
    assert "skipped: unit test" in status


def test_h2_output_goal_is_not_marked_as_premature_scope_work() -> None:
    goal = ActiveGoal(
        goal_id="goal-h2",
        title="Generate deterministic H2 event-window outputs",
        status="active",
        phase="Phase 5: H2 Event Study And CAR",
        why=(),
        deliverables=(),
        scope=(),
        out_of_scope=(),
        acceptance_criteria=(),
        next_commit="feat: generate h2 outputs",
    )

    block = render_status_block(
        branch="main",
        latest_commit="abc123",
        git_status="clean",
        diff_stat="no unstaged diff",
        pytest_result=CommandResult(("pytest",), 0, "133 passed", ""),
        goal=goal,
        roadmap_phase=goal.phase,
    )

    assert "Do not implement H2/H3 before" not in block


def test_review_check_passes_for_minimal_project(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    results = run_checks(tmp_path, skip_pytest="unit test")
    assert all(result.passed for result in results)


def test_review_check_fails_for_select_star(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "operations" / "bad.py").write_text(
        'SQL = "SELECT * FROM table LIMIT 1"\n',
        encoding="utf-8",
    )
    results = run_checks(tmp_path, skip_pytest="unit test")
    assert any(result.name == "sql select star" and not result.passed for result in results)


def test_review_check_fails_for_h2_code_before_selected_window(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "operations" / "analysis" / "event_study.py").write_text(
        '"""Event study implementation placeholder."""\n',
        encoding="utf-8",
    )
    results = run_checks(tmp_path, skip_pytest="unit test")
    assert any(result.name == "h2 window guard" and not result.passed for result in results)


def test_review_check_fails_for_h3_code_before_selected_tiers(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "operations" / "analysis" / "granger.py").write_text(
        '"""Granger implementation placeholder."""\n',
        encoding="utf-8",
    )
    results = run_checks(tmp_path, skip_pytest="unit test")
    assert any(result.name == "h3 tier guard" and not result.passed for result in results)


def test_review_check_fails_for_ml_scope_before_h1_h2_h3_outputs(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "docs" / "research" / "RESEARCH_SPEC.md").write_text(
        "# RESEARCH_SPEC.md\n\n## ML Scope Rule\n\n- ml_scope_status: selected\n",
        encoding="utf-8",
    )
    results = run_checks(tmp_path, skip_pytest="unit test")
    assert any(result.name == "ml scope guard" and not result.passed for result in results)


def test_review_check_fails_without_strategy_architecture_doc(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "docs" / "research" / "STRATEGY_AGENT_ARCHITECTURE.md").unlink()

    results = run_checks(tmp_path, skip_pytest="unit test")

    assert any(result.name == "strategy architecture" and not result.passed for result in results)


def test_review_check_fails_for_live_trading_implementation(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "operations" / "analysis" / "trade.py").write_text(
        "def place_order():\n    return 'blocked'\n",
        encoding="utf-8",
    )

    results = run_checks(tmp_path, skip_pytest="unit test")

    assert any(result.name == "live trading guard" and not result.passed for result in results)


def test_review_check_fails_for_active_prompt_without_metric_scope(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    prompt_root = tmp_path / "directives" / "roles"
    prompt_root.mkdir(parents=True)
    (prompt_root / "bad_agent.md").write_text(
        "# Bad Agent\n\nStatus: active\n\nCalculate metrics in the prompt.\n",
        encoding="utf-8",
    )

    results = run_checks(tmp_path, skip_pytest="unit test")

    assert any(result.name == "active prompt metric scope" and not result.passed for result in results)


def test_group_changed_paths_suggests_project_automation_group() -> None:
    groups = group_changed_paths(
        [
            "operations/project/update_status.py",
            "tests/test_project_automation.py",
            "GOAL.md",
        ]
    )
    assert list(groups) == ["project automation", "project control docs"]


def test_parse_status_paths_includes_untracked_files() -> None:
    paths = parse_status_paths(" M AGENTS.md\n?? operations/project/init.py\n")
    assert paths == ["AGENTS.md", "operations/project/init.py"]


def test_commit_plan_reports_no_diff_for_non_git_project(tmp_path: Path) -> None:
    report = render_commit_plan(tmp_path)
    assert report.startswith("FAIL:") or "No unstaged file changes detected." in report
