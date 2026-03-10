# Phase 1: Data Foundation - Research

**Researched:** 2026-03-10
**Domain:** SQLite schema design, data ingestion pipelines, Polymarket CLOB API, FiveThirtyEight CSV, RCP poll scraping, Dune Analytics, GDELT sentiment
**Confidence:** HIGH for schema fixes and SQLite patterns; MEDIUM for Polymarket API specifics and FiveThirtyEight data availability

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Polymarket prices (Jan-Nov 2024) via CLOB API cached in SQLite with strict `price_timestamp`/`fetched_at` separation | CLOB `/prices-history` endpoint confirmed public; response fields `t` (timestamp) and `p` (price) verified; schema fix required |
| DATA-02 | SQLite WAL mode supporting simultaneous reads by 3 MCP servers without lock errors | WAL PRAGMA syntax verified from SQLite official docs; `busy_timeout` setting documented |
| DATA-03 | FiveThirtyEight model probabilities 2024 imported as daily time series into `poll_forecasts` | GitHub repo at fivethirtyeight/data confirmed; 2024 polling averages CSVs available; column structure needs verification at ingestion time |
| DATA-04 | RealClearPolitics poll averages scraped/imported and transformed via logit to 0.0-1.0 probabilities | `realclearpolitics` PyPI package exists; `scipy.special.expit` for logit-to-probability conversion verified |
| DATA-05 | Whale transactions (>$10k) from Dune Analytics with market-maker exclusion list | Multiple Polymarket Dune dashboards confirmed; `market_maker_exclusions` table required in schema; exclusion list sources identified |
| DATA-06 | GDELT sentiment scores for US Election 2024 keywords at daily granularity in `sentiment_scores` | `gdelt` PyPI package verified; GKG files available at 15-min intervals; GDELT DOC API preferred over bulk download |
| DATA-07 | `events_timeline` with >= 20 curated key events with UTC timestamps and category labels | Manual curation required; `event_category` column missing from current schema; ~20 events specified |
</phase_requirements>

---

## Summary

Phase 1 is entirely a data engineering phase: fix the existing schema, populate all five data sources for the Jan-Nov 2024 window, and validate completeness before any analysis begins. The existing `init_db.py` has five concrete gaps that must be repaired before any data is written — these are not optional improvements, they are correctness requirements that downstream success criteria directly test.

The Polymarket CLOB API at `https://clob.polymarket.com/prices-history` is public (no auth for reads) and confirmed active. The critical known limitation is that resolved markets only return data at 12-hour or coarser granularity — daily (fidelity=1440) snapshots are achievable and sufficient for Brier Score analysis. The Gamma API at `gamma-api.polymarket.com` provides market metadata including `condition_id`, which must be used as the stable join key (not the Gamma internal `id`). FiveThirtyEight 2024 polling average CSVs exist in their public GitHub repository. RCP data requires scraping via the `realclearpolitics` PyPI package. GDELT is free and available without a key but bulk GKG files are large; the GDELT DOC API provides targeted queries. Dune Analytics has community-built Polymarket dashboards that can be adapted for whale queries.

The WAL mode PRAGMA must be the very first thing executed after opening the database connection in `init_db.py`. This is a property stored in the database file itself and is persistent once set. The `busy_timeout` of 10,000ms should accompany it. All other schema changes (column renames, new tables) must happen in the same initialization script before any ingest script writes a single row.

**Primary recommendation:** Fix `init_db.py` completely (all five schema gaps) as Wave 0 before writing any ingest script. The schema is the foundation all other work rests on — a schema error discovered after ingestion requires re-fetching all data.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sqlite3 | stdlib | Primary database write operations | Already in Python, zero setup; WAL mode + UNIQUE constraints handle concurrency and idempotency |
| aiosqlite | >=0.20.0 | Async SQLite for MCP server handlers (Phase 2) | Prevents blocking the FastMCP event loop; already in requirements.txt |
| duckdb | >=1.1.0 | Analytical queries over SQLite during analysis phase | SQLite ATTACH syntax verified; columnar engine 10-50x faster for aggregations |
| httpx | >=0.27.0 | HTTP client for Polymarket CLOB/Gamma APIs and GDELT | Already in requirements.txt; async support; used by Anthropic SDK |
| pandas | >=2.2.0 | FiveThirtyEight/RCP CSV parsing and reshaping | Handles date parsing, column renaming, type coercion in a few lines |
| scipy | >=1.14.0 | Logit-to-probability conversion for RCP data | `scipy.special.expit(x)` is the inverse logit; `scipy.special.logit(p)` for forward |
| python-dotenv | >=1.0.0 | Load DUNE_API_KEY from .env | Already in requirements.txt; never hardcode keys |
| tqdm | >=4.66.0 | Progress bars during multi-hour ingestion runs | GDELT historical fetch can take many minutes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| py-clob-client | latest | Official Polymarket Python client (optional) | Can use raw httpx instead; py-clob-client wraps the same REST API |
| gdelt (gdeltPyR) | PyPI | Python wrapper for GDELT data retrieval | Simplifies date-range queries; alternatively, direct HTTP to `data.gdeltproject.org` |
| realclearpolitics | PyPI | Scrape RCP poll averages to CSV | CLI: `realclearpolitics <url> -o output.csv`; also has Python API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| raw httpx for Polymarket | py-clob-client | py-clob-client is official but adds a dependency; raw httpx gives full control and is already in requirements.txt |
| gdelt PyPI package | Direct HTTP to data.gdeltproject.org | Direct HTTP avoids an unvetted dependency; GDELT PyPI package simplifies date range handling |
| realclearpolitics PyPI | Manual HTML scrape | PyPI package is maintained; manual scrape is brittle but gives more control |

**Installation:**
```bash
source .venv/bin/activate
# All core packages already in requirements.txt
pip install -r requirements.txt

# Optional: official Polymarket client
pip install py-clob-client

# If using GDELT Python package
pip install gdelt
```

---

## Architecture Patterns

### Recommended Project Structure
```
ba-thesis/
├── init_db.py               # REWRITE: schema + WAL mode + all tables
├── ingest/
│   ├── __init__.py
│   ├── polymarket.py        # CLOB API -> polymarket_prices
│   ├── fivethirtyeight.py   # CSV -> poll_forecasts (source='fivethirtyeight')
│   ├── rcp.py               # Scrape -> poll_forecasts (source='rcp')
│   ├── dune.py              # Dune API -> whale_trades + market_maker_exclusions
│   ├── gdelt.py             # GDELT API -> sentiment_scores
│   └── events.py            # Static JSON -> events_timeline (manual curation)
├── data/
│   └── thesis.db            # Single source of truth (WAL mode, fixed schema)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures: in-memory DB, mocked API responses
│   ├── fixtures/            # Saved API response JSON for offline testing
│   │   ├── polymarket_prices_sample.json
│   │   ├── dune_whale_sample.json
│   │   └── gdelt_sample.json
│   ├── test_init_db.py      # Validates schema, WAL mode, table existence
│   ├── test_ingest_polymarket.py
│   ├── test_ingest_538.py
│   ├── test_ingest_rcp.py
│   ├── test_ingest_dune.py
│   └── test_ingest_gdelt.py
```

### Pattern 1: WAL Mode + Busy Timeout Initialization
**What:** Enable WAL mode and busy timeout as the very first pragma executed on a new database connection
**When to use:** In `init_db.py` and at the top of every ingest script that opens the database
**Example:**
```python
# Source: https://sqlite.org/wal.html
import sqlite3

def get_connection(db_path: str) -> sqlite3.Connection:
    """Oeffnet eine SQLite-Verbindung mit WAL-Modus und Busy-Timeout."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")  # 10 seconds
    conn.execute("PRAGMA synchronous=NORMAL;")   # faster writes, safe with WAL
    return conn
```
WAL mode is persistent once set on the file — subsequent connections do not need to set it again, but setting it idempotently is safe and documents intent.

### Pattern 2: Idempotent Ingestion with INSERT OR IGNORE
**What:** All ingest scripts check for existing data via UNIQUE constraints, never re-inserting duplicate rows
**When to use:** Every INSERT in every ingest script
**Example:**
```python
# Pattern: idempotent write with UNIQUE constraint
conn.execute(
    """INSERT OR IGNORE INTO polymarket_prices
       (price_timestamp, fetched_at, market_id, token_id, price, volume_24h, best_bid, best_ask)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (price_ts, fetched_at, market_id, token_id, price, volume, bid, ask)
)
```
The UNIQUE constraint on `(price_timestamp, market_id, token_id)` makes this safe to run multiple times.

### Pattern 3: Separate `price_timestamp` from `fetched_at`
**What:** Two distinct timestamp columns — when the price was observed vs. when we fetched it
**When to use:** polymarket_prices table only; critical for look-ahead bias prevention
**Example:**
```python
from datetime import datetime, timezone

def to_utc_iso(ts_unix: int) -> str:
    """Konvertiert Unix-Timestamp (ms) in UTC ISO 8601 String."""
    dt = datetime.fromtimestamp(ts_unix / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

# price_timestamp: the 't' field from CLOB API (when price existed)
# fetched_at: datetime.now(timezone.utc) at time of API call
price_ts = to_utc_iso(api_row["t"])
fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
```

### Pattern 4: Logit Conversion for RCP Poll Averages
**What:** Convert percentage poll averages (e.g., 52.3%) to implied probabilities (0.0-1.0) using logistic function
**When to use:** `ingest/rcp.py` only; document the conversion in thesis methodology
```python
from scipy.special import expit
import numpy as np

def poll_pct_to_probability(trump_pct: float, harris_pct: float) -> float:
    """Konvertiert RCP-Umfrageprozente in eine Gewinnwahrscheinlichkeit via Logit-Skalierung."""
    # Margin: positive = Trump advantage
    margin = (trump_pct - harris_pct) / 100.0
    # Scale margin to logit space; 0 margin -> 0.5 probability
    # Scaling factor 4.0 calibrated to typical election polling spreads
    return float(expit(margin * 4.0))
```
**Note:** The exact scaling factor is a methodological choice that must be documented explicitly in the thesis. An alternative is direct normalization: `trump_pct / (trump_pct + harris_pct)`. Both approaches should be compared in a sensitivity table.

### Pattern 5: DuckDB Attaches SQLite for Validation Queries
**What:** Use DuckDB to run analytical validation queries against the completed database
**When to use:** Post-ingestion validation scripts; not inside ingest scripts
```python
import duckdb

# Source: DuckDB SQLite extension documentation
conn = duckdb.connect()
conn.execute("INSTALL sqlite; LOAD sqlite;")
conn.execute("ATTACH 'data/thesis.db' AS thesis (TYPE sqlite, READ_ONLY TRUE)")

# Validate DATA-01 success criterion
row_count = conn.execute(
    "SELECT COUNT(*) FROM thesis.polymarket_prices"
).fetchone()[0]
assert row_count > 0, "polymarket_prices ist leer"
```

### Anti-Patterns to Avoid
- **Using `timestamp` as the column name:** The old schema uses `timestamp` in `polymarket_prices`. This must become `price_timestamp`. `timestamp` is also an SQLite keyword — avoid it as a column name.
- **Setting WAL mode after creating tables:** WAL mode must be set before any table creation or the database may be initialized in default journal mode.
- **Storing wallet addresses as mixed case:** All blockchain wallet addresses must be lowercased on ingestion per CLAUDE.md convention.
- **Using `datetime.utcnow()`:** Deprecated in Python 3.12. Use `datetime.now(timezone.utc)` only.
- **Fetching Dune API during development:** Use Dune web UI to develop and test SQL queries (no credit cost). Only call the API for the final production data pull.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retries with backoff | Custom retry loop | `httpx` with built-in timeout + `tenacity` or simple loop | Polymarket API can return 429; hand-rolled backoff misses edge cases |
| Logit conversion math | Manual `log(p/(1-p))` | `scipy.special.expit` / `scipy.special.logit` | SciPy handles edge cases (0.0, 1.0 inputs) without division-by-zero |
| CSV column detection | Custom parser | `pandas.read_csv` with dtype specification | Header detection, encoding, NA handling all handled |
| Unix ms timestamp conversion | Manual arithmetic | `datetime.fromtimestamp(ts/1000, tz=timezone.utc)` | Handles DST, timezone correctly; explicit ms division documented |
| Database connection pooling | Custom pool | Direct `sqlite3.connect()` per operation | SQLite is file-based; connection pooling adds complexity with no benefit for single-writer pattern |
| WAL checkpoint management | Manual PRAGMA wal_checkpoint | SQLite automatic checkpoint (default threshold 1000 pages) | Automatic checkpointing is correct for this workload; manual only needed at controlled shutdown |

**Key insight:** This phase is all I/O and schema — the complexity is in the data sources and their quirks, not in algorithms. Use established libraries for every mechanical operation so that attention can focus on data quality and correctness.

---

## Common Pitfalls

### Pitfall 1: Schema Written to Existing DB Without Dropping Old Tables
**What goes wrong:** Running the revised `init_db.py` on an existing `data/thesis.db` that already has old tables (e.g., `whale_transactions` instead of `whale_trades`). `CREATE TABLE IF NOT EXISTS` silently succeeds with the old schema — both table names exist, nothing fails, but ingest scripts writing to `whale_trades` produce different data than whatever reads from `whale_transactions`.
**Why it happens:** The IF NOT EXISTS guard prevents errors but also prevents schema migration.
**How to avoid:** Either delete `data/thesis.db` before running the revised `init_db.py`, or include an explicit migration: `ALTER TABLE whale_transactions RENAME TO whale_trades;`. Given the DB is currently empty, deletion is simpler.
**Warning signs:** `SELECT name FROM sqlite_master WHERE type='table'` returns both `whale_transactions` and `whale_trades`.

### Pitfall 2: Polymarket Resolved Market 12-Hour Granularity Floor
**What goes wrong:** Requesting fidelity < 720 minutes (12 hours) for the resolved 2024 presidential market returns an empty `history` array — confirmed in py-clob-client GitHub issue #216.
**Why it happens:** Polymarket stores resolved market price history at coarser granularity than active markets.
**How to avoid:** Use `fidelity=1440` (daily) for the Jan-Nov 2024 presidential market. This is sufficient for Brier Score analysis. Document this limitation explicitly in the thesis data section.
**Warning signs:** `GET /prices-history?market=<token_id>&interval=max&fidelity=60` returns `{"history": []}`.

### Pitfall 3: FiveThirtyEight 2024 General vs. Primary Data Confusion
**What goes wrong:** The only general election CSV in the confirmed GitHub directory is `presidential_general_averages_2024-09-12_uncorrected.csv` — this may be a partial snapshot, not the full Jan-Nov series. The primary averages CSV covers the primary season only.
**Why it happens:** FiveThirtyEight's GitHub data publication cadence is irregular and some files are snapshot exports, not complete time series.
**How to avoid:** Verify CSV row count and date range immediately after download. If the general election CSV does not cover Jan-Nov 2024 fully, supplement with the Wayback Machine archive of FiveThirtyEight's forecast page or use their `state-of-the-polls-2024` directory data.
**Warning signs:** `SELECT MIN(date), MAX(date), COUNT(*) FROM poll_forecasts WHERE source='fivethirtyeight'` returns a date range shorter than Jan 1 to Nov 5, 2024.

### Pitfall 4: RCP Scraper Returns Percentage Not Probability
**What goes wrong:** The `realclearpolitics` PyPI package returns raw poll percentage values (e.g., 47.3, 48.1). Storing these directly in `poll_forecasts.probability` violates the [0.0, 1.0] constraint and breaks every downstream calculation.
**Why it happens:** RCP is not a probability forecaster — it averages raw poll percentages. The conversion to probability is a researcher choice, not a data feature.
**How to avoid:** Apply `expit(margin * scaling_factor)` conversion in `ingest/rcp.py` before any INSERT. Store the conversion method and scaling factor in a `metadata` table or code comment. Mark rows with `poll_type='rcp_converted'` to distinguish from native probabilities.
**Warning signs:** `SELECT MAX(probability) FROM poll_forecasts WHERE source='rcp'` returns a value > 1.0.

### Pitfall 5: WAL Mode Not Persisting Across init_db.py Runs
**What goes wrong:** `PRAGMA journal_mode=WAL` is executed but the database file already existed in DELETE journal mode. The PRAGMA command appears to succeed but the WAL transition silently fails if there are active connections.
**Why it happens:** SQLite cannot switch journal modes while other connections are open. On Windows, file locking may leave stale connections.
**How to avoid:** Always delete `data/thesis.db` and recreate from scratch when running `init_db.py` during development. In production, run `PRAGMA journal_mode` after setting it and assert the return value is `'wal'`.
**Warning signs:** `PRAGMA journal_mode` returns `'delete'` instead of `'wal'` after initialization.

### Pitfall 6: GDELT GKG File Size (Already Documented in PITFALLS.md)
**What goes wrong:** Downloading full GKG files for 2024 (2.5TB/year) instead of using the GDELT DOC API for targeted queries.
**How to avoid:** Use `https://api.gdeltproject.org/api/v2/doc/doc?query=election+USA+2024&mode=artlist&format=json` to get article lists for specific keywords and date ranges. Extract `Tone` field for sentiment. Process in daily chunks.

### Pitfall 7: Timezone Corruption (Critical — from PITFALLS.md)
**What goes wrong:** Polymarket API returns Unix ms timestamps; GDELT uses `YYYYMMDDHHMMSS` UTC strings; RCP uses calendar dates. Each conversion path has failure modes.
**How to avoid:** One central utility function `to_utc_iso(value, source_format)` in `ingest/__init__.py` that normalizes all inputs to `YYYY-MM-DDTHH:MM:SS.ffffffZ`. All tests assert timestamp format conformance.

---

## Code Examples

Verified patterns from official sources and confirmed API behavior:

### Polymarket CLOB API — Price History Fetch
```python
# Source: https://docs.polymarket.com/developers/CLOB/timeseries
# and https://github.com/Polymarket/py-clob-client/issues/216 (resolved market limitation)
import httpx
from datetime import datetime, timezone

async def fetch_polymarket_prices(
    token_id: str,
    fidelity: int = 1440,  # daily granularity (minutes)
) -> list[dict]:
    """Laedt historische Preisdaten fuer einen Polymarket-Token via CLOB API.

    Wichtig: Aufgeloeste Maerkte liefern nur Daten bei fidelity >= 720.
    """
    url = "https://clob.polymarket.com/prices-history"
    params = {
        "market": token_id,
        "interval": "max",
        "fidelity": fidelity,
    }
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    # Response format: {"history": [{"t": <unix_ms>, "p": <price_float>}, ...]}
    return [
        {
            "price_timestamp": datetime.fromtimestamp(
                row["t"] / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "fetched_at": fetched_at,
            "price": float(row["p"]),
        }
        for row in data.get("history", [])
    ]
```

### Revised init_db.py Schema (Key Fixes)
```python
# All five gaps from the known issues list addressed:
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=10000;

CREATE TABLE IF NOT EXISTS polymarket_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price_timestamp TEXT NOT NULL,   -- FIXED: was 'timestamp'
    fetched_at TEXT NOT NULL,        -- FIXED: was missing
    market_id TEXT NOT NULL,
    token_id TEXT,
    price REAL NOT NULL,
    volume_24h REAL,
    best_bid REAL,
    best_ask REAL,
    UNIQUE(price_timestamp, market_id, token_id)
);

CREATE TABLE IF NOT EXISTS whale_trades (  -- FIXED: was 'whale_transactions'
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price_timestamp TEXT NOT NULL,
    tx_hash TEXT UNIQUE,
    wallet_address TEXT NOT NULL,    -- always lowercase per CLAUDE.md
    market_id TEXT,
    direction TEXT NOT NULL CHECK(direction IN ('BUY', 'SELL')),
    amount_usd REAL NOT NULL,
    token_id TEXT,
    price_at_trade REAL
);

CREATE TABLE IF NOT EXISTS market_maker_exclusions (  -- FIXED: was missing
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address TEXT UNIQUE NOT NULL,  -- lowercase
    label TEXT,
    source TEXT,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TEXT NOT NULL,   -- ISO 8601 UTC; rename avoids SQLite keyword
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL,    -- FIXED: was missing (DATA-07 success criterion)
    description TEXT,
    impact_score REAL
);

-- poll_forecasts and sentiment_scores are correct in existing schema
-- ... (existing definitions unchanged)
"""
```

### RCP Logit Conversion
```python
# Source: scipy.special documentation https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expit.html
from scipy.special import expit
import numpy as np

def rcp_margin_to_probability(trump_pct: float, harris_pct: float) -> float:
    """Konvertiert RCP-Umfragemargin in eine implizite Gewinnwahrscheinlichkeit.

    Methode: logistische Transformation der prozentualen Differenz.
    Skalierungsfaktor 4.0 ist eine Forschungsentscheidung — muss in der
    Thesis-Methodologie dokumentiert werden.
    """
    if trump_pct <= 0 or harris_pct <= 0:
        raise ValueError("Umfrageprozente muessen positiv sein")
    margin = (trump_pct - harris_pct) / 100.0
    return float(expit(margin * 4.0))
```

### SQLite WAL Verification (for tests)
```python
# Source: SQLite official documentation https://sqlite.org/wal.html
import sqlite3

def assert_wal_mode(db_path: str) -> None:
    """Behauptet, dass WAL-Modus aktiv ist — wird in pytest aufgerufen."""
    conn = sqlite3.connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal", f"Erwartet WAL-Modus, gefunden: {mode}"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FiveThirtyEight live API | Static GitHub CSV export | 2023 (538 relaunch) | Must use CSV files from github.com/fivethirtyeight/data; live API no longer available |
| Polymarket AMM (FPMM) | Polymarket CLOB (order book) | 2022-2023 transition | Old Dune queries targeting FPMM contracts are wrong; use CLOB-specific tables |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 deprecation | `utcnow()` still works but raises DeprecationWarning; must use aware datetime |
| Polygon direct RPC for whale data | Dune Analytics SQL | Ongoing | Direct RPC requires archival node access; Dune indexes Polygon and has Polymarket-specific community queries |

**Deprecated/outdated:**
- `datetime.utcnow()`: deprecated Python 3.12, removed in 3.14. Use `datetime.now(timezone.utc)`.
- FiveThirtyEight API (`projects.fivethirtyeight.com/...`): The 2024 presidential forecast model may not have a public API endpoint; use GitHub CSV files as primary source.
- FPMM-based Dune queries for Polymarket: CLOB replaced FPMM; old dashboards targeting FPMM tables will return no data for 2024.

---

## Open Questions

1. **FiveThirtyEight 2024 general election forecast — complete time series availability**
   - What we know: `presidential_general_averages_2024-09-12_uncorrected.csv` exists in the GitHub repo; this appears to be a snapshot from September 12, not a complete Jan-Nov series
   - What's unclear: Whether there is a full Jan-Nov 2024 daily forecast CSV anywhere in the official repo; the filename date suggests a single export date
   - Recommendation: At ingestion time, check `MIN(date)` and `MAX(date)` in the parsed CSV. If the series starts after January 2024, supplement with `state-of-the-polls-2024` directory data or use Wayback Machine snapshots of FiveThirtyEight's forecast page. Have a fallback strategy ready before starting Wave 1.

2. **Polymarket presidential market token_id — confirmed value for 2024 POTUS market**
   - What we know: The Gamma API at `gamma-api.polymarket.com/markets` allows filtering by slug or question text
   - What's unclear: The exact `token_id` values for YES and NO outcomes of the 2024 presidential market
   - Recommendation: The first step of `ingest/polymarket.py` should be a Gamma API call to resolve market metadata and store it, rather than hardcoding token IDs. Use `condition_id` (on-chain identifier) as the stable primary key, not Gamma's internal `id`.

3. **RCP scraper reliability for historical 2024 data**
   - What we know: The `realclearpolitics` PyPI package exists and scrapes RCP pages; RCP may have changed their page structure after 2024 election
   - What's unclear: Whether the PyPI package still works against current RCP HTML structure; whether historical poll average data for Jan-Nov 2024 is still accessible
   - Recommendation: Manually verify the scraper works against one RCP URL before writing the full ingest script. If the scraper fails, use a static archived copy of the RCP polling data (multiple web archives exist).

4. **Dune Analytics CLOB-specific table names for Polymarket 2024**
   - What we know: Multiple Dune dashboards for Polymarket exist; the CLOB replaced FPMM
   - What's unclear: The exact Dune table names for Polymarket CLOB trades on Polygon in 2024
   - Recommendation: Start with existing community dashboards (e.g., `dune.com/rchen8/polymarket`, `dune.com/filarm/polymarket-activity`) and fork their SQL rather than writing from scratch. Develop and test all queries on Dune web UI before calling the API.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | none yet — Wave 0 creates `pytest.ini` |
| Quick run command | `pytest tests/test_init_db.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-02 | WAL mode active after init | unit | `pytest tests/test_init_db.py::test_wal_mode -x` | Wave 0 |
| DATA-01 | polymarket_prices has price_timestamp + fetched_at columns | unit | `pytest tests/test_init_db.py::test_schema_polymarket_prices -x` | Wave 0 |
| DATA-05 | market_maker_exclusions table exists | unit | `pytest tests/test_init_db.py::test_schema_exclusions -x` | Wave 0 |
| DATA-07 | events_timeline has event_category column | unit | `pytest tests/test_init_db.py::test_schema_events_timeline -x` | Wave 0 |
| DATA-01 | Polymarket ingest writes rows with correct fields | unit (mocked) | `pytest tests/test_ingest_polymarket.py -x` | Wave 0 |
| DATA-03 | 538 CSV parse produces daily rows in poll_forecasts | unit | `pytest tests/test_ingest_538.py -x` | Wave 0 |
| DATA-04 | RCP rows have probability in [0.0, 1.0] | unit | `pytest tests/test_ingest_rcp.py::test_probability_range -x` | Wave 0 |
| DATA-05 | Whale ingest filters market-maker addresses | unit (mocked) | `pytest tests/test_ingest_dune.py::test_mm_exclusion -x` | Wave 0 |
| DATA-06 | GDELT ingest produces sentiment_scores rows | unit (mocked) | `pytest tests/test_ingest_gdelt.py -x` | Wave 0 |
| DATA-07 | events_timeline row count >= 20 | unit | `pytest tests/test_ingest_events.py::test_event_count -x` | Wave 0 |
| DATA-01 | No look-ahead: fetched_at >= price_timestamp always | unit | `pytest tests/test_ingest_polymarket.py::test_no_lookahead -x` | Wave 0 |
| DATA-01 | All timestamps match UTC ISO 8601 format | unit | `pytest tests/test_init_db.py::test_timestamp_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_init_db.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — shared fixtures: in-memory DB, mock httpx responses for Polymarket + Dune + GDELT
- [ ] `tests/test_init_db.py` — schema validation: WAL mode, all table names, all column names
- [ ] `tests/test_ingest_polymarket.py` — mocked CLOB API responses, timestamp separation
- [ ] `tests/test_ingest_538.py` — CSV parsing, date range coverage
- [ ] `tests/test_ingest_rcp.py` — probability range, logit conversion correctness
- [ ] `tests/test_ingest_dune.py` — market-maker exclusion filter
- [ ] `tests/test_ingest_gdelt.py` — sentiment score extraction
- [ ] `tests/test_ingest_events.py` — minimum 20 rows, non-null categories
- [ ] `pytest.ini` — asyncio_mode = auto for pytest-asyncio

---

## Sources

### Primary (HIGH confidence)
- SQLite WAL documentation: https://sqlite.org/wal.html — WAL PRAGMA syntax, persistence behavior, concurrent read semantics
- Polymarket CLOB API: https://docs.polymarket.com/developers/CLOB/timeseries — `/prices-history` endpoint, response format `{history: [{t, p}]}`
- Polymarket py-clob-client GitHub issue #216: https://github.com/Polymarket/py-clob-client/issues/216 — confirmed 12h minimum fidelity for resolved markets
- scipy.special.expit documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.expit.html — logit-to-probability conversion
- DuckDB SQLite extension (internal knowledge, HIGH confidence for ATTACH syntax — documented in DuckDB release notes)

### Secondary (MEDIUM confidence)
- FiveThirtyEight GitHub data repo: https://github.com/fivethirtyeight/data/tree/master/polls/2024-averages — CSV files confirmed to exist; full column structure requires download to verify
- Polymarket Gamma API overview: https://docs.polymarket.com/developers/gamma-markets-api/overview — confirmed market metadata structure, condition_id as stable key
- Dune Analytics Polymarket dashboards: https://dune.com/rchen8/polymarket, https://dune.com/filarm/polymarket-activity — confirmed community SQL queries exist for CLOB trades
- realclearpolitics PyPI: https://pypi.org/project/realclearpolitics/ — confirmed package exists; current reliability against RCP HTML structure unverified
- GDELT data access: https://www.gdeltproject.org/data.html and gdelt PyPI package https://pypi.org/project/gdelt/ — file format and availability confirmed; DOC API query syntax for targeted pulls needs verification at implementation time

### Tertiary (LOW confidence — flagged for validation)
- FiveThirtyEight 2024 general election forecast completeness: filename `presidential_general_averages_2024-09-12_uncorrected.csv` suggests partial export; full Jan-Nov coverage unverified without downloading the file
- Exact Dune table names for Polymarket CLOB on Polygon: community dashboards use these but specific table names (e.g., `polymarket_polygon.clob_trades`) need verification via Dune web UI

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are in requirements.txt or are well-known ecosystem packages
- Architecture: HIGH — follows established ingest-cache-analyze separation; patterns consistent with prior research in .planning/research/
- Schema fixes: HIGH — the five gaps are unambiguous and directly stated in the phase brief
- Polymarket API specifics: MEDIUM — endpoint confirmed active; fidelity limitation for resolved markets confirmed via GitHub issues; exact token_id for presidential market requires runtime resolution
- FiveThirtyEight data: MEDIUM — CSVs confirmed to exist; completeness of general election coverage uncertain
- RCP scraper: LOW — package exists but current reliability unverified
- GDELT DOC API query syntax: MEDIUM — API structure confirmed; optimal filter parameters for election sentiment need testing

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (30 days — Polymarket API and RCP scraper may change; FiveThirtyEight data is static)
