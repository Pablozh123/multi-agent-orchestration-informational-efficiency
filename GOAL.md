# GOAL.md

## Active Goal

goal_id: goal-h2-summary-persistence-001
title: Persist reviewed H2 summaries into analysis_summaries
status: active
phase: Phase 5: H2 Event Study And CAR
why:
- H2 event-window CSV outputs exist and their column shape is accepted.
- Compact H2 summaries should be available through the thesis support table
  before any interpretation layer is considered.
deliverables:
- A deterministic writer that persists compact H2 summary metadata into
  `analysis_summaries`.
- Tests proving the write is idempotent and does not persist raw row-level
  traces.
- Documentation of the H2 summary payload shape.
scope:
- Persisting reviewed, compact H2 summary outputs from accepted CSV artifacts.
- Keeping `data/results/h2_event_window_rows.csv` as the detailed calculation
  trace outside the database.
out_of_scope:
- H3 lead-lag or Granger implementation.
- Agents, MCP, model routing, ML, cloud deployment, and interpretation workflows.
- Adding or removing curated events based on observed results.
- Persisting full row-level H2 traces into `analysis_summaries`.
acceptance_criteria:
- Exactly one active goal remains in this file.
- H2 summary persistence is deterministic and idempotent.
- Persisted H2 data are compact summaries, not raw table dumps.
- Existing H2 CSV outputs remain reproducible.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: persist h2 summaries in analysis_summaries

## Decision Inputs For This Goal

- H2 event-study window status is explicit in `docs/research/EVENT_SELECTION.md`.
- H2 output shape is accepted in `docs/research/EVENT_SELECTION.md`.
- Compact H2 summary persistence is approved for a later implementation.
- The default H2 event source is the tracked `data/events_timeline_seed.csv`.
- H3 wallet-tier method status is explicit in `docs/research/WHALE_METHOD.md`.
- ML scope and re-entry conditions are explicit in `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Compact H2 summaries are available in `analysis_summaries`.
- The persistence step is idempotent and tested.
- Full row-level H2 traces remain file-based under `data/results/`.
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
