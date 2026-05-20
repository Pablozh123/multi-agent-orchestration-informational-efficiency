# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-20 15:49

Current goal: `goal-monitor-v2-contract-001` - Specify near-real-time politics/geo monitor v2 contract

Current roadmap phase: Phase 10: Politics/Geo Anomaly Monitor Prototype

Test status: PASS

Pytest summary: `178 passed in 5.46s`

Git branch: `main`

Latest commit: `a12dff5`

Git status:

```text
 M AGENTS.md
 M GOAL.md
 M ROADMAP.md
 M STATUS.md
 M data/results/thesis_figures_metadata.json
 M docs/project/WORK_LOG.md
 M docs/research/RESEARCH_SPEC.md
 M docs/research/STRATEGY_AGENT_ARCHITECTURE.md
 M docs/research/WHALE_METHOD.md
 M operations/analysis/thesis_figures.py
 M tests/test_thesis_figures.py
?? data/results/thesis_h3_event_wallet_anomalies.png
```

Git diff stat:

```text
 AGENTS.md                                    | 14 ++++++++
 GOAL.md                                      | 46 ++++++++++++++----------
 ROADMAP.md                                   |  8 +++--
 STATUS.md                                    | 36 +++++++++++--------
 data/results/thesis_figures_metadata.json    |  6 ++--
 docs/project/WORK_LOG.md                     | 46 ++++++++++++++++++++++++
 docs/research/RESEARCH_SPEC.md               | 10 ++++++
 docs/research/STRATEGY_AGENT_ARCHITECTURE.md | 42 ++++++++++++++++++++++
 docs/research/WHALE_METHOD.md                | 54 ++++++++++++++++++++++++++++
 operations/analysis/thesis_figures.py        | 42 ++++++++++++++++++++++
 tests/test_thesis_figures.py                 | 23 ++++++++++++
 11 files changed, 288 insertions(+), 39 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- docs: specify near-real-time monitor v2 contract
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
