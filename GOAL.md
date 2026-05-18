# GOAL.md

## Active Goal

goal_id: goal-empirical-scope-001
title: Generate deterministic H2 event-window outputs
status: active
phase: Phase 5: H2 Event Study And CAR
why:
- H2 event windows are selected and the canonical event seed is curated.
- The next thesis artifact should be reproducible event-window output generated
  from tracked events and deterministic Polymarket price data.
deliverables:
- `data/results/h2_event_window_rows.csv`.
- `data/results/h2_event_window_summary.csv`.
- A deterministic CLI that regenerates the H2 CSV outputs from
  `data/events_timeline_seed.csv` and `data/thesis.db`.
- Tests proving the runner is deterministic and uses the curated seed as the
  event source.
scope:
- Deterministic H2 output generation from the curated event seed and daily
  Polymarket price series.
- Project-control documentation updates needed to reflect the H2 implementation
  step.
out_of_scope:
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Writing H2 summaries into `analysis_summaries`.
- Adding or removing curated events based on observed results.
acceptance_criteria:
- Exactly one active goal remains in this file.
- H2 outputs can be regenerated with a local CLI.
- H2 output tests and full pytest pass.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: generate h2 event-window outputs from curated catalog

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method status is explicit in `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- The H2 event-window CSV outputs exist under `data/results/`.
- The H2 runner reads explicit SQLite columns and never mutates the database.
- The H2 runner uses the curated seed CSV by default.
- Project review checks still detect premature H3, ML, agent, or MCP work.

## Blocked Follow-Up Goals

- Persisting H2 outputs into `analysis_summaries` is blocked until CSV output
  shape is reviewed.
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
