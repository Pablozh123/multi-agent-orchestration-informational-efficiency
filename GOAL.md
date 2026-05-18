# GOAL.md

## Active Goal

goal_id: goal-empirical-scope-001
title: Define empirical research scope before H2/H3 implementation
status: active
phase: Phase 4: Event Catalog And H2 Method
why:
- H2 and H3 are blocked by research-design decisions, not code volume.
- Event selection, event windows, RCP treatment, and wallet-tier rules must be fixed before CAR, lead-lag, or Granger code is written.
deliverables:
- Final event inclusion and exclusion criteria.
- Fixed event-window definitions for H2.
- RCP treatment documented as polling signal unless a tested transformation is added later.
- Whale method documented with dataset-relative tiers and current BUY-only limitations.
scope:
- Research design, project-control automation, and documentation needed before deterministic H2/H3 code.
- Deterministic foundation guardrails that keep work aligned with AGENTS.md.
out_of_scope:
- H2 CAR implementation.
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Project-control scripts can update status, run review checks, and suggest commit groups.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: clarify project goal and workflow roles

## Decision Outputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H3 wallet-tier method status is explicit in `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- The active goal defines the research-scope decisions needed before H2/H3 code.
- Blocked follow-up goals are visible without becoming active goals.
- Project review checks can detect premature H2, H3, ML, agent, or MCP work.
- No new markdown control files are required for the goal system.

## Blocked Follow-Up Goals

- H2 CAR implementation is blocked until event windows are selected and the
  canonical event catalog is curated.
- H3 lead-lag and Granger implementation is blocked until wallet tiers are
  distribution-derived and documented.
- ML, runtime agents, MCP, and interpretation workflows are blocked until
  deterministic H1, H2, and H3 outputs exist and pass tests.

## Completed Goals

- Project synchronization documentation exists.
- Prompt and legacy instruction cleanup exists.
- Deterministic schema migrations, validation, data inventory, Brier baseline,
  RCP guardrails, agent/MCP deferral guards, event catalog tooling, and
  project-control automation exist.
