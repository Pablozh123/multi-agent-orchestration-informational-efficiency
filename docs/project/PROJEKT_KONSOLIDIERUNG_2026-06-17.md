# Projekt-Konsolidierung — Stand 2026-06-17

Kurzer Gesamtüberblick: wo das Projekt steht, Antworten auf vier offene Fragen
und eine priorisierte Roadmap.

## 1. Wo wir stehen

**Empirischer Kern (fertig, getestet):** H1 (Brier/Diebold-Mariano), H2
(Ereignisfenster), H3 (Wallet-Tiers, Granger, Anomalie-Diagnostik,
Informed-Trading-Signatur), Monitor und Schweizer Fallstudie. Alle Kennzahlen
deterministisch in Python berechnet.

**Thesis-Rohbau:** 9 Kapitel, zusammen rund 4'300 Wörter. Kapitel 1 (Einleitung)
und 2 (Theorie) sind voll FHNW-konform ausgeschrieben. Dünn sind noch H2 (~220),
Diskussion (~280) und Ausblick (~35 Wörter). Ziel der Wegleitung: 50–80 Seiten,
also muss der Fliesstext deutlich wachsen — vor allem durch Grafik-Auswertung und
die dünnen Kapitel.

**Formales (steht):** FHNW-Regeln gespeichert, Word-Vorlage befüllt, Zotero-Pfad
definiert. Das Word-Dokument `thesis/Bachelorarbeit_FHNW.docx` ist generiert
(Arial 11, Blocksatz, Verzeichnisse, APA-Kurzbelege, Hilfsmittelverzeichnis-Entwurf).

**Quellen:** 15 Kerntitel in `references.bib`. Der manuelle Quellen-Review ist
noch offen (11 Einträge `final_citation_ready = FALSE`).

**Website (Produkt):** 9 read-only Dashboards in `data/results/` (Monitor v2,
Anomalie-Review, Detection-Backtest, Referenz-Kandidaten + Sensitivität,
Wallet-Graph, Wallet-Referenz-Similarity, Schweizer Referendum, Agenten-Review-Queue).

**Agenten-Tool:** Stufen 1–3 implementiert — Signatur-Modul, read-only MCP-Schicht
und die vier Review-Agenten in `operations/agents/review_queue/` (8 Dateien) plus
der Generator `agent_review_queue_dashboard.py`.

**Git:** alles committet, aktuell 12 Commits vor `origin/main` (Push von deiner Maschine).

## 2. Antworten auf die vier Fragen

**(Q1) Grafik-Interpretationen — Codex-Auftrag oder nicht?**
Aufteilen. Die **Figur-Qualität** (Entzerrung, Label-Überlappung) ist ein
deterministischer Matplotlib-Job → **Codex** (Auftrag `figure-quality-pass-001`
ist bereits formuliert). Die **Interpretation** (was zeigt die Grafik, Lesart,
Grenzen) ist Schreibarbeit aus den getesteten Zahlen → **das mache ich**, direkt
in die Kapitel H1–H3 und kondensiert in den Dozentenbericht. Also kein
Codex-Auftrag für die Interpretation.

**(Q2) Multiagenten-Orchestrierung — wo kommt sie vor, mehr machen?**
Sie erscheint an drei Stellen: (a) als **lauffähiges Tool** (der separate
Website-Teil: `operations/agents/review_queue` + Agenten-Review-Queue-Dashboard),
(b) in der **Thesis als Sekundär-/Prozessbeitrag** (Kapitel 7 Erweiterungen und
Kapitel 9 Ausblick) und (c) in den **Design-Docs** (AGENT_TOOL_BLUEPRINT,
Pipeline-Roadmap). Empfehlung: inhaltlich **nicht** als empirischen Teil ausweiten
(Guardrails — die Agenten berechnen keine Kennzahlen). Stattdessen Kapitel 7 sauber
ausschreiben (Bau-Methodik als Prozessbeitrag) und die veraltete Formulierung
„nicht implementiert / Future Work" in Kapitel 7 und 9 an die jetzt umgesetzte
Realität anpassen. Mehr „machen" heisst hier dokumentieren, nicht mehr Code.

**(Q3) Website-Inhalte auflisten und erklären — wohin?**
In **Kapitel 7 (Erweiterungen)**, wo Monitor und praktischer Beitrag schon stehen.
Vorschlag: eine knappe Unterüberschrift „Inhalt des Webprodukts" mit einer Liste
der Dashboards und ihrem Zweck, je ein Screenshot in den **Anhang**. Schreibe ich.

**(Q4) Reichen die Quellen?**
Die 15 Kerntitel decken Theorie (Effizienz, Aggregation), Methodik (Brier,
Diebold-Mariano, Ereignisstudien, Granger, Kyle) und Polymarket-Evidenz ab — eine
solide Basis, aber für ein BA-Literatur-Review eher am unteren Rand (üblich sind
grob 20–40). Wichtiger als die Menge: der **Review der vorhandenen 15 ist noch
offen** und hat Priorität. Danach gezielt ~5–10 ergänzen (Prognosemarkt-Effizienz-
Klassiker, Wisdom of Crowds, Forecast-Kalibrierung, neuere 2024-Wahlmarkt-Studien),
Qualität vor Menge. Jede neue Quelle läuft über den Review-Prozess.

## 3. Priorisierte Roadmap

- **A. Inhalt vertiefen (grösster Hebel, ich):** Grafik-Interpretationen plus die
  dünnen Kapitel (H2, Diskussion, Ausblick) ausschreiben. Bringt Umfang und Qualität.
- **B. Figur-Qualität (Codex):** Auftrag `figure-quality-pass-001` ausführen.
- **C. Kapitel 7 (ich):** Webprodukt-Inhalt und Multiagenten-Prozessbeitrag
  dokumentieren, Formulierung 7/9 an die Umsetzung anpassen.
- **D. Quellen (du + ich):** Review der 15 abschliessen, dann gezielt ergänzen.
- **E. Formales (du + ich):** Titelseiten-Felder, Hilfsmittelverzeichnis je
  Textstelle, Management Summary verfassen.

Empfohlener nächster Schritt: **A** — ich beginne mit den Grafik-Interpretationen
und den dünnen Kapiteln, parallel kann Codex **B** laufen lassen.
