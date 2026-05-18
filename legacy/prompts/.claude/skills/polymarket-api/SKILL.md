---
name: polymarket-api
description: Polymarket API Referenz. Nutze bei Fragen zu Polymarket, Gamma API, CLOB, Märkten, Preisen, Trades.
---

# Polymarket API

## Gamma API (einfacher Einstieg)
- Base URL: https://gamma-api.polymarket.com
- GET /markets — Alle Märkte auflisten
- GET /markets/{id} — Einzelner Markt mit Metadaten
- Keine Authentifizierung nötig

## CLOB API (granularer)
- Base URL: https://clob.polymarket.com
- GET /markets — Märkte mit Condition IDs
- GET /prices — Aktuelle Preise
- Keine Auth für Read-Only

## Datenmodell
- Preise: 0.0 bis 1.0 (implizite Wahrscheinlichkeit)
- Condition ID: Verknüpft Markt mit On-Chain CTF Token
- Token ID: Spezifischer Token (YES/NO Outcome)

## Rate Limits
- Inoffiziell ~10 req/sec, konservativ 5 req/sec nutzen
- Responses in SQLite cachen, nicht wiederholt abrufen
