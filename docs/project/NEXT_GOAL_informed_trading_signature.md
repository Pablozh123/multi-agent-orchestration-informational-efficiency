# Naechstes Goal: Informed-Trading-Signatur als getestetes Modul

Status der Vorarbeit: explorativ vorhanden
(`data/results/h3_event_wallet_profile_exploratory.csv`,
`data/results/h3_informed_trading_profile.png`). Befund: in den Ereignisfenstern
median 57% neue Wallets, 64% Top-1-Konzentration, erhoehtes Volumen. Noch KEIN
getestetes Modul. Genau das ist der naechste Bau-Schritt.

## Ziel (ein aktives Goal)
`goal-h3-informed-trading-signature-001`: aus dem explorativen Befund eine
deterministische, getestete Diagnostik machen, die pro Ereignisfenster eine
verteilungsbasierte Verdachts-Signatur berechnet. Bleibt aggregiert,
beschreibend und ohne Insider-/Kausalanspruch.

## Was Codex baut
1. `operations/analysis/informed_trading_signature.py` mit deterministischen
   Features je Ereignisfenster (aus `whale_trades`, `polymarket_prices`,
   `events_timeline_seed.csv`):
   - `new_wallet_share`: Anteil aktiver Wallets, deren erste beobachtete
     Transaktion im Fenster liegt (dataset-relativ).
   - `top1_concentration` und `hhi` der Fenster-Betraege.
   - `abnormal_trade_size_z`: mittlere Fenster-Trade-Groesse vs Basisfenster
     (z-Wert), angelehnt an Delvecchio (2026) und Kyle (1985).
   - `active_wallet_z`, `volume_z` (bestehende Anomalie-Logik wiederverwenden).
   - `tier1_lead`: Lead-Lag/Granger-Signal aus bestehender H3-Diagnostik.
2. Kombinierter `suspicion_score` ueber Rang-/Perzentil-Normalisierung der
   Features (verteilungsbasiert, KEINE willkuerlichen Schwellen).
3. Bounded Outputs: `data/results/h3_informed_trading_signature.csv` +
   `..._metadata.json` + eine Figur. Keine Wallet-Adressen ausgeben.
4. Tests `tests/test_informed_trading_signature.py`: Feature-Wertebereiche,
   Determinismus, No-Wallet-Address-Guard, Monotonie des Scores gegen einen
   synthetischen Aktivitaets-Spike.

## Guardrails (aus AGENTS.md / ARCHITECTURE_DECISIONS.md)
- Deterministisch in Python, getestet. LLM/Agenten rechnen nichts.
- Schwellen verteilungsbasiert, nicht willkuerlich. 10k-Filter bleibt
  Quell-Metadatum, keine analytische Schwelle.
- Nur aggregierte Tier-/Fenster-Groessen, keine Wallet-Adress-Ausgabe.
- Nur Verdachts-/Auffaelligkeits-Diagnostik. Kein Insider-, Kausal-,
  Private-Information- oder Profitabilitaetsanspruch.
- Atomarer Commit. Danach `update_status`, WORK_LOG-Eintrag, `review_check`,
  `commit_plan`.

## Spaetere Erweiterung (nicht jetzt)
Funding-Quelle der Wallets (CEX/Mixer) und Wallet-Lebensdauer brauchen externe
On-Chain-Daten und ein neues Ingest. Erst nach diesem Modul. Out-of-Sample-Test
gegen dokumentierte Faelle ebenfalls spaeter.
