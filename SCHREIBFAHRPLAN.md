# Schreibfahrplan: von Quellen + Artefakten zur fertigen BA

Datum: 2026-06-16
Zweck: Wie wir aus den vorhandenen Quellen und deterministischen Artefakten den
BA-Text sauber schreiben — ohne neues System, mit dem, was schon da ist.

---

## Kernbotschaft

Dir fehlt **keine Methodik und keine Maschinerie**. Beides existiert bereits und
ist gut. Der Engpass ist nur zweierlei: (1) das **manuelle Quellen-Review** und
(2) das **tatsaechliche Ausschreiben** der Kapitel. Beides ist Handarbeit, kein
Tooling-Problem.

---

## Was du schon hast (nicht neu bauen)

| Asset | Datei | Rolle |
| --- | --- | --- |
| Kapitel-Skelett (9 Kapitel) | `docs/research/THESIS_CHAPTER_DRAFT.md` | Struktur + erste Prosa-Seeds |
| Schreib-Blueprint | `docs/research/THESIS_WRITING_BLUEPRINT.md` | pro Kapitel: Status, Evidence-IDs, fertige Ergebnis-Saetze **mit Zahlen + Quell-Artefakt**, Limitation, naechster Schritt |
| Reihenfolge + Freigaben | `data/results/thesis_drafting_sequence.csv` | 10 Schritte, je mit `draft_permission` (write_now vs. blocked) |
| Claim-zu-Beleg-Bindung | `data/results/thesis_evidence_map.csv` | jeder Claim -> Artefakt -> Quelle -> erlaubte/verbotene Formulierung |
| Quellen-Ledger (24 Zeilen, alle pending) | `data/results/thesis_source_review_progress_ledger.csv` | der eigentliche Engpass (siehe unten) |
| Tabellen/Figuren-Captions | `data/results/thesis_table_figure_captions.csv` | 5 Kern-Tabellen, 4 Kern-Figuren, fertige Captions |

Heisst: Fuer fast jeden Absatz ist Zahl, Quell-Artefakt und erlaubte Formulierung
**schon vorbereitet**. Du schreibst Prosa drumherum, nicht von Null.

---

## Der saubere Schreibloop (pro Absatz)

Diese 5 Schritte sind die ganze "Sauberkeit". Sie stammen direkt aus der Core
Writing Rule des Blueprints:

1. **Abschnitt waehlen** aus `thesis_drafting_sequence.csv` — nur Zeilen mit
   `draft_permission = write_now_bounded` anfassen.
2. **Aussage + Beleg ziehen** aus dem Blueprint: dort steht der fertige
   Ergebnis-Satz inkl. Zahl und Quell-Artefakt (z.B. "262/285 State-Date-Zeilen,
   Quelle `h1_poll_claim_readiness_summary.csv`").
3. **Prosa schreiben** in Schweizer Deutsch (ss, kein scharfes s), gebunden an
   genau ein Artefakt oder eine `evidence_id`.
4. **Quelle zitieren** — nur Quellen mit Status `reviewed`/`cited`. Solange eine
   Quelle `skimmed`/`pending` ist: Platzhalter setzen, nicht final zitieren.
5. **Wording-Guard pruefen:** die `must_not_claim`-Spalte der Sequenz einhalten
   (keine universelle Effizienz, keine Intraday-Speed, keine Granger-Kausalitaet,
   keine RCP-Wahrscheinlichkeit ohne dokumentierte Transformation, keine
   Profitabilitaet).

Faustregel des Blueprints: **Jeder Ergebnis-Absatz nennt ein Artefakt. Jeder
Methoden-Absatz nennt die Methodenquelle.**

---

## Reihenfolge (was jetzt schreibbar ist)

Aus `thesis_drafting_sequence.csv`:

- **Sofort schreibbar** (`write_now_bounded`): Methodik-Kapitel (Schritt 2),
  H1-Ergebnisse (3), H2/H3-Ergebnisse (4), Tabellen/Figuren-Integration (5),
  Swiss-Fallstudie (7).
- **Blockiert bis Quellen-Review** (`final_blocked`): Theorie/Literatur (Schritt
  1) — kann inhaltlich entworfen, aber **nicht final zitiert** werden.
- **Nur als Ausblick** (`future_work_only`): Agenten-Pipeline (Schritt 8) — hier
  greift deine neue Entscheidung, siehe unten.

Konkrete Startempfehlung: **Kapitel 3 (Daten und Methodik)** zuerst — Status
`draft_ready`, voll schreibbar, und es traegt alle drei Hypothesen.

---

## Der echte Engpass: manuelles Quellen-Review

24 Ledger-Zeilen stehen auf `pending`, davon **11 Priority-1-Methodenquellen**
(z.B. Brier 1950, Diebold-Mariano 1995, MacKinlay 1997, die Polymarket-Paper). Es
gibt **bewusst kein Skript**, das Status automatisch hochstuft — das schuetzt die
wissenschaftliche Integritaet.

- **Nur du kannst:** das relevante PDF/Kapitel lesen und im Ledger
  `page_or_section_note`, `claim_support_decision`, `reviewed_by`, `reviewed_at`
  eintragen. Erst dann `status` in `literature_index.csv` auf `reviewed`/`cited`.
- **Ich kann:** pro Quelle die Review-Zeile vorbereiten (welcher Claim haengt
  dran, welche Formulierung ist erlaubt/verboten, welche Seite du suchen musst),
  damit dein Lesen 10 Minuten statt einer Stunde dauert.
- **Gesperrt:** `zotero_poly_004` (EMH.pdf) ist `rejected` — nicht zitieren.

---

## Deine zwei Narrativ-Entscheidungen — sauber eingebaut

Beide sind akademisch tragfaehig, wenn sie **an die Forschungsfrage gebunden**
und vom empirischen Kern **getrennt** bleiben.

**1. Website als Produkt-Ergebnis.** Rahmen: waehrend der Effizienz-Untersuchung
wurde Bedarf an einem Monitoring-Werkzeug erkannt; die Website operationalisiert
die Befunde (H1-H3, Anomalie-Monitor) in ein laufendes, read-only Produkt. Das ist
ein **Gestaltungs-/Praxisbeitrag** (Design-Science-Artefakt), nicht der Kernbeweis.
Gehoert in **Kapitel 7 (Erweiterungen)** plus kurze Erwaehnung in der Diskussion.

**2. Agenten-Pipeline als Bau-Methode.** Rahmen: die Multiagenten-Orchestrierung
wurde zur **Umsetzung der Website** genutzt; dokumentiert wird die **Methodik**
(wie ein Agenten-Workflow das Artefakt gebaut hat). Das ist ein **Prozess-/
Methodenbeitrag** — und es verletzt die Kernregel nicht, weil die Agenten Software
gebaut, aber **keine Statistik gerechnet** haben. Hebt **Kapitel 9** vom reinen
"Ausblick" zu einem dokumentierten Methodenkapitel. Vorhandene Grundlage:
`docs/research/STRATEGY_AGENT_ARCHITECTURE.md` und die
`THESIS_AGENT_PIPELINE_*`-Dokumente.

**Caveat (wichtig):** Eine BA zur informationellen Effizienz hat ihren Kern in
H1-H3. Website und Agenten-Methodik sind **Sekundaerbeitraege** — sie duerfen die
Forschungsfrage nicht verwaessern. Beide Punkte mit dem Dozenten bestaetigen
(Schritt `draft_09_advisor_iteration`), bevor du viel Text investierst; laut
Projektgedaechtnis schaetzt er innovative Arbeit, also stehen die Chancen gut.

---

## Zielsetup zum Schreiben

Laut Projektgedaechtnis: **Overleaf (LaTeX) + Zotero mit Better BibTeX**. Sinnvoll,
weil:

- Better BibTeX synct die `reviewed` Zotero-Quellen automatisch in die `.bib`.
- Figuren liegen als PNG in `data/results/` (nicht in `thesis/figures/`, das ist
  leer) — beim Einbau Pfade pruefen.
- Captions 1:1 aus `thesis_table_figure_captions.csv` uebernehmen.

Hinweis: Im Repo gibt es noch **keine `.tex`-Dateien**. Erster Setup-Schritt waere
ein Overleaf-Projekt mit Kapitelstruktur aus `THESIS_CHAPTER_DRAFT.md`.

---

## Was ich als Naechstes fuer dich tun kann

- **Kapitel 3 (Methodik) als ersten echten Entwurf** schreiben — gebunden an
  Evidence-Map und Artefakte, in Schweizer Deutsch, zitierfertig mit Platzhaltern.
- **Die 11 Priority-1-Review-Zeilen vorbereiten**, damit dein PDF-Lesen schnell geht.
- **RCP-Note in literature_index + evidence_map registrieren** (siehe
  `docs/research/RCP_TRANSFORMATION.md`).
- **Overleaf-Grundgerust** (LaTeX-Kapiteldateien + `.bib`-Stub) anlegen.

Sag, womit ich starten soll.
