# CLAUDE.md — Prompt Contract v2.1

> Bachelorarbeit: "Informationelle Effizienz dezentraler Prognosemärkte (Polymarket)
> im Vergleich zu traditionellen Prognosequellen (FiveThirtyEight, RealClearPolitics)"
>
> Letzte Revision: 2026-04-09
> Status: ENTWURF — wartet auf Freigabe

---

## 1. Ziel & Forschungsfragen

Analyse der informationellen Effizienz von Polymarket als dezentralem Prognosemarkt
im Vergleich zu traditionellen Forecasting-Quellen. Case Study: US-Präsidentschaftswahl 2024.

**Hypothesen:**
- **H1 (Brier Score):** Polymarket liefert kalibriertere Prognosen als FiveThirtyEight/RCP
- **H2 (Informationsintegration):** Polymarket integriert neue Informationen schneller
  (Event-Windows, Cumulative Abnormal Returns)
- **H3 (Whale Alpha):** Grosse Wallet-Adressen handeln systematisch vor Preisbewegungen
  (Granger-Kausalität, Lead-Time-Histogramme)

**Zentraler Hook:** Trump/Polymarket-Divergenz; Whale-Wallet-Tracking als potenzielle
Alpha-/Insider-Signal-Quelle.

---

## 2. Architektur

### 2.1 Topologie: Hub-and-Spoke mit Pydantic AI

```
                    ┌──────────────────────┐
                    │   Orchestrator       │
                    │   (Sonnet 4.6)       │
                    │   asyncio.gather()   │
                    └──┬────────┬────────┬─┘
                       │        │        │
              ┌────────┘        │        └────────┐
              ▼                 ▼                 ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Market Agent│  │ Sentiment   │  │ Whale Agent │
    │ (Haiku 4.5) │  │ Agent       │  │ (Haiku 4.5) │
    │             │  │ (Sonnet 4.6)│  │             │
    └─────────────┘  └─────────────┘  └─────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌─────────────────────────────────────────────────┐
    │          SQLite (WAL) + DuckDB                  │
    │          thesis.db                              │
    └─────────────────────────────────────────────────┘
```

- **Framework:** Pydantic AI (typsichere Agent-Definitionen, strukturierte Outputs)
- **Orchestrierung:** Plain Python `asyncio.gather()` — kein Framework-Lock-in
- **Topologie:** Hub-and-Spoke. Kein Peer-to-Peer zwischen Agents.
- **Kein LangGraph, kein CrewAI** — Pipeline ist linear genug.

### 2.2 MCP-Strategie: Drei Schichten

MCP ist sowohl Forschungsgegenstand als auch optionaler Infrastruktur-Layer.

| Schicht                       | Rolle                                              | Technologie            |
|-------------------------------|----------------------------------------------------|------------------------|
| **Kern-Pipeline**             | Datensammlung, Analyse, Synthese                   | Direkte Python-Clients |
|                               | Schnell, schlank, reproduzierbar                   | httpx + Pydantic       |
| **MCP-Demonstrationslayer**   | Thin Wrapper über die Python-Clients               | FastMCP 3.x            |
|                               | Zeigt dieselben Quellen als MCP-Tools              | Einzelner Server       |
|                               | Empirischer Vergleich in der Thesis (Schema-       |                        |
|                               | Overhead vs. Standardisierung)                     |                        |
| **Claude Desktop-Integration**| Explorative Datenanalyse via MCP-Server            | Claude Desktop + MCP   |
|                               | Konversationelle Interaktion mit Thesis-Daten      |                        |

**Thesis-Argument:** "Wir haben die Datenquellen sowohl über direkte API-Clients
als auch über MCP-Server implementiert und können die Trade-offs empirisch
vergleichen — Schema-Overhead vs. Standardisierung, Latenz vs. Interoperabilität."

### 2.3 Datenquellen — Direkte Python-Clients (Kern-Pipeline)

| Datenquelle         | Client-Typ            | Bibliothek            | Begründung                          |
|---------------------|-----------------------|------------------------|-------------------------------------|
| Polymarket CLOB     | REST + WebSocket      | httpx + Pydantic       | Fixe API, volle Paginationskontrolle|
| Dune Analytics      | REST (API-Key)        | httpx + Pydantic       | Trivial zu wrappen                  |
| GDELT               | REST (Batch-Download) | httpx + Pydantic       | Batch-Queries, keine Echtzeit nötig |
| FiveThirtyEight     | CSV-Download          | pandas.read_csv()      | Statische historische Daten         |
| RCP Poll Averages   | Scraping/CSV          | httpx + BeautifulSoup  | Logit-Transformation vor Analyse    |
| Polygonscan         | REST (API-Key)        | httpx + Pydantic       | Blockchain-Daten für Whale-Tracking |

### 2.4 Datenhaltung

| Layer            | Tool                 | Rolle                                        |
|------------------|----------------------|----------------------------------------------|
| Writes / OLTP    | SQLite (WAL-Mode)    | Datensammlung, Persistenz, `thesis.db`       |
| Reads / OLAP     | DuckDB (in-memory)   | Analytische Queries via `ATTACH` auf SQLite  |
| Visualisierung   | matplotlib / seaborn | Thesis-Plots                                 |
| Archivierung     | Parquet-Export       | Reproduzierbarkeit, Langzeitarchiv           |
| DataFrames       | Pandas               | Brücke zwischen DuckDB und Visualisierung    |

**Core-Tabellen in SQLite:**
1. `polymarket_prices` (307 Rows)
2. `whale_transactions` (25'113 Rows)
3. `poll_forecasts`
4. `sentiment_scores` (310 Rows)
5. `events_timeline`
6. `analysis_summaries` (Pre-Computed Summaries für Iceberg-Architektur)
7. `llm_audit_log` (Structured Logging für alle LLM-Calls)

---

## 3. Agenten-Definitionen

### 3.1 Sub-Agenten

| Agent            | Modell        | Verantwortung                                    | Input                        | Output (Pydantic Model)        |
|------------------|---------------|--------------------------------------------------|------------------------------|--------------------------------|
| Market Agent     | Haiku 4.5     | Polymarket-Preise, Poll-Forecasts, Normalisierung| API-Clients, Summaries       | `MarketDataResult`             |
| Sentiment Agent  | Sonnet 4.6    | GDELT-Sentiment, qualitative Einordnung          | API-Clients, Summaries       | `SentimentAnalysisResult`      |
| Whale Agent      | Haiku 4.5     | Blockchain-Transaktionen, Anomalie-Detection     | API-Clients, Summaries       | `WhaleActivityResult`          |
| Reviewer Agent   | Sonnet 4.6    | Code-Review (context-isoliert, leerer Kontext)   | Einzelnes Script + Standards | `CodeReviewResult`             |
| Orchestrator     | Sonnet 4.6    | Koordination, Synthese, Dokumentation            | Alle Agent-Outputs           | `AnalysisReport`               |

### 3.2 Orchestrator-Dokumentationsmodus

Kein separater Dokumentations-Agent. Stattdessen generiert der Orchestrator
nach jedem abgeschlossenen Analyse-Run automatisch einen strukturierten
Changelog-Eintrag als Post-Run-Hook:

```json
{
  "run_id": "uuid",
  "timestamp": "ISO-8601",
  "agents_invoked": ["market", "sentiment", "whale"],
  "data_processed": {"trades": 500, "prices": 307, "sentiment": 310},
  "key_findings": ["Divergenz KW42 detected", "Whale anomaly flagged"],
  "tokens_used": {"haiku": 45000, "sonnet": 12000},
  "cost_usd": 0.35
}
```

### 3.3 Parallelisierung

| Ebene              | Was läuft parallel?                          | Mechanismus         |
|--------------------|----------------------------------------------|---------------------|
| **Agenten-Ebene**  | Market, Sentiment, Whale Agent gleichzeitig  | `asyncio.gather()`  |
| **Entwicklung**    | Parallel Coding via Claude Code Agent Teams  | `.claude/settings`  |
| **NICHT parallel** | Brier → Granger → CAR Analyse (sequenziell)  | Datenabhängigkeiten |

---

## 4. System-Prompt-Architektur

### 4.1 Vier-Block-Struktur (pro Agent)

Jeder Agent-Call besteht aus vier gecachten/dynamischen Blöcken:

```
┌──────────────────────────────────────────────────┐
│ Block 1: Rolle & Identität (~200-400 Tokens)     │  ← cache_control
│ Aus: /directives/roles/{agent_name}.md           │
│ "Du bist ein Blockchain-Analyst, spezialisiert   │
│  auf Wallet-Tracking auf Polygon..."             │
├──────────────────────────────────────────────────┤
│ Block 2: Methodenbeschreibung (~300-500 Tokens)  │  ← cache_control
│ Aus: /directives/methodology.md                  │
│ Identisch für alle Agenten. Metriken, Methoden.  │
├──────────────────────────────────────────────────┤
│ Block 3: Pre-Computed Summaries (~1-2K Tokens)   │  ← cache_control (pro Session)
│ Aus: analysis_summaries-Tabelle (JSON)           │
│ Agenten-spezifisch gefiltert.                    │
├──────────────────────────────────────────────────┤
│ Block 4: Events-Katalog (~500-1K Tokens)         │  ← cache_control
│ Aus: events_timeline-Tabelle                     │
│ Komplett im Prompt. Identisch für alle Agenten.  │
├──────────────────────────────────────────────────┤
│ Block 5: Dynamische User-Frage (~50-200 Tokens)  │  ← NICHT gecacht
│ "Analysiere die Divergenz in KW 42"              │
└──────────────────────────────────────────────────┘

Total: ~2'000 - 4'000 Tokens (weit unter 20K Limit)
```

### 4.2 Prompt Caching

| Inhalt                        | Cache-Strategie      | Änderungsfrequenz  |
|-------------------------------|----------------------|--------------------|
| System-Prompt (Rolle, Rules)  | Immer cachen         | Nie (pro Session)  |
| Methodenbeschreibung          | Immer cachen         | Nie (pro Session)  |
| Pre-Computed Summaries        | Cachen pro Session   | Pro Analyse-Run    |
| Events-Katalog                | Immer cachen         | Selten (manuell)   |
| Dynamische User-Frage         | Nie cachen           | Jeder Call         |

Anthropic `cache_control`: Write 1.25×, Read 0.1× (90% Savings). TTL: 5 Minuten.

---

## 5. Model Routing

### 5.1 Tier-System

| Tier | Modell               | Use Cases                                          | Auslöser                              |
|------|----------------------|----------------------------------------------------|---------------------------------------|
| 2    | Claude Haiku 4.5     | Trade-Parsing, Preis-Normalisierung, Sentiment-    | >100 Calls, strukturierte I/O,        |
|      | (Batch API)          | Aufbereitung, GDELT-Verarbeitung                   | keine Echtzeit-Anforderung            |
| 1    | Claude Sonnet 4.6    | Orchestrierung, Analyse-Interpretation, Code-      | Reasoning, Synthese, Entscheidungen   |
|      | (Standard API)       | Review, Textgenerierung                            |                                       |
| 0    | Claude Opus 4.6      | Finale Synthese-Berichte, komplexe Interpretation  | Widersprüchliche Evidenz, Eskalation  |
|      | (Eskalation)         | mit widersprüchlicher Evidenz                      | durch Sonnet, ~5-10 Calls total       |

### 5.2 Routing-Logik

```
Input → Komplexitätscheck
  ├── Volumen / Extraktion     → Tier 2 (Haiku Batch)
  ├── Logik / Orchestrierung   → Tier 1 (Sonnet)
  └── Synthese / Widersprüche  → Tier 0 (Opus, nur bei Eskalation)
```

### 5.3 Benchmark-Pipeline (akademisch, nicht Produktion)

Für das Model-Routing-Kapitel der Thesis: 2-3 Tasks zusätzlich mit Gemini 2.5 Flash
und GPT-4o-mini evaluieren. Pydantic AI erlaubt Provider-Wechsel durch Änderung
des Model-Strings.

### 5.4 Kostenprojektion

| Posten                               | Geschätzte Kosten |
|--------------------------------------|-------------------|
| Haiku Batch (500 Calls, ~4M Tokens)  | ~$2-3             |
| Sonnet Standard (130 Calls, ~1.5M T) | ~$4-6             |
| Opus Eskalation (~10 Calls)          | ~$1-2             |
| Prompt Caching Savings               | -40% bis -90%     |
| **Geschätztes Total**                | **~$6-12**        |

---

## 6. Data Validation Pipeline

### 6.1 Dreistufige Validierungskette (vor jedem DB-Write)

```
API Response
    │
    ▼
┌─────────────────────────────────────┐
│ Stufe 1: Pydantic Models            │
│ API-Response-Schema-Validierung     │
│ Fehlende Felder? Typ-Änderung?      │
│ → ValidationError sofort            │
└──────────────┬──────────────────────┘
               │ ✓ Schema OK
               ▼
┌─────────────────────────────────────┐
│ Stufe 2: Pandera                    │
│ DataFrame-Schema-Validierung        │
│ Wertebereich: Preise ∈ [0,1]        │
│ Positive Beträge, GDELT ∈ [-100,100]│
│ Keine Duplikate, keine Nulls        │
│ → SchemaError wenn inhaltlich falsch│
└──────────────┬──────────────────────┘
               │ ✓ Inhalt OK
               ▼
┌─────────────────────────────────────┐
│ Stufe 3: Tenacity                   │
│ Retry bei transienten Fehlern       │
│ Exponentieller Backoff, max 3       │
│ Persistent? → Self-Annealing Stufe 4│
└──────────────┬──────────────────────┘
               │ ✓ Validiert
               ▼
        SQLite Write (WAL)
```

### 6.2 Pandera-Schema-Beispiele

> **Hinweis zur Implementierung:** Die tatsächlichen Spaltennamen in `init_db.py`
> weichen teilweise von dieser Tabelle ab. Code in `operations/validation/pandera_schemas.py`
> hält sich an die echten DB-Namen:
> - `whale_transactions` → tatsächlich `whale_trades`
> - `sentiment_scores.tone` → tatsächlich `sentiment_scores.sentiment`
> - `polymarket_prices.timestamp` → tatsächlich `polymarket_prices.price_timestamp`

| Tabelle              | Feld             | Constraint                        |
|----------------------|------------------|-----------------------------------|
| polymarket_prices    | price            | `Check.in_range(0, 1)`            |
| polymarket_prices    | timestamp        | `Check(lambda s: s.is_monotonic)` |
| whale_transactions   | amount_usd       | `Check.greater_than(0)`           |
| whale_transactions   | wallet_address   | `Check.str_length(42, 42)`        |
| sentiment_scores     | tone             | `Check.in_range(-100, 100)`       |
| poll_forecasts       | probability      | `Check.in_range(0, 1)`            |

---

## 7. Self-Annealing mit Guardrails

### 7.1 Vier-Stufen-Fallback

```
Fehler erkannt
  │
  ├── Stufe 1: Auto-Retry
  │   HTTP 429/500/503 → Exponentieller Backoff (max 3 Retries, Jitter)
  │   Gehandelt durch: Anthropic SDK / httpx / Tenacity nativ
  │
  ├── Stufe 2: Modell-Fallback
  │   Haiku scheitert wiederholt → Eskalation auf Sonnet für diesen Call
  │   Sonnet scheitert → Queue mit Backoff, dann Opus
  │
  ├── Stufe 3: Degraded Mode
  │   API komplett nicht erreichbar → Lokales Cache-Lookup aus SQLite
  │   Agent loggt Ausfall, fährt mit letzten bekannten Daten fort
  │   Kein Hard-Fail.
  │
  └── Stufe 4: Human-Eskalation
      Auslöser:
      - Confidence-Score < 0.7
      - Retry-Budget erschöpft
      - Unbekanntes Datenformat (kein Pandera-Schema-Match)
      - Budget-Schwelle überschritten
      → Agent stoppt, loggt Zustand, wartet auf manuellen Eingriff
```

### 7.2 Hard Limits gegen Endlosschleifen

| Guardrail                  | Wert    | Begründung                                    |
|----------------------------|---------|-----------------------------------------------|
| Max Iterationen pro Run    | 25      | Produktions-Erfahrungswert                    |
| Max Tokens pro Session     | 500K    | Budget-Schutz                                 |
| Same-Error-Detection       | 3       | Nach 3 identischen Fehlern → Circuit Breaker  |
| Circuit Breaker Threshold  | 5       | 5 Failures → Circuit öffnet                   |
| Circuit Breaker Cooldown   | 60s     | Wartezeit vor Half-Open-Versuch               |
| Degraded-State Trigger     | >5%     | Error-Rate über 5% → Degraded Mode            |
| Critical Alert             | >15%    | Error-Rate über 15% → Human-Eskalation        |

### 7.3 Context-Isolation für Reviewer-Agent

Der Reviewer-Agent läuft mit leerem Kontext — er erbt nichts vom
Code-Generierungs-Kontext. Er bekommt ausschliesslich:
- Das zu prüfende Script (einzelne Datei)
- Die Coding-Standards (aus /directives/coding_standards.md)
- Checkliste: API-Limits, Fehlerbehandlung, Typsicherheit, .env-Nutzung

---

## 8. Context Management — Iceberg-Architektur

### 8.1 Prinzip

```
┌─────────────────────────────────────────┐
│  SICHTBAR IM PROMPT (~2-4K Tokens)      │
│                                         │
│  • Events-Katalog (komplett)            │
│  • Pre-Computed Summaries (JSON)        │
│  • Methodenbeschreibung                 │
└─────────────────────────────────────────┘
          ▲ Agent sieht nur das
──────────┼──────────────────────────────
          ▼ Volle Daten via Tool-Calls
┌─────────────────────────────────────────┐
│  UNTERWASSER (SQLite/DuckDB)            │
│                                         │
│  • 25'113 Whale-Transaktionen           │
│  • 307 Polymarket-Preispunkte           │
│  • 310 Sentiment-Scores                 │
│  • Alle Poll-Forecasts                  │
│  • Rohe API-Responses                   │
└─────────────────────────────────────────┘
```

### 8.2 Pre-Computation Layer (deterministisch, kein LLM)

| Metrik                          | Quelle               | Aggregation                        |
|---------------------------------|----------------------|------------------------------------|
| Wochen-Durchschnittspreis       | polymarket_prices    | `GROUP BY week, AVG(price)`        |
| Preis-Volatilität               | polymarket_prices    | Rolling StdDev (7 Tage)            |
| Brier Score pro Zeitfenster     | polymarket + polls   | Deterministisch (scipy)            |
| Whale Netto-Volumen / Tag       | whale_transactions   | `SUM(CASE buy/sell)` pro Tag       |
| Whale Anomalie-Flag             | whale_transactions   | >2σ vom 30-Tage-Durchschnitt       |
| Sentiment Tages-Aggregat        | sentiment_scores     | AVG(tone), COUNT(sources)          |
| Poll-Markt-Delta                | poll_forecasts + pm  | Logit-transformiert, Differenz     |

### 8.3 Tool-Access Layer

| Tool-Funktion                  | Parameter                | Max Rows | LLM-Involvement |
|--------------------------------|--------------------------|----------|-----------------|
| `compute_brier_score()`        | start_date, end_date     | —        | Keines          |
| `fetch_polymarket_prices()`    | date_range, resolution   | 50       | Keines          |
| `query_whale_activity()`       | wallet?, week?, min_usd? | 50       | Keines          |
| `fetch_gdelt_sentiment()`      | date_range, theme?       | 50       | Keines          |
| `generate_data_summary()`      | table, date_range        | —        | Keines          |

**Keine Tool-Call-Akkumulation:** Ergebnisse werden als temporärer Kontext für die
aktuelle Antwort genutzt, aber NICHT in den System-Prompt für den nächsten Call
übernommen. Jeder Call startet mit den gleichen Summaries.

### 8.4 Hard Limits

- ❌ Kein Agent-Call über 20K Tokens Kontext
- ❌ Kein `SELECT *` ohne LIMIT (max 50 Rows pro Query)
- ❌ Kein Dump ganzer Tabellen in den Prompt
- ❌ Keine rohen Log-Files im Prompt (nur Fehler-Typ + Message)
- ❌ Keine Codebase im Prompt (Reviewer bekommt einzelne Dateien)
- ✓ Events-Katalog als einzige Tabelle komplett im Prompt erlaubt

---

## 9. Wissenschaftliche Nachvollziehbarkeit

### 9.1 Audit Trail — Structured Logging

Jeder LLM-Call wird in `llm_audit_log` (SQLite) vollständig protokolliert:

```json
{
  "call_id": "uuid-v4",
  "run_id": "uuid-v4 (gruppiert Calls pro Analyse-Run)",
  "timestamp": "ISO-8601",
  "model": "claude-sonnet-4-6",
  "tier": 1,
  "system_prompt_hash": "sha256:abc123",
  "system_prompt_version": "orchestrator-v1.2.0",
  "user_prompt": "Vollständiger Prompt-Text",
  "response": "Vollständige Antwort",
  "input_tokens": 3200,
  "output_tokens": 850,
  "cost_usd": 0.022,
  "cached_tokens": 2800,
  "tools_called": ["query_whale_activity(week=42)"],
  "tool_results_summary": "10 trades returned, max $450K"
}
```

### 9.2 Determinismus-Separator

Im Methodik-Kapitel der Thesis wird klar getrennt:

| Ergebnis-Typ                 | Methode                      | Reproduzierbarkeit          |
|------------------------------|------------------------------|-----------------------------|
| Brier Scores (Tabellen 1-3)  | Python (scipy/numpy)         | 100% deterministisch        |
| Granger-Kausalität (Tab 4-5) | Python (statsmodels)         | 100% deterministisch        |
| CAR-Analyse (Tab 6-7)        | Python (pandas/numpy)        | 100% deterministisch        |
| Qualitative Interpretationen | Claude Sonnet 4.6            | Self-Consistency geprüft    |
| Synthese-Berichte            | Claude Opus 4.6 (Eskalation) | Self-Consistency geprüft    |

### 9.3 Self-Consistency-Check für qualitative Aussagen

- 3-5 Runs desselben Interpretations-Prompts bei Temperature 0.3
- Kernaussagen-Extraktion pro Run
- Stabilität = Übereinstimmung in ≥80% der Runs
- Instabile Aussagen werden als "keine eindeutige Zuordnung" dokumentiert
- Alle Runs im Audit-Log mit gemeinsamer `consistency_group_id`

---

## 10. Constraints (Hard Limits — gilt immer)

### 10.1 Sicherheit & Secrets
- API Keys ausschliesslich via `.env` (python-dotenv), nie hardcoded
- `.env` in `.gitignore` — immer
- `.env.example` mit Platzhaltern im Repo
- Pre-Tool-Use Hook in Claude Code: `.env`-Schreibschutz

### 10.2 Code-Qualität
- Strict Async I/O: alle Agent-Calls via asyncio, kein synchrones Blocking
- Type Hints auf allen Funktionen (Pydantic Models für I/O)
- Black Auto-Format via Post-Tool-Use Hook
- Atomare Git-Commits (ein logischer Change pro Commit)
- Data Validation: Pydantic → Pandera → Tenacity vor jedem DB-Write

### 10.3 Reproduzierbarkeit
- Alle Berechnungen (Brier Score, Aggregate, Statistik) deterministisch in Python
- LLM interpretiert Ergebnisse, berechnet sie nicht
- Random Seeds wo nötig (numpy, random)
- Parquet-Export der finalen Analysedaten
- `requirements.txt` mit gepinnten Versionen
- Audit Trail für alle LLM-Calls (§9.1)

### 10.4 Deployment
- Rein lokal (Windows), kein Cloud-Deployment nötig
- Windows Task Scheduler für automatisierte Datensammlung (optional)
- `git clone && pip install -r requirements.txt && python run.py` muss funktionieren

---

## 11. Directives / Operations Trennung

### 11.1 Directives (natürliche Sprache, .md Dateien)

```
/directives
  ├── roles/
  │   ├── orchestrator.md       # Rolle, Ziel, Constraints für Orchestrator
  │   ├── market_agent.md       # Rolle für Market Data Agent
  │   ├── sentiment_agent.md    # Rolle für Sentiment Agent
  │   ├── whale_agent.md        # Rolle für Whale Tracking Agent
  │   └── reviewer.md           # Rolle für Code-Reviewer (leerer Kontext!)
  ├── methodology.md            # Methodenbeschreibung für Prompt-Kontext
  └── coding_standards.md       # Coding-Standards für Reviewer-Agent
```

### 11.2 Operations (deterministische Python-Skripte)

```
/operations
  ├── data_collection/
  │   ├── collect_polymarket.py
  │   ├── collect_dune.py
  │   ├── collect_gdelt.py
  │   └── collect_polls.py
  ├── validation/
  │   ├── schemas.py            # Pydantic Models für API-Responses
  │   ├── pandera_schemas.py    # DataFrame-Validierung
  │   └── validators.py         # Validierungs-Pipeline (Stufe 1-3)
  ├── analysis/
  │   ├── compute_brier_scores.py
  │   ├── compute_car.py          # Cumulative Abnormal Returns
  │   ├── granger_causality.py
  │   └── generate_summaries.py   # Pre-Computation Layer
  ├── agents/
  │   ├── market_agent.py         # Pydantic AI Agent-Definition
  │   ├── sentiment_agent.py
  │   ├── whale_agent.py
  │   ├── reviewer_agent.py       # Context-isoliert
  │   └── orchestrator.py         # asyncio.gather() + Dokumentationsmodus
  ├── tools/
  │   ├── db_tools.py             # SQLite/DuckDB Query-Tools
  │   ├── api_clients.py          # httpx Wrapper für alle Datenquellen
  │   └── cache_manager.py        # Prompt-Caching-Logik
  ├── mcp/
  │   └── thesis_mcp_server.py    # FastMCP Demonstrationslayer
  └── audit/
      ├── logger.py               # Structured JSON Logging
      └── consistency_check.py    # Self-Consistency Runner
```

### 11.3 Prompt-Versionierung

Semantic Versioning für alle Directive-Files:
- **Major** (1.0 → 2.0): Verhaltensänderung des Agenten
- **Minor** (1.0 → 1.1): Verfeinerung, neue Constraints
- **Patch** (1.0.0 → 1.0.1): Tippfehler, Klarstellung

---

## 12. Tool-Landschaft (nach Phase)

### 12.1 Datensammlung & Analyse (April–Juni)

| Tool                     | Zweck                                            | Wann                          |
|--------------------------|--------------------------------------------------|-------------------------------|
| **Claude Code (VS Code)**| Python-Entwicklung, Agent-Code, Analyse-Scripts  | Primäre Entwicklungsumgebung  |
| **Claude Desktop + MCP** | Explorative Datenanalyse, konversationell        | Wenn MCP-Layer steht          |
| **Perplexity**           | Literaturrecherche, Event-Kontextrecherche       | Laufend, manuell              |

### 12.2 Thesis-Schreibphase (Juni–August)

| Tool                       | Zweck                                            | Wann                          |
|----------------------------|--------------------------------------------------|-------------------------------|
| **Claude.ai**              | Kapitelentwürfe iterieren, Prosa-Generierung     | Haupttool für Text            |
| **Overleaf**               | LaTeX-Kompilierung, Formatierung                 | Finale Dokument-Erstellung    |
| **Zotero + Better BibTeX** | Quellenmanagement, automatischer BibTeX-Export   | Laufend                       |
| **Perplexity**             | State-of-the-Art-Recherche, Quellensuche         | Laufend, manuell              |

### 12.3 Explizit nicht in der Pipeline

| Tool                        | Grund                                            |
|-----------------------------|--------------------------------------------------|
| Perplexity (programmatisch) | Nicht reproduzierbar, GDELT deckt Sentiment ab   |
| OpenAI Codex CLI            | Claude Code + Reviewer-Agent reicht              |
| Twitter/X API               | Kostenpflichtig, durch GDELT ersetzt             |
| LiteLLM / OpenRouter        | Zusätzliche Dependency ohne Kostenvorteil        |

---

## 13. Erste 5 atomare Tasks (nach Freigabe)

1. Repository-Struktur anlegen: `git init`, `.gitignore`, `.env.example`,
   `/directives`, `/operations`, `requirements.txt`
2. Pydantic AI Setup: `pip install pydantic-ai`, Basis-Agent-Definition
   mit strukturiertem Output (Market Agent als erster Prototyp)
3. Data Validation Pipeline: Pydantic Models + Pandera Schemas für
   alle 6 Core-Tabellen definieren
4. Pre-Computation Pipeline: `generate_summaries.py` — liest bestehende
   `thesis.db`, berechnet alle Aggregate aus §8.2, schreibt in
   `analysis_summaries`-Tabelle
5. Orchestrator-Grundgerüst: `asyncio.gather()` mit 3 Agent-Stubs,
   System-Prompt aus `/directives/orchestrator.md`, Prompt-Caching aktiv,
   Audit-Logging aktiviert

---

## 14. Explizit ausgeschlossen

| Tool/Konzept              | Grund                                              |
|---------------------------|----------------------------------------------------|
| MCP als Kern-Pipeline     | Schema-Overhead (bis 72% Kontext), fixe APIs       |
| LangGraph / CrewAI        | Pipeline zu linear für Graph-/Rollen-Overhead      |
| PostgreSQL / Supabase     | Overkill für Thesis-Scale                          |
| Twitter/X API             | Kostenpflichtig, durch GDELT ersetzt               |
| Cloud-Deployment (Modal)  | Nicht nötig für Thesis-Fragestellungen             |
| Multi-Agent Consensus     | Halluzinations-Risiko bei deterministischen Daten  |
| Stochastic Multi-Framing  | Korrelierte Fehler > Einzelagent-Self-Consistency  |
| DevSwarm / ccswarm        | Enterprise-Overhead                                |

---

## 15. Stil & Kommunikation

- **Schweizer Deutsch OK** — informell, aber präzise
- **Keine Absolutismen** — immer Trade-offs nennen
- **ss statt ß** — immer (Schweizer Rechtschreibung)
- **Kompakt** — Tabellen und Code bevorzugen, keine langen Prosa-Abschnitte
- **Ehrlich bei Unsicherheit** — lieber "ich bin nicht sicher" als halluzinieren
- **Atomare Commits** — ein logischer Change, eine Commit-Message
