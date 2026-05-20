# GOAL.md

## Active Goal

goal_id: goal-politics-geo-anomaly-monitor-spec-001
title: Specify politics/geo anomaly monitor before implementation
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The strategy track is more useful as a politics/geopolitics anomaly monitor
  than as an immediate trading backtest.
- The monitor can use historical US-election events for validation while
  staying open to later sourced geopolitical event candidates.
- Agent and MCP ideas remain thesis architecture extensions; the monitor
  specification must stay deterministic and Python-first.
deliverables:
- Define the v1 anomaly monitor as a historical politics/geo monitoring
  specification, not a live-trading system.
- Record that v1 watches Polymarket politics/geopolitical markets; Kalshi is a
  later extension candidate.
- Index and classify the local Polybench PDF as a literature candidate.
- Clarify how market, wallet, event, and concentration anomalies would be
  analysed without raw wallet-address prompt dumps.
- Keep the existing deterministic backtest plan as a later validation path,
  not the immediate active goal.
scope:
- Documentation and literature-index update only.
- Politics/geopolitical prediction-market anomaly monitoring design.
- Historical validation uses the existing curated US-election event set first.
- Event candidates such as geopolitical shocks require sourced timestamps and
  market mappings before analysis.
out_of_scope:
- Analysis-code changes, new statistical modules, database writes, and H3
  backtest implementation.
- Agents, MCP, model routing, ML, cloud deployment, live trading, and order
  execution.
- New real events in the canonical seed unless they are separately curated.
- Profitability claims, insider claims, intraday claims, or RCP probability use.
acceptance_criteria:
- Exactly one active goal remains in this file.
- `STRATEGY_AGENT_ARCHITECTURE.md` describes the anomaly-monitor direction and
  keeps agents/MCP deferred.
- `WHALE_METHOD.md` records event-centred wallet anomaly analysis as the next
  H3/strategy bridge.
- `LITERATURE_MAP.md` and `literature_index.csv` include Polybench as a
  candidate source, not a thesis claim.
- No code, database, agent, MCP, ML, or live-trading implementation is added.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: pivot strategy track to politics geo anomaly monitor

## Decision Inputs For This Goal

- Thesis-facing H1-H3 summaries and figures exist in `data/results/`.
- Thesis results narrative skeleton exists in `docs/research/RESEARCH_SPEC.md`.
- Overleaf-ready results prose exists in `docs/research/RESEARCH_SPEC.md`.
- Deterministic strategy prototype specification exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- First deterministic backtest baseline plan exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`, but is deferred behind the
  anomaly-monitor specification.
- H1-H3 empirical baseline review exists in `docs/research/RESEARCH_SPEC.md`.
- Strategy and anomaly-monitor boundaries are recorded in
  `ARCHITECTURE_DECISIONS.md`, `ROADMAP.md`, and
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in
  `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- The politics/geo anomaly-monitor specification separates market anomalies,
  wallet-tier anomalies, event candidates, and later backtest validation.
- The spec states that v1 is historical and Polymarket-first, while near-real
  time monitoring and Kalshi are later extensions.
- Polybench is indexed as a candidate source and cannot support thesis claims
  until reviewed.
- Project review checks still detect premature ML, agent, MCP, live-trading,
  order-execution, or profit-guarantee work.

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
