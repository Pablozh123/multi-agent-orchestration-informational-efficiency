# H3 Source Review Decision Queue

Dieses Artefakt verdichtet die H3 Source Review auf eine konkrete Entscheidungsqueue. Es liest keine Quelleninhalte, setzt keine Page-/Section-Notes, trifft keinen Claim-Support-Entscheid und promotet keinen Quellenstatus.

## Counts

- H3 decision rows: 8
- Unique H3 sources: 4
- Method rows: 5
- Interpretation rows: 3
- External locator rows: 2
- Local PDF rows: 6
- Final citation ready rows: 0

## Decision Queue

| decision_order | source_id | evidence_id | item_type | access_route | decision_focus_de | queue_status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | lit_granger_001 | method_h3_granger_timing | method | external_locator_review | Methodenanker: Quelle gegen Granger-/Lead-Lag-Diagnostik pruefen; keine Kausalitaet ableiten. | pending_manual_h3_source_review |
| 2 | lit_granger_001 | interpretation_h3_top_tier_signal | interpretation | external_locator_review | Interpretationsgrenze: top-tier timing pattern als bounded predictive diagnostic pruefen. | pending_manual_h3_source_review |
| 3 | zotero_poly_001 | method_h3_wallet_tiers | method | local_pdf_review | Methodenanker: Quelle gegen dataset-relative Wallet-Tiers pruefen; keine festen Whale-Schwellen. | pending_manual_h3_source_review |
| 4 | zotero_poly_001 | interpretation_h3_top_tier_signal | interpretation | local_pdf_review | Interpretationsgrenze: top-tier timing pattern als bounded predictive diagnostic pruefen. | pending_manual_h3_source_review |
| 5 | zotero_poly_005 | method_h3_granger_timing | method | local_pdf_review | Methodenanker: Quelle gegen Granger-/Lead-Lag-Diagnostik pruefen; keine Kausalitaet ableiten. | pending_manual_h3_source_review |
| 6 | zotero_poly_005 | method_h3_wallet_tiers | method | local_pdf_review | Methodenanker: Quelle gegen dataset-relative Wallet-Tiers pruefen; keine festen Whale-Schwellen. | pending_manual_h3_source_review |
| 7 | zotero_poly_005 | interpretation_h3_top_tier_signal | interpretation | local_pdf_review | Interpretationsgrenze: top-tier timing pattern als bounded predictive diagnostic pruefen. | pending_manual_h3_source_review |
| 8 | zotero_poly_007 | method_h3_wallet_tiers | method | local_pdf_review | Methodenanker: Quelle gegen dataset-relative Wallet-Tiers pruefen; keine festen Whale-Schwellen. | pending_manual_h3_source_review |

## Use Rule

Arbeite die Queue in `decision_order` ab. Fuer jede Zeile muss ein Mensch die Quelle oeffnen und Page-/Section-Note, Claim-Support, Blocked-Wording, Citation-Use, Granger-Grenze, Wallet-Grenze und Reviewer-Kommentar erfassen. Bis diese Felder belegt sind, bleibt H3 final blockiert: keine finale Zitation, keine Quellenstatus-Hochstufung, keine Rohartefakt-Dumps, keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade.

## H3 Boundary

H3 darf Granger- und Lead-Lag-Signale nur als predictive timing diagnostics unter Modellannahmen formulieren. Die Queue blockiert Kausalclaims, Private-Information-Beweise, Profitabilitaetsclaims, Trading-Claims, willkuerliche Whale-Schwellen und Wallet-Adressen.

## Future Agent Boundary

Spaetere Agenten duerfen nur fehlende Felder markieren oder Evidence-ID, Quelle und Artefakt spiegeln. Sie duerfen keine Quelleninhalte bewerten, keine Seitenzahlen erfinden, keine Granger-Grenze oder Wallet-Grenze lockern, keine Zitation freigeben und keine Kennzahlen berechnen. Jede spaetere Nutzung braucht ein separates Goal, bounded inputs mit max 50 rows, Tests und `llm_audit_log`.
