# H3 Source Review Ledger Fill Guide

Dieser Guide zeigt, wie die acht H3 Worksheet-Zeilen manuell in den Source Review Progress Ledger uebertragen werden. Er schreibt keine Ledger-Felder, liest keine Quelleninhalte, setzt keine Page-/Section-Notes, entscheidet keinen Claim-Support, promotet keinen Quellenstatus und erzeugt keine finale Zitation. Die H3 Granger-Grenze und Wallet-Grenze bleiben pro Zeile sichtbar.

## Counts

- Guide rows: 8
- Matched ledger rows: 8
- Unique sources: 4
- Method rows: 5
- Interpretation rows: 3
- External locator rows: 2
- Local PDF rows: 6
- Final release ready rows: 0
- Selected table/figure: T4/F3

## Fill Rows

| guide_order | source_id | evidence_id | item_type | ledger_id | access_route | current_ledger_progress_state | fill_sequence_de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_granger_001 | method_h3_granger_timing | method | ledger_h3_lit_granger_001__method_h3_granger_timing | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 2 | lit_granger_001 | interpretation_h3_top_tier_signal | interpretation | ledger_h3_lit_granger_001__interpretation_h3_top_tier_signal | external_locator_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 3 | zotero_poly_001 | method_h3_wallet_tiers | method | ledger_h3_zotero_poly_001__method_h3_wallet_tiers | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 4 | zotero_poly_001 | interpretation_h3_top_tier_signal | interpretation | ledger_h3_zotero_poly_001__interpretation_h3_top_tier_signal | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 5 | zotero_poly_005 | method_h3_granger_timing | method | ledger_h3_zotero_poly_005__method_h3_granger_timing | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 6 | zotero_poly_005 | method_h3_wallet_tiers | method | ledger_h3_zotero_poly_005__method_h3_wallet_tiers | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 7 | zotero_poly_005 | interpretation_h3_top_tier_signal | interpretation | ledger_h3_zotero_poly_005__interpretation_h3_top_tier_signal | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |
| 8 | zotero_poly_007 | method_h3_wallet_tiers | method | ledger_h3_zotero_poly_007__method_h3_wallet_tiers | local_pdf_review | pending_manual_review | 1 Page-/Section-Note erfassen; 2 Claim-Support entscheiden; 3 Blocked-Wording pruefen; 4 H3 Granger-Grenze pruefen; 5 H3 Wallet-Grenze pruefen; 6 Citation-Use setzen; 7 reviewed_by, reviewed_at und review_comment_de dokumentieren; 8 Ledger regenerieren und preserved_manual_fields pruefen. |

## Use Rule

Arbeite die Guide-Zeilen in `guide_order` ab. Pro Zeile nur diese Ledger-Felder manuell pflegen: `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at` und `review_comment_de`. Fuer H3 zusaetzlich Granger-Grenze und Wallet-Grenze pruefen: keine Kausalclaims, keine Private-Information-Beweise, keine willkuerlichen Whale-Schwellen, keine Wallet-Adressen, keine Trading-Claims und keine Profitabilitaetsclaims. Danach den Ledger regenerieren und pruefen, ob `preserved_manual_fields=True` und der `review_progress_state` plausibel gesetzt ist. Keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, max 50 rows und `llm_audit_log` fuer spaetere Agentenhilfe.
