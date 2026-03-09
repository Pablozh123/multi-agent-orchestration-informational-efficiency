# Technology Stack

**Project:** Informationseffizienz dezentraler Prädiktionsmärkte
**Researched:** 2026-03-09
**Confidence:** MEDIUM (WebSearch/WebFetch unavailable; based on training data up to August 2025 + project constraints from PROJECT.md)

---

## Non-Negotiable Constraints

These are fixed by PROJECT.md and CLAUDE.md — not recommendations, not up for debate:

| Constraint | Value | Source |
|------------|-------|--------|
| Python version | 3.12 | PROJECT.md |
| MCP framework | FastMCP >=3.0 | PROJECT.md |
| LLM client | Anthropic SDK | PROJECT.md |
| Primary DB | SQLite (`data/thesis.db`) | PROJECT.md |
| Analytics DB | DuckDB | PROJECT.md |
| Visualization | matplotlib + seaborn | CLAUDE.md |

---

## Recommended Stack

### Core Agent Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastMCP | >=3.0 | MCP server implementation for all four agents | FastMCP 2.x/3.x drastically simplifies MCP server boilerplate vs raw `mcp` SDK. Decorator-based tool registration (`@mcp.tool`), built-in transport support (stdio, HTTP/SSE). Non-negotiable per project constraints. |
| anthropic | >=0.44.0 | Claude API calls in Orchestrator | Official SDK with async support (`AsyncAnthropic`). Streaming, tool use, and system prompts all required for multi-agent coordination. |
| httpx | >=0.27.0 | Async HTTP client for all external APIs | Preferred over `aiohttp` for cleaner API, better timeout/retry ergonomics. Polymarket CLOB API, GDELT, NewsAPI all require async HTTP. Used internally by Anthropic SDK as well. |

**Confidence:** HIGH (FastMCP version confirmed by project constraints; httpx is established standard)

### Database Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite (stdlib) | 3.45+ (bundled with Python 3.12) | Primary cache for all API responses | No server required. Portable — thesis can be reproduced on any machine. Built-in Python. All external data must be cached here before analysis (reproducibility + rate limit protection). |
| aiosqlite | >=0.20.0 | Async SQLite access from async MCP handlers | FastMCP servers run async; blocking `sqlite3` calls would stall the event loop. `aiosqlite` wraps stdlib sqlite3 with `async/await`. Minimal overhead. |
| DuckDB | >=1.1.0 | Analytical queries over cached time-series | Columnar in-process engine. Can query SQLite files or Parquet directly. Window functions, time-series aggregations, and Brier Score computations over 300k+ rows are 10-50x faster than pandas groupby on the same hardware. No server, no setup. |

**Confidence:** HIGH (DuckDB 1.x is current stable line; aiosqlite is the established async wrapper)

**Why NOT PostgreSQL:** No server to manage. Thesis data fits comfortably in SQLite. DuckDB handles all analytical performance needs. Portability for reproducibility matters more than write concurrency.

**Why NOT SQLAlchemy ORM:** Direct SQL gives full control over INSERT OR IGNORE / UPSERT patterns critical for idempotent caching. ORM abstraction adds complexity with no benefit for this workload.

### Data Ingestion

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pandas | >=2.2.0 | FiveThirtyEight/RCP CSV parsing, data reshaping | Ingest CSV forecasts, normalize column dtypes, merge on timestamps. pandas 2.x has Copy-on-Write semantics that reduce memory footprint. |
| numpy | >=1.26.0 | Numerical arrays, Brier Score computation | Required by pandas, scipy, sklearn. Direct use for vectorized probability scoring. |
| requests / httpx | (httpx already listed) | Polymarket CLOB REST API | Polymarket exposes a public REST API (no auth required for historical OHLC and orderbook data). httpx handles both sync and async. |

**Note on Polymarket API Access:** Polymarket's CLOB API (`clob.polymarket.com`) provides historical price data. No official Python SDK exists in the ecosystem as of mid-2025 — raw httpx calls are the correct approach. Gamma API (`gamma.polymarket.com`) provides market metadata. Both are unauthenticated for read operations.

**Confidence:** MEDIUM (Polymarket API structure from training data; verify endpoints before implementation — APIs may have changed)

### Blockchain / Whale Tracking

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Dune Analytics API (via httpx) | REST API v1 | Whale wallet queries on Polygon | Polymarket runs on Polygon PoS. Direct RPC queries require parsing complex contract ABI interactions. Dune has community-maintained Polymarket dashboards with pre-built whale/volume queries. Access via Dune API (API key required). Far lower implementation cost than direct blockchain parsing. |
| `web3.py` (optional fallback) | >=7.0.0 | Direct Polygon RPC if Dune is insufficient | web3.py 7.x dropped legacy APIs. Use ONLY if Dune query latency or API limits become blockers. Polygon public RPC endpoints (Alchemy/Infura free tier) provide transaction history. |

**Confidence:** MEDIUM (Dune Analytics strategy confirmed as lower-complexity path in PROJECT.md Key Decisions; web3.py 7.x version from training data — verify on PyPI)

**Why NOT direct Polygon node:** Would require archival node access (expensive) or parsing full transaction logs. Dune's indexed data with SQL interface is sufficient for whale analysis.

### Sentiment Analysis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PRAW | >=7.8.0 | Reddit data collection | Official Reddit API wrapper. Rate-limit-aware. Auth required (OAuth2 credentials). Subreddits: r/politics, r/PoliticalDiscussion, r/Destiny, r/neoliberal. Push to SQLite cache immediately. |
| GDELT (via httpx) | REST/CSV API | News event sentiment | GDELT 2.0 GKG (Global Knowledge Graph) provides tone scores for news articles. No API key. Files available at 15-minute intervals. Query via GDELT DOC API or raw GKG CSV downloads. |
| TextBlob OR VADER (nltk) | textblob>=0.18.0 OR nltk>=3.9.0 | Sentiment scoring on cached text | For Reddit posts and GDELT article headlines. VADER is calibrated for social media (short, informal text) — better than TextBlob for Reddit. TextBlob better for longer news text. Use VADER for Reddit, GDELT native tone scores for news. |

**Confidence:** MEDIUM (PRAW 7.8 confirmed in existing requirements.txt; VADER/NLTK choice is my recommendation over training data; GDELT API behavior from training data — verify file formats)

**Why NOT Hugging Face transformers for sentiment:** Overkill for a BA thesis. VADER + GDELT native scores are interpretable, fast, reproducible, and require no GPU. Transformer models add infrastructure complexity without meaningful accuracy gain for this use case (political news sentiment at daily granularity).

### Statistical Analysis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| scipy | >=1.14.0 | Statistical tests (Wilcoxon, Mann-Whitney, t-test) | Brier Score significance testing across forecasters requires non-parametric tests. `scipy.stats` covers all needed hypothesis tests. |
| statsmodels | >=0.14.0 | Time-series analysis, Granger causality | Granger causality test for H2 (does Polymarket price lead polls?) and H3 (do whale trades lead price?). Also HAC-robust standard errors. |
| scikit-learn | >=1.5.0 | Calibration curves, cross-validation | `sklearn.calibration.calibration_curve` for reliability diagrams. Brier Score via `sklearn.metrics.brier_score_loss`. |

**Confidence:** HIGH (stable, established scientific Python stack; versions in existing requirements.txt are current)

### Visualization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| matplotlib | >=3.9.0 | Primary plotting engine | Academic paper figures require fine-grained control over axes, labels, fonts, export DPI. matplotlib gives this. seaborn works on top of it. |
| seaborn | >=0.13.0 | Statistical visualization | Calibration plots, distribution comparisons, heatmaps. seaborn 0.13 has improved object-based API. |

**Confidence:** HIGH (standard academic Python visualization stack; no better alternative for LaTeX-ready figure export)

**Why NOT Plotly/Dash:** Interactive dashboards are explicitly out of scope (PROJECT.md). Static publication-quality figures are the output. matplotlib/seaborn produce PDF/SVG output directly importable into LaTeX.

**Why NOT altair:** Vega-Lite based, harder to control exact font sizes and layout for academic formatting standards.

### Developer Tooling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pytest | >=8.3.0 | Test runner | Project convention (CLAUDE.md). Parametrized fixtures for API mock testing. |
| pytest-asyncio | >=0.24.0 | Async test support | All MCP server handlers are async; pytest-asyncio enables `async def test_*` functions. |
| python-dotenv | >=1.0.0 | .env file loading | API keys for Anthropic, Reddit, Dune, NewsAPI — never hardcoded, loaded at startup. |
| tqdm | >=4.66.0 | Progress bars in data ingestion scripts | Multi-hour ingestion runs (GDELT historical data) need progress visibility. |

**Confidence:** HIGH (all in existing requirements.txt, standard choices)

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| MCP Framework | FastMCP >=3.0 | raw `mcp` SDK | 3-5x more boilerplate, no added benefit for this project |
| HTTP Client | httpx | aiohttp | httpx has cleaner API, native sync+async, used by Anthropic SDK internally |
| Analytics DB | DuckDB | pandas-only | pandas groupby on 100k+ row time-series is 10-50x slower; DuckDB window functions make event-study queries trivial |
| Blockchain Access | Dune Analytics API | web3.py direct | Direct parsing requires ABI decoding, archival node, 100x more code; Dune provides indexed SQL access |
| Sentiment | VADER + GDELT native | HuggingFace transformers | GPU dependency, reproducibility concerns, no accuracy advantage at daily granularity for this domain |
| Visualization | matplotlib/seaborn | Plotly/Dash | Out-of-scope (interactive dashboards excluded by PROJECT.md); LaTeX figure export requires static formats |
| ORM | Direct SQL | SQLAlchemy | Upsert/caching patterns require direct SQL; ORM adds complexity with no gain |
| Async tasks | asyncio (built-in) | Celery/RQ | No distributed task queue needed; single-machine batch processing, asyncio sufficient |

---

## Installation

```bash
# Activate venv first
source .venv/bin/activate

# Core (already in requirements.txt)
pip install -r requirements.txt

# Verify FastMCP version
python -c "import fastmcp; print(fastmcp.__version__)"

# Verify DuckDB
python -c "import duckdb; print(duckdb.__version__)"
```

For `web3.py` (only if Dune Analytics proves insufficient):
```bash
pip install "web3>=7.0.0"
```

For NLTK/VADER (add to requirements.txt):
```bash
pip install "nltk>=3.9.0"
python -c "import nltk; nltk.download('vader_lexicon')"
```

---

## Version Pinning Strategy

For a BA thesis, pin exact versions in requirements.txt for reproducibility:

```
fastmcp==3.x.x          # pin after initial install
anthropic==0.44.x
duckdb==1.1.x
pandas==2.2.x
```

Use `pip freeze > requirements-lock.txt` after confirming the environment works. The main `requirements.txt` keeps `>=` bounds; the lock file ensures exact reproduction.

---

## API Keys Required

| Service | Env Variable | Free Tier Sufficient? |
|---------|-------------|----------------------|
| Anthropic Claude | `ANTHROPIC_API_KEY` | Yes (Claude Haiku for orchestration) |
| Reddit (PRAW) | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Yes |
| Dune Analytics | `DUNE_API_KEY` | Yes (limited executions/month) |
| NewsAPI | `NEWSAPI_KEY` | Yes (developer tier, 100 req/day) |
| Polymarket CLOB | none | Public, no auth needed |
| GDELT | none | Public, no auth needed |

---

## Gaps Needing Verification Before Implementation

1. **FastMCP 3.x API surface** — The project specifies `>=3.0` but FastMCP was at 2.x as of training data. Verify the actual current version and whether the API (especially multi-server coordination from Orchestrator) has changed. Run `pip index versions fastmcp` to check.

2. **Polymarket CLOB API endpoints** — Endpoint structure (`/markets`, `/prices-history`, `/trades`) may have changed. Verify against official Polymarket documentation before writing ingestion code.

3. **Dune Analytics API v1 rate limits** — Free tier may have 100 executions/month cap. If historical data requires more queries than the free tier allows, either cache aggressively (already mandated) or pre-compute all needed queries during a single data collection session.

4. **PRAW Reddit API post-2023 changes** — Reddit severely restricted API access in June 2023. Historical data access may require Pushshift or academic research API instead of standard PRAW. Verify what subreddit data is actually accessible before building the sentiment pipeline.

5. **GDELT GKG file format** — GDELT 2.0 GKG files are large (several GB for full 2024 coverage). A targeted query strategy using the GDELT DOC API is preferable to full file downloads. Verify the DOC API search syntax for election-related content filtering.

---

## Sources

- Project constraints: `/c/Users/chole/ba-thesis/.planning/PROJECT.md` and `CLAUDE.md`
- Existing dependency list: `/c/Users/chole/ba-thesis/requirements.txt`
- Training data (Python ecosystem, up to August 2025) — MEDIUM confidence
- WebSearch and WebFetch unavailable during this research session — external verification not performed
