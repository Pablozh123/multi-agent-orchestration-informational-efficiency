# Recherche: Polymarket Earnings-Call-Mention-Märkte

Status: Recherche abgeschlossen, Umsetzungsentscheid offen
Erstellt: 22.07.2026
Anlass: Prüfung, ob die bestehende Mentions-Bot-Pipeline auf Earnings-Call-Märkte
übertragbar ist. Einstiegsfall: Tesla Q2 2026 (Event 701009).

## Methodik und Belegstufen

Zwei unabhängige Erhebungen:

- **Eigene Messung (EM):** direkte Abrufe der Polymarket-Gamma-API, der CLOB-Preis-
  historie und der Data-API-Trades am 22.07.2026, ca. 12:15–12:40 UTC. Endpunkte in
  §11 dokumentiert, reproduzierbar. Dies ist die belastbarste Quelle in diesem Dokument.
- **Web-Recherche (WR):** Deep-Research-Lauf mit 104 Agenten, adversarielle Prüfung
  jedes Claims (2 von 3 Gegenstimmen = verworfen). 25 Claims geprüft, 7 bestätigt,
  18 verworfen.

Jede Aussage unten ist markiert: **[EM]** eigene Messung, **[WR]** belegte Web-Recherche,
**[EINSCHÄTZUNG]** Interpretation, **[OFFEN]** nicht belegt.

Wichtig für die Thesis: §10 listet ausdrücklich, was *nicht* belegt ist. Nichts aus
diesem Dokument geht ungeprüft in den Text.

---

## 1. Zeitpunkt — mit Korrektur an der Recherche

**[WR]** Der Tesla-Q2-2026-Call findet am **22.07.2026, 16:30 CT / 17:30 ET** statt.
Primärbeleg: Tesla-Pressemitteilung vom 02.07.2026, zugleich SEC-8-K-Exhibit
(sec.gov, Archives/edgar/data/1318605). Vorlaufzeit der Ankündigung: 20 Tage.

**[EM] Korrektur:** Die Recherche rechnet 17:30 ET in **22:30 UTC** um. Das ist falsch —
im Juli gilt EDT (UTC−4), also **21:30 UTC**. Gegenprobe am GM-Call (21.07., 8:30 ET):
die gemessene Handelsaktivität setzt exakt um 12:30 UTC ein, was UTC−4 bestätigt. Der
Januar-Call (28.01., EST/UTC−5) lag dagegen tatsächlich bei 22:30 UTC — daher vermutlich
die Verwechslung.

Operativ relevant: Eine Armierung auf 22:30 UTC würde die erste Stunde des Calls verpassen.

## 2. Regelwerk — strukturell übertragbar

**[WR, 3-0 bestätigt]** Die Serie nutzt denselben *Event Mentions Contract*, den unsere
Zähl-Engine bereits umsetzt. Bestätigte Regeln:

- **Kein Sprecherfilter:** „resolve to Yes if the listed term is mentioned by **anyone**
  during this event." Alle 19 Tesla-Märkte tragen eine byte-identische Description.
  Q&A zählt ausdrücklich mit („If the event contains a Q&A, the Q&A will count").
  Analystenfragen zählen also. → Keine Sprecher-Verifikation nötig (anders als MrBeast).
- **Wortformen:** Plural, Possessiv und Compounds zählen; **alle anderen Formen zählen
  ausdrücklich nicht** („other forms will NOT count"). Ableitungen wie „tokenization"
  für „Token" zählen nicht — Compound vs. Ableitung muss sauber getrennt werden.
- **Resolutionsquelle:** „The resolution source will be audio of the event." Das
  Regelwerk-PDF präzisiert: „according to the audio **or video** of the first official
  release. Transcripts or any subsequent releases that differ from the initial release
  will not be considered." **Transkripte sind regeltechnisch ausgeschlossen.**
- **Nur live Gesendetes zählt:** „only remarks that are broadcast or streamed live will
  count"; Bildschirmtext nur, wenn vorgelesen. → **Pressemitteilung, Shareholder-Deck
  und 8-K lösen nichts aus.** Sie sind ein Prior für die Wahrscheinlichkeit, kein
  Auflösungspfad.
- **Cancellation-Backstop:** `-No Qualifying Event-` löst YES aus, wenn der Call bis
  23.07.2026 23:59 ET nicht gesendet wird.

**[WR] Zwei Fallen für eine Bot-Spezifikation:**

1. Das Regelwerk ist ein Template mit `{entity}`-Slot. Die Serie *„What will Elon Musk
   say during Tesla Q1 2025 earnings call?"* hat auf **Markt-Ebene sehr wohl einen
   Sprecherfilter**, während der Event-Text widersprüchlich „mentioned during this event"
   sagt. Markt-Ebene ist massgeblich. Eine hartcodierte Annahme „kein Sprecherfilter"
   ist ein Fehlerpfad — pro Event neu parsen.
2. **Boilerplate-Drift:** Die Mai-2026-Fassung enthält eine Klausel zu vorab
   aufgezeichneten Clips, die Nov-2025-Fassung nicht.

**[WR]** Resolver ist Polymarkets UMA-CTF-Adapter V4
(`0x65070BE91477460D8A7AeEb94ef92fe056C2f2A7`, Polygon), der das UMA-Optimistic-Oracle
abfragt. Die konkreten Dispute-Fristen wurden **nicht** belegt (§10).

## 3. Kernmessung: Wie schnell preist der Markt ein

Die Recherche liess diese Frage ausdrücklich offen („Für keinen einzigen Earnings-Call-
Mention-Markt liegt eine intra-Call-Preiszeitreihe vor"). **[EM]** schliesst sie.

### 3.1 Tesla Q4 2025 (Call 28.01.2026, 22:30 UTC) — Sekundenauflösung

Trades aus der Data-API, Markt „Refinery" (löste YES auf):

| Zeit (UTC) | Preis | Grösse | Wallet |
|---|---|---|---|
| 22:49:52 | 0.800 | 5.0 | Portly-Guilty |
| 22:49:56 | **0.973** | 102.8 | Threadbare-Signal |
| 22:49:58 | 0.980 | 20.4 | Darling-Baboon |
| 22:50:04 | 0.990 | 1.0 | Threadbare-Signal |
| 22:50:12 | 0.990 | 101.0 | Threadbare-Signal |

**Von 0.80 auf 0.973 in vier Sekunden.** Von der ersten Reaktion bis zur vollständigen
Auspreisung: ~20 Sekunden. Das handelbare Volumen unterhalb von 0.90 betrug **5 Shares**.

Markt „Tariff" (YES): 22:47:12 @0.950 → 22:48:02 @0.986 ×265. Gleiche Grössenordnung.

### 3.2 General Motors (Call 21.07.2026, 12:30 UTC) — frischeste Evidenz

Minuten-Preishistorie während des Calls:

| Markt | Ergebnis | Verlauf |
|---|---|---|
| Emission | YES | 0.445 → **0.995** in einer Minute (12:44) |
| Quarter 10+ | YES | 0.696 → **0.996** in einer Minute (12:43) |
| Car 10+ | NO | 0.045 vor dem Call → 0.026 (korrekt vorgepreist) |
| Income 10+ | NO | 0.045 → 0.019 |
| Horsepower | NO | 0.080 → 0.044 |

### 3.3 Wo das Volumen wirklich entsteht

**[EM]** Beim GM-Event fand das meiste YES-Volumen **Tage vor dem Call** statt
(14.–20.07. zu Preisen von 0.46–0.95). Während des Calls wurde fast ausschliesslich
bei 0.99+ gehandelt.

**[EINSCHÄTZUNG]** Das ist der eigentliche Strukturbefund: Der Markt ist ein
Vorpreisungs-Markt, kein Reaktionsmarkt. Bei GM lag `Car 10+` schon vor dem Call bei
0.045 und löste korrekt NO auf. Die Gegenseite ist gut informiert.

### 3.4 Konsequenz für unsere Parameter

**[EM]** Mit `ASK_OBERGRENZE` = 0.90 (aktuell: `EV_P_WIN` 0.93 − `EV_MIN_EDGE` 0.03)
hätten wir in **beiden** gemessenen Calls praktisch keinen Fill bekommen — unterhalb
von 0.90 lagen nur einzelne Shares.

## 4. Historie und Auflösungsverhalten

**[EM]** Tesla Q4 2025 (Event 181137, Call 28.01.2026): 16 gelistete Märkte, davon
14 aufgelöst — **9 YES, 5 NO** (NO: Loyalty, SpaceX, Gigafactory, Semi Truck, Lidar).
Zwei Märkte (Architecture, Units Deployed) wurden nie deployt (`closed=false`, Volumen 0).
Eventvolumen **43.467,43 USD**, grösster Einzelmarkt Cybertruck 12.918,42 USD.
Alle 14 tragen `umaResolutionStatuses = ["proposed"]` — kein Dispute erkennbar.

> **Hinweis zur Widerlegung in der Web-Recherche:** Die WR hat eine Behauptung mit
> denselben Zahlen (43.467 USD, Cybertruck 12.918 USD) mit 0-3 verworfen. Die
> Widerlegung ist ein **False Negative**: Der Slug
> `what-will-tesla-say-during-their-next-earnings-call` ist ein **Rolling Slug** und
> zeigt inzwischen auf das Juli-Event (5.828 USD). Die Verifizierer haben das aktuelle
> Event geprüft und die Januar-Zahlen folgerichtig nicht gefunden. Die eigene Messung
> ging über die **stabile Event-ID 181137** und ist massgeblich. Die ebenfalls
> verworfene Auflösungsquote „10 von 14 YES" war dagegen sachlich falsch — korrekt
> sind 9 von 14.
>
> **Lehre für die Thesis:** Earnings-Call-Events immer per Event-ID zitieren, nie per
> Slug. Jede Zitation braucht ein Abrufdatum.

**[EM]** GM Q2 2026 (Event 701017, Call 21.07.2026): 22 Märkte, **14 YES, 8 NO**,
Eventvolumen 20.330 USD.

**[WR, 3-0]** Nvidia (Call 20.05.2026): 10.651,02 USD Volumen über ~25 Märkte, Median
274 USD pro Einzelmarkt, Open Interest 4.276,89 USD. Volumenstärkster Einzelmarkt war
mit 1.569,59 USD der **Zählmarkt** „Token 20+ times".

**[WR, 3-0]** Die Marktklasse ist ein Template-Batch-Rollout: Tesla, GM und Verizon
wurden am 13.07.2026 innerhalb von rund sieben Minuten angelegt (Slug-Zeitstempel
…183304, …183530, …183952). Am 22.07.2026 gleichzeitig aktiv: Tesla, Dow, Intel,
Verizon, P&G. Die Klasse existiert mindestens seit Q2 2025.

## 5. Aktueller Tesla-Markt (Momentaufnahme)

**[EM]** Event 701009, Abruf 22.07.2026 ~12:15 UTC. 19 Märkte, Eventvolumen
5.827,72 USD, Gamma-Feld `liquidity` 14.021,45.

Strukturell neu gegenüber Januar: Das Juli-Event enthält **Zähl-Brackets**
(`Income 10+`, `Quarter 10+`, `Fiscal 10+`, `Car 10+`, `Growth 5+`) — im Januar-Event
gab es ausschliesslich Einzelwort-Märkte. Damit stehen 5 Zählmärkte gegen
13 Ein-Nennungs-Märkte plus den Cancellation-Backstop.

Preisbild zum Abrufzeitpunkt (YES): Software 0.978, Factory 0.964, Robot 0.963,
Optimus 0.960, Energy 0.960, America 0.950, China 0.930, Car 10+ 0.871, Solar 0.825,
Quarter 10+ 0.750, Subscription 0.685, Growth 5+ 0.680, Texas 0.585, SpaceX 0.395,
Cybertruck 0.330, Emission 0.125, Income 10+ 0.070, Fiscal 10+ 0.031,
No-Qualifying-Event 0.007.

> Die WR hat eine Behauptung verworfen, die diese Wörter bei 95–99,8¢ verortete. Die
> eigene Messung zeigt: die Richtung stimmte, die konkreten Zahlen waren zu hoch. Es
> gelten die oben gemessenen Werte.

## 6. Auffälligkeiten

**[EM] Konkurrenz ist nachweisbar und persistent.** Im Januar-Call sweept das Wallet
**„Threadbare-Signal"** auf „Refinery" in Clips: 102.8 @0.973 → 17.4 @0.98 → 1.0 @0.99
→ 101.0 @0.99, alles innerhalb von 16 Sekunden. Das ist exakt unser FAK-Sweep-Muster.

**„Darling-Baboon"** taucht in *beiden* Events auf (Tesla Januar „Refinery" 22:49:58,
GM Juli „Software" 12:33:51) — ein über Monate und Firmen hinweg aktiver Akteur.
**„Shady-Vitality"** erscheint 10× über die geprüften GM-Märkte.

**[EM] Ein ungeklärter Ausschlag:** „Refinery" fiel im Januar um 22:38 UTC um −0.395
(0.855 → 0.460), bevor es ab 22:49 endgültig stieg. Ursache nicht ermittelt — mögliche
Kandidaten: Fehl-Hörer, dünnes Buch, oder ein Verkäufer. Für die Thesis interessant als
Beispiel für Rauschen in dünnen Büchern, aber nicht aufgeklärt.

**[WR] Belegte Regel-Ambiguitäten:** (1) Der „Source Agency"-Abschnitt des Regelwerks
listet nur politische Nachrichtenquellen (Weisses Haus, Reuters, AP …) und keine
Unternehmens-IR-Quelle — für einen IR-Webcast passt die Liste nicht. (2) Der genannte
Event-vs-Markt-Widerspruch bei der Elon-Serie ist ein latenter Disputgrund.
(3) Boilerplate-Drift zwischen Quartalen.

**[OFFEN]** Dispute-Historie, Fehlauflösungen, Manipulationsvorwürfe und
Presseberichterstattung wurden **nicht** untersucht — das Suchbudget war erschöpft.
„Keine Streitfälle gefunden" wäre hier eine unzulässige Schlussfolgerung.

## 7. Publikationsweg — der offene Blocker

**[WR, niedrige Konfidenz]** `livestream.tesla.com` antwortete in der Recherche
durchgehend mit **HTTP 403** gegen Nicht-Browser-Clients, `ir.tesla.com` ebenfalls.
Eine öffentlich abgreifbare Direkt-Audio-URL nach Art eines RSS-Enclosures wurde
**nicht nachgewiesen**. Der Endpunkt ist zwar Wochen im Voraus bekannt und muss nicht
gesucht werden, ist aber gegen einfache HTTP-Clients unfreundlich.

**[OFFEN]** Die im Auftrag zentrale Frage — tatsächlicher Delay des Webcasts gegenüber
Realtime — ist **unbeantwortet**. Ohne diese Zahl lässt sich nicht sagen, ob überhaupt
ein Zeitfenster existiert.

**[OFFEN]** ToS-, Regulation-FD- und Urheberrechtsfragen zum automatisierten Abgreifen
eines IR-Webcasts wurden gar nicht adressiert. **Das ist vor jedem produktiven Einsatz
zu klären.**

## 8. Einschätzung: existiert ein Geschwindigkeits-Edge?

**[EINSCHÄTZUNG]** Nein — jedenfalls nicht der, auf dem die Podcast-Pipeline beruht.
Vier Gründe, jeder einzeln belegt:

1. **Kein Akquisitionsvorsprung.** Der Podcast-Edge beruht auf schnellerem Datei-Download
   nach dem RSS-Drop. Beim Earnings Call gibt es keine Datei; alle hören denselben
   Live-Stream simultan, und die Regel „only remarks broadcast or streamed live" schliesst
   einen Datei-Pfad aus. Übrig bleibt nur Transkriptions-zu-Order-Latenz.
2. **Das Fenster ist gemessen und es ist winzig.** Vier Sekunden von 0.80 auf 0.973,
   davon unter 0.90 exakt 5 Shares (§3.1).
3. **Die Konkurrenz ist schon da** und sweept nach demselben Muster (§6).
4. **Die Marktgrösse deckelt alles.** Median 274 USD Volumen pro Einzelmarkt (Nvidia,
   [WR]); das gesamte Tesla-Event 5.828 USD. Selbst ein perfekter Fill auf jedem Outcome
   bewegt sich im niedrigen dreistelligen Bereich **Bruttonotional** — der Edge davon
   ist ein Bruchteil.

**[EINSCHÄTZUNG] Der einzige verteidigungsfähige Rest-Edge liegt bei den Zähl-Brackets,
nicht bei den Einzelwort-Märkten.** Bei einem Ein-Nennungs-Markt kollabiert der Vorsprung
mit der ersten Nennung — ein Sekundenrennen. Bei `Quarter 10+` oder `Car 10+` ist die
handelsrelevante Grösse der *laufende Zählstand* über 45–70 Minuten. Ein deterministischer
Live-Zähler hält dort einen **Verarbeitungsvorsprung** statt eines Latenzvorsprungs.
Konsistent damit: Der volumenstärkste Einzelmarkt des Nvidia-Events war ein Zählmarkt.

Diese Hypothese ist **nicht belegt**. Der GM-Datenpunkt spricht eher dagegen: `Quarter 10+`
sprang in einer Minute von 0.696 auf 0.996 — die Gegenseite zählte offenbar mit.

## 9. Falls Umsetzung — der Weg

**[EINSCHÄTZUNG]** Der Grenzaufwand wäre gering: dieselbe Whisper-Chunk-Architektur,
dieselbe deterministische Zählung, kein Sprecher-Verifikations-Bedarf. Was fehlt, ist
ausschliesslich die **Audioquelle**. Konkret zu bauen wäre:

- Ein Stream-Watcher statt `rss_watch.py` (kein Drop-Ereignis, sondern ein zur bekannten
  Uhrzeit startender Stream) — Voraussetzung: §7 geklärt.
- Zähl-Brackets in der Decision-Schicht: `groupItemThreshold` steht im Gamma-Snapshot
  bereits zur Verfügung; die Engine zählt heute schon deterministisch.
- Pro-Event-Parsing der Markt-Description statt Profil-Konstanten (wegen der
  Sprecherfilter-Falle aus §2).

Der Armierungs-Pfad selbst bliebe der etablierte: Feature-Branch `feat/<profil>-armierung`
im Live-Klon ba-thesis, additiver `PROFILE`-Eintrag, Tests, PR, dann `watchdog.json` und
`starte_bots.ps1`.

**Für heute (Call 21:30 UTC) ist das nicht seriös machbar** — der Publikationsweg ist
ungeklärt, ToS ungeprüft, und der PR-Zyklus passt nicht in die verbleibende Zeit.

**[EINSCHÄTZUNG] Die stärkste Verwendung ist methodisch, nicht handelnd.** Der Fall
isoliert sauber, welcher Anteil des Podcast-Edges auf *Akquisitionslatenz* entfällt
(hier: null) und welcher auf *Verarbeitungslatenz* (hier: der Rest). Das ist ein
direktes Argument für die Effizienz-Aussage in Kapitel 4 — und es kostet kein Kapital.

**Ein billiger nächster Schritt ohne jede Handelsentscheidung:** Den heutigen Call
passiv mitschneiden und die CLOB-Preishistorie danach abrufen. Das erzeugt einen
dritten, selbst erhobenen Datenpunkt zur Reprice-Geschwindigkeit — und ist genau der
Nachweis, den die Recherche als offene Frage markiert hat.

## 10. Was ausdrücklich NICHT belegt ist

1. Der tatsächliche Webcast-Delay gegenüber Realtime. Ohne ihn ist die Kernfrage
   quantitativ unbeantwortbar.
2. Ob der Media-Endpunkt ohne Headless-Browser abgreifbar ist.
3. Konkrete UMA-Dispute-Fristen und der Zeitpunkt der Kapitalfreigabe.
4. Ein Präzedenzfall, in dem eine ausschliesslich in einer **Analystenfrage** gefallene
   Erwähnung YES auflöste. Regeltext deckt es ab — Regel und Auflösungspraxis sind
   zweierlei.
5. Dispute-Historie, Manipulationsvorwürfe, Presseberichterstattung (§6).
6. ToS- und Rechtslage (§7).
7. Eine lückenlose Tesla-Quartalshistorie. Belegt sind Q4 2025 und Q2 2026.

## 10a. Nachtrag 23.07.: Ergebnis des Tesla-Calls und zwei neue Befunde

**Auflösung Tesla Q2 2026 [EM, Abruf 23.07. 11:56 UTC]:** 13 YES, 6 NO
(Event 701009, Stand `closed=false` — Auflösung lief noch). Eventvolumen
stieg von 5.828 auf 11.946 USD.

**Der Reprice-Befund bestätigt sich zum dritten Mal.** Die Minutenbalken
legten zunächst Einbrüche nahe (`Software` auf 0.72), die Trade-Ebene
entlarvt sie als Staub: Der 0.500-Print bei `Software` waren **1,2 Shares**,
der 0.71-Print bei `Growth 5+` **5 Shares**. Die tatsächlichen Grössen
liefen bei 0.941 und dann 0.999 (293, 50, 750 Shares an ein Wallet).
Unterhalb von 0.90 war erneut nichts zu holen.

> Methodische Lehre: Minutenbalken in dünnen Büchern sind als Beleg
> untauglich. Jede Aussage über Fenster und Tiefe braucht die Trade-Ebene.

**Die China-Anomalie.** Um 21:54:48 UTC wurden in *derselben Sekunde*
~758 Shares zu 0.900–0.910 über zehn Gegenparteien weggeräumt. Sechs Minuten
später handelte `China` bei 0.480, aktuell 0.580. Ein Akteur hat mit
Überzeugung bei 0.90 gekauft und liegt hinten — selbst ein scheinbar
sicheres Wort ist bei einem Tesla-Call nicht sicher.

**Zugangsbeschränkung als struktureller Blocker (siehe Messprotokoll §8).**
Dow und Intel verlangen Registrierung mit personenbezogenen Daten für den
Webcast; Tesla war die Ausnahme. Das beantwortet die offene Frage 2 aus §10
teilweise — nicht mit einer Latenzzahl, sondern mit der Feststellung, dass
der Zugang bei den meisten Firmen gar nicht erst offensteht.

**Zeitangaben der Marktbeschreibung sind unzuverlässig.** Polymarket nennt
für den Dow-Call „9 AM ET", die Firma selbst 08:00 ET. Vor jeder Armierung
ist die Uhrzeit an der IR-Quelle zu prüfen.

## 11. Reproduktion

Alle EM-Abrufe am 22.07.2026, 12:15–12:40 UTC, mit Browser-User-Agent
(ohne UA liefert der CLOB HTTP 403):

```
Event nach Slug:   https://gamma-api.polymarket.com/events?slug=<slug>
Event nach ID:     https://gamma-api.polymarket.com/events/<event_id>
Preishistorie:     https://clob.polymarket.com/prices-history
                     ?market=<clobTokenId>&startTs=<unix>&endTs=<unix>&fidelity=1
Trades:            https://data-api.polymarket.com/trades
                     ?market=<conditionId>&limit=500&takerOnly=false
Suche:             https://gamma-api.polymarket.com/public-search
                     ?q=earnings%20call&limit_per_type=40&events_status=all
```

Verwendete Event-IDs: 701009 (Tesla Q2 2026), 181137 (Tesla Q4 2025),
701017 (GM Q2 2026).

Volltext des Regelwerk-PDFs aus dem Recherchelauf:
`.claude/projects/<session>/tool-results/rules.txt`.
Regelwerk-Original: `polymarket-upload.s3.us-east-2.amazonaws.com/market_products/Event+Mentions+Contract+DeFi.pdf`
