# GOAL.md

## Active Goal

goal_id: goal-thesis-consolidation-001
title: Consolidate thesis-ready evidence, results, and future agent design
status: active
phase: Phase 12: Thesis Consolidation And Evidence Mapping
why:
- H1-H3 deterministic baseline outputs exist and pass project tests.
- The advisor report is now strong enough as a written update, but the thesis
  still needs a cleaner high-level consolidation layer.
- Methods, claims, interpretations, tables, and figures must map explicitly to
  deterministic artifacts and scientific sources.
- The result presentation should become thesis-ready: a small number of strong
  tables and figures instead of many raw artifacts.
- Future agent improvements may be planned only at a high level while runtime
  agents, MCP tools, model routing, autonomous execution, and unlogged LLM
  interpretation remain deferred.
deliverables:
- Create a deterministic thesis evidence map that links each central method,
  result, interpretation, limitation, and thesis claim to source artifacts and,
  where needed, literature sources.
- Create a compact thesis-ready result package with a deliberately small set
  of selected tables and figures for H1, H2, H3, the monitor prototype, and the
  Swiss referendum side track.
- Mark which outputs are thesis-facing now, descriptive only, blocked, or
  pending later source/result review.
- Document a high-level agent improvement roadmap that respects the project
  guardrails: deterministic Python metrics first, bounded summaries only,
  `llm_audit_log` for later LLM calls, no raw table dumps, max 50 rows, no
  wallet-address exposure by default, no order/trading paths, and no active
  runtime agent implementation.
- Keep the Swiss referendum track in data-collection mode until the 14 June
  2026 vote result is available; do not add a final efficiency interpretation
  before the official result.
- Keep monitor anomaly review outputs as prototype/appendix material unless
  human review and thesis-use gates later approve them.
scope:
- `operations/analysis/thesis_result_summaries.py`.
- `operations/analysis/thesis_figures.py`.
- New or updated deterministic thesis-consolidation scripts under
  `operations/analysis/`.
- `data/literature/literature_index.csv`.
- `data/results/thesis_*`.
- `docs/research/`.
- `ROADMAP.md`.
- Project workflow docs/status/log updates required before stopping.
out_of_scope:
- Multi-agent orchestration.
- MCP demo implementation.
- Claude Desktop integration.
- Model routing.
- Self-consistency runs.
- Cloud deployment.
- Trading, order placement, order cancellation, authenticated user channels,
  trading credentials, strategy PnL, profitability claims, or autonomous
  execution.
- Calculating metrics with LLMs or agents.
- Exposing raw monitor rows, raw wallet addresses, unrestricted SQL, or more
  than 50 rows through any future default tool surface.
- Claiming causality, private information, misconduct, tradeability,
  profitability, or market inefficiency from monitor labels or Granger tests.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Each thesis-facing method has a deterministic implementation artifact and at
  least one suitable source or methodology reference where needed.
- Each thesis-facing interpretation names the deterministic artifact that
  supports it and its main limitation.
- The curated result package contains a small explicit set of recommended
  tables and figures, not a raw dump of every generated artifact.
- H1/H2/H3 interpretations remain bounded to the deterministic outputs and do
  not rely on LLM-calculated metrics.
- Swiss referendum outputs remain descriptive until the official result is
  available.
- Monitor and agent content is framed as prototype, appendix, or future work
  unless deterministic thesis-use gates approve it.
- Future agent pipeline design remains documentation-only and does not activate
  runtime agents, MCP tools, model routing, or unlogged LLM interpretation.
- Tests cover the generated evidence map and curated result package where
  reasonable.
- `STATUS.md` and `docs/project/WORK_LOG.md` are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: add thesis writing blueprint

## Running Side Goal

- `goal-swiss-referendum-efficiency-001` remains a running data-collection
  track until the 14 June 2026 vote. Do not add final referendum efficiency
  interpretation before the official result is available.

## Paused Previous Goal

- `goal-monitor-anomaly-review-queue-001` remains paused. Its deterministic
  queue and static access contract exist, but further review-access work is
  intentionally deferred while the thesis is consolidated.

- `goal-monitor-detection-backtest-wallet-graph-001` remains paused as a broad
  monitor expansion goal.
