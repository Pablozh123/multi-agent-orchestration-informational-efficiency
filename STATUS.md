# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 14:36

Current goal: `goal-empirical-scope-001` - Define empirical research scope before H2/H3 implementation

Current roadmap phase: Phase 4: Event Catalog And H2 Method

Test status: PASS

Pytest summary: `127 passed in 5.25s`

Git branch: `main`

Latest commit: `0a4e325`

Git status:

```text
 M GOAL.md
 M STATUS.md
 M docs/project/WORK_LOG.md
```

Git diff stat:

```text
 GOAL.md                  |  2 +-
 STATUS.md                | 29 ++++++-----------------------
 docs/project/WORK_LOG.md | 32 ++++++++++++++++++++++++++++++++
 3 files changed, 39 insertions(+), 24 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.
- Do not implement H2/H3 before the empirical scope deliverables are complete.

Next recommended action:

- docs: finalize h2 event selection and window specification
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project is in deterministic data-foundation mode. The deterministic Python
core is being built before H2, H3, agents, MCP, model routing, or ML workflows.

Current implemented foundation:

- SQLite schema support tables exist or are migrated idempotently.
- Validation foundation exists for core row types.
- Data inventory module exists.
- First deterministic Brier baseline exists.
- RCP usage in Brier and calibration code is guarded by explicit flags.
- Agent and MCP entry points are deferred.
- Canonical event catalog audit and loader exist.
- Project-control automation is being added for goal-driven Codex work.

## Event Catalog Audit Result

Current command:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.event_catalog_audit
```

Current result against `data/thesis.db`:

| Check | Result |
| --- | ---: |
| Row count | 20 |
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

Interpretation: legacy event rows exist, but canonical H2 fields are not yet
curated. CAR and event-window analysis must not start until the canonical event
catalog is filled and reviewed.

## Current Blockers

- Canonical event catalog fields are missing for all 20 existing event rows.
- RCP is not a native probability forecast. It remains a polling signal until a
  documented and tested probability transformation exists.
- H2 window definitions and event inclusion rules need sign-off before CAR.
- H3 whale data currently has a BUY-only limitation and a minimum
  `amount_usd` of 10000, so analytical whale tiers are not yet valid.
- Distribution-derived wallet classification is not implemented.
- Granger and lead-time pipelines are not implemented.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `chore: add goal-driven project automation`
   - Commit `operations/project`, tests, and project-control docs.
   - Acceptance: automation CLIs work, review checks pass, pytest passes.

2. `docs: finalize h2 event selection and window specification`
   - Commit research-scope and event-method updates only.
   - Acceptance: event inclusion, exclusion, and windows are fixed before CAR.

3. `data: curate canonical event catalog seed`
   - Commit reviewed event seed rows with source URLs.
   - Acceptance: event audit reports no missing canonical fields for included events.
