# All-In E284, Lauf 07./08.08.2026 — 0 Fills, NO-Chance um 6 Minuten verfehlt

Zweck: Ergebnisdokumentation des Laufs `allin_august7` (Event 790609) und
Fortschreibung der Spread-Messreihe aus `ALLIN_JULY31_LAUF.md`. Zwei
Kernbefunde: die Messreihe reproduziert sich, und erstmals laesst sich
der ZEITLICHE Preis der NO-Pruefkette exakt beziffern.

## 1. Aufsetzung und Ablauf

Profil als 1:1-Kopie der E283-Woche, nur Event, Lauf-Ordner und Budget
neu (Commit `fa16da7`). Brett diesmal 11 statt 18 Maerkte, mit
angehobenen Schwellen: AI 50+ (war 35+), Anthropic 5+ (war 3+).
Budget 680 von 711.58 pUSD.

| Zeit (UTC) | Ereignis |
| --- | --- |
| 07.08. 16:10:19 | Start, 10 aktive Maerkte, Basisraten (11 Wochen) |
| 08.08. 01:29:12 | **Drop** — `mp3_url_prober`, ALLIN-E284_Ch.mp3 (108 MB) |
| 01:30:09 | Chunk 1, danach YES-Endchecks (6 Maerkte) |
| 01:34:24 | NO-Konsens large-v3: **248.2 s**, 170 Segmente |
| 01:36:12 | Gap-Verify: eine Luecke 4457.5-4517.4 s, Delta 0 |
| 01:36:12 | NO-Runde (10 Maerkte) |
| 03:07:32 | `fertig` — 0 Kaeufe, 0.00 USD |

Drop um 01:29 UTC = der spaeteste der bisherigen fuenf Laeufe (20:52 /
22:12 / 22:49 / 00:47 / 01:15). Das Watchdog-Fenster war vorsorglich auf
09.08. verlaengert worden. Kein Fehler-Event im gesamten Lauf.

## 2. Zaehlergebnis

| Zaehler | Maerkte |
| --- | --- |
| >= 1 | AI 50, Hundred/Thousand/Million 24, Anthropic 18, SpaceX 16, IPO 10, Software 9, Nvidia 5 |
| 0 | Red, Blue, Stock Market (je auch erweitert 0) |

Merke zum `erweitert_count`: er liegt durchgehend bei rund dem Doppelten
des Live-Zaehlers (50->99, 24->44, 18->40, 16->33, 10->20, 9->18, 5->11;
identisches Bild am 31.07.). Er ist also keine bessere Schaetzung des
wahren Zaehlstands, sondern eine konservative Obergrenze aus zwei
summierten Durchlaeufen. Fuer seinen einzigen Zweck — NO-Kaeufe blocken —
zeigt die Verzerrung in die sichere Richtung.

## 3. Warum 0 Fills

**YES (6 Endchecks):** ausnahmslos `yes_ask 0.97-0.99 > 0.9`. Die Mauer
stand schon 57 Sekunden nach dem Drop.

**NO (10 Runden):** von den drei Null-Zaehlern blockierte
- **Basisraten-Veto:** Blue (0.83, n=6). Insgesamt sperrte das Veto 6 der
  10 Maerkte schon vor dem Lauf (Anthropic 1.00 n=18, Software 1.00 n=11,
  Hundred 1.00 n=6, IPO 1.00 n=5, AI 0.93 n=14, Blue 0.83 n=6).
- **Preisdeckel 0.80:** Red (`no_ask 0.99`), Stock Market (`no_ask 0.96`)
  — Gruende woertlich aus `decisions_log.jsonl`.

## 4. Der Red-Fall: die Kette kostete den Trade (Kernbefund)

Red war der einzige Markt des Abends, bei dem alle inhaltlichen Tore
offen standen: Zaehler 0, erweiterter Zaehler 0, kein Veto. Der Buchlog
zeigt, dass auch der Preis passte — bis kurz vor der Runde:

| Zeit (UTC) | Red, YES-Seite | NO-Ask (abgeleitet/gemessen) |
| --- | --- | --- |
| 07.08. 16:10 - 08.08. 01:28 | Bid **0.36** konstant, 9 h | ~0.64 |
| 01:29:12 | **Drop** | |
| 01:30:09 | Bid weiter **0.36** | ~0.64 — unter dem Deckel 0.80 |
| 01:36:14 | NO-Runde | **0.99 gemessen** -> abgelehnt |

Zwischen der letzten Buchzeile mit 0.36 (01:30:09) und der NO-Runde
(01:36:14) liegen 6 Minuten — und exakt darin liegt die Pruefkette:
NO-Konsens large-v3 248 s plus Gap-Verify. Die Gegenseite verschwand
in genau diesem Fenster.

**Der Zielkonflikt, sauber belegt auf drei Wochen:**

| Woche | Was die Kette tat | Wirkung |
| --- | --- | --- |
| 24.07. | Innovation: Zaehler 0, KEIN Nachbarschafts-/Vetocheck griff | NO gekauft, loeste YES auf — Verlust |
| 31.07. | Veto stoppte SpaceX (0.83) und Blue (1.00) | Zwei vermutliche Verluste verhindert |
| 07.08. | Konsens+Gap-Verify kosteten 6 Minuten | Red-NO @0.64 verpasst |

Die Kette ist also nachweislich beides: nuetzlich und teuer. Kein Bug,
sondern ein echter Zielkonflikt.

**Ansatzpunkt fuer spaeter (nicht umgesetzt):** Der teure Teil ist der
large-v3-Konsens ueber die GANZE Episode (248 s). Fuer einen
Schwelle-1-Markt mit Live-Zaehler 0 lautet die Frage aber nur, ob das
Wort irgendwo faellt — eine gezielte Suche koennte das schneller
beantworten als ein vollstaendiger Zweitdurchlauf. Umbau an der
Sicherungskette, daher bewusst nicht im laufenden Betrieb entschieden.

## 5. Spread-Messreihe: reproduziert

Median-Spread der YES-Seite, stuendlich (aus `orderbook_log.csv`):

| Stunde (UTC) | 31.07. (Drop 22:49) | 07./08.08. (Drop 01:29) |
| --- | --- | --- |
| 14 | 0.230 | — |
| 15 | 0.380 | — |
| 16 | 0.460 | 0.465 |
| 17 | 0.460 | 0.465 |
| 18 | 0.460 | 0.465 |
| 19 | 0.510 | 0.470 |
| 20 | 0.510 | 0.470 |
| 21 | 0.510 | 0.510 |
| 22 | **0.620** | 0.510 |
| 23 | — | 0.510 |
| 00 | — | 0.515 |
| 01 | — | 0.515 |

Die Werte 16:00-21:00 stimmen auf wenige Tausendstel ueberein. Der breite,
stille Markt ist damit der NORMALZUSTAND vor dem Drop, nicht die
Ausnahme — die Hypothese vom 31.07. haelt, N=2.

Offen bleibt der 22:00-Sprung auf 0.620 am 31.07. (Drop 49 min spaeter),
dem diese Woche nichts entspricht (Spread flach bei 0.510-0.515, Drop
erst um 01:29). Kandidat fuer ein Vorlaufsignal, aber N=1 — naechste
Woche gezielt auf die letzte Stunde vor dem Drop schauen.

Die Messreihe der Vorwoche begann um 14:00 mit 0.230; diese Woche wurde
erst um 16:10 armiert, der Anstieg 14:00-16:00 ist also unbeobachtet.
**Konsequenz fuer E285: frueher armieren**, damit die Reihe den Beginn
des Aufreissens erfasst.

## 6. Buchhaltung

`ausgegeben_usd 0.0` ist korrekt. Wallet vor dem Lauf 711.58, danach
626.65 — das Delta von −84.93 stammt vollstaendig aus VIER MANUELLEN
Trades auf die President-Curtis-Mention-Maerkte am 07.08. (Secret 38.94,
Paranormal 16.54, Rick 13.45 um 19:56; Ghost 16.00 um 22:46; Summe
84.93). Keine Bot-Bewegung.

## 7. Einordnung in die Strecke

Fuenfter Lauf in Folge ohne Fill, auf drei Shows und zwei Bot-Typen:

| Datum | Lauf | Befund |
| --- | --- | --- |
| 31.07. | All-In E283 | Asks auf 0.98 gemauert, Zaehler 17/17 deckungsgleich |
| 05.08. | JRE #2535 | 5 von 8 Maerkten OHNE jedes Ask, Rest 0.99 |
| 07.08. | Elon (Texas) | Treffer erkannt, `best_ask: null` |
| 07./08.08. | All-In E284 | YES gemauert, NO-Chance in 6 min verschwunden |

Das Muster ist auf beiden Seiten dasselbe: Die Liquiditaet ist vor dem
Ereignis breit und still, und im Moment der Information verschwindet
sie, statt sich zu bewegen.

## 8. Offen

1. Nachbarschafts-/Homophon-Filter fuer die NO-Seite weiterhin nicht
   gebaut; das Basisraten-Veto traegt die Absicherung allein und hat das
   auch diese Woche getan (6 von 10 Maerkten gesperrt).
2. Beschleunigung der NO-Kette (siehe §4) — Entscheid offen.
3. Frueheres Armieren fuer die vollstaendige Spread-Messreihe (§5).
