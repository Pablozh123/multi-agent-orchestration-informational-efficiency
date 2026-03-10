# Requirements: Informationseffizienz dezentraler Pradiktionsmarkte

**Defined:** 2026-03-09
**Core Value:** Das System beweist oder widerlegt empirisch, ob Polymarket informationseffizienter ist als FiveThirtyEight und RCP — messbar via Brier Score, Reaktionsgeschwindigkeit und Whale-Trade-Timing.

## v1 Requirements

### Data Foundation

- [x] **DATA-01**: System ladt historische Polymarket-Preise (Jan-Nov 2024) via CLOB API und cached sie in SQLite — mit strikter Trennung von `price_timestamp` und `fetched_at` zur Vermeidung von Look-ahead Bias
- [x] **DATA-02**: SQLite-Datenbank lauft im WAL-Mode und unterstutzt gleichzeitige Reads durch 3 MCP-Server ohne Datenverlust
- [x] **DATA-03**: System importiert FiveThirtyEight-Modellwahrscheinlichkeiten 2024 (CSV) als tagliche Zeitreihe in `poll_forecasts`
- [x] **DATA-04**: System scrapt oder importiert RealClearPolitics Poll-Averages und transformiert sie mittels Logit-Funktion zu Wahrscheinlichkeiten 0.0-1.0
- [x] **DATA-05**: System ladt Whale-Transaktionen (>$10k) von Dune Analytics via API und filtert bekannte Market-Maker-Adressen heraus
- [x] **DATA-06**: System importiert GDELT-Sentiment-Scores fur US-Election-2024-Keywords (tagliche Granularitat) in `sentiment_scores`
- [x] **DATA-07**: Event-Katalog (`events_timeline`) enthalt mindestens 20 kuratierte Key-Events (Debatten, Umfrage-Schocks, Skandale) mit exakten UTC-Timestamps

### MCP Agent Layer

- [ ] **AGENT-01**: Market Agent (FastMCP, Port 8001) stellt Tools bereit: Preisabfrage nach Zeitraum, Anomalie-Detection (Z-Score >3), Volumen-Aggregation
- [ ] **AGENT-02**: Sentiment Agent (FastMCP, Port 8002) stellt Tools bereit: GDELT-Sentiment-Score nach Datum, Sentiment-Trend uber Zeitfenster
- [ ] **AGENT-03**: Whale Agent (FastMCP, Port 8003) stellt Tools bereit: Grosse Trades nach Zeitraum, Wallet-Aktivitats-Timeline, Trade-vor-Event-Analyse

### Analysis — H1: Brier Score and Kalibrierung

- [ ] **H1-01**: System berechnet Brier Score Zeitreihe (tagliche / wochentliche Fenster) fur Polymarket, FiveThirtyEight und RCP uber den gesamten Analysezeitraum
- [ ] **H1-02**: System generiert Kalibrierungskurven (Reliability Diagrams) fur alle drei Quellen in einem vergleichbaren Plot
- [ ] **H1-03**: System berechnet Diebold-Mariano Test auf statistische Signifikanz der Brier-Score-Differenzen zwischen den Quellen
- [ ] **H1-04**: System berechnet naive Baseline-Modelle (50%-Modell und Vortages-Preis) als untere Benchmark

### Analysis — H2: Informationsintegrations-Geschwindigkeit

- [ ] **H2-01**: Event-Fenster fur alle Analysen sind vor Code-Schreibung schriftlich dokumentiert (+-1h, +-6h, +-24h) zur P-Hacking-Pravention
- [ ] **H2-02**: System berechnet Cumulative Abnormal Returns (CAR) um kuratierte Events fur Polymarket
- [ ] **H2-03**: System vergleicht Reaktionszeit (Zeit bis 50% der finalen Preisbewegung) zwischen Polymarket und FiveThirtyEight/RCP uber den Event-Katalog

### Analysis — H3: Whale Alpha

- [ ] **H3-01**: System identifiziert Whale-Trade-Cluster (>$10k, nicht Market-Maker) in einem definierten Zeitfenster vor signifikanten Preisbewegungen (>5%)
- [ ] **H3-02**: System berechnet Granger-Kausalitats-Tests: Whale-Volumen als Pradiktor fur Polymarket-Preisbewegungen
- [ ] **H3-03**: System generiert Lead-Time-Histogramme: Verteilung der Zeitdifferenz Whale-Trade -> Preisbewegung

### Orchestrator and Reporting

- [ ] **ORC-01**: Orchestrator koordiniert alle drei MCP-Server via Claude API (Anthropic SDK) und aggregiert ihre Outputs fur qualitative Fallbeispiel-Analyse
- [ ] **ORC-02**: Orchestrator erkennt Divergenz-Signale: Wenn Polymarket-Preis >10% von Sentiment-Score-Implikation abweicht, wird ein Analyse-Run ausgelost
- [ ] **VIS-01**: System generiert thesis-fahige Visualisierungen (matplotlib, DPI>=300, LaTeX-kompatible Fonts): Brier-Score-Zeitreihe, Reliability Diagrams, Event-Study-Plot, Whale-Lead-Time-Histogramm

## v2 Requirements

### Erweiterte Datenquellen

- **V2-01**: Reddit/PRAW Sentiment-Integration (abhangig von API-Restriktions-Klarung)
- **V2-02**: NewsAPI Integration fur strukturiertere Nachrichtensuche
- **V2-03**: Ausweitung auf andere Polymarket-Markte aus 2024 fur grossere Stichprobe

### Erweiterte Analyse

- **V2-04**: Murphy-Score-Dekomposition (Reliability, Resolution, Uncertainty)
- **V2-05**: Sub-Markt-Analyse (Swing States, Senate Races) fur N-Erhohung
- **V2-06**: Automatische Event-Detection aus Preis-Anomalien (erganzend zu manuellem Katalog)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Copy-Trading-System | Bachelorarbeit, kein Produktionssystem — konzeptionell in Thesis erwahnt |
| Live-Trading / Real-Money | Reine historische Analyse |
| Echtzeit-Dashboard | Batch-Analyse reicht fur Thesis |
| Allgemeine Marktanalyse | Fokus: nur US-Prasidentschaftswahl 2024 |
| Reddit/PRAW in v1 | API-Restriktionen post-2023 unklar; GDELT deckt News-Sentiment ab |
| NewsAPI in v1 | GDELT ausreichend fur akademische Zwecke, ein Sentiment-Signal reicht |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| DATA-06 | Phase 1 | Complete |
| DATA-07 | Phase 1 | Complete |
| AGENT-01 | Phase 2 | Pending |
| AGENT-02 | Phase 2 | Pending |
| AGENT-03 | Phase 2 | Pending |
| H1-01 | Phase 3 | Pending |
| H1-02 | Phase 3 | Pending |
| H1-03 | Phase 3 | Pending |
| H1-04 | Phase 3 | Pending |
| H2-01 | Phase 4 | Pending |
| H2-02 | Phase 4 | Pending |
| H2-03 | Phase 4 | Pending |
| H3-01 | Phase 4 | Pending |
| H3-02 | Phase 4 | Pending |
| H3-03 | Phase 4 | Pending |
| ORC-01 | Phase 5 | Pending |
| ORC-02 | Phase 5 | Pending |
| VIS-01 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 — full coverage

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 — traceability populated after roadmap creation*
