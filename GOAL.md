# GOAL.md

## Active Goal

goal_id: goal-monitor-v2-access-guardrail-checks-001
title: Enforce monitor v2 read-only access guardrails
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The politics/geopolitics anomaly-monitor specification is now recorded.
- The first historical anomaly-output artifacts are reviewed and accepted as a
  descriptive daily baseline.
- The near-real-time monitor v2 contract is documented before implementation.
- The deterministic monitor v2 snapshot prototype now exists and emits
  row-level diagnostics, compact summaries, and metadata from mocked snapshots.
- The monitor v2 snapshot output shape is reviewed and accepted.
- Rule C, combined-family confirmation, is selected as the default alert rule.
- Deterministic historical replay snapshots now exist from existing local
  artifacts.
- The historical replay output shape is reviewed and accepted.
- The replay produced no `critical` rows under the strict same-day event rule.
- Event-proximity sensitivity shows that daily `[-1d, +1d]` context captures
  event-adjacent market plus wallet clusters that same-day matching misses.
- `event_watch` is selected as a separate descriptive label for
  event-proximity wallet clusters without market-move confirmation.
- The selected proximity labels are integrated into the historical replay
  output contract through a context sidecar file.
- Recorded input validators now exist for monitor v2 watchlist, market
  snapshots, wallet-tier snapshots, and event candidates.
- Recorded monitor v2 input files now exist and pass validation.
- Recorded monitor v2 input outputs are reviewed and accepted for the first
  validated-input scoring runner.
- The validated-input scoring runner now exists and produces bounded recorded
  scoring outputs.
- Recorded scoring outputs are reviewed and accepted as bounded daily replay
  monitor outputs.
- A thesis-facing figure now summarises direct alert severities and
  event-context labels.
- Compact monitor-v2 result summaries now exist and cite their deterministic
  source artifacts.
- Compact monitor-v2 result summaries are reviewed and accepted as the first
  monitor summary boundary.
- The read-only monitor-v2 summary access contract is now specified.
- The read-only monitor-v2 summary access contract is reviewed and accepted.
- The next safe step is to make the access contract enforceable by project
  checks before any MCP, agent, live collector, strategy backtest, or trading
  path is added.
deliverables:
- Extend project review checks for monitor-v2 read-only access guardrails.
- Check that the bounded summary artifacts exist.
- Check that raw monitor row-level outputs are not treated as prompt-facing
  defaults in active docs.
- Check that MCP, agents, live collection, and execution paths remain
  deferred.
- Add or update tests for the new review-check guardrails.
scope:
- Project automation guardrails and tests only.
- Existing monitor-v2 summary/access docs only.
- Existing curated US-election event seed only.
- No new live data and no new event curation.
out_of_scope:
- Agents, MCP, model routing, ML, cloud deployment, live trading, and order
  execution.
- Live WebSocket or API collection.
- Database writes.
- New real events in the canonical seed unless they are separately curated.
- Large monitor refactor or live collector code.
- Strategy backtest implementation, PnL, profitability claims, insider claims,
  causal claims, Kalshi integration, or RCP probability use.
acceptance_criteria:
- Exactly one active goal remains in this file.
- Project review checks enforce the monitor-v2 read-only summary access
  boundary.
- Tests cover the new project guardrail logic.
- `python -m operations.project.review_check` passes.
- Bounded summaries remain default and raw row-level alert dumps remain
  blocked by default.
- MCP, agents, live collection, and strategy backtests remain deferred.
- No new live data, external API, WebSocket, database write, agent, MCP, ML, or
  order execution path is activated.
- Outputs remain aggregate-only and contain no wallet addresses or order
  instructions.
- No live collector, agent, MCP, ML, live-trading, or order-execution path is
  activated.
- Review checks pass and no deferred agent/MCP surface is activated.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: test: enforce monitor v2 read-only access guardrails

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
- Deterministic monitor v2 snapshot prototype outputs exist under
  `data/results/`.
- Monitor v2 historical replay output review is documented in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` and
  `docs/research/WHALE_METHOD.md`.
- Monitor v2 event-proximity sensitivity outputs exist under `data/results/`
  and are documented in `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Monitor v2 historical replay context labels exist in
  `data/results/monitor_v2_historical_replay_context_rows.csv`.
- Monitor v2 recorded input output review exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` and accepts the file shape for
  a validated-input scoring runner.
- Monitor v2 recorded scoring outputs exist under `data/results/` and are
  documented in `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Monitor v2 recorded scoring output review exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`, with a thesis-facing figure
  in `data/results/thesis_monitor_v2_recorded_scoring.png`.
- Compact monitor-v2 bounded summary artifacts exist:
  `data/results/monitor_v2_bounded_summary.csv` and
  `data/results/monitor_v2_bounded_summary_metadata.json`.
- Compact monitor-v2 bounded summary output review exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Read-only monitor-v2 summary access contract exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Read-only monitor-v2 summary access contract review exists in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- Literature intake structure exists in `docs/research/LITERATURE_MAP.md` and
  `data/literature/literature_index.csv`.
- ML scope and re-entry conditions are explicit in
  `docs/research/RESEARCH_SPEC.md`.
- Codex workflow roles are separate from deferred thesis runtime agents.

## Done Means

- Automated project checks enforce the monitor-v2 read-only access boundary or
  a precise blocker is recorded.
- The monitor has an accepted bounded summary, reviewed access boundary, and
  project-check enforcement before live collection, MCP, or agent
  interpretation is added.
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
- Deterministic monitor v2 snapshot prototype exists with row-level alert
  diagnostics, summary rows, metadata, and tests.
- Monitor v2 snapshot prototype output shape is reviewed and accepted with a
  threshold-sensitivity caveat.
- Rule C, combined-family confirmation, is selected and tested as the first
  monitor v2 default alert rule.
- Deterministic monitor v2 historical replay snapshots and alerts exist from
  existing local artifacts.
- Monitor v2 historical replay outputs are reviewed and accepted as a first
  daily replay baseline; zero `critical` rows are interpreted as strict
  same-day event-context behaviour.
- Monitor v2 event-proximity sensitivity exists and selects `[-1d, +1d]` daily
  event context plus separate descriptive `event_watch` labels.
- Monitor v2 historical replay context labels are integrated as a sidecar
  output that keeps `critical_proximity_candidate` separate from
  `event_watch_candidate`.
- Monitor v2 recorded-input validators exist for watchlist, market snapshots,
  wallet-tier snapshots, and event candidates.
- Monitor v2 recorded-input adapter exists and generates validated replay-
  derived input files.
- Monitor v2 recorded-input output shape is reviewed and accepted for a
  validated-input scoring runner.
- Monitor v2 validated-input scoring runner exists and emits recorded scoring
  snapshots, alert rows, summaries, context rows, validation report, and
  metadata.
- Monitor v2 recorded scoring outputs are reviewed and visualised in
  `data/results/thesis_monitor_v2_recorded_scoring.png`.
- Compact monitor-v2 bounded summary artifacts exist and cite source files.
- Compact monitor-v2 bounded summary artifacts are reviewed and accepted as
  the first monitor summary boundary.
- Read-only monitor-v2 summary access contract is specified while actual MCP,
  agent, live collector, strategy backtest, and audit-log implementation remain
  deferred.
- Read-only monitor-v2 summary access contract is reviewed and accepted as the
  monitor-v2 access boundary.
