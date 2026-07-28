# Übergabe 28.07.2026 abends: Live-Mentions-Strecke — Stand, Erkenntnisse, Graham-Lauf, offene Aufgaben

Zweck: Eine NEUE Claude-Session übernimmt ab hier (diese Datei zuerst
lesen, dazu SYNC_KONTEXT, PROJEKT_INVENTAR und die Runbooks unten).
Geschrieben von der Tages-Session am 28.07. ~19:10 CEST, vor dem
Graham-Lauf (Task feuert 19:45 automatisch).

## 1. Setup-Stand (alles deployt und verifiziert)

- **ba-thesis läuft auf Branch `feat/earnings-bot`** (seit heute früh;
  Handkopien-Betrieb beendet, origin/main inkl. elon_july27/
  trump_july27 gemergt, Commit a123846 ff.). Zweit-Klon
  (`Projects\multi-agent-...`) ist die Arbeitskopie; Deploy = commit/
  push dort, `git pull` im ba-thesis.
- Tests zuletzt 1108+ grün; jeder Lauf-Tag hat ein eigenes Runbook:
  `TRUMP_MICHIGAN_JULY27_ARMIERUNG.md` (Postmortem §3b/§5),
  `TRUMP_GRAHAM_JULY28_ARMIERUNG.md` (heute Abend, §3 Betriebsplan),
  `EARNINGS_BOT_PG_JULY29_ARMIERUNG.md` (morgen),
  `RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md` (Quellen/Zeiten).
- **Boeing lief als erster large-v3-Hauptlauf** (Profil-Feld
  `transcriber_modell`), Verify teilt sich die Modell-Instanz
  (`large-v3/geteilte-instanz` im trigger_verify_bereit-Event).
  PayPal/P&G stehen noch auf small — **P&G morgen auf large-v3
  umstellen ist offene Aufgabe** (User-Wunsch, 1-Zeilen-Profiledit).

## 2. Die Läufe von heute (28.07.)

| Lauf | Ergebnis | Kern |
| --- | --- | --- |
| PayPal (12:00 UTC, small) | **1 Fill: Users YES @0.64, 25.12 Shares ≈ 16.08 USD** (on-chain 12:15:44 verifiziert; Markt resolvet Richtung 1.0 → ~+9 USD). 394 Chunks, null Lücken | Treffer lag IM 7-s-Reprice-Fenster (12:12:58→12:13:05); Kauf kam aus dem Vorscan-Re-Check in den Zweifel-Rücksetzer |
| Boeing (14:30 UTC, large-v3) | 0 Fills, 457 Chunks bis Call-Ende (Ctrl+C 15:30:40), 7 Verify-OKs | Alles Kaufbare war vorgepreist; „Space" zeigte: Markt springt 17–20 s VOR unserer Verify |

**Offener Prüfpunkt:** PayPal-`fertig`-Event meldet `ausgegeben_usd
0.0` trotz on-chain-Fill — vermutlich Buchführungs-Detail des
Executors; morgen per Wallet-Delta-Abgleich klären (Vorbild
`wallet_abgleich_2026-07-18.json`).

## 3. Die sieben Kern-Erkenntnisse (mit Belegen)

1. **Latenz-Rennen ist verloren, endgültig:** Markt preist gehörte
   Wörter in 1–4 s ein (Trades: Save America 2 s, Transgender 1 s,
   Supreme Court 1 s, Space 3 s); wir liegen 17–20 s hinter den
   schnellsten Menschen (Kette: Player 2–5 s + Chunk 0–10 s +
   large 0.8 s + Verify 1–3 s + Order ~1 s).
2. **Menschen antizipieren — und irren:** Boeing „Guidance": 485
   Shares @0.455 exakt beim Outlook-Thema, ABER das Wort fiel nie
   (Goldstandard-Pass). Die Irrtümer der Antizipierer sind unser
   +Kanal: alle DREI bisherigen Fills (AXP Luxury/Fraud, PayPal
   Users) kamen aus Zweifel-Fenstern/Rücksetzern, nie aus
   Erst-Erkennung.
3. **large-v3 als Hauptmodell:** +0.53 s je 10-s-Chunk (Benchmark),
   dafür Eigennamen-Recall (Braintree: large 10 Nennungen, small live
   2 — die Erstnennung 12:02 ging small durch die Lappen).
4. **Abwesenheits-Beweise nur per VAD-freiem Vollpass:** Batched-
   Transkription hat VAD-Löcher — PayPal „agentic commerce" fiel
   GENAU in eins (Batch-Pass: 0; VAD-frei: 1 — Markt 0.92 hatte
   recht). Boeing-Goldstandard (76.5 min VAD-frei, 9.4 min GPU):
   **elf offene Wörter alle 0** (guidance/tariff/fraud/oil/china/
   philippine/iran/airbus/artemis/dividend/moon; Preise 0.11–0.50).
   Vollpass-Transkripte liegen je Lauf-Ordner (`vollpass_*.txt`).
5. **Resolutions-Risiko ist real und LIVE beobachtbar:** Boeing
   „Guidance" ist trotz 0 Nennungen **YES proposed**
   (umaResolutionStatus, Preis 0.995). → §4 Beobachtungsauftrag.
6. **Sprechergebundene Events:** Referenz MUSS aus der Event-
   Übertragungskette stammen (Michigan: Studio-Referenz max 0.396
   auf PA-Audio; PA-Referenz trennt 0.610 vs. 0.287); Stream-
   Selbstheilung (Stall-Detektor+Reconnect) und `--fenster-modus`
   existieren seit heute Nacht.
7. **PayPal-NO-Korb (batched, NICHT handelsreif):** stablecoin/
   stripe/block/regulation alle 0 im Batch-Pass bei Preisen ~0.48–
   0.58 — vor jeder Aussage VAD-freien Vollpass über das PayPal-Band
   fahren (steht aus, §6).

## 4. Guidance-UMA-Fall: Beobachtungsauftrag (Kalibrierpunkt #0)

Wort fiel nachweislich nicht (VAD-freier Goldstandard über das
komplette Band), trotzdem YES proposed. Ablauf: Proposal mit Bond →
~2-h-Challenge-Fenster → ohne Dispute FINAL (dann zählt der Resolver-
Irrtum wie ein echter Fall); mit Dispute → UMA-DVM-Abstimmung (~48 h).
**Auftrag an die nächste Session:** `umaResolutionStatus` +
Endergebnis aller heutigen Prognose-Märkte verfolgen (Gamma, Events
745733/745748) und als Kalibrier-Tabelle Vollpass-Prognose vs.
UMA-Endergebnis in dieses Dokument nachtragen. Resolvet Guidance
trotz 0 Nennungen YES, ist das ein hartes Warnsignal für die gesamte
Late-NO-Idee (Resolver zählen anders als das Audio).

### §4-Nachtrag der Übernahme-Session, 28.07. ~19:00 CEST

**PayPal (745733) ist final: 18/19 resolved** (nur Agentic Commerce
noch proposed→YES 0.9995). Kalibriertabelle VAD-freier Vollpass
(30-s-Raster, large-v3, Goldstandard-Methode) vs. UMA-Endergebnis:

| Markt | Schwelle | Vollpass | UMA | Deckung |
| --- | --- | --- | --- | --- |
| Quarter 15+ | 15 | 52 | YES | ✓ |
| Transaction 5+ | 5 | 30 | YES | ✓ |
| Consumer 10+ | 10 | 16 | YES | ✓ |
| Braintree | 1 | 10 | YES | ✓ |
| AI/Artificial Intelligence | 1 | 4 | YES | ✓ |
| Merchant 5+ | 5 | 7 | YES | ✓ |
| Users (unser Fill) | 1 | 2 | YES | ✓ |
| Anthropic/Bitcoin/Block/Blockchain/Cash Back/Google/Regulation/Stablecoin/Stash/Stripe | je 1 | alle 0 | alle NO | ✓ |
| **Agentic Commerce** | 1 | **0** | **→YES** | **✗ Zählartefakt** |

**Agentic-Forensik (Methodik-Befund, wichtig für §6.1):** Das Wort
fiel ~717-721s — mein 30-s-Raster schneidet GENAU dort (Block 690s
endet "…such as agentic", Block 720s beginnt "meaningful
contributors"; die Grenzsekunden fehlen, Whisper verwirft das
angeschnittene Segment). Zusätzlich 2550s phonetische Verschreibung
"agent e-commerce" (= agentic commerce fürs Ohr, 0 für jeden
Text-Zähler). Der Live-Batch-Pass verlor dieselbe Stelle durch ein
VAD-Loch. → Late-NO-Kette braucht: überlappende Fenster, Matching
über Blockgrenzen, Ausschluss von Neologismen (agentic), und
Zwei-Methoden-Konsens vor jedem NO. Der Markt (0.92) und UMA hatten
recht; KEIN Resolver-Irrtum.

**Boeing (745748), Stand 19:00:** Delivery, Space, "not air"
resolved (alle ✓ zur Erwartung); Rest proposed — **Guidance weiter
YES proposed (0.995) trotz Goldstandard-0, Kalibrierpunkt #0 offen.**
Markt-Zweifel trotz Vollpass-0 bei Oil (0.44) und Philippine
Airlines (0.18).

**§2-Prüfpunkt geklärt (ausgegeben_usd 0.0):** execution.py
`_budget_sync()` ersetzt die korrekte post_antwort-Summe (16.08)
durch start_balance−aktuell; der Server-Balance-Cache war Sekunden
nach dem FAK-Fill noch stale, danach kam nie eine weitere Order →
kein Re-Sync. Buchführungs-, kein Geldproblem. On-chain bestätigt:
12:15:44Z, 25.12 sh @0.64 = 16.08 USD (tx 0x326ae5…7917).
Fix-Idee (offen): Delta nur übernehmen wenn ≥ Fill-Summe; Sync vor
dem fertig-Event.

**Wallet-Befund 13:23:49Z (15:23 CEST):** BUY NO @0.149, 67.11 sh
= 10 USD auf Agentic Commerce — OHNE Bot-Log (Bot kauft nie NO);
vermutlich manueller Late-NO-Versuch auf Batch-Pass-Basis. Markt
resolvet YES → −10 USD. Live-Beleg für "NIE NO ohne VAD-freien
Vollpass" (und selbst der reicht allein nicht, s.o.).

## 5. Graham-Lauf HEUTE 19:45 (Task `TrumpGrahamBot` feuert selbst)

Rollen: Der Task startet, findet den Stream (WNCathedral→C-SPAN→ABC→
NBC, Titel-Gate graham|lindsey|funeral|memorial|tribute), Kaufpfad
bleibt zu bis der Auto-Marker Trumps Stimme erkennt (Union-Referenz
PA+Studio, Schwelle 0.50). Budget 650, Kappe 100/Markt. Die Session
ueberwacht NUR (Monitor unten) und greift bei zwei Szenarien ein:

1. **Kein Stream gefunden** (start_log zeigt Poll-Zeilen ohne
   Treffer): Kanalliste/Titel-Gate pruefen, ggf. manuell Watch-URL
   per yt-dlp aufloesen und Bot mit `--stream <url> --live` starten.
2. **Trump spricht, aber kein Auto-Marker/keine ziel_counts binnen
   ~90 s** (Kathedral-Akustik): Umschalten auf Fenster-Modus —
   Playbook exakt in `TRUMP_GRAHAM_JULY28_ARMIERUNG.md` §3 Punkt 3
   (`bot_stop.cmd` → `bot_stop_aufheben.cmd` → Neustart mit
   `--fenster-modus` → Marker-an/aus-cmds). Neustart vor Trumps Slot
   kostet nichts.

Monitor-Kommando fuer die neue Session (persistent, meldet Kaeufe/
Marker/Fehler/Ende):

    cd /c/Users/chole/ba-thesis && tail -n 0 -f data/live/trump_graham_july28/bot_events.jsonl | python -u -c "<Filter wie in den heutigen Sessions: art in (audio_laeuft, sprecher_marker_gesetzt, trigger_verifikation, yes_entscheidung[action=YES], stream_stall, stream_reconnect, fehler, call_ende, fertig)>"

Nach dem Lauf: Auswertung wie heute (Events, Gamma-Preise, Trades der
gefallenen Woerter, VAD-freier Vollpass), Ergebnis in Runbook §-Neu.

## 6. Offene Aufgaben (Reihenfolge)

1. **Heute Abend nach Graham: Late-NO-Kette bauen** (User-Go liegt
   vor): VAD-freier Vollpass nach Call-Ende als NO-Quelle, nur
   Brackets ≤ 0.7×Schwelle und Einzelwoerter mit Vollpass-0 ohne
   Eigennamen-/Homophon-Risiko, Preisdeckel ~0.60–0.70, kleine Clips
   (15er), NIE Live-NO. Vorher Homophon-Luecke im erweiterten Zaehler
   fixen (offenes Review, siehe Memory). Scharf erst nach
   Kalibrier-Abgleich (§4) — P&G morgen laeuft NO weiter im
   Beobachtungsmodus.
2. **P&G morgen 12:30 UTC (14:30 CEST):** Profil `earnings_pg_july29`
   auf `transcriber_modell: large-v3` stellen (+Test), Budget-Frage
   an User (aktuell Platzhalter 100/15×10 — heute liefen 650/50×40),
   Runbook-Schritte 2–7; Start wie heute per Loopback.
3. PayPal-`ausgegeben_usd`-Diskrepanz klaeren (Wallet-Delta).
4. VAD-freier Vollpass ueber das PayPal-Band (NO-Korb §3.7 belastbar
   machen) — GPU-Zeit ~10 min.
5. Kalibrier-Tabelle §4 fortschreiben, sobald UMA-Resolutionen final.
6. Idee aus dem Tages-Gespraech, unpriorisiert: Live-Zaehlstand-Panel
   als Info-Edge fuer manuelles Handeln (Hybrid Mensch+Maschine).

## 7. Session-Regeln (Betriebshandbuch-Kurzform)

Neue Session im Ordner `C:\Users\chole\Projects\multi-agent-...`
starten (eine aktive Session je Ordner; die Tages-Session vom 28.07.
wird danach geschlossen). Live-Daten/GPU liegen im ba-thesis-Klon —
Kommandos dorthin wie heute per absolutem Pfad. Niemals fremde
uncommittete Aenderungen anfassen; `data/results/*`-Diffs sind
Ketten-Artefakte. STOP-Datei nach jedem Notaus wieder aufheben
(`bot_stop_aufheben.cmd`) — sie blockt sonst ALLE Bots inkl. Watchdog.
