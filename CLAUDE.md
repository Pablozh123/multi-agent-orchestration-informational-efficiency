# BA-Thesis: Informationseffizienz dezentraler Prädiktionsmärkte

## Projektübersicht
Multi-Agent-System zur Analyse der informationellen Effizienz von Polymarket
im Vergleich zu traditionellen Prognose-Quellen (FiveThirtyEight, RealClearPolitics).
Primäre Fallstudie: US-Präsidentschaftswahl 2024.

## Tech-Stack
- Python 3.11+, FastMCP, Anthropic SDK
- Datenbank: SQLite (data/thesis.db) + DuckDB für Analytik
- Visualisierung: matplotlib + seaborn

## Architektur
- MCP-Server (FastMCP) in mcp_servers/
  - market_agent/: Polymarket-Preisdaten, Anomalien, Volumen
  - sentiment_agent/: GDELT, Reddit, NewsAPI → Sentiment-Scores
  - whale_agent/: Polygon Blockchain, grosse Wallets, Trade-Timing
  - orchestrator/: Koordination, Divergenz-Erkennung, Claude API Calls
- Analyse-Scripts in analysis/
- Tests in tests/

## Konventionen
- Type Hints auf JEDER Funktion
- Docstrings auf Deutsch (akademisch)
- Code-Kommentare auf Englisch
- Immer "ss" statt "ß" (Schweizer Schreibweise)
- API-Responses IMMER in SQLite cachen, nie live in Analyse nutzen
- .env für alle API Keys, NIEMALS hardcoden
- pytest für Tests, Fixtures für API-Mocks

## Wichtige Dateien
- data/thesis.db — SQLite Hauptdatenbank
- .env — API Keys (NICHT committen)
- requirements.txt — Python Dependencies

## Regeln
- Zeitstempel IMMER in UTC (ISO 8601)
- Blockchain-Adressen IMMER lowercase
- Polymarket-Preise: 0.0 bis 1.0 (implizite Wahrscheinlichkeiten)
- Brier Score: 0 = perfekt, 1 = maximal falsch
- Commits auf Englisch, atomare Messages

## Python-Umgebung
- venv in .venv/ — vor dem Arbeiten aktivieren: source .venv/bin/activate
- Packages installieren: pip install -r requirements.txt
