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
next_commit: chore: add goal-driven project automation
