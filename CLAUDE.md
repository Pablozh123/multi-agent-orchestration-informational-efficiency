# CLAUDE.md

Status: active
Source of truth: AGENTS.md and ARCHITECTURE_DECISIONS.md
Role: Claude project instruction pointer
Allowed scope: interpretation only, no deterministic calculations

## Binding Instruction

Follow `AGENTS.md` and `ARCHITECTURE_DECISIONS.md` for all project work.
Those files override older prompt contracts, roadmap notes, skills, and agent
instructions.

## Current Architecture

The deterministic analysis core comes before all agents. Statistical
calculations must be implemented in Python and covered by tests where
reasonable. LLMs may only interpret bounded, precomputed outputs.

Do not implement or extend agents, MCP, Claude Desktop integration, model
routing, self-consistency runs, or cloud deployment until the deterministic core
is stable and explicitly approved.

## Parallel Sessions

- One folder, one active session: continue the existing session instead of
  opening a second one in the same project folder.
- Parallel work in this repo runs in an isolated worktree (session start
  option) or on a feature branch merged via pull request with green CI.
- Stage only files you changed yourself. Never commit, revert, or stash
  another session's uncommitted changes; report them instead.

## Guardrails

- No raw table dumps into prompts.
- No `SELECT *` without `LIMIT`.
- Maximum 50 rows per tool query unless explicitly justified.
- No arbitrary whale thresholds.
- No causal claims from Granger tests.
- RCP probability transformations must be documented before use.
- Events must be curated before event-window analysis.
- Keep changes atomic and avoid unrelated edits.
