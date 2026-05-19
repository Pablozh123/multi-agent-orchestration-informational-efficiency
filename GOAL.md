# GOAL.md

## Active Goal

goal_id: goal-strategy-backtest-implementation-001
title: Implement first deterministic strategy backtest baseline
status: active
phase: Phase 10: Strategy Research Prototype
why:
- H1-H3 thesis-facing result summaries and figures now exist.
- The results narrative skeleton now states what was investigated, how the
  results were derived, what can be interpreted, and what remains open.
- The deterministic strategy prototype is now specified as a future historical
  backtest contract, not as an agent or live-trading system.
- Overleaf-ready results prose now exists for H1, H2, H3, and the strategy
  bridge.
- The first deterministic backtest baseline plan now defines the source
  artifacts, signal rule, evaluation split, cost assumptions, outputs, and
  tests.
- The next step is to implement that one baseline in Python without activating
  agents, MCP, ML, or live trading.
deliverables:
- Add a deterministic Python module for
  `h3_top_1pct_lag1_daily_timing_baseline`.
- Add focused toy-data tests for signal construction, lookahead prevention,
  costs, slippage, drawdown, and output shape.
- Generate reproducible CSV/JSON artifacts under `data/results/`.
- Keep output interpretation bounded as an exploratory historical backtest.
scope:
- Deterministic Python implementation only.
- H3 tier-level daily activity and Polymarket daily prices only.
- File-based result artifacts only.
- No database writes unless a separate persistence decision is documented.
out_of_scope:
- Agents, MCP, model routing, ML, cloud deployment, and live trading.
- New event selection, RCP usage, intraday claims, or wallet-address-level
  prompts.
- Treating the backtest as proof of future profitability.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Tests cover the planned signal rule, no-lookahead shift, costs, slippage,
  drawdown, missing fields, and deterministic outputs.
- Generated outputs contain no wallet addresses and no raw table dumps.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: add deterministic h3 strategy backtest baseline

## Decision Inputs For This Goal

- Thesis-facing H1-H3 summaries and figures exist in `data/results/`.
- Thesis results narrative skeleton exists in `docs/research/RESEARCH_SPEC.md`.
- Overleaf-ready results prose exists in `docs/research/RESEARCH_SPEC.md`.
- Deterministic strategy prototype specification exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- First deterministic backtest baseline plan exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- H1-H3 empirical baseline review exists in `docs/research/RESEARCH_SPEC.md`.
- Strategy prototype boundaries are recorded in `ARCHITECTURE_DECISIONS.md`,
  `ROADMAP.md`, and `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in
  `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- The first H3-derived strategy backtest module is implemented and tested.
- Result CSV/JSON artifacts can be regenerated deterministically.
- The output reports gross and net variants, drawdown, signal count, benchmark
  comparison, and limitations.
- Project review checks still detect premature ML, agent, MCP, live-trading,
  or profit-guarantee work.

## Blocked Follow-Up Goals

- Runtime agents and MCP remain blocked until bounded summary contracts,
  `llm_audit_log` usage, and deterministic backtest outputs exist.
- ML remains blocked until deterministic H1-H3 outputs and any strategy
  prototype baseline have written methodology and review notes.

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
- Zotero Polymarket sources are indexed as candidate literature for RAG-ready
  review.
- Initial literature synthesis exists for skimmed source pages and local HTML
  files.
- Remaining local PDFs are reviewed: `zotero_poly_005` and `zotero_poly_007`
  are skimmed; `zotero_poly_004` is rejected until replaced by a verifiable EMH
  source.
- Literature-backed thesis methodology outline exists.
- Canonical EMH source is indexed; rejected local `EMH.pdf` remains non-citable.
- Thesis tables and figures plan exists.
- Thesis-ready H2 and H3 figure artifacts are generated from existing result
  files.
- Thesis results narrative skeleton exists and separates evidence,
  interpretation, limitations, and further investigations.
- Overleaf-ready results chapter draft exists for H1, H2, H3, the strategy
  bridge, and the empirical interim conclusion.
- Deterministic strategy prototype specification exists with candidate signal
  families, interface fields, risk assumptions, and rejection criteria.
- First deterministic strategy backtest baseline plan exists for
  `h3_top_1pct_lag1_daily_timing_baseline`.
- Strategy/agent guardrails are enforced by project review checks.
