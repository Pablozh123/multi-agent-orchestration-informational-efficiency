# Thesis-Erkenntnisse Live-Mentions-Strecke (Stand 29.07.2026)

Rohmaterial fuer die BA (Fazit/Diskussion), gesammelt aus den
Live-Laeufen 24.-29.07. (AXP, PayPal, Boeing, Graham, P&G) und den
Podcast-Laeufen davor. Jede These mit Beleg-Verweis. Quellen: die
Runbooks (`*_ARMIERUNG.md`), `UEBERGABE_2026-07-28_LIVE_MENTIONS.md`
(§4-Nachtraege = Kalibriertabellen), Event-Logs je `data/live/`-Ordner.

## A. Markteffizienz und die Grenzen des Latenz-Edges

1. **Das Latenz-Rennen auf Einzelwoerter ist strukturell verloren.**
   Der Markt preist ein live gehoertes Wort in 1-4 s ein (Michigan-
   Reprice-Messung; Graham bestaetigt). Latenzkette gemessen:
   schnellste Teilnehmer 1-4 s, Mensch am Low-Latency-Stream ~5-8 s,
   Bot 15-25 s (Chunk-Fuellzeit dominiert). Graham-Detail: Unser
   ffplay-Audio lag ~20 s VOR dem YouTube-Player-Ton — und die
   gefallenen Woerter waren trotzdem ~20 s vor uns ausverkauft.

2. **Antizipation frisst den Sicherheits-Edge.** Menschen kaufen,
   sobald das THEMA auf ein Listenwort zulaeuft (Tough Cookie/Supreme
   Court beim Graham-Tribute ~20 s vor dem Wort; Boeing-Guidance:
   485 Shares exakt beim Outlook-Thema). Wer auf die echte Nennung
   wartet (= quasi risikofreier Profit), bekommt nur noch Restpreise
   0.94-0.999. Antizipierer irren aber auch: Agentic-NO-Kauf 13:23
   (-10 USD), Fiscal-10+-NO gegen Endstand 23 (-10 USD).

3. **Der reale Bot-Edge sind Zweifel-Fenster, nie Erst-Erkennung.**
   Alle 4 Bot-Fills (AXP Luxury/Fraud +60.06, PayPal Users +9) kamen
   aus Zweifel-/Ruecksetzer-Situationen mit verifiziertem Wissen
   gegen einen unsicheren Markt. Verify-Praezision ueber alle
   Laeufe: 100% (0 Fehltrigger bei 27+ Trigger-Verifikationen
   Graham+P&G).

4. **Zaehl-Brackets: Verarbeitungs- statt Latenzvorsprung — aber das
   Fenster ist schmaler als gedacht.** P&G (8 Brackets, 4 ueber
   Schwelle) als vierter Beleg: SICHERE Brackets sind vorgepreist
   (Quarter-Entscheid bei ask 0.996), ZWEIFELHAFTE erreichten die
   Schwelle nie (Customer 2/5, Income 1/10). Der Edge braucht ein
   vom Markt UNTERSCHAETZTES Bracket; an vier Messtagen existierte
   keins. Das Mitzaehlen bleibt trotzdem der einzige Kanal, in dem
   der Bot dem Saal strukturell voraus ist.

5. **Liquiditaets-Paradox.** Wo wenige handeln, ist der Edge leicht,
   aber nicht skalierbar (All-In-Podcasts: dominante Treffer, kaum
   Volumen); wo Volumen ist (Trump-Events), sind die Gegenspieler
   schnell/antizipativ. Dazu Slippage dünner Buecher: Die ersten
   100 USD @0.50, die naechsten erst @0.95 — jeder zusaetzliche
   Dollar Einsatz verschlechtert das Chancen-Risiko-Verhaeltnis
   (durchschnittlicher Fill-Preis steigt mit der Groesse). FAK-Sweeps
   mit Preisdeckel begrenzen genau das.

6. **Podcast-Drops (Urspruungsidee) leiden am MM-Rueckzug:** Beim
   Drop ziehen Market Maker die Quotes (JRE-Leerlaeufe) — der
   Informationsvorsprung existiert, aber das Buch ist im
   entscheidenden Moment unhandelbar.

## B. Resolution-Schicht (UMA) als eigene Risikoklasse

7. **Mechanik:** Beliebiger Proposer + 750-USDC-Bond + ~5 USD Reward
   → 2-h-Challenge-Fenster → ohne Dispute FINAL; Dispute → 48-h-
   DVM-Token-Abstimmung, Verlierer-Bond halbiert. Prominente
   Praezedenzfaelle zeigen: selbst disputierte falsche Ergebnisse
   koennen final werden (Token-Abstimmung irrt oder wird dominiert).

8. **Anreiz-Luecke bei kleinen Maerkten:** Dispute-Risiko (750) >>
   typische Positionsgroesse (10-100) → bei ambigen Faellen fechtet
   niemand Rationales an; der ERSTE Proposer definiert de facto die
   Wahrheit. Proposing ist ein automatisiertes Yield-Geschaeft
   weniger pseudonymer Akteure (Bots auf Transkript-Quellen mit
   ASR-Fehlerprofil). Empirisch 29.07.: eindeutige P&G-Faelle wurden
   sofort proposed, die vier Zweifelsfaelle zuletzt —
   **Proposer-Reihenfolge als Ambiguitaets-Signal.**

9. **Kalibrier-Datensatz (84 finale Maerkte, 28.-29.07.):** PayPal
   19/19, Boeing 20/20, Graham 23/23, P&G 22/22 — Vollpass-Prognose
   vs. UMA-Endergebnis in 82/84 deckungsgleich. Die Resolver
   bestanden am 29.07. drei Ambiguitaetstests streng nach Audio
   (Valuation/World Cup/Trump NO trotz 0.45-0.50-Maerkten). Beide
   Diskrepanzen (Guidance, Customer 5+) liegen in der
   Verwechslungsklasse und sind je einmal eher pro Resolver
   (Customer) und unentscheidbar (Guidance) — kein belegter
   Willkuerakt. Das Resolution-Risiko ist damit kleiner als nach
   dem Guidance-Schreck befuerchtet; das dominante Restrisiko ist
   die eigene ASR (These 10).

## C. Grenzen ASR-basierter Beweise (Kernbefund fuer die NO-Seite)

10. **Die Verschreibungs-/Nachbarform-Klasse:** agentic commerce →
    "agent e-commerce" (phonetisch identisch), guidance → "guide(s)
    that" (Zwei-Pass-konsistent — UNENTSCHEIDBAR ob ASR- oder
    Resolver-Seite), valuation → "value creation" (Band 1546s,
    on-chain-dokumentierter Kauf 5 s spaeter), customer →
    "consumer" (P&G: Resolver YES bei 5+, unsere Zaehlung 2 gegen
    34x consumer — Whispers Sprachmodell-Prior NORMALISIERT seltene
    Woerter auf kontexttypische; diesmal lag wahrscheinlich UNSERE
    Seite falsch). Dazu die Blockgrenzen-Falle: 30-s-Raster verlor
    "agentic commerce" exakt am Schnitt (Whisper verwirft
    angeschnittene Segmente). Wichtig: small und large-v3 sind
    DIESELBE Modellfamilie — ihre Fehler korrelieren, zwei
    Whisper-Paesse sind kein unabhaengiger Konsens.

11. **YES/NO-Asymmetrie:** YES braucht EIN sicheres Hoeren; NO
    braucht lueckenlose Abdeckung (Stall-frei!) + fehlerfreie
    Transkription ueber die GESAMTE Laufzeit + Resolver-Kongruenz.
    NO ist strukturell die teurere Behauptung. Konsequenz
    (Late-NO-Pflichtfilter): durchgehender Pass statt Raster,
    phonetischer Nachbarschafts-Check (guide/value/Neologismen →
    gesperrt), Zwei-METHODEN-Konsens (zwei Laeufe desselben Modells
    zaehlen nicht), Preisdeckel 0.60-0.70 als Resolution-Risiko-
    Puffer.

12. **Der kollektive Verhoerer ist ein Markt-Phaenomen, kein
    Einzelfehler:** Valuation sprang 0.16→0.50, weil viele
    dasselbe "value creation" hoerten; World Cup (0.45) und Trump
    (0.47) zweifelten sogar OHNE Audio-Anker. Maerkte bepreisen
    hier ehrlich ihre eigene Wahrnehmungsunsicherheit — und der
    lueckenlose Vollpass ist genau dann der Informationsvorsprung.

## D. Systemlehren (Betrieb)

13. **Infrastruktur-Fragilitaet ist der dominante Verlustkanal, nicht
    Latenz:** Michigan 65 min blind (2 Stalls), Graham 54 s Stall =
    alle 3 Misses des Laufs (Trump sagte 3 Listenwoerter in genau
    dieser Minute), Task-Datums-Falle (/ST ohne /SD → Task haette
    nie gefeuert), Fenster-X-Abbruch ohne Endcheck. Robustheit
    (Stall-Detektor 12-s-Reconnect, /SD-Regel, bot_stop-Disziplin)
    schlaegt jede Latenz-Optimierung.

14. **Sprecherbindung liefert messbare Praezision:** Graham-Forever
    stand 2 im Gesamtzaehler (Fremdredner), resolvete NO — ECAPA
    verhinderte einen ~75-USD-Fehlkauf. Referenz MUSS aus der
    Event-Uebertragungskette stammen (Studio-Referenz auf PA-Audio:
    max 0.396 = alle echten Treffer verworfen).

15. **Hybrid Mensch+Maschine ist komplementaer, nicht redundant:**
    Der Mensch ist Stall-Redundanz und darf mit Ohr-Bestaetigung
    ueber den blinden Modell-Deckel gehen (Graham-Blindfenster:
    manuell Supreme Court @0.944 + Tough Cookie @0.99, beide YES,
    +6.90 — erster belegter Mensch-schlaegt-Maschine-Fall). Die
    Maschine haelt Brackets, Verify-Disziplin und zaehlt, was kein
    Mensch ueber 60+ Minuten haelt. Der Mensch verliert dafuer bei
    Bauch-NOs (Agentic -10, Fiscal -10) — Ohr-Bestaetigung wirkt
    nur fuer ANWESENHEIT, nie fuer Abwesenheit.

16. **Venue-Vergleich (Kalshi-Analyse 29.07., eigene Doku):** gleiche
    Calls, tiefere Buecher, 1-Cent-Ticks — aber Resolution primaer
    per Video/Audio (ASR-Beweise dort noch schwaecher), keine
    Zaehlschwellen, Gebuehrenmaximum genau im Zweifel-Fenster
    (P≈0.5). Der deutsche Zugang ist offen (Member Agreement).
