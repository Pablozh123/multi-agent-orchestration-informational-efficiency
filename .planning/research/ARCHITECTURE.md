# Architecture Patterns

**Domain:** Multi-agent financial analysis system (academic thesis)
**Researched:** 2026-03-09
**Confidence:** HIGH (project constraints are fixed; patterns are well-established)

---

## Recommended Architecture

```
External APIs
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ingestion Layer                          │
│  ingest/polymarket.py   ingest/fivethirtyeight.py           │
│  ingest/dune.py         ingest/gdelt.py   ingest/reddit.py  │
└───────────────────────┬─────────────────────────────────────┘
                        │ writes rows
                        ▼
              data/thesis.db  (SQLite — single source of truth)
                        │
           ┌────────────┼──────────────┐
           │            │              │
           ▼            ▼              ▼
    ┌─────────────┐ ┌───────────┐ ┌──────────────┐
    │market_agent │ │sentiment  │ │ whale_agent  │
    │  MCP :8001  │ │agent :8002│ │   MCP :8003  │
    │             │ │           │ │              │
    │ - prices    │ │ - GDELT   │ │ - tx history │
    │ - anomalies │ │ - Reddit  │ │ - wallet rank│
    │ - volume    │ │ - NewsAPI │ │ - timing     │
    └──────┬──────┘ └─────┬─────┘ └──────┬───────┘
           │              │               │
           └──────────────┼───────────────┘
                          │ MCP tool calls
                          ▼
                 ┌─────────────────┐
                 │  orchestrator   │
                 │  (Claude API)   │
                 │                 │
                 │ - divergence    │
                 │ - H1/H2/H3      │
                 │ - coordination  │
                 └────────┬────────┘
                          │ writes results
                          ▼
              data/thesis.db  (analysis_results table)
                          │
                          ▼
                 ┌─────────────────┐
                 │ analysis/       │
                 │ (DuckDB + pandas│
                 │  + matplotlib)  │
                 └────────┬────────┘
                          │
                          ▼
                 reports/ + thesis/
```

---

## Component Boundaries

| Component | Responsibility | Reads From | Writes To | Communicates With |
|-----------|---------------|------------|-----------|-------------------|
| `ingest/polymarket.py` | Fetch Polymarket CLOB API prices and volume for market Jan–Nov 2024 | Polymarket REST API | `polymarket_prices` | Nothing (fire-and-forget) |
| `ingest/dune.py` | Fetch whale transactions from Dune Analytics (Polygon blockchain) | Dune API | `whale_transactions` | Nothing |
| `ingest/fivethirtyeight.py` | Parse FiveThirtyEight CSV/JSON presidential forecasts | Local CSV or 538 API | `poll_forecasts` | Nothing |
| `ingest/rcp.py` | Parse RealClearPolitics poll averages | RCP scrape or static CSV | `poll_forecasts` | Nothing |
| `ingest/gdelt.py` | Fetch GDELT event/sentiment data for election topics | GDELT API | `sentiment_scores` | Nothing |
| `ingest/reddit.py` | Fetch Reddit posts/comments via PRAW, compute sentiment | Reddit API (PRAW) | `sentiment_scores` | Nothing |
| `mcp_servers/market_agent/` | Expose price analysis, anomaly detection, volume queries as MCP tools | `polymarket_prices` (via SQLite) | None | Orchestrator (MCP protocol) |
| `mcp_servers/sentiment_agent/` | Expose sentiment scores, topic trends as MCP tools | `sentiment_scores` | None | Orchestrator |
| `mcp_servers/whale_agent/` | Expose wallet rankings, pre-move timing analysis as MCP tools | `whale_transactions` | None | Orchestrator |
| `mcp_servers/orchestrator/` | Coordinate agents, call Claude API, detect divergences, drive H1/H2/H3 analysis | All MCP servers + SQLite | `analysis_results` | All three MCP agents, Claude API |
| `analysis/` | Compute Brier scores, calibration curves, reaction time, statistical tests | `data/thesis.db` via DuckDB | `reports/` | Nothing |
| `tests/` | Pytest with mocked API responses | Fixtures | Nothing | Nothing |

**Key constraint:** Ingest scripts are the ONLY components that call external APIs. Everything downstream reads from SQLite exclusively. This guarantees reproducibility — re-running any analysis produces identical results.

---

## Data Flow

### Phase 1 — Ingestion (runs once, then data is frozen)

```
External API → ingest/*.py → SQLite (thesis.db)
```

Each ingestion script:
1. Checks SQLite for existing records (avoid duplicate fetches)
2. Calls external API with pagination
3. Writes raw + normalized rows to SQLite immediately
4. Logs fetch timestamp and record count

The database is the checkpoint. If ingestion fails halfway, restart picks up from last committed rows.

### Phase 2 — MCP Agent Queries (during orchestrator sessions)

```
SQLite → MCP Server (FastMCP tool) → Orchestrator → Claude API
```

Each MCP server exposes read-only tools. Tools accept parameters (time range, market ID, wallet address), query SQLite, and return structured data. The orchestrator composes multi-step analyses by calling multiple tools in sequence, then passes results to Claude for synthesis.

### Phase 3 — Analysis (for thesis output)

```
SQLite → DuckDB (analytical queries) → pandas DataFrame → scipy/statsmodels → matplotlib → reports/
```

DuckDB attaches to the SQLite file and runs columnar aggregations that would be slow in SQLite (e.g., rolling averages, cross-table joins on 300k+ rows). Results flow into pandas for statistical testing, then matplotlib/seaborn for figures.

---

## Patterns to Follow

### Pattern 1: Cached Ingestion with Idempotency Guard

Every ingest function checks for existing data before fetching. Use `INSERT OR IGNORE` with the UNIQUE constraints already on the DB schema (`UNIQUE(timestamp, market_id, token_id)` etc.).

```python
# Correct pattern
conn.execute(
    "INSERT OR IGNORE INTO polymarket_prices (timestamp, market_id, token_id, price, volume) "
    "VALUES (?, ?, ?, ?, ?)",
    (ts, market_id, token_id, price, volume)
)
```

This makes ingestion scripts safe to run multiple times without duplication.

### Pattern 2: MCP Server as a Read-Only Query Layer

Each MCP server should be a thin translation layer: SQL query in, structured Python dict out. No business logic in the MCP layer — logic lives in the orchestrator or analysis scripts.

```python
# market_agent/server.py
from fastmcp import FastMCP
import sqlite3

mcp = FastMCP("market-agent")

@mcp.tool()
def get_price_series(market_id: str, start: str, end: str) -> list[dict]:
    """Gibt Preiszeitreihe fuer einen Markt zurueck."""
    conn = sqlite3.connect("data/thesis.db")
    rows = conn.execute(
        "SELECT timestamp, price, volume FROM polymarket_prices "
        "WHERE market_id = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp",
        (market_id, start, end)
    ).fetchall()
    return [{"timestamp": r[0], "price": r[1], "volume": r[2]} for r in rows]
```

### Pattern 3: Orchestrator Uses Tool Calls, Not Direct DB Access

The orchestrator never queries SQLite directly. It calls MCP tools. This enforces separation of concerns and means the orchestrator logic is testable by mocking tool responses.

```python
# orchestrator/main.py
async def analyze_reaction_speed(event_timestamp: str, market_id: str) -> dict:
    """Analysiert Informationsintegrations-Geschwindigkeit nach einem Event."""
    # Call market agent for price window around event
    prices_before = await market_client.call_tool(
        "get_price_series", {"market_id": market_id,
                             "start": minus_6h(event_timestamp),
                             "end": event_timestamp}
    )
    prices_after = await market_client.call_tool(
        "get_price_series", {"market_id": market_id,
                             "start": event_timestamp,
                             "end": plus_6h(event_timestamp)}
    )
    # Call sentiment agent for same window
    sentiment = await sentiment_client.call_tool(
        "get_sentiment_around", {"topic": "election", "event_time": event_timestamp}
    )
    # Pass to Claude for interpretation
    result = await claude_client.messages.create(...)
    return result
```

### Pattern 4: DuckDB Attaches to SQLite for Analytics

DuckDB can attach a SQLite database as an external source. This avoids copying data while enabling fast columnar queries.

```python
import duckdb

conn = duckdb.connect()
conn.execute("ATTACH 'data/thesis.db' AS thesis (TYPE sqlite)")

# Brier Score calculation across all sources
df = conn.execute("""
    SELECT
        source,
        AVG(POWER(probability - outcome, 2)) AS brier_score
    FROM thesis.poll_forecasts
    JOIN thesis.events_timeline USING (date)
    GROUP BY source
""").df()
```

This pattern (DuckDB + SQLite attachment) is purpose-built for exactly this use case: a research codebase with a local SQLite store that needs analytical performance.

### Pattern 5: aiosqlite for Async MCP Handlers

FastMCP runs async handlers. Use `aiosqlite` (already in requirements.txt) inside MCP tools to avoid blocking the event loop on DB reads.

```python
import aiosqlite

@mcp.tool()
async def get_whale_trades(wallet: str, market_id: str) -> list[dict]:
    """Gibt alle Trades einer Wallet fuer einen Markt zurueck."""
    async with aiosqlite.connect("data/thesis.db") as db:
        async with db.execute(
            "SELECT timestamp, direction, amount_usd, price_at_trade "
            "FROM whale_transactions WHERE wallet_address = ? AND market_id = ?",
            (wallet.lower(), market_id)  # wallets always lowercase per convention
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"timestamp": r[0], "direction": r[1], "amount_usd": r[2], "price": r[3]}
            for r in rows]
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Live API Calls Inside Analysis Scripts

**What:** Calling Polymarket or Dune API directly from an analysis function or notebook.
**Why bad:** Analysis becomes non-reproducible the moment the API changes data, rate-limits, or the market resolves. Breaks the thesis guarantee that results are based on a fixed dataset.
**Instead:** All API calls go through `ingest/`, write to SQLite, and the data is frozen before analysis begins.

### Anti-Pattern 2: Storing Raw API JSON in SQLite BLOB

**What:** Caching raw API JSON as a blob to avoid schema design.
**Why bad:** DuckDB cannot query inside a BLOB. Analysis scripts need structured columns. This turns the DB into a bag of unqueryable bytes.
**Instead:** Normalize on ingestion. The existing schema already does this correctly (price, volume, timestamp as typed columns). Raw samples belong in a `_raw` overflow column only if truly needed for debugging.

### Anti-Pattern 3: Single Monolithic Analysis Script

**What:** One `analysis.py` that does ingestion, scoring, visualization, and report generation.
**Why bad:** Impossible to re-run a single step (e.g., regenerate one figure after tweaking parameters) without running the whole pipeline. Debugging becomes painful.
**Instead:** Separate scripts per hypothesis:
- `analysis/brier_score.py` — H1
- `analysis/reaction_speed.py` — H2
- `analysis/whale_timing.py` — H3
- `analysis/visualize.py` — figures only

### Anti-Pattern 4: MCP Servers With Business Logic

**What:** Putting Brier Score calculations, statistical tests, or divergence detection inside MCP tool handlers.
**Why bad:** MCP servers become hard to test, tightly coupled to analysis logic, and difficult to reason about. The orchestrator should own analysis logic.
**Instead:** MCP tools are thin DB wrappers. Orchestrator (or standalone analysis scripts) own the logic.

### Anti-Pattern 5: Running MCP Servers as Production Services

**What:** Treating the three MCP servers as always-on services that need deployment, health checks, and uptime monitoring.
**Why bad:** This is a thesis, not a product. Operational overhead for zero gain.
**Instead:** Start MCP servers as subprocesses for the duration of an orchestrator run, then shut them down. A simple `subprocess.Popen` in the orchestrator startup suffices.

---

## Suggested Build Order

The dependency chain is strict. Each layer depends on the one above it being functional.

```
1. DB Schema (done — init_db.py exists)
   └── Required by: everything

2. Ingest Layer (ingest/*.py)
   ├── polymarket.py — CLOB API, paginated historical fetch
   ├── dune.py — Dune Analytics API, whale transactions
   ├── fivethirtyeight.py — CSV parsing
   ├── rcp.py — poll averages
   ├── gdelt.py — event/sentiment data
   └── reddit.py — PRAW sentiment
   Required by: MCP servers (need data to query)

3. MCP Servers (one at a time, in order of test complexity)
   ├── market_agent/ — simplest, price data is clean
   ├── sentiment_agent/ — medium, multi-source aggregation
   └── whale_agent/ — hardest, blockchain address parsing
   Required by: orchestrator

4. Orchestrator
   ├── basic: start/stop MCP subprocesses, ping tools
   ├── H2 analysis: reaction speed (market + sentiment agents)
   ├── H3 analysis: whale timing (market + whale agents)
   └── H1 analysis: Brier Score framing (can also be standalone)
   Required by: integrated results in DB

5. Analysis Scripts (independent of MCP servers — read DB directly)
   ├── brier_score.py (H1) — needs poll_forecasts + polymarket_prices
   ├── reaction_speed.py (H2) — needs events_timeline + prices + sentiment
   └── whale_timing.py (H3) — needs whale_transactions + prices

6. Visualization + Reports
   └── All analysis scripts must be complete first
```

**Build order rationale:**
- Ingest before agents: agents have nothing to query until DB is populated.
- Agents before orchestrator: orchestrator MCP clients will fail to connect without running servers.
- Analysis scripts can be built in parallel with agents (they read DB directly), but need populated data.
- Visualization is always last — figures are summaries of completed analysis.

---

## SQLite Schema Assessment

The existing schema (from `init_db.py`) is well-structured for this domain. Key observations:

| Table | Coverage | Index Coverage | Notes |
|-------|----------|---------------|-------|
| `polymarket_prices` | Prices + volume per market/token | `(market_id, timestamp)` composite — correct | UNIQUE constraint prevents duplicate ingestion runs |
| `whale_transactions` | Per-trade blockchain data | `wallet_address` + `timestamp` separately | Consider adding `(market_id, timestamp)` composite for H3 queries |
| `poll_forecasts` | 538 + RCP probability by date | `(date, source)` — correct | `poll_type` column allows distinguishing model vs raw poll average |
| `sentiment_scores` | Multi-source sentiment over time | `(timestamp, source)` — correct | `topic` column enables filtering by "election" vs other topics |
| `events_timeline` | Key events (debates, scandals, endorsements) | None yet | Should add index on `timestamp` for JOIN performance |

Missing table that should be added: `analysis_results` — for storing orchestrator output (Brier scores, timing measurements, divergence events) so they are reproducible and can be referenced in the thesis.

---

## DuckDB Integration Pattern

DuckDB v1.1+ supports SQLite attachment natively. The connection pattern is:

```python
import duckdb

# Open DuckDB in-memory, attach SQLite file as read-only
conn = duckdb.connect()
conn.execute("INSTALL sqlite; LOAD sqlite;")
conn.execute("ATTACH 'data/thesis.db' AS thesis (TYPE sqlite, READ_ONLY TRUE)")

# All thesis tables are now queryable as thesis.<tablename>
result = conn.execute("SELECT * FROM thesis.polymarket_prices LIMIT 5").df()
```

DuckDB is used exclusively in `analysis/` scripts, never inside MCP servers. MCP servers use `aiosqlite` directly. This prevents the complexity of two DB connection types in the same process.

---

## Reproducibility Architecture (Thesis-Critical)

For academic reproducibility, the architecture enforces a strict separation:

```
Mutable zone (can change):         Frozen zone (immutable once collected):
  - External APIs                    - data/thesis.db (after ingestion run)
  - Orchestrator prompts             - ingest/ output
  - Analysis parameters              - reports/ figures

Rule: Once ingestion is complete and the thesis analysis begins,
      data/thesis.db is treated as append-only and the ingestion
      window (Jan–Nov 2024) is closed.
```

Practical implementation: record a `data_collection_completed` timestamp in a `metadata` table when ingestion finishes. Analysis scripts assert this timestamp exists before running. This makes it explicit when the "data is frozen" state was reached.

---

## Sources

- FastMCP documentation and source patterns: HIGH confidence (framework design)
- DuckDB SQLite attachment: HIGH confidence (documented in DuckDB v1.0+ release notes)
- aiosqlite async pattern with FastMCP: HIGH confidence (aiosqlite is the standard solution for async SQLite in Python async contexts)
- Multi-agent orchestration pattern (thin tools, logic in orchestrator): HIGH confidence (established pattern in LLM agent literature)
- SQLite UNIQUE constraints for idempotent ingestion: HIGH confidence (standard SQLite feature)
- Build order rationale: derived directly from dependency analysis, HIGH confidence
