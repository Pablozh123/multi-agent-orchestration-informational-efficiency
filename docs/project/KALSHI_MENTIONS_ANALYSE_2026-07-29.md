# Kalshi Mentions-Märkte: Analyse und Implementierungsplan

Stand: 29.07.2026 (Recherche 28.07. ~22:30 UTC, öffentliche Kalshi-API
`api.elections.kalshi.com/trade-api/v2`, unauthentifiziert).
Bezug: `UEBERGABE_2026-07-28_LIVE_MENTIONS.md` (Polymarket-Strecke).

## 1. Kurzbefund

Kalshi betreibt dieselbe Marktgattung wie unsere Polymarket-Strecke, aber
mit **drei strukturell anderen Regeln**, die unsere Methodik direkt
betreffen:

1. **Aufgelöst wird primär per Video/Audio, nicht per Transkript.**
2. **Keine Zählschwellen** — alle Mentions-Märkte sind binär "Wort fällt
   mindestens einmal".
3. **Wortvarianten sind deterministisch geregelt** (nur Plural und
   Genitiv, keine Tempus-/Grammatikformen).

Dazu kommen: deutlich größeres Universum (397 Serien, davon 152
Earnings-Calls), deutlich mehr Liquidität, 1-Cent-Ticks — aber
Handelsgebühren, die Polymarket nicht hat, und ein
Nach-Call-Handelsfenster, das von Kalshi-Ops abhängt statt von einem
Oracle.

Unsere Pipeline ist zu ~80 % übertragbar. Venue-spezifisch sind nur drei
Module (Regelbau, Orderbuch, Ausführung); Audio, Transkription, Zähler,
Sprecher-Marker und Entscheidungslogik bleiben unverändert.

## 2. Was Kalshi anders macht (belegt)

| Dimension | Polymarket (unsere Strecke) | Kalshi |
| --- | --- | --- |
| Auflösungsquelle | UMA-Oracle, faktisch Transkript-/Textzählung | **Video primär**, Transkript nur bei Uneinigkeit |
| Entscheider | UMA-Proposer + Bond + Dispute-DVM (~48 h) | Kalshi-Mitarbeiter, `settlement_timer_seconds` 1800 (30 min); Outcome Review Committee bei Streit |
| Marktform | Zählschwellen ("Quarter 15+") und Einzelwörter | **Nur binär**, `strike_type: custom`, `custom_strike: {"Word": "Braintree"}` |
| Varianten | unscharf, wir raten per `VARIANTEN_MAP` | **Regel im Markt**: exakte Phrase, Plural oder Genitiv; Tempus-/Grammatikflexionen zählen **nicht** |
| Gebühren | keine Handelsgebühr | Taker `ceil(0.07·P·(1−P)·100)/100` pro Kontrakt, Maker 25 % davon |
| Zugang | Wallet, USDC, on-chain | KYC-Konto, keine Wallet/Gas/Allowance-Strecke |
| Tick | 0.001 | 0.01 (`price_level_structure: linear_cent`) |

Wörtlicher Regeltext (`rules_secondary`, identisch über Earnings und Fed):

> Video of the … earnings call will be primarily used to resolve the
> market; if a consensus by Kalshi employees cannot be reached using
> video, transcripts … will be used … The exact phrase/word, or a plural
> or possessive form of the phrase/word, must be used. Grammatical/tense
> inflections are otherwise not included.

### Universum

- **397 Serien** in der Kategorie Mentions, davon **152 Earnings-Calls**.
  Alle unsere bisher gefahrenen Namen sind dabei: `KXEARNINGSMENTIONPG`,
  `…BA`, `…AXP`, `…PYPL`, `…META`, `…MSFT`, `…AAPL`, `…TSLA`, `…NVDA`,
  `…AMZN`. (Google fehlt.)
- Dazu Fed-Pressekonferenz (`KXFEDMENTION`, 44 Märkte je Termin),
  Trump-Rallies/Pressekonferenzen (`KXDJTRALLY`, `KXTRUMPSAY*`,
  `KXBUSINESSROUNDTABLE`), Podcasts (Rogan, Portnoy, Carlson, Threadguy),
  Sport (NFL, NBA, NCAAB, NASCAR, ATP), Politik (Leavitt, Johnson,
  Mamdani, Pelosi, Bessent).
- **Dieselben Calls, die wir schon fahren** — ein Audio-Lauf kann zwei
  Venues bedienen.

### Liquidität (gemessen 28.07. abends)

| Event | Märkte | Volumen (Kontrakte) | Open Interest | Beispiel-Spread |
| --- | --- | --- | --- | --- |
| PayPal 28.07. (abgelaufen, derselbe Call wie unser Lauf) | 16 | 125.933 | 81.636 | — |
| Fed/Warsh Juli | 44 | 301.869 | 210.366 | Projection 0.39/0.40 |
| Meta 29.07. | 18 | 61.589 | 28.416 | Ray-Ban 0.73/0.74, Llama 0.21/0.22 |

Spreads durchgehend 1 Cent, Größen im vierstelligen Kontraktbereich
(Fed Productivity: Bid-Size 1.894, Ask-Size 1.585). Das ist deutlich
tiefer als das, worin unser PayPal-Fill von 25 Shares stattfand.

### Handelsfenster (gemessen, n=1)

Unser PayPal-Call endete **13:01:11Z** (`call_ende`, 394 Chunks). Kalshi
schloss alle 16 Märkte erst **13:53:31–13:53:37Z** — also **52 Minuten
nach Call-Ende**, und *nicht* beim Wortfall: Braintree fiel um 12:02 und
blieb bis 13:53 offen. Das Feld `early_close_condition` ("closes early if
the event occurs") wurde also nicht wortweise angewandt, sondern als
Event-Schluss nach dem Call.

**Konsequenz:** Es gibt auf Kalshi ein Nach-Call-Fenster für die
Late-NO-Idee — groß genug für unseren VAD-freien Vollpass (Boeing:
9,4 min GPU für 76 min Band). Aber es ist Ops-abhängig, nicht garantiert,
und bei n=1 nicht belastbar. Fensterlänge über mehrere Calls messen ist
Aufgabe von Phase 1.

## 3. Was das für unsere sieben Erkenntnisse bedeutet

- **§3.4 / §4 (Vollpass-Abwesenheitsbeweise):** Auf Kalshi misst der
  Resolver das Ohr, unser Vollpass misst das Transkript. Beide
  Kalibrierfälle vom 28.07. wären auf Kalshi *gegen* uns gelaufen:
  "Agentic Commerce" ist dort YES resolved (Kalshi-`result: yes`) — genau
  wie bei UMA, und genau wie das Audio es hergibt. Boeing "Guidance"
  ebenso. Der **Nachbarschafts-/Verschreibungs-Filter** (guide/guides,
  agent e-commerce) ist auf Kalshi damit nicht optional, sondern die
  Kernbedingung jedes NO.
- **§3.2 (Antizipierer irren):** Kanal bleibt, wird aber teurer — bei
  P≈0.5 kostet ein Taker-Trade 1,75 Cent pro Kontrakt, also ~3,5 % des
  Einsatzes. Zweifel-Fenster-Käufe bei 0.45–0.65 verlieren spürbar Edge.
  Käufe nahe 0.9 kosten nur ~0,6 Cent.
- **§3.1 (Latenzrennen verloren):** Auf Kalshi eher schlimmer — US-Publikum,
  professionellere Bücher. Unser 17–20-s-Rückstand bleibt bestehen. Die
  These "Edge = Zweifel-Fenster, nicht Erst-Erkennung" gilt unverändert.
- **Wegfallende Komplexität:** keine Zählschwellen ⇒ `parse_schwelle`,
  Bracket-Logik und `≤0.7×Schwelle`-Regel entfallen; kein Wallet, kein
  Gas, kein `wrap_pusd`/`set_allowances`; kein UMA-Dispute-Spiel.
- **Neu für die Thesis:** Zwei Venues lösen denselben Call nach *zwei
  verschiedenen Wahrheitsbegriffen* auf (Audio vs. Text) und preisen ihn
  unabhängig. Das ist ein direkt messbares Informationseffizienz-Objekt —
  Preisspur-Divergenz, Reaktionslatenz je Venue, Auflösungsdivergenz.
  Phase 1 liefert diese Daten ohne jedes Handelsrisiko.

## 4. Passt unsere Pipeline?

Venue-agnostisch (unverändert nutzbar): `transcription.py`,
`counter_engine.py`, `speaker.py`, `gap_verify.py`, `trigger_verify.py`,
`no_konsens.py`, Stream-Selbstheilung und Fenster-Modus im
`earnings_bot.py`.

Venue-spezifisch (drei Nähte):

| Modul | Heute | Für Kalshi |
| --- | --- | --- |
| `market_rules.py` | parst Polymarket-Fragetext → Begriffe, Schwelle, Token-IDs | Kalshi liefert `custom_strike.Word` explizit; Schwelle immer 1; Varianten nach Kalshi-Regel statt `VARIANTEN_MAP` |
| `orderbook.py` | CLOB `fetch_book(token_id)` | `GET /markets/{ticker}/orderbook`, Felder `orderbook_fp.yes/no_dollars` |
| `execution.py` | `py-clob-client`, on-chain | REST + RSA-PSS-Signatur, `POST /portfolio/events/orders` |
| `decision.py` | Edge ohne Gebühren | Gebührenterm `ceil(0.07·P·(1−P)·100)/100` in die Edge-Schwelle |

`MarketRule` (market_rules.py:22) passt als Datenklasse weiter — `yes_token_id`/
`no_token_id` werden durch den Kalshi-Ticker belegt, `schwelle` ist konstant 1.

### API-Fakten für die Umsetzung

- Basis: `https://api.elections.kalshi.com/trade-api/v2` (Prod),
  `https://external-api.demo.kalshi.co/trade-api/v2` (Demo, Spielgeld,
  Preise **nicht** realitätsnah).
- Auth: Header `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP` (ms),
  `KALSHI-ACCESS-SIGNATURE`. Signiert wird `timestamp_ms + METHOD + path`
  **ohne Query-String**, RSA-PSS/SHA-256, Salt = Digest-Länge, Base64.
- Ratelimit Basic: 200 Read-/100 Write-Token pro Sekunde, die meisten
  Requests kosten 10 Token (⇒ ~20 Reads/s, ~10 Writes/s). Upgrade auf
  Advanced (300/300) per API-Call, höhere Stufen über Volumen.
- Order: `POST /portfolio/events/orders`, Felder `ticker`, `side`
  (`bid` = YES kaufen, `ask` = YES verkaufen ≙ NO), `count`, `price`
  (Dezimalstring), `time_in_force` (`fill_or_kill` / `immediate_or_cancel`
  / `good_till_canceled`), `self_trade_prevention_type`; dazu `post_only`,
  `reduce_only`, `cancel_order_on_pause`. Antwort enthält `order_id`,
  `fill_count`, `remaining_count`, `ts_ms` (Matching-Engine-Zeit).
- WebSocket-Kanäle: Ticker, Orderbook-Deltas, Public Trades, User Orders,
  User Fills, Order-Group-Updates. Für den Live-Betrieb ersetzt der
  Ticker-/Orderbook-Kanal unser Polling.

## 5. Implementierungsplan

**Stand 29.07.:** Phase 0 erledigt (Konto angelegt), Phase 1–3 gebaut und
getestet. Offen sind der API-Key und der Demo-Trockenlauf (Phase 3b), dann
Phase 4.

### Phase 0 — Zugangsklärung (erledigt 29.07.)

1. Kontoeignung Deutschland im **Kalshi Member Agreement** prüfen. Dritt-
   quellen führen Deutschland als unterstützt und Frankreich, Italien,
   Belgien, Polen, Portugal, Irland, Ungarn, Bulgarien, UK und die Schweiz
   als gesperrt — **das ist nicht von Kalshi selbst bestätigt und muss vor
   jeder Live-Arbeit verifiziert werden.**
2. Konto + KYC; Einzahlung international nur per Debitkarte, Wire ab
   1.000 USD oder Krypto (kein ACH/PayPal).
3. API-Key erzeugen (Kontoeinstellungen → API Keys), Private Key sofort
   sichern — er ist nicht erneut abrufbar.
4. Demo-Konto separat anlegen (eigene Credentials).

Phase 1 läuft **ohne** Phase 0 und sollte sofort starten.

### Phase 1 — Read-only-Adapter und Preisspur-Recorder (~1 Tag, kein Konto nötig)

Neue Dateien:

- `operations/pipeline/kalshi_client.py` — öffentliche REST-Calls
  (`/series`, `/events`, `/markets`, `/markets/{t}/orderbook`), Retry,
  Ratelimit-Bremse. Auth-Hook vorbereitet, aber ungenutzt.
- `operations/pipeline/kalshi_rules.py` — Kalshi-Markt-JSON → `MarketRule`.
  `custom_strike.Word` splitten (Kalshi trennt Alternativen mit " / ",
  z. B. "AI / Artificial Intelligence", "Stablecoin / Stable Coin"),
  Schwelle = 1, Varianten nach Kalshi-Regel (Grundform + Plural + Genitiv,
  **keine** Tempusformen), `homophon_sensitiv` aus bestehender Liste.
  **Meta-Markt `-NQE` ("Event does not qualify") hart ausschließen** — der
  ist kein Wortmarkt, sein `rules_primary` ist ein Template-Artefakt.
- `operations/pipeline/kalshi_recorder.py` — schreibt während jedes
  laufenden Polymarket-Bots parallel die Kalshi-Preisspur desselben Calls
  mit (WS-Ticker oder Polling), Format analog `orderbook_log.csv`.

Tests in `tests/test_kalshi_rules.py` (26), offline gegen den echten
API-Abzug `tests/fixtures/kalshi_mentions_snapshot.json`.

Ertrag ohne jedes Risiko: Latenz- und Preisdivergenz Kalshi ↔ Polymarket ↔
unsere Verify-Zeit auf demselben Audio; Messung der tatsächlichen
Nach-Call-Fensterlänge über mehrere Calls.

**Gebaut 29.07.** Ein Befund kam beim Bauen dazu: `compile_patterns` deckt
Kalshis Variantenregel bereits exakt ab (Suffix `('s|s|')`) — bis auf
Plurale, die nicht durch bloßes „s" entstehen. Ohne die Ergänzung hätte
der Fed-Markt „Tax" ein gesprochenes *taxes* nie gezählt. Unregelmäßige
Plurale (leaf/leaves) werden bewusst nicht geraten: ein verpasster Treffer
kostet weniger als ein Geistertreffer.

### Phase 2 — Regel- und Entscheidungsschicht (gebaut 29.07.)

`operations/pipeline/kalshi_decision.py`:

- **Gebühr im Deckel.** Geprüft wird der Vollpreis (Ask + Gebühr), nicht
  der rohe Ask. Sonst kauft der Bot am 0.90-Deckel systematisch einen Cent
  zu teuer — bei 0.895 liegt der Vollpreis bereits über der Grenze.
- **Verschreibungsfilter als NO-Pflichtsperre.** Ein NO unterbleibt,
  sobald das Vollpass-Transkript ein Wort enthält, das mit dem Zielwort
  mindestens vier Anfangsbuchstaben teilt, ohne selbst ein Treffer zu
  sein. Die Schwelle 4 ist aus den beiden belegten Fällen abgeleitet:
  *guidance*/*guides* teilen „guid", *agentic*/*agent* teilen „agen".
  Der Filter kann nur Käufe verhindern, nie welche auslösen.
- **Kein NO ohne Vollpass-Transkript.** Fehlt es, gibt es kein NO — auf
  einer video-aufgelösten Venue ist Abwesenheit sonst nicht belegbar.

### Phase 3 — Ausführung (gebaut 29.07., Demo-Trockenlauf offen)

`operations/pipeline/kalshi_execution.py`. Beim Bauen zeigte die
OpenAPI-Spezifikation zwei Dinge, die aus der Doku allein falsch
herausgelesen waren:

- Der Endpunkt ist **`POST /portfolio/events/orders`** (V2). Das ältere
  `/portfolio/orders` wird laut Spec ab Mai 2026 abgekündigt.
- V2 quotiert **alles aus YES-Sicht**: `side: bid` kauft YES, `side: ask`
  verkauft YES — wirtschaftlich ein NO-Kauf zu `1 − price`. Es gibt kein
  `yes_price`/`no_price`-Paar mehr, und Preise wie Stückzahlen sind
  Dezimalstrings (Bruchteile ab 0.01 Kontrakt).

Weitere Entscheidungen:

- **Buchung aus der Orderantwort**, nicht aus dem Kontostand. Die
  V2-Antwort liefert `average_fill_price` und `average_fee_paid` — der
  Einsatz ist damit gemessen statt geschätzt. Der `_budget_sync`-Fehler
  der Polymarket-Seite (PayPal 28.07.: `ausgegeben_usd 0.0` trotz 16.08
  USD Fill) wird nicht mitgeschleppt.
- **FOK statt Level-Sweep**: 1-Cent-Ticks und bekanntes bestes Level;
  fällt die Order durch, greift der nächste Durchlauf mit frischem Buch.
- Das Kalshi-Buch wird per `kalshi_client.buch_als_polymarket` in das
  CLOB-Format übersetzt, damit Budget-, Tiefen- und Kill-Switch-Logik der
  bewährten `ExecutorBase` unverändert greifen.

Tests in `tests/test_kalshi_handel.py` (38), darunter die beiden
Verschreibungsfälle als Regressionstests und eine Signaturprüfung gegen
ein Wegwerf-Schlüsselpaar.

### Phase 3b — Demo-Trockenlauf (offen, braucht den API-Key)

1. API-Key im Kalshi-Konto erzeugen, Private Key als PEM sichern.
2. In `.env`: `KALSHI_KEY_ID=…`, `KALSHI_PRIVATE_KEY_PFAD=…`.
3. Eine Order über `baue_executor(live=True, demo=True)` gegen
   `external-api.demo.kalshi.co`, ein Kontrakt, Signatur- und
   Fehlerpfade prüfen.

### Phase 4 — Ein kleiner Live-Lauf, parallel zu Polymarket

Ein Earnings-Call, den wir ohnehin fahren, mit Kleinstbudget (z. B. 50 USD,
10 USD/Markt), NO weiterhin gesperrt. Ziel ist nicht Ertrag, sondern:
Signatur/Latenz/Fill-Verhalten unter Last, Gebührenabrechnung
nachrechnen, Fensterlänge bestätigen.

### Phase 5 — Universum ausrollen (danach)

Kalender-Automatik über `/events?series_ticker=…` für die 152
Earnings-Serien; Fed-Pressekonferenz (44 Märkte, höchstes gemessenes
Volumen) und Trump-Formate als eigene Profile. Erst nach stabiler Phase 4.

## 6. Risiken und offene Punkte

1. **Deutschland-Zugang unbestätigt** (Phase 0). Harter Blocker für
   Phase 3–5.
2. **Gebühren fressen die mittleren Preise.** Der Zweifel-Fenster-Kanal
   liegt genau dort, wo die Gebühr am höchsten ist. Vor Phase 4 einmal
   durchrechnen, ob unsere bisherigen vier Fills nach Kalshi-Gebühren
   überhaupt profitabel gewesen wären.
3. **Nach-Call-Fenster ist n=1.** 52 min bei PayPal, Ops-abhängig,
   `can_close_early: true`. Late-NO darauf zu bauen, ist vor Phase-1-Messung
   unbegründet.
4. **Menschliche Resolver statt Oracle.** Näher an unserer Messgröße
   (Audio), aber weniger vorhersagbar in Grenzfällen und ohne
   Dispute-Mechanik, in die man einsteigen könnte.
5. **P&G ist auf Kalshi derzeit nicht gelistet.** `KXEARNINGSMENTIONPG`
   existiert, hat aber nur Events für Apr und Okt — kein Event für den
   29.07. Morgen bleibt also Polymarket-only; im Laufe des Vormittags
   nochmals prüfen, Kalshi legt Earnings-Events teils erst ~1 Woche vorher
   an.
6. **Gemessene Preise stammen aus einem einzelnen Snapshot** vom 28.07.
   abends, nicht aus einer Zeitreihe.

## 7. Sofort nutzbare Termine

| Termin | Kalshi-Event | Nutzen |
| --- | --- | --- |
| Meta, 29.07. nach US-Schluss | `KXEARNINGSMENTIONMETA-26JUL29`, 18 Märkte | Phase-1-Recorder, auch ohne eigenen Audio-Lauf |
| Fed/Warsh, 30.07. | `KXFEDMENTION-26JUL`, 44 Märkte, höchstes Volumen | bestes Messobjekt für Preisspur + Fensterlänge |
| P&G, 29.07. 12:30 UTC | auf Kalshi nicht gelistet | Polymarket-only, Kalshi-Recorder entfällt |
