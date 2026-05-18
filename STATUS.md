# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-18 18:22

Current goal: `goal-h3-wallet-tier-classification-001` - Implement H3 wallet tier classification

Current roadmap phase: Phase 6: H3 Whale Distribution And Classification

Test status: PASS

Pytest summary: `150 passed in 5.83s`

Git branch: `main`

Latest commit: `eca70c2`

Git status:

```text
clean
```

Git diff stat:

```text
no unstaged diff
```

Blockers:

- None detected.

Next recommended action:

- feat: classify h3 wallets by distribution tier
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project is moving from H3 wallet distribution inventory into deterministic
wallet tier classification. H2 event windows are selected, curated seed events
exist, deterministic H2 CSV outputs have been generated, and compact H2
summaries are persisted into `analysis_summaries`. H3 lead-lag and Granger code
remain blocked until wallet tiers are implemented and tested.

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
- Wallet tier classification is not implemented yet.
- Granger and lead-time pipelines are not implemented.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `feat: classify h3 wallets by distribution tier`
   - Apply selected percentile thresholds to wallet-level aggregates.
   - Acceptance: no Granger or lead-lag code yet.

2. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.

3. `feat: prepare h3 tiered wallet activity series`
   - Aggregate wallet activity by selected tier for later timing analysis.
   - Acceptance: no causal language and no Granger code yet.
