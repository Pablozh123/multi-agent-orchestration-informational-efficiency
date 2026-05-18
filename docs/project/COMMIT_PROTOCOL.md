# COMMIT_PROTOCOL.md

## Atomic Commits

Each commit should contain one logical change. Do not mix documentation sync,
schema migrations, validation, H1, H2, H3, prompt cleanup, and agent deferral in
one commit.

Good commit slices:

- Documentation control files.
- Schema migration and migration tests.
- Validation foundation and validation tests.
- Data inventory module and tests.
- Brier baseline and tests.
- RCP guardrails and tests.
- Event catalog audit and loader with tests.

## Commit Message Style

Use conventional-style messages:

- `docs: ...`
- `chore: ...`
- `feat: ...`
- `fix: ...`
- `test: ...`

Examples:

- `docs: add project control and research specification`
- `test: guard rcp usage behind documented transformation`
- `feat: add canonical event catalog audit and loader`

## When To Run Tests

Run focused tests after changing a focused module.

Run the full suite before any commit that touches:

- Python analysis code.
- Validation code.
- Database migrations.
- CLI entry points.
- Prompt or agent guards.

For documentation-only commits, running pytest is still preferred when the
worktree already contains related code changes.

## What To Include Before Commit

Before committing:

- Run `git diff --stat`.
- Run `git status --short`.
- Confirm no unrelated files are staged.
- Confirm tests pass or document why they were not run.
- Confirm no database file was modified unless the task explicitly required it.
- Confirm no real events were invented for seed files.

## Handling Uncommitted Foundation Changes

The current repository may contain many uncommitted foundation changes. Handle
them by splitting commits in dependency order:

1. Project architecture and documentation sync.
2. Prompt and legacy inventory cleanup.
3. Schema migrations.
4. Validation foundation.
5. Data inventory.
6. Brier baseline and RCP guardrails.
7. Agent and MCP deferral guards.
8. Event catalog audit and loader.
9. Project management and research control docs.

If a file contains changes from multiple tasks, inspect the diff carefully and
stage only the hunks that belong to the current commit. Do not revert user work
or unrelated foundation changes.

