# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 17:54

Current goal: `goal-h2-summary-persistence-001` - Persist reviewed H2 summaries into analysis_summaries

Current roadmap phase: Phase 5: H2 Event Study And CAR

Test status: PASS

Pytest summary: `140 passed in 5.76s`

Git branch: `main`

Latest commit: `4b2b0f9`

Git status:

```text
 M GOAL.md
 M ROADMAP.md
 M STATUS.md
 M docs/project/WORK_LOG.md
 M docs/research/EVENT_SELECTION.md
```

Git diff stat:

```text
 GOAL.md                          | 48 +++++++++++++--------------
 ROADMAP.md                       |  9 +++--
 STATUS.md                        | 71 ++++++++++++++++++++++++----------------
 docs/project/WORK_LOG.md         | 35 ++++++++++++++++++++
 docs/research/EVENT_SELECTION.md | 68 ++++++++++++++++++++++++++++++++++++--
 5 files changed, 172 insertions(+), 59 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- feat: persist h2 summaries in analysis_summaries
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project is in deterministic H2 event-study mode. H2 event windows are
selected, curated seed events exist, and deterministic H2 CSV outputs have been
generated and reviewed for shape. H3, agents, MCP, model routing, and ML remain
deferred.

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
- Compact H2 summary persistence into `analysis_summaries` is not implemented
  yet.
- H3 whale data currently has a BUY-only limitation and a minimum
  `amount_usd` of 10000, so analytical whale tiers are not yet valid.
- Distribution-derived wallet classification is not implemented.
- Granger and lead-time pipelines are not implemented.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `feat: persist h2 summaries in analysis_summaries`
   - Persist compact accepted H2 summaries, not full row-level traces.
   - Acceptance: idempotent writer, tests, no raw table dumps.

2. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.

3. `docs: choose h3 wallet-tier decision rule`
   - Select a distribution-derived wallet-tier method before H3 code.
   - Acceptance: no arbitrary whale thresholds.
