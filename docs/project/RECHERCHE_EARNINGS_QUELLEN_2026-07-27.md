# Recherche: Live-Quellen Earnings-Kandidaten 28./29.07. + Konzept Trump-Michigan

Erhoben 27.07.2026, ~13:00 UTC (Gamma-API + IR-Quellen + Presse). Zweck:
Quellenlage fuer die naechsten Earnings-Laeufe und Umsetzungs-Konzept fuer
das sprechergebundene Event "What will Trump say during remarks in Michigan".
Gegenstueck: `EARNINGS_BOT_PG_JULY29_ARMIERUNG.md` (Runbook, Prozess).

## 1. Terminuebersicht (alle Polymarket-Zeiten IR-bestaetigt, keine Dow-Falle)

| Event | Event-ID | Call/Rede | UTC | CEST | Quelle der Bestaetigung |
| --- | --- | --- | --- | --- | --- |
| Trump, GM Proving Ground Milford | 745732 | Mo 27.07. 15:00 ET (C-SPAN listet 14:50) | 19:00 | 21:00 | WXYZ/C-SPAN, 27.07. |
| PayPal Q2 2026 | 745733 | Di 28.07. 08:00 ET | 12:00 | 14:00 | IR-Eventseite investor.pypl.com |
| Boeing Q2 2026 | 745748 | Di 28.07. 10:30 ET | 14:30 | 16:30 | Boeing-PM 01.07. (mediaroom) |
| P&G Q4 FY25/26 | 715467 | Mi 29.07. 08:30 ET | 12:30 | 14:30 | P&G-PM 01.07. (us.pg.com/Businesswire) |

PayPal-Ende (~60 min) vor Boeing-Start: **Doppel-Lauf am 28.07. sequenziell
machbar**, ein GPU-Setup (small + large-v3, ~4-5 GB VRAM), >1 h Puffer.
Elon-/Trump-Wochenprofile sind seit 27.07. 03:59 UTC zu — keine GPU-Kollision.

## 2. Webcast-Zugang je Event (Weg zum Audio)

Alle Earnings-Laeufe wie beim AXP-Erstlauf: Zugang per Hand im Browser,
Bot hoert das Loopback-Geraet (`earnings_bot --geraet`). Kein Auto-Login.

- **PayPal:** Q4-Inc-Plattform `events.q4inc.com/attendee/222501806`
  (verlinkt von investor.pypl.com → Events). **Attendee-Registrierung
  noetig** (Name/E-Mail, Handarbeit im Browser). Am Vortag registrieren
  und Player testen.
- **Boeing:** Events-and-Presentations-Sektion auf `boeing.com/investors`.
  PM nennt keinen Registrierungszwang ("verify access prior to the
  event"); konkreter Player-Link erscheint auf der Events-Seite.
  Vortags-Check noetig (Runbook Schritt 2).
- **P&G:** offener Live-**Audio**-Webcast auf `pginvestor.com`
  ("Media and investors may access"), keine Registrierung erwaehnt.
  IR-Zeitverifikation damit erledigt: 8:30 ET = 12:30 UTC, deckt sich
  mit Profil `earnings_pg_july29` (`call_start_utc`).
- **Trump Milford:** frei empfangbare Streams — C-SPAN (Programmpunkt
  14:50 ET), erfahrungsgemaess zusaetzlich YouTube-Livestreams (White
  House, Lokalsender WXYZ Detroit, News-Kanaele). Stream-Latenz
  5-30 s. Zugang trivial; das Problem liegt in der Markt-Resolution (§4).

## 3. Marktstruktur der drei Earnings-Events (Gamma, 27.07. ~13:00 UTC)

- **PayPal (745733):** 19 Maerkte, Liq 21.1k, Vol 9.5k. Brackets:
  Quarter 15+, Consumer 10+, Transaction 5+, Merchant 5+ (alle >0.96
  vorgepreist). Dickes Mittelfeld fuer den AXP-Kanal (Aufmerksamkeits-
  Edge auf mittelpreisige Woerter): Stablecoin/Stable Coin 0.61,
  Agentic Commerce 0.52, Braintree 0.405, Stripe 0.30, Cash Back 0.265,
  Regulation-Familie 0.205, Anthropic/Claude 0.20, Stash 0.195,
  Block 0.145, Blockchain 0.135, Google 0.18, Bitcoin 0.09.
  Auffaellig viele **Oder-Fragen** ("Stablecoin" or "Stable Coin";
  "AI" or "Artificial Intelligence"; "Cash Back" or "Cashback";
  "Regulation" or "Regulator" or "Regulatory"; "Anthropic" or
  "Claude") — Regel-Builder auf Oder-Listen pruefen.
- **Boeing (745748):** 20 Maerkte, Liq 19.9k, Vol 16.5k. Brackets:
  Quarter 15+ (0.971), Consumer 10+ (0.031, quasi tot), Airplane 10+
  (0.98), Customer 3+ (0.98). Mittelfeld: Guidance 0.475 (!),
  Philippine Airlines 0.495, Tariff 0.38, Iran 0.355, Airbus 0.245,
  Dividend 0.22, Artemis/Moon je 0.165, Oil 0.12, Space 0.765,
  China 0.80. "Philippine Airlines" als Phrase → Komposita-Override
  pruefen.
- **P&G (715467):** unveraendert 22 Maerkte, Liq 31.5k. Stand heute:
  Customer 5+ 0.225, Valuation 0.15, Trump 0.11, World Cup 0.095,
  Restbrackets 0.046-0.058. Details im Runbook §2.

Beide neuen Events tragen den identischen Regeltext wie AXP/P&G
("mentioned by anyone", Resolution source: audio, No-Qualifying-Event-
Markt) — das Anyone-Gate laesst sie durch. Rolling Slugs: Refresh an
Event-ID 745733/745748 binden (bekannte Falle 3).

## 4. Trump-Michigan (745732): warum der earnings_bot hier zu Recht blockt

26 Maerkte, Liq 66.4k, Vol 115.1k — liquidestes Event der Mention-
Familie. Brackets: Percent 15+ (0.665), Joe/Biden 12+ (0.495),
Oil/Gas 10+ (0.445), Hell 7+ (0.695), Trump 5+ (0.745); dazu breites
Einzelwort-/Phrasen-Feld (Motor City 0.455, Drill Baby Drill 0.425,
Grocery/Dairy 0.465, Ethanol 0.285, Supreme Court 0.295, Mars 0.165 …).

**Drei strukturelle Unterschiede zu Earnings:**

1. **Sprecherbindung:** Resolution ist "if **Trump** says the listed
   term", nicht "mentioned by anyone". Unser Zaehler zaehlt den ganzen
   Audio-Feed — Vorredner (Lokalpolitik, ggf. GM-Fuehrung), Einspieler
   und Vorprogramm-Musik wuerden mitgezaehlt. Genau dafuer existiert
   das Anyone-Gate: es setzt alle 26 Maerkte auf SKIP. Korrekt.
2. **Die Crowd hoert zu:** 115k Volumen; Trump-Say-Maerkte sind das
   Flaggschiff der Serie, manuelle Live-Hoerer druecken Einzelwoerter
   in Sekunden. Der AXP-Kanal (von der Crowd ueberhoerte mittelpreisige
   Woerter) ist hier strukturell duenn. Verbleibender Kanal: exakter
   Zaehlstand auf den hohen Brackets (Percent 15+, Joe/Biden 12+,
   Hell 7+) ueber 60-90 min Redezeit — Verarbeitungs-, kein
   Latenzvorsprung (GM-/AXP-Befund).
3. **Startzeit-Chaos:** Trump-Events starten regelmaessig 30-60+ min
   verspaetet; Vorprogramm laeuft auf demselben Stream. Leere/fremde
   Chunks kosten nichts, aber die Sprecherbindung (Punkt 1) wird
   dadurch zum Hauptrisiko.

**Umsetzungs-Konzept (fuer die wiederkehrende Trump-Serie, nicht fuer
heute):** neues Profil-Flag `sprecher_modus` fuer Einzelsprecher-Events:

- Kaufpfad bleibt gesperrt, bis der Operator einen **Sprecher-Marker**
  setzt (Mechanik analog Kill-Switch: Datei `data/live/SPRECHER_AKTIV`
  oder Konsolen-Eingabe), sobald Trump am Pult steht.
- Beim Marker: **Zaehler-Reset** (alles vor dem Marker zaehlt nicht zur
  Resolution) — der Vorredner-Zaehlstand wird verworfen, laeuft aber im
  Log weiter (Kalibrierungs-Daten).
- Trigger-Verify (large-v3, fail-closed) bleibt an — faengt Musik-/
  Halluzinations-Trigger; gegen echte Vorredner-Woerter hilft nur der
  Marker. Restrisiko dokumentieren: Q&A-/Zwischenrufe zaehlen nicht als
  "Trump says" (Resolution), landen aber im Feed; bei Remarks ohne Q&A
  klein.
- NO-Seite bleibt zu (Capture-Abdeckung ungeloest, hier verschaerft
  durch Startzeit-Chaos).

**Option fuer heute Abend (21:00 CEST), falls Kapazitaet:** reiner
**Paper-/Messlauf** im ba-thesis-Klon — C-SPAN/YouTube im Browser auf
Loopback, `earnings_bot --geraet` OHNE `--live` mit ad-hoc-Profil, oder
nur Tape-Mitschnitt. Ertrag: fuenfter Reprice-Datenpunkt (erstes
Polit-Event), Vorredner-Tape zur Kalibrierung des Sprecher-Markers,
Bracket-Zeitreihe gegen 66k-Liquiditaet. Kein Echtgeld ohne
Sprecher-Gate.

## 5. Offene Entscheide (Studentin)

1. **Profile Boeing + PayPal anlegen?** Vorlage AXP/P&G, je ~1 h inkl.
   Offline-Tests; muesste am 27.07. passieren (Calls 28.07. 12:00 /
   14:30 UTC). Danach uebliche Armierungs-Schritte im Runbook.
2. **Budget je Lauf** (Platzhalter 100 USD; drei Laeufe in 27 h —
   Wallet-Stand gegen parallele Profile pruefen).
3. **ToS-Frage Webcast-Mitschnitt** (Runbook §4.1) — unveraendert offen,
   gilt fuer alle drei Earnings-Events; PayPal-Registrierung akzeptiert
   ggf. explizite Teilnahmebedingungen (beim Registrieren pruefen).
4. ~~Sprecher-Marker-Feature fuer die Trump-Serie bauen~~ **GEBAUT
   27.07. nachmittags** (User-Entscheid, Fokus auf heute): Profil
   `trump_michigan_july27` mit Klausel-Gate, ECAPA-Zurechnung
   (ziel_count) und Operator-Marker; Suite 1062 gruen. Statt des
   urspruenglichen Zaehler-Reset-Konzepts traegt die vorhandene
   ECAPA-Infrastruktur die Sprecherbindung — der Marker ist das
   zusaetzliche harte Zeit-Gate. Runbook:
   `TRUMP_MICHIGAN_JULY27_ARMIERUNG.md`.
