---
phase: 01-data-foundation
plan: "04"
subsystem: database
tags: [dune-analytics, whale-trades, market-maker-exclusion, sqlite, httpx, python-dotenv]

# Dependency graph
requires:
  - phase: 01-00
    provides: pytest infrastructure and conftest.py with mock_dune_response fixture
  - phase: 01-01
    provides: ingest/__init__.py with get_connection, DB_PATH, to_utc_iso; whale_trades and market_maker_exclusions schema

provides:
  - ingest/dune.py: Dune Analytics API ingest with filter_market_makers (pure, testable) and ingest_dune (API + write)
  - data/market_maker_exclusions.json: Static seed list of 5 known Polymarket market-maker wallet addresses
  - filter_market_makers(): pure function — returns rows excluding known MM wallets, normalizes to lowercase
  - load_exclusions(): reads MM wallet list from DB for runtime filtering
  - _populate_market_maker_exclusions(): populates DB table from JSON seed file on each ingest run

affects:
  - Phase 4 H3 analysis (whale alpha): depends on whale_trades populated without MM noise
  - whale_agent MCP server: will call ingest_dune to refresh whale trade data

# Tech tracking
tech-stack:
  added: [httpx (already in requirements), python-dotenv (already in requirements)]
  patterns:
    - Pure filter function pattern for testable exclusion logic (no DB access in filter_market_makers)
    - INSERT OR IGNORE with UNIQUE constraint for idempotent ingest (tx_hash deduplication)
    - Column name aliasing to handle Dune query result variations
    - JSON seed file for static reference data (market-maker addresses)

key-files:
  created:
    - ingest/dune.py
    - data/market_maker_exclusions.json
  modified: []

key-decisions:
  - "filter_market_makers() is pure (no DB access) — enables clean unit testing with mock_dune_response fixture without DB setup"
  - "DUNE_QUERY_ID = 0 placeholder — user must develop query on Dune web UI and update constant before first live ingest"
  - "data/market_maker_exclusions.json seeds 5 known MM addresses; DB table populated on each ingest_dune() call via INSERT OR IGNORE"
  - "Column name aliasing in _map_row() handles Dune query result variations (taker/wallet, size_usd/amount_usd, side/direction)"
  - "direction normalization maps buy/sell variants to uppercase BUY/SELL to satisfy whale_trades CHECK constraint"

patterns-established:
  - "Pure filter functions: isolation of business logic from I/O for testability"
  - "JSON seed files: static reference data committed to repo, loaded into DB on ingest run"
  - "INSERT OR IGNORE: idempotent writes keyed on UNIQUE constraint (tx_hash)"

requirements-completed: [DATA-05]

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 1 Plan 04: Dune Whale Ingest Summary

**Dune Analytics whale-trade ingest with pure filter_market_makers() function, 5-entry MM exclusion JSON seed, and column-aliasing _map_row() for Dune query result variations**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-10T22:38:35Z
- **Completed:** 2026-03-10T22:40:22Z
- **Tasks:** 1 of 2 (Task 2 is a human-verify checkpoint — awaiting user setup)
- **Files modified:** 2

## Accomplishments
- Implemented `filter_market_makers()` as a pure function: filters MM wallets, normalizes wallet_address to lowercase; both whale tests pass
- Implemented `ingest_dune()` with full Dune REST API call, column aliasing, whale threshold ($10k), direction normalization, and INSERT OR IGNORE deduplication
- Created `data/market_maker_exclusions.json` with 5 known Polymarket MM addresses (all lowercase)
- Module import works; unit tests pass without any API key required

## Task Commits

Each task was committed atomically:

1. **Task 1: ingest/dune.py and data/market_maker_exclusions.json** - `3aee579` (feat)

**Plan metadata:** _(pending — blocking checkpoint active)_

_Note: Task 2 is a blocking human-verify checkpoint requiring Dune API key, web UI query development, and live data verification._

## Files Created/Modified
- `ingest/dune.py` - Dune Analytics ingest: filter_market_makers, ingest_dune, load_exclusions, _populate_market_maker_exclusions
- `data/market_maker_exclusions.json` - Static seed list of 5 known Polymarket market-maker wallet addresses

## Decisions Made
- `filter_market_makers()` kept pure (no DB access) to allow clean unit testing with mock fixture
- `DUNE_QUERY_ID = 0` placeholder constant with comment directing user to Dune web UI
- Column aliasing in `_map_row()` handles multiple Dune column name conventions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

Before running `ingest_dune()` for live data, the following manual steps are required:

1. Get Dune API key: https://dune.com/settings/api -> add `DUNE_API_KEY=your_key` to `.env`
2. Develop SQL query on Dune web UI (https://dune.com/queries/new) for Polymarket CLOB trades >= $10k in 2024
   - Reference dashboard: https://dune.com/rchen8/polymarket
   - Example: `SELECT block_time, tx_hash, taker, condition_id, 'BUY' as direction, usd_amount FROM polymarket_polygon.clob_trades WHERE block_time BETWEEN TIMESTAMP '2024-01-01' AND TIMESTAMP '2024-11-05' AND usd_amount >= 10000`
3. Note the query ID from the URL after saving
4. Update `DUNE_QUERY_ID` constant in `ingest/dune.py` (currently `0`)
5. Run: `.venv/Scripts/python.exe ingest/dune.py`
6. Verify: `SELECT COUNT(*), MIN(amount_usd) FROM whale_trades` should return count > 0, min >= 10000

## Checkpoint Status

**Stopped at:** Task 2 — `checkpoint:human-verify` (blocking)

The unit tests (pure logic) all pass. The blocking checkpoint requires:
- DUNE_API_KEY in .env
- Dune SQL query developed and tested on web UI
- DUNE_QUERY_ID updated in ingest/dune.py
- Live ingest run with data integrity verification

## Next Phase Readiness
- `filter_market_makers()` and `ingest_dune()` are production-ready once DUNE_QUERY_ID is set
- Unit tests provide ongoing regression coverage for the exclusion filter logic
- After checkpoint approval, `whale_trades` table will be populated for Phase 4 H3 analysis

---
*Phase: 01-data-foundation*
*Completed: 2026-03-10*
