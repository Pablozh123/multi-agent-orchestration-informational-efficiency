# H2 Source Review Batch Worksheet

Dieses Worksheet ist die manuelle Arbeitsliste fuer den zweiten H2 Source-Review-Batch. Es setzt keine Page-/Section-Notes, trifft keine Claim-Support-Entscheide, promotet keinen Quellenstatus und erzeugt keine finale Zitation.

## Counts

- Worksheet rows: 5
- Unique sources: 3
- Method rows: 3
- Interpretation rows: 2
- External locator rows: 4
- Local PDF rows: 1
- Pending citation rows: 5
- Final release ready rows: 0
- Selected table/figure: T3/F2
- Update checklist steps: 8

## Worksheet Rows

| worksheet_order | source_id | evidence_id | item_type | access_route | selected_table | selected_figure | current_citation_use_decision | causal_claim_boundary_de | next_action_de |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_emh_001 | method_h2_event_window | method | external_locator_review | T3 | F2 | blocked_pending_manual_review | Kausalclaim-Grenze: H2 darf nur daily event-window movement und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; keine Kausalitaet und keine sofortige Marktreaktion behaupten. | H2: `lit_emh_001` fuer `method_h2_event_window` (method) manuell pruefen. Erst nach Page-/Section-Note, Claim-Support und Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere Agentenhilfe nur bounded mit max 50 rows und llm_audit_log. |
| 2 | lit_emh_001 | interpretation_h2_daily_response | interpretation | external_locator_review | T3 | F2 | blocked_pending_manual_review | Kausalclaim-Grenze: H2 darf nur daily event-window movement und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; keine Kausalitaet und keine sofortige Marktreaktion behaupten. | H2: `lit_emh_001` fuer `interpretation_h2_daily_response` (interpretation) manuell pruefen. Erst nach Page-/Section-Note, Claim-Support und Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere Agentenhilfe nur bounded mit max 50 rows und llm_audit_log. |
| 3 | lit_eventstudy_001 | method_h2_event_window | method | external_locator_review | T3 | F2 | blocked_pending_manual_review | Kausalclaim-Grenze: H2 darf nur daily event-window movement und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; keine Kausalitaet und keine sofortige Marktreaktion behaupten. | H2: `lit_eventstudy_001` fuer `method_h2_event_window` (method) manuell pruefen. Erst nach Page-/Section-Note, Claim-Support und Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere Agentenhilfe nur bounded mit max 50 rows und llm_audit_log. |
| 4 | lit_eventstudy_001 | interpretation_h2_daily_response | interpretation | external_locator_review | T3 | F2 | blocked_pending_manual_review | Kausalclaim-Grenze: H2 darf nur daily event-window movement und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; keine Kausalitaet und keine sofortige Marktreaktion behaupten. | H2: `lit_eventstudy_001` fuer `interpretation_h2_daily_response` (interpretation) manuell pruefen. Erst nach Page-/Section-Note, Claim-Support und Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere Agentenhilfe nur bounded mit max 50 rows und llm_audit_log. |
| 5 | zotero_poly_001 | method_h2_event_window | method | local_pdf_review | T3 | F2 | blocked_pending_manual_review | Kausalclaim-Grenze: H2 darf nur daily event-window movement und deskriptive Reaktion im verfuegbaren Tagesraster beschreiben; keine Kausalitaet und keine sofortige Marktreaktion behaupten. | H2: `zotero_poly_001` fuer `method_h2_event_window` (method) manuell pruefen. Erst nach Page-/Section-Note, Claim-Support und Blocked-Wording-Check darf die row fuer finale Zitation vorbereitet werden. Keine Rohartefakt-Dumps, keine Runtime-Agenten; spaetere Agentenhilfe nur bounded mit max 50 rows und llm_audit_log. |

## Use Rule

Arbeite H2 row-by-row: Quelle oeffnen, Page-/Section-Note eintragen, Claim-Support entscheiden, Blocked-Wording und Kausalclaim-Grenze pruefen, Citation-Use setzen und reviewer metadata dokumentieren. Erlaubte Ledger-Felder bleiben `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at` und `review_comment_de`. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Kausalclaims, keine Intraday-Ueberclaims, keine Rohartefakt-Dumps und keine Runtime-Agenten. Spaetere Agentenhilfe nur bounded mit max 50 rows und `llm_audit_log`.
