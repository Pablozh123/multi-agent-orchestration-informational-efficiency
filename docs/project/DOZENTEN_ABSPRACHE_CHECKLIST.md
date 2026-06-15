# Dozenten-Absprache-Checklist

Diese Checkliste uebersetzt den Highlevel-Projektstand in konkrete Fragen fuer die naechste Abstimmung mit dem Dozenten. Sie ist ein Projektmanagement-Artefakt und erzeugt keine neuen empirischen Resultate.

## Counts

- Advisor questions: 8

## Empfohlene Gespraechsreihenfolge

1. Erst H1-H2-H3 Scope bestaetigen: bounded H1, H2 Tagesfenster, H3 Timingdiagnostik.
2. Danach Source Review Tiefe festlegen: Priority-1-Quellen und Seiten-/Abschnittsnotizen.
3. Dann Tabellen/Figuren und Kapitelintegration entscheiden.
4. Monitor und Swiss nur als Appendix, Diskussion oder Side-Track abgrenzen; Review-Access bleibt pausiert.
5. Agenten nur als Future Work bestaetigen und finale QA-Gates festlegen.

## Questions

| question_id | topic | advisor_question_de | current_project_position_de | decision_needed_de | guardrail |
| --- | --- | --- | --- | --- | --- |
| advisor_q01_h1_wording | H1 bounded wording | Ist die H1-Formulierung als begrenzte Polymarket-Stuetze in definierten Poll-Vergleichsscopes akzeptabel? | 8 Wording-Guard-Zeilen sind fuer Thesis-Text nach Source Review vorgesehen; H1 bleibt bounded, nicht universal. | Bestaetigen, ob H1 als bounded result chapter geschrieben werden soll. | Keine universelle Polymarket-Ueberlegenheit und keine RCP-Wahrscheinlichkeitsbehauptung. |
| advisor_q02_source_depth | Source review depth | Reicht fuer die Abgabe ein Full Review der Priority-1-Methodenquellen plus Seiten-/Abschnittsnotizen? | Worksheet: 15 Quellenreview-Zeilen, 11 Priority-1, 1 blocked/future-only, 15 pending reviewer decisions. | Festlegen, welche Quellen vor finaler Zitation voll reviewt werden muessen. | Quellenstatus nicht automatisch hochstufen; candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen. |
| advisor_q03_h2_h3_scope | H2/H3 scope | Soll H2/H3 als Tagesfenster- und Timingdiagnostik genuegen, ohne Intraday- und Kausalclaims? | H2 nutzt kuratierte Tagesfenster; H3 nutzt dataset-relative Wallet-Tiers und Granger nur diagnostisch. | Absegnen, dass Intraday-Speed, Kausalitaet und Profitabilitaet ausserhalb des aktuellen Scopes bleiben. | Keine Intraday-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims. |
| advisor_q04_table_figure_package | Tables and figures | Sind 5 Kern-Tabellen und 4 Kern-Figuren als kompakte Ergebnisdarstellung sinnvoll? | Das Thesis-Paket priorisiert wenige beschriftete Tabellen/Figuren statt Rohartefakt-Dumps. | Bestaetigen, ob diese Auswahl in den Haupttext darf und was in den Appendix geht. | Keine neuen Rohartefakte in den Haupttext ohne Evidence-Map- und Kapitelplan-Update. |
| advisor_q05_monitor_appendix | Monitor appendix | Soll der Monitor nur als Appendix-/Workflow-Prototyp gezeigt werden? | Review-Access bleibt pausiert; Monitor-Faelle sind source-check-pending und nicht thesis-facing. | Klaeren, ob ein kurzer Appendix reicht oder der Monitor im Haupttext nur erwaehnt wird. | Keine Wallet-Adress-Exposition, keine Order- oder Trading-Pfade, keine Kausal- oder Ineffizienzclaims. |
| advisor_q06_swiss_gate | Swiss final case | Wie soll der Swiss-Referendum-Track als Post-Resultat-Fallstudie platziert werden? | Swiss ist mit offiziellem Resultat gemappt und bleibt bounded Side-Track ohne Effizienz- oder Tradeability-Claim. | Entscheiden, ob Swiss in Diskussion, Appendix oder als aktuelles Side-Example steht. | Poll-Anteile sind keine Gewinnwahrscheinlichkeiten; keine Effizienz-, Mispricing- oder Stimmenanteilsueberlegenheitsbehauptung. |
| advisor_q07_agent_outlook | Agent outlook | Soll die Agenten-Pipeline nur als Future-Work-Ausblick bleiben? | Agenten sind documentation-only; keine Runtime-Agenten, kein MCP, kein Model Routing. | Bestaetigen, dass Agenten nicht Teil des empirischen Kerns oder der Abgabe-Pipeline werden. | Vor jeder spaeteren Aktivierung: separates Goal, bounded prompts, Tests und llm_audit_log. |
| advisor_q08_final_qa | Final QA | Welche finale QA erwartet der Dozent vor Abgabe oder naechstem Entwurf? | Workplan endet mit Tests, Review-Checks, Citation Checks, Tabellen/Figuren und Swiss-Spelling. | Abklaeren, welche Checks der Dozent sehen moechte und welche Artefakte genuegen. | Keine finale Aussage darf ueber deterministische Artefakte und reviewte Quellen hinausgehen. |

## Use Rule

Die Fragen sollen Scope und Wording klaeren. Sie duerfen nicht genutzt werden, um Review-Access, Agenten, MCP, Model Routing, Rohdatenzugriff oder Trading-Pfade zu aktivieren.
