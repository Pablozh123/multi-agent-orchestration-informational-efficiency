# Advisor Source Review Follow-up

Dieses Artefakt ordnet die naechsten Schritte nach Dozenten-Handoff: Feedback erfassen, Source-Review-Tiefe festlegen, H1-H2-H3 manuell reviewen, bounded Draft aktualisieren, Final-Gates erneut pruefen und Agenten nur als Future Work halten. Die Manual Source Review Follow-up Overview bleibt der kompakte Kontrollpunkt fuer die 23 offenen H1-H2-H3 Review-Zeilen. Es erzeugt keine neuen empirischen Resultate und interpretiert keine Quelleninhalte.

## Counts

- Follow-up rows: 8
- Manual Source Review rows: 23
- Manual Source Review pending rows: 23
- Manual Source Review final-ready rows: 0
- Final-submission-ready follow-up rows: 1

## Follow-up Rows

| followup_order | followup_id | workstream_de | current_evidence_de | required_next_action_de | guardrail_de |
| --- | --- | --- | --- | --- | --- |
| 1 | followup_01_capture_advisor_feedback | Dozentenfeedback erfassen | Feedback-Integration: 8 Rows; pending: 8; kleine Commit-Scopes: 8. | Dozentenantwort in das Feedback-Log eintragen und genau einen passenden kleinen Integrations-Scope waehlen. | Keine neuen empirischen Claims, kein Review-Access, keine Runtime-Agenten und keine Rohartefakt-Dumps aus Feedback ableiten. |
| 2 | followup_02_confirm_source_review_depth | Source-Review-Tiefe festlegen | Manual Source Review: 23 Rows; pending: 23; final-ready: 0; Quellenstatus-Aenderungen erlaubt: 0. Manual Source Review Follow-up Overview: 3 Slices; 23 offene H1-H2-H3 Review-Zeilen; 9 eindeutige Quellen; 23 pending; 0 final-ready. | Review-Tiefe gegen Source Review Protocol und Final Gate Board festlegen, ohne Quellenstatus automatisch hochzustufen. | Keine finale Zitation, keine Quellenstatus-Hochstufung und keine Candidate-Quelle fuer thesis-facing Claims. |
| 3 | followup_03_h1_manual_source_review | H1 Manual Source Review ausfuehren | H1: 10 Manual Source Review Rows; pending: 10; final-ready: 0; bounded-draft-ready: 10; final-submission-ready: 0. | H1: Quelle oeffnen, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use im Ledger erfassen. | Keine Quellenstatus-Hochstufung, keine finale Zitation, keine automatischen Page Notes und keine thesis-facing Claims ohne manuelle Entscheidung. |
| 4 | followup_04_h2_manual_source_review | H2 Manual Source Review ausfuehren | H2: 5 Manual Source Review Rows; pending: 5; final-ready: 0; bounded-draft-ready: 5; final-submission-ready: 0. | H2: Quelle oeffnen, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use im Ledger erfassen. | Keine Quellenstatus-Hochstufung, keine finale Zitation, keine automatischen Page Notes und keine thesis-facing Claims ohne manuelle Entscheidung. |
| 5 | followup_05_h3_manual_source_review | H3 Manual Source Review ausfuehren | H3: 8 Manual Source Review Rows; pending: 8; final-ready: 0; bounded-draft-ready: 8; final-submission-ready: 0. | H3: Quelle oeffnen, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use im Ledger erfassen. | Keine Quellenstatus-Hochstufung, keine finale Zitation, keine automatischen Page Notes und keine thesis-facing Claims ohne manuelle Entscheidung. |
| 6 | followup_06_update_bounded_chapter_draft | Bounded H1-H2-H3 Draft aktualisieren | Kernpaket: 5 Tabellen und 4 Figuren; Package gaps: 0. | Nur erlaubtes, source-gated Wording und wenige gute Tabellen/Figuren in den BA-Draft uebernehmen. | Keine neuen Kennzahlen, keine Rohartefakt-Dumps, keine Universal-, Intraday-, Kausalitaets- oder Profitabilitaetsclaims. |
| 7 | followup_07_recheck_final_gates | Final-Gates erneut pruefen | Final Gate Board: 8 Rows; final-ready: 1; final-blocked: 7; blocking count total: 31. | Source Review, Swiss Resultat-Gate, DOCX-Render-QA, review_check und commit_plan vor jedem Abschlussclaim erneut laufen lassen. | Keine finale Abgabebereitschaft behaupten, solange Source Review, Swiss-Gate oder DOCX-Render-QA offen sind. |
| 8 | followup_08_keep_agents_future_work | Agenten nur als Future Work halten | Agent Upgrade Rows: 7; active: 0; inactive/deferred: 7. | Agentenverbesserungen nur dokumentieren; eine Aktivierung braucht spaeter ein separates Goal, Tests, bounded inputs und llm_audit_log. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken, kein Rohdatenzugriff und keine Trading-Pfade. |

## Use Rule

Nach dem Dozentenfeedback zuerst das Feedback-Log ausfuellen. Danach die Manual Source Review Follow-up Overview pruefen und Source Review manuell je H1-H2-H3-Zeile ausfuehren: Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen. Erst danach bounded Draft und wenige gute Tabellen/Figuren aktualisieren. Finale Zitation, Quellenstatus-Hochstufung, finale Abgabebereitschaft, Review-Access, Runtime-Agenten, MCP, Model Routing, LLM-Metriken, Rohartefakt-Dumps und Trading-Pfade bleiben blockiert, bis die jeweiligen Gates belegt geschlossen sind.
