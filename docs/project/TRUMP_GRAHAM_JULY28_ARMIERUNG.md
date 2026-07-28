# Armierungs-Runbook: Trump-Tribute Lindsey Graham, 28.07.2026 (Event 745731)

Status: gebaut, getestet, im Live-Klon deployt — Task-Anlage durch die
Studentin steht aus. Erstellt 28.07. ~01:00 CEST nach dem Michigan-
Postmortem (dessen Zahlen: `TRUMP_MICHIGAN_JULY27_ARMIERUNG.md` §5).

## 1. Event

Trauerfeier fuer Senator Lindsey Graham, Washington National Cathedral,
**Di 28.07. 14:00 ET = 20:00 CEST** (Zeremonie-Beginn; Trumps
Tribute-Slot liegt IRGENDWO in der 1.5-2.5-h-Zeremonie). Event 745731,
20 Maerkte, Liq 66k / Vol 54k (27.07. abends), 17 offene Ausgaenge
0.10-0.90 — Einzelwoerter/Phrasen wie Patriot 0.815, Ukraine 0.76,
Sister 0.72, Nobody Like Him 0.515, Tough Cookie 0.345; einziges
Bracket "Hell" 2+. VIELE Fremdredner (Klerus, Familie, Politiker) —
die Sprecherbindung traegt hier alles.

## 2. Die drei Michigan-Lehren, alle umgesetzt (Commits bis 8f4c21e)

1. **Stream-Selbstheilung**: Stall-Detektor (WAV waechst 25 s nicht →
   /live-Kanaele mit Titel-Gate neu aufloesen, frische WAV anbinden,
   `transcriber.neue_quelle()`; Markt-Zaehler ueberleben). Auch ein
   sterbender ffmpeg loest jetzt Reconnect statt Lauf-Ende aus.
   Michigan verlor ~65 min in zwei Blindfenstern — u.a. den
   Supreme-Court-Fall (Reprice 0.19 → 0.97 um 20:13:27, 6 min NACH
   dem zweiten Einfrieren).
2. **Referenz aus der Event-Domaene**: Studio-Referenz auf PA-Audio =
   max 0.396 (haette JEDEN echten Trump-Treffer verworfen). Neue
   PA-Referenz aus den Transkript-verifizierten Trump-Passagen des
   Michigan-Mitschnitts: Trump ungesehen min 0.610/median ~0.77,
   Gaeste max 0.287, AXP-Fremde max -0.040. Profil faehrt die
   **Union PA+Studio, Schwelle 0.50**; Kopien liegen in
   `data/live/trump_graham_july28/`.
3. **`--fenster-modus` (Fallback)**: Sprecherbindung ueber das
   Operator-Fenster statt ECAPA — gezaehlt und gekauft wird NUR bei
   existierender Marker-Datei (kein Latch; loeschen pausiert wieder),
   Trigger auf dem Gesamtzaehler. Fuer den Fall, dass die
   Kathedral-Akustik die Zurechnung erneut verschiebt.

Unveraendert: Klausel-Gate ("if Trump says the listed term" — 19 aktiv,
1 Negations-Skip, live verifiziert), Trigger-Verify large-v3
fail-closed, NO zu, Kappe 100/Markt (2x50), Pool 650, Deckel 0.90,
Auto-Marker 6 Segmente (nur ECAPA-Modus).

## 3. Betriebsplan (Studentin)

1. **Task anlegen** (oder 19:45 Doppelklick `trump_graham_start_live.cmd`):
   `schtasks /Create /TN TrumpGrahamBot /TR "C:\Users\chole\ba-thesis\trump_graham_start_live.cmd" /SC ONCE /ST 19:45 /F`
   Rechner an + angemeldet; Standby ist seit gestern aus.
2. Ab 19:45 pollt das Skript WNCathedral → C-SPAN → ABC → NBC
   (Titel-Gate graham|lindsey|funeral|memorial|tribute) und startet
   den Bot LIVE. Kaufpfad bleibt zu, bis der Auto-Marker Trumps
   Stimme erkennt (Union-Referenz) — Fremdredner-Stunden davor
   koennen nie kaufen.
3. **Publikums-Check waehrend der Zeremonie** (optional, empfohlen):
   Wenn Trump am Pult ist und binnen ~90 s weder Auto-Marker noch
   ziel_counts kommen (Kathedral-Akustik-Fall), umschalten:
   `bot_stop.cmd` → `bot_stop_aufheben.cmd` → im Terminal
   `trump_graham_start_live.cmd` mit haendisch ergaenztem
   `--fenster-modus` ODER direkt:
   `set BOT_PROFIL=trump_graham_july28 && python -m operations.pipeline.earnings_bot --stream <url> --live --fenster-modus`
   dann `trump_graham_marker_an.cmd` bei Trump-Beginn,
   `trump_graham_marker_aus.cmd` bei Trump-Ende. Neustart vor Trumps
   Slot kostet nichts (nur seine Worte zaehlen).
4. Ende: laeuft selbst aus (240+30 min) oder `bot_stop.cmd`
   (danach `bot_stop_aufheben.cmd` nicht vergessen — Watchdog!).

## 4a. Lauf-Ergebnis 28.07. (Nachtrag der Abend-Session, 29.07. ~01:00)

**Betrieb:** Scheduled Task war auf 27.07. datiert und haette NIE
gefeuert (LastTaskResult 267011, NextRunTime leer) — um 18:20 mit
/SD 28.07.2026 neu angelegt. Feuer 19:45:01, Kathedral-Stream sofort
gefunden (19:45:24, LIVE, 22 aktive Maerkte — drei neue seit dem
DRY_RUN: Democrat, Top Five/Top Ten, Afghanistan). **Auto-Marker
20:24:49 nach 6 Segmenten** — die Union-Referenz PA+Studio trug in
der Kathedrale, kein Fenster-Modus noetig (Michigan-Lehre 2
validiert). Lauf endete 20:49:20 durch Schliessen des Task-Fensters
(forrtl window-CLOSE, ffmpeg starb zuerst als "prozess_beendet")
OHNE fertig-Event/Endcheck → **Betriebsregel: Laeufe NUR ueber
bot_stop.cmd beenden, nie uebers Fenster-X.**

**Ergebnis: 0 Fills, aber die Kette stand.** 8 der 11 YES-Woerter
live erkannt und large-v3-verifiziert (Sister, Military, Security,
Worker, Stop Calling Me, Golf, Patriot, Air Force), 0 Fehltrigger.
Kein Kauf: alles binnen Sekunden >=0.98 oder Buch leer; selbst der
0.41er "Stop Calling Me" war nach unserer ~20-s-Kette abgeraeumt.

**Stall #1 kostete alle drei Misses:** 20:30:06-20:31:00 (54 s;
Selbstheilung reconnectete 12 s nach Detektion — Michigan-Lehre 1
validiert, aber Erkennungsschwelle 40 s bleibt teuer). GENAU darin
fielen Supreme Court (~20:30:22, Reprice-Beleg), Democrat
(~20:30:46, Reprice 0.68→0.99) und Tough Cookie (~20:31:00). Die
Sekunden fehlen auch im Band — nicht rekonstruierbar.

**Sprecherbindung verhinderte einen Fehlkauf:** "Forever" stand im
Gesamtzaehler auf 2 (Fremdredner), resolvet NO — ohne ECAPA-Bindung
haette der Bot bei 0.745 gekauft (~-75 USD vermieden). Kein
Forever-Trigger wurde je ausgeloest: Bindung + Verify arbeiteten
korrekt.

**Hybrid-Duell Mensch vs. Bot — erster Sieg des Menschen:** Operator
hoerte per ffplay-Direktstream (~3-6 s hinter Saal) und kaufte IM
Bot-Blindfenster manuell Supreme Court YES @0.944 (105.9 sh) und
Tough Cookie YES @0.99 (101 sh); beide YES resolved → +5.90/+1.00.
Lehren: (1) Der Mensch ist die Stall-Redundanz. (2) Mit
Ohr-Bestaetigung ist Kaufen ueber dem 0.90-Modell-Deckel rational —
die Information ist besser als die Deckel-Annahme. (3) Die
"20 s vor mir"-Kaeufer waren Kontext-Antizipierer (Tough Cookie =
bekannte Trump-Wendung); Erstschlag bleibt unerreichbar.

**Kalibrier-Bilanz Graham: 23/23 resolved,** Bot-Zaehler konsistent
bis auf die drei Blindfenster-Misses; Forever-Diskrepanz ist
Fremdstimmen-Artefakt des Gesamtzaehlers (Kaufpfad korrekt).

## 4. Ehrliche Erwartung (Reprice-Messung Michigan)

Der Markt preist ein live mitgehoertes Wort in **1-4 Sekunden** ein
(Save America 19:32:34 0.87→0.98 in 2 s; Transgender 19:42:54 acht
Trades in EINER Sekunde, +4 s → 0.988; Supreme Court 0.19→0.97 in
1 s). Das Latenz-Rennen ist mit Stream-Verzug 15-30 s strukturell
verloren. Die realen Kanaele: (a) Woerter, die der Saal-Crowd
durchrutschen (Supreme Court stand 30 min bei 0.19, obwohl es um
19:41 noch 0.19er-VERKAEUFE gab — der Markt irrte lange), (b) das
Hell-2+-Bracket, (c) der Nachlauf, wenn MMs Quotes spaeter neu
stellen. Ein Tribute ist kurz (5-15 min) — wenige, dafuer klare
Chancen; fail-closed bleibt ueberall Prinzip.
