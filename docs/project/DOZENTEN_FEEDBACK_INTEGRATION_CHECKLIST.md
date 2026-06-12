# Dozenten-Feedback-Integration-Checklist

Diese Checkliste sagt, wie spaeteres Dozentenfeedback in kleine, pruefbare Folgecommits uebersetzt wird. Sie ist pending, bis der Dozent geantwortet hat, und erzeugt keine neuen empirischen Resultate.

## Counts

- Integration rows: 8
- Feedback status: pending_advisor_feedback
- Active runtime agents: 0

## Integration Rows

| integration_id | advisor_question_id | topic | feedback_status | required_evidence_check_de | small_commit_scope_de | final_gate_de | guardrail_de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| integration_01_advisor_q01_h1_wording | advisor_q01_h1_wording | H1 bounded wording | pending_advisor_feedback | Vor Textaenderung pruefen, dass method_h1_brier_dm und die H1-Interpretationen deterministische Artefakte, Literatur-IDs, Limitationen und Source Review Gates tragen. | docs: integrate advisor h1 wording feedback | Finale H1-Zitation erst nach Source Review und Wording-Guard-Abgleich. | Keine universelle Polymarket-Ueberlegenheit, keine RCP-Wahrscheinlichkeitsbehauptung und keine neuen Metriken. |
| integration_02_advisor_q02_source_depth | advisor_q02_source_depth | Source review depth | pending_advisor_feedback | Jede Methode und jede Interpretation braucht vor finaler Nutzung eine reviewte Quelle oder ein deterministisches Artefakt plus Page-/Section-Note im Source Review Ledger. | docs: integrate advisor source review depth feedback | Keine Quellenstatus-Hochstufung ohne manuelle Claim-Support-Entscheidung. | Quellenstatus nicht automatisch hochstufen; candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen. |
| integration_03_advisor_q03_h2_h3_scope | advisor_q03_h2_h3_scope | H2/H3 scope | pending_advisor_feedback | H2/H3-Methoden und Interpretationen muessen auf deterministische Artefakte, Literatur-IDs, Limitationen und blockiertes Wording verweisen. | docs: integrate advisor h2 h3 scope feedback | Finale H2/H3-Aussagen erst nach Source Review und Limitationscheck. | Keine Intraday-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims. |
| integration_04_advisor_q04_table_figure_package | advisor_q04_table_figure_package | Tables and figures | pending_advisor_feedback | Nur wenige gute Tabellen/Figuren verwenden: jede Tabelle/Figur braucht Caption, deterministisches Artefakt, Interpretation, Limitation und Source-Review-Bezug. | docs: integrate advisor table figure feedback | Finale Nummerierung und Platzierung erst im Thesis-Layout. | Keine Rohartefakt-Dumps und keine neuen Tabellen/Figuren ohne Evidence-Map- und Kapitelplan-Update. |
| integration_05_advisor_q05_monitor_appendix | advisor_q05_monitor_appendix | Monitor appendix | pending_advisor_feedback | Monitor-Inhalte nur als Prototyp verwenden und keine thesis-facing Interpretation ohne Human Review, Source Check und bounded Summary. | docs: integrate advisor monitor appendix feedback | Monitor bleibt appendix-only, bis Human Review und Thesis-Use-Gate abgeschlossen sind. | Review-Access bleibt pausiert; keine Wallet-Adress-Exposition, keine Order- oder Trading-Pfade und keine Kausalclaims. |
| integration_06_advisor_q06_swiss_gate | advisor_q06_swiss_gate | Swiss result gate | pending_advisor_feedback | Swiss bleibt bis zum offiziellen Resultat beschreibend; nach Resultat nur deterministisch generierte Artefakte und klare Poll-Proxy-Limitationen nutzen. | docs: integrate advisor swiss placement feedback | Keine finale Swiss-Effizienzinterpretation vor offizieller Resultatzuordnung. | Poll-Anteile sind keine Gewinnwahrscheinlichkeiten; keine finale Accuracy- oder Effizienzbehauptung vor Resultat. |
| integration_07_advisor_q07_agent_outlook | advisor_q07_agent_outlook | Agent outlook | pending_advisor_feedback | Agenten duerfen nur documentation-only bleiben: spaetere Nutzung braucht separate Freigabe, bounded inputs, Tests, max 50 rows und llm_audit_log. | docs: integrate advisor agent outlook feedback | 0 aktive Runtime-Agenten, bis ein separates spaeteres Goal alle Gates erfuellt. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade. |
| integration_08_advisor_q08_final_qa | advisor_q08_final_qa | Final QA | pending_advisor_feedback | Vor jedem Completion-Claim Tests, Review-Checks, Source Review, Swiss-Spelling, DOCX-Render-QA und offene Finalgates nachweisen. | docs: integrate advisor final qa feedback | Kein Zielabschluss, solange Source Review, Swiss official result oder DOCX-Render-QA offen sind. | Keine finale Aussage darf ueber deterministische Artefakte und reviewte Quellen hinausgehen. |

## Use Rule

Nach der Betreuung zuerst die passende Feedback-Zeile im `DOZENTEN_FEEDBACK_LOG.md` ausfuellen. Danach genau eine passende Integration-Zeile aus dieser Checkliste waehlen und als kleinen Commit-Scope bearbeiten. Jede Methode und jede Interpretation muss weiterhin eine reviewte Quelle oder ein deterministisches Artefakt, eine Limitation und ein Source Review Gate haben. Das Resultatpaket bleibt bei wenigen guten Tabellen/Figuren; Rohartefakt-Dumps, Review-Access, Runtime-Agenten, MCP, Model Routing, LLM-Metriken und Trading-Pfade bleiben deaktiviert.
