# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-06-12 01:05

Current goal: `goal-monitor-anomaly-review-queue-001` - Build deterministic anomaly review queue for politics/geopolitics monitor

Current roadmap phase: Phase 10: Politics/Geo Anomaly Monitor Prototype

Test status: PASS

Pytest summary: `488 passed in 50.42s`

Git branch: `main`

Latest commit: `6ecb03c`

Git status:

```text
 M STATUS.md
 M data/literature/literature_index.csv
 M data/results/swiss_referendum_10mio_auto_refresh_log.csv
 M data/results/swiss_referendum_10mio_auto_refresh_metadata.json
 M data/results/swiss_referendum_10mio_comparison.csv
 M data/results/swiss_referendum_10mio_dashboard.html
 M data/results/swiss_referendum_10mio_efficiency.png
 M data/results/swiss_referendum_10mio_efficiency_metadata.json
 M data/results/swiss_referendum_10mio_latest_source_comparison.csv
 M data/results/swiss_referendum_10mio_latest_summary.md
 M data/results/swiss_referendum_10mio_polymarket_price_history_metadata.json
 M data/results/swiss_referendum_10mio_polymarket_snapshot_metadata.json
 M data/results/swiss_referendum_10mio_polymarket_snapshots.csv
 M data/results/swiss_referendum_10mio_refresh_metadata.json
 M data/results/swiss_referendum_10mio_running_status.json
 M docs/project/WORK_LOG.md
 M docs/project/dozentenbericht_ba_thesis.docx
 M docs/project/dozentenbericht_ba_thesis.html
 M docs/project/dozentenbericht_ba_thesis.md
 M operations/project/build_dozenten_report.py
```

Git diff stat:

```text
 STATUS.md                                          |  46 +-
 data/literature/literature_index.csv               |   4 +
 .../swiss_referendum_10mio_auto_refresh_log.csv    |   7 +
 ...iss_referendum_10mio_auto_refresh_metadata.json |  40 +-
 data/results/swiss_referendum_10mio_comparison.csv |   7 +
 data/results/swiss_referendum_10mio_dashboard.html |  33 +-
 data/results/swiss_referendum_10mio_efficiency.png | Bin 84509 -> 84718 bytes
 ...swiss_referendum_10mio_efficiency_metadata.json |  12 +-
 ...s_referendum_10mio_latest_source_comparison.csv |   6 +-
 .../swiss_referendum_10mio_latest_summary.md       |  18 +-
 ...um_10mio_polymarket_price_history_metadata.json |   2 +-
 ...erendum_10mio_polymarket_snapshot_metadata.json |  12 +-
 ...swiss_referendum_10mio_polymarket_snapshots.csv |   7 +
 .../swiss_referendum_10mio_refresh_metadata.json   |  33 +-
 .../swiss_referendum_10mio_running_status.json     |  14 +-
 docs/project/WORK_LOG.md                           | 150 +++++
 docs/project/dozentenbericht_ba_thesis.docx        | Bin 7435625 -> 7441088 bytes
 docs/project/dozentenbericht_ba_thesis.html        |  66 ++-
 docs/project/dozentenbericht_ba_thesis.md          |  93 ++-
 operations/project/build_dozenten_report.py        | 649 ++++++++++++++++++++-
 20 files changed, 1066 insertions(+), 133 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.

Next recommended action:

- docs: add anomaly review access contract
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
