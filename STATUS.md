# STATUS.md

<!-- PROJECT_STATUS:START -->
## Automation Snapshot

Generated: 2026-07-13 15:06

Current goal: `goal-h3-informed-trading-signature-001` - Build tested H3 informed-trading signature diagnostics

Current roadmap phase: Phase 13: H3 Informed-Trading Signature Diagnostics

Test status: FAIL

Pytest summary: `1 failed, 786 passed in 65.62s (0:01:05)`

Git branch: `main`

Latest commit: `1020f69`

Git status:

```text
 M data/results/mentions_latency_metadata.json
 M data/results/monitor_anomaly_case_review_packets.csv
 M data/results/monitor_anomaly_case_review_packets.json
 M data/results/monitor_anomaly_review_access_contract.json
 M data/results/monitor_anomaly_review_dashboard.html
 M data/results/monitor_anomaly_review_decision_readiness.csv
 M data/results/monitor_anomaly_review_decision_readiness.json
 M data/results/monitor_anomaly_review_metadata.json
 M data/results/monitor_anomaly_review_queue.csv
 M data/results/monitor_anomaly_review_status_transitions.csv
 M data/results/monitor_anomaly_review_status_transitions.json
 M data/results/monitor_anomaly_review_summary.csv
 M data/results/monitor_candidate_human_review_report.csv
 M data/results/monitor_candidate_human_review_report.html
 M data/results/monitor_candidate_human_review_report_metadata.json
 M data/results/monitor_candidate_materiality_context.csv
 M data/results/monitor_reference_candidate_dashboard.html
 M data/results/monitor_reference_candidate_features.csv
 M data/results/monitor_reference_candidate_metadata.json
 M data/results/monitor_reference_candidate_similarity_scores.csv
 M data/results/monitor_reference_candidate_similarity_summary.csv
 M data/results/monitor_reference_candidate_summary.csv
 M data/results/monitor_v2_polymarket_live_collection_metadata.json
 M data/results/monitor_v2_polymarket_live_input_validation_report.json
 M data/results/monitor_v2_polymarket_live_market_snapshots.csv
 M data/results/monitor_v2_polymarket_live_wallet_tier_snapshots.csv
 M data/results/monitor_v2_polymarket_live_watchlist.csv
 M data/results/monitor_v2_polymarket_rolling_alert_rows.csv
 M data/results/monitor_v2_polymarket_rolling_alert_summary.csv
 M data/results/monitor_v2_polymarket_rolling_history.png
 M data/results/monitor_v2_polymarket_rolling_history_figure_metadata.json
 M data/results/monitor_v2_polymarket_rolling_history_metadata.json
 M data/results/monitor_v2_polymarket_rolling_scoring_metadata.json
 M data/results/monitor_v2_polymarket_rolling_scoring_snapshots.csv
 M data/results/monitor_v2_polymarket_rolling_scoring_validation_report.json
 M data/results/stage3_llm_audit_log.jsonl
 M operations/pipeline/run_dashboard.py
 M tests/test_run_dashboard.py
```

Git diff stat:

```text
 data/results/mentions_latency_metadata.json        |   2 +-
 .../monitor_anomaly_case_review_packets.csv        |   4 +
 .../monitor_anomaly_case_review_packets.json       |  74 ++-
 .../monitor_anomaly_review_access_contract.json    |  14 +-
 data/results/monitor_anomaly_review_dashboard.html |  96 ++-
 .../monitor_anomaly_review_decision_readiness.csv  |   4 +
 .../monitor_anomaly_review_decision_readiness.json |  62 +-
 data/results/monitor_anomaly_review_metadata.json  |  10 +-
 data/results/monitor_anomaly_review_queue.csv      |  10 +-
 .../monitor_anomaly_review_status_transitions.csv  |   4 +
 .../monitor_anomaly_review_status_transitions.json |  58 +-
 data/results/monitor_anomaly_review_summary.csv    |   2 +-
 .../monitor_candidate_human_review_report.csv      |  10 +-
 .../monitor_candidate_human_review_report.html     | 278 +++++++-
 ...tor_candidate_human_review_report_metadata.json |   6 +-
 .../monitor_candidate_materiality_context.csv      |  10 +-
 .../monitor_reference_candidate_dashboard.html     |  12 +-
 .../monitor_reference_candidate_features.csv       |  32 +
 .../monitor_reference_candidate_metadata.json      |  10 +-
 ...nitor_reference_candidate_similarity_scores.csv |   8 +
 ...itor_reference_candidate_similarity_summary.csv |   4 +
 .../monitor_reference_candidate_summary.csv        |   2 +-
 ...tor_v2_polymarket_live_collection_metadata.json |   8 +-
 ...v2_polymarket_live_input_validation_report.json |  10 +-
 ...monitor_v2_polymarket_live_market_snapshots.csv |  40 ++
 ...or_v2_polymarket_live_wallet_tier_snapshots.csv |  20 +
 .../monitor_v2_polymarket_live_watchlist.csv       |  10 +-
 .../monitor_v2_polymarket_rolling_alert_rows.csv   | 120 ++++
 ...monitor_v2_polymarket_rolling_alert_summary.csv |  48 +-
 .../monitor_v2_polymarket_rolling_history.png      | Bin 130370 -> 132234 bytes
 ...polymarket_rolling_history_figure_metadata.json |   8 +-
 ...tor_v2_polymarket_rolling_history_metadata.json |  34 +-
 ...tor_v2_polymarket_rolling_scoring_metadata.json |  24 +-
 ...tor_v2_polymarket_rolling_scoring_snapshots.csv | 120 ++++
 ...lymarket_rolling_scoring_validation_report.json |  10 +-
 data/results/stage3_llm_audit_log.jsonl            | 720 +++++++++++++++++++++
 operations/pipeline/run_dashboard.py               | 187 +++++-
 tests/test_run_dashboard.py                        |  79 +++
 38 files changed, 1999 insertions(+), 151 deletions(-)
```

Blockers:

- Worktree has uncommitted changes that need review before commit.
- Pytest is failing; inspect output before continuing.

Next recommended action:

- feat: add h3 informed trading signature diagnostics
<!-- PROJECT_STATUS:END -->

## Current Status

Status date: 2026-05-18

The project now has deterministic daily H1, H2, and H3 baseline outputs, and
the empirical baseline package has been reviewed in
`docs/research/RESEARCH_SPEC.md`. The active work is preparing compact
thesis-facing result summaries before Overleaf export or interpretation-layer
work.

Current implemented foundation and H2 baseline:

- SQLite schema support tables exist or are migrated idempotently.
- Validation foundation exists for core row types.
- Data inventory module exists.
- First deterministic Brier baseline exists.
- RCP usage in Brier and calibration code is guarded by explicit flags.
- Agent and MCP entry points are deferred.
- Canonical event catalog audit and loader exist.
- Project-control automation exists for goal-driven Codex work.
- Deterministic H2 event-window CSV outputs exist under `data/results/`.
- The H2 row-level and summary CSV shapes are accepted for the initial daily
  baseline.
- Compact H2 summaries are persisted idempotently into `analysis_summaries`.
- H3 wallet-tier method is selected as wallet-level cumulative observed
  `amount_usd` percentiles.
- H3 wallet distribution inventory exists under `data/results/`.
- H3 wallet tier classification exists under `data/results/`.
- H3 tiered daily wallet activity series exists under `data/results/`.
- H3 descriptive lead-time histograms exist under `data/results/`.
- H3 daily lead-lag correlations and Granger outputs exist under
  `data/results/`.
- H3 Granger interpretation limits and sensitivity needs are documented.
- H1-H3 empirical baseline review is documented in
  `docs/research/RESEARCH_SPEC.md`.

## Event Catalog Audit Result

Current command:

```powershell
.\.venv\Scripts\python.exe -m operations.tools.event_catalog_audit
```

Current result against `data/thesis.db`:

| Check | Result |
| --- | ---: |
| Row count | 27 |
| Missing `event_id` | 20 |
| Missing `event_date` | 20 |
| Missing `title` | 20 |
| Missing `source_url` | 20 |
| Missing `expected_direction` | 20 |
| Missing `relevance_score` | 20 |
| Invalid canonical dates | 0 |
| Detectable duplicate `event_id` | 0 |
| Detectable duplicate canonical keys | 0 |
| Detectable duplicate legacy keys | 0 |

Interpretation: 20 legacy event rows remain without canonical fields, while
the tracked seed CSV contains the curated 7-event H2 set used for deterministic
output generation. The legacy rows are preserved but are not the default source
for H2 outputs.

## Current Blockers

- RCP is not a native probability forecast. It remains a polling signal until a
  documented and tested probability transformation exists.
- H3 wallet data currently has a BUY-only limitation and a minimum observed
  `amount_usd` of 10000, which remain source-filter metadata rather than
  analytical tier thresholds.
- Thesis-facing H1-H3 result summary tables are not prepared yet.
- Agent and MCP layers remain deferred.

## Next Recommended Commits

1. `docs: review h1 h2 h3 empirical baseline`
   - Commit the empirical baseline review and next active thesis-summary goal.
   - Acceptance: thesis-ready result tables and sensitivity gaps are explicit.

2. `docs: prepare h1 h2 h3 thesis result summaries`
   - Prepare compact, traceable result summaries for thesis drafting.
   - Acceptance: each summary maps to deterministic source artifacts.

3. `docs: document h2 thesis interpretation limits`
   - Document daily-window interpretation, event timing limitations, and
     accepted wording for H2.
   - Acceptance: thesis-facing text stays aligned with deterministic outputs.

## Mentions-Latenz, 10.10.2026, Umsetzung

Expliziter Nutzerauftrag: frühe Auswertung, unabhängige Quellen, WS-Bücher,
SDK-Tokenwarmup und Offline-Vergleich. Kein Bot gestartet, keine Order gesendet.
Während Download weiterhin 20 s mit 2 s Overlap. Finaler GPU-Rest liefert jetzt
jedes fertige ASR-Segment sofort; andere Transkriptor-Aufrufer behalten den
vollständigen Flush. Quellen und Buchlogger blockieren Audio nicht mehr.

E292-Replay: erstes Segment 17,85 statt 44,44 s; Anthropic-Schwelle 18,91 statt
44,44 s, Microsoft 22,41 statt 44,44 s. Alle 13 Marktstände identisch.
Durchgehend 20-s-GPU-Aufträge verworfen: 152,34 s insgesamt und Zuckerberg verpasst.
CPU/GPU-Probe auf 360 s: 66,15 s parallel statt 89,64 s seriell; nicht produktiv übernommen.
Das sind warme ASR-Zeiten, kein gemessener Ordervorsprung.

Prüfung: 111 fokussierte Tests bestanden. Isolierte Gesamtsuite: 1514 bestanden,
ein vorhandener Schema-2/3-Testfehler. Entwicklungskopie nach Übernahme: 1565 bestanden.
Ruff bestanden; unabhängiges Review ohne verbleibendes blockierendes Finding.
Vier globale Projekt-Review-Beanstandungen bleiben. Kein pauschales Ready-Signal.

Bericht: docs/project/MENTIONS_OPTIMIERUNG_2026-10-10.md
ADR: docs/decisions/2026-10-10-mentions-latenz.md
Messdateien: docs/project/evidence/mentions_latency_20261010/

Offen: Order-Parallelisierung mit Budgetreservierung, SDK-Versionscache,
Fill-Buchhaltung, Jev. NO-Konsens und Gap-Verify bleiben erhalten.
Intendant-Agenda nicht erreichbar (HTTP 426/TLS); offene Punkte im Bericht gesichert.
Nächster Commit: perf(mentions): stream final ASR results and decouple public market data
Nur eigene Änderungen aufnehmen, vorhandene Config-/Basisratenarbeit nicht mitziehen.


## Mentions-Nachauftrag: MP3 und parallele Orders, 10. Oktober 2026

Fortlaufende MP3-Dekodierung und unabhängige gleichzeitige Wort-Aufträge
umgesetzt. Live-All-In nutzt das verfügbare Wallet mit gemeinsamer Reservierung,
3-%-Puffer und bestehenden Preisdeckeln. Paper behält simuliertes Gesamtbudget.
Bekannte verspätete Fills setzen den Sweep fort, unbekannte POSTs halten
Reservierung. STOP/NO-Konsens/Gap-Verify erhalten. Kein Live-Bot gestartet.

E292: zehn wachsende Präfixe58,97 zu8,98s Dekodierung, fertige89'508'096 Samples
bitgleich. Keine Messung des Vorsprungs bis zum echten Fill.
Entwicklung:1588 Tests PASS in105,90s; operativ134 fokussierte Tests PASS.
Operativ separat bestehender Schema2/3-Fehler:12 PASS/1 FAIL. Vier vorhandene
globale Projekt-Review-Fehlergruppen bleiben. Keine allgemeine Repo-Freigabe.

Bericht: docs/project/MENTIONS_OPTIMIERUNG_2026-10-10.md
ADR: docs/decisions/2026-10-10-mentions-latenz.md
Evidenz: docs/project/evidence/mentions_latency_20261010/followup_verification.json
Offen: Jev, reale Publikations-zu-Fill-Messung, Recovery unklarer POSTs über
Neustart, prozessübergreifende Budgetreservierung und ASR-unabhängiger Resume
nach verzögerter Bestätigung. Eigene Änderungen nicht gestaged/committed.
Nächster eigener Commit: perf(mentions): decode growing audio once and parallelize wallet sweeps.


### Lokaler Commit auf Nutzerauftrag, 10.10.2026

Expliziter Nachauftrag «commiten»: Mentions-Änderungen in beiden Repositories
lokal committen, ohne Push. Codestand per SHA-256 unverändert gegenüber
followup_verification.json. Frische fokussierte Entwicklungssuite: 134 PASS
in 12,81 s. Vorhandene Config-/Basisratenänderungen und fremde
Status-/Logabschnitte bleiben ausserhalb des Commits.
Commit: perf(mentions): decode growing audio once and parallelize wallet sweeps.
