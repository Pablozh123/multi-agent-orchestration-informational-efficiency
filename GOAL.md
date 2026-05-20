# GOAL.md

## Active Goal

goal_id: goal-monitor-v2-snapshot-prototype-001
title: Implement deterministic monitor v2 snapshot prototype
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The politics/geopolitics anomaly-monitor specification is now recorded.
- The first historical anomaly-output artifacts are reviewed and accepted as a
  descriptive daily baseline.
- The near-real-time monitor v2 contract is documented before implementation.
- The next safe step is a deterministic Python prototype over recorded or
  mocked snapshots, not a live collector.
deliverables:
- Add tested monitor v2 data-contract helpers or a small runner using recorded
  or mocked snapshots.
- Implement robust rolling score and rolling percentile diagnostics on toy
  snapshot data.
- Emit deterministic alert rows, summary rows, and metadata without writing to
  the database.
- Ensure missing or unstable baselines return explicit diagnostic statuses.
- Keep outputs aggregate-only and free of wallet addresses.
scope:
- Deterministic Python prototype only.
- Recorded or mocked snapshots only.
- Polymarket politics/geopolitical monitor contract only.
- Existing historical anomaly artifacts and v2 contract can be used as design
  inputs.
out_of_scope:
- Agents, MCP, model routing, ML, cloud deployment, live trading, and order
  execution.
- Live WebSocket or API collection.
- Database writes.
- New real events in the canonical seed unless they are separately curated.
- Strategy backtest implementation, PnL, profitability claims, insider claims,
  causal claims, Kalshi integration, or RCP probability use.
acceptance_criteria:
- Exactly one active goal remains in this file.
- The prototype follows the documented v2 contract.
- Robust rolling score tests cover normal, spike, zero-MAD, and insufficient
  baseline cases.
- Alert output includes severity, evidence references, limitations, and review
  status.
- Output files contain no wallet addresses and no order instructions.
- No live collector, agent, MCP, ML, live-trading, or order-execution path is
  activated.
- Review checks pass and no deferred agent/MCP surface is activated.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: add deterministic monitor v2 snapshot prototype

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
- The anomaly-monitor specification is committed before this implementation.
- Historical anomaly output artifacts exist under `data/results/`.
- Historical anomaly output review exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` and
  `docs/research/WHALE_METHOD.md`.
- Near-real-time monitor v2 contract exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` and
  `docs/research/WHALE_METHOD.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in
  `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- A deterministic snapshot prototype can generate monitor alert rows, summary
  rows, and metadata from recorded or mocked inputs.
- The prototype demonstrates robust rolling score, percentile rank, alert
  level, and review-status handling without live collection.
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
- Politics/geo anomaly-monitor specification is documented, Polymarket-first,
  and keeps Kalshi, near-real-time monitoring, agents, and MCP deferred.
- Historical politics/geo anomaly outputs exist:
  `h3_event_wallet_anomaly_rows.csv`,
  `h3_event_wallet_anomaly_summary.csv`, and
  `h3_event_wallet_anomaly_metadata.json`.
- Historical anomaly outputs are reviewed and visualised in
  `data/results/thesis_h3_event_wallet_anomalies.png`.
- Near-real-time monitor v2 contract is specified as Polymarket-first,
  read-only, robust-score based, human-reviewed, and file-based before live
  collection.
