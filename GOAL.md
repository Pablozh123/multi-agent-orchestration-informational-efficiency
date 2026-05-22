# GOAL.md

## Active Goal

goal_id: goal-polymarket-live-watchlist-review-001
title: Review first Polymarket politics/geopolitics watchlist candidates
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The read-only Polymarket collector and bounded rolling-history collector
  exist.
- The curated watchlist contract and validator exist.
- The current curated watchlist seed has 3 candidate rows and 0 accepted rows.
- Auto-discovered Gamma rows are not monitor-ready until manually reviewed.
- Thesis-facing live alerts remain blocked until at least one politics or
  geopolitics watchlist row is reviewed and marked `accepted`.
deliverables:
- Review each current candidate row in `data/monitor_v2_curated_watchlist.csv`.
- Fill required source and review metadata for any accepted row.
- Mark unsuitable rows as `rejected` with an exclusion reason, or
  `needs_followup` if source or market mapping is unclear.
- Regenerate the curated watchlist validation report.
- Keep accepted watchlist rows separated from automatic Gamma discovery.
scope:
- `data/monitor_v2_curated_watchlist.csv`.
- `data/results/monitor_v2_curated_watchlist_validation_report.json`.
- The current 3 Gamma-discovered candidate rows.
- Polymarket politics/geopolitics markets only.
- Human-readable review metadata.
out_of_scope:
- Agents, MCP, model routing, ML, cloud deployment, trading, and order
  execution.
- Database writes.
- New real events in the canonical seed unless they are separately curated.
- Authenticated user channel, order endpoints, API trading credentials, cloud
  scheduler setup, or background daemon.
- Strategy backtest implementation, PnL, profitability claims, insider claims,
  causal claims, Kalshi integration, or RCP probability use.
acceptance_criteria:
- Exactly one active goal remains in this file.
- At least one current candidate is manually reviewed.
- Accepted rows include `source_url`, `inclusion_reason`, `reviewed_by`, and
  timezone-aware `reviewed_at_utc`.
- Rejected rows include `exclusion_reason`.
- Rows that cannot be accepted or rejected are marked `needs_followup`.
- Auto-discovered markets remain candidates until they pass the watchlist
  contract.
- The curated watchlist validator passes and the report is regenerated.
- Existing collector and scoring outputs remain read-only and file-based.
- No authenticated user channel, order endpoint, agent, MCP, ML, strategy
  backtest, cloud daemon, database write, or trading credential path is
  activated.
- Review checks pass and no deferred agent/MCP surface is activated.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: data: review first polymarket live watchlist candidates

## Decision Inputs For This Goal

- `data/monitor_v2_curated_watchlist.csv` exists.
- `operations/collectors/polymarket_watchlist.py` validates the local
  watchlist contract.
- `data/results/monitor_v2_curated_watchlist_validation_report.json` reports
  3 candidate rows, 0 accepted rows, and validation status `pass`.
- The current candidates are:
  - `Xi Jinping out before 2027?`
  - `Will Gavin Newsom win the 2028 Democratic presidential nomination?`
  - `Will Alexandria Ocasio-Cortez win the 2028 Democratic presidential nomination?`

## Done Means

- The first reviewed watchlist state exists.
- At least one row is no longer an unchecked candidate.
- The validator report documents whether any row is monitor-ready.
- The next code step can integrate accepted watchlist rows into the collector
  without changing the watchlist contract.
- Project review checks still detect premature ML, agent, MCP, trading,
  order-execution, raw prompt data, or profit-guarantee work.

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
- Project review checks enforce the monitor-v2 read-only summary access
  boundary, including bounded summary artifacts, row limits, no wallet-address
  exposure, and blocked raw monitor files.
- Monitor-v2 live input collection contract is specified as read-only,
  replay-first, UTC timestamped, 15-minute bucketed for first live-capable
  alerts, validation-first, and no-lookahead.
- Monitor-v2 live input collection contract is reviewed and accepted for a
  replay-first validator/prototype path; live API/WebSocket collection remains
  blocked.
- Replay-first monitor-v2 live input validators exist and reject invalid
  timestamps, missing required fields, invalid price ranges, negative counts or
  amounts, wallet-address fields, invalid event review states, and invalid
  bucket boundaries.
- Replay-first monitor-v2 live input validators are reviewed and accepted for a
  local batch prototype; cross-file market consistency remains a prototype
  implementation concern.
- Local replay-first monitor-v2 live input batch prototype exists and writes
  validated mocked fixture files plus metadata under `data/results/`.
- Local replay-first monitor-v2 live input batch output shape is reviewed and
  accepted for a diagnostic deterministic local scoring bridge.
- Local replay-first monitor-v2 live input scoring bridge exists and writes
  diagnostic snapshots, alert rows, alert summaries, validation report, and
  metadata under `data/results/`.
- Local replay-first monitor-v2 live input scoring output shape is reviewed and
  accepted as a pipeline diagnostic, not empirical market evidence.
- First real-data replay boundary is specified as `daily_recorded_replay_v1`
  using existing recorded daily input artifacts and the v2 30/20 baseline rule.
- Existing recorded daily replay outputs satisfy `daily_recorded_replay_v1`;
  no additional daily adapter is needed for this boundary.
- Read-only Polymarket live collector foundation exists for public Gamma
  discovery, CLOB midpoint polling, Data API aggregate trade activity,
  validated monitor-v2 input files, scoring bridge diagnostics, and a simple
  snapshot figure.
- Bounded read-only Polymarket rolling-history collector exists with append
  and dedupe logic, rolling scoring outputs, baseline-readiness metadata, and
  a rolling-history figure.
- Curated Polymarket live watchlist contract exists with a local CSV seed,
  validator, tests, and validation report; current rows are candidates and not
  monitor-ready.
