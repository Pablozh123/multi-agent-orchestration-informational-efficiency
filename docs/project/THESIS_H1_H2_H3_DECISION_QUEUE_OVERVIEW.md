# H1-H2-H3 Decision Queue Overview

Diese Uebersicht konsolidiert die drei H1-H2-H3 Source Review Decision Queues in ein kompaktes Steuerungsartefakt. Sie liest nur deterministisch erzeugte Queue-CSVs, liest keine Quelleninhalte, setzt keine Page-/Section-Notes, trifft keine Claim-Support-Entscheide, promotet keinen Quellenstatus und macht keine finale Zitation.

## Counts

- Overview rows: 3
- Total decision rows: 23
- Unique sources across H1-H2-H3: 9
- Method rows: 12
- Interpretation rows: 11
- External locator rows: 13
- Local PDF rows: 10
- Pending queue rows: 23
- Final citation ready rows: 0
- Source-status change rows: 0

## Queue Overview

| slice_id | decision_rows | unique_sources | method_rows | interpretation_rows | pending_queue_rows | final_ready_rows | source_status_change_rows | selected_tables | selected_figures | queue_statuses | next_action_de |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 10 | 4 | 4 | 6 | 10 | 0 | 0 | T2 | F1 | pending_manual_h1_source_review | H1 Decision Queue source-by-source manuell bearbeiten; danach Ledger und bounded BA-Prosa aktualisieren, aber keine Zitation freigeben, solange Reviewfelder offen sind. |
| H2 | 5 | 3 | 3 | 2 | 5 | 0 | 0 | T3 | F2 | pending_manual_h2_source_review | H2 Decision Queue source-by-source manuell bearbeiten; danach Ledger und bounded BA-Prosa aktualisieren, aber keine Zitation freigeben, solange Reviewfelder offen sind. |
| H3 | 8 | 4 | 5 | 3 | 8 | 0 | 0 | T4 | F3 | pending_manual_h3_source_review | H3 Decision Queue source-by-source manuell bearbeiten; danach Ledger und bounded BA-Prosa aktualisieren, aber keine Zitation freigeben, solange Reviewfelder offen sind. |

## Use Rule

Arbeite die Review in der Reihenfolge H1, H2, H3 ab. Jede Queue-Zeile braucht manuell gesetzte Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use. H2 braucht zusaetzlich die Kausalclaim-Grenze. H3 braucht zusaetzlich Granger-Grenze und Wallet-Grenze. Bis diese Felder belegt und im Ledger kontrolliert sind, bleiben alle 23 H1-H2-H3 Decision Rows final blockiert: keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken.

## Future Agent Boundary

Spaetere Agentenhilfe darf nur fehlende Felder markieren, Evidence IDs spiegeln oder kompakte To-do-Hinweise aus maximal 50 rows erzeugen. Jede spaetere Nutzung braucht ein separates Goal, Tests und `llm_audit_log`. Agenten duerfen keine Quelleninhalte bewerten, keine Seitenzahlen erfinden, keine Kennzahlen berechnen, keine Zitation freigeben, keine Kausalclaims lockern, keine Wallet-Adressen ausgeben, keine Trading-Claims und keine Profitabilitaetsclaims formulieren.
