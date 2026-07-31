# Messprotokoll ISW-Vorlauf (Vorregistrierung), Version 1

Stand 30.07.2026. Analog zur Vorregistrierungslogik des Echtgeld-Piloten
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

*(leer — Einträge nur nach dem Einfrieren, datiert, mit Begründung)*
