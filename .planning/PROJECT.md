# Informationseffizienz dezentraler Prädiktionsmärkte

## What This Is

Multi-Agent-System zur empirischen Analyse der informationellen Effizienz von Polymarket
im Vergleich zu FiveThirtyEight und RealClearPolitics, am Fallbeispiel der US-Präsidentschaftswahl 2024.
Das System sammelt, verarbeitet und analysiert Daten aus fünf Quellen über drei spezialisierte
MCP-Server und einen Orchestrator, der Claude API Calls koordiniert.

## Core Value

Das System beweist oder widerlegt empirisch, ob dezentrale Prädiktionsmärkte informationseffizienter
sind als traditionelle Prognosemodelle — messbar via Brier Score, Informationsintegrations-Geschwindigkeit
und Whale-Trade-Timing.

## Forschungshypothesen

1. **H1 — Effizienz**: Polymarket hat einen niedrigeren Brier Score als FiveThirtyEight und RCP
   über den Zeitraum Jan–Nov 2024.
2. **H2 — Reaktionsgeschwindigkeit**: Polymarket-Preise integrieren neue Informationen
   (News-Events, Debatten, Skandale) schneller als Umfrage-basierte Modelle.
3. **H3 — Whale Alpha**: Grosse Wallets (>$10k pro Trade) handeln systematisch VOR
   signifikanten Preisbewegungen — Whale-Aktivität als Vorlauf-Indikator.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Data Ingestion Pipeline: Polymarket API, Dune Analytics, FiveThirtyEight CSVs, GDELT, Reddit
- [ ] Market Agent MCP-Server (Port 8001): Preisanalyse, Anomalien, Volumen
- [ ] Sentiment Agent MCP-Server (Port 8002): News/Social-Sentiment-Scores
- [ ] Whale Tracking Agent MCP-Server (Port 8003): Blockchain-Analyse, grosse Wallets
- [ ] Orchestrator: Koordination der Agenten, Divergenz-Erkennung, Claude API
- [ ] Brier Score Berechnung und Kalibrierungskurven für alle drei Quellen
- [ ] Event-Reaktionszeit-Analyse (Informationsintegrations-Geschwindigkeit)
- [ ] Whale-Trade-Timing-Analyse (vor/nach Preisbewegungen)
- [ ] Visualisierungen für Thesis (matplotlib/seaborn)
- [ ] Statistischer Bericht mit Fallbeispielen

### Out of Scope

- Copy-Trading-System — konzeptionell erwähnt, aber nicht implementiert (kein Produktionssystem)
- Live-Trading oder Real-Money-Transaktionen — reine Analyse
- Andere Wahlen/Märkte als US-Präsidentschaftswahl 2024 — Fokus bewusst begrenzt
- Echtzeit-Dashboard — Batch-Analyse reicht für Thesis

## Context

- **Zeitraum**: Januar bis November 2024 (US-Wahljahr)
- **Datenlage**: Alles noch zu sammeln — Pipeline zuerst aufbauen
- **Thesis-Typ**: Bachelorarbeit — kein Produktionssystem, akademische Rigidität wichtiger als Skalierung
- **Datenbank**: SQLite (data/thesis.db) für gecachte API-Responses + DuckDB für Analytik
- **API-Responses immer cachen**: Nie live in Analyse, alles erst in SQLite
- **Schweizer Schreibweise**: "ss" statt "ß" im gesamten Code

## Constraints

- **Tech Stack**: Python 3.12, FastMCP >=3.0, Anthropic SDK — nicht verhandelbar
- **Datenbank**: SQLite + DuckDB — kein Postgres, kein externe DB
- **API-Caching**: Alle externen Calls müssen in SQLite gecacht werden (Rate-Limits, Reproduzierbarkeit)
- **Zeitstempel**: IMMER UTC (ISO 8601)
- **Thesis-Deadline**: Akademisches Semester 2025/26 — kein endloser Scope-Creep

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastMCP für MCP-Server | Standardisierte Agent-Kommunikation, erweiterbar | — Pending |
| SQLite statt Postgres | Kein Server nötig, einfach portable für Thesis | — Pending |
| DuckDB für Analytik | Columnar queries auf grossen Zeitreihen viel schneller | — Pending |
| Dune Analytics für Whale-Daten | Polygon-Blockchain direkt zu komplex, Dune hat fertige Queries | — Pending |
| Copy-Trading nur konzeptionell | Bachelorarbeit, kein Produktionssystem | ✓ Good |

---
*Last updated: 2026-03-09 after initialization*
