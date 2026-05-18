# GOAL.md

## Active Goal

goal_id: goal-h3-tier-method-001
title: Select distribution-derived H3 wallet-tier method
status: active
phase: Phase 6: H3 Whale Distribution And Classification
why:
- H2 deterministic outputs and compact summary persistence now exist.
- H3 remains blocked until wallet tiers are derived from the observed wallet or
  trade distribution instead of arbitrary thresholds.
deliverables:
- Document the selected wallet-tier method in `docs/research/WHALE_METHOD.md`.
- Define which wallet or trade distribution fields are used for tiers.
- Define boundary behavior for percentile or rank-based tiers.
- Keep current BUY-only and minimum `amount_usd` limitations separate from
  analytical whale definitions.
scope:
- Research-method decision for H3 wallet tiers.
- Documentation and guardrail updates needed before H3 deterministic code.
out_of_scope:
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Implementing wallet classification code before the tier method is selected.
acceptance_criteria:
- Exactly one active goal remains in this file.
- `docs/research/WHALE_METHOD.md` names one selected distribution-derived tier
  method.
- The method does not use fixed arbitrary thresholds such as 10000 USD.
- Current source filters and data limitations remain documented separately.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: select h3 wallet-tier method

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H2 output shape is accepted in `docs/research/EVENT_SELECTION.md`.
- Compact H2 summary persistence exists in `analysis_summaries`.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method status is explicit in `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- H3 wallet-tier selection is documented before wallet classification code.
- The selected method is dataset-relative and reproducible.
- The method can be implemented and tested without relying on fixed source
  filters as analytical thresholds.
- Project review checks still detect premature H3, ML, agent, or MCP work.

## Blocked Follow-Up Goals

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
- Deterministic H2 event-window CSV outputs exist and their shape is accepted.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`,
  while full row-level H2 traces remain file-based.
