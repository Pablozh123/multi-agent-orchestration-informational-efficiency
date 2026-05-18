---
name: dune-analytics
description: Dune Analytics für Blockchain-Daten. Nutze bei Whale-Tracking, Polygon-Transaktionen, On-Chain-Analyse.
---

# Dune Analytics

## API Workflow
1. Query erstellen/finden auf dune.com
2. Ausführen: POST https://api.dune.com/api/v1/query/{id}/execute
3. Status prüfen: GET https://api.dune.com/api/v1/execution/{execution_id}/status
4. Ergebnisse: GET https://api.dune.com/api/v1/execution/{execution_id}/results
5. CSV exportieren und in SQLite laden

## Auth
- Header: x-dune-api-key: {DUNE_API_KEY}
- Free Tier: 2.500 Credits/Monat

## Nützliche Community Queries
- Polymarket Top Wallets by Volume
- Large Trades (>$10k) Timeline
- Eigene Queries: SQL auf Polygon-Daten

## Kostenoptimierung
- Queries auf Dune Website entwickeln (kostenlos)
- Nur finale Queries via API ausführen
- Ergebnisse in SQLite cachen
