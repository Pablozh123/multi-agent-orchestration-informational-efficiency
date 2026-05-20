---
phase: 01-data-foundation
plan: "02"
subsystem: database
tags: [polymarket, clob-api, sqlite, httpx, async, ingest]

# Dependency graph
requires:
  - phase: 01-00
    provides: test infrastructure, pytest fixtures, conftest.py
  - phase: 01-01
    provides: ingest/__init__.py with to_utc_iso(), get_connection(), DB_PATH

provides:
  - "ingest/polymarket.py: parse_prices() pure function (testable, no I/O)"
  - "ingest/polymarket.py: fetch_polymarket_prices() async CLOB API fetch at fidelity=1440"
  - "ingest/polymarket.py: resolve_token_id() dynamic CLOB API token resolution (no Gamma API)"
  - "ingest/polymarket.py: ingest_polymarket() idempotent INSERT OR IGNORE to polymarket_prices"
  - "polymarket_prices: 307 rows, 2024-01-05 to 2024-11-06, zero lookahead violations"

affects:
  - analysis
  - brier-score
  - market-agent

# Tech tracking
tech-stack:
  added: [httpx async client, json stdlib for debug output]
  patterns:
    - "Pure parse function separated from I/O for testability (parse_prices has no network calls)"
    - "fetched_at passed as parameter to parse_prices — caller records timestamp before API call"
    - "resolve_token_id uses CLOB API /markets endpoint — Gamma API returns archived 2024 markets with no tokens"
    - "INSERT OR IGNORE with UNIQUE(price_timestamp, market_id, token_id) for idempotency"
    - "Timestamps from CLOB API are unix_s (seconds), not unix_ms — must pass source_format='unix_s' to to_utc_iso()"

key-files:
  created:
    - ingest/polymarket.py
  modified: []

key-decisions:
  - "fetched_at is optional parameter with None default in parse_prices — allows tests to call without it while production always passes explicit value"
  - "fidelity=1440 (daily) is the correct granularity for resolved Polymarket markets; finer fidelity returns empty history"
  - "Empty history triggers debug JSON save to data/polymarket_debug.json — no silent failure"
  - "resolve_token_id switched from Gamma API to CLOB API (/markets) — Gamma API returns archived 2024 markets with empty tokens[] array"
  - "CLOB prices-history returns unix_s timestamps, not unix_ms as documented — parse_prices now calls to_utc_iso(t, 'unix_s')"

patterns-established:
  - "Pattern: Lookahead-bias-free ingestion — fetched_at recorded before API call, passed explicitly to parse function"
  - "Pattern: Dynamic market resolution — never hardcode token_id/market_id, always resolve from API"

requirements-completed: [DATA-01]

# Metrics
duration: 10min
completed: 2026-03-16
---

# Phase 01 Plan 02: Polymarket Ingest Summary

**Async Polymarket CLOB price history ingest with dynamic CLOB API token resolution, fidelity=1440 daily granularity, lookahead-bias-free timestamp handling — 307 rows ingested covering 2024-01-05 to 2024-11-06**

## Performance

- **Duration:** ~10 min (including two auto-fix iterations)
- **Completed:** 2026-03-16
- **Tasks:** 2/2 (Task 2 checkpoint:human-verify approved)
- **Files modified:** 1

## Accomplishments

- parse_prices() pure function with no network I/O, fully testable with pytest fixtures
- Dynamic token_id resolution via CLOB API /markets (Gamma API returns archived markets with empty tokens[])
- Idempotent ingest via INSERT OR IGNORE on UNIQUE(price_timestamp, market_id, token_id)
- Empty history handled gracefully: warning logged, raw response saved to data/polymarket_debug.json
- All three unit tests pass: test_polymarket_row_count, test_no_lookahead_bias, test_price_timestamp_format
- **307 rows ingested** covering 2024-01-05 to 2024-11-06
- **Zero lookahead bias violations** (fetched_at >= price_timestamp for all rows)
- **Idempotency confirmed** — second run inserted 0 rows

## Task Commits

Each task was committed atomically:

1. **Task 1: ingest/polymarket.py — parse_prices() pure function** — `cf1a75c` (feat)
2. **Auto-fix: Gamma API slug resolution + CLOB timestamp format** — `4b3f159` (fix)

## Files Created/Modified

- `ingest/polymarket.py` — Full Polymarket ingest: parse_prices(), fetch_polymarket_prices(), resolve_token_id(), ingest_polymarket()

## Decisions Made

- Made `fetched_at` optional in `parse_prices` (None default generates current UTC) — existing tests call without it, production always passes explicit pre-call timestamp
- fidelity=1440 is the only valid granularity for resolved 2024 presidential market (finer returns empty history)
- Empty history saves to data/polymarket_debug.json for diagnosis rather than raising exception
- resolve_token_id switched from Gamma API to CLOB API /markets endpoint (see Deviations)
- CLOB API timestamps are unix_s not unix_ms — to_utc_iso() source_format corrected

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] resolve_token_id() switched from Gamma API to CLOB API**
- **Found during:** Task 2 (human-verify checkpoint — live API run)
- **Issue:** Gamma API returns archived 2024 presidential market records with empty `tokens[]` array, so the YES token_id could not be resolved
- **Fix:** Replaced Gamma API call (`gamma-api.polymarket.com/markets`) with CLOB API call (`clob.polymarket.com/markets`) which returns active market data including token IDs
- **Files modified:** `ingest/polymarket.py` (`resolve_token_id()`)
- **Commit:** `4b3f159`

**2. [Rule 1 - Bug] parse_prices() timestamp conversion: unix_ms -> unix_s**
- **Found during:** Task 2 (human-verify checkpoint — live API run)
- **Issue:** The plan specified `to_utc_iso(row["t"], "unix_ms")` but the CLOB prices-history endpoint returns timestamps as Unix seconds (unix_s), not milliseconds. This caused wildly incorrect price_timestamp values (year ~56000+).
- **Fix:** Changed `to_utc_iso(row["t"], "unix_ms")` to `to_utc_iso(row["t"], "unix_s")` in parse_prices()
- **Files modified:** `ingest/polymarket.py` (`parse_prices()`)
- **Commit:** `4b3f159`

## Issues Encountered

None beyond the two auto-fixed bugs above.

## User Setup Required

None — Polymarket CLOB API is public (no auth required for read access).

## Next Phase Readiness

- DATA-01 requirement fulfilled: 307 rows in polymarket_prices, Jan-Nov 2024 range, zero lookahead violations
- Wave 2 ingest scripts (fivethirtyeight, rcp, dune, gdelt) can reference this module's patterns
- market_agent (Phase 2) can now query polymarket_prices for Brier Score analysis

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*

## Self-Check: PASSED
- `ingest/polymarket.py`: FOUND
- Commit `cf1a75c`: FOUND
- Commit `4b3f159`: FOUND
- polymarket_prices: 307 rows, 2024-01-05 to 2024-11-06 (user-verified)
- Idempotency: confirmed (0 rows on second run)
