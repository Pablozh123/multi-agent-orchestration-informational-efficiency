# H1 Source Review Decision Queue

Dieses Artefakt verdichtet die H1 Source Review auf eine konkrete Entscheidungsqueue. Es liest keine Quelleninhalte, setzt keine Page-/Section-Notes, trifft keinen Claim-Support-Entscheid und promotet keinen Quellenstatus.

## Counts

- H1 decision rows: 10
- Unique H1 sources: 4
- Method rows: 4
- Interpretation rows: 6
- External locator rows: 7
- Local PDF rows: 3
- Final citation ready rows: 0

## Decision Queue

| decision_order | source_id | evidence_id | item_type | access_route | decision_focus_de | queue_status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_brier_001 | method_h1_brier_dm | method | external_locator_review | Methodenanker: Quelle gegen H1 Brier-/DM-Methodenwahl pruefen. | pending_manual_h1_source_review |
| 2 | lit_brier_001 | interpretation_h1_bounded_advantage | interpretation | external_locator_review | Interpretationsgrenze: bounded H1 Support nur im definierten Vergleichsscope pruefen. | pending_manual_h1_source_review |
| 3 | lit_brier_001 | interpretation_h1_broad_claim_not_proven | interpretation | external_locator_review | Interpretationsgrenze: breite Polymarket-Ueberlegenheitsbehauptung bleibt nicht belegt. | pending_manual_h1_source_review |
| 4 | lit_dm_001 | method_h1_brier_dm | method | external_locator_review | Methodenanker: Quelle gegen H1 Brier-/DM-Methodenwahl pruefen. | pending_manual_h1_source_review |
| 5 | lit_dm_001 | interpretation_h1_bounded_advantage | interpretation | external_locator_review | Interpretationsgrenze: bounded H1 Support nur im definierten Vergleichsscope pruefen. | pending_manual_h1_source_review |
| 6 | lit_emh_001 | method_h1_brier_dm | method | external_locator_review | Methodenanker: Quelle gegen H1 Brier-/DM-Methodenwahl pruefen. | pending_manual_h1_source_review |
| 7 | lit_emh_001 | interpretation_h1_broad_claim_not_proven | interpretation | external_locator_review | Interpretationsgrenze: breite Polymarket-Ueberlegenheitsbehauptung bleibt nicht belegt. | pending_manual_h1_source_review |
| 8 | zotero_poly_002 | method_h1_brier_dm | method | local_pdf_review | Methodenanker: Quelle gegen H1 Brier-/DM-Methodenwahl pruefen. | pending_manual_h1_source_review |
| 9 | zotero_poly_002 | interpretation_h1_bounded_advantage | interpretation | local_pdf_review | Interpretationsgrenze: bounded H1 Support nur im definierten Vergleichsscope pruefen. | pending_manual_h1_source_review |
| 10 | zotero_poly_002 | interpretation_h1_broad_claim_not_proven | interpretation | local_pdf_review | Interpretationsgrenze: breite Polymarket-Ueberlegenheitsbehauptung bleibt nicht belegt. | pending_manual_h1_source_review |

## Use Rule

Arbeite die Queue in `decision_order` ab. Fuer jede Zeile muss ein Mensch die Quelle oeffnen und Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use und Reviewer-Kommentar erfassen. Bis diese Felder belegt sind, bleibt H1 final blockiert: keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.

## Future Agent Boundary

Spaetere Agenten duerfen nur fehlende Felder markieren oder Evidence-ID, Quelle und Artefakt spiegeln. Sie duerfen keine Quelleninhalte bewerten, keine Seitenzahlen erfinden, keine Zitation freigeben und keine Kennzahlen berechnen. Jede spaetere Nutzung braucht ein separates Goal, bounded inputs mit max 50 rows, Tests und `llm_audit_log`.
