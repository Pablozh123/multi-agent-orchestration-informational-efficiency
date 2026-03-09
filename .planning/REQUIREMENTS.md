# Requirements: Informationseffizienz dezentraler Prädiktionsmärkte

**Defined:** 2026-03-09
**Core Value:** Das System beweist oder widerlegt empirisch, ob Polymarket informationseffizienter ist als FiveThirtyEight und RCP — messbar via Brier Score, Reaktionsgeschwindigkeit und Whale-Trade-Timing.

## v1 Requirements

### Data Foundation

- [ ] **DATA-01**: System lädt historische Polymarket-Preise (Jan–Nov 2024) via CLOB API und cached sie in SQLite — mit strikter Trennung von `price_timestamp` und `fetched_at` zur Vermeidung von Look-ahead Bias
- [ ] **DATA-02**: SQLite-Datenbank läuft im WAL-Mode und unterstützt gleichzeitige Reads durch 3 MCP-Server ohne Datenverlust
- [ ] **DATA-03**: System importiert FiveThirtyEight-Modellwahrscheinlichkeiten 2024 (CSV) als tägliche Zeitreihe in `poll_forecasts`
- [ ] **DATA-04**: System scrapt oder importiert RealClearPolitics Poll-Averages und transformiert sie mittels Logit-Funktion zu Wahrscheinlichkeiten 0.0–1.0
- [ ] **DATA-05**: System lädt Whale-Transaktionen (>$10k) von Dune Analytics via API und filtert bekannte Market-Maker-Adressen heraus
- [ ] **DATA-06**: System importiert GDELT-Sentiment-Scores für US-Election-2024-Keywords (tägliche Granularität) in `sentiment_scores`
- [ ] **DATA-07**: Event-Katalog (`events_timeline`) enthält mindestens 20 kuratierte Key-Events (Debatten, Umfrage-Schocks, Skandale) mit exakten UTC-Timestamps

### MCP Agent Layer

- [ ] **AGENT-01**: Market Agent (FastMCP, Port 8001) stellt Tools bereit: Preisabfrage nach Zeitraum, Anomalie-Detection (Z-Score >3), Volumen-Aggregation
- [ ] **AGENT-02**: Sentiment Agent (FastMCP, Port 8002) stellt Tools bereit: GDELT-Sentiment-Score nach Datum, Sentiment-Trend über Zeitfenster
- [ ] **AGENT-03**: Whale Agent (FastMCP, Port 8003) stellt Tools bereit: Grosse Trades nach Zeitraum, Wallet-Aktivitäts-Timeline, Trade-vor-Event-Analyse

### Analysis — H1: Brier Score & Kalibrierung

- [ ] **H1-01**: System berechnet Brier Score Zeitreihe (tägliche / wöchentliche Fenster) für Polymarket, FiveThirtyEight und RCP über den gesamten Analysezeitraum
- [ ] **H1-02**: System generiert Kalibrierungskurven (Reliability Diagrams) für alle drei Quellen in einem vergleichbaren Plot
- [ ] **H1-03**: System berechnet Diebold-Mariano Test auf statistische Signifikanz der Brier-Score-Differenzen zwischen den Quellen
- [ ] **H1-04**: System berechnet naive Baseline-Modelle (50%-Modell und Vortages-Preis) als untere Benchmark

### Analysis — H2: Informationsintegrations-Geschwindigkeit

- [ ] **H2-01**: Event-Fenster für alle Analysen sind vor Code-Schreibung schriftlich dokumentiert (±1h, ±6h, ±24h) zur P-Hacking-Prävention
- [ ] **H2-02**: System berechnet Cumulative Abnormal Returns (CAR) um kuratierte Events für Polymarket
- [ ] **H2-03**: System vergleicht Reaktionszeit (Zeit bis 50% der finalen Preisbewegung) zwischen Polymarket und FiveThirtyEight/RCP über den Event-Katalog

### Analysis — H3: Whale Alpha

- [ ] **H3-01**: System identifiziert Whale-Trade-Cluster (>$10k, nicht Market-Maker) in einem definierten Zeitfenster vor signifikanten Preisbewegungen (>5%)
- [ ] **H3-02**: System berechnet Granger-Kausalitäts-Tests: Whale-Volumen als Prädiktor für Polymarket-Preisbewegungen
- [ ] **H3-03**: System generiert Lead-Time-Histogramme: Verteilung der Zeitdifferenz Whale-Trade → Preisbewegung

### Orchestrator & Reporting

- [ ] **ORC-01**: Orchestrator koordiniert alle drei MCP-Server via Claude API (Anthropic SDK) und aggregiert ihre Outputs für qualitative Fallbeispiel-Analyse
- [ ] **ORC-02**: Orchestrator erkennt Divergenz-Signale: Wenn Polymarket-Preis >10% von Sentiment-Score-Implikation abweicht, wird ein Analyse-Run ausgelöst
- [ ] **VIS-01**: System generiert thesis-fähige Visualisierungen (matplotlib, DPI≥300, LaTeX-kompatible Fonts): Brier-Score-Zeitreihe, Reliability Diagrams, Event-Study-Plot, Whale-Lead-Time-Histogramm

## v2 Requirements

### Erweiterte Datenquellen

- **V2-01**: Reddit/PRAW Sentiment-Integration (abhängig von API-Restriktions-Klärung)
- **V2-02**: NewsAPI Integration für strukturiertere Nachrichtensuche
- **V2-03**: Ausweitung auf andere Polymarket-Märkte aus 2024 für grössere Stichprobe

### Erweiterte Analyse

- **V2-04**: Murphy-Score-Dekomposition (Reliability, Resolution, Uncertainty)
- **V2-05**: Sub-Markt-Analyse (Swing States, Senate Races) für N-Erhöhung
- **V2-06**: Automatische Event-Detection aus Preis-Anomalien (ergänzend zu manuellem Katalog)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Copy-Trading-System | Bachelorarbeit, kein Produktionssystem — konzeptionell in Thesis erwähnt |
| Live-Trading / Real-Money | Reine historische Analyse |
| Echtzeit-Dashboard | Batch-Analyse reicht für Thesis |
| Allgemeine Marktanalyse | Fokus: nur US-Präsidentschaftswahl 2024 |
| Reddit/PRAW in v1 | API-Restriktionen post-2023 unklar; GDELT deckt News-Sentiment ab |
| NewsAPI in v1 | GDELT ausreichend für akademische Zwecke, ein Sentiment-Signal reicht |

## Traceability

Wird bei Roadmap-Erstellung befüllt.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| DATA-05 | — | Pending |
| DATA-06 | — | Pending |
| DATA-07 | — | Pending |
| AGENT-01 | — | Pending |
| AGENT-02 | — | Pending |
| AGENT-03 | — | Pending |
| H1-01 | — | Pending |
| H1-02 | — | Pending |
| H1-03 | — | Pending |
| H1-04 | — | Pending |
| H2-01 | — | Pending |
| H2-02 | — | Pending |
| H2-03 | — | Pending |
| H3-01 | — | Pending |
| H3-02 | — | Pending |
| H3-03 | — | Pending |
| ORC-01 | — | Pending |
| ORC-02 | — | Pending |
| VIS-01 | — | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 23 ⚠️

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after initial definition*
