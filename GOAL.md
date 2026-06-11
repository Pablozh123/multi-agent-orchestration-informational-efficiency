# GOAL.md

## Active Goal

goal_id: goal-monitor-anomaly-review-queue-001
title: Build deterministic anomaly review queue for politics/geopolitics monitor
status: active
phase: Phase 10: Politics/Geo Anomaly Monitor Prototype
why:
- H1-H3 deterministic baseline outputs and thesis-facing summaries exist.
- The read-only Polymarket monitor has bounded local artifacts for market
  moves, aggregate wallet-tier activity, concentration diagnostics, reference
  similarity, materiality context, and detection-backtest context.
- The Swiss referendum track is running as bounded data collection until the
  14 June 2026 vote and should not receive a new analysis decision before the
  final result is available.
- The next thesis-relevant infrastructure step is a deterministic human-review
  queue that can identify review-worthy anomaly cases without activating
  runtime agents, MCP tools, model routing, ML, database writes, or trading
  paths.
deliverables:
- Add a deterministic anomaly review queue over existing bounded monitor
  artifacts.
- Generate `data/results/monitor_anomaly_review_queue.csv`.
- Generate `data/results/monitor_anomaly_review_summary.csv`.
- Generate `data/results/monitor_anomaly_review_metadata.json`.
- Generate `data/results/monitor_anomaly_review_dashboard.html`.
- Generate `data/results/monitor_anomaly_case_review_packets.csv`.
- Generate `data/results/monitor_anomaly_case_review_packets.json`.
- Add `data/monitor_anomaly_review_status_updates.csv` as the curated manual
  review-status worksheet that can update queued cases deterministically.
- Record manual source-check status for all current anomaly-review cases
  without upgrading them to thesis-facing evidence.
- Include case fields for market slug, review priority, trigger family,
  market-move context, wallet-flow context, concentration context, event
  context, reference overlap, review label, missing evidence, reviewer,
  source URLs, review notes, allowed interpretation, and blocked claims.
- Keep `insider_risk_review_candidate` as an internal human-review label only,
  never as proof, fact, causal evidence, misconduct finding, or trading signal.
- Document future agent and MCP access as contract-only: bounded summaries,
  max 50 rows, no raw SQL, no wallet-address exposure by default, no order or
  trading paths, and later `llm_audit_log` logging.
scope:
- `operations/analysis/monitor_anomaly_review_queue.py`.
- `tests/test_monitor_anomaly_review_queue.py`.
- `data/monitor_anomaly_review_status_updates.csv`.
- `data/results/monitor_anomaly_review_*`.
- `docs/research/STRATEGY_AGENT_ARCHITECTURE.md`.
- `ROADMAP.md`.
- Project workflow docs/status/log updates required before stopping.
out_of_scope:
- Trading, order placement, order cancellation, authenticated user channels,
  trading credentials, PnL, profitability claims, strategy backtests, cloud
  deployment, resident background daemons, active runtime agents, active MCP
  demo layers, model routing, ML, and database writes.
- Calculating metrics with LLMs or agents.
- Exposing raw monitor rows, wallet addresses, unrestricted SQL, or more than
  50 rows through any future default tool surface.
- Claiming causality, market inefficiency, private information, misconduct, or
  insider activity from anomaly labels.
acceptance_criteria:
- Exactly one active goal remains in this file.
- The queue is generated only from existing bounded deterministic artifacts.
- Outputs contain no wallet-address columns and no order instructions.
- Review priorities use existing monitor severity and distribution-based
  percentile ranks, not arbitrary whale thresholds.
- The queue contains the planned review fields and a deterministic status
  update helper for human-review state changes.
- Case-review packets expose bounded per-case review summaries for later
  human, MCP, or agent reading without activating MCP or agents.
- The review-status worksheet is validated, rejects duplicate case IDs and
  invalid statuses, and is merged into the generated queue, including
  `source_check_pending` entries for all current queued cases.
- Future agent and MCP contracts remain metadata/documentation only and do not
  activate guarded runtime entry points.
- Tests cover queue creation, summary counts, case-review packets,
  wallet-address rejection, future MCP/agent contract flags, and review-status
  updates.
- `STATUS.md` and `docs/project/WORK_LOG.md` are updated before stopping work.
- Review checks pass before recommending a commit.
next_commit: feat: add anomaly case review packets

## Running Side Goal

- `goal-swiss-referendum-efficiency-001` remains a running data-collection
  track until the 14 June 2026 vote. Do not add new referendum interpretation
  decisions before the final result is available.

## Paused Previous Goal

- `goal-monitor-detection-backtest-wallet-graph-001` remains paused as a broad
  monitor expansion goal. The current active goal builds a bounded review queue
  on top of its existing deterministic outputs.
