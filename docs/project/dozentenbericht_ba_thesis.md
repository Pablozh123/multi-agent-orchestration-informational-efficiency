# Dozentenbericht zur Bachelorarbeit

Erstellt: 2026-06-12T22:59:12+00:00

**Arbeitstitel:** Informationelle Effizienz dezentraler Prognosemaerkte am Beispiel Polymarket im Vergleich zu traditionellen Prognosequellen.

## Kurzfazit

Das Projekt hat eine deterministische Analysegrundlage aufgebaut. Statistische Kennzahlen werden in Python berechnet; LLMs oder Agenten interpretieren keine Rohdaten und berechnen keine Metriken.

- H1 ist ein Forecast-Qualitaetsvergleich.
- H2 ist eine taegliche Event-Window-Analyse.
- H3 ist eine Wallet-Tier-Timing-Diagnostik.
- Der Monitor ist ein read-only Forschungsprototyp mit deterministischer Anomaly-Review-Queue.
- Der Schweizer 10-Millionen-Referendumsvergleich laeuft als separater Datensammlungs-Track.

## Aufbau wie in der Bachelorarbeit

Dieser Dozentenbericht ist als Zwischenstand im Stil einer Bachelorarbeit aufgebaut:

- Einleitung und Forschungsfrage: Warum Prediction Markets als Informationsmaerkte relevant sind.
- Theorie und Literatur: Effizienz, Prediction Markets, Polling-Vergleiche, Wallet- und Mikrostrukturgrenzen.
- Methodik: deterministische Python-Pipeline, validierte Artefakte, keine LLM-Metriken.
- Empirie: H1 Forecast-Qualitaet, H2 Event-Window-Reaktion, H3 Wallet-Tier-Timing.
- Erweiterung: read-only Monitor und Schweizer Referendumsvergleich als laufender Track.
- Diskussion: Grenzen, belastbare Formulierungen und naechste Arbeitsschritte.

## Highlevel-Projektstand

Der Review-Access bleibt pausiert. Der aktuelle Fortschritt liegt in der Thesis-Konsolidierung: Methoden, Interpretationen, Quellen, Tabellen und Figuren sind auf deterministische Artefakte gemappt.

- Aktive Phase: Phase 12: Thesis Consolidation And Evidence Mapping.
- Thesis-Paket: 5 Kern-Tabellen und 4 Kern-Figuren; insgesamt 10 Caption-Zeilen.
- Evidenzkarte: 13 Evidence-Zeilen; 6 zentrale Resultatzeilen; 8 Kapitelplan-Zeilen.
- Citation-Gate: 33 Review-Pakete, davon 32 mit Full-Source-Review vor finaler Zitation.
- Agenten bleiben nur dokumentierter Ausblick; keine Runtime-Agenten, kein MCP, keine Modell-Router.

| Ebene | Stand | Konsequenz fuer die Thesis |
| --- | --- | --- |
| Empirischer Kern | H1 Forecast-Qualitaet, H2 Event-Windows und H3 Wallet-Timing sind die zentrale Ergebnisbasis. | Die Bachelorarbeit sollte diese drei Strukturen zuerst schreiben und erst danach Monitor, Swiss und Agenten einordnen. |
| Tabellen und Figuren | 5 Kern-Tabellen und 4 Kern-Figuren sind ueber `thesis_table_figure_captions.csv` beschriftet. | Der Dozent bekommt eine fokussierte Ergebnisdarstellung statt einer Rohartefakt-Sammlung. |
| Quellen und Zitation | Die Citation-Review-Pakete verknuepfen Quellen mit Evidence-IDs, erlaubtem Wording und Review-Gates. | Finale Thesis-Zitate brauchen noch Seiten- oder Abschnittsnachweise; candidate Quellen bleiben blockiert. |
| Monitor und Swiss | Monitor bleibt Prototype/Appendix; Swiss bleibt bis zum offiziellen Ergebnis beschreibender Side-Track. | Beide Teile duerfen die H1-H3-Kernaussage nicht staerker machen als die deterministischen Artefakte erlauben. |
| Agenten-Ausblick | Agenten koennen spaeter bei Source Review, Drafting und Guardrail-Checks helfen, bleiben aber jetzt deaktiviert. | Keine Runtime-Agenten, kein MCP, keine Modell-Router und keine LLM-Metriken vor stabilem deterministic core. |

## Dozentenpaket und Uebergabereihenfolge

Das Advisor-Handoff-Paket ordnet 12 Dateien fuer die naechste Betreuung. Zuerst kommt der `advisor_handoff_note`, danach folgen Word-Bericht, Absprache-Checklist, Submission Readiness Board, Drafting Sequence, Feedback-Log und die Arbeitsdateien fuer Kapitel und Source Review.

| Reihenfolge | Datei | Verwendung | Entscheidung | Grenze |
| --- | --- | --- | --- | --- |
| 1 | `docs/project/DOZENTEN_UEBERGABE_TEXT.md` | Als kurze Mail- oder Chat-Vorlage fuer die Uebergabe nutzen. | Keine Entscheidung; eroeffnet die Betreuung mit klarer Datei- und Fragenordnung. | Zwischenstand, kein finales Abgabe- oder Quellenreview-Signal. |
| 2 | `docs/project/dozentenbericht_ba_thesis.docx` | Als schriftliches Word-Update mit Source-Gated H1-H2-H3 Drafting Sequence an den Dozenten geben: 15 Absatzschritte, 23 Manual Source Review Zeilen verlinkt. | Projektstand, Aufbau, H1-H3-Kern, Source-Review-Gates, Grenzen und naechste Schritte abstimmen. | Source-Gated Sequence bleibt bounded-draft-ready und nicht final-submission-ready (0 final-ready Source-Review-Zeilen); DOCX-Render-QA bleibt lokal blockiert, wenn LibreOffice/soffice fehlt. |
| 3 | `docs/project/DOZENTEN_ABSPRACHE_CHECKLIST.md` | Als Gespraechsagenda fuer die naechste Betreuung nutzen. | H1-Wording, Source-Review-Tiefe, H2/H3-Scope, Swiss und Appendix-Scope klaeren. | Fragen klaeren Scope; sie aktivieren keine Empirie-Erweiterung. |
| 4 | `docs/project/THESIS_SUBMISSION_READINESS_BOARD.md` | Als Gate-Uebersicht fuer draft-ready, final-blocked und deferred Schritte nutzen. | Klaeren, welche finalen Gates vor Abgabe zwingend geloest werden muessen. | Source Review, Swiss-Gate und DOCX-Render-QA bleiben final blockiert. |
| 5 | `docs/project/THESIS_DRAFTING_SEQUENCE.md` | Als naechste Schreibreihenfolge fuer den BA-Entwurf nutzen. | Bestaetigen, ob diese Reihenfolge fuer den naechsten Entwurf sinnvoll ist. | Trennt bounded Draft-Arbeit von finalen Blockern und Future Work. |
| 6 | `docs/project/THESIS_EXECUTION_CHECKLIST.md` | Nach Feedback als Kapitel- und Abnahme-Checkliste nutzen. | Reihenfolge und Done-Kriterien fuer die BA-Kapitel bestaetigen. | Review-Access bleibt pausiert; keine Runtime-Agenten oder Rohartefakt-Dumps. |
| 7 | `docs/project/THESIS_CHAPTER_SOURCE_BINDINGS.md` | Beim Schreiben je Kapitel Quellen, Artefakte und Gates pruefen. | Klaeren, ob diese Kapitel-zu-Quelle-Bindung fuer die Abgabe reicht. | Keine thesis-facing Claims ohne Human Review, Artefaktverweis, Limitation und Wording Guard. |
| 8 | `docs/project/THESIS_SOURCE_REVIEW_EXECUTION.md` | Als manuelle Reihenfolge fuer die Quellenpruefung nutzen. | Prioritaet der 11 Priority-1-Quellen und blocked/future-only Quellen bestaetigen. | Quellenstatus nicht automatisch hochstufen. |
| 9 | `docs/project/THESIS_MANUAL_SOURCE_REVIEW_FOLLOWUP_OVERVIEW.md` | Als kompakte H1-H2-H3 Source-Review-Steuerung nutzen: 23 offene Review-Zeilen, 3 Slices, 23 pending, 0 final-ready. | Klaeren, ob H1, H2 und H3 in dieser Reihenfolge source-by-source reviewed werden sollen. | Alle Zitationen bleiben final blockiert; keine Quellenstatus-Hochstufung, keine Kausalclaims, keine Runtime-Agenten und keine Rohartefakt-Dumps. |
| 10 | `docs/project/THESIS_AGENT_FUTURE_WORK_HANDOFF.md` | Nur als Future-Work-Ausblick fuer spaetere Pipeline-Verbesserungen nutzen. | Bestaetigen, dass Agenten nicht Teil des empirischen Kerns werden. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade. |
| 11 | `docs/project/DOZENTEN_FEEDBACK_LOG.md` | Nach der Betreuung Feedback und Folgeaktionen eintragen. | Keine Entscheidung im Voraus; dient als pending Feedback-Log. | Alle Eintraege bleiben pending, bis der Dozent Feedback gegeben hat. |
| 12 | `docs/project/THESIS_CONSOLIDATION_INDEX.md` | Als Navigationsindex fuer alle aktuellen Projektartefakte nutzen. | Keine Entscheidung; dient Orientierung und Nachvollziehbarkeit. | Nicht als neues empirisches Resultat verwenden. |

## Projektmatrix fuer die naechste Abstimmung

Die Projektmatrix fasst 10 Ebenen als Status-, Entscheidungs- und Gate-Sicht zusammen. Sie zeigt explizit, dass Review-Access pausiert bleibt und Agenten nur dokumentierter Ausblick sind.

| Projektteil | Status | Entscheidung | Naechstes Gate |
| --- | --- | --- | --- |
| Gesamtrahmen | Aktiver Thesis-Kern | H1-H3 als Kern schreiben; Decision Queues 10/5/8 mit 0 final-ready rows abarbeiten. | Decision Queues, Source Review und Kapiteldraft. |
| H1 Forecast-Qualitaet | Thesis-ready | H1 als begrenzte Polymarket-Stuetze schreiben; H1 Queue: 10 rows, T2/F1, 0 final-ready. | H1 Queue-Felder vor finalem Wording fuellen. |
| H2 Event-Windows | Thesis-ready | H2 als taegliche Event-Window-Evidenz schreiben; H2 Queue: 5 rows, T3/F2, Kausalclaim-Grenze. | H2 Queue-Felder inklusive Kausalclaim-Grenze fuellen. |
| H3 Wallet-Timing | Thesis-ready mit Grenzen | H3 als Timingdiagnostik schreiben; H3 Queue: 8 rows, T4/F3, Granger-/Wallet-Grenze. | H3 Queue-Felder inklusive Granger-/Wallet-Grenze fuellen. |
| Quellen und Zitation | Aktives Gate | H1/H2/H3 Decision Queues bilden den 23-row Manual Source Review Pfad; Status wird nicht automatisch hochgestuft. | Page-/Section-Notes, Claim-Support, Blocked-Wording und Citation-Use eintragen. |
| Tabellen/Figuren-Paket | Thesis-Paket | 5 Kern-Tabellen und 4 Kern-Figuren mit Captions verwenden. | In Thesis-Layout integrieren; Nummerierung spaeter finalisieren. |
| Monitor Review-Access | Pausiert / Appendix | Review-Access bleibt pausiert; Monitor bleibt Appendix/Prototype. | Nur mit Human Review oder separatem freigegebenem Goal fortsetzen. |
| Swiss Referendum | Beschreibend bis Resultat | Bis zum offiziellen Ergebnis nur beschreibend verwenden. | Nach offiziellem 14. Juni 2026 Resultat Artefakte neu generieren. |
| Agenten-Ausblick | Nur Ausblick | Agenten bleiben Dokumentationsausblick, keine Runtime-Implementierung. | Separates Goal, Tests und llm_audit_log vor Aktivierung. |
| Dozentenabstimmung | Advisor-Abstimmung | Dozent soll H1-Wording, Quellenreview-Tiefe, Swiss und Appendix-Scope absegnen. | Feedback loggen und in kleinen Commit-Plan uebersetzen. |

## Submission Readiness und finale Gates

Das Submission Readiness Board trennt 9 Gates in Draft-Arbeit, finale Blocker und Future Work. Draft-ready Gates: 4; final blockierte Gates: 2. Source Review steht auf `final_blocked_source_review`, Swiss steht auf `final_blocked_official_result`, Agenten stehen auf `deferred_future_work_only`.

| Gate | Status | Naechste Aktion | Grenze | Thesis-Nutzung |
| --- | --- | --- | --- | --- |
| advisor_handoff | ready_for_advisor_discussion | Dozentenbericht und Absprache-Checklist zuerst verwenden. | DOCX-Render-QA bleibt lokal blockiert, wenn LibreOffice/soffice fehlt. | Projektstand schriftlich uebergeben und Scope-Feedback einholen. |
| chapter_source_mapping | ready_for_draft | Kapitel entlang Evidence IDs, Quellen, Tabellen/Figuren und Gates schreiben. | Finale Claims erst nach Human Review, Artefaktverweis, Limitation und Wording Guard. | Schreibstruktur fuer alle BA-Kapitel. |
| source_review | final_blocked_source_review | Priority-1-Quellen mit Seiten- oder Abschnittsnotizen reviewen. | 11 Priority-1-Quellen und 1 blocked/future-only Quelle bleiben Gate. | Draft-Struktur ja; finale Zitation erst nach Human Review. |
| h1_h2_h3_results | ready_for_bounded_result_draft | H1 bounded, H2 daily event-window, H3 timing diagnostics schreiben. | Keine universelle Effizienz-, Intraday-, Kausalitaets- oder Profitabilitaetsclaims. | Empirischer Kern der BA-Arbeit. |
| table_figure_package | ready_for_draft_integration | 5 Kern-Tabellen und 4 Kern-Figuren mit Captions integrieren. | Keine Rohartefakt-Dumps in den Haupttext aufnehmen. | Kompakte Ergebnisdarstellung. |
| monitor_appendix | appendix_only_pending_human_review | Monitor nur als read-only Prototyp und Review-Workflow erwaehnen. | Keine Wallet-Adress-Exposition, keine Order-/Trading-Pfade, keine Kausalclaims. | Appendix oder Diskussion, nicht empirischer Kern. |
| swiss_result_gate | final_blocked_official_result | Bis zum offiziellen 14. Juni 2026 Resultat beschreibend bleiben. | Poll-Anteile sind keine Gewinnwahrscheinlichkeiten und tragen keine finale Effizienzaussage. | Diskussion oder Side-Track nach Resultat-Gate. |
| agent_future_work | deferred_future_work_only | Nur als Future-Work-Ausblick verwenden. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade. | Ausblick auf spaetere Pipeline-Verbesserung. |
| final_qa | pending_after_draft | Nach Draft: Tests, review_check, citation review, spelling scan und DOCX render gate wiederholen. | Repository nicht als final abgabebereit markieren, solange Source Review oder Render-QA offen sind. | Abgabe-Checkliste nach fertigem Entwurf. |

## Schreibsequenz fuer den naechsten Entwurf

Die Drafting Sequence ordnet 10 Schritte vom Quellenreview bis zur finalen QA. Erste Sequenz ist `draft_01_01_source_review`, letzte Sequenz ist `draft_10_10_final_qa`. Bounded write-now: 4; final blockiert: 2; Future-work-only: 1.

| Prioritaet | Thesis-Abschnitt | Erlaubnis | Schreibaktion | Nicht behaupten |
| --- | --- | --- | --- | --- |
| 1 | theory_literature_and_methods | review_now_final_blocked | Review the 11 priority-1 method-foundation sources and record page or section notes. Gate-Aktion: Priority-1-Quellen mit Seiten- oder Abschnittsnotizen reviewen. | Quellenstatus nicht automatisch hochstufen und keine finale Zitation ohne Human Review. |
| 2 | chapters_01_to_03 | write_now_bounded | Use the 8 chapter-plan rows to draft the front matter and methods chapters. Gate-Aktion: Kapitel entlang Evidence IDs, Quellen, Tabellen/Figuren und Gates schreiben. | Keine Methodenbehauptung ohne deterministisches Artefakt, reviewte Quelle oder sichtbaren Pending-Status. |
| 3 | h1_results | write_now_bounded | Write H1 as bounded Polymarket support plus explicit broad-claim boundary. Gate-Aktion: H1 bounded, H2 daily event-window, H3 timing diagnostics schreiben. | Keine universelle Polymarket-Ueberlegenheit und keine RCP-Wahrscheinlichkeitsclaims. |
| 4 | h2_h3_results | write_now_bounded | Draft H2 as daily event-window response and H3 as wallet-tier timing diagnostics. Gate-Aktion: H1 bounded, H2 daily event-window, H3 timing diagnostics schreiben. | Keine Intraday-Speed-, Granger-Kausalitaets-, Private-Information- oder Profitabilitaetsclaims. |
| 5 | results_and_appendix | write_now_bounded | Use 5 core tables and 4 core figures with the generated captions and limitation notes. Gate-Aktion: 5 Kern-Tabellen und 4 Kern-Figuren mit Captions integrieren. | Keine Rohartefakt-Dumps und keine neuen Tabellen/Figuren ohne Evidence-Map-Update. |
| 6 | appendix_or_discussion | appendix_only_pending_review | Mention monitor only as read-only prototype and review workflow. Gate-Aktion: Monitor nur als read-only Prototyp und Review-Workflow erwaehnen. | Review-Access bleibt pausiert; keine Wallet-Adress-Exposition, keine Order-/Trading-Pfade und keine thesis-facing Alert-Evidenz. |
| 7 | discussion_pending_final_result | descriptive_only_final_blocked | Keep the Swiss comparison descriptive until the official vote result is available and mapped. Gate-Aktion: Bis zum offiziellen 14. Juni 2026 Resultat beschreibend bleiben. | Keine finale Effizienzinterpretation vor offizieller Resultatzuordnung vom 14. Juni 2026. |
| 8 | future_work | future_work_only | Use the 7 protocol rows only as a future-work design section. Gate-Aktion: Nur als Future-Work-Ausblick verwenden. | Keine Runtime-Agenten, kein MCP, kein Model Routing, keine LLM-Metriken und keine Trading-Pfade. |
| 9 | project_management | advisor_discussion_now | Ask the advisor to approve the bounded H1 wording, source-review depth, Swiss placement, and appendix scope. Gate-Aktion: Dozentenbericht und Absprache-Checklist zuerst verwenden. | Keinen Scope-Ausbau starten, bevor der H1-H2-H3-Kern geschrieben und abgestimmt ist. |
| 10 | whole_thesis | qa_after_draft | Run full tests, review checks, citation checks, table/figure checks, and Swiss spelling scan before export. Gate-Aktion: Nach Draft: Tests, review_check, citation review, spelling scan und DOCX render gate wiederholen. | Keine finale Abgabebereitschaft behaupten, solange Source Review, Swiss-Gate oder DOCX-Render-QA offen sind. |

## Bounded H1-H2-H3 Kapitelentwurf

Der neue H1-H2-H3 Bounded Chapter Draft liefert 18 geordnete Prosa-Bausteine: 6 je H1, H2 und H3. Bounded-draft-ready: 18; final-submission-ready: 0.
Der Dozent sieht damit direkt, dass jede empirische Methode und jede Interpretation eine Evidence-ID, Literatur-IDs, deterministische Artefakte, ein kuratiertes Tabellen-/Figurenpaar, Limitationen und ein Source-Review-Gate hat.

| Kapitel | Methoden | Interpretationen | Literatur/Artefakte | Tabelle/Figur | Gate |
| --- | --- | --- | --- | --- | --- |
| H1 | `method_h1_brier_dm` | `interpretation_h1_bounded_advantage; interpretation_h1_broad_claim_not_proven` | Literatur `lit_brier_001; lit_dm_001; lit_emh_001; zotero_poly_002`; Artefakte `data/results/thesis_h1_summary.csv; data/results/h1_poll_claim_readiness_summary.csv; plus 7 weitere`. | T2 / F1 | H1: 10 Source-Review-Zeilen im Ledger und in der Manual Source Review Follow-up Overview; 10 pending; 0 final-ready. |
| H2 | `method_h2_event_window` | `interpretation_h2_daily_response` | Literatur `lit_eventstudy_001; lit_emh_001; zotero_poly_001`; Artefakte `data/results/h2_event_window_summary.csv; data/events_timeline_seed.csv; plus 3 weitere`. | T3 / F2 | H2: 5 Source-Review-Zeilen im Ledger und in der Manual Source Review Follow-up Overview; 5 pending; 0 final-ready. |
| H3 | `method_h3_wallet_tiers; method_h3_granger_timing` | `interpretation_h3_top_tier_signal` | Literatur `zotero_poly_001; zotero_poly_005; zotero_poly_007; lit_granger_001`; Artefakte `data/results/h3_wallet_distribution_inventory.json; data/results/h3_granger_results.csv; plus 5 weitere`. | T4 / F3 | H3: 8 Source-Review-Zeilen im Ledger und in der Manual Source Review Follow-up Overview; 8 pending; 0 final-ready. |

Diese Sektion ist eine Schreibvorlage, kein finaler Zitations- oder Abgabeclaim. Keine neuen Kennzahlen, keine Rohartefakt-Dumps, keine Quellenstatus-Hochstufung und keine Runtime-Agenten.

## Source-Gated H1-H2-H3 Drafting Sequence

Der source-gated Thesis-Drafting-Pass bringt den H1-H2-H3-Kern in 15 paragraphenweise Schreibschritte: 5 je Kapitel. Bounded-draft-ready: 15; final-submission-ready: 0. Manual Source Review: 23 Rows verlinkt, 23 pending, 0 final-ready.
Fuer den Dozenten ist das die konkrete Schreibreihenfolge nach dem Bounded Chapter Draft: Methode/Resultat setzen, Interpretation und Limitation setzen, Tabelle/Figur einbauen, Manual Source Review ausfuehren, Finalgate und Future-Agent-Grenze sichtbar lassen.
Review-Access bleibt pausiert; auf Projektebene geht es jetzt ueber Advisor-Feedback, Manual Source Review Follow-up Overview-/Ledger-Abgleich, H1-H3-Prosa, kompakte Tabellen/Figuren, Swiss-Result-Gate und finale DOCX-Render-QA weiter. Kontrollpunkt: 23 offene H1-H2-H3 Review-Rows, 23 pending, 0 final-ready; keine finale Zitation und keine Quellenstatus-Hochstufung vor abgeschlossenem Overview-/Ledger-Abgleich.

| Kapitel | Schritte | Manual Source Review | Tabelle/Figur | Status |
| --- | --- | --- | --- | --- |
| H1 | 5: Methode und Resultat setzen -> Interpretation und Limitation setzen -> Tabelle und Figur einbauen -> Manual Source Review ausfuehren -> Finalgate und Future-Agent-Grenze setzen | 10 rows; 10 pending; 0 final-ready; Manual Source Review Follow-up Overview-/Ledger-Abgleich offen | T2 / F1 | source_gated_thesis_draft_ready_final_source_review_pending |
| H2 | 5: Methode und Resultat setzen -> Interpretation und Limitation setzen -> Tabelle und Figur einbauen -> Manual Source Review ausfuehren -> Finalgate und Future-Agent-Grenze setzen | 5 rows; 5 pending; 0 final-ready; Manual Source Review Follow-up Overview-/Ledger-Abgleich offen | T3 / F2 | source_gated_thesis_draft_ready_final_source_review_pending |
| H3 | 5: Methode und Resultat setzen -> Interpretation und Limitation setzen -> Tabelle und Figur einbauen -> Manual Source Review ausfuehren -> Finalgate und Future-Agent-Grenze setzen | 8 rows; 8 pending; 0 final-ready; Manual Source Review Follow-up Overview-/Ledger-Abgleich offen | T4 / F3 | source_gated_thesis_draft_ready_final_source_review_pending |

| Ordnung | Kapitel | Schreibschritt | Writer Action | Finalgate |
| --- | --- | --- | --- | --- |
| 1 | H1 | Methode und Resultat setzen | H1: Methoden- und Resultatabsatz aus dem Source-Gated Writing Pass in den BA-Entwurf uebernehmen; Evidence IDs sichtbar halten. | H1: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 2 | H1 | Interpretation und Limitation setzen | H1: Interpretation nur bounded formulieren und Limitation direkt nach dem Resultat platzieren. | H1: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 3 | H1 | Tabelle und Figur einbauen | H1: Nur Tabelle T2 und Abbildung F1 einbauen; keine Rohartefakt-Dumps. | H1: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 4 | H1 | Manual Source Review ausfuehren | H1: Manual Source Review Execution Pass abarbeiten und Manual Source Review Follow-up Overview-/Ledger-Abgleich, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen. | H1: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 5 | H1 | Finalgate und Future-Agent-Grenze setzen | H1: Finalgate sichtbar lassen und Agenten nur als Future-Work-Grenze mit llm_audit_log-Vorbedingung erwaehnen. | H1: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 6 | H2 | Methode und Resultat setzen | H2: Methoden- und Resultatabsatz aus dem Source-Gated Writing Pass in den BA-Entwurf uebernehmen; Evidence IDs sichtbar halten. | H2: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 7 | H2 | Interpretation und Limitation setzen | H2: Interpretation nur bounded formulieren und Limitation direkt nach dem Resultat platzieren. | H2: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 8 | H2 | Tabelle und Figur einbauen | H2: Nur Tabelle T3 und Abbildung F2 einbauen; keine Rohartefakt-Dumps. | H2: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 9 | H2 | Manual Source Review ausfuehren | H2: Manual Source Review Execution Pass abarbeiten und Manual Source Review Follow-up Overview-/Ledger-Abgleich, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen. | H2: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 10 | H2 | Finalgate und Future-Agent-Grenze setzen | H2: Finalgate sichtbar lassen und Agenten nur als Future-Work-Grenze mit llm_audit_log-Vorbedingung erwaehnen. | H2: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 11 | H3 | Methode und Resultat setzen | H3: Methoden- und Resultatabsatz aus dem Source-Gated Writing Pass in den BA-Entwurf uebernehmen; Evidence IDs sichtbar halten. | H3: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 12 | H3 | Interpretation und Limitation setzen | H3: Interpretation nur bounded formulieren und Limitation direkt nach dem Resultat platzieren. | H3: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 13 | H3 | Tabelle und Figur einbauen | H3: Nur Tabelle T4 und Abbildung F3 einbauen; keine Rohartefakt-Dumps. | H3: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 14 | H3 | Manual Source Review ausfuehren | H3: Manual Source Review Execution Pass abarbeiten und Manual Source Review Follow-up Overview-/Ledger-Abgleich, Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use erfassen. | H3: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |
| 15 | H3 | Finalgate und Future-Agent-Grenze setzen | H3: Finalgate sichtbar lassen und Agenten nur als Future-Work-Grenze mit llm_audit_log-Vorbedingung erwaehnen. | H3: Source-Coverage-Gaps 0; final-ready Manual-Execution rows 0. Manual Source Review Follow-up Overview-/Ledger-Abgleich vor Citation Gate sichtbar halten. |

Auch diese Sequenz ist kein finaler Zitations- oder Abgabeclaim: Page-/Section-Note, Claim-Support, Blocked-Wording und Citation-Use bleiben manuelle Gates; Agenten bleiben documentation-only Future Work.

## Naechste Arbeitsschritte

Der Next-Work-Plan ordnet 10 Workstreams. Erste Prioritaet ist `work_01_source_review`, letzte QA-Prioritaet ist `work_10_final_qa`.

| Prioritaet | Workstream | Naechste Aktion | Guardrail |
| --- | --- | --- | --- |
| 1 | Quellenreview Kernquellen | Die 11 Priority-1-Quellen mit Seiten- oder Abschnittsnotizen pruefen. | Quellenstatus nicht automatisch hochstufen. |
| 2 | Einleitung, Theorie und Methodik schreiben | Die 8 Kapitelplan-Zeilen fuer Front Matter und Methodenkapitel nutzen. | RCP, H2-Kuration, H3-Tiers und Agent-Deferral explizit halten. |
| 3 | H1-Ergebniskapitel schreiben | H1 als begrenzte Polymarket-Stuetze plus breiten Claim-Grenze formulieren. | Keine universelle Polymarket-Ueberlegenheit behaupten. |
| 4 | H2- und H3-Ergebniskapitel schreiben | H2 als taegliche Event-Window-Reaktion und H3 als Wallet-Timingdiagnostik schreiben. | Keine Intraday-, Kausalitaets-, Private-Information- oder Profitabilitaetsclaims. |
| 5 | Kompakte Tabellen und Figuren integrieren | 5 Kern-Tabellen und 4 Kern-Figuren mit generierten Captions verwenden. | Keine Rohartefakte ohne Update von Evidence Map und Kapitelplan einfuegen. |
| 6 | Monitor als Appendix-Prototyp halten | Monitor nur als read-only Review-Workflow und nicht als Kernbeweis darstellen. | Keine Wallet-Adress-Exposition und keine Order- oder Trading-Pfade. |
| 7 | Swiss Side-Track nach Ergebnis finalisieren | Bis zum offiziellen Ergebnis beschreibend bleiben und danach Artefakte neu generieren. | Poll-Anteile nicht als Gewinnwahrscheinlichkeiten behandeln. |
| 8 | Agenten-Pipeline als Future Work halten | Die 7 Protokollzeilen nur als Zukunftsdesign nutzen. | Keine Runtime-Agenten, kein MCP, kein Model Routing und keine LLM-Metriken. |
| 9 | Dozentenfeedback zur Scope-Engfuehrung nutzen | H1-Wording, Source-Review-Tiefe, Swiss-Platzierung und Appendix-Scope klaeren. | Empirischen Scope nicht erweitern, bevor der Kern geschrieben ist. |
| 10 | Finale Thesis-QA | Tests, Review-Checks, Citation Checks, Tabellen/Figuren und Swiss-Spelling pruefen. | Keine finale Aussage ueber Artefakte und gepruefte Quellen hinaus. |

## Kapitelweise Umsetzungscheckliste

Die Execution-Checkliste uebersetzt die Highlevel-View in 8 Kapitelaufgaben. Erste Aufgabe ist `exec_01_01_intro`, letzte Aufgabe ist `exec_08_08_discussion_conclusion`.

| Task | Kapitel | Schreibaktion | Fertig wenn | Advisor-Fragen |
| --- | --- | --- | --- | --- |
| exec_01_01_intro | Einleitung und Forschungsfrage | Forschungsfrage, Scope Polymarket/US-Wahl und Proxy-Logik knapp formulieren. | Forschungsfrage, H1-H3-Logik und Nicht-Ziele sind sichtbar. | advisor_q01_h1_wording; advisor_q08_final_qa |
| exec_02_02_theory_literature | Theorie und Literatur | EMH, Prognosemaerkte, Event-Study und Wallet-Vorsicht quellengebunden ausarbeiten. | Jede Theorie- und Methodenbehauptung hat eine reviewte Quelle oder bleibt Draft. | advisor_q02_source_depth |
| exec_03_03_data_method | Daten und Methodik | Datenpipeline, Artefakthierarchie und Python-only-Metrikregel als Methodik schreiben. | Alle Methoden verweisen auf deterministische Artefakte und passende Quellenanker. | advisor_q02_source_depth; advisor_q03_h2_h3_scope |
| exec_04_04_h1_results | H1: Prognosequalitaet | H1 als begrenzte Polymarket-Stuetze plus klare Grenze der breiten Behauptung schreiben. | Bounded H1-Claim, Gegenbeispiel und Limitation stehen direkt nebeneinander. | advisor_q01_h1_wording; advisor_q04_table_figure_package |
| exec_05_05_h2_results | H2: Ereignisfenster | H2 als Tagesfensterdiagnostik schreiben und Intraday-Speed ausschliessen. | Ereignisse, Tagesfenster und Tagesfrequenz-Limitation sind transparent. | advisor_q03_h2_h3_scope; advisor_q04_table_figure_package |
| exec_06_06_h3_results | H3: Wallet-Timing | H3 als dataset-relative Timingdiagnostik schreiben, nicht als Kausal- oder Private-Information-Claim. | BUY-only, Tagesaggregation, Mehrfachtests und Nicht-Profitabilitaet sind genannt. | advisor_q03_h2_h3_scope; advisor_q04_table_figure_package |
| exec_07_07_extensions | Erweiterungen: Monitor und Schweizer Abstimmung | Monitor als Prototyp und Swiss als Side-Track knapp platzieren. | Review-Access bleibt pausiert und Swiss traegt keine finale Effizienzaussage. | advisor_q05_monitor_appendix; advisor_q06_swiss_gate |
| exec_08_08_discussion_conclusion | Diskussion, Limitationen und Fazit | Fazit als begrenzte Evidenz fuer H1-H3 schreiben und Agenten nur als Future Work fuehren. | Keine finale Aussage geht ueber deterministische Artefakte und reviewte Quellen hinaus. | advisor_q07_agent_outlook; advisor_q08_final_qa |

Die Liste ist kein neues empirisches Ergebnis. Sie zeigt nur, welche Kapitel mit welchen Inputs, Done-Kriterien und Advisor-Fragen abgearbeitet werden sollen.

## Forschungsfrage und Hypothesen

Die Leitfrage lautet, inwiefern Polymarket-Preise Informationen waehrend politischer Ereignisse abbilden, schneller oder anders als traditionelle Prognosequellen reagieren und ob aggregierte Wallet-Aktivitaet als frueher Timing-Indikator sichtbar wird.

- H1: Polymarket wird als Probability-Forecast gegen traditionelle Forecast- oder Poll-derived Vergleichsquellen getestet.
- H2: Vorab kuratierte Ereignisse werden in taeglichen Event-Windows ausgewertet.
- H3: Wallet-Aktivitaet wird ueber verteilungsbasierte Tiers als Timing-Diagnostik analysiert.

## Wissenschaftlicher Quellenrahmen

Der lokale Literaturindex umfasst 15 Quellen; fuer diesen Bericht werden 10 wissenschaftlich relevante Kernquellen als Rahmen verwendet. Statusverteilung: candidate: 2, rejected: 1, skimmed: 12.
Das neue Source-Review-Worksheet enthaelt 15 manuelle Review-Zeilen, davon 11 Priority-1-Methodenquellen und 1 blockierte oder Future-Work-Quelle. Alle Reviewer-Entscheide bleiben pending.

| Quelle | Rolle in der Arbeit | Beitrag zur Interpretation | Status |
| --- | --- | --- | --- |
| `lit_emh_001` - Eugene F. Fama (1970): Efficient Capital Markets: A Review of Theory and Empirical Work | Theorie: informationelle Effizienz und EMH-Proxy-Logik. | Preise als Informationsaggregate motivieren die Proxy-Tests, beweisen aber keine Effizienz. | skimmed |
| `lit_brier_001` - Glenn W. Brier (1950): Verification of Forecasts Expressed in Terms of Probability | H1-Methode: Probability-Forecast-Verifikation mit Brier-Verlust. | Begruendet H1 als Verlustvergleich von Wahrscheinlichkeitsprognosen. | skimmed |
| `lit_dm_001` - Francis X. Diebold; Roberto S. Mariano (1995): Comparing Predictive Accuracy | H1-Methode: Vergleich konkurrierender Forecast-Loss-Serien. | Begruendet den Test auf Unterschiede in vorliegenden Forecast-Verlustreihen. | skimmed |
| `lit_eventstudy_001` - A. Craig MacKinlay (1997): Event Studies in Economics and Finance | H2-Methode: Event-Window-Design und Grenzen von Ereignisstudien. | Begruendet H2 als Ereignisfenster-Design statt freier News-Interpretation. | skimmed |
| `lit_granger_001` - C. W. J. Granger (1969): Investigating Causal Relations by Econometric Models and Cross-Spectral Methods | H3-Methode: Lead-Lag-Diagnostik mit vorsichtiger Kausalitaetsabgrenzung. | Begruendet H3 als Vorhersage-/Timingdiagnostik, nicht als starker Ursachenbeweis. | skimmed |
| `zotero_poly_001` - Kwok Ping Tsang; Zichao Yang (2026): The Anatomy of a Blockchain Prediction Market: Polymarket in the 2024 U.S. Presidential Election | Polymarket-Kontext: Transaktionslogik, Wallet- und Volumen-Caveats. | Stuetzt Vorsicht bei on-chain Volumen, Wallet-Flows und Austausch-Equivalenten. | skimmed |
| `zotero_poly_002` - Laurie E. Cutting; Sarah S. Hughes-Berheim; Paul M. Johnson; Hiba Baroud; Brett Goldstein (2025): Are Betting Markets Better than Polling in Predicting Political Elections? | H1-Kontext: Prediction Markets versus Polling/Forecasting. | Stuetzt die Vergleichsfrage Polymarket versus Polling, ersetzt aber keine lokale Transformation. | skimmed |
| `zotero_poly_005` - Robin Hanson (2007): Insider Trading and Prediction Markets | H3-Kontext: Abgrenzung von Information, Informationsvorsprung- und Ethikfragen. | Hilft bei der ethischen Abgrenzung von Informationsvorsprung und Marktpreisen. | skimmed |
| `zotero_poly_006` - Constantin Buergi; Wanying Deng; Karl Whelan (2025): Makers and Takers: The Economics of the Kalshi Prediction Market | Marktmikrostruktur: Maker/Taker, Bias- und Risikocaveats. | Stuetzt Mikrostruktur- und Bias-Caveats fuer spaetere Monitor-/Strategieformulierungen. | skimmed |
| `zotero_poly_007` - Pavel Rezabek (2024): Analysis of Prediction Markets in Crypto: Investigating Convergence in Time Volatility and Biases in Polymarket | Polymarket-Forschungskontext: Konvergenz, Volatilitaet und Biases. | Positioniert Polymarket-Forschung mit Konvergenz-, Volatilitaets- und Bias-Grenzen. | skimmed |

Die Quellen sind als lokaler Literaturrahmen hinterlegt. Thesis-facing Detailclaims duerfen erst nach Vollreview als reviewed oder cited verwendet werden; candidate/rejected Quellen tragen keine Ergebnisbehauptungen.

## Methodisches Design und Begruendung

Die Arbeit operationalisiert informationelle Effizienz nicht als direkt beobachtbare Eigenschaft, sondern ueber drei Proxies. Forecast-Qualitaet wird mit Brier-Verlusten und Vergleichstests gemessen; Ereignisreaktionen werden nur fuer vorab kuratierte Events ausgewertet; Wallet-Signale bleiben aggregierte Timing-Diagnostik. Damit sind die Resultate reproduzierbar und methodisch begrenzt.

- Alle Kennzahlen stammen aus Python-Artefakten unter `data/results`.
- RCP bleibt ausgeschlossen, solange keine dokumentierte Probability-Transformation existiert.
- Granger-Outputs werden nicht kausal interpretiert.
- Monitor- und Live-Daten bleiben read-only und schreiben bounded Artefakte.

## Zentrale Erkenntnisse, Begruendung und Interpretation

Die wichtigste inhaltliche Verbesserung ist die Trennung zwischen Ergebnis, Interpretation und Grenze. Dadurch kann der Dozent sehen, was bereits empirisch tragfaehig ist und welche Aussagen bewusst nicht gemacht werden.

| Bereich | Erkenntnis | Evidenz | Interpretation | Grenze |
| --- | --- | --- | --- | --- |
| H1 Forecast-Qualitaet | Polymarket ist in den aktuellen Resultaten nicht pauschal ueberlegen, zeigt aber einen klaren Vorteil in bestimmten spaeten und kompetitiven Vergleichsfenstern. | Primary Brier: 0.2303 vs 0.3324; H1-Synthesis 7 von 9 Zeilen mit niedrigerem mittleren Polymarket-Brier, aber nur 3 von 9 mit Fallmehrheit. | Die belastbare Aussage ist ein bounded Forecast-Quality-Vorteil, besonders im <=90-Tage Low/Middle-Poll-Distanz-Scope. | Der breite Viele-Faelle-Claim bleibt not_proven; das State-Date-Vollpanel stuetzt poll-derived in 1360 von 1720 Zeilen. |
| H2 Event-Windows | Polymarket bewegt sich um mehrere kuratierte politische Ereignisse sichtbar in der Tagesauflosung. | 7 kuratierte Ereignisse; groesstes Primaerfenster nach Betrag: 07_13_trump_shooting +7.2 Prozentpunkte. | Das stuetzt eine These, dass oeffentliche Ereignisse in den Marktpreisen sichtbar werden koennen. | Taegliche Daten zeigen Reaktionsrichtung und Groessenordnung, aber keine intraday Reaktionsgeschwindigkeit. |
| H3 Wallet-Timing | Top-Wallet-Tier-Aktivitaet zeigt eine messbare, aber vorsichtig zu formulierende Timing-Struktur. | 1216 alignierte Modellzeilen; staerkste Korrelation tier_1_top_1pct lag 1 = 0.1858; kleinster Granger-p-Wert 0.0012. | Das ist als Vorhersage-/Timingdiagnostik verwendbar und motiviert weitere Sensitivitaetschecks. | BUY-only Quelle, Tagesaggregation und Multiple-Testing-Risiko begrenzen die Aussage. |
| Monitor und Review-Queue | Der Monitor hat die richtige Rolle als Kontroll- und Review-Infrastruktur, nicht als Ergebnisgenerator fuer starke Claims. | 3 aktuelle Review-Cases, davon 1 high und 2 medium; Status source_check_pending=3. | Die Review-Queue ist methodisch wichtig, weil sie auffaellige Faelle von thesis-faehiger Evidenz trennt. | Die Queue ist kein Nachweis fuer Ursachen, Regelverstoss, Handelbarkeit, Profitabilitaet oder zukuenftige Entwicklung. |
| Swiss-Referendum Side-Track | Der laufende Referendumsvergleich zeigt aktuell eine grosse Divergenz zwischen Marktpreis und Umfrageanteilen. | 7 Umfragen, 48 Polymarket-Snapshots; latest Polymarket Yes 26.0%, latest poll Yes 45.0%, raw gap -19.0 pp. | Das ist ein anschauliches aktuelles Beispiel fuer die Trennung von Marktpreisen und traditionellen Umfragesignalen. | Umfrageanteile sind keine Gewinnwahrscheinlichkeiten; vor dem Abstimmungsergebnis gibt es keine finale Effizienzbewertung. |

## Warum dieses Vorgehen methodisch sinnvoll ist

| Entscheidung | Begruendung | Konsequenz |
| --- | --- | --- |
| Brier Score und DM-Test | H1 vergleicht Probability-Forecasts, deshalb braucht es einen Verlustscore und einen Test auf Verlustserien. | Die Aussage bleibt Forecast-Qualitaet, nicht Reaktionsgeschwindigkeit oder Mechanismus. |
| Vorab kuratierte Events | H2 soll nicht Ereignisse nach sichtbaren Kursbewegungen auswaehlen. | Die Event-Auswahl ist dadurch strenger, aber weniger flexibel. |
| Verteilungsbasierte Wallet-Tiers | H3 vermeidet willkuerliche Whale-Schwellen und leitet Tiers aus der beobachteten Verteilung ab. | Die Quelle bleibt BUY-only und kann nicht alle Marktaktivitaet abbilden. |
| Review-Queue statt Agentenclaim | Auffaellige Monitor-Faelle brauchen menschliche Quellenpruefung vor Interpretation. | Aktuelle Cases bleiben Review-Cues und werden nicht automatisch thesis-faehig. |
| Swiss-Referendum als Side-Track | Ein aktueller, zeitlich begrenzter Markt zeigt die Methode in einem laufenden politischen Kontext. | Die Analyse bleibt bis zum Ergebnis des 14. Juni 2026 beschreibend. |

## Projektstruktur

- SQLite-Datenbank: 9 Tabellen.
- Ergebnisartefakte: 366 Dateien unter `data/results`.
- Analyse-Module: 78 Dateien.
- Collector-Module: 10 Dateien.
- Tests: 137 Testdateien; letzter Status: 593 passed in 70.75s (0:01:10).

## H1 - Forecast-Qualitaet

- Beobachtungen: 194.
- Mean Brier Polymarket: 0.2303.
- Mean Brier FiveThirtyEight: 0.3324.
- Mean Brier 50-Prozent-Baseline: 0.2500.
- Mean Brier Vortag-Polymarket: 0.2303.
- DM p-Wert Polymarket vs FiveThirtyEight: 6.71e-61.
- Polymarket niedrigerer Tagesverlust als FiveThirtyEight: 194 von 194 Tagen (100.0%).
- Mittlerer Verlustvorteil gegenueber FiveThirtyEight: 0.1021 Brier-Punkte.
- H1-Synthesis ueber traditionelle Vergleichsquellen: 7 von 9 Vergleichszeilen stuetzen Polymarket im mittleren Brier; 3 von 9 zeigen auch eine Mehrheit niedrigerer Einzelfallverluste. Breiter Viele-Faelle-Beweis: 0 von 9.
- H1-Claim-Evidence-Audit: 16 von 22 Audit-Zeilen stuetzen Polymarket begrenzt, 5 widerspricht dem starken Claim; bei direkt pollbezogenen Zeilen sind 12 von 15 stuetzend und 3 widersprechend. Breiter User-Claim belegt: 0.
- H1-Poll-Comparison-Result: Im primaeren <=90-Tage-Low/Middle-Poll-Distanz-Scope hat Polymarket in 262 von 285 State-Date-Zeilen (91.9%) den niedrigeren Brier-Verlust; poll-derived gewinnt 23 Zeilen. Auf State-Ebene sind es 9 von 9 States, exakter einseitiger p-Wert 0.0020. Direkt pollbezogen stuetzen 12 von 15 Audit-Zeilen Polymarket begrenzt; das Vollpanel bleibt Gegenbeleg mit poll-derived 1360 von 1720 Zeilen. Status: not_proven.
- H1-Poll-Claim-Readiness: 4 von 13 Claim-Zeilen stuetzen den bounded <=90-Tage Low/Middle-Poll-Distanz-Scope, 5 sind Gegenbeispiel-Scopes und 3 zeigen nur Mean-Loss-Stuetze ohne Fall- oder State-Mehrheit. Im bounded Scope hat Polymarket 262 von 285 State-Date-Zeilen (91.9%) und 17 von 17 State-Month-Einheiten (exact p=7.6e-06, 95-Prozent-Untergrenze 0.838) auf seiner Seite. Bounded Claim supported: 1; breiter Claim belegt: 0.
- H1-Poll-Scope-Frontier: 8 von 30 Horizont-x-Poll-Distanz-Scopes erfuellen die robuste Regel. Der groesste robuste Scope ist <=120 days + Low/middle distance: Polymarket 313 von 433 State-Date-Zeilen (72.3%), 18 von 26 State-Month-Einheiten, exact p=0.0378. Der staerkste Scope bleibt lte_90_days_low_middle_distance mit 285 Zeilen und p=7.6e-06. <=90 Tage ueber alle Distanzen stuetzen Polymarket zwar in 262 von 357 Zeilen (73.4%), aber State-Month p=0.0758; das Vollpanel bleibt Gegenbeleg mit poll-derived 1360 von 1720 Zeilen. Status not_proven.
- H1-Poll-Decision-Matrix: 2 von 9 Entscheidungszeilen sind robuste bounded-Yes-Zeilen, 3 zeigen Mean-Loss-Stuetze ohne Fall-/Unit-Mehrheit und 2 sind Gegenbelege. Groesster robuster Scope: Polymarket 313 von 433 State-Date-Zeilen (72.3%), 18 von 26 State-Month-Einheiten, p=0.0378. Kalibrierungskontext: 5 von 5 Pairwise-Reihen stuetzen Polymarket im mittleren Brier, aber nur 2 auch per Fallmehrheit. Bounded ready 1; breiter Claim 0; Status not_proven.
- H1-Robust-Poll-Scope-Quality: 1436 Forecast-Zeilen aus 718 State-Date-Faellen und 2 robusten Poll-Scopes. Groesster robuster Scope: Polymarket 313 von 433 Zeilen (72.3%), Mean Brier 0.1982 vs 0.2555, ECE 0.3868 vs 0.4251, Separation 0.2182 vs 0.1394. Staerkster robuster Scope: Polymarket 262 von 285 Zeilen (91.9%), Mean Brier 0.2214 vs 0.3147, ECE 0.4523 vs 0.5362. Dort sind alle Outcomes positiv, deshalb ist Separation nicht definiert. Breiter Claim belegt 0.
- H1-Robust-Poll-Scope-Unit-Quality: Die robusten Scopes bleiben auch auf weniger wiederholten Einheiten sichtbar. Groesster robuster Scope: State-Ebene Polymarket 10 von 11 (p=0.00586), State-Month 18 von 26 (p=0.0378), State-Horizon 20 von 26 (p=0.00468). Staerkster robuster Scope: States 9 von 9 (p=0.00195), State-Month 17 von 17 (p=7.6e-06). Medianer State-Month-Brier-Vorteil: 0.0484 im groessten und 0.0723 im staerksten Scope. Breiter Claim belegt 0.
- H1-Poll-Comparison-Unit-Robustness: Der primaere Scope haelt auch nach Aggregation: Polymarket wird in 9 von 9 States, 17 von 17 State-Month-Einheiten und 17 von 17 State-Horizon-Einheiten gestuetzt; State-Month exact p=7.6e-06, 95-Prozent-Untergrenze 0.838. Full-Panel-State-Month-Gegenbeleg: poll-derived 61 von 80; Late-High-Distance-State-Month-Gegenbeleg: poll-derived 8 von 8, exact p=0.0039. Status: not_proven.
- H1-Direct-Poll-Loss-Decomposition: Direkte Poll-Transform-Vergleiche ergeben Mean Brier 0.0544 fuer Polymarket vs 0.0729 fuer poll-derived Comparatoren. Polymarket hat niedrigeren Verlust in 22 von 56 Source-State-Faellen, poll-derived in 34; die Polymarket-Gewinnfaelle haben aber im Mittel 0.0498 Brier-Vorteil gegenueber 0.0018 bei poll-derived Gewinnfaellen. Das erklaert den aggregierten Brier-Vorteil, ersetzt aber keinen Fallmehrheits- oder Viele-Wahlen-Beweis.
- H1-Direct-Poll-State-Cluster-Diagnostic: Auf 43 State-Clustern bleibt der gleichgewichtete mittlere Verlustvorteil positiv (0.0122; Bootstrap-95%-Intervall 0.0041 bis 0.0217; Sign-Flip-p=0.0045). Die State-Mehrheit geht aber gegen Polymarket: 13 States fuer Polymarket, 30 fuer poll-derived Comparatoren. Das stuetzt einen mittleren Verlustvorteil, nicht eine State-Mehrheitsbehauptung.
- H1-Direct-Poll-Outlier-Robustness: Der gleiche State-Cluster-Mean von 0.0122 bleibt nach jeder einzelnen State-Entfernung positiv; das Minimum ist 0.0095 ohne Wisconsin. Entfernt man die groessten positiven State-Beitraege, bleibt der Mean bis 6 entfernte States positiv und kippt bei 7 entfernten States auf -0.0001. Das zeigt: nicht ein einzelner Ausreisser, aber Konzentration in den groessten positiven State-Beitraegen; Status not_proven.
- H1-State-Source-Konsens: 156 Source-State-Vergleiche ueber 50 States; Polymarket hat niedrigeren Verlust in 43 Source-State-Faellen, traditionelle Comparatoren in 112. Im All-Source-State-Konsens gewinnt Polymarket 9 States, Comparatoren 37, Ties 4. Bei States mit zwei direkten Poll-Transform-Quellen gewinnt Polymarket 8 von 13 States.
- H1-Competitive-State-Diagnose: In den niedrigsten Comparator-Distanz-Terzilen gewinnt Polymarket 35 von 52 All-Source-Faellen und 18 von 19 direkten Poll-Transform-Faellen. In der hoechsten Distanz-Terzile gewinnt Polymarket 0 von 40 All-Source-Faellen, Comparatoren 40 von 40. Das stuetzt eine begrenzte Competitive-State-Ausnahme, aber keinen breiten Viele-Faelle-Beweis.
- H1-State-Date-Competitiveness-x-Horizon: Im <=90-Tage-Fenster und in Low/Middle-Poll-Distanz-Terzilen hat Polymarket in 262 von 285 State-Date-Zeilen niedrigeren Verlust und in 9 von 9 States eine Mehrheit niedrigerer Verluste. In der spaeten High-Distance-Terzile gewinnt Polymarket 0 von 72 Zeilen, poll-derived 72 von 72. Das ist ein starker spaeter Competitive-Poll-Befund, aber wegen wiederholter State-Date-Zeilen kein unabhaengiger Viele-Wahlen-Beweis.
- H1-State-Level-Signifikanzdiagnose: Fuer dieselben spaeten Low/Middle-Poll-Distanz-Faelle stuetzt Polymarket 9 von 9 States; der exakte einseitige Binomial-p-Wert betraegt 0.0020, die exakte 95-Prozent-Untergrenze der Support-Quote 0.717. Die spaeten High-Distance-States bleiben ein Gegenbeleg: poll-derived 5 von 5 States.
- H1-Kalibrierungsdiagnostik: 192 Forecast-Case-Zeilen aus 7 Quellen und 5 Pairwise-Reihen; 5 von 5 zeigen niedrigeren mittleren Polymarket-Brier, 2 von 5 auch eine Mehrheit niedrigerer Einzelfallverluste, breiter Viele-Faelle-Beweis 0 von 5.
- 50-State-Kalibrierung: Polymarket Mean Brier 0.0262 und Fixed-Bin-ECE 0.0838; Rieke ECE 0.0774, 270toWin/JHK ECE 0.0802. Das ist ein Forecast-Qualitaets-, aber kein klarer Kalibrierungssieg.
- Final-Snapshot-Erweiterung: Polymarket niedrigerer Verlust in 5 von 8 geloesten 2024-Outcomes; Mean Brier Polymarket 0.0784 vs 538 final forecast 0.0933.
- State-Poll-Snapshot-Erweiterung: Polymarket niedrigerer Verlust in 8 von 13 geloesten State-Outcomes; Mean Brier Polymarket 0.1336 vs poll-derived 0.1764.
- 270toWin-Polling-Average-Erweiterung: 43 gematchte State-Outcomes; Polymarket niedrigerer Verlust in 14 Faellen, poll-derived in 29. Mean Brier Polymarket 0.0304 vs 270toWin poll-derived 0.0416.
- Popular-Vote-Erweiterung: 51 nationale Tageszeilen fuer Trump popular vote; Polymarket niedrigerer Verlust in 21 Zeilen, poll-derived in 30. Mean Brier Polymarket 0.5179 vs poll-derived 0.4824; dieser Zusatz ist ein Gegenbeleg zum starken Claim.
- Margin-Threshold-Readiness: 7 Trump-State-Margin-Maerkte geprueft; 4 haben 538-State-Poll-Average-Zeilen, aber 0 haben CLOB-Historie im bewahrten 538-Fenster. H1-kompatible neue Brier-Faelle: 0; 4 blockiert durch fehlende zeitliche Ueberlappung und 3 durch fehlende 538-State-Polls.
- State-Date-Poll-Panel: 1720 gematchte State-Date-Zeilen ueber 15 States und 186 Daten; Polymarket hat nur in 360 Zeilen niedrigeren Verlust, die poll-derived 538-Transformation in 1360. Mean Brier Polymarket 0.1595 vs poll-derived 0.1026.
- Temporal-Diagnose des State-Date-Panels: In den Polymarket-stuetzenden Monaten 2024-08, 2024-09 liegen 387 Zeilen ueber 13 States vor; Polymarket hat dort in 280 Zeilen niedrigeren Verlust, poll-derived in 107. Mean Brier 0.1842 vs 0.2543. Das erklaert den spaeten Polymarket-Vorteil, hebt aber den negativen Vollpanel-Befund nicht auf.
- Forecast-Horizon-Diagnose: Im <=90-Tage-Fenster vor der Wahl (61_90_days, 0_60_days) liegen 357 Zeilen ueber 13 States vor; Polymarket hat in 262 Zeilen niedrigeren Verlust, poll-derived in 95. Mean Brier 0.1799 vs 0.2520. Diese Horizon-Diagnose stuetzt Polymarket naeher an der Wahl, bleibt aber ein wiederholtes Forecast-Row-Fenster.
- State-Level-Horizon-Diagnose: Im selben <=90-Tage-Fenster stuetzt Polymarket 8 von 13 States nach mittlerem Brier und 8 von 13 States nach Mehrheit niedrigerer Tagesverluste; 5 States stuetzen Polymarket nicht.
- <=90-Day-Score-Quality-Diagnose: 714 Forecast-Zeilen aus 357 State-Date-Faellen und zwei Quellen. Polymarket hat niedrigeren Mean Brier 0.1799 vs 0.2520, niedrigeren Fixed-Bin-ECE 0.3797 vs 0.4391 und hoehere Probability-Separation 0.4560 vs 0.4366. Das stuetzt Forecast-Qualitaet im spaeten Fenster, bleibt aber ein wiederholtes State-Date-Forecast-Panel.
- Poll-Transform-Sensitivitaet: MAE 2.0 bis 10.0 Prozentpunkte; Polymarket bleibt im mittleren Brier in allen 12 Parameterzeilen niedriger und hat in 7 bis 12 von 13 State-Outcomes den niedrigeren Einzelfallverlust.
- State-Poll-Coverage-Audit: 50 US-States geprueft, 50 mit Polymarket-State-Markt, aber nur 13 mit REP/DEM-Zeilen im bewahrten 538-Polling-Average-Snapshot. 37 States fallen wegen fehlender 538-Snapshot-Pollwerte aus.
- Rieke-50-State-Erweiterung: 50 geloeste State-Outcomes gegen ein unabhaengiges pollbasiertes Rieke-Modell; Mean Brier Polymarket 0.0262 vs Rieke 0.0296. Polymarket hat nur in 12 von 50 State-Einzelfaellen den niedrigeren Verlust, Rieke in 38 von 50.
- 270toWin/JHK-50-State-Erweiterung: 50 geloeste State-Outcomes, davon 22 exakt ausgewiesene State-Wahrscheinlichkeiten und 28 zensierte >99.9-Prozent-Boundary-Werte; Mean Brier Polymarket 0.0262 vs 270toWin/JHK 0.0306. Polymarket hat in 9 von 50 Einzelfaellen den niedrigeren Verlust, 270toWin/JHK in 40 von 50.
- H1-Zusatzchecks insgesamt: 21 geloeste Outcomes in den 538-nahen Zusatzchecks, davon 13 mit niedrigerem Polymarket-Verlust. Die Rieke- und 270toWin/JHK-State-Reihen werden separat berichtet, weil sie dasselbe Praesidentschaftsrennen mit anderen traditionellen Modellen abdecken.

## H2 - Event-Window-Reaktion

- Kuratierte Ereignisse: 7.
- Kompakte H2-Zeilen: 15.
- Beispielhafte Primaerfenster:
  - 05_30_trump_conviction: -4.1 Prozentpunkte
  - 06_28_biden_trump_debate: +2.5 Prozentpunkte
  - 07_13_trump_shooting: +7.2 Prozentpunkte
  - 07_15_vance_vp_pick: +3.5 Prozentpunkte
  - 07_21_biden_withdrawal: -1.7 Prozentpunkte
  - 08_06_walz_vp_pick: +1.3 Prozentpunkte
  - 09_11_harris_trump_debate: -2.9 Prozentpunkte

## H3 - Wallet-Tier-Timing

- Aligned model rows: 1216.
- Tier counts: tier_1_top_1pct: 32, tier_2_top_5pct: 120, tier_3_top_10pct: 150, tier_4_observed_baseline: 2704.
- Staerkste dokumentierte Lead-Lag-Korrelation: tier_1_top_1pct lag 1 = 0.1858.
- Kleinster dokumentierter Granger-p-Wert: tier_1_top_1pct lag 1 = 0.0012.

## Monitor-Prototyp

- Recorded replay rows: 3394.
- Severity counts: none: 2813, info: 334, watch: 169, high: 78, critical: 0.
- Latest live dashboard markets: 12; alert rows: 7.
- Wallet graph: 238 nodes, 7966 edges.
- Anomaly review queue: 3 Cases (1 high, 2 medium, 0 low); Status source_check_pending=3.
- Review limitation: Die Queue ist kein Nachweis fuer Ursachen, Regelverstoss, Handelbarkeit, Profitabilitaet oder zukuenftige Entwicklung.

## Schweizer Referendum

- Kuratierte Umfragen: 7.
- Polymarket snapshots: 48.
- Bounded price-history rows: 504.
- Latest Polymarket Yes: 26.0 Prozent.
- Latest matched poll Yes: 45.0 Prozent.
- Raw gap: -19.0 Prozentpunkte.
- Decided-voter gap: -20.4 Prozentpunkte.

## Abbildungen

![Projektlogik: deterministische Analyse vor Interpretation.](dozentenbericht_assets/project_pipeline_overview.png)

*Die Abbildung zeigt die einfache Lesart fuer die Praesentation: Daten werden validiert, in Python analysiert und erst danach als Bericht, Dashboard oder spaeter als bounded Interpretation verwendet.*

![H1 Forecast-Quality Vergleich](../../data/results/h1_forecast_quality.png)

*Zeigt Brier Scores, Head-to-head-Tagesverluste und Forecast-Zeitreihen ohne ueberstarken Kalibrierungsanspruch.*

![H1 Forecast-Quality Synthesis](../../data/results/h1_forecast_quality_synthesis.png)

*Fasst alle aktuellen H1-Vergleichsquellen zusammen und trennt aggregierte Brier-Stuetze von einem breiten Viele-Faelle-Beweis.*

![H1 Claim-Evidence Audit](../../data/results/h1_claim_evidence_audit.png)

*Fuehrt die H1-Evidenz als Claim-Ledger zusammen: spaete Polymarket-Stuetze, widersprechendes Full-Panel und weiterhin nicht belegter breiter User-Claim.*

![H1 Poll-Comparison Result](../../data/results/h1_poll_comparison_result.png)

*Verdichtet die direkt pollbezogene H1-Evidenz: 262 von 285 spaeten Low/Middle-Poll-Distanz-Zeilen und 9 von 9 States stuetzen Polymarket, waehrend Vollpanel und High-Distance-Zeilen Grenzen bleiben.*

![H1 Poll-Claim Readiness](../../data/results/h1_poll_claim_readiness.png)

*Trennt die aktuell belegbare bounded Aussage von Gegenbeispiel-Scopes: Polymarket ist im <=90-Tage Low/Middle-Poll-Distanz-Scope stark, aber der breite Claim bleibt nicht belegt.*

![H1 Poll-Scope Frontier](../../data/results/h1_poll_scope_frontier.png)

*Visualisiert systematisch, wie weit sich der H1-Poll-Scope nach Horizont und quantilbasierter Poll-Distanz ausweiten laesst: groesster robuster Scope <=120 Tage Low/Middle, Vollpanel bleibt Gegenbeleg.*

![H1 Poll-Decision Matrix](../../data/results/h1_poll_decision_matrix.png)

*Verdichtet die H1-Poll-Evidenz in eine Claim-Matrix: robuste bounded-Yes-Zeilen, Mean-Loss-Stuetze ohne Mehrheit, Kalibrierungskontext und Vollpanel-Gegenbeleg.*

![H1 Robust Poll-Scope Quality](../../data/results/h1_robust_poll_scope_quality.png)

*Visualisiert Mean Brier, Fixed-Bin-ECE, Kalibrierungsbins und Lower-Loss-Zaehler fuer die robusten late Low/Middle-Poll-Distanz-Scopes.*

![H1 Robust Poll-Scope Unit Quality](../../data/results/h1_robust_poll_scope_unit_quality.png)

*Aggregiert die beiden robusten Poll-Scopes zu State-, State-Month-, State-Horizon- und Horizon-Tier-Einheiten, damit der bounded H1-Befund weniger von wiederholten State-Date-Zeilen abhaengt.*

![H1 Poll-Comparison Unit Robustness](../../data/results/h1_poll_comparison_unit_robustness.png)

*Aggregiert den primaeren H1-Poll-Scope zu State-, State-Month-, State-Horizon- und Horizon-Tier-Einheiten; Polymarket wird in allen primaeren Einheiten gestuetzt, waehrend Full-Panel und High-Distance Grenzen bleiben.*

![H1 Direct Poll Loss Decomposition](../../data/results/h1_direct_poll_loss_decomposition.png)

*Zerlegt direkte Poll-Transform-Vergleiche: Polymarket hat den niedrigeren mittleren Brier, obwohl poll-derived Comparatoren mehr Einzel-Faelle gewinnen.*

![H1 Direct Poll State-Cluster Diagnostic](../../data/results/h1_direct_poll_state_cluster_diagnostic.png)

*Prueft direkte Poll-Transform-Vergleiche mit gleichgewichteten State-Clustern: Der mittlere Verlustvorteil bleibt positiv, aber die State-Mehrheit stuetzt poll-derived Comparatoren.*

![H1 Direct Poll Outlier Robustness](../../data/results/h1_direct_poll_outlier_robustness.png)

*Prueft, ob der direkte Poll-State-Cluster-Vorteil nur von einzelnen Ausreissern getragen wird: alle Leave-one-state-out Means bleiben positiv, aber Top-k-Exclusions zeigen Konzentration.*

![H1 Calibration Diagnostic](../../data/results/h1_calibration_diagnostic.png)

*Visualisiert feste Kalibrierungsbins, Mean Brier, ECE und Pairwise-Lower-Loss-Zaehler aus geloesten H1-Fallartefakten.*

![H1 Evidence-Scope Audit](../../data/results/h1_evidence_scope.png)

*Trennt die 194 taeglichen Forecast-Paare von der Anzahl unabhaengiger geloester H1-Outcomes.*

![H1 Expansion-Readiness Audit](../../data/results/h1_expansion_readiness.png)

*Zeigt, dass zusaetzliche Polymarket-Tagespreise ohne kompatible Probability-Forecast-Vergleichsreihe noch keine weiteren H1-Brier-Paare ergeben.*

![H1 Margin-Threshold Readiness](../../data/results/h1_margin_threshold_readiness.png)

*Prueft sieben Trump-State-Margin-Maerkte und zeigt, dass ohne zeitliche Ueberlappung zwischen bewahrten 538-Poll-Averages und CLOB-Historie keine neuen H1-Brier-Faelle entstehen.*

![H1 Final-Snapshot Extension](../../data/results/h1_final_snapshot.png)

*Vergleicht acht geloeste 2024-Final-Snapshot-Outcomes gegen 538 final forecast; kleine Erweiterung, kein Viele-Faelle-Beweis.*

![H1 State-Poll-Snapshot Extension](../../data/results/h1_state_poll_snapshot.png)

*Vergleicht 13 geloeste State-Outcomes gegen eine dokumentiert transformierte 538 Polling-Average-Wahrscheinlichkeit; nicht Rohpoll und kein offizieller 538 State-Forecast.*

![H1 270toWin Polling-Average Extension](../../data/results/h1_270towin_poll_average.png)

*Vergleicht 43 gematchte State-Outcomes gegen eine dokumentiert transformierte 270toWin-Polling-Average-Wahrscheinlichkeit.*

![H1 Popular-Vote Extension](../../data/results/h1_popular_vote.png)

*Vergleicht 51 nationale 538-Poll-Transform-Tageszeilen mit dem Polymarket-Trump-popular-vote-Markt und zeigt einen Gegenbeleg zum starken Claim.*

![H1 State-Date Poll Panel](../../data/results/h1_state_poll_panel.png)

*Vergleicht 1720 gematchte State-Date-Zeilen gegen transformierte 538 Polling-Averages; das groessere Panel spricht gegen den starken Polymarket-Claim.*

![H1 State-Date Poll Panel Temporal Diagnostic](../../data/results/h1_state_poll_panel_temporal_diagnostic.png)

*Zeigt, dass der Vollpanel-Befund gegen Polymarket spricht, waehrend August und September 2024 als diagnostischer Teilbereich Polymarket stuetzen.*

![H1 State-Date Poll Panel Horizon Diagnostic](../../data/results/h1_state_poll_panel_horizon_diagnostic.png)

*Zeigt, dass das <=90-Tage-Forecast-Fenster Polymarket stuetzt, waehrend der Vollpanel-Befund weiter gegen den starken Claim spricht.*

![H1 <=90-Day State-Level Support](../../data/results/h1_state_poll_panel_horizon_state_support.png)

*Aggregiert das <=90-Tage-Fenster auf State-Ebene: Polymarket wird in 8 von 13 States nach mittlerem Brier und Row-Majority gestuetzt.*

![H1 <=90-Day Score Quality](../../data/results/h1_state_poll_panel_near_window_quality.png)

*Visualisiert Mean Brier, Fixed-Bin-ECE, Probability-Separation und lower-loss rows im <=90-Tage-Fenster des State-Date-Panels.*

![H1 Poll-Transform Sensitivity](../../data/results/h1_state_poll_snapshot_sensitivity.png)

*Prueft die State-Poll-Erweiterung ueber MAE-Annahmen von 2.0 bis 10.0 Prozentpunkten, ohne den Parameter auf Outcomes zu fitten.*

![H1 State-Poll Coverage Audit](../../data/results/h1_state_poll_snapshot_coverage.png)

*Zeigt, warum 50 States und 50 Polymarket-State-Maerkte nur 13 valide H1-Brier-Paare mit dem bewahrten 538-Polling-Average-Snapshot ergeben.*

![H1 Rieke 50-State Forecast Extension](../../data/results/h1_rieke_state_forecast.png)

*Vergleicht 50 Polymarket State-Winner-Maerkte mit dem pollbasierten Rieke-Forecast; Polymarket hat niedrigeren mittleren Brier, aber nur in 12 von 50 Einzelstaaten niedrigeren Verlust.*

![H1 270toWin/JHK 50-State Forecast Extension](../../data/results/h1_270towin_state_forecast.png)

*Vergleicht 50 Polymarket State-Winner-Maerkte mit 270toWin/JHK; Polymarket hat niedrigeren mittleren Brier, aber nur in 9 von 50 Einzelstaaten niedrigeren Verlust.*

![H1 State-Source Consensus Diagnostic](../../data/results/h1_state_source_consensus.png)

*Aggregiert bestehende H1-State-Artefakte ueber 156 Source-State-Vergleiche und trennt All-Source-Konsens von direktem Poll-Transform-Konsens.*

![H1 Competitive-State Diagnostic](../../data/results/h1_competitive_state_diagnostic.png)

*Quantilbasierte Diagnose: Polymarket ist in der niedrigsten Distanz-/kompetitivsten Terzile besser, sichere States bleiben Gegenbeleg.*

![H1 State-Date Competitiveness x Horizon](../../data/results/h1_state_poll_panel_competitiveness.png)

*Zeigt, dass Polymarket im <=90-Tage-Fenster bei Low/Middle-Poll-Distanz 262 von 285 State-Date-Zeilen gewinnt, waehrend spaete High-Distance-Zeilen Gegenbeleg bleiben.*

![H1 State-Level Significance Diagnostic](../../data/results/h1_state_poll_panel_state_significance.png)

*Zeigt den exakten State-Level-Sign-Test fuer spaete Low/Middle-Poll-Distanz-Faelle: Polymarket 9 von 9 States, einseitiger p-Wert 0.0020.*

![H2 Event-Window Movement](../../data/results/thesis_h2_event_window_car.png)

*Zeigt taegliche Event-Window-Bewegungen fuer die kuratierten Ereignisse.*

![H3 Wallet-Tier-Verteilung](../../data/results/thesis_h3_wallet_tier_counts.png)

*Zeigt, dass Wallet-Tiers aus der beobachteten Verteilung abgeleitet wurden.*

![H3 Granger-Diagnostik](../../data/results/thesis_h3_granger_pvalues.png)

*Fasst predictive timing diagnostics zusammen, ohne Kausalitaet zu behaupten.*

![Historische Event-Wallet-Anomalien](../../data/results/thesis_h3_event_wallet_anomalies.png)

*Zeigt den pausierten Monitor-Prototyp als deskriptive Review-Schicht.*

![Monitor-v2 Rolling History](../../data/results/monitor_v2_polymarket_rolling_history.png)

*Visualisiert die kurze read-only Polymarket-Monitor-Historie.*

![Swiss Referendum: Polymarket vs Polls](../../data/results/swiss_referendum_10mio_efficiency.png)

*Vergleicht die lokale Polymarket-Wahrscheinlichkeit mit kuratierten Umfragen.*

![Swiss Referendum: Reaction Windows](../../data/results/swiss_referendum_10mio_reaction_windows.png)

*Zeigt beschreibende 1h/6h/24h/48h-Fenster nach Poll-Releases.*

![Swiss Referendum: Information Response](../../data/results/swiss_referendum_10mio_information_response.png)

*Zeigt Richtungsgleichheit zwischen neuer Poll-Signalrichtung und Polymarket-Bewegungen.*
