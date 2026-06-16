# Manual Source Review Update Checklist

Diese Checkliste beschreibt, wie die manuellen Felder im Source Review Progress Ledger aktualisiert werden duerfen. Sie liest keine Quelleninhalte, trifft keine Claim-Support-Entscheide, setzt keine Page-/Section-Notes, promotet keinen Quellenstatus und macht keine finale Zitation.

## Counts

- Checklist rows: 8
- Ledger rows in scope: 23
- Unique sources in scope: 9
- External locator rows: 13
- Local PDF rows: 10
- Pending citation rows: 23
- Final ready rows: 0
- Final citation release ready checklist rows: 0

## Checklist Rows

| check_order | update_phase | manual_field_targets | pending_citation_rows | final_ready_rows | completion_test_de | next_action_de |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | preflight_alignment_and_gate_check | none | 23 | 0 | `matched_rows=23`, `field_mismatch_rows=0`, `blocked_pending_citation_rows=23`, `final_citation_ready_rows=0`. | Mit Source Access und Page-/Section-Note-Erfassung beginnen. |
| 2 | source_access_and_locator_review | page_or_section_note | 23 | 0 | `page_or_section_note` ist nicht leer und bezieht sich auf die konkrete Evidence ID. | Nach Page-/Section-Note Claim-Support entscheiden. |
| 3 | claim_support_decision | claim_support_decision; review_status | 23 | 0 | Claim-Support ist nicht `pending`; Begrenzung bleibt im Review-Kommentar sichtbar. | Danach Blocked-Wording gegen Quelle und Limitation pruefen. |
| 4 | blocked_wording_check | blocked_wording_check; review_comment_de | 23 | 0 | Blocked-Wording ist nicht `pending`; problematische Formulierungen sind notiert. | Danach Citation-Use als Draft, final, not usable oder needs_more_review setzen. |
| 5 | citation_use_decision | citation_use_decision; final_citation_ready | 23 | 0 | Final-ready Rows haben `approved_for_final_citation`; alle anderen Rows bleiben sichtbar blockiert. | Reviewer-Metadaten und Kommentar ergaenzen. |
| 6 | reviewer_metadata_and_comment | reviewed_by; reviewed_at; review_comment_de | 23 | 0 | Reviewer-Metadaten sind gesetzt, wenn eine row nicht mehr `pending_manual_review` ist. | Ledger regenerieren und Preservation pruefen. |
| 7 | regenerate_and_preserve_manual_fields | preserved_manual_fields; review_progress_state | 23 | 0 | `preserved_manual_fields=True` fuer geaenderte rows; Citation-Gate Summary aktualisiert. | Nach erfolgreichem Rebuild Source Review Checks und Index aktualisieren. |
| 8 | final_release_guard | final_citation_ready | 23 | 0 | Vor finaler BA-Abgabe: 0 pending required rows, 0 source-status changes, review_check gruen. | Bis dahin bounded Draft fortsetzen und Source Review manuell abarbeiten. |

## Use Rule

Arbeite diese acht Schritte vor jeder manuellen Ledger-Aenderung ab. Die einzigen manuell zu pflegenden Ledger-Felder sind `review_status`, `page_or_section_note`, `claim_support_decision`, `blocked_wording_check`, `citation_use_decision`, `reviewed_by`, `reviewed_at` und `review_comment_de`. Finale Zitation bleibt blockiert, solange Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use nicht abgeschlossen sind. Keine Quellenstatus-Hochstufung, keine Runtime-Agenten, kein MCP, kein Model Routing, keine Kennzahlen aus LLMs, keine Rohdaten-Prompts, max 50 rows und `llm_audit_log` fuer spaetere Agentenhilfe.
