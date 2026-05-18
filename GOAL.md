# GOAL.md

## Active Goal

goal_id: goal-h3-tiered-activity-series-001
title: Prepare H3 tiered wallet activity series
status: active
phase: Phase 6: H3 Whale Distribution And Classification
why:
- H2 deterministic outputs and compact summary persistence now exist.
- The H3 tier method is selected as wallet-level cumulative `amount_usd`
  percentiles.
- The wallet distribution inventory now documents observed source filters,
  percentile thresholds, and tier counts.
- Wallet tier classification now assigns observed wallets to deterministic
  distribution tiers.
deliverables:
- Deterministic daily wallet activity series aggregated by selected tier.
- Output metadata documenting BUY-only limitations and tier coverage.
- Tests proving tier joins and daily aggregation are reproducible.
scope:
- Prepare tiered wallet activity inputs for later timing analysis.
- Keep source-filter metadata separate from analytical tier definitions.
out_of_scope:
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Treating the source-filter minimum `amount_usd` as a whale threshold.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Tiered activity series uses existing wallet classification outputs.
- Aggregation is deterministic and does not calculate lead-lag or Granger
  statistics.
- Output avoids raw table dumps into prompts and preserves source-filter
  metadata separately.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: prepare h3 tiered wallet activity series

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H2 output shape is accepted in `docs/research/EVENT_SELECTION.md`.
- Compact H2 summary persistence exists in `analysis_summaries`.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method is selected in `docs/research/WHALE_METHOD.md`.
- H3 wallet distribution inventory exists in `data/results/`.
- H3 wallet tier classification exists in `data/results/`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Tiered wallet activity series exists before lead-lag or Granger code.
- Wallet tiers are applied from deterministic classification outputs.
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
- H3 wallet distribution inventory exists with source-filter metadata,
  percentile thresholds, and tier counts.
- H3 wallet tier classification exists for observed wallets with compact
  metadata and deterministic tier counts.
