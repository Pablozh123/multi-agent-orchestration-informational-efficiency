# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 19:22

Current goal: `goal-empirical-baseline-review-001` - Review H1-H3 deterministic baseline before thesis export

Current roadmap phase: Phase 9: Thesis Export

Test status: PASS

Pytest summary: `173 passed in 6.85s`

Git branch: `main`

Latest commit: `e7ea25f`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M STATUS.md
 M docs/project/WORK_LOG.md
 M docs/research/WHALE_METHOD.md
```

Git diff stat:

```text
 GOAL.md                       | 37 ++++++++++++++++++-----------
 ROADMAP.md                    |  9 ++++----
 STATUS.md                     | 54 ++++++++++++++++++++-----------------------
 docs/project/WORK_LOG.md      | 34 +++++++++++++++++++++++++++
 docs/research/WHALE_METHOD.md | 38 ++++++++++++++++++++++++++++++
 5 files changed, 125 insertions(+), 47 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- docs: review h1 h2 h3 empirical baseline
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project now has deterministic daily H1, H2, and H3 baseline outputs. H3
trade analysis includes wallet tiers, daily tiered activity, descriptive
lead-time histograms, lead-lag correlations, and Granger outputs. The active
work is reviewing the complete empirical baseline before thesis export or any
interpretation layer.

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
- H1-H3 baseline outputs still need a coherent thesis-facing review before
  final result tables and interpretation text are prepared.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `docs: review h3 granger outputs and interpretation limits`
   - Commit the H3 Granger interpretation limits, persistence decision, and
     next active goal.
   - Acceptance: H3 claims remain predictive and exploratory.

2. `docs: review h1 h2 h3 empirical baseline`
   - Review all deterministic outputs as one thesis-facing empirical package.
   - Acceptance: thesis-ready result tables and sensitivity gaps are explicit.

3. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.
