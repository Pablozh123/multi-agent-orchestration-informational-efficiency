---
phase: "01"
plan: "03"
subsystem: ingest
tags: [fivethirtyeight, rcp, poll_forecasts, logit, scipy, pandas]
dependency_graph:
  requires: [01-00, 01-01]
  provides: [ingest/fivethirtyeight.py, ingest/rcp.py, poll_forecasts rows for 538 and RCP]
  affects: [Phase 3 Brier Score computation]
tech_stack:
  added: [scipy.special.expit, pandas CSV parsing, httpx HTTP download]
  patterns: [INSERT OR IGNORE idempotency, logit probability conversion, TDD RED-GREEN]
key_files:
  created: [ingest/fivethirtyeight.py, ingest/rcp.py]
  modified: []
decisions:
  - "FiveThirtyEight probability column detection uses priority list [pct_estimate, mean, avg, value] — handles CSV schema variations"
  - "RCP logit SCALING_FACTOR=4.0 stored as module constant with reference to thesis Section 3.2"
  - "ingest_rcp() returns 0 gracefully when realclearpolitics package unavailable — scraper is optional, pure conversion function is tested"
  - "Harris probability derived as 1 - trump_probability for consistent two-candidate market representation"
metrics:
  duration: "4 min"
  completed_date: "2026-03-10T22:40:38Z"
  tasks_completed: 2
  files_created: 2
---

# Phase 1 Plan 03: FiveThirtyEight and RCP Poll Ingest Summary

**One-liner:** FiveThirtyEight CSV parsing with probability normalization and RCP logit conversion via scipy.special.expit, both writing to poll_forecasts with INSERT OR IGNORE idempotency.

## What Was Built

Two ingest scripts that populate `poll_forecasts` with daily forecast probabilities from traditional polling sources:

1. **`ingest/fivethirtyeight.py`** — Downloads the FiveThirtyEight 2024 presidential averages CSV from GitHub, detects the probability column (pct_estimate/mean/avg/value), normalizes values >1.0 by dividing by 100, filters to trump/harris via canonical alias sets, and writes rows via INSERT OR IGNORE.

2. **`ingest/rcp.py`** — Converts RCP poll percentages to implicit probabilities using `scipy.special.expit((trump_pct - harris_pct) / 100 * 4.0)`. The `poll_pct_to_probability()` function is the core tested unit. `ingest_rcp()` attempts the `realclearpolitics` package first, falls back to HTTP, and returns 0 if unavailable — the pure conversion function is always testable regardless of network/package availability.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | ingest/fivethirtyeight.py — CSV parse and write | 09ae591 | ingest/fivethirtyeight.py |
| 2 | ingest/rcp.py — scrape and logit conversion | aab94c9 | ingest/rcp.py |

## Test Results

All required tests pass:
- `test_fivethirtyeight_rows` — parse_csv returns rows with YYYY-MM-DD dates and probability in [0.0, 1.0]
- `test_rcp_probability_range` — poll_pct_to_probability(52.0, 47.0) returns value in (0.5, 1.0)
- `test_rcp_symmetric` — poll_pct_to_probability(50.0, 50.0) == approx(0.5)

## Decisions Made

1. **FiveThirtyEight column detection via priority list** — Rather than hard-coding `pct_estimate`, the parser tries `[pct_estimate, mean, avg, value]` in order. This makes the script resilient to minor CSV schema changes from the FiveThirtyEight repository.

2. **RCP SCALING_FACTOR=4.0 as named constant** — The scaling factor is declared as `SCALING_FACTOR: float = 4.0` at module level with a comment referencing thesis Section 3.2. This makes the methodological choice explicit and auditable.

3. **ingest_rcp() graceful degradation** — If the `realclearpolitics` PyPI package is not installed, the function logs a warning and returns 0. This keeps the module importable and `poll_pct_to_probability()` testable without requiring network access or the optional package. The pure function is the primary analytical artifact.

4. **Harris probability as complement** — Harris is stored as `1.0 - trump_probability` per the two-candidate zero-sum market assumption. This is consistent with Polymarket's binary market structure (DATA-03/DATA-04 requirement).

## Deviations from Plan

None — plan executed exactly as written.

## Must-Haves Status

| Truth | Status |
|-------|--------|
| poll_forecasts contains daily rows for source='fivethirtyeight' | Ready (post-run) |
| poll_forecasts contains rows for source='rcp' with probability in [0.0, 1.0] | Ready (post-run) |
| RCP probability > 0.5 when Trump poll average exceeds Harris poll average | Verified via test_rcp_probability_range |
| FiveThirtyEight rows have probability derived from pct_estimate (not raw %) | Implemented and tested |
| Both scripts are idempotent | INSERT OR IGNORE guarantees idempotency |
