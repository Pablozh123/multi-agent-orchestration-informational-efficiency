# H2 Source Review Decision Queue

Dieses Artefakt verdichtet die H2 Source Review auf eine konkrete Entscheidungsqueue. Es liest keine Quelleninhalte, setzt keine Page-/Section-Notes, trifft keinen Claim-Support-Entscheid und promotet keinen Quellenstatus.

## Counts

- H2 decision rows: 5
- Unique H2 sources: 3
- Method rows: 3
- Interpretation rows: 2
- External locator rows: 4
- Local PDF rows: 1
- Final citation ready rows: 0

## Decision Queue

| decision_order | source_id | evidence_id | item_type | access_route | decision_focus_de | queue_status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_emh_001 | method_h2_event_window | method | external_locator_review | Methodenanker: Quelle gegen H2 Event-Window-Design und Ereigniskuration pruefen. | pending_manual_h2_source_review |
| 2 | lit_emh_001 | interpretation_h2_daily_response | interpretation | external_locator_review | Interpretationsgrenze: sichtbare Tagesbewegung ohne Intraday- oder Kausalclaim pruefen. | pending_manual_h2_source_review |
| 3 | lit_eventstudy_001 | method_h2_event_window | method | external_locator_review | Methodenanker: Quelle gegen H2 Event-Window-Design und Ereigniskuration pruefen. | pending_manual_h2_source_review |
| 4 | lit_eventstudy_001 | interpretation_h2_daily_response | interpretation | external_locator_review | Interpretationsgrenze: sichtbare Tagesbewegung ohne Intraday- oder Kausalclaim pruefen. | pending_manual_h2_source_review |
| 5 | zotero_poly_001 | method_h2_event_window | method | local_pdf_review | Methodenanker: Quelle gegen H2 Event-Window-Design und Ereigniskuration pruefen. | pending_manual_h2_source_review |

## Use Rule

Arbeite die Queue in `decision_order` ab. Fuer jede Zeile muss ein Mensch die Quelle oeffnen und Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, Kausalclaim-Grenze und Reviewer-Kommentar erfassen. Bis diese Felder belegt sind, bleibt H2 final blockiert: keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.

## H2 Boundary

H2 darf nur als taegliche Event-Window-Evidenz ueber vorkuratierte oeffentliche Ereignisse und fixe Fenster formuliert werden. Die Queue blockiert Intraday-Geschwindigkeitsaussagen, Kausalclaims und post-hoc Ereignisauswahl.

## Future Agent Boundary

Spaetere Agenten duerfen nur fehlende Felder markieren oder Evidence-ID, Quelle und Artefakt spiegeln. Sie duerfen keine Quelleninhalte bewerten, keine Seitenzahlen erfinden, keine Kausalclaim-Grenze lockern, keine Zitation freigeben und keine Kennzahlen berechnen. Jede spaetere Nutzung braucht ein separates Goal, bounded inputs mit max 50 rows, Tests und `llm_audit_log`.
