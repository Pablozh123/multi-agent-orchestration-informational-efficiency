# Domain Pitfalls

**Domain:** Prediction Market Analysis / Academic Thesis (Polymarket Informationseffizienz)
**Researched:** 2026-03-09
**Confidence:** HIGH for methodology pitfalls (established literature), MEDIUM for Polymarket-specific API quirks (partially from training data + skill files)

---

## Critical Pitfalls

Mistakes that cause rewrites, invalidate findings, or fail academic review.

---

### Pitfall 1: Look-Ahead Bias in Brier Score Calculations

**What goes wrong:** Calculating Brier Scores using the "final" price snapshot before resolution rather than the price at a specific, consistent timestamp. If you query Polymarket prices retroactively and store only end-of-day prices, you may inadvertently include price adjustments that happened after the "event" you are studying — effectively letting future information contaminate past forecasts.

**Why it happens:** Polymarket prices update continuously. Pulling historical data retroactively and binning it by date without pinning an exact intraday timestamp (e.g., 23:59:59 UTC each day) means the "daily price" may reflect post-event information from that same day. An event at 14:00 UTC and a price snapshot at 23:00 UTC already incorporates the market's reaction — but it looks like a pre-event forecast.

**Consequences:** Polymarket appears more accurate than it really is, because the "pre-event" price you measure already reflects the event. H1 (efficiency) and H2 (reaction speed) both become meaningless.

**Prevention:**
- Define a strict forecast-evaluation time: use the price at exactly T=00:00:00 UTC each day (start-of-day) as "day D forecast."
- Store `fetched_at` and `price_timestamp` as separate fields in SQLite — never conflate them.
- For event studies, only use prices from before the event window opens. Explicitly document the cutoff timestamp for every analysis.
- Add a validation query: `SELECT * FROM prices WHERE price_timestamp > event_time AND labeled_as_pre_event = 1` should return zero rows.

**Detection:** If Polymarket's Brier Score is suspiciously low on high-volatility event days, look-ahead contamination is the first suspect. Cross-check: does removing the event day from the sample materially change the result?

**Phase:** Data ingestion pipeline (Phase 1) — the schema must enforce this from day one. Impossible to fix retroactively without re-fetching all data.

---

### Pitfall 2: Polymarket Price Resolution ≠ Continuous Probability

**What goes wrong:** Treating Polymarket CLOB prices as unbiased probability estimates without accounting for liquidity-adjusted pricing. On thin markets, the mid-price between best bid and best ask can be far from the "true" implied probability. Using the last-trade price is even worse — it may reflect a single small trade that moved a thin book.

**Why it happens:** The Polymarket API returns prices that are order book artifacts, not aggregated market consensus. On the 2024 presidential market (high liquidity), this is less severe — but sub-markets (e.g., "Who wins Pennsylvania by >3%") can have wide bid-ask spreads of 5–15 cents.

**Consequences:** Brier Score comparisons become noise-dominated. A spread of 0.10 on a 0.50 market means your "probability" is anywhere from 0.45 to 0.55 — washing out any real informational signal.

**Prevention:**
- Always store and use the mid-price `(best_bid + best_ask) / 2`, not last-trade price.
- Add a `liquidity_flag` column: mark any market-day where `(best_ask - best_bid) > 0.05` as low-liquidity. Exclude or note separately in analysis.
- Focus primary Brier Score analysis on the highest-liquidity market only: "Who wins the 2024 US Presidential Election?" (POTUS winner market). Treat sub-markets as secondary/sensitivity analysis.
- Store `volume_24h` alongside every price snapshot — use it as a liquidity proxy.

**Detection:** Run `SELECT MIN(best_bid), MAX(best_ask), AVG(best_ask - best_bid) FROM prices GROUP BY market_id` early. Any market with average spread > 0.04 should trigger a liquidity warning.

**Phase:** Data ingestion (Phase 1) + Brier Score analysis (Phase 3).

---

### Pitfall 3: Whale Detection False Positives — Market Makers and Wash Trading

**What goes wrong:** Classifying automated market maker (AMM) rebalancing transactions and wash trading as "informed whale trades." This inflates the apparent predictive power of large wallet activity and produces a spurious H3 result.

**Why it happens:** On Polymarket (Polygon chain), several known addresses are automated liquidity providers that constantly trade both YES and NO tokens to collect spreads. A single AMM can appear as dozens of "large trades" above the $10k threshold. Separately, wash trading (wallet A sells to wallet B, both controlled by the same entity) creates artificial volume that looks like informed flow.

**Consequences:** Whale-trade-timing analysis shows strong "predictive" signals that are actually just market making — the AMM trades continuously, so by chance it always appears "before" price moves. H3 is confirmed but for the wrong reason.

**Prevention:**
- Maintain an explicit exclusion list of known market maker addresses. Cross-reference with Dune community queries and Polymarket documentation. Store in a `wallet_classifications` table with `wallet_type` enum: `['unknown', 'market_maker', 'retail', 'whale_candidate']`.
- Wash trading filter: flag wallets that appear on both the buy and sell side of the same market within a 24-hour window.
- Liquidity provider filter: addresses with >200 trades/day in the same market are almost certainly automated. Exclude from whale analysis.
- For remaining candidates, require that the trade is directional (not balanced YES+NO) and large relative to average daily volume (>2% of 7-day ADV).

**Detection:** If a single wallet ID appears in more than 5% of all large trades, it is likely a market maker. Plot trade frequency per wallet — genuine whales have sparse, episodic activity, not high-frequency patterns.

**Phase:** Whale agent design (Phase 2). Must be baked into the Dune query filters — cannot patch retroactively without rerunning expensive queries.

---

### Pitfall 4: Overfitting to a Single Election Cycle (n=1 Problem)

**What goes wrong:** Drawing strong causal conclusions about prediction market efficiency from a single event (the 2024 US presidential election). A bachelor thesis based on one outcome cannot distinguish "Polymarket is structurally more efficient" from "Polymarket happened to price Trump correctly in 2024."

**Why it happens:** The research design is inherently limited by scope. Researchers then over-claim by using language like "proves" or "demonstrates" rather than "suggests" or "is consistent with."

**Consequences:** Failed defense review. A methodologically literate examiner will immediately note that with one binary outcome, any metric difference could be sampling variance. The thesis appears naive.

**Prevention:**
- Frame every finding explicitly as a case study, not a general claim: "This analysis provides evidence consistent with H1 for the 2024 US presidential election cycle. Generalization requires multi-event replication."
- Use multiple sub-markets within the 2024 cycle to increase N: state-level outcomes, Senate races, etc. This gives 10–50 resolution events instead of 1.
- Report confidence intervals on all Brier Scores, not just point estimates. With a small N, wide CIs are honest and defensible.
- Add a explicit "Limitations" section discussing the single-election scope.

**Detection:** If the thesis conclusion section contains the word "proves" without qualification, the n=1 problem is not adequately addressed.

**Phase:** Research design and hypothesis framing (Phase 0) + writing phase (final). The framing must be correct from the start.

---

### Pitfall 5: P-Hacking via Event Window Selection

**What goes wrong:** Iterating over different event window sizes (±1 hour, ±4 hours, ±12 hours, ±24 hours) until the reaction speed difference between Polymarket and FiveThirtyEight appears statistically significant, then reporting only the "best" window as if it were pre-specified.

**Why it happens:** Event window choice is genuinely ambiguous (how long after a debate does the market "react"?). Without pre-registration or explicit documentation, it is trivially easy to try several windows and report the most flattering result.

**Consequences:** False positive: Polymarket appears to react significantly faster when in reality it does not. This is classic p-hacking and would invalidate H2. If discovered in review, it kills the thesis.

**Prevention:**
- Pre-specify event windows in writing before running any analysis. Document this choice in the thesis methodology section with explicit justification (e.g., "We use a ±6-hour window because most major debate commentary appears within this period — consistent with Wolfers & Zitzewitz (2004)").
- Run sensitivity analysis as an explicit robustness check: "We verify the result holds for windows of ±3h, ±6h, and ±12h." Report all three. If only one works, say so.
- Define "significant reaction" as a >2% price change in a single window, pre-specified, before running the event study code.

**Detection:** If the analysis code contains a loop over event window parameters and only the result for one is reported in the thesis, p-hacking has occurred.

**Phase:** Analysis design (Phase 3). Must be locked before code is written.

---

## Moderate Pitfalls

### Pitfall 6: FiveThirtyEight vs. Polymarket Temporal Misalignment

**What goes wrong:** Comparing daily Polymarket prices with FiveThirtyEight daily forecasts without verifying that "day D" means the same point in time for both. FiveThirtyEight publishes their model output once per day, but the exact publication time is not documented and may vary. Polymarket prices change continuously. If the Polymarket snapshot is taken at 23:00 UTC and FiveThirtyEight published at 14:00 UTC, you are comparing a 9-hour-newer prediction to an older one — systematically biasing Polymarket's Brier Score.

**Prevention:**
- Use FiveThirtyEight's "forecast_date" as the alignment key, and pair it with the Polymarket price at 00:00:00 UTC on the SAME date (i.e., the price before the FiveThirtyEight update).
- Store the alignment logic explicitly in code with comments explaining the convention chosen.
- Document the choice in the thesis methodology section.

**Phase:** Data pipeline and Brier Score calculation (Phase 1, Phase 3).

---

### Pitfall 7: SQLite Write Contention with Concurrent MCP Servers

**What goes wrong:** Four MCP servers (market_agent, sentiment_agent, whale_agent, orchestrator) all writing to `data/thesis.db` simultaneously causes SQLite "database is locked" errors. SQLite's default journal mode (DELETE) only allows one writer at a time.

**Why it happens:** SQLite is not designed for high-concurrency multi-writer scenarios. With four async Python processes each making rapid inserts during data collection, lock timeouts are common.

**Consequences:** Data collection crashes partway through, leaving partial data. Worse: partial writes with no error logging create silently incomplete datasets that corrupt analysis.

**Prevention:**
- Enable WAL mode immediately after opening every SQLite connection: `PRAGMA journal_mode=WAL;`
- Set a generous busy timeout: `PRAGMA busy_timeout=10000;` (10 seconds)
- Use a single "writer" pattern: only the orchestrator writes to SQLite; MCP servers return data as JSON, orchestrator persists it. This is architecturally cleaner and avoids contention entirely.
- For analytical reads, use DuckDB against the SQLite file via DuckDB's SQLite scanner — reads never block writes in WAL mode.

**Detection:** Any `sqlite3.OperationalError: database is locked` in logs. Check early during integration testing.

**Phase:** Architecture design (Phase 1) — WAL pragma must be set in the database initialization code.

---

### Pitfall 8: GDELT Sentiment Noise — Geopolitical Event Contamination

**What goes wrong:** GDELT's event detection algorithm assigns sentiment scores to news events based on CAMEO event codes, not free-text sentiment. A "MAKE STATEMENT" event (code 010) between a US politician and a foreign leader gets scored as a domestic political sentiment signal when it has nothing to do with the election. This creates persistent noise in the sentiment signal.

**Why it happens:** GDELT is designed for international relations research, not election market analysis. The event actor and event target fields are frequently mis-assigned, especially for US political news where international events dominate volume.

**Consequences:** Sentiment-price correlation analysis produces weak or spurious results. The sentiment agent appears to add no value.

**Prevention:**
- Filter GDELT events to: `Actor1CountryCode = 'USA'` AND `Actor2CountryCode = 'USA'` AND `EventCode IN ('14', '15', '17', '18', '19')` (protest, demand, threat categories relevant to elections).
- Supplement or replace GDELT with NewsAPI filtered specifically to US election keywords. GDELT is a secondary source; primary sentiment should come from NewsAPI or Reddit.
- Use a rolling 7-day sentiment window (not daily) to reduce noise. Single-day GDELT sentiment is too noisy to be meaningful.

**Detection:** If the correlation between GDELT sentiment and Polymarket price changes is below |0.05| across the full dataset, GDELT filtering is insufficient.

**Phase:** Sentiment agent design (Phase 2).

---

### Pitfall 9: Reddit Sentiment Survivorship — Subreddit Selection Bias

**What goes wrong:** Choosing Reddit sources (r/politics, r/PredictionMarkets) as if they are neutral signals, when these communities have strong systematic biases. r/politics skews heavily Democratic, meaning sentiment scores will be systematically bearish on Republican outcomes regardless of actual election conditions.

**Why it happens:** Reddit's user base is not a representative sample of the US electorate or of Polymarket users.

**Prevention:**
- Use multiple subreddits representing different political leanings and neutralize by averaging: `r/politics` + `r/Conservative` + `r/PredictionMarkets` + `r/Elections`.
- Do not treat raw sentiment as an absolute signal. Use sentiment *change* (delta week-over-week) rather than absolute sentiment level.
- Document the subreddit selection and its known biases explicitly in the thesis.

**Detection:** If aggregate Reddit sentiment is consistently negative (< 0.3 on a 0–1 scale) even during periods when Polymarket prices Trump above 60%, subreddit bias is distorting the signal.

**Phase:** Sentiment agent design (Phase 2).

---

### Pitfall 10: Brier Score Class Imbalance with Calibration Curve Bins

**What goes wrong:** Using sklearn's `calibration_curve` with `n_bins=10` on a binary election outcome with few resolution events produces calibration curves that are meaningless — most bins contain 0 or 1 data points, and the curve looks perfectly calibrated by accident.

**Why it happens:** Calibration curves require many resolved events across the probability range to be statistically meaningful. With only one binary outcome (Trump wins / Harris wins), you have N=1 per forecast source — that is zero degrees of freedom for calibration analysis.

**Prevention:**
- Use the FULL history of ALL Polymarket markets resolved during Jan–Nov 2024 to build calibration curves, not just the presidential market. Retrieve resolved binary markets from the Gamma API. This gives N>100 resolution events to bin meaningfully.
- For the presidential market specifically, do NOT show a calibration curve. Show time-series Brier Score over the forecast horizon instead (how does accuracy improve as election day approaches).
- When using sub-markets (state-level predictions), document sample size per bin in calibration plots.

**Detection:** If any calibration bin has fewer than 10 observations, that bin is not reliable. Report bin counts as a table alongside the calibration plot.

**Phase:** Analysis scripts (Phase 3).

---

### Pitfall 11: Dune Analytics Free Tier Credit Exhaustion

**What goes wrong:** Running complex Polygon blockchain queries repeatedly during development exhausts the 2,500 monthly Dune credits before the final production data pull, leaving the whale analysis underpowered or requiring a paid tier mid-project.

**Why it happens:** Development and debugging naturally involves many query re-runs. Each execution of a non-cached query costs credits proportional to query complexity.

**Prevention:**
- Develop and debug all Dune queries exclusively on the Dune web interface (no API credit cost) until queries are finalized and verified.
- Use the API only for the final production data pull, immediately cache results in SQLite.
- Maintain a `dune_query_log` table tracking every API call with `credits_used`, `execution_id`, `cached` flag.
- Write a read-from-cache-first pattern: if results for a `(query_id, date_range)` combination already exist in SQLite, never re-execute via API.

**Detection:** Check Dune dashboard credit balance before any API execution. Log balance in the query log table.

**Phase:** Whale agent data collection (Phase 2).

---

### Pitfall 12: Timezone Corruption in SQLite Storage

**What goes wrong:** Storing some timestamps as UTC ISO 8601 strings and others as local time or Unix timestamps (without documentation), then joining tables on timestamp columns — producing off-by-hours errors in event study calculations.

**Why it happens:** Python's `datetime.now()` returns local time; `datetime.utcnow()` is deprecated but still common; `datetime.now(timezone.utc)` is correct but easy to forget. APIs return times in different formats (Polymarket uses Unix ms, GDELT uses YYYYMMDDHHMMSS in UTC, Reddit uses Unix seconds).

**Consequences:** Event reaction timing is off by hours. Polymarket may appear to react "before" a news event simply because the timestamps were in different timezones.

**Prevention:**
- ALL timestamps stored as TEXT in ISO 8601 UTC format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`. No exceptions.
- Use a single utility function for all timestamp normalization: `def to_utc_iso(dt: datetime) -> str` — enforced across the entire codebase.
- Add a database-level CHECK constraint or a startup validation script that verifies all timestamp columns end in 'Z'.
- In the SQLite schema, document the format in the column comment.

**Detection:** Query `SELECT timestamp FROM prices WHERE timestamp NOT LIKE '%Z'` should return 0 rows. Run this as a data quality assertion in the test suite.

**Phase:** Database schema design (Phase 1). Cannot be corrected retroactively without full data re-normalization.

---

## Minor Pitfalls

### Pitfall 13: RealClearPolitics Polling Average Granularity

**What goes wrong:** RCP polling averages update infrequently (sometimes every few days). Using them as a daily forecast source introduces artificial flatness — the "forecast" does not change for 3 days because there is no new data, not because the forecaster is confident. This makes RCP appear stable in comparison to Polymarket without that stability reflecting genuine forecasting quality.

**Prevention:**
- Use the actual poll publication dates, not the RCP average update dates. When no new polls exist for a day, mark the forecast as "stale" with a `data_staleness_days` column.
- Report RCP comparisons separately from FiveThirtyEight comparisons. They are methodologically different (raw average vs. model).

**Phase:** Data ingestion (Phase 1).

---

### Pitfall 14: FastMCP Async I/O Blocking

**What goes wrong:** Making synchronous SQLite calls inside async FastMCP tool handlers blocks the event loop. Under concurrent orchestrator requests, this causes timeouts and missed data.

**Prevention:**
- Use `aiosqlite` for all database operations in MCP server handlers.
- Never call `sqlite3` directly inside an `async def` tool function.
- Test with concurrent client calls in the integration test suite.

**Phase:** MCP server implementation (Phase 2).

---

### Pitfall 15: Polymarket Gamma API Market ID Instability

**What goes wrong:** The Gamma API sometimes creates multiple market entries for what is logically the same event (e.g., "Trump wins 2024 election" appears under different condition IDs after market resets or liquidity migrations). Using market ID as a stable join key produces duplicate or missing rows.

**Prevention:**
- Use `condition_id` (the on-chain identifier) as the primary key, not the Gamma API internal `id`.
- Add a deduplication step in the ingestion pipeline that groups markets by `question_text` similarity and flags duplicates.

**Phase:** Data ingestion (Phase 1).

---

### Pitfall 16: Matplotlib Non-Reproducible Figure State

**What goes wrong:** Calling `plt.figure()` and `plt.plot()` in interactive analysis sessions leaves matplotlib in a shared global state. Running cells out of order in Jupyter produces different figures than running scripts top-to-bottom — figures submitted in the thesis cannot be reproduced by running the analysis script once.

**Prevention:**
- All thesis visualization scripts must use the object-oriented matplotlib API: `fig, ax = plt.subplots()`.
- Each figure-generating function must receive all required data as arguments and return a `Figure` object. No reliance on global `plt` state.
- Add `plt.close('all')` at the start of every visualization script.

**Phase:** Visualization scripts (Phase 4).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| DB schema design | Timezone corruption (P12), SQLite concurrency (P7), timestamp misalignment (P6) | Lock schema with correct UTC convention and WAL mode before first data write |
| Polymarket data ingestion | Look-ahead bias (P1), price resolution (P2), market ID instability (P15) | Use start-of-day snapshots; store mid-price + spread; use condition_id as PK |
| Whale agent / Dune | False positives: market makers (P3), credit exhaustion (P11) | Maintain exclusion list; develop queries on web, API only for final pull |
| Sentiment agent | GDELT noise (P8), Reddit subreddit bias (P9) | Filter GDELT event codes; use multiple subreddits; use delta not absolute |
| Brier Score analysis | Look-ahead bias (P1), class imbalance calibration (P10), FiveThirtyEight misalignment (P6) | Pre-specify evaluation timestamps; use full resolved-markets N for calibration |
| Event study / H2 | P-hacking event windows (P5) | Pre-register window choice before writing analysis code |
| Whale timing / H3 | False positives from AMMs (P3) | Exclude known MM addresses before any timing analysis |
| Thesis writing | n=1 overfitting (P4), look-ahead language | Use "consistent with" not "proves"; report CIs; include Limitations section |
| MCP server implementation | Async blocking (P14) | Use aiosqlite; test concurrent tool calls |
| Visualization | Matplotlib state (P16) | OO API throughout; figure functions return Figure objects |

---

## Sources

- Brier Score methodology: SKILL.md (brier-score), sklearn documentation
- Polymarket API behavior: SKILL.md (polymarket-api), Gamma API and CLOB API documentation
- Dune Analytics constraints: SKILL.md (dune-analytics), Dune free tier credit documentation
- SQLite WAL mode: SQLite official documentation (https://www.sqlite.org/wal.html)
- Event study methodology: Fama et al. (1969) "Adjustment of Stock Prices to New Information"; standard financial econometrics methodology — HIGH confidence
- GDELT data structure: GDELT documentation (https://www.gdeltproject.org/data.html#rawdatafiles) — MEDIUM confidence (API details may have changed)
- P-hacking prevention: pre-registration literature, Gelman & Loken (2014) "The Statistical Crisis in Science" — HIGH confidence for principle, MEDIUM for specific thresholds
- Polymarket market maker behavior: derived from known DeFi AMM patterns on Polygon — MEDIUM confidence (specific address patterns need verification against current Dune community queries)
- Reddit API sentiment bias: well-documented in computational social science literature — HIGH confidence for principle
