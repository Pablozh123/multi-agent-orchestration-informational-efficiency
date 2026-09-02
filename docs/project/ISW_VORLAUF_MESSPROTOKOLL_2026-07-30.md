# Messprotokoll ISW-Vorlauf (Vorregistrierung), Version 1

Stand 30.07.2026 (Amendments bis 02.09.2026). Analog zur Vorregistrierungslogik des Echtgeld-Piloten
(PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md): Ereignisdefinition, Kennzahlen,
Erfolgskriterien und Entscheidungsregel werden VOR dem Einlauf der Daten
festgelegt. Änderungen nach dem Einfrieren nur als datierter
Amendment-Eintrag am Ende dieses Dokuments.

**Status: ENTWURF.** Die mit ▸ markierten Schwellen sind Vorschläge von
Claude Code; eingefroren werden sie durch die Studentin. Ab dem Einfrieren
gilt Regel-Freeze wie beim Piloten.

## 1. Fragestellung

Existiert auf den Polymarket-Ukraine-Karten-Märkten ein wiederkehrender
Latenz-Edge gegenüber der Auflösungsquelle (ISW-ArcGIS-Karte) — und wie oft?
Die zwei Vorab-Beobachtungen spannen das Spektrum auf: Krasnoiarske
(22.07., 18 min 43 s totes Fenster, ~50 pp) und Oleksiyevo-Druzhkivka
(29.07., weitgehend antizipiert, ~5 pp Restbewegung). Die entscheidende
Grösse ist der **Anteil der Überraschungsfälle**, nicht der mittlere
Vorlauf.

## 2. Datenquelle und Instrument

Ereignisprotokoll des read-only ISW-Rekorders (Watchdog-Profil
`isw_ukraine` im ba-thesis-Klon, `data/live/isw_ukraine/ereignisse.jsonl`).
Instrument-Dokumentation: UKRAINE_ISW_LATENZ_SONDIERUNG.md. Auswertung
ausschliesslich deterministisch über:

```
python -m operations.analysis.isw_vorlauf_auswertung \
    --protokoll data/live/isw_ukraine/ereignisse.jsonl --mit-referenz
```

Die Lizenzfrage zur Nutzung der ISW-Daten ist geklärt (Rückmeldung der
Studentin, 30.07.): Nutzung möglich.

## 3. Ereignisdefinition

**Marktzeile:** ein `kandidat_treffer` mit `polaritaet=russisch` und
`kriterium=beruehrung` (auswertbar), der das 60-Minuten-Beruhigungsfenster
als `treffer_bestaetigt` übersteht oder per `treffer_markt_geschlossen`
endet. Flaps (`treffer_verworfen`) und offene Kandidaten zählen nicht.

**Siedlungsereignis** (Analyseeinheit): Gruppe der Marktzeilen mit
gleichem (Siedlung, Layer, Erkennungszeit). Mehrere Deadlines derselben
Siedlung sind korrelierte Instanzen desselben physischen Ereignisses und
zählen als EIN Ereignis. Klassifiziert wird über den **Median der
T+0-Preise** der Gruppe (neutral gegenüber der Deadline-Wahl).

**Referenzfall:** Krasnoiarske (22.07.) wurde vor der Armierung manuell
aus CLOB-/ArcGIS-Daten rekonstruiert und geht als markierte Referenzzeile
(`--mit-referenz`) in die Verteilung ein; in der Thesis wird er als
rekonstruiert ausgewiesen.

## 4. Klassifikation (T+0 = YES-Mittelpreis bei Erkennung)

| Klasse | Bedingung | Bedeutung |
| --- | --- | --- |
| ueberraschung | T+0 < ▸0.50 | Markt hatte die Schattierung nicht eingepreist |
| teilweise | 0.50–0.85 | Markt war unterwegs |
| antizipiert | T+0 > ▸0.85 | Markt war der Karte voraus |

## 5. Kennzahlen je Ereignis

Vorlauf (Erkennung − jüngste Flächen-Änderung), T+0-Preis und Ask,
Ask-Tiefe ≤0.30/≤0.50 USD bei T+0, Preis bei T+1/5/30 min, delta_t30.

Auf Siedlungsereignis-Ebene ist jede Kennzahl der **Median über die
Marktzeilen** der Gruppe.

**Gültigkeit der Nachfassungen.** Ein Preis zählt nur dann als T+n, wenn
er auch dort gemessen wurde: `|real_s − 60·n| ≤ 180 s`. Der Rekorder holt
Nachfassungen am Zyklusende (Ruhe-Takt 120 s), und offene Aufträge
überleben im Zustand — nach einem Absturz mit Watchdog-Neustart feuert
eine 30-Minuten-Nachfassung sonst Stunden später und ihre Bewegung ginge
als `delta_t30` in die Verteilung ein. Verspätete Messungen werden
verworfen und als `nachfassung_verspaetet` ausgewiesen.

## 6. Erfolgskriterium und Entscheidungsregel

Auswertungsstichtag: ▸**14.08.2026** oder ▸**N = 10 Siedlungsereignisse**,
je nachdem, was zuerst eintritt.

**Go für eine Paper-Trade-Phase** (nicht Echtgeld), wenn ALLE drei gelten:

1. Anteil Überraschungsfälle ≥ ▸20 % der **klassifizierbaren**
   Siedlungsereignisse,
2. in den Überraschungsfällen mediane Ask-Tiefe ≤0.50 bei T+0 ≥ ▸100 USD,
3. in den Überraschungsfällen medianes delta_t30 ≥ ▸+10 pp.

Kriterien 2 und 3 werden über die als `ueberraschung` klassifizierten
**Siedlungsereignisse** gerechnet, nicht über einzeln klassifizierte
Marktzeilen: eine 0.48er-Zeile innerhalb eines insgesamt „teilweise"
eingepreisten Ereignisses gehört nicht in den Überraschungs-Median, und
korrelierte Zeilen desselben Ereignisses dürfen ihn nicht mehrfach
gewichten.

**Nenner von Kriterium 1** sind die klassifizierbaren Ereignisse, also
solche mit mindestens einem T+0-Preis. Ereignisse ohne Preis (das
HTTP-Budget des Rekorders deckelt 12 Abrufe je Zyklus, bei
Massenübergängen bleiben spätere Kandidaten preislos) sind keine Aussage
„war eingepreist"; sie würden den Anteil einseitig nach unten verwässern
und die 20-%-Schwelle kippen. Sie werden als Klasse `unbekannt`
gesondert ausgewiesen.

Das Skript wertet diese Kriterien selbst aus und gibt eine Entscheidung
(`go_paper` / `no_go` / `weiter_messen`) aus; die Schwellen stehen in
`GO_SCHWELLEN` und sind mit diesem Dokument abzugleichen.

**No-Go / weiter messen** sonst. Ein Go führt zunächst zu einer
Paper-Phase mit denselben Protokollregeln; Echtgeld erst nach separater
Entscheidung der Studentin auf Basis der Paper-Ergebnisse (Budget- und
Sizing-Regeln dann analog Pilot-Protokoll).

Unabhängig vom Ausgang sind die Ergebnisse Thesis-Material: ein
dokumentierter Ineffizienzfall (18 min) und ein Antizipationsfall in
derselben Marktfamilie tragen die Effizienz-Diskussion in Kapitel 4 auch
als Null- oder Negativbefund.

## 7. Bekannte Grenzen (vorab deklariert)

- Der Rekorder lief erst ab 28.07. (23:15 UTC) durchgehend; frühere
  Ereignisse existieren nur als Rekonstruktion (Krasnoiarske).
- `gains24h` liefert keine Feature-Zeitstempel → Vorlauf dort undefiniert.
- Erkennungslatenz des Rekorders (~20–120 s je nach Taktfenster) ist im
  Vorlauf enthalten; bei Fenstern im Minutenbereich vernachlässigbar.
- Marktschluss vor Fensterende wird gesondert ausgewiesen
  (`markt_geschlossen`), oft der Fall „aufgelöst wegen des Ereignisses".
- Doppelzeilen nach Prozessabsturz werden deterministisch dedupliziert.

## Amendments

**A1 — 27.08.2026: Instrument-Wechsel Poll-Takt 20 s → 1 s (aktives
Fenster) + Cache-Buster.** Anlass: Trade-Forensik Stinky 11.08. — die
ersten Käufe kamen 5 s nach der Karten-Publikation, das Buch war nach
6 s leergefegt; mit 20-s-Takt (gemessene Latenz 45 s) misst der Rekorder
den T+0-Preis systematisch NACH dem Sofort-Repricing. Zusätzlich
entdeckt 27.08.: der CDN cached die Layer-Metadaten 300 s
(`max-age=300`) — der bisherige Poll las bis zu 5 Minuten alte Stände;
seit diesem Amendment erzwingt ein Cache-Buster-Parameter Origin-
Antworten. Lasttest 27.08. (2×4 min, 2 und 4 req/s): keine Drosselung.
Konsequenz für die Auswertung: `vorlauf_s` und die T+0-Preise vor/nach
dem 27.08. stammen aus verschiedenen Instrumenten und werden bei
Latenz-Aussagen getrennt ausgewiesen; die Klassifikation
(Überraschung/antizipiert) bleibt definitionsgleich. Der bekannte
Grenzen-Punkt „Erkennungslatenz ~20–120 s" gilt ab 27.08. als „~2 s im
Aktivfenster, ~120 s im Ruhefenster". Auftrag der Autorin vom 27.08.
(„Umbau auf 1–2-Sekunden-Polling"), umgesetzt in Commit auf Branch
feat/isw-schnellpoll.

**A2 — 02.09.2026: Zweiter Messkanal DeepStateMap (Vorlauf zur
ISW-Quelle).** Anlass: Hannivka 01.09. — der ISW-Rekorder erkannte die
Änderung 0,8 s nach dem Feature-Zeitstempel (Instrument aus A1 arbeitet),
und die Ask-Seite war trotzdem schon weg (bid 0.79 / ask 0.98 bei +1 s,
erste Prints bei +3 s durch dieselbe Bot-Crew wie bei Stinky). Das
Latenzrennen an der ISW-Quelle ist damit unabhängig vom Poll-Takt
verloren. Die grossen capture-Leitern nennen DeepStateMap als offiziellen
Fallback; DeepState aktualisiert mehrmals täglich, Stunden vor dem
ISW-Tagesupdate, und bei Stinky lag der Markt bis zur ISW-Minute flach
(n=1). Seit diesem Amendment läuft parallel und read-only der
`deepstate_rekorder` (Watchdog-Profil `deepstate_ukraine`,
`operations/pipeline/deepstate_rekorder.py`): Stolperdraht ist
`/api/history/last` mit ETag (304 ohne Änderung, Cache-Buster gegen den
300-s-CDN-Cache), Klassen `besetzt` (occupied) und `grauzone` (unknown
status, Gegenstück zum ISW-Infiltrationslayer), Übergänge je Markt und
Klasse auf denselben Siedlungsflächen wie beim ISW-Rekorder mit
T+0-Preis, Buchtiefe und Nachfassungen +1/+5/+30 min; dazu die im
Beschreibungstext erwähnten Orte mit Koordinaten (Umkreis 5 km). Die
Auswertung `operations.analysis.deepstate_vorlauf_auswertung` verknüpft
DeepState- und ISW-Ereignisse je Siedlung (Fenster ▸96 h) und liefert
Trefferquote, Median-Vorlauf, Preisraum (ISW-T+0 minus DeepState-T+0)
sowie die Gegenrichtung (ISW-Ereignisse ohne DeepState-Vorlauf).
Vorschlag für eine Go-Prüfung des Kanals (▸ = Vorschlag, Einfrieren
Sache der Autorin): N ≥ ▸10 entschiedene DeepState-Siedlungsereignisse,
Trefferquote ≥ ▸0.5, Median-Vorlauf ≥ ▸2 h, Median-Preisraum ≥ ▸0.10.
**Die Messsemantik von §3–§6 (ISW-Kanal) bleibt unverändert;** der
DeepState-Kanal ist eine eigene Messreihe mit eigenem Protokoll
(`data/live/deepstate_ukraine/ereignisse.jsonl`). Offen und weiterhin
Entscheidung der Autorin: der T+0-Anker des ISW-Kanals (Hannivka wird
mit T+0-Mid 0.885 als „antizipiert" geführt, gegen die
Vor-Publikations-Baseline 0.79 wäre es „teilweise") und die Aufnahme der
capture-all-of-Klasse in die ISW-Klassifikation.

**A3 — 02.09.2026: Abkühlpause bei quellseitiger Abweisung (HTTP 403).**
Anlass: Betriebsvorfall 01.09. — der ArcGIS-Origin wies 20:00–21:01 UTC
exakt eine Stunde lang jede Anfrage auf allen vier Layern mit HTTP 403
ab (1674 Fehlerzeilen). 403 stand bewusst nicht im Wiederhol-Backoff
des Clients (dauerhafter Fehler), der 1-s-Takt aus A1 lief deshalb
ungebremst durch die Sperre — mit dem Risiko, dass aus einer
Stundensperre eine Dauersperre des Schnell-Polls wird. Seit diesem
Amendment schaltet ein 403 den Rekorder in eine Abkühlpause (60 s,
verdoppelt bis 600 s), protokolliert EIN `sperre`-Ereignis beim Beginn
und ein `sperre_ende` (Dauer, Versuche) beim ersten Erfolg, beide mit
`von_utc` (Sperrbeginn); Herzschläge
laufen während der Pause weiter, damit der Watchdog den wartenden
Rekorder nicht neu startet. **Messsemantik unverändert:** gesperrte
Zyklen schreiben `letzter_zyklus_ts` nicht fort, das erste Ereignis
nach einer Sperre trägt deshalb `nach_ausfall_s` über die gesamte
Sperrdauer — derselbe Pfad wie `ausfall_erkannt` nach Prozess- oder
Host-Ausfällen (§7). Ereignisse mit `nach_ausfall_s` > 300 s gelten
weiterhin als „unsicher". Zwei weitere Lücken sind vorab zu deklarieren:
29.08. 07:25Z – 30.08. 10:47Z (27,4 h, Host-Ausfall inkl. Watchdog, kein
Bot-Fehler) und 01.09. 20:00–21:01Z (Sperre). Umsetzung: Branch
`fix/isw-403-sperre`, Tests `tests/test_isw_rekorder_sperre.py`.
