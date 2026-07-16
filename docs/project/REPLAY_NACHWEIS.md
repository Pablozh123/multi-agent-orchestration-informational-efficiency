# Replay-Nachweis für die Tabelle-6-Einstufungen (Kapitel 7)

Status: Befund vom 16.07.2026, erstellt gemäß Pilot-Protokoll V2, Abschnitt
"Offener Nachweis-Punkt". Entscheidung über die Konsequenz liegt bei der
Studentin.

## Auftrag

Für die Verteidigung muss auffindbar sein, worauf die Strategie-Einstufungen
in Tabelle 6 der Arbeit (`thesis/chapters/07_erweiterungen.tex`, Zeilen 59–71)
und in `docs/project/PROZESS_ZUSAMMENFASSUNG_DOZENT.md` (Zeilen 65–92)
beruhen — insbesondere die Angabe zum Crypto Oracle-Divergence-Fade
("N=28: Fade-Richtung 26W/2L, ~93 %").

## Fundort: Repo `prediction-alpha-bot` (Phase-1-Scanner)

Der Edge-Katalog und die Forward-Replay-Läufe liegen nicht im Thesis-Repo,
sondern im Schwesterprojekt `C:\Users\chole\Projects\prediction-alpha-bot`
(TypeScript, paper-only, eigene CI; Commits 19.05.–Anfang Juni 2026).

**1. Edge-Katalog mit den Einstufungen (Primärdokument der Tabelle 6):**

- `docs/playbook/EDGES.md`, Abschnitt 12 "Crypto Up/Down Fade / Oracle
  Divergence (Tier B)", Zeile 197:
  "On historical N=28 data, NORM direction was 2W/26L (7% WR), FADE was
  26W/2L (93% WR, Wilson lb95=77.4%). Mechanism plausibly causal — different
  oracle feed. Requires out-of-sample confirmation before live flip."
- `docs/playbook/EDGES.md`, Abschnitt 7 "Tail-Fade / Premium Harvest
  (Tier B)", Zeile 118: "Consistent small-$ edge. Resolution-window holding
  discipline matters — 40-70% of mid recovered on early exit due to
  thin-book." (Deckt die Tabelle-6-Formulierung "konstanter Klein-Edge;
  Haltedisziplin nötig" ab.)
- Ergänzend `docs/playbook/ANTIPATTERNS.md`, Zeile 82 (gleiche Zahlen) und
  `docs/playbook/METHODOLOGY.md` (Wilson-lb95-Berichtsregel).

**2. Forward-Replay-Reports (Beleg für die Struktur-Scanner-Aussagen):**

- `docs/reports/forward-replay-2026-05-20/21.{md,json}` und
  `docs/reports/basket-forward-replay-2026-05-22` bis `…-06-02.{md,json}`
  decken das im Dozenten-Dokument genannte Fenster 20.05.–02.06.2026 ab
  (0-Arb-Befunde der strukturellen Scanner, Coverage-Reports, Cross-Venue-
  Reports bis 10.06.).
- Lauf-Logs und Snapshot-Datenbanken unter `logs/`
  (u. a. `forward-clean-2026-05-22.db`, `bot-24h-archive-20260520-*`).

## Kritische Lücke: Rohdaten der 28 Oracle-Fälle nicht auffindbar

Die Zahl N=28 ist ausschließlich als **fertiger Playbook-Eintrag**
dokumentiert. Auf dem gesamten Rechner existiert keine fallweise Rohdaten-
Liste (keine 28 Einzelfälle, kein Updown-Scanner-Quellcode, keine
Auswertungs-DB):

- `EDGES.md` wurde am 19.05.2026 im **allerersten Commit** des Repos angelegt
  (d165718 "initial paper-only scanner skeleton") und seither nie geändert.
  Die N=28-Auswertung ist damit älter als das Repo selbst.
- `ANTIPATTERNS.md` (Zeile 66) verweist als Datenquelle auf eine
  "VPS-live DB" — eine Datenbank eines Vorgängersystems auf einem VPS, die
  lokal nicht archiviert ist.
- Durchsucht ohne Treffer: `prediction-alpha-bot` (Quellcode, Logs, Reports),
  `ba-thesis`, `prediction-market-terminal`, `RL trading`,
  `tradingview-mcp-jackson`, `polymarket-reddit-sentiment` (Dateinamen- und
  Inhaltssuche nach updown/oracle/divergence/fade/N=28/26W) sowie alle
  Claude-Code-Session-Transkripte.

**Abgrenzung:** Die Artefakte `data/results/monitor_v2_historical_replay_*`
im Thesis-Repo sind H2/H3-Monitor-Replays (Wallet-/Event-Scoring) und haben
mit dem Strategie-Forward-Replay nichts zu tun.

## Konsequenz-Optionen für die Arbeit (Entscheidung Studentin)

Die Angabe "N=28, 26W/2L" ist damit eine **dokumentierte, aber nicht mehr
reproduzierbare Auswertung eines Vorgängersystems** — kein archivierter
Backtest. Optionen für `07_erweiterungen.tex` (Zeile 67) und die
Dozenten-Dokumente:

1. **Quelle präzisieren (empfohlen):** Zahl behalten, aber ausweisen als
   "dokumentierte Auswertung des Vorgänger-Scanners (Playbook-Eintrag vom
   19.05.2026); Rohdaten nicht archiviert, Out-of-Sample-Bestätigung offen".
   Das ist ehrlich, behält die Information und passt zur ohnehin
   vorhandenen Einschränkung "Out-of-Sample offen".
2. **Vorsichtiger formulieren:** Auf die Zahl verzichten und nur
   "vielversprechendes, unbestätigtes Muster (Tier B)" schreiben.

Für Tail-Fade ist die Evidenz ohnehin qualitativ (EDGES.md §7); dort genügt
der bestehende Wortlaut mit Quellenverweis auf den Playbook-Eintrag.

## Suchprotokoll

Suche am 16.07.2026 durch Claude Code: Dateinamen-Suche (BRIEFING/PILOT/
updown/oracle/divergence/fade/replay) über die Projektordner und Home-
Verzeichnisse, Inhaltssuche (ripgrep) in `prediction-alpha-bot`
(src/docs/logs), `ba-thesis` (alle Branches und Git-Historie),
`prediction-market-terminal` (*.md, *.py), Session-Transkript-Volltextsuche
("PILOT_PROTOKOLL", "Echtgeld", "Oracle-Divergence", "Watcher", "Briefing").
