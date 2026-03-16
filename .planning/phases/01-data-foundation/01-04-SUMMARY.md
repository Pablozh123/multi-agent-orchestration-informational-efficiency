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
  - "DUNE_QUERY_ID = 6810777 — developed and tested on Dune web UI before API use"
  - "data/market_maker_exclusions.json seeds 5 known MM addresses; DB table populated on each ingest_dune() call via INSERT OR IGNORE"
  - "Column name aliasing in _map_row() handles Dune query result variations (taker/wallet, size_usd/amount_usd, side/direction)"
  - "direction normalization maps buy/sell variants to uppercase BUY/SELL to satisfy whale_trades CHECK constraint"

patterns-established:
  - "Pure filter functions: isolation of business logic from I/O for testability"
  - "JSON seed files: static reference data committed to repo, loaded into DB on ingest run"
  - "INSERT OR IGNORE: idempotent writes keyed on UNIQUE constraint (tx_hash)"

requirements-completed: [DATA-05]

# Metrics
duration: 2min (code) + human checkpoint (Dune setup)
completed: 2026-03-16
---

# Phase 1 Plan 04: Dune Whale Ingest Summary

**Dune Analytics whale-trade ingest with pure filter_market_makers() function, 5-entry MM exclusion JSON seed, and column-aliasing _map_row() for Dune query result variations — 25,113 whale trades verified (amount_usd >= $10k, DUNE_QUERY_ID=6810777)**

## Performance

- **Duration:** 2 min (code) + human checkpoint (Dune query setup and live verification)
- **Started:** 2026-03-10T22:38:35Z
- **Completed:** 2026-03-16
- **Tasks:** 2 of 2 (including human-verify checkpoint — approved)
- **Files modified:** 2

## Accomplishments
- Implemented `filter_market_makers()` as a pure function: filters MM wallets, normalizes wallet_address to lowercase; both whale tests pass
- Implemented `ingest_dune()` with full Dune REST API call, column aliasing, whale threshold ($10k), direction normalization, and INSERT OR IGNORE deduplication
- Created `data/market_maker_exclusions.json` with 5 known Polymarket MM addresses (all lowercase)
- Live ingest executed with DUNE_QUERY_ID=6810777: **25,113 rows** inserted into `whale_trades`
- All rows verified: amount_usd >= 10,000 (min check passed), cross-join with market_maker_exclusions returns 0 (no MM wallets in results)
- Idempotency confirmed: running script a second time inserted 0 new rows (tx_hash UNIQUE constraint)

## Task Commits

Each task was committed atomically:

1. **Task 1: ingest/dune.py and data/market_maker_exclusions.json** - `3aee579` (feat)

## Files Created/Modified
- `ingest/dune.py` - Dune Analytics ingest: filter_market_makers, ingest_dune, load_exclusions, _populate_market_maker_exclusions
- `data/market_maker_exclusions.json` - Static seed list of 5 known Polymarket market-maker wallet addresses

## Decisions Made
- `filter_market_makers()` kept pure (no DB access) to allow clean unit testing with mock fixture
- `DUNE_QUERY_ID = 6810777` — developed and tested on Dune web UI before using API credits
- Column aliasing in `_map_row()` handles multiple Dune column name conventions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Live Ingest Results

| Check | Result | Status |
|-------|--------|--------|
| whale_trades row count | 25,113 | Pass |
| MIN(amount_usd) | >= 10,000.0 | Pass |
| MM cross-join count | 0 | Pass |
| Idempotency (2nd run) | 0 new rows | Pass |
| DUNE_QUERY_ID used | 6810777 | — |

## Self-Check: PASSED

- `ingest/dune.py` — exists (committed 3aee579)
- `data/market_maker_exclusions.json` — exists (committed 3aee579)
- whale_trades: 25,113 rows verified by human
- All integrity checks passed

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*
