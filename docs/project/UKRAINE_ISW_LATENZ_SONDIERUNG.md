# Ukraine-Karten-Märkte: Latenz-Sondierung ISW → Polymarket

Stand 23.07.2026. Erhoben in der wt-ukraine-Session per read-only Abfragen
gegen die öffentlichen Endpunkte von Polymarket (Gamma, CLOB, Data-API) und
den ArcGIS-FeatureServer des ISW. Kein Order-Pfad, kein Handel.

Ergänzt den Startpunkt-Abschnitt in `SESSIONS_UEBERSICHT.md`. Dort ging es um
den Markt „Donetsk Oblast komplett" (Event 139550) mit einem unscharfen
Neun-Städte-Kriterium. Diese Sondierung betrifft eine **andere, deutlich
besser handhabbare Marktfamilie**: die Einzelsiedlungs-Märkte im Tag
`ukraine-map`.

## 1. Warum die Einzelsiedlungs-Märkte der bessere Angriffspunkt sind

Der Auflösungstext (wörtlich aus der Gamma-API, Markt
`will-russia-enter-krasnoiarske-by-july-31`) nennt drei Dinge, die der
Donetsk-Oblast-Markt nicht hat:

1. **Eine exakte Koordinate.** „Krasnoiarske, Donetsk Oblast, (48.419117° N,
   37.125165° E)". Kein Namensabgleich nötig.
2. **Eine abgeschlossene Layer-Liste.** Qualifizierend ist *jede*
   zusammenhängende Schattierung aus „Assessed Russian Infiltration Areas in
   Ukraine", „Assessed Russian Control", „Assessed Russian Advance In
   Ukraine" oder „Assessed Russian Gains in the Past 24 Hours".
3. **Ein Flächenkriterium statt eines Vollständigkeitskriteriums.** „*any
   part* of the specified territory" — nicht „neun Munizipalitäten
   gleichzeitig".

Damit ist die Auflösungsfrage ein Polygon-Schnitt-Test: Schneidet die
Siedlungsfläche eines der vier Layer? Das ist deterministisch berechenbar und
passt in den deterministischen Kern.

Unverändert bestehen bleibt die **Persistenzklausel**: die Schattierung muss
„through the next full ISW daily update cycle" Bestand haben. Ein Treffer zum
Zeitpunkt T ist also noch keine Auflösung.

**Universum:** 52 offene Märkte tragen eine maschinell extrahierbare
Koordinate im Beschreibungstext (Regex `\(([0-9.]+)[^0-9]*N[^0-9]*([0-9.]+)[^0-9]*E\)`).

## 2. Der Fall Krasnoiarske, gemessen

Marktbewegung und Quellenänderung liegen beide als harte Zeitstempel vor.

| Zeit (UTC) | Ereignis | Beleg |
| --- | --- | --- |
| 22.07. 19:36:58 | letzter Trade vor dem Ereignis (NO @ 0.959) | Data-API `/trades` |
| 22.07. **20:39:00.759** | ISW legt Infiltrations-Polygon OID 2104 an (43.4 km², deckt Krasnoyarske), Editor `smcree_understandingwar` | FeatureServer `CreationDate` |
| — | *18 min 43 s ohne einen einzigen Trade* | Data-API `/trades` |
| 22.07. **20:57:43** | ein Block, 5 Fills, 4'408 USD, YES 0.046 → 0.93 | Data-API `/trades` |
| 22.07. 21:02:53 | ISW überarbeitet dasselbe Polygon | FeatureServer `EditDate` |
| 22.07. 22:44 / 22:57 | Layer-`lastEditDate` Infiltration / Advance | Layer-Metadaten |

**Gemessener Vorlauf der Quelle vor dem Markt: 18 Minuten 43 Sekunden.**

Drei Schwestermärkte sprangen praktisch gleichzeitig (`july-31` 20:58:06,
`september-30` 20:58:05, `december-31` 20:59:06) — zwischen den Laufzeiten
gibt es also keinen ausnutzbaren Versatz.

Der billigste YES-Fill im Sweep lag bei **0.395**. Unterhalb davon war das Buch
dünn; der Sweeper zahlte im Mittel rund 0.66.

### Zwei Fallstricke, die diese Messung fast verdorben hätten

**Layer-Zeitstempel ≠ Feature-Zeitstempel.** Die `editingInfo.lastEditDate`
des Infiltrations-Layers stand auf 22:44 — zwei Stunden *nach* der
Marktbewegung. Wer nur die Layer-Metadaten als Ereigniszeit nimmt, misst den
Vorlauf mit falschem Vorzeichen und schliesst, ISW sei zu langsam. Erst der
Feature-`CreationDate` (20:39) zeigt das Gegenteil. Layer-Metadaten taugen als
Auslöser, nicht als Zeitstempel.

**Namensschreibweise.** Der Markt schreibt „Krasnoiarske", der ISW-Layer
`Ukrainian_Settlements_Updated_view` führt „Krasnoyarske" (Красноярське,
Hromada Dobropilska, Rajon Pokrovskyi). Eine Suche nach `LIKE '%rasnoiarske%'`
liefert landesweit **null** Treffer. Es darf ausschliesslich über die
Koordinate zugeordnet werden.

## 3. Was der Markt bereits einpreist

Ein Abgleich aller 52 offenen Märkte gegen den aktuellen ISW-Stand
(Skript: Flächenschnitt Siedlung × vier qualifizierende Layer) ergibt:

**Keine stehende Divergenz.** Jeder russische „enter"-Markt, dessen Siedlung
heute von einem qualifizierenden Layer gedeckt ist, steht bereits bei
0.91 bis 0.998. Der Markt ist gegenüber dem *aktuellen* ISW-Stand effizient.

Die Kante liegt damit ausschliesslich im Moment der Änderung, nicht in einer
dauerhaften Fehlbewertung.

> Methodenwarnung aus dem eigenen Lauf: Ein erster Filter meldete sechs
> „Chancen". Alle sechs waren `will-ukraine-re-enter-…`-Märkte, bei denen
> russische Schattierung das *Gegen*signal ist — der Filter `"enter" in slug`
> fängt „re-enter" mit. Die Marktpolarität muss explizit geparst werden.

## 4. Warum der historische Backtest nicht trägt

Naheliegend wäre, für alle vergangenen Repricings den Vorlauf rückwirkend zu
messen. Das geht **nicht**, und zwar aus einem harten Grund:

Am 21.07. wurden im Infiltrations-Layer **115 Features innerhalb von 48
Minuten neu angelegt** (19:42–20:30). ISW löscht und zeichnet periodisch neu.
Der `CreationDate` eines heute vorhandenen Polygons sagt daher nichts darüber
aus, wann die betreffende Fläche *zuerst* schattiert wurde.

Ein Backtest über die aktuelle Momentaufnahme produziert entsprechend Unsinn:
für Vasylivka und Novyi Donbas ergab er „Vorlauf" von −24'827 bzw. −30'218
Minuten, weil das heutige Polygon lange nach der damaligen Marktbewegung
entstand. Zusätzlich vermischt ein naiver Lauf die „enter"-Märkte mit den
„capture all of"-Märkten, die ein anderes Kriterium haben.

**Belastbar ist ausschliesslich Vorwärtsmessung.** Es gibt genau eine saubere
Beobachtung (Krasnoiarske, drei korrelierte Märkte, N=1 Ereignis).

## 5. Zwei klar getrennte Kanten

**(A) Schneller als der Markt am ISW-Update — deterministisch.**
Die Auflösungsquelle *ist* die ISW-Karte. Wer den FeatureServer schneller
liest als der Markt, braucht keine Prognose, sondern nur einen Geometrietest.
Gemessenes Fenster: 18.7 Minuten. Das ist die Kante, die zum
deterministischen Kern passt.

**(B) Schneller als ISW — spekulativ, und lizenzrechtlich versperrt.**
DeepState und Telegram-Kanäle laufen der ISW-Karte typischerweise voraus, aber
eine Wette darauf ist eine Prognose über künftiges ISW-Verhalten, keine
Ableitung aus der Auflösungsregel. Regelseitig ist DeepStateMap ausdrücklich
**nur Ausfall-Fallback** („If the ISW map is rendered unavailable…"), also
niemals selbst auflösungswirksam.

Dazu kommt ein harter rechtlicher Blocker: Die **DeepStateMap-API ist für
gewinnorientierte Nutzung genehmigungspflichtig**. Die englische Fassung
erlaubt sie kostenlos nur für Volunteer-/Wohltätigkeitsarbeit und
Verteidigungszwecke; die ukrainische Originalfassung ist strenger und nennt
ausdrücklich „Фізичні та юридичні особи" — also auch **Privatpersonen** mit
Gewinnerzielungsabsicht. Rechteinhaber ist DEEPSTATEUATECH LLC, Anfragen über
`https://api.deepstatemap.live/request`. Proxying und Weitergabe an Dritte
sind untersagt.

Technisch: `/api/history` verlangt Authentifizierung (**HTTP 401**, selbst
geprüft); `/api/history/last` ist offen, liefert GeoJSON mit 523 Features und
unterstützt ETag/`If-None-Match` → 304. Cloudflare setzt `max-age=300`, die
effektive Auflösung liegt also bei ~5 Minuten. Das Feld `datetime` ist **kein**
ISO-8601 („22.07 o 13:07", ohne Jahr und Zeitzone) — als Change-Detector taugt
nur `id` (Unix-Zeitstempel) oder der ETag.

Das GitHub-Archiv `cyterat/deepstate-map-data` ist **kein** Frühwarnkanal: ein
Snapshot pro Kalendertag, cron 03:00 UTC, faktischer Push ~05:50 UTC,
Worst-Case-Staleness ~27 h. Als historisches Backtest-Korpus brauchbar.

Empfehlung: (A) bauen und messen. (B) nicht handeln — und ohne Genehmigung
nicht einmal pollen.

## 6. Poll-Architektur

Gemessene Kosten der Endpunkte:

| Abruf | Latenz | Nutzlast |
| --- | --- | --- |
| Layer-Metadaten `?f=json` (`lastEditDate`) | **104 ms** | 10.8 KB |
| `outStatistics` MAX(CreationDate) | 659 ms | 0.5 KB |
| alle Geometrien eines Layers | 1'494 ms | 965 KB |

15 Polls in Folge: 15/15 erfolgreich, Median 543 ms, kein Rate-Limit
beobachtet.

**Dreistufig:**

1. **Stolperdraht**, alle 20 s je Layer: Layer-Metadaten holen,
   `editingInfo.lastEditDate` mit dem letzten Stand vergleichen. Vier Layer
   × 3 Polls/min ≈ 17'000 Abrufe/Tag, rund 190 MB/Tag. Erkennt auch
   Löschungen und Änderungen, nicht nur Neuanlagen.
2. **Delta**, nur bei Änderung: Für Infiltration/Advance/Control gezielt
   `EditDate > letzter_stand` abfragen. Für Gains24h gibt es **keine
   Edit-Felder** (`editFieldsInfo: null`) — dort muss die Geometrie vollständig
   geholt und lokal gegen den Cache gediffed werden.
3. **Geometrietest**, lokal: geänderte Polygone gegen die 52 gecachten
   Siedlungsflächen schneiden (shapely, kein weiterer Netzabruf).

Erwartete Erkennungslatenz nach dem ISW-Insert: Poll-Intervall/2 plus
Abrufzeit plus Geometrie (gemessen 2.3 s je Volldurchlauf, siehe Abschnitt
10). Bei 20-Sekunden-Takt liegt sie deutlich unter einer Minute. Gegen 18.7
Minuten Marktträgheit ist das reichlich Reserve; ein 60-Sekunden-Takt
genügte ebenfalls.

Nicht vergessen: der FeatureServer drosselt unter Dauerlast (HTTP 429 im
error-Objekt einer 200-Antwort). Backoff ist Pflicht, nicht Kür.

**Zeitfenster.** Beobachtete Einzel-Edits am 22.07.: 15:20, 18:47, 19:48,
20:14, 20:39 UTC; Bulk-Rebuild am 21.07. 19:42–20:30 UTC; Control-Layer
21.07. 22:16 UTC. Der Schwerpunkt liegt zwischen 14:00 und 23:00 UTC
(US-Ostküsten-Arbeitstag). Ausserhalb genügt ein 120-Sekunden-Takt.

## 7. Signal-Logik und Schutz vor Falsch-Positiven

```
je geändertem Polygon P:
    für jede Siedlung S der Watchlist:
        wenn P ∩ S ≠ ∅ und S war zuvor nicht gedeckt:
            → Kandidat
```

Fünf Filter, jeder aus einem beobachteten Fehlermodus oder Präzedenzfall:

1. **Rebuild-Bremse.** Werden mehr als 10 Features eines Layers innerhalb von
   5 Minuten neu angelegt, ist das ein Bulk-Rebuild (Muster vom 21.07.: 115
   Features in 48 min). Dann neu grundieren statt signalisieren — sonst feuert
   der Bot auf einmal für Dutzende Siedlungen.
2. **Polarität.** `will-russia-enter-*` und `will-ukraine-re-enter-*` haben
   entgegengesetzte Logik. Aus dem Slug parsen, nicht aus dem Wortstamm.
3. **Kriteriumstyp.** `enter` (Flächenschnitt genügt) von `capture all of`
   (Vollüberdeckung nötig) trennen. Für „capture all of" ist der Test
   `S \ P = ∅`, nicht `P ∩ S ≠ ∅`.
4. **Persistenz.** Ein Treffer ist erst mit dem nächsten vollen ISW-Zyklus
   auflösungswirksam. Der Bot protokolliert zwei Zustände: `geschattet_seit`
   und `persistenz_bestätigt`. Der aktuelle Krasnoiarske-Preis von 0.91
   statt 0.99 ist genau der Preis dieser offenen Persistenzfrage. Der
   Myrnohrad-Fall (Abschnitt 8) zeigt, wogegen diese Stufe schützt: eine
   Karteneditierung, die am Folgetag wieder verschwindet.

5. **Clarification-Wächter.** Publiziert Polymarket eine „Clarification",
   wird das Orderbuch geleert und alle Resting Orders storniert. Der Bot
   muss den Marktzustand danach neu lesen statt anzunehmen, seine Order
   liege noch.

## 8. Regelmechanik und Präzedenzfälle (Recherche)

Ergänzend zu den eigenen Messungen, aus einer Mehrquellen-Recherche mit
adversarialer Verifikation (107 Agenten, 25 Quellen, 122 Rohbehauptungen, 14
bestätigt, 11 verworfen).

**Der Infiltrations-Layer ist strukturell der früheste.** ISW definiert
Infiltrationsgebiete methodisch als Flächen mit „begrenzter Präsenz, aber ohne
Kontrolle" — die **niedrigste Beweisschwelle** der vier Layer. Das erklärt die
eigene Messung: der Auslöser war der Infiltrations-Layer, der Control-Layer
hinkte über einen Tag hinterher.

**Absorbierender Zustand.** Der Regeltext des Zielmarkts enthält wörtlich:
„Once a qualifying condition is met, any subsequent loss of control will not be
considered towards the resolution of this market." Nach bestätigter
Qualifikation hat NO keinen Erholungspfad mehr. Das erklärt die Asymmetrie des
Preisverlaufs — 0.96 → 0.09 ohne Rückkehr.

**Myrnohrad, 15./16.11.2025 — der Präzedenzfall, der die Persistenzklausel
erzeugt hat.** Eine *unautorisierte Editierung* der ISW-Karte zeigte kurz vor
Auflösung russische Kontrolle über eine Kreuzung. Polymarket zahlte einen
Markt über rund 1.3 Mio. USD aus; die Editierung verschwand am Folgetag. Der
damalige Regeltext kannte die Persistenzanforderung noch nicht — sie taucht
erst ab der Deadline 31.12.2025 auf.

Drei Konsequenzen, die direkt in die Bot-Auslegung gehören:

1. Die Angriffsfläche liegt **bei der Datenquelle selbst**. Ein Bot, der auf
   die erste Schattierung feuert, ist gegen eine manipulierte oder
   fehlerhafte Karteneditierung genauso blind wie ein Mensch. Die
   Persistenzstufe ist der einzige Schutz — und genau deshalb existiert sie.
2. Die operative Durchsetzung über UMA ist mindestens einmal an der Realität
   gescheitert. Regeltext und tatsächliche Auflösung können auseinanderlaufen.
3. Für die Thesis ist der Fall ein dokumentiertes Beispiel dafür, dass
   Auflösungsquellen selbst zum Angriffsziel werden, sobald genug Geld an
   ihnen hängt.

**UMA-Auflösungspfad.** Proposal mit 750 pUSD Bond, 2 h Challenge-Fenster,
bei Streit 24–48 h Debatte plus ~48 h DVM-Vote. Adapter `UmaCtfAdapter v3.0`
(`0x157Ce2d672854c848c9b79C49a8Cc6cc89176a49`). Polymarkets allgemeine
Dokumentation enthält **keine** generische Quellenhierarchie — bindend ist
ausschliesslich der marktspezifische Regeltext.

**Operative Nebenwirkung mit Bot-Relevanz:** Wird eine „Clarification"
publiziert, **leert Polymarket das Orderbuch und storniert alle Resting
Orders**. Ein Bot, der mit liegenden Limit-Orders arbeitet, muss diesen Fall
behandeln, sonst hält er stillschweigend keine Position mehr.

**Was die Recherche nicht leisten konnte:** Die Zeitachse des
Krasnoiarske-Falls war aus offenen Quellen *nicht* rekonstruierbar — kein
einziger Zeitstempel-Claim überlebte die Verifikation. Ihre beiden wichtigsten
offenen Fragen („welcher Layer wechselt zuerst?", „wie gross ist die Latenz
ISW → Preis?") sind genau die, die in Abschnitt 2 dieses Dokuments durch
direkte Messung beantwortet werden. Zur Quellenlandschaft ausserhalb von
DeepState (ISW-Publikationszeit, russisches Verteidigungsministerium,
Rybar/WarGonzo/Dva Majora, LiveUAMap, Suriyakmaps, GeoConfirmed) überlebte
**kein** Claim — dieser Block bleibt offen.

## 9. Offene Punkte

- **Lizenz und Nutzungsbedingungen** der ISW-/AEI-Kartendaten und der
  ArcGIS-Endpunkte für automatisierte Weiterverwendung: weiterhin ungeklärt
  (die Recherche hat sie nicht auflösen können). Für DeepState ist die Lage
  dagegen geklärt und negativ — siehe Abschnitt 5. Gleiche offene Frage wie
  bei den IR-Webcasts.
- **Quellenlandschaft ausserhalb von DeepState** (ISW-Publikationszeit, RSS,
  russisches Verteidigungsministerium, Rybar/WarGonzo/Dva Majora,
  Generalstab, LiveUAMap, Suriyakmaps, Andrew Perpetua, Militaryland,
  GeoConfirmed): unbeantwortet. Für Kante (A) nicht nötig.
- **Handelbare Grösse.** Ask-Tiefe unter 0.30 in vergleichbaren billigen
  „enter"-Märkten: 27 bis 2'107 USD, Median einige hundert USD. Das ist eine
  Kleinbetrags-Kante, keine skalierbare Strategie.
- **N=1.** Ein sauber gemessenes Ereignis. Vor jeder Handelsaussage muss der
  Rekorder laufen und eine Verteilung liefern.
- **Wer war der Sweeper?** Ob am 22.07. um 20:57:43 ein Mensch oder ein Bot
  handelte, ist aus den Daten nicht zu sehen. 18.7 Minuten sprechen eher für
  manuelle Beobachtung als für Automatisierung — aber das ist eine Vermutung.

## 10. Gebauter Rekorder (23.07.)

`operations/pipeline/isw_karten_watch.py` — Zugriff und Geometrie.
`operations/pipeline/isw_rekorder.py` — Orchestrierung und Protokoll.
Trennung analog zu `x_watch.py` / `elon_bot.py`. Read-only, kein Order-Pfad.

Der Geometrietest ist ohne `shapely` implementiert (Ray-Casting plus
Kantenschnitt, Boxen-Vorfilter): keine neue Abhängigkeit, und der
deterministische Kern ist damit vollständig testabgedeckt.

Aufruf:

```
python -m operations.pipeline.isw_rekorder --einmal
python -m operations.pipeline.isw_rekorder --takt-s 20
```

Stand des ersten Laufs: 52 Märkte mit Siedlungsfläche aufgelöst, davon **26
auswertbar** (russische Polarität und Berührungskriterium). Die übrigen 26
sind `re-enter`- oder `capture all of`-Märkte und werden protokolliert, aber
nicht als Signal gewertet.

**Zwei Fehler, die erst der Probelauf gegen die echten Endpunkte zeigte:**

1. *Gains24h antwortete mit HTTP 400.* Der View führt `FID` statt
   `OBJECTID`; eine feste Feldannahme quittiert ArcGIS mit 400. Das ID-Feld
   gehört pro Layer konfiguriert.
2. *Die Rebuild-Bremse hätte das Instrument still ausgeschaltet.* Sie prüfte
   die Zeitstempel **aller** Features statt nur der seit dem letzten Stand
   hinzugekommenen. Da die Layer-Historie durch die periodischen ISW-Rebuilds
   immer geclustert ist, hätte die Bremse bei jedem Poll gegriffen und der
   Rekorder nie ein Signal geliefert — ohne Fehlermeldung. Behoben über
   `neue_zeitstempel(...)`, mit Regressionstest in beiden Richtungen
   (gefiltert bremst nicht, ungefiltert bremst).

Beide Fälle sind der Grund, warum der Rekorder vor dem Handel läuft: Der
zweite wäre im Live-Betrieb als „es passiert eben nichts" durchgegangen.

**Zwei weitere Fehler zeigte erst der Dauerlauf:**

3. *Der Geometrietest war unbrauchbar langsam.* Das grösste Kontroll-Polygon
   trägt **51'901 Stützpunkte in einem einzigen Ring**. Der naive Test — alle
   Ecken beider Polygone gegeneinander plus alle Kantenpaare — kostete dafür
   gemessene **5.6 s je Siedlung**, hochgerechnet **48 Minuten je
   Durchlauf**. Der Rekorder blieb im ersten Durchlauf hängen und schrieb nie
   eine Zustandsdatei. Die in Abschnitt 6 genannte Erkennungslatenz von
   10–16 s galt für diese Fassung schlicht nicht.

   Behoben durch einen Kantenfilter: Nur die Kanten des grossen Polygons, die
   in die Bounding-Box der Siedlung hineinreichen, werden geprüft; fehlt jede
   Randberührung, entscheidet je ein einziger Punkttest über Enthaltung oder
   Disjunktheit. Ergebnis unverändert (21/16/4 Treffer), Kosten:

   | | vorher | nachher |
   | --- | --- | --- |
   | ein Schnitt gegen das grösste Kontroll-Polygon | 5'559 ms | **19.6 ms** |
   | Geometrie je Volldurchlauf (4 Layer × 52 Siedlungen) | ~2'891 s | **2.3 s** |

4. *Der FeatureServer drosselt.* Unter Dauerlast antwortet ArcGIS mit
   `HTTP 429 "Unable to perform query. Too many requests."` — und zwar im
   `error`-Objekt einer **HTTP-200-Antwort**, nicht als HTTP-Status. Der
   frühere Befund „15 Polls in Folge ohne Rate-Limit" war zu optimistisch
   verallgemeinert. Behoben durch exponentiellen Backoff (429/5xx, vier
   Versuche ab 5 s) und eine Pause von 0.3 s zwischen den rund 50
   Siedlungsabfragen beim Watchlist-Aufbau (einmalig 16.5 s).

Damit ist die Latenzangabe belastbar: Poll-Intervall/2 plus rund 2.3 s
Geometrie plus Abrufzeit. Bei 20-Sekunden-Takt liegt die Erkennung
gut unter einer Minute nach dem ISW-Insert — gegen 18.7 Minuten
Marktträgheit weiterhin reichlich Reserve, aber eben nicht 10 Sekunden.

## 11. Erstes Beobachtungsfenster (23.07. 14:35 – 24.07. 10:36 UTC)

**Ergebnis: kein neues Messereignis.** Der Rekorder lief rund 20 Stunden
durch und protokollierte ausser der Grundierung nichts.

Das ist ein echtes Nullergebnis, kein stiller Ausfall: Ein Abgleich der
gespeicherten Layer-Stände gegen den Live-Server zeigt für alle vier Layer
exakt dieselben Zeitstempel. **ISW hat in diesem Fenster keinen der vier
qualifizierenden Layer angefasst** — letzte Änderung 23.07. 14:13:31 UTC
(Infiltration). Der erwartete Abendzyklus des 23.07. hat diese Layer nicht
berührt.

**Der Krasnoiarske-Fall ist abgeschlossen und bestätigt das Signal.** Alle
drei offenen Märkte der Serie lösten am **23.07. um 23:35:58 UTC mit YES**
auf (July-31, September-30, December-31; `umaResolutionStatus: resolved`).
Damit ist die vollständige Kette belegt:

| Zeit (UTC) | Ereignis |
| --- | --- |
| 22.07. 20:39:00 | ISW legt Infiltrations-Polygon an |
| 22.07. 20:57:43 | Markt repreist, YES 0.046 → 0.93 |
| 23.07. 14:13:31 | letzte ISW-Änderung, Schattierung bleibt |
| 23.07. 23:35:58 | Auflösung YES |

Das Signal vom 22.07. war also ein **echter Positivfall**, kein Fehlalarm.
Vom ISW-Eintrag bis zur Auflösung vergingen rund 27 Stunden; die
Persistenzklausel wurde erfüllt, ohne dass ISW die Fläche nochmals anfassen
musste.

Der gemessene Vorlauf von 18 min 43 s bleibt damit die einzige saubere
Beobachtung, ist aber jetzt eine mit bekanntem Ausgang. N=1 unverändert.

### Konstruktionsfehler: die Watchlist veraltet

Der Cache aus Abschnitt 10 behandelt die ganze Watchlist als unveränderlich.
Das gilt für die Siedlungsgeometrien — **nicht** für die Marktliste: Von den
52 gecachten Märkten waren nach 19 Stunden bereits **10 geschlossen** (die
drei Krasnoiarske-Märkte plus Novyi Donbas, Svitle, Vasylivka, zwei
Novooleksandrivka und zwei Rodynske). Auswertbar und offen blieben 18 statt
26.

Der Rekorder beobachtet also weiter Siedlungen, deren Markt es nicht mehr
gibt, und sieht neue Märkte nicht. Beides verzerrt die Messung: verpasste
Ereignisse fehlen in der Verteilung, tote Märkte erzeugen Treffer ohne
handelbaren Gegenwert.

**Zu trennen:** Siedlungsgeometrie dauerhaft cachen (ändert sich nie, teuer
abzufragen, Auslöser der Drosselung), Marktliste dagegen regelmässig neu
ziehen (ein einziger Gamma-Aufruf, billig). Das ist die erste Aufgabe vor
dem nächsten Dauerlauf.

## 12. Umbau nach Logik-Review (28.07.)

Ein adversarialer Review (36 Agenten, jeder Befund von zwei unabhängigen
Prüfern am Code verifiziert) fand vor dem zweiten Dauerlauf drei bestätigte
und mehrere plausible Defekte — alle mit derselben Signatur wie die fünf
Fehler der ersten Runde: kein Fehler, nur eine still verzerrte Messung.

**Bestätigt:**

1. *`vorlauf_s` mass die falsche Zeit.* Anlage-vor-Edit ignoriert, dass ISW
   bestehende Polygone per Edit ERWEITERT (Krasnoiarske trug einen Edit
   21:02 auf einem 20:39 angelegten Polygon); zusätzlich nahm `deckung()`
   die erste statt der jüngsten schneidenden Fläche, und `jetzt` war vor dem
   Backoff eingefroren (negative Vorläufe möglich).
2. *Die Löschphase eines Rebuilds erzeugte falsche `deckung_verloren` ohne
   Gegenbuchung* — die Persistenzmessung hätte exakt falsche Daten geliefert
   (Schattierung „verschwand", stand aber durchgehend).
3. *Die Rebuild-Bremse griff im Live-Takt nie* (beim 21.07.-Muster sieht ein
   20-s-Poll ~1 neues Feature je Delta, Schwelle war 10) und deckte
   Löschungen gar nicht ab.

**Plausibel, mit Repro belegt:** Der Enthaltungstest prüfte nur den ersten
Punkt des ersten Rings — Multipart-Features (mehrere Aussenringe, in den
ISW-Layern real) erzeugten stille Falsch-Negative. Dazu: Layer-Stand wurde
vor der Auswertung committet (Fehlschlag des Flächenabrufs verlor das
Ereignis endgültig), `None` überschrieb bekannte Stände, eine
Nicht-JSON-200-Antwort umging den Backoff.

**Umbau (Commits vom 28.07.):**

- **Kandidaten-Architektur mit Beruhigungsfenster (60 min).** Jeder
  Übergang wird sofort als `kandidat_treffer`/`kandidat_verlust` mit voller
  T+0-Messung protokolliert (Preis, Orderbuch-Tiefe bis 0.30/0.50, Vorlauf)
  und erst nach Bestand über das Fenster `*_bestaetigt`; kehrt der alte
  Zustand vorher zurück, heben sich Kandidat und Gegenereignis auf (Flap).
  Das ersetzt die Rebuild-Bremse, nettet Löschen-und-Neuzeichnen zu null
  und spiegelt die Persistenzklausel der Marktregel. Die Auswertung nutzt
  nur bestätigte Ereignisse, die T+0-Messung stammt aus dem Kandidaten.
- Vorlauf gegen `max(CreationDate, EditDate)` der jüngsten schneidenden
  Fläche, Erkennungszeit je Layer frisch, Nachfassungen tragen den realen
  Abstand zusätzlich zur geplanten Minute.
- Layer-Stand-Commit erst nach erfolgreicher Auswertung; `None` überschreibt
  nie; Nicht-JSON-200 geht in den Backoff; Zustand-/Protokoll-Schreiben mit
  Wiederholversuch (Windows-Locks).
- Multipart-Fix: Enthaltungstest je Aussenring.
- Marktliste alle 15 min frisch (ein Gamma-Aufruf); nur Siedlungsgeometrien
  dauerhaft gecacht (`geometrie_cache.json`, migriert aus der alten
  watchlist.json). Kandidaten geschlossener Märkte werden als
  `*_markt_geschlossen` protokolliert — oft der interessante Fall
  (aufgelöst wegen des Ereignisses).
- Polarität nur noch über das Slug-Subjekt (`will-russia-…`/`will-ukraine-…`)
  — ein `-recapture-`-Substring hätte `will-russia-recapture-…` invertiert.
- HTTP-Budget je Zyklus (12 Preis-/Buchabrufe): ein Massenübergang löst
  keinen CLOB-Sturm aus.
- Zustands-Schema v2; ein v1-Zustand wird bewusst verworfen und neu
  grundiert, weil der Multipart-Fix die Deckung ändern kann.

Bekannte Restlücke: zwischen Protokoll-Zeile und Zustands-Schreiben kann ein
Absturz einen Kandidaten nach Neustart doppelt protokollieren — bei der
Auswertung über (slug, layer, erste_sichtung) deduplizieren.

Stand nach Umbau: 46 offene Märkte mit Koordinate, 20 auswertbar (vor fünf
Tagen 52/26 — die Veraltung, die der Markt-Refresh jetzt behebt). Suite 1086
grün.

## 13. Nächster Schritt

Rekorder vor Handel. Konkret: ein Profil, das die vier Layer im
20-Sekunden-Takt beobachtet, jede Änderung mit Feature-Zeitstempel und
Geometrie protokolliert, den Schnitt gegen die Watchlist rechnet und für jeden
Treffer den Marktpreis bei T+0, T+1min, T+5min, T+30min mitschreibt — ohne
Order-Pfad. Nach einigen Ereignissen liegt eine Vorlauf-Verteilung vor. Erst
dann ist die Frage „gibt es hier eine Kante" beantwortbar statt behauptbar.

Das entspricht dem Vorgehen beim Mentions-Strang (erst Paper-Protokoll, dann
Echtgeld) und der Vorregistrierungslogik des Piloten.

Konkrete Reihenfolge nach dem ersten Fenster:

1. Marktliste vom Geometrie-Cache trennen (Abschnitt 11).
2. Rekorder in den `ba-thesis`-Klon unter den Watchdog, damit er
   Session-unabhängig läuft. Ohne das gibt es keine Verteilung, sondern nur
   Stichproben von wenigen Stunden.
3. Erst danach über Handel reden.

### Was die Fehlersuche selbst gezeigt hat

Fünf Fehler traten auf, keiner davon im Test sichtbar, alle mit derselben
Signatur — kein Fehler, nur Schweigen:

| Fehler | wie es sich angefühlt hätte |
| --- | --- |
| Rebuild-Bremse prüfte alle statt neue Features | „an der Front passiert nichts" |
| Geometrie 5.6 s je Siedlung | Prozess hängt ohne Meldung |
| ArcGIS 429 im error-Objekt einer 200-Antwort | sporadische Aussetzer |
| Transportfehler ungefangen | Prozess weg, Daten hören auf |
| Watchlist-Neuaufbau bei jedem Start | Start scheitert nach Neustarts |

Bei einem Long-Shot-Markt ist „es passiert gerade nichts" über Wochen
plausibel. Genau deshalb ist bei Latenz-Strategien nicht die fehlende Kante
das Hauptrisiko, sondern die stille Fehlfunktion des Messapparats. Dasselbe
Muster steht in den Mentions-Annotationen: Der Feed-Cache, der eine Stunde
nachhing, war kein Fehler, sondern ein Schweigen.

## Anhang: verwendete Endpunkte

```
Markt-Metadaten   https://gamma-api.polymarket.com/events?tag_slug=ukraine-map
Preishistorie     https://clob.polymarket.com/prices-history?market=<token>&fidelity=1
Orderbuch         https://clob.polymarket.com/book?token_id=<token>
Trades            https://data-api.polymarket.com/trades?market=<conditionId>
ISW-Basis         https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/
  Infiltration    View_AssessedRussianInfiltrationAreasinUkraine_V4/FeatureServer/0
  Advance         AssessedRussianAdvanceInUkraine_V2_view/FeatureServer/0
  Control         VIEW_RussiaCoTinUkraine_V3/FeatureServer/49
  Gains24h        Assessed_Russian_Gains_in_the_Past_24_Hours_view/FeatureServer/0
  Siedlungen      Ukrainian_Settlements_Updated_view/FeatureServer/0
```

Feldverfügbarkeit je Layer (entscheidet die Delta-Strategie):

| Layer | CreationDate | EditDate | Delta-Abfrage möglich |
| --- | --- | --- | --- |
| Infiltration | ja | ja | ja |
| Advance | ja | ja | ja |
| Control (CoT) | nein | ja | nur über EditDate |
| Gains24h | nein | nein | **nein** — Geometrie-Diff nötig |
