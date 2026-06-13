# H2 Source Review Ledger Fill Guide

Dieser Guide zeigt, wie die fuenf H2 Worksheet-Zeilen manuell in den Source Review Progress Ledger uebertragen werden. Er schreibt keine Ledger-Felder, liest keine Quelleninhalte, setzt keine Page-/Section-Notes, entscheidet keinen Claim-Support, promotet keinen Quellenstatus und erzeugt keine finale Zitation. Die H2 Kausalclaim-Grenze bleibt pro Zeile sichtbar.

## Counts

- Guide rows: 5
- Matched ledger rows: 5
- Unique sources: 3
- Method rows: 3
- Interpretation rows: 2
- External locator rows: 4
- Local PDF rows: 1
- Final release ready rows: 0
- Selected table/figure: T3/F2

## Fill Rows

| guide_order | source_id | evidence_id | item_type | ledger_id | access_route | current_ledger_progress_state | fill_sequence_de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_emh_001 | method_h2_event_window | method | ledger_h2_lit_emh_001__method_h2_event_window | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; 5 Citation-Use setzen; 6 reviewed_by, reviewed_at und review_comment_de dokumentieren; 7 Ledger regenerieren und preserved_manual_fields pruefen. |
| 2 | lit_emh_001 | interpretation_h2_daily_response | interpretation | ledger_h2_lit_emh_001__interpretation_h2_daily_response | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; 5 Citation-Use setzen; 6 reviewed_by, reviewed_at und review_comment_de dokumentieren; 7 Ledger regenerieren und preserved_manual_fields pruefen. |
| 3 | lit_eventstudy_001 | method_h2_event_window | method | ledger_h2_lit_eventstudy_001__method_h2_event_window | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; 5 Citation-Use setzen; 6 reviewed_by, reviewed_at und review_comment_de dokumentieren; 7 Ledger regenerieren und preserved_manual_fields pruefen. |
| 4 | lit_eventstudy_001 | interpretation_h2_daily_response | interpretation | ledger_h2_lit_eventstudy_001__interpretation_h2_daily_response | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; 5 Citation-Use setzen; 6 reviewed_by, reviewed_at und review_comment_de dokumentieren; 7 Ledger regenerieren und preserved_manual_fields pruefen. |
| 5 | zotero_poly_001 | method_h2_event_window | method | ledger_h2_zotero_poly_001__method_h2_event_window | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H2 Kausalclaim-Grenze pruefen; 5 Citation-Use setzen; 6 reviewed_by, reviewed_at und review_comment_de dokumentieren; 7 Ledger regenerieren und preserved_manual_fields pruefen. |

## Use Rule

Arbeite die Guide-Zeilen in `guide_order` ab. Pro Zeile nur diese Ledger-Felder manuell pflegen: `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at` und `review_comment_de`. Fuer H2 zusaetzlich die Kausalclaim-Grenze pruefen: keine Kausalitaet, keine sofortige Marktreaktion und keine Intraday-Ueberclaims aus daily Event-Windows. Danach den Ledger regenerieren und pruefen, ob `preserved_manual_fields=True` und der `review_progress_state` plausibel gesetzt ist. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Kausalclaims, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, max 50 rows und `llm_audit_log` fuer spaetere Agentenhilfe.
