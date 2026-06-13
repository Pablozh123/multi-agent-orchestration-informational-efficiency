# H1 Source Review Ledger Fill Guide

Dieser Guide zeigt, wie die zehn H1 Worksheet-Zeilen manuell in den Source Review Progress Ledger uebertragen werden. Er schreibt keine Ledger-Felder, liest keine Quelleninhalte, setzt keine Page-/Section-Notes, entscheidet keinen Claim-Support, promotet keinen Quellenstatus und erzeugt keine finale Zitation.

## Counts

- Guide rows: 10
- Matched ledger rows: 10
- Unique sources: 4
- Method rows: 4
- Interpretation rows: 6
- External locator rows: 7
- Local PDF rows: 3
- Final release ready rows: 0
- Selected table/figure: T2/F1

## Fill Rows

| guide_order | source_id | evidence_id | item_type | ledger_id | access_route | current_ledger_progress_state | fill_sequence_de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_brier_001 | method_h1_brier_dm | method | ledger_h1_lit_brier_001__method_h1_brier_dm | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 2 | lit_brier_001 | interpretation_h1_bounded_advantage | interpretation | ledger_h1_lit_brier_001__interpretation_h1_bounded_advantage | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 3 | lit_brier_001 | interpretation_h1_broad_claim_not_proven | interpretation | ledger_h1_lit_brier_001__interpretation_h1_broad_claim_not_proven | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 4 | lit_dm_001 | method_h1_brier_dm | method | ledger_h1_lit_dm_001__method_h1_brier_dm | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 5 | lit_dm_001 | interpretation_h1_bounded_advantage | interpretation | ledger_h1_lit_dm_001__interpretation_h1_bounded_advantage | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 6 | lit_emh_001 | method_h1_brier_dm | method | ledger_h1_lit_emh_001__method_h1_brier_dm | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 7 | lit_emh_001 | interpretation_h1_broad_claim_not_proven | interpretation | ledger_h1_lit_emh_001__interpretation_h1_broad_claim_not_proven | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 8 | zotero_poly_002 | method_h1_brier_dm | method | ledger_h1_zotero_poly_002__method_h1_brier_dm | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 9 | zotero_poly_002 | interpretation_h1_bounded_advantage | interpretation | ledger_h1_zotero_poly_002__interpretation_h1_bounded_advantage | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |
| 10 | zotero_poly_002 | interpretation_h1_broad_claim_not_proven | interpretation | ledger_h1_zotero_poly_002__interpretation_h1_broad_claim_not_proven | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 Citation-Use setzen; 5 reviewed_by, reviewed_at und review_comment_de dokumentieren; 6 Ledger regenerieren und preserved_manual_fields pruefen. |

## Use Rule

Arbeite die Guide-Zeilen in `guide_order` ab. Pro Zeile nur diese Ledger-Felder manuell pflegen: `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at` und `review_comment_de`. Danach den Ledger regenerieren und pruefen, ob `preserved_manual_fields=True` und der `review_progress_state` plausibel gesetzt ist. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, max 50 rows und `llm_audit_log` fuer spaetere Agentenhilfe.
