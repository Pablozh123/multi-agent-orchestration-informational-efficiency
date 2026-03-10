---
phase: 01-data-foundation
plan: "01"
subsystem: database
tags: [sqlite, wal, schema, init_db, ingest, python, utc, iso8601]

# Dependency graph
requires:
  - phase: 01-00
    provides: test infrastructure (conftest.py fixtures, test_schema.py with 8 schema tests)
provides:
  - Idempotent init_db.py producing WAL-mode SQLite with six correct tables and all indexes
  - ingest/ package exporting to_utc_iso() and get_connection() for all ingest scripts
affects:
  - 01-02 (polymarket ingest imports ingest.to_utc_iso and ingest.get_connection)
  - 01-03 (dune whale ingest same imports)
  - 01-04 (gdelt sentiment ingest same imports)
  - 01-05 (fivethirtyeight/rcp poll ingest same imports)
  - All Wave 2 plans depend on correct table/column names established here

# Tech tracking
tech-stack:
  added: []
  patterns:
    - PRAGMA journal_mode=WAL first in SCHEMA string before any CREATE TABLE
    - force_recreate=True deletes and recreates DB to prevent schema drift
    - to_utc_iso() normalises unix_ms/unix_s/gdelt to 'YYYY-MM-DDTHH:MM:SS.ffffffZ'
    - datetime.fromtimestamp(tz=timezone.utc) — no deprecated datetime.utcnow()

key-files:
  created:
    - ingest/__init__.py
  modified:
    - init_db.py

key-decisions:
  - "init_db.py: PRAGMA journal_mode=WAL placed as first statement in SCHEMA string (before CREATE TABLE) to guarantee WAL activation"
  - "init_db.py: force_recreate=True default deletes existing file — prevents stale schema causing column-name bugs in Wave 2"
  - "init_db.py: WAL assertion after executescript() catches silent PRAGMA failures at init time"
  - "ingest/__init__.py: to_utc_iso raises ValueError for unknown source_format — explicit failure preferred over silent wrong data"
  - "events_timeline.event_category is TEXT (nullable) matching conftest fixture — test checks presence not NOT NULL"

patterns-established:
  - "Schema pattern: avoid SQLite reserved word 'timestamp' — use price_timestamp, event_timestamp"
  - "Ingest pattern: all scripts import to_utc_iso and get_connection from ingest/__init__.py"
  - "WAL pattern: get_connection() always sets WAL + busy_timeout + synchronous=NORMAL"

requirements-completed: [DATA-01, DATA-02, DATA-05]

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 1 Plan 01: Schema Fix and Ingest Package Summary

**SQLite schema corrected (9 gaps fixed), WAL mode enforced, and ingest/ package created with to_utc_iso() and get_connection() for all five ingest scripts to import**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-10T22:34:29Z
- **Completed:** 2026-03-10T22:36:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Rewrote init_db.py fixing all 9 schema gaps (price_timestamp, fetched_at, volume_24h, best_bid, best_ask, whale_trades table name, market_maker_exclusions table, event_timestamp, event_category columns)
- WAL mode now set as first PRAGMA in SCHEMA string with assertion verifying activation; init() idempotently deletes and recreates the database
- Created ingest/__init__.py exporting to_utc_iso() (three source formats), get_connection() (WAL + busy_timeout + synchronous=NORMAL), and DB_PATH constant
- All 8 schema tests pass; full pytest suite exits 0 (13 passed, 8 skipped, 1 xfailed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite init_db.py with correct schema and WAL mode** - `8cd3567` (feat)
2. **Task 2: Create ingest/ package with shared utilities** - `3a134b3` (feat)

**Plan metadata:** committed after SUMMARY creation (docs)

## Files Created/Modified

- `init_db.py` - Full rewrite: 9 schema gaps fixed, WAL PRAGMA first, WAL assertion, force_recreate, get_connection(), pathlib.Path DB_PATH
- `ingest/__init__.py` - New package: to_utc_iso() (unix_ms/unix_s/gdelt), get_connection(), DB_PATH constant

## Decisions Made

- PRAGMA journal_mode=WAL is first statement in SCHEMA string before any CREATE TABLE — guarantees WAL is set before tables exist
- force_recreate=True default: deletes existing file to prevent schema drift; all Wave 2 ingest scripts assume correct column names
- WAL mode assertion after executescript() catches silent PRAGMA failures at database init time
- to_utc_iso() raises ValueError for unknown source_format — explicit failure preferred over silent wrong data
- events_timeline.event_category is TEXT (nullable) to match conftest.py fixture which is the test source of truth

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- data/thesis.db exists with correct WAL-mode schema and all six tables
- ingest/__init__.py ready for import by all five Wave 2 ingest scripts (01-02 through 01-06)
- Wave 2 plans (01-02 polymarket, 01-03 dune, 01-04 gdelt, 01-05 fivethirtyeight/rcp) can begin immediately

---
*Phase: 01-data-foundation*
*Completed: 2026-03-10*
