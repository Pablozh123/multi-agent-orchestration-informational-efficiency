---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `.venv/Scripts/python.exe -m pytest tests/test_schema.py -q` |
| **Full suite command** | `.venv/Scripts/python.exe -m pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/Scripts/python.exe -m pytest tests/test_schema.py -q`
- **After every plan wave:** Run `.venv/Scripts/python.exe -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01-01 | 1 | DATA-02 | unit | `.venv/Scripts/python.exe -m pytest tests/test_schema.py::test_wal_mode -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01-01 | 1 | DATA-01 | unit | `.venv/Scripts/python.exe -m pytest tests/test_schema.py::test_price_timestamp_columns -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01-01 | 1 | DATA-05 | unit | `.venv/Scripts/python.exe -m pytest tests/test_schema.py::test_whale_trades_table -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 01-02 | 2 | DATA-01 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_polymarket_row_count -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 01-03 | 2 | DATA-03 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_fivethirtyeight_rows -q` | ❌ W0 | ⬜ pending |
| 1-03-02 | 01-03 | 2 | DATA-04 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_rcp_probability_range -q` | ❌ W0 | ⬜ pending |
| 1-04-01 | 01-04 | 2 | DATA-05 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_whale_trades_exclusion -q` | ❌ W0 | ⬜ pending |
| 1-05-01 | 01-05 | 2 | DATA-06 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_gdelt_sentiment_rows -q` | ❌ W0 | ⬜ pending |
| 1-06-01 | 01-06 | 2 | DATA-07 | integration | `.venv/Scripts/python.exe -m pytest tests/test_ingest.py::test_events_catalog_count -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_schema.py` — stubs for DATA-01, DATA-02, DATA-03, DATA-04, DATA-05 schema checks
- [ ] `tests/test_ingest.py` — stubs for DATA-01 through DATA-07 row count / integrity checks
- [ ] `tests/conftest.py` — shared fixture: in-memory SQLite DB initialized with schema

*Wave 0 must create these before any ingest scripts run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Three simultaneous read connections don't produce a lock error | DATA-02 | Requires spawning 3 concurrent processes | Run `python -c "import sqlite3, threading; ..."` test script from RESEARCH.md |
| Polymarket prices have no look-ahead bias (price_timestamp < fetched_at always) | DATA-01 | Requires data to exist first | `SELECT COUNT(*) FROM polymarket_prices WHERE price_timestamp >= fetched_at` must return 0 |
| RCP probability values are in [0.0, 1.0] after logit conversion | DATA-04 | Boundary check on real data | `SELECT MIN(probability), MAX(probability) FROM poll_forecasts WHERE source='rcp'` |
| No whale wallet in market_maker_exclusions list | DATA-05 | Cross-table join check | `SELECT COUNT(*) FROM whale_trades wt JOIN market_maker_exclusions mme ON wt.wallet_address = mme.wallet_address` must return 0 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
