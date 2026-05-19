# GOAL.md

## Active Goal

goal_id: goal-literature-intake-001
title: Import and map Perplexity literature sources
status: active
phase: Phase 10: Strategy Research Prototype
why:
- H1-H3 thesis-facing result summaries now exist.
- The strategy/agent idea is scoped as a backtested research prototype, not as
  live trading.
- Literature intake structure exists, but downloaded Perplexity/PDF sources are
  not indexed yet.
deliverables:
- Add local Perplexity/PDF source metadata to `data/literature/literature_index.csv`.
- Map each source to H1, H2, H3, strategy prototype, or architecture.
- Mark unreviewed discoveries as `candidate` until the paper is checked.
- Keep raw PDFs and exports in ignored local storage only.
scope:
- Literature metadata and research mapping only.
- Perplexity output may guide discovery but not thesis claims.
out_of_scope:
- New statistical code, new event selection, or backtest implementation.
- Agents, MCP, model routing, ML, cloud deployment, and live trading.
- Treating Perplexity summaries as cited evidence.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Literature index has one metadata row per imported source.
- Every source has a topic, thesis mapping, status, and notes.
- Raw PDFs/exports remain untracked.
- No thesis claim is added from an unchecked Perplexity summary.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: index imported literature sources

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
- Backtested strategy prototype boundaries are recorded in
  `ARCHITECTURE_DECISIONS.md` and `ROADMAP.md`.
- Thesis-facing H1-H3 summaries exist in `data/results/`.
- Strategy agent architecture is specified in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Downloaded literature sources are indexed and mapped.
- Perplexity discoveries are separated from checked academic sources.
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
- Thesis-facing H1-H3 summary tables exist and are traceable to deterministic
  source artifacts.
- Literature intake structure and strategy-agent architecture are documented.
- Strategy/agent guardrails are enforced by project review checks.
