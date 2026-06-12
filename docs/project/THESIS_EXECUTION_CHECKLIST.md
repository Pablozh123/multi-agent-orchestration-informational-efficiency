# Thesis Execution Checklist

Diese Checkliste uebersetzt die Highlevel-View in konkrete Schreib- und Abnahmeaufgaben. Sie ist ein Projektsteuerungsartefakt und erzeugt keine neuen empirischen Resultate.

## Counts

- Execution tasks: 8
- First task: exec_01_01_intro
- Final task: exec_08_08_discussion_conclusion

## Execution Tasks

| task_id | chapter_title | execution_phase | table_figure_items | source_gate_de | draft_action_de | done_when_de | advisor_question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exec_01_01_intro | Einleitung und Forschungsfrage | draft_frame | T1 (tab:t1) | Als Entwurf schreiben; finale Einordnung erst nach Quellenreview. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | Forschungsfrage, Scope Polymarket/US-Wahl und Proxy-Logik knapp formulieren. | Forschungsfrage, H1-H3-Logik und Nicht-Ziele sind sichtbar. | advisor_q01_h1_wording; advisor_q08_final_qa |
| exec_02_02_theory_literature | Theorie und Literatur | source_review_first | T1 (tab:t1) | Priority-1-Methodenquellen mit Seiten- oder Abschnittsnotizen reviewen. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | EMH, Prognosemaerkte, Event-Study und Wallet-Vorsicht quellengebunden ausarbeiten. | Jede Theorie- und Methodenbehauptung hat eine reviewte Quelle oder bleibt Draft. | advisor_q02_source_depth |
| exec_03_03_data_method | Daten und Methodik | method_draft | T1 (tab:t1) | Methodenquellen pruefen; RCP-Transformation, Event-Kuration und Wallet-Tiers explizit abgrenzen. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | Datenpipeline, Artefakthierarchie und Python-only-Metrikregel als Methodik schreiben. | Alle Methoden verweisen auf deterministische Artefakte und passende Quellenanker. | advisor_q02_source_depth; advisor_q03_h2_h3_scope |
| exec_04_04_h1_results | H1: Prognosequalitaet | result_draft | T2 (tab:t2); F1 (fig:f1) | Draft ist moeglich; finale H1-Zitation wartet auf Source Review. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | H1 als begrenzte Polymarket-Stuetze plus klare Grenze der breiten Behauptung schreiben. | Bounded H1-Claim, Gegenbeispiel und Limitation stehen direkt nebeneinander. | advisor_q01_h1_wording; advisor_q04_table_figure_package |
| exec_05_05_h2_results | H2: Ereignisfenster | result_draft | T3 (tab:t3); F2 (fig:f2) | Draft ist moeglich; Event-Study-Quelle und Event-Kuration vor finaler Fassung pruefen. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | H2 als Tagesfensterdiagnostik schreiben und Intraday-Speed ausschliessen. | Ereignisse, Tagesfenster und Tagesfrequenz-Limitation sind transparent. | advisor_q03_h2_h3_scope; advisor_q04_table_figure_package |
| exec_06_06_h3_results | H3: Wallet-Timing | result_draft | T4 (tab:t4); F3 (fig:f3) | Draft ist moeglich; Granger- und Wallet-Literatur vor finaler Interpretation pruefen. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | H3 als dataset-relative Timingdiagnostik schreiben, nicht als Kausal- oder Private-Information-Claim. | BUY-only, Tagesaggregation, Mehrfachtests und Nicht-Profitabilitaet sind genannt. | advisor_q03_h2_h3_scope; advisor_q04_table_figure_package |
| exec_07_07_extensions | Erweiterungen: Monitor und Schweizer Abstimmung | appendix_or_discussion_gate | T5 (tab:t5); F4 (fig:f4) | Monitor bleibt Review-pending; Swiss bleibt bis zum offiziellen Resultat vom 14. Juni 2026 beschreibend. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | Monitor als Prototyp und Swiss als Side-Track knapp platzieren. | Review-Access bleibt pausiert und Swiss traegt keine finale Effizienzaussage. | advisor_q05_monitor_appendix; advisor_q06_swiss_gate |
| exec_08_08_discussion_conclusion | Diskussion, Limitationen und Fazit | synthesis_after_core | none | Erst nach H1-H3-Draft, Quellenreview und Swiss-/Appendix-Gates finalisieren. Aktueller Quellen-Gate: 11 Priority-1-Quellen und 11 Quellen mit Full-Review-Bedarf; 1 Quelle bleibt blocked/future-only. | Fazit als begrenzte Evidenz fuer H1-H3 schreiben und Agenten nur als Future Work fuehren. | Keine finale Aussage geht ueber deterministische Artefakte und reviewte Quellen hinaus. | advisor_q07_agent_outlook; advisor_q08_final_qa |

## Use Rule

Nutze diese Checkliste zum Schreiben der BA-Kapitel nach der Dozentenabstimmung. Review-Access bleibt pausiert. Runtime-Agenten, MCP, Model Routing, Rohartefakt-Dumps, Trading-Pfade und LLM-Metrikberechnung bleiben ausserhalb des aktiven Thesis-Kerns.
