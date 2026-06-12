# Thesis Consolidation Index

Dieser Index zeigt, welche Artefakte fuer den aktuellen Highlevel-Projektstand, den Dozentenbericht, Source Review, Wording Guard, Tabellen/Figuren und Future-Work-Agenten relevant sind.

## Counts

- Indexed artifacts: 12

## Artifact Index

| artifact_id | artifact_type | path | purpose_de | use_now_de | gate_or_limit_de |
| --- | --- | --- | --- | --- | --- |
| index_01_advisor_report_docx | advisor_deliverable | docs/project/dozentenbericht_ba_thesis.docx | Schriftlicher Zwischenstand fuer den Dozenten. | Direkt als Word-Update geben. | DOCX-Render-QA lokal nur moeglich, wenn LibreOffice/soffice verfuegbar ist. |
| index_02_advisor_report_md | advisor_review_source | docs/project/dozentenbericht_ba_thesis.md | Transparente Markdown-Quelle des Dozentenberichts. | Inhalt schnell pruefen oder nach Word uebertragen. | Keine neuen Claims ohne Update der deterministischen Artefakte. |
| index_03_advisor_questions | advisor_alignment | docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md | Acht konkrete Fragen fuer die naechste Dozentenabstimmung. | Als Gespraechsagenda nutzen. | Dient Scope-Klaerung, nicht Empirie-Erweiterung. |
| index_04_highlevel_view | project_status | docs/research/THESIS_PROJECT_HIGHLEVEL_VIEW.md | Statusmatrix ueber Projektteile, Entscheidungen und Gates. | Highlevel-Orientierung fuer Projektfortschritt. | Review-Access bleibt pausiert; Agenten bleiben documentation-only. |
| index_05_next_work_plan | work_plan | docs/research/THESIS_NEXT_WORK_PLAN.md | Priorisierte Workstreams von Source Review bis finaler QA. | Naechste Arbeitsschritte sequenzieren. | Kein Scope-Ausbau vor geschriebenem H1-H3-Kern. |
| index_06_source_worksheet | source_review | docs/research/THESIS_SOURCE_REVIEW_WORKSHEET.md | Manuelle Quellenreview-Zeilen mit Evidence IDs und Pending-Feldern. | Quellen mit Seiten-/Abschnittsnotizen pruefen. | Quellenstatus nicht automatisch hochstufen. |
| index_07_wording_guard | drafting_guard | docs/research/THESIS_WORDING_GUARD.md | Erlaubtes und blockiertes deutsches Thesis-Wording je Evidence ID. | Beim Schreiben der Kapitel als Claim-Grenze nutzen. | Keine Formulierung ohne Artefakt und Limitation uebernehmen. |
| index_08_table_figure_captions | result_package | docs/research/THESIS_TABLE_FIGURE_CAPTIONS.md | Beschriftungen, Quellen- und Limitationstexte fuer Tabellen/Figuren. | 5 Kern-Tabellen und 4 Kern-Figuren in die Thesis einbauen. | Keine Rohartefakt-Dumps in den Haupttext. |
| index_09_chapter_draft | chapter_draft | docs/research/THESIS_CHAPTER_DRAFT.md | Erster deutschsprachiger Kapitelentwurf aus der Konsolidierung. | Als Rohfassung fuer BA-Kapitel nutzen. | Vor finaler Abgabe Quellenreview und Wording Guard anwenden. |
| index_10_source_review_plan | source_review | docs/research/THESIS_SOURCE_REVIEW_PLAN.md | Priorisierte Quellenreview-Planung nach Quelle. | Quelle-fuer-Quelle abarbeiten. | Candidate/rejected Quellen nicht fuer thesis-facing Claims nutzen. |
| index_11_agent_protocol | future_work | docs/research/THESIS_AGENT_ASSISTANCE_PROTOCOL.md | Dokumentations-only Agenten-Ausblick mit erlaubten Rollen und Gates. | Nur als Future-Work-Abschnitt nutzen. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade. |
| index_12_status_and_log | project_control | STATUS.md; docs/project/WORK_LOG.md | Automatisierter Projektstatus und append-only Arbeitslog. | Vor jedem Stop und Commit pruefen. | Nicht behaupten, dass Phase bereit ist, wenn Checks fehlschlagen. |

## Use Rule

Nutze zuerst den Dozentenbericht und die Absprache-Checklist fuer die Betreuung. Nutze danach Source Worksheet, Wording Guard und Next Work Plan fuer das Schreiben. Review-Access, Runtime-Agenten, MCP, Model Routing, Rohdatenzugriff und Trading-Pfade bleiben deaktiviert.
