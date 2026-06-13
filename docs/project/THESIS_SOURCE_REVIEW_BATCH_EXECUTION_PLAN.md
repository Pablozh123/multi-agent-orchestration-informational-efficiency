# Source Review Batch Execution Plan

Dieser Plan ordnet die 23 offenen H1-H2-H3 Source-Review-Zeilen in drei manuelle Review-Batches und einen Rebuild-/Finalgate-Batch. Er liest keine Quelleninhalte, trifft keine Claim-Support-Entscheide, setzt keine Page-/Section-Notes, promotet keinen Quellenstatus und erzeugt keine finale Zitation.

## Counts

- Plan rows: 4
- Source review rows: 23
- Unique sources: 9
- Method rows: 12
- Interpretation rows: 11
- External locator rows: 13
- Local PDF rows: 10
- Pending citation rows: 23
- Final ready rows: 0
- Source-status change rows: 0
- Update checklist steps: 8
- Final release ready rows: 0

## Batch Rows

| batch_order | execution_batch | thesis_area | source_review_rows | unique_sources | pending_citation_rows | final_ready_rows | selected_tables | selected_figures | completion_gate_de | next_action_de |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | batch_01_h1_forecast_quality_source_review | H1 | 10 | 4 | 10 | 0 | T2 | F1 | H1 ist nur fuer finale Zitation bereit, wenn alle 10 H1 rows manuell abgeschlossen sind; aktuell 10 pending citation rows und 0 final-ready rows. | H1 Batch manuell gegen die Update Checklist starten. |
| 2 | batch_02_h2_event_window_source_review | H2 | 5 | 3 | 5 | 0 | T3 | F2 | H2 ist nur fuer finale Zitation bereit, wenn alle 5 H2 rows manuell abgeschlossen sind; aktuell 5 pending citation rows und 0 final-ready rows. | Nach H1 den H2 Batch mit Kausalclaim-Grenze manuell abarbeiten. |
| 3 | batch_03_h3_wallet_timing_source_review | H3 | 8 | 4 | 8 | 0 | T4 | F3 | H3 ist nur fuer finale Zitation bereit, wenn alle 8 H3 rows manuell abgeschlossen sind; aktuell 8 pending citation rows und 0 final-ready rows. | Nach H2 den H3 Batch mit Granger-Grenze und Wallet-Grenze abarbeiten. |
| 4 | batch_04_rebuild_and_finalgate | TOTAL | 23 | 9 | 23 | 0 | T2, T3, T4 | F1, F2, F3 | Finale Freigabe erst, wenn alle benoetigten rows Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use abgeschlossen haben; aktuell 23 pending citation rows, 0 final-ready rows und 0 source-status change rows. | Nach manuellen Ledger-Aenderungen Generatoren neu ausfuehren und erst bei gruenen Gates bounded BA-Prosa aktualisieren. |

## Use Rule

Arbeite die Batches in dieser Reihenfolge ab: H1, H2, H3, danach TOTAL Rebuild und Finalgate. Vor jeder Ledger-Aenderung gilt die Manual Source Review Update Checklist. Erlaubte manuelle Felder sind `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at`, `review_comment_de`. Alle 23 rows bleiben bis zur manuellen Page-/Section-Note, Claim-Support-, Blocked-Wording- und Citation-Use-Entscheidung citation-blocked. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein Model Routing, keine Rohdaten-Prompts, keine Wallet-Adressen, keine Trading-Claims und keine Profitabilitaetsclaims. Spaetere Agentenhilfe ist nur als missing-field oder to-do-Unterstuetzung mit max 50 rows, Tests und llm_audit_log zulaessig.
