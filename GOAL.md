# GOAL.md

## Active Goal

goal_id: goal-thesis-result-summaries-001
title: Prepare thesis-facing H1-H3 result summaries
status: active
phase: Phase 9: Thesis Export
why:
- H1, H2, and H3 deterministic baseline outputs exist.
- The empirical baseline package has been reviewed in
  `docs/research/RESEARCH_SPEC.md`.
- Thesis-facing result tables need compact, reproducible summaries before
  Overleaf export or interpretation-layer work.
deliverables:
- Compact thesis-facing summary tables for H1, H2, and H3 baseline outputs.
- Clear mapping from each summary table to its deterministic source artifact.
- German thesis wording notes using Swiss spelling where thesis-facing text is
  introduced.
- Figure/table readiness checklist for Overleaf export.
scope:
- Summarise existing deterministic outputs only.
- Keep source-filter metadata separate from analytical tier definitions.
out_of_scope:
- New statistical code.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Treating the source-filter minimum `amount_usd` as a whale threshold.
- RCP probability transformation.
- Intraday lead-lag claims.
acceptance_criteria:
- Exactly one active goal remains in this file.
- H1-H3 thesis-facing summary tables are traceable to deterministic outputs.
- H3 wording remains limited to predictive timing diagnostics.
- RCP and intraday limitations remain explicit.
- Output avoids raw table dumps into prompts and preserves source-filter
  metadata separately.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: prepare h1 h2 h3 thesis result summaries

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
- H3 daily lead-lag and Granger outputs exist in `data/results/`.
- H3 Granger output interpretation limits are accepted in
  `docs/research/WHALE_METHOD.md`.
- H1-H3 empirical baseline review is accepted in
  `docs/research/RESEARCH_SPEC.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- H1-H3 summary tables are prepared for thesis drafting.
- Each summary is traceable to deterministic result artifacts.
- Source filters and analytical tier definitions remain separated.
- Project review checks still detect premature H3, ML, agent, or MCP work.

## Blocked Follow-Up Goals

- ML, runtime agents, MCP, and interpretation workflows remain blocked until
  H3 result interpretation limits are reviewed and explicitly approved.

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
- H3 deterministic daily lead-lag correlations and Granger outputs exist with
  tests and compact metadata.
- H3 Granger interpretation limits, persistence decision, and sensitivity needs
  are documented.
- H1-H3 deterministic baseline package is reviewed for thesis readiness.
