# Project Research Summary

**Project:** Informationseffizienz dezentraler Pradiktionsmarkte (BA-Thesis)
**Domain:** Academic prediction market efficiency analysis — multi-agent data pipeline
**Researched:** 2026-03-09
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project is a retrospective academic analysis system, not a product. It tests three hypotheses about the 2024 US presidential election: whether Polymarket prices its forecasts more accurately than FiveThirtyEight and RealClearPolitics (H1), whether Polymarket integrates new information faster (H2), and whether large-wallet "whale" trades systematically precede price moves (H3). The right engineering approach for a BA thesis is radical simplicity: a local SQLite database as the single source of truth, data frozen after ingestion, and all analysis reading only from cache. The multi-agent MCP architecture (FastMCP + Anthropic Claude orchestrator) is a non-negotiable project constraint, but it must be treated as a thin query layer over pre-collected data, not as a live analytical system.

The recommended build path is sequential and dependency-driven. Everything blocks on data collection first — MCP agents have nothing to query until the SQLite database is populated. Data ingestion is the riskiest phase because external APIs (Polymarket CLOB, Dune Analytics, GDELT, Reddit/PRAW) all have documented quirks that can corrupt the dataset silently if not handled correctly from day one. The schema must enforce UTC timestamps, mid-price storage, and idempotent upserts before a single API call is made. The statistical analysis layer (Brier Score, event study, Granger causality) is methodologically well-established — the challenge is not the statistics themselves, but ensuring the underlying data is clean enough for the methods to produce valid results.

The primary risks are methodological, not technical. Look-ahead bias (Pitfall 1) and p-hacking in event window selection (Pitfall 5) could invalidate H1 and H2 respectively if not prevented at the schema and analysis-design stages. The n=1 election cycle scope (Pitfall 4) means all findings must be framed as case-study evidence, not causal proof. These risks require decisions before code is written — not after.

---

## Key Findings

### Recommended Stack

The stack is largely fixed by project constraints (Python 3.11+, FastMCP >=3.0, Anthropic SDK, SQLite, DuckDB, matplotlib/seaborn). The key non-obvious choices within those constraints are: `aiosqlite` for async-safe DB access inside FastMCP handlers, DuckDB attached to the SQLite file for analytical queries (10-50x faster than pandas groupby on time-series), and VADER for Reddit sentiment over transformer models (reproducible, fast, no GPU dependency). For blockchain data, the Dune Analytics API is the correct choice over direct web3.py Polygon RPC calls — it provides pre-indexed SQL access to Polymarket contract activity with far less implementation cost.

See `.planning/research/STACK.md` for full stack rationale and version requirements.

**Core technologies:**
- FastMCP >=3.0: MCP server framework for all four agents — project-mandated, decorator-based tool registration
- aiosqlite >=0.20.0: Async SQLite in FastMCP handlers — prevents event loop blocking; MCP handlers are async
- DuckDB >=1.1.0: Analytical queries attached to thesis.db — columnar performance for Brier Score and time-series aggregations over 100k+ rows
- httpx >=0.27.0: Async HTTP for Polymarket CLOB, GDELT, Dune APIs — cleaner than aiohttp, also used internally by Anthropic SDK
- VADER (nltk >=3.9.0): Reddit sentiment scoring — calibrated for informal social media text, reproducible, no GPU needed
- Dune Analytics API: Whale transaction history on Polygon — indexed SQL access, far lower complexity than direct RPC
- scipy + statsmodels + scikit-learn: Hypothesis testing — Wilcoxon/Diebold-Mariano tests, Granger causality, calibration curves

### Expected Features

See `.planning/research/FEATURES.md` for full feature dependency graph and academic rigor notes.

**Must have (table stakes — thesis fails without these):**
- Brier Score computation with proper scoring rule per Murphy (1973) decomposition
- Time-series Brier Score at daily granularity for all three sources (Polymarket, 538, RCP) across Jan-Nov 2024
- Calibration curve (reliability diagram) — requires using full resolved Polymarket market history, not just the presidential market, for sufficient N
- Head-to-head comparison table with statistical significance (Diebold-Mariano test)
- Price interpolation / gap-filling to align continuous Polymarket prices with discrete poll updates
- Event catalog — manually curated, ~20 key events with exact UTC timestamps — required for event study (H2)
- Data caching with idempotent ingestion — all API responses to SQLite before any analysis
- Baseline naive model (prior-day price, always-50%) — required to contextualize any Brier Score
- RCP implied probability conversion — RCP is a poll average, not a probability forecast; must convert explicitly

**Should have (differentiators that justify a full BA thesis):**
- Event study: abnormal price reaction speed (H2) — information half-life comparison, Polymarket vs poll update lag
- Whale trade detection and lead-time analysis (H3) — Dune Analytics queries on Polygon, filtered for market makers
- Sentiment-price correlation — GDELT + Reddit sentiment vs same-day Polymarket price delta
- Anomaly detection on price series — flags >3-sigma moves without catalog events
- Orchestrator divergence detection + Claude API explanations for flagged anomalies

**Defer (v2+ or time-permits):**
- Murphy decomposition (sharpness/resolution separation) — nice academic addition, not required for H1-H3
- Volume-weighted TWAP price series — simple mid-price is sufficient for primary analysis
- Cross-event reproducibility beyond top 5 events
- Interactive visualizations — out of scope per PROJECT.md

### Architecture Approach

The architecture is a strict data-flow pipeline: external APIs -> ingestion scripts -> SQLite (frozen dataset) -> MCP agents (read-only query layer) -> orchestrator (Claude API coordination) -> analysis scripts (DuckDB + statistical libraries) -> figures and reports. The critical constraint is that ingest scripts are the ONLY components that call external APIs. Everything downstream reads exclusively from SQLite. This guarantees academic reproducibility: re-running any analysis on the frozen database produces identical results. MCP servers are thin SQL-to-JSON wrappers with no business logic — all analysis logic belongs in the orchestrator or standalone analysis scripts. MCP servers run as temporary subprocesses for orchestrator sessions, not as production services.

See `.planning/research/ARCHITECTURE.md` for full component boundary table, build order, and code patterns.

**Major components:**
1. `ingest/` scripts (polymarket.py, dune.py, fivethirtyeight.py, rcp.py, gdelt.py, reddit.py) — only components that call external APIs; write normalized rows to SQLite with idempotent upserts
2. MCP servers (market_agent :8001, sentiment_agent :8002, whale_agent :8003) — read-only FastMCP tools over SQLite; thin query layer using aiosqlite
3. Orchestrator (FastMCP + Anthropic Claude API) — calls MCP tools, passes results to Claude for synthesis, writes analysis_results to SQLite; drives H1/H2/H3 coordination
4. Analysis scripts (analysis/brier_score.py, reaction_speed.py, whale_timing.py) — read thesis.db via DuckDB attachment; produce scipy/statsmodels results and matplotlib figures
5. SQLite (data/thesis.db) — single source of truth; WAL mode required; data frozen after ingestion completes

### Critical Pitfalls

See `.planning/research/PITFALLS.md` for full prevention strategies, detection queries, and phase-specific warnings.

1. **Look-ahead bias in Brier Score (Pitfall 1)** — Use start-of-day price (00:00:00 UTC) as "day D forecast." Store `price_timestamp` and `fetched_at` as separate fields. Validate with assertion query before any analysis runs. Must be enforced in schema design — impossible to fix retroactively.

2. **P-hacking via event window selection (Pitfall 5)** — Pre-specify event window (e.g., +-6 hours) in writing before analysis code is written. Run sensitivity analysis across multiple windows (+-3h, +-6h, +-12h) and report all results. If only one window yields significance, say so explicitly.

3. **Whale detection false positives — market makers (Pitfall 3)** — Maintain explicit exclusion list of known AMM/market-maker addresses. Require trades to be directional, >2% of 7-day ADV, from wallets with sparse (not high-frequency) activity. Build into Dune query filters, not post-hoc.

4. **n=1 overfitting (Pitfall 4)** — Frame all findings as "consistent with H1 for 2024 US presidential election cycle." Use multiple sub-markets (state-level outcomes) to increase N to 10-50 resolution events. Report confidence intervals, not just point estimates. Add explicit Limitations section.

5. **SQLite WAL mode / write contention (Pitfall 7)** — Enable `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=10000` in database init. Prefer single-writer pattern: only orchestrator writes analysis results; MCP servers are read-only. Set in init_db.py before any concurrent process touches the DB.

---

## Implications for Roadmap

Based on combined research, the dependency chain is strict: each phase blocks on the previous. A 5-phase structure maps cleanly to the hypothesis and feature dependency tree.

### Phase 1: Data Foundation

**Rationale:** Everything else blocks on a populated, clean SQLite database. Schema errors (timezone corruption, wrong price field, missing market ID stability) are fatal if not caught before ingestion runs. Correcting them requires re-fetching all data. Build the schema correctly once, then freeze.

**Delivers:** Populated thesis.db with price, forecast, whale, sentiment, and event data for Jan-Nov 2024; idempotent ingestion pipeline; event catalog with ~20 key events.

**Addresses features:** Data caching layer, idempotent ingestion, UTC enforcement, price interpolation/gap-filling, event catalog, data provenance metadata, RCP implied probability conversion.

**Avoids pitfalls:** Look-ahead bias (P1 — enforce start-of-day snapshot convention in schema), timezone corruption (P12 — single UTC utility function, database-level CHECK), SQLite WAL mode (P7 — set in init_db.py), market ID instability (P15 — use condition_id as PK), RCP granularity issue (P13 — mark stale forecasts).

### Phase 2: MCP Agent Layer

**Rationale:** Agents need populated data to return anything meaningful. Build one agent at a time in order of complexity: market_agent (cleanest data), then sentiment_agent (multi-source aggregation), then whale_agent (blockchain address handling). Each must be tested with real DB data before the orchestrator is built.

**Delivers:** Three working FastMCP servers exposing read-only tools; whale exclusion list and Dune query filters finalized; sentiment filtering for GDELT and subreddit bias mitigation.

**Uses:** FastMCP >=3.0, aiosqlite >=0.20.0, VADER/NLTK, Dune Analytics API (production pull only after web-interface development).

**Implements:** market_agent, sentiment_agent, whale_agent components.

**Avoids pitfalls:** Async blocking (P14 — aiosqlite in all MCP handlers), GDELT noise (P8 — event code filtering, 7-day rolling window), Reddit bias (P9 — multi-subreddit, delta not absolute), whale false positives (P3 — exclusion list in Dune query), Dune credit exhaustion (P11 — develop on web UI, API only for final pull).

### Phase 3: H1 Analysis — Brier Score and Calibration

**Rationale:** H1 is the core thesis finding. Analysis scripts are independent of MCP servers (they read DB directly via DuckDB). Pre-specify evaluation timestamps and window choices before writing any analysis code to prevent p-hacking.

**Delivers:** Brier Score time-series for Polymarket vs 538 vs RCP; calibration curves (using full resolved-market N, not just presidential market); head-to-head comparison table with Diebold-Mariano significance tests; baseline naive model for contextualization.

**Uses:** DuckDB >=1.1.0 (attached to thesis.db), scipy.stats, scikit-learn calibration_curve, matplotlib/seaborn.

**Implements:** analysis/brier_score.py, analysis/calibrate.py, analysis/visualize.py.

**Avoids pitfalls:** Look-ahead bias (P1 — validation assertion before running), calibration class imbalance (P10 — use full resolved markets for calibration curves), FiveThirtyEight temporal misalignment (P6 — pair 538 forecast date with Polymarket price at 00:00:00 UTC same day), liquidity-adjusted pricing (P2 — mid-price with liquidity_flag).

### Phase 4: H2 and H3 Analysis — Event Study and Whale Timing

**Rationale:** Event study (H2) and whale timing (H3) require the event catalog and whale exclusion list to be finalized in earlier phases. Event window choice must be pre-specified in writing before this phase begins — document the choice in the thesis methodology section first, then write the code.

**Delivers:** Event study results (abnormal price reaction speed, information half-life) across ~5 key events; whale lead-time analysis with Granger causality; sentiment-price correlation; anomaly detection output.

**Uses:** statsmodels (Granger causality, HAC standard errors), scipy.stats, analysis/reaction_speed.py, analysis/whale_timing.py.

**Implements:** H2 and H3 analysis scripts; orchestrator H2/H3 coordination with Claude API.

**Avoids pitfalls:** P-hacking event windows (P5 — pre-specified window with multi-window sensitivity table), whale false positives (P3 — exclusion list already in DB from Phase 2), n=1 framing (P4 — use multiple sub-events).

### Phase 5: Orchestrator Integration and Reporting

**Rationale:** Orchestrator coordination and Claude API integration come last because they depend on all MCP servers running and all analysis patterns being validated. Claude is used for divergence explanation and synthesis, not for primary analysis.

**Delivers:** Working orchestrator that starts MCP subprocesses, coordinates agents, calls Claude API for anomaly explanations; final reports/ figures ready for thesis inclusion; matplotlib figures in OO API format for reproducibility.

**Uses:** Anthropic SDK (AsyncAnthropic), FastMCP orchestrator, matplotlib OO API.

**Avoids pitfalls:** Matplotlib global state (P16 — OO API throughout), MCP servers as production services (anti-pattern from ARCHITECTURE.md — subprocess pattern, not always-on services).

### Phase Ordering Rationale

- Ingest before everything: agents and analysis scripts have no data until thesis.db is populated.
- Schema correctness before ingest: timezone, mid-price, and ID conventions cannot be corrected retroactively without re-fetching all data.
- Analysis scripts (H1) before orchestrator integration (H2/H3): validates that the DB data is analytically usable before building the more complex multi-agent coordination.
- Pre-specification of event windows and hypothesis framing before Phase 4 code: prevents p-hacking at the root.
- Visualization and reporting last: figures summarize completed, validated analysis.

### Research Flags

Phases likely needing deeper research or early validation during planning:

- **Phase 1 (Data Foundation):** Polymarket CLOB API endpoints may have changed since training data — verify `/markets`, `/prices-history`, `/trades` structure before writing ingestion code. PRAW Reddit API post-2023 restrictions may require Pushshift or academic research API for historical data — verify before building sentiment pipeline. GDELT GKG file format for targeted DOC API queries needs verification against current documentation.

- **Phase 2 (MCP Agents):** FastMCP 3.x API surface needs verification (`pip index versions fastmcp`) — the project specifies >=3.0 but 2.x was current as of training data. Dune Analytics free tier credit limit (2,500/month) may constrain development iteration — plan to finalize all queries on the web UI before using the API.

- **Phase 4 (H2/H3 Analysis):** Event window pre-specification must be documented in the thesis methodology section before any code is written for this phase — this is a process requirement, not a technical one.

Phases with standard, well-documented patterns (research-phase can be skipped):

- **Phase 3 (H1 Brier Score):** Brier Score, calibration curves, and Diebold-Mariano tests are canonical methods with established Python implementations in scipy and scikit-learn. No novel patterns needed.

- **Phase 5 (Reporting):** matplotlib OO API and SQLite-to-DuckDB analytical query patterns are fully documented and stable.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Core choices (FastMCP, DuckDB, aiosqlite, scipy) are stable and well-matched to constraints. Polymarket API endpoints and FastMCP 3.x surface need verification before implementation. PRAW Reddit historical access post-2023 restrictions is a known risk. |
| Features | HIGH | Feature list grounded in canonical academic literature (Brier 1950, Murphy 1973, Wolfers & Zitzewitz 2004, Diebold-Mariano 1995). Feature dependency tree is well-understood. Calibration N-requirement (Pitfall 10) is a non-obvious constraint that research surfaced. |
| Architecture | HIGH | Architecture is fixed by project constraints with standard FastMCP multi-agent patterns. Component boundaries, build order, and DuckDB-SQLite integration pattern are all high-confidence. WAL mode and single-writer constraints are documented SQLite behavior. |
| Pitfalls | HIGH (methodology), MEDIUM (API-specific) | Look-ahead bias, p-hacking, n=1 framing, and calibration class imbalance are established methodological pitfalls from academic literature. Polymarket-specific behaviors (market maker addresses, market ID instability, bid-ask spread dynamics) are MEDIUM confidence and need verification against current Dune community queries and Gamma API docs. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Polymarket CLOB API endpoints:** Run a manual verification of `/prices-history` and `/trades` endpoints against current Polymarket documentation before writing ingest/polymarket.py. The API structure in STACK.md is from training data (up to August 2025) and may have changed.

- **FastMCP 3.x API surface:** Run `pip index versions fastmcp` to check current version and review changelog for multi-server coordination patterns before building the orchestrator.

- **Reddit historical data access:** Test PRAW against a target subreddit (r/politics) for 2024 historical data before committing to the PRAW-based pipeline. If access is restricted, Pushshift or Pullpush.io may be required as a fallback for pre-2024 historical data.

- **Dune Analytics whale query design:** Develop and validate the core whale transaction Dune SQL queries on the Dune web interface before touching the API. Finalize the known market-maker exclusion list by cross-referencing current Polymarket Dune community dashboards.

- **RCP implied probability conversion method:** Document the specific logistic conversion method for converting RCP poll averages to implied win probabilities before Phase 3 analysis code is written. This choice affects RCP's Brier Score and should be in the thesis methodology section.

- **Event catalog finalization:** The ~20 key events must be manually curated with exact UTC timestamps from primary sources before Phase 3/4 analysis begins. This is a research task, not a coding task.

---

## Sources

### Primary (HIGH confidence)

- Brier, G.W. (1950). "Verification of forecasts expressed in terms of probability." Monthly Weather Review — canonical Brier Score definition
- Murphy, A.H. (1973). "A new vector partition of the probability score." — Brier Score decomposition
- Campbell, Lo, MacKinlay (1997) "The Econometrics of Financial Markets" Ch. 4 — event study methodology
- Wolfers & Zitzewitz (2004) "Prediction Markets" Journal of Economic Perspectives — canonical framework for prediction market comparison studies
- Diebold, F.X. & Mariano, R.S. (1995). "Comparing predictive accuracy." — forecast accuracy comparison test
- Fama et al. (1969) "Adjustment of Stock Prices to New Information" — event study foundations
- SQLite WAL mode documentation: https://www.sqlite.org/wal.html
- DuckDB SQLite attachment: DuckDB v1.0+ release notes (documented, stable feature)
- Project constraints: `/c/Users/chole/ba-thesis/.planning/PROJECT.md` and `CLAUDE.md`
- Existing dependency list: `/c/Users/chole/ba-thesis/requirements.txt`

### Secondary (MEDIUM confidence)

- Manski (2006) "Interpreting the predictions of prediction markets" — on converting market prices to probabilities; verify applicability to Polymarket CLOB structure
- Gelman & Loken (2014) "The Statistical Crisis in Science" — p-hacking prevention principles
- GDELT documentation (https://www.gdeltproject.org/data.html) — event code structure; API details may have changed
- Training data (Python ecosystem knowledge, up to August 2025) — FastMCP 3.x, Polymarket API structure, Dune Analytics patterns; WebSearch unavailable during research session

### Tertiary (LOW confidence — verify before implementation)

- Polymarket CLOB API endpoint structure (`clob.polymarket.com`) — from training data; must verify against current docs
- Dune Analytics free tier credit limit (2,500/month) — verify current terms before relying on this budget
- Polymarket market maker wallet addresses — derive from current Dune community dashboards, not training data

---

*Research completed: 2026-03-09*
*Ready for roadmap: yes*
