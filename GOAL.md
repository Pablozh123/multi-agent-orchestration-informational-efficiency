# GOAL.md

## Active Goal

goal_id: goal-h3-granger-baseline-001
title: Compute deterministic H3 lead-lag and Granger baseline
status: active
phase: Phase 7: H3 Lead-Lag And Granger Tests
why:
- H2 deterministic outputs and compact summary persistence now exist.
- The H3 tier method is selected as wallet-level cumulative `amount_usd`
  percentiles.
- H3 wallet distribution inventory, tier classification, and daily tiered
  activity inputs exist.
- Descriptive H3 lead-time histograms exist and their shape is accepted for
  the first daily baseline.
deliverables:
- Daily lead-lag correlation outputs between tiered wallet activity and
  Polymarket daily price changes.
- Daily Granger baseline outputs by wallet tier and selected activity measure.
- Tests proving lag alignment and Granger result extraction are deterministic.
- Documentation that results are predictive timing diagnostics, not proof of
  true causality or misconduct.
scope:
- Deterministic Python analysis using existing daily H3 tiered activity inputs
  and daily Polymarket prices from SQLite.
- Keep source-filter metadata separate from analytical tier definitions.
out_of_scope:
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Treating the source-filter minimum `amount_usd` as a whale threshold.
- RCP probability transformation.
- Intraday lead-lag claims.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Lead-lag and Granger calculations are deterministic Python.
- Granger outputs are described as predictive timing diagnostics only.
- Daily and BUY-only limitations remain explicit.
- Output avoids raw table dumps into prompts and preserves source-filter
  metadata separately.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: compute h3 lead-lag and granger baseline

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H2 output shape is accepted in `docs/research/EVENT_SELECTION.md`.
- Compact H2 summary persistence exists in `analysis_summaries`.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method is selected in `docs/research/WHALE_METHOD.md`.
- H3 wallet distribution inventory exists in `data/results/`.
- H3 wallet tier classification exists in `data/results/`.
- H3 tiered wallet activity series exists in `data/results/`.
- H3 descriptive lead-time histograms exist in `data/results/`.
- H3 lead-time output shape is reviewed and accepted in
  `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Deterministic H3 lead-lag and Granger outputs exist.
- Lead-lag alignment uses pre-existing daily tiered wallet activity and daily
  Polymarket price changes.
- Source filters and analytical tier definitions remain separated.
- Project review checks still detect premature H3, ML, agent, or MCP work.

## Blocked Follow-Up Goals

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
- H3 tiered wallet activity series exists as a complete daily tier panel.
- H3 descriptive lead-time histograms exist and are reviewed as a daily
  descriptive timing baseline.
