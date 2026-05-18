# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 18:52

Current goal: `goal-h3-tiered-activity-series-001` - Prepare H3 tiered wallet activity series

Current roadmap phase: Phase 6: H3 Whale Distribution And Classification

Test status: PASS

Pytest summary: `154 passed in 5.97s`

Git branch: `main`

Latest commit: `5682f31`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M STATUS.md
 M docs/project/WORK_LOG.md
 M docs/research/WHALE_METHOD.md
?? data/results/h3_wallet_tiers.csv
?? data/results/h3_wallet_tiers_metadata.json
?? operations/analysis/classify_wallet_tiers.py
?? tests/test_wallet_tier_classification.py
```

Git diff stat:

```text
 GOAL.md                       | 29 ++++++++++++++----------
 ROADMAP.md                    |  5 +++--
 STATUS.md                     | 52 ++++++++++++++++++++++++++++---------------
 docs/project/WORK_LOG.md      | 40 +++++++++++++++++++++++++++++++++
 docs/research/WHALE_METHOD.md | 38 +++++++++++++++++++++++++++++++
 5 files changed, 132 insertions(+), 32 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- feat: prepare h3 tiered wallet activity series
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project is moving from H3 wallet tier classification into deterministic
tiered wallet activity series. H2 event windows are selected, curated seed
events exist, deterministic H2 CSV outputs have been generated, and compact H2
summaries are persisted into `analysis_summaries`. H3 lead-lag and Granger code
remain blocked until tiered activity inputs are prepared and tested.

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
- Tiered wallet activity series is not implemented yet.
- Granger and lead-time pipelines are not implemented.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `feat: prepare h3 tiered wallet activity series`
   - Join wallet tiers back to trade rows and aggregate activity by day and
     tier.
   - Acceptance: no Granger or lead-lag code yet.

2. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.

3. `feat: compute h3 lead-time histograms`
   - Measure descriptive lead-time distributions after tiered activity inputs
     exist.
   - Acceptance: descriptive timing only, no causal language.
