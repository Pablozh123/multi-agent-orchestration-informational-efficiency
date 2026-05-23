# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-23 21:32

Current goal: `goal-polymarket-alert-review-workflow-001` - Specify alert-review workflow from compact summaries and wallet reference cases

Current roadmap phase: Phase 10: Politics/Geo Anomaly Monitor Prototype

Test status: PASS

Pytest summary: `310 passed in 15.75s`

Git branch: `main`

Latest commit: `b267236`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M data/results/monitor_reference_candidate_dashboard.html
 M data/results/monitor_reference_candidate_features.csv
 M data/results/monitor_reference_candidate_metadata.json
 M data/results/monitor_reference_candidate_sensitivity_dashboard.html
 M data/results/monitor_reference_candidate_sensitivity_features.csv
 M data/results/monitor_reference_candidate_sensitivity_metadata.json
 M data/results/monitor_reference_candidate_sensitivity_rows.csv
 M data/results/monitor_reference_candidate_sensitivity_similarity_scores.csv
 M data/results/monitor_reference_candidate_sensitivity_similarity_summary.csv
 M data/results/monitor_reference_candidate_sensitivity_summary.csv
 M data/results/monitor_reference_candidate_similarity_scores.csv
 M data/results/monitor_reference_candidate_similarity_summary.csv
 M data/results/monitor_reference_candidate_summary.csv
 M data/results/monitor_v2_live_window_registry.csv
 M data/results/monitor_v2_live_window_registry_metadata.json
 M data/results/monitor_v2_polymarket_dashboard.html
 M data/results/monitor_v2_polymarket_dashboard_metadata.json
 M data/results/monitor_v2_polymarket_live_collection_metadata.json
 M data/results/monitor_v2_polymarket_live_input_validation_report.json
 M data/results/monitor_v2_polymarket_live_market_snapshots.csv
 M data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv
 M data/results/monitor_v2_polymarket_live_watchlist.csv
 M data/results/monitor_v2_polymarket_refresh_metadata.json
 M data/results/monitor_v2_polymarket_rolling_alert_rows.csv
 M data/results/monitor_v2_polymarket_rolling_alert_summary.csv
 M data/results/monitor_v2_polymarket_rolling_history.png
 M data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json
 M data/results/monitor_v2_polymarket_rolling_history_metadata.json
 M data/results/monitor_v2_polymarket_rolling_scoring_metadata.json
 M data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv
 M data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json
 M docs/project/WORK_LOG.md
```

Git diff stat:

```text
 GOAL.md                                            |  19 ++-
 ROADMAP.md                                         |  12 +-
 .../monitor_reference_candidate_dashboard.html     |  16 +-
 .../monitor_reference_candidate_features.csv       |  24 +++
 .../monitor_reference_candidate_metadata.json      |  12 +-
 ..._reference_candidate_sensitivity_dashboard.html |  18 +-
 ...or_reference_candidate_sensitivity_features.csv | 120 +++++++++++++
 ...r_reference_candidate_sensitivity_metadata.json |  24 +--
 ...onitor_reference_candidate_sensitivity_rows.csv |  15 ++
 ...nce_candidate_sensitivity_similarity_scores.csv |  30 ++++
 ...ce_candidate_sensitivity_similarity_summary.csv |  15 ++
 ...tor_reference_candidate_sensitivity_summary.csv |   2 +-
 ...nitor_reference_candidate_similarity_scores.csv |   6 +
 ...itor_reference_candidate_similarity_summary.csv |   3 +
 .../monitor_reference_candidate_summary.csv        |   2 +-
 data/results/monitor_v2_live_window_registry.csv   |   1 +
 .../monitor_v2_live_window_registry_metadata.json  |   6 +-
 data/results/monitor_v2_polymarket_dashboard.html  |  82 ++++-----
 .../monitor_v2_polymarket_dashboard_metadata.json  |  36 ++--
 ...tor_v2_polymarket_live_collection_metadata.json |   8 +-
 ...v2_polymarket_live_input_validation_report.json |  10 +-
 ...monitor_v2_polymarket_live_market_snapshots.csv |  24 +++
 ...or_v2_polymarket_live_wallet_tier_snapshots.csv |  14 +-
 .../monitor_v2_polymarket_live_watchlist.csv       |  24 +--
 .../monitor_v2_polymarket_refresh_metadata.json    |  16 +-
 .../monitor_v2_polymarket_rolling_alert_rows.csv   |  72 ++++++++
 ...monitor_v2_polymarket_rolling_alert_summary.csv | 120 ++++++-------
 .../monitor_v2_polymarket_rolling_history.png      | Bin 133660 -> 139371 bytes
 ...polymarket_rolling_history_figure_metadata.json |  10 +-
 ...tor_v2_polymarket_rolling_history_metadata.json | 188 +++------------------
 ...tor_v2_polymarket_rolling_scoring_metadata.json |  22 ++-
 ...tor_v2_polymarket_rolling_scoring_snapshots.csv |  72 ++++++++
 ...lymarket_rolling_scoring_validation_report.json |  10 +-
 docs/project/WORK_LOG.md                           |  41 +++++
 34 files changed, 697 insertions(+), 377 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- data: add third live monitor window and candidate review outputs
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project now has deterministic daily H1, H2, and H3 baseline outputs, and
the empirical baseline package has been reviewed in
`docs/research/RESEARCH_SPEC.md`. The active work is preparing compact
thesis-facing result summaries before Overleaf export or interpretation-layer
work.

Current implemented foundation and H2 baseline:

- SQLite schema support tables exist or are migrated idempotently.
- Validation foundation exists for core row types.
- Data inventory module exists.
- First deterministic Brier baseline exists.
- RCP usage in Brier and calibration code is guarded by explicit flags.
- Agent and MCP entry points are deferred.
- Canonical event catalog audit and loader exist.
- Project-control automation exists for goal-driven Codex work.
- Deterministic H2 event-window CSV outputs exist under `data/results/`.
- The H2 row-level and summary CSV shapes are accepted for the initial daily
  baseline.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`.
- H3 wallet-tier method is selected as wallet-level cumulative observed
  `amount_usd` percentiles.
- H3 wallet distribution inventory exists under `data/results/`.
- H3 wallet tier classification exists under `data/results/`.
- H3 tiered daily wallet activity series exists under `data/results/`.
- H3 descriptive lead-time histograms exist under `data/results/`.
- H3 daily lead-lag correlations and Granger outputs exist under
  `data/results/`.
- H3 Granger interpretation limits and sensitivity needs are documented.
- H1-H3 empirical baseline review is documented in
  `docs/research/RESEARCH_SPEC.md`.

## Event Catalog Audit Result

Current command:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.event_catalog_audit
```

Current result against `data/thesis.db`:

| Check | Result |
| --- | ---: |
| Row count | 27 |
| Missing `event_id` | 20 |
| Missing `event_date` | 20 |
| Missing `title` | 20 |
| Missing `source_url` | 20 |
| Missing `expected_direction` | 20 |
| Missing `relevance_score` | 20 |
| Invalid canonical dates | 0 |
| Detectable duplicate `event_id` | 0 |
| Detectable duplicate canonical keys | 0 |
| Detectable duplicate legacy keys | 0 |

Interpretation: 20 legacy event rows remain without canonical fields, while
the tracked seed CSV contains the curated 7-event H2 set used for deterministic
output generation. The legacy rows are preserved but are not the default source
for H2 outputs.

## Current Blockers

- RCP is not a native probability forecast. It remains a polling signal until a
  documented and tested probability transformation exists.
- H3 wallet data currently has a BUY-only limitation and a minimum observed
  `amount_usd` of 10000, which remain source-filter metadata rather than
  analytical tier thresholds.
- Thesis-facing H1-H3 result summary tables are not prepared yet.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `docs: review h1 h2 h3 empirical baseline`
   - Commit the empirical baseline review and next active thesis-summary goal.
   - Acceptance: thesis-ready result tables and sensitivity gaps are explicit.

2. `docs: prepare h1 h2 h3 thesis result summaries`
   - Prepare compact, traceable result summaries for thesis drafting.
   - Acceptance: each summary maps to deterministic source artifacts.

3. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.
