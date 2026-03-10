# Roadmap: Informationseffizienz dezentraler Pradiktionsmarkte

## Overview

The project builds a multi-agent analysis system to empirically test three hypotheses about Polymarket's
information efficiency relative to FiveThirtyEight and RealClearPolitics during the 2024 US presidential
election. The build order is strictly dependency-driven: data must exist before agents can query it,
agents must be verified before the orchestrator coordinates them, and analysis must be validated before
visualizations are produced. Five phases deliver the complete thesis artifact — from a populated SQLite
database to thesis-ready figures with statistical significance tests.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Foundation** - Populate thesis.db with all source data (Jan-Nov 2024) and lock schema before any analysis
- [ ] **Phase 2: MCP Agent Layer** - Build three read-only FastMCP servers that expose thesis.db to the orchestrator
- [ ] **Phase 3: H1 Analysis — Brier Score and Calibration** - Compute and compare forecast accuracy across all three sources
- [ ] **Phase 4: H2 and H3 Analysis — Event Study and Whale Timing** - Measure information integration speed and whale lead-time
- [ ] **Phase 5: Orchestrator and Reporting** - Coordinate agents via Claude API and produce thesis-ready figures

## Phase Details

### Phase 1: Data Foundation
**Goal**: thesis.db is fully populated with clean, reproducible, look-ahead-bias-free data for Jan-Nov 2024 across all five sources, with WAL mode enabled and schema validated before any analysis begins
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07
**Success Criteria** (what must be TRUE):
  1. Running `SELECT COUNT(*) FROM polymarket_prices` returns at least one row per day for Jan-Nov 2024, and every row has a distinct `price_timestamp` and `fetched_at` field
  2. Running `PRAGMA journal_mode` on thesis.db returns `wal`, and three simultaneous read connections do not produce a lock error
  3. Running `SELECT COUNT(*) FROM poll_forecasts WHERE source='fivethirtyeight'` and `source='rcp'` returns continuous daily rows for Jan-Nov 2024; RCP rows have a `probability` column in [0.0, 1.0]
  4. Running `SELECT COUNT(*) FROM events_timeline` returns >= 20 rows, each with a non-null UTC timestamp and event category label
  5. Running `SELECT COUNT(*) FROM whale_trades WHERE amount_usd >= 10000` returns rows, and no row has a wallet address that appears on the market-maker exclusion list
**Plans**: 7 plans (Wave 0 + Waves 1-2)

Plans:
- [ ] 01-00-PLAN.md — Test infrastructure: pytest.ini, conftest.py, test stubs for all DATA-01..07 requirements (Wave 0)
- [ ] 01-01-PLAN.md — Schema + init_db.py rewrite: WAL mode, 5 schema gap fixes, ingest/__init__.py utilities (Wave 1)
- [ ] 01-02-PLAN.md — Polymarket CLOB ingestion: price_timestamp/fetched_at separation, look-ahead bias prevention (Wave 2)
- [ ] 01-03-PLAN.md — FiveThirtyEight CSV + RCP scraper with logit conversion to [0,1] probabilities (Wave 2)
- [ ] 01-04-PLAN.md — Dune Analytics whale ingestion with market-maker exclusion filter (Wave 2)
- [ ] 01-05-PLAN.md — GDELT DOC API sentiment ingestion, daily granularity, Jan-Nov 2024 (Wave 2)
- [ ] 01-06-PLAN.md — Event catalog: curate 20+ key events with UTC timestamps and category labels (Wave 2)

### Phase 2: MCP Agent Layer
**Goal**: Three FastMCP servers run against thesis.db and return correct, well-typed results for every tool call — verified with real database data, not mocks
**Depends on**: Phase 1
**Requirements**: AGENT-01, AGENT-02, AGENT-03
**Success Criteria** (what must be TRUE):
  1. Calling `market_agent` tool `get_prices` with a valid date range returns a JSON list of price rows; calling `detect_anomalies` returns flagged rows where Z-score > 3
  2. Calling `sentiment_agent` tool `get_sentiment_score` for a specific date returns a GDELT-derived score; calling `get_sentiment_trend` for a window returns a signed delta
  3. Calling `whale_agent` tool `get_large_trades` for a date range returns only trades >= $10k from non-market-maker wallets; calling `get_lead_time_analysis` returns a ranked list of trade-to-event time deltas
  4. All three servers start without error from the orchestrator subprocess pattern and respond within 5 seconds on a cold start against the populated database
**Plans**: TBD

Plans:
- [ ] 02-01: market_agent FastMCP server (Port 8001 — price query, anomaly detection, volume aggregation, AGENT-01)
- [ ] 02-02: sentiment_agent FastMCP server (Port 8002 — GDELT score lookup, trend window, AGENT-02)
- [ ] 02-03: whale_agent FastMCP server (Port 8003 — large trades, wallet timeline, lead-time tools, AGENT-03)

### Phase 3: H1 Analysis — Brier Score and Calibration
**Goal**: H1 is answered with a statistically validated Brier Score comparison and calibration curves for all three sources, with a naive baseline establishing the floor
**Depends on**: Phase 1
**Requirements**: H1-01, H1-02, H1-03, H1-04
**Success Criteria** (what must be TRUE):
  1. `analysis/brier_score.py` produces a daily Brier Score time-series for Polymarket, FiveThirtyEight, and RCP over Jan-Nov 2024, with an assertion that no forecast uses a price timestamped after the evaluation day
  2. `analysis/calibrate.py` produces a reliability diagram (calibration curve) for all three sources in a single comparable plot, using resolved Polymarket market history for sufficient N
  3. A Diebold-Mariano test result (p-value and test statistic) is written to the database or a results file, quantifying whether Brier Score differences are statistically significant
  4. Naive baseline results (always-50% and prior-day-price models) are computed alongside the three sources, providing a lower-bound benchmark visible in the output table
**Plans**: TBD

Plans:
- [ ] 03-01: Brier Score computation and time-series (analysis/brier_score.py — DuckDB, H1-01/H1-04)
- [ ] 03-02: Calibration curves and Diebold-Mariano test (analysis/calibrate.py — H1-02/H1-03)

### Phase 4: H2 and H3 Analysis — Event Study and Whale Timing
**Goal**: H2 and H3 are answered with pre-specified event windows, Granger causality tests, and lead-time histograms — all window choices documented in writing before any code is written
**Depends on**: Phase 1, Phase 2
**Requirements**: H2-01, H2-02, H2-03, H3-01, H3-02, H3-03
**Success Criteria** (what must be TRUE):
  1. A written methodology note (in thesis prose or a pre-analysis document) specifies event windows (+-1h, +-6h, +-24h) and the significance threshold before any H2 or H3 script is executed
  2. `analysis/reaction_speed.py` computes Cumulative Abnormal Returns (CAR) around >= 5 key events from the event catalog and produces an event-study plot showing Polymarket price path vs. 538/RCP update timing
  3. `analysis/whale_timing.py` produces a lead-time histogram (whale trade timestamp minus next price movement >= 5%) across all qualifying whale trades, with market-maker exclusion verified by address lookup
  4. A Granger causality test result (lag selection, F-statistic, p-value) is written to a results file showing whether whale volume Granger-causes Polymarket price changes
**Plans**: TBD

Plans:
- [ ] 04-01: Pre-analysis methodology note — event windows and hypothesis framing (H2-01, process step before code)
- [ ] 04-02: Event study and reaction speed analysis (analysis/reaction_speed.py — CAR, H2-02/H2-03)
- [ ] 04-03: Whale lead-time and Granger causality analysis (analysis/whale_timing.py — H3-01/H3-02/H3-03)

### Phase 5: Orchestrator and Reporting
**Goal**: The orchestrator coordinates all three agents via Claude API for qualitative case-study synthesis, and all thesis-ready figures are rendered at DPI >= 300 with LaTeX-compatible fonts
**Depends on**: Phase 2, Phase 3, Phase 4
**Requirements**: ORC-01, ORC-02, VIS-01
**Success Criteria** (what must be TRUE):
  1. Running the orchestrator against a single flagged event triggers tool calls to all three MCP servers and returns a Claude-synthesized explanation of the divergence, written to the database
  2. When Polymarket price deviates > 10% from GDELT sentiment implication, the orchestrator automatically initiates an analysis run without manual intervention
  3. All four thesis figures (Brier Score time-series, Reliability Diagram, Event Study plot, Whale Lead-Time Histogram) are saved as PNG files at DPI >= 300 using the matplotlib OO API and are visually correct when opened
**Plans**: TBD

Plans:
- [ ] 05-01: Orchestrator MCP coordination and Claude API integration (ORC-01/ORC-02)
- [ ] 05-02: Thesis figure rendering (VIS-01 — matplotlib OO API, DPI >= 300, LaTeX fonts)

## Progress

**Execution Order:**
Phases execute in dependency order: 1 → 2 → 3 → 4 → 5
Note: Phase 3 depends only on Phase 1 (not Phase 2) and can begin as soon as data is ingested.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 0/7 | Planned | - |
| 2. MCP Agent Layer | 0/3 | Not started | - |
| 3. H1 Analysis — Brier Score and Calibration | 0/2 | Not started | - |
| 4. H2 and H3 Analysis — Event Study and Whale Timing | 0/3 | Not started | - |
| 5. Orchestrator and Reporting | 0/2 | Not started | - |
