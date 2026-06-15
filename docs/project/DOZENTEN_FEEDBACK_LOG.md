# Dozenten-Feedback-Log

Dieses Log ist eine Vorlage fuer die naechste Betreuung. Alle Entscheidungen bleiben pending, bis der Dozent Feedback gegeben hat. Es erzeugt keine neuen empirischen Resultate.

## Counts

- Feedback rows: 8
- Current status: pending_advisor_feedback

## Feedback Rows

| feedback_id | topic | advisor_question_de | advisor_feedback_status | advisor_feedback_de | resulting_action_de | guardrail_de |
| --- | --- | --- | --- | --- | --- | --- |
| feedback_01_advisor_q01_h1_wording | H1 bounded wording | Ist die H1-Formulierung als begrenzte Polymarket-Stuetze in definierten Poll-Vergleichsscopes akzeptabel? | pending_advisor_feedback | pending | pending | Keine universelle Polymarket-Ueberlegenheit und keine RCP-Wahrscheinlichkeitsbehauptung. |
| feedback_02_advisor_q02_source_depth | Source review depth | Reicht fuer die Abgabe ein Full Review der Priority-1-Methodenquellen plus Seiten-/Abschnittsnotizen? | pending_advisor_feedback | pending | pending | Quellenstatus nicht automatisch hochstufen; candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen. |
| feedback_03_advisor_q03_h2_h3_scope | H2/H3 scope | Soll H2/H3 als Tagesfenster- und Timingdiagnostik genuegen, ohne Intraday- und Kausalclaims? | pending_advisor_feedback | pending | pending | Keine Intraday-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims. |
| feedback_04_advisor_q04_table_figure_package | Tables and figures | Sind 5 Kern-Tabellen und 4 Kern-Figuren als kompakte Ergebnisdarstellung sinnvoll? | pending_advisor_feedback | pending | pending | Keine neuen Rohartefakte in den Haupttext ohne Evidence-Map- und Kapitelplan-Update. |
| feedback_05_advisor_q05_monitor_appendix | Monitor appendix | Soll der Monitor nur als Appendix-/Workflow-Prototyp gezeigt werden? | pending_advisor_feedback | pending | pending | Keine Wallet-Adress-Exposition, keine Order- oder Trading-Pfade, keine Kausal- oder Ineffizienzclaims. |
| feedback_06_advisor_q06_swiss_gate | Swiss final case | Wie soll der Swiss-Referendum-Track als Post-Resultat-Fallstudie platziert werden? | pending_advisor_feedback | pending | pending | Poll-Anteile sind keine Gewinnwahrscheinlichkeiten; keine Effizienz-, Mispricing- oder Stimmenanteilsueberlegenheitsbehauptung. |
| feedback_07_advisor_q07_agent_outlook | Agent outlook | Soll die Agenten-Pipeline nur als Future-Work-Ausblick bleiben? | pending_advisor_feedback | pending | pending | Vor jeder spaeteren Aktivierung: separates Goal, bounded prompts, Tests und llm_audit_log. |
| feedback_08_advisor_q08_final_qa | Final QA | Welche finale QA erwartet der Dozent vor Abgabe oder naechstem Entwurf? | pending_advisor_feedback | pending | pending | Keine finale Aussage darf ueber deterministische Artefakte und reviewte Quellen hinausgehen. |

## Use Rule

Nach dem Gespraech jede Antwort in `advisor_feedback_de` eintragen, daraus eine kleine Folgeaktion ableiten und nur passende kleine Commits planen. Review-Access, Runtime-Agenten, MCP, Model Routing, LLM-Metriken und Trading-Pfade bleiben deaktiviert, solange kein separates Goal sie ausdruecklich erlaubt.
