# All-In E283, Lauf 31.07.2026 — 0 Fills, Liquiditaetsentzug vor dem Drop

Zweck: Ergebnisdokumentation des Laufs `allin_july31` (Event 758791).
Kernbefund ist nicht das Handelsergebnis, sondern eine Messreihe: die
Ask-Seite wurde Stunden VOR dem Informationsereignis abgezogen. Die
Vergleichsmessung naechste Woche entscheidet, ob das Reaktion oder
Zufall war.

## 1. Aufsetzung

Profil `allin_july31` als 1:1-Kopie der E282-Woche, nur Event, Lauf-
Ordner und Gesamtbudget neu (Commit `8602e3a`).

| | |
| --- | --- |
| Event | 758791, 18 Maerkte, Serie 11300 |
| Budget | 620 pUSD (Wallet 643.67, User-Freigabe "volles Budget") |
| Clip / Sweep | 50 USD x bis zu 40 Clips (budget-, nicht clip-limitiert) |
| Nachlauf | 90 min |
| Transcriber | `small` im Livepfad (Default), Gap-Verify und NO-Konsens large-v3 |
| Vorflug | E282 HTTP 200 (134 964 123 B), E283 404 -> Prober feuert bei Minute 0 |

Regeltext gegen july24 gelesen: gleiche Schablone (Playlist-Regel,
Audio als Aufloesungsquelle, Specials zaehlen nicht). Tests 1181 gruen.

## 2. Ablauf

| Zeit (UTC) | Ereignis |
| --- | --- |
| 14:35:04 | Start durch Watchdog, 17 aktive Maerkte, Basisraten (13 Wochen) |
| 14:35:53 | Whisper bereit, cuda/float16 |
| 22:49:02 | **Drop erkannt** — `mp3_url_prober`, ALLIN-E283_Ch.mp3 |
| 22:49:26 | MP3 vollstaendig (139 MB in 24 s) |
| 22:50:28 | YES-Endchecks (10 Maerkte) |
| 22:55:36 | NO-Konsens large-v3: 306 s, 206 Segmente |
| 22:59:26 | Gap-Verify: eine Luecke 5733.4-5793.1 s, **Delta 0** |
| 22:59:26 | NO-Runde (17 Maerkte) |
| 00:29:40 | `fertig` — 0 Kaeufe, 0.00 USD |

Drop-Zeit im historischen Mittelfeld (bisher 20:52 / 22:12 / 00:47 /
01:15 UTC). Kein Fehler-Event im gesamten Lauf.

## 3. Zaehlergebnis: 17 von 17 Maerkten deckungsgleich mit dem Markt

Nach der Neubepreisung stimmt unser Transkript mit dem Markt in JEDEM
Markt ueberein — kein Zweifelsfall, kein Zaehlartefakt.

| Zaehler | Maerkte | Markt danach |
| --- | --- | --- |
| >= 1 | AI 52, Hundred/Thousand/Million 33, Anthropic 20, China 19, Regulatory 6, Red 3, Software 3, Nvidia 2, Europe 1, Innovation 1 | YES-Ask 0.98-0.998 |
| 0 | Canada, Blue, Cancer, Constitution, Disruptive, Stock Market, SpaceX (3+) | YES-Ask 0.049-0.05 |

Einzige Restunschaerfe: SpaceX (Schwelle 3+) steht nach der Episode bei
0.27 — der Markt zweifelt dort selbst.

## 4. Warum 0 Fills — beide Seiten, verschiedene Ursachen

**YES:** alle 10 Endchecks mit `yes_ask 0.98/0.99 > 0.9` abgelehnt. Die
Mauer stand bereits 86 s nach dem Drop. Der Bot war NICHT zu langsam —
es gab kein Angebot.

**NO:** sieben Maerkte mit Zaehler 0 und erweitertem Zaehler 0.
Geblockt durch:

- **Basisraten-Veto:** SpaceX (0.83, n=6) und Blue (1.00, n=5). Beide
  lagen unter dem 0.80-Deckel und waeren sonst gekauft worden. Das
  Schild sagt: Historie sagt, das Wort faellt praktisch immer — eine 0
  ist eher ASR-Verpasser als echte Abwesenheit. Nach dem
  Innovation-Verlust der Vorwoche (Zaehler 0, loeste YES auf) die
  richtige Bremse.
- **Preisdeckel 0.80:** Canada 0.85, Cancer 0.89, Disruptive 0.91,
  Constitution 0.92, Stock Market 0.95.

Alle Tore haben also getan, wofuer sie gebaut wurden. 0 Fills ist das
korrekte Ergebnis, keine Fehlfunktion.

## 5. Die Messreihe (Kernartefakt)

Median-Spread der YES-Seite, stuendlich, aus `orderbook_log.csv`:

| Stunde (UTC) | 24.07. (Drop 20:52) | 31.07. (Drop 22:49) |
| --- | --- | --- |
| 14 | — | 0.230 |
| 15 | 0.050 | 0.380 |
| 16 | 0.050 | 0.460 |
| 17 | 0.050 | 0.460 |
| 18 | 0.050 | 0.460 |
| 19 | 0.050 | 0.510 |
| 20 | 0.050 | 0.510 |
| 21 | — | 0.510 |
| 22 | — | 0.620 |

Vorwoche: konstant 0.050 ueber den gesamten Lauf, bis in den Drop
hinein. Diese Woche: monoton aufreissend, am steilsten unmittelbar vor
dem Drop. Einzelverlauf (Ask, UTC):

```
nvidia        14:35 0.71   15:12 0.93   15:47 0.98 ... 19:20 0.98
cancer        14:35 0.58   15:12 0.94   16:23 0.98 ... 19:20 0.98
constitution  14:35 0.38   15:47 0.95   18:09 0.98 ... 19:20 0.98
blue          14:35 0.72   16:23 0.95   18:09 0.98 ... 19:20 0.98
```

Die Bid-Seite blieb dabei intakt (0.08-0.92). Gamma bestaetigt die
Werte unabhaengig von unserer Kette — kein Datenartefakt.

## 6. Kontrafaktisch: was der Entzug gekostet hat

Haette das Buch um 22:50 ausgesehen wie in der Vorwoche, waeren mit
unserem Zaehlstand vier Maerkte unter dem 0.90-Deckel kaufbar gewesen —
alle vier loesen YES auf:

| Markt | Ask nachmittags | Zaehler | Ergebnis |
| --- | --- | --- | --- |
| Europe | 0.63 | 1 | YES (+59 %) |
| Innovation | 0.66 | 1 | YES (+52 %) |
| Nvidia | 0.71 | 2 | YES (+41 %) |
| Red | 0.77 | 3 | YES (+30 %) |

Vorwoche kaufte der Bot 60 s nach dem Drop zu 0.29/0.33/0.88, weil der
Markt die Episode noch nicht gelesen hatte. Dieses Fenster wurde diesmal
nicht durch schnellere Konkurrenz geschlossen, sondern vorab
ausgeraeumt.

## 7. Hypothese und Test

**Hypothese:** Der Maker hat nach dem E282-Sweep (7 Fills, davon 4 NO)
gelernt und zieht vor dem Informationsereignis die Offers. Der Edge
verschwindet dann nicht ueber Latenz, sondern ueber Liquiditaet.

**Gegenhypothese:** Zufall / einzelner abwesender Maker. N=1.

**Test naechste Woche (E284):** dieselbe stuendliche Spread-Messung ab
Bot-Start. Bleibt der Spread eng, war es Zufall; reisst er erneut vor
dem Drop auf, ist es Reaktion. Die Messung faellt ohne Zusatzaufwand an
— `orderbook_log.csv` schreibt der Bot ohnehin.

## 8. Buchhaltung

`ausgegeben_usd 0.0` ist hier korrekt (nicht der PayPal-Buchungsfall):
Wallet 14:26 = 643.67, nach dem Lauf 669.86. Das Delta +26.19 sind
fuenf REDEEMs auf manuelle AI-Modell-Positionen (4x Anthropic, 1x
Google, 18:08 und 21:35-21:37), keine Bot-Bewegung.

## 9. Offen

1. Nachbarschafts-/Homophon-Filter fuer die NO-Seite weiterhin nicht
   gebaut (Lehre aus Agentic/Guidance und dem Innovation-Verlust).
   Solange traegt das Basisraten-Veto die Absicherung allein — es hat
   diese Woche zweimal korrekt gegriffen.
2. Livepfad laeuft auf `small`. Umstellung auf large-v3 stand zur
   Entscheidung, blieb unbeantwortet. Diese Woche ohne Folgen: der
   Zaehlstand war 17/17 deckungsgleich mit dem Markt.
3. `mrbeast_gaming` lief nach der Watchdog-Reparatur ungefragt wieder
   an (Profil stand auf aktiv=true). Entscheid offen.
