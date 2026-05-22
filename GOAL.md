# GOAL.md

## Active Goal

goal_id: goal-polymarket-alert-review-workflow-001
title: Specify alert-review workflow from compact live-window summaries
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The read-only Polymarket collector and bounded rolling-history collector
  exist.
- The curated watchlist contract and validator exist.
- The current curated watchlist seed has 3 accepted rows and 0 candidate rows.
- The read-only collector can now collect from accepted curated watchlist rows.
- The first curated rolling-history run now has 3 real closed 5-minute buckets
  and diagnostic scoring is available.
- The first static read-only dashboard exists and makes the current monitor
  state understandable from bounded local artifacts.
- The bounded refresh runner exists and can collect future buckets, score them,
  and regenerate the dashboard.
- The latest refresh run has 4 real closed 5-minute buckets, 0 alerts, and
  diagnostic baseline readiness.
- The safe operator protocol is documented with copy-pasteable commands and
  interpretation rules.
- A production-like live monitor baseline has now been collected with 21 real
  closed 5-minute buckets and the v2 30/20 rolling-baseline settings.
- The production-like baseline review reports 0 alerts and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- The reviewed summary has 300 `insufficient_baseline` rows and 72 `zero_mad`
  rows, with 372 `none` severity rows.
- The threshold-sensitivity report shows that default Rule C produced 0 alerts,
  while only the diagnostic 10/5 scenario produced 3 `watch` rows.
- The diagnostic 10/5 rows are percentile-only watch rows with low robust-z
  values, so they do not justify changing the default rule.
- The reviewed watchlist has been expanded from 3 to 12 accepted
  politics/geopolitics markets using public Gamma market metadata.
- A temporary read-only collector verification produced 12 watchlist rows,
  24 token midpoint rows, and 12 aggregate wallet/activity rows without
  touching repository result artifacts.
- The expanded production-like live baseline has now been collected with 20
  real closed 5-minute buckets on 12 reviewed markets.
- The run produced 480 market snapshot rows, 240 aggregate wallet/activity
  rows, 1'416 scoring rows, 60 summary rows, 0 alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- The expanded-baseline review accepts the output shape and keeps Rule C
  unchanged.
- The read-only dashboard/reporting layer now surfaces current market universe,
  latest bucket, baseline readiness, status counts, severity counts, scoring
  rows, summary rows, and limitations without opening multiple CSV/JSON files.
- The next implementation step is a small local read-only wrapper over the
  existing dashboard artifacts, not a background daemon, agent layer, or
  trading surface.
- The local dashboard launcher now returns a read-only `file://` dashboard URI
  plus market count, bucket count, alert count, and baseline readiness without
  collecting data or running continuously.
- The second bounded expanded-watchlist live window has now been collected
  using the same v2 30/20 settings.
- The second window matches the first high-level baseline shape: 12 markets,
  20 buckets, 480 market snapshot rows, 240 aggregate wallet/activity rows,
  1'416 scoring rows, 60 summary rows, 0 alerts, severity counts of 1'416
  `none`, status counts of 1'200 `insufficient_baseline` and 216 `zero_mad`,
  and baseline readiness `baseline_available_zero_mad_or_non_alerting`.
- A compact live-window registry now stores repeated run summaries without
  preserving unbounded raw API dumps.
- The registry contains `expanded_window_001` and `expanded_window_002`, both
  with 12 markets, 20 buckets, 0 alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- The next methodological step is to define how future non-zero alerts should
  be reviewed before they become thesis-facing monitor evidence.
deliverables:
- Define a deterministic alert-review workflow over compact monitor outputs.
- Specify review states, required evidence fields, rejection criteria, and
  thesis-facing wording limits.
- Keep alerts descriptive until human review confirms source artifacts,
  timestamp validity, market mapping, and no-lookahead status.
- Keep refresh/collection explicit and bounded.
- Keep Rule C thresholds unchanged.
scope:
- `data/monitor_v2_curated_watchlist.csv`.
- `data/results/monitor_v2_curated_watchlist_validation_report.json`.
- `data/results/monitor_v2_polymarket_rolling_*`.
- `data/results/monitor_v2_polymarket_live_*`.
- `data/results/monitor_v2_polymarket_dashboard.html`.
- Existing dashboard/reporting code and tests if needed.
- Local wrapper or launcher code and tests if needed.
- Existing project/research docs.
- Polymarket politics/geopolitics markets only.
- Existing local validated output files.
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
- Alert-review states and rejection criteria are documented before any
  thesis-facing alert claim is made.
- The workflow uses compact summaries and source artifact references, not raw
  wallet-address data or unbounded raw API dumps.
- The workflow does not change Rule C thresholds without a separate reviewed
  sensitivity decision.
- The workflow does not collect data automatically, run continuously, execute
  orders, call agents, call MCP, use ML, write the database, or require trading
  credentials.
- The dashboard still reports 12 reviewed markets and 20 closed buckets from
  the latest expanded baseline unless a later bounded run intentionally
  replaces it.
- The output contains no wallet addresses and no order instructions.
- Rule C thresholds remain unchanged.
- Existing scoring outputs are not reinterpreted as causal, profitable,
  private-information, or efficiency evidence.
- No authenticated user channel, order endpoint, agent, MCP, ML, strategy
  backtest, cloud daemon, database write, or trading credential path is
  activated.
- Review checks pass and no deferred agent/MCP surface is activated.
- STATUS.md and WORK_LOG.md are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: docs: specify monitor alert-review workflow

## Decision Inputs For This Goal

- `data/monitor_v2_curated_watchlist.csv` exists.
- `operations/collectors/polymarket_watchlist.py` validates the local
  watchlist contract.
- `data/results/monitor_v2_curated_watchlist_validation_report.json` reports
  12 accepted rows, 0 candidate rows, 0 rejected rows, 0 needs-followup rows,
  and validation status `pass`.
- The expanded accepted watchlist includes:
  - 3 existing politics/leadership/election rows,
  - 3 US election and midterm control rows,
  - 6 geopolitics rows covering China/Taiwan, Iran, Russia/Ukraine leadership,
    and Ukraine/Russia peace-process risk.
- Temporary collector verification against public read-only Polymarket
  endpoints produced 12 watchlist rows, 24 token midpoint rows, and 12
  aggregate wallet/activity rows.
- The expanded production-like live refresh reports:
  - 20 real closed 5-minute buckets,
  - 12 reviewed watchlist markets,
  - 480 token midpoint rows,
  - 240 aggregate wallet/activity rows,
  - 1'416 scoring rows,
  - 60 summary rows,
  - 0 alerts,
  - baseline readiness `baseline_available_zero_mad_or_non_alerting`,
  - v2 scoring settings `baseline_observations=30` and
    `min_baseline_observations=20`,
  - `production_like_baseline_available=true`,
  - severity counts: 1'416 `none`,
  - status counts: 1'200 `insufficient_baseline` and 216 `zero_mad`.
- `operations/collectors/polymarket_readonly.py` accepts
  `curated_watchlist_path` and uses only accepted rows.
- The latest curated live collector run produced:
  - 3 watchlist rows,
  - 6 token midpoint rows,
  - 3 aggregate wallet/activity rows,
  - 12 scoring rows,
  - 0 alerts,
  - scoring status `insufficient_baseline`.
- The latest curated rolling-history run produced:
  - 3 closed 5-minute buckets,
  - 48 scoring rows,
  - 0 alerts,
  - baseline readiness `diagnostic_scores_available`.
- `data/results/monitor_v2_polymarket_dashboard.html` exists and reports:
  - 3 markets,
  - 4 closed buckets,
  - 0 alerts,
  - baseline readiness `diagnostic_scores_available`.
- The latest production-like refresh reports:
  - 21 real closed 5-minute buckets,
  - 3 reviewed watchlist markets,
  - 126 token midpoint rows,
  - 63 aggregate wallet/activity rows,
  - 372 scoring rows,
  - 0 alerts,
  - baseline readiness `baseline_available_zero_mad_or_non_alerting`,
  - v2 scoring settings `baseline_observations=30` and
    `min_baseline_observations=20`,
  - `production_like_baseline_available=true`,
  - severity counts: 372 `none`,
  - status counts: 300 `insufficient_baseline` and 72 `zero_mad`.
- `operations/collectors/polymarket_monitor_refresh.py` exists and regenerates
  rolling outputs plus dashboard output in one bounded command.
- Safe operator protocol is documented in
  `docs/research/STRATEGY_AGENT_ARCHITECTURE.md` and
  `docs/project/TOOL_USAGE.md`.

## Done Means

- Future non-zero monitor alerts have a documented human-review path before
  they can be used in thesis-facing prose or strategy hypotheses.
- The next decision is whether to implement a compact alert-review artifact or
  run another bounded window after the review workflow exists.
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
  validator, tests, and validation report.
- First Polymarket live watchlist candidates are reviewed against public Gamma
  market metadata; 3 rows are accepted for monitor watchlist use and 0 rows
  remain candidates.
- Read-only Polymarket collector and rolling-history code accept a curated
  watchlist path; candidate, rejected, or needs-followup rows are excluded from
  monitor-ready collection.
- First curated live collector run produced 3 watchlist rows, 6 token midpoint
  rows, 3 aggregate wallet/activity rows, 12 scoring rows, and 0 alerts with
  `insufficient_baseline`.
- Curated rolling-history collection produced 3 real closed 5-minute buckets,
  18 token midpoint rows, 9 aggregate wallet/activity rows, 48 scoring rows,
  0 alerts, and baseline readiness `diagnostic_scores_available`.
- First local read-only monitor dashboard exists under
  `data/results/monitor_v2_polymarket_dashboard.html` with metadata, source
  artifact references, rolling figure, baseline readiness, and alert summary.
- Bounded live monitor refresh runner exists and has refreshed the dashboard
  from 4 real closed 5-minute buckets with 0 alerts and baseline readiness
  `diagnostic_scores_available`.
- Safe live monitor operator protocol exists with preflight, single-refresh,
  diagnostic, and production-like run commands plus interpretation limits.
- First production-like Polymarket live monitor baseline exists with 21 real
  closed 5-minute buckets, 0 alerts, v2 30/20 scoring settings, and baseline
  readiness `baseline_available_zero_mad_or_non_alerting`.
- Production-like live monitor baseline review is accepted: the observed
  zero-alert result is a descriptive Rule C outcome, not evidence that the
  broader market was quiet, efficient, inefficient, causal, or tradeable.
- Threshold-sensitivity outputs exist:
  `monitor_v2_polymarket_threshold_sensitivity.csv`,
  `monitor_v2_polymarket_threshold_sensitivity_by_family.csv`,
  `monitor_v2_polymarket_threshold_sensitivity.png`, and
  `monitor_v2_polymarket_threshold_sensitivity_metadata.json`.
- Threshold-sensitivity review is accepted: keep Rule C unchanged for now;
  the 10/5 diagnostic scenario produced 3 watch rows, but they are not enough
  to justify changing the default monitor rule.
- Curated Polymarket watchlist is expanded from 3 to 12 accepted
  politics/geopolitics markets and the validation report passes with 12
  accepted rows, 0 candidates, 0 rejected rows, and 0 needs-followup rows.
- Expanded Polymarket live baseline is collected with 20 real closed
  5-minute buckets, 12 reviewed markets, 480 token midpoint rows, 240
  aggregate wallet/activity rows, 1'416 scoring rows, 60 summary rows, 0
  alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- Expanded Polymarket live baseline review is accepted: the output shape is
  usable as a short-window prototype baseline, Rule C remains unchanged, and
  0 alerts are interpreted only as no Rule C trigger in the observed window.
- Read-only live monitor dashboard/reporting is improved: the HTML dashboard
  now surfaces run context, baseline settings, scoring row count, summary row
  count, severity counts, status counts, source links, and zero-alert
  interpretation limits.
- Local read-only monitor launcher exists:
  `python -m operations.tools.monitor_dashboard_launcher` returns a structured
  dashboard URI and safety flags, and `--open` can open the dashboard without
  collecting data or activating agents, MCP, ML, database writes, or order
  paths.
- Second expanded Polymarket live monitor window is collected with 20 real
  closed 5-minute buckets, 12 reviewed markets, 480 token midpoint rows, 240
  aggregate wallet/activity rows, 1'416 scoring rows, 60 summary rows, 0
  alerts, and baseline readiness
  `baseline_available_zero_mad_or_non_alerting`.
- Repeated live-window registry exists:
  `data/results/monitor_v2_live_window_registry.csv` and
  `data/results/monitor_v2_live_window_registry_metadata.json` preserve compact
  summaries for the first two expanded live windows.
