# STATUS.md

## Current Status

Status date: 2026-05-18

The project is in deterministic data-foundation mode. The deterministic Python
core is being built before H2, H3, agents, MCP, model routing, or ML workflows.

Current test result:

- `115 passed`

Current implemented foundation:

- SQLite schema support tables exist or are migrated idempotently.
- Validation foundation exists for core row types.
- Data inventory module exists.
- First deterministic Brier baseline exists.
- RCP usage in Brier and calibration code is guarded by explicit flags.
- Agent and MCP entry points are deferred.
- Canonical event catalog audit and loader exist.

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

- The repository has many uncommitted foundation changes. Commit history needs
  to be split into atomic commits before new feature work continues.
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

1. `docs: add project control and research specification`
   - Add this document set only.
   - Acceptance: docs exist, no code changes, pytest passes.

2. `chore: commit synchronized architecture and prompt docs`
   - Commit `AGENTS.md`, `PROJECT_CONTEXT.md`, `ARCHITECTURE_DECISIONS.md`,
     directive updates, and legacy inventory.
   - Acceptance: no active prompt conflicts remain.

3. `feat: add deterministic schema migrations`
   - Commit migration layer and schema tests.
   - Acceptance: migrations are idempotent, tests pass.

4. `feat: add validation and inventory foundation`
   - Commit validation modules, data inventory, and related tests.
   - Acceptance: invalid rows fail, inventory CLI works.

5. `test: guard rcp usage behind documented transformation`
   - Commit RCP guardrails and Brier/calibration tests.
   - Acceptance: RCP is excluded by default and requires both explicit flags.

6. `feat: add canonical event catalog audit and loader`
   - Commit event audit, loader, seed CSV, and tests.
   - Acceptance: audit CLI reports current gaps, loader upserts by `event_id`.

