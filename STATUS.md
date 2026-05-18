# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 18:04

Current goal: `goal-h3-tier-method-001` - Select distribution-derived H3 wallet-tier method

Current roadmap phase: Phase 6: H3 Whale Distribution And Classification

Test status: PASS

Pytest summary: `145 passed in 6.05s`

Git branch: `main`

Latest commit: `4be8021`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M STATUS.md
 M docs/project/WORK_LOG.md
 M docs/research/EVENT_SELECTION.md
?? operations/analysis/persist_h2_summaries.py
?? tests/test_h2_summary_persistence.py
```

Git diff stat:

```text
 GOAL.md                          | 49 +++++++++++++++++++-----------------
 ROADMAP.md                       | 13 ++++++----
 STATUS.md                        | 54 +++++++++++++++++++++-------------------
 docs/project/WORK_LOG.md         | 38 ++++++++++++++++++++++++++++
 docs/research/EVENT_SELECTION.md | 30 +++++++++++++++++++---
 5 files changed, 128 insertions(+), 56 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- docs: select h3 wallet-tier method
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project is moving from the deterministic H2 event-study baseline into H3
method selection. H2 event windows are selected, curated seed events exist,
deterministic H2 CSV outputs have been generated, and compact H2 summaries are
persisted into `analysis_summaries`. H3 code remains blocked until the wallet
tier method is selected.

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
- H3 whale data currently has a BUY-only limitation and a minimum
  `amount_usd` of 10000, so analytical whale tiers are not yet valid.
- Distribution-derived wallet-tier selection is not documented yet.
- Granger and lead-time pipelines are not implemented.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `docs: select h3 wallet-tier method`
   - Select one distribution-derived wallet-tier method before H3 code.
   - Acceptance: no arbitrary whale thresholds and BUY-only limitations remain
     separate from analytical tier definitions.

2. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.

3. `feat: inventory wallet distribution for h3 tiering`
   - Compute deterministic wallet/trade distribution summaries needed for H3
     tier implementation.
   - Acceptance: no Granger or lead-lag code yet.
