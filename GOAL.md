# GOAL.md

## Active Goal

goal_id: goal-h3-wallet-distribution-inventory-001
title: Inventory wallet distribution for H3 tiering
status: active
phase: Phase 6: H3 Whale Distribution And Classification
why:
- H2 deterministic outputs and compact summary persistence now exist.
- The H3 tier method is selected as wallet-level cumulative `amount_usd`
  percentiles.
- Before wallet classification code, the observed wallet distribution needs a
  reproducible deterministic inventory.
deliverables:
- Deterministic wallet distribution inventory for the observed H3 dataset.
- Output metadata with wallet count, direction distribution, observed source
  filters, percentile thresholds, and tier membership counts.
- Tests proving percentile thresholds and boundary behavior are reproducible.
scope:
- Deterministic distribution inventory needed before wallet classification.
- No lead-lag, Granger, or timing analysis.
out_of_scope:
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Treating the source-filter minimum `amount_usd` as a whale threshold.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Distribution inventory code computes thresholds from observed data.
- Output metadata documents source-filter limitations separately from tier
  definitions.
- Tests cover percentile boundary behavior and BUY-only limitations.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: inventory wallet distribution for h3 tiering

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H2 output shape is accepted in `docs/research/EVENT_SELECTION.md`.
- Compact H2 summary persistence exists in `analysis_summaries`.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method is selected in `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Wallet-level distributions are inventoried before classification.
- Percentile thresholds are calculated from observed data, not hardcoded.
- Source filters and analytical tier definitions remain separated.
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
- H3 wallet-tier method is selected as wallet-level cumulative observed
  `amount_usd` percentiles.
