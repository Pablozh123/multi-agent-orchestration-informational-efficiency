# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-05-20 14:49

Current goal: `goal-strategy-backtest-implementation-001` - Implement first deterministic strategy backtest baseline

Current roadmap phase: Phase 10: Strategy Research Prototype

Test status: PASS

Pytest summary: `172 passed in 5.83s`

Git branch: `main`

Latest commit: `04d15dc`

Git status:

```text
 D .planning/PROJECT.md
 D .planning/REQUIREMENTS.md
 D .planning/ROADMAP.md
 D .planning/STATE.md
 D .planning/config.json
 D .planning/phases/01-data-foundation/01-00-PLAN.md
 D .planning/phases/01-data-foundation/01-00-SUMMARY.md
 D .planning/phases/01-data-foundation/01-01-PLAN.md
 D .planning/phases/01-data-foundation/01-01-SUMMARY.md
 D .planning/phases/01-data-foundation/01-02-PLAN.md
 D .planning/phases/01-data-foundation/01-02-SUMMARY.md
 D .planning/phases/01-data-foundation/01-03-PLAN.md
 D .planning/phases/01-data-foundation/01-03-SUMMARY.md
 D .planning/phases/01-data-foundation/01-04-PLAN.md
 D .planning/phases/01-data-foundation/01-04-SUMMARY.md
 D .planning/phases/01-data-foundation/01-05-PLAN.md
 D .planning/phases/01-data-foundation/01-05-SUMMARY.md
 D .planning/phases/01-data-foundation/01-06-PLAN.md
 D .planning/phases/01-data-foundation/01-06-SUMMARY.md
 D .planning/phases/01-data-foundation/01-07-PLAN.md
 D .planning/phases/01-data-foundation/01-08-PLAN.md
 D .planning/phases/01-data-foundation/01-RESEARCH.md
 D .planning/phases/01-data-foundation/01-VALIDATION.md
 D .planning/phases/01-data-foundation/01-VERIFICATION.md
 D .planning/research/ARCHITECTURE.md
 D .planning/research/FEATURES.md
 D .planning/research/PITFALLS.md
 D .planning/research/STACK.md
 D .planning/research/SUMMARY.md
 D data/summaries.json
 D directives/roles/market_agent.md
 D directives/roles/orchestrator.md
 D directives/roles/reviewer.md
 D directives/roles/sentiment_agent.md
 D directives/roles/whale_agent.md
 M docs/legacy_inventory.md
 M docs/project/WORK_LOG.md
 M legacy/audits/LEGACY_SCAN_2026-05-20.md
 D logs/changelog/1b7be1de-9637-4012-9597-c0f81e6701c0.json
 M operations/agents/market_agent.py
 M operations/agents/sentiment_agent.py
 M operations/agents/whale_agent.py
 M operations/project/review_check.py
 M tests/test_market_agent.py
 M tests/test_project_automation.py
 M tests/test_sentiment_agent.py
 M tests/test_whale_agent.py
?? legacy/changelog/
?? legacy/data/
?? legacy/deferred_agents/market_agent.py
?? legacy/deferred_agents/sentiment_agent.py
?? legacy/deferred_agents/whale_agent.py
?? legacy/deferred_prompts/
?? legacy/planning/
```

Git diff stat:

```text
 .planning/PROJECT.md                               |   79 -
 .planning/REQUIREMENTS.md                          |  109 -
 .planning/ROADMAP.md                               |  126 -
 .planning/STATE.md                                 |  107 -
 .planning/config.json                              |   13 -
 .planning/phases/01-data-foundation/01-00-PLAN.md  |  240 -
 .../phases/01-data-foundation/01-00-SUMMARY.md     |  142 -
 .planning/phases/01-data-foundation/01-01-PLAN.md  |  261 --
 .../phases/01-data-foundation/01-01-SUMMARY.md     |  116 -
 .planning/phases/01-data-foundation/01-02-PLAN.md  |  220 -
 .../phases/01-data-foundation/01-02-SUMMARY.md     |  141 -
 .planning/phases/01-data-foundation/01-03-PLAN.md  |  237 -
 .../phases/01-data-foundation/01-03-SUMMARY.md     |   76 -
 .planning/phases/01-data-foundation/01-04-PLAN.md  |  242 -
 .../phases/01-data-foundation/01-04-SUMMARY.md     |  120 -
 .planning/phases/01-data-foundation/01-05-PLAN.md  |  235 -
 .../phases/01-data-foundation/01-05-SUMMARY.md     |  122 -
 .planning/phases/01-data-foundation/01-06-PLAN.md  |  241 -
 .../phases/01-data-foundation/01-06-SUMMARY.md     |  119 -
 .planning/phases/01-data-foundation/01-07-PLAN.md  |  167 -
 .planning/phases/01-data-foundation/01-08-PLAN.md  |  379 --
 .planning/phases/01-data-foundation/01-RESEARCH.md |  514 ---
 .../phases/01-data-foundation/01-VALIDATION.md     |   85 -
 .../phases/01-data-foundation/01-VERIFICATION.md   |  125 -
 .planning/research/ARCHITECTURE.md                 |  380 --
 .planning/research/FEATURES.md                     |  156 -
 .planning/research/PITFALLS.md                     |  319 --
 .planning/research/STACK.md                        |  212 -
 .planning/research/SUMMARY.md                      |  236 -
 data/summaries.json                                | 4740 --------------------
 directives/roles/market_agent.md                   |   33 -
 directives/roles/orchestrator.md                   |   33 -
 directives/roles/reviewer.md                       |   27 -
 directives/roles/sentiment_agent.md                |   33 -
 directives/roles/whale_agent.md                    |   35 -
 docs/legacy_inventory.md                           |   30 +-
 docs/project/WORK_LOG.md                           |   40 +
 legacy/audits/LEGACY_SCAN_2026-05-20.md            |   20 +
 .../1b7be1de-9637-4012-9597-c0f81e6701c0.json      |   31 -
 operations/agents/market_agent.py                  |  133 +-
 operations/agents/sentiment_agent.py               |  104 +-
 operations/agents/whale_agent.py                   |  115 +-
 operations/project/review_check.py                 |    9 +-
 tests/test_market_agent.py                         |   73 +-
 tests/test_project_automation.py                   |   14 +-
 tests/test_sentiment_agent.py                      |   69 +-
 tests/test_whale_agent.py                          |   70 +-
 47 files changed, 174 insertions(+), 10954 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- feat: add deterministic h3 strategy backtest baseline
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
