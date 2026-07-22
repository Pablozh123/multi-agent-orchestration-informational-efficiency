# Kuratierte Live-Laeufe

Versionierte, reduzierte Kopien der abgeschlossenen Bot-Laeufe. Sie sind die
Quelle fuer `pipeline_forward.json`, wenn die Arbeitskopie kein `data/live/`
hat -- das Verzeichnis ist gitignored und existiert nur in dem Checkout, in dem
die Bots gelaufen sind. Vorher publizierte die taegliche Kette darum ein leeres
Artefakt.

Erzeugt und aktualisiert mit:

    python -m operations.pipeline.kuratiere_live_laeufe --live-root <pfad-zu-data/live>

## Was hier liegt

Je Lauf ein Verzeichnis `<profil>/` mit hoechstens zwei Dateien:

| Datei | Inhalt |
| --- | --- |
| `decisions_log.jsonl` | `wall_ts_utc`, `decision.{action,reason,limit_price}`, `result.size_usd`, `book_snapshot.{asks,bids}` auf `price` reduziert |
| `bot_events.jsonl` | nur Ereignisse mit Wortzaehler-Staenden (`chunk`/`staende`, `fertig`/`endstaende`) in Original-Reihenfolge |

Genau diese Felder publiziert `daily_review_run.build_pipeline_forward` ohnehin.
Der Publish-Schritt liefert aus den kuratierten Kopien Feld fuer Feld dasselbe
Artefakt wie aus den Rohdaten; ein Test haelt das fest
(`tests/test_kuratiere_live_laeufe.py`).

## Was bewusst draussen bleibt

`token_id`, `market_id`, `outcome`, `result.status`/`detail`/`size_shares` (das
`detail` enthaelt gekuerzte Wallet-Ids), Buch-Groessen und Buch-Zeitstempel,
`deposit_wallet.json`, Wallet- und Schluesseldateien, Orderbuch-CSV, Bot-Logs
sowie Audio- und Videodateien. Vor dem Schreiben laeuft dasselbe
Redaktions-Gate wie im Publish-Schritt ueber jede Datei; ein Fund bricht ab.

Die Kennzeichnung bleibt unveraendert: beobachtend/paper, keine Wallet-Daten,
keine Rendite-Aussage.

## Stand

Acht abgeschlossene Laeufe, 308 Entscheidungen (03.07. bis 21.07.2026):
`allin_july3`, `allin_july10`, `allin_july17`, `jre_july6`, `jre_july13`,
`jre_july20`, `elon_july13`, `lemonade_july15`. `elon_july13` ist der X-Feed-Lauf
und fuehrt keine Wortzaehler.
