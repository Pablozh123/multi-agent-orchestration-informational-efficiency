# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 19:19

Current goal: `goal-h3-granger-review-001` - Review H3 Granger baseline before thesis interpretation

Current roadmap phase: Phase 7: H3 Lead-Lag And Granger Tests

Test status: PASS

Pytest summary: `173 passed in 7.28s`

Git branch: `main`

Latest commit: `ae90e29`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M docs/research/WHALE_METHOD.md
?? data/results/h3_granger_metadata.json
?? data/results/h3_granger_results.csv
?? data/results/h3_lead_lag_correlations.csv
?? operations/analysis/h3_granger_baseline.py
?? tests/test_h3_granger_baseline.py
```

Git diff stat:

```text
 GOAL.md                       | 39 ++++++++++++++++++-----------------
 ROADMAP.md                    |  4 +++-
 docs/research/WHALE_METHOD.md | 48 +++++++++++++++++++++++++++++++++++++++----
 3 files changed, 67 insertions(+), 24 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- docs: review h3 granger outputs and interpretation limits
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project now has a complete deterministic daily H3 baseline for the current
trade extract: wallet tiers, daily tiered activity, descriptive lead-time
histograms, lead-lag correlations, and Granger outputs. The active work is
reviewing H3 interpretation limits before thesis wording or any interpretation
layer is allowed.

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
- H3 result interpretation still needs review for daily-data limits,
  BUY-only source limits, and multiple-testing sensitivity.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `feat: compute h3 lead-lag and granger baseline`
   - Commit the deterministic H3 Granger module, tests, and output artifacts.
   - Acceptance: pytest passes and no proof-of-causality language is added.

2. `docs: review h3 granger outputs and interpretation limits`
   - Review Granger result shape, multiple-testing limits, BUY-only caveat, and
     accepted thesis wording.
   - Acceptance: H3 claims remain predictive and exploratory.

3. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.
