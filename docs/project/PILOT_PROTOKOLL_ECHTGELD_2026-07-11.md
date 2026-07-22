# Vorregistrierung: Echtgeld-Mini-Pilot (Feldtest), Version 3

## Änderung in Version 3 (22.07.2026): Arm 2 wird automatisch ausgeführt

Version 3 ändert gegenüber Version 2 **ausschliesslich den Ausführungsmodus und die Einsatzgrösse**, nicht die Signal- oder Entry-Regeln. Die Änderungen im Einzelnen:

1. **Arm 2 wird automatisiert ausgeführt.** Die Formulierung «gehandelt wird manuell durch die Studentin» gilt für Arm 2 nicht mehr. Ein read-only Watcher erzeugt die Signale, ein separates Ausführungsmodul (`operations/pilot/auto_arm2.py`) kauft sie regelkonform. Grund: Die manuelle Prüfung je Signal war für den Stellenwert des Piloten innerhalb der Arbeit zu aufwendig; ohne Automatisierung wäre das Handelsfenster ohne einen einzigen Trade verstrichen.
2. **Arm 1 bleibt manuell** und wird nicht automatisiert. Er verlangt ein Urteil darüber, ob eine externe Referenzquelle den Ausgang irreversibel entschieden hat; das ist maschinell nicht verlässlich entscheidbar. Belegender Fall aus dem Lauf vom 22.07.: Der Watcher markierte «Will bitcoin hit $1m before GTA VI?» als Kandidat, obwohl nichts entschieden ist. Automatisch gehandelt wäre das ein sicherer Verlust. Arm-1-Kandidaten werden weiterhin nur ausgewiesen, nicht gehandelt.
3. **Einsatz je Trade 5 USDC statt 10 USDC**, Gesamtbudget unverändert 100 USDC, also maximal 20 statt 10 Trades. Untergrenze ist das Börsenminimum von 5 Anteilen je Order (bei Preis 0.97 entspricht 5 USDC rund 5.15 Anteilen); ein kleinerer Einsatz wäre technisch nicht ausführbar und würde zudem keine belastbare Slippage mehr erzeugen.
4. **Auswahlregel ergänzt (in Version 2 offen geblieben).** Version 2 legte nicht fest, welche Signale bei Budgetkonkurrenz gehandelt werden. Es gilt ab sofort: **strenge Vorwärts-Reihenfolge nach Signal-Zeitstempel**, ältestes zuerst, bis Budget oder Trade-Deckel erreicht sind. Keine Auswahl nach Attraktivität. Damit ist die Auswahl mechanisch und nachvollziehbar.
5. **Neuprüfung am Buch vor jedem Kauf.** Signale veralten; unmittelbar vor dem Kauf werden Preisfenster (0.90–0.97) und ausführbare Tiefe (mindestens 20 USDC) am Live-Orderbuch erneut geprüft. Fällt ein Signal durch, wird es mit Grund verworfen und nicht gehandelt.

**Wichtig für die Gültigkeit der Vorregistrierung:** Zum Zeitpunkt dieser Änderung war **kein einziger Trade ausgeführt** (`pilot/trades.csv` enthielt nur die Kopfzeile). Version 3 gilt damit für die gesamte Stichprobe; es entsteht kein Bruch innerhalb der Daten und keine nachträgliche Umdeutung bereits getätigter Trades. Die Ergebnis-Box in Kapitel 4 weist die Änderung und ihr Datum ausdrücklich aus.

**Unverändert bleiben:** Universum, Signal- und Entry-Bedingungen beider Arme, Exit nur über die Auflösung, Filter (Tiefe, eindeutige Auflösung, kein Streit, ein Trade pro Markt), Gesamtbudget, Zeitplan, Abbruchkriterien, Dokumentationspflichten je Trade und das Berichtsformat.

**Sicherheitsnetze der Automatisierung:** Dry-Run ist Standard (Echtgeld nur mit ausdrücklichem `--live`), Probeläufe schreiben in ein getrenntes Journal und fassen `pilot/trades.csv` nicht an, harter Budgetdeckel aus der bereits gehandelten Summe, höchstens ein Trade je Markt, ausschliesslich Käufe (Verkäufe sind protokollwidrig), Kill-Switch über `data/live/STOP`, automatischer Stopp nach Fensterende am 01.08.2026.

---

## Version 2 (16.07.2026), weiterhin gültig ausser den oben genannten Punkten

Version 2 vom 16.07.2026, ersetzt die Fassung vom 11.07. Grund: Die Fassung 1 verlangte, bestehende Strategie-Parameter aus dem Repo «einzufrieren». Eine Prüfung des Repos hat gezeigt, dass es keine formalisierten Regeln gibt. Die Einstufungen in Tabelle 6 der Arbeit (Tail-Fade B, Oracle-Divergence-Fade B mit 26 Treffern bei 28 Fällen) stammen aus Forward-Replay-Beobachtungen ohne dokumentierte Schwellen, Entry- oder Exit-Regeln. Darum definiert diese Version die Regeln neu und ex ante. Es wurde noch kein Trade ausgeführt, die Vorregistrierung bleibt damit gültig. Nach Bestätigung durch die Studentin gilt Regel-Freeze.

## Zweck und Einordnung

Der Pilot ist ein Ausführbarkeits- und Kosten-Feldtest, kein Renditenachweis. Er prüft unter echten Bedingungen (Fills, Gebühren, Slippage, Orderbuchtiefe), ob sich zwei aus den Replay-Beobachtungen abgeleitete, hier erstmals formalisierte Regeln handeln lassen. Wichtig für die Ehrlichkeit der Arbeit: Die Pilot-Regeln sind eine Neudefinition in Anlehnung an die beobachteten Muster, nicht die (nicht formalisierten) Replay-Kriterien. Die Ergebnis-Box in Kapitel 4 wird genau das sagen. Die Werkzeuge aus Kapitel 4 behalten ihren Zustand ohne Order-Pfad, gehandelt wird manuell durch die Studentin.

## Regeln (ex ante, nach Bestätigung eingefroren)

**Arm 1: Referenz-entschieden-Fade** (formalisierte Fassung des beobachteten Oracle-Divergence-Musters)

Universum: Polymarket-Krypto-Märkte mit numerischer Auflösungsreferenz und dokumentierter Referenzquelle (z.B. «BTC über X am Datum D»). Signal: Die Referenzquelle hat den Ausgang gemäss Marktregeln bereits irreversibel entschieden (Schwelle erreicht oder Stichtag verstrichen), der Markt handelt die entschiedene Seite aber noch zu 0.97 oder tiefer. Entry: Kauf der entschiedenen Seite zum Briefkurs, solange dieser höchstens 0.97 beträgt. Exit: nur über die Auflösung. Filter: Orderbuchtiefe auf der Kaufseite mindestens 20 USDC, keine Märkte mit laufendem Orakel-Streit ohne eindeutige Referenz, höchstens ein Trade pro Markt.

**Arm 2: Favoriten-Seite (Tail-Fade)**

Universum: Polymarket-Märkte mit Auflösung bis spätestens 02.08.2026. Signal und Entry: Die Favoriten-Seite handelt zwischen 0.90 und 0.97 bei einer Restlaufzeit von höchstens 21 Tagen. Exit: nur über die Auflösung, kein vorzeitiger Verkauf. Filter: Orderbuchtiefe mindestens 20 USDC, eindeutige Auflösungsregeln, kein laufender Streit, höchstens ein Trade pro Markt.

**Beide Arme:** Einsatz pro Trade ist fix ein Zehntel des Gesamtbudgets. Bei Budgetkonkurrenz hat Arm 1 Vorrang. Ein Trade ausserhalb dieser Regeln gilt als Protokollverletzung und wird als solche berichtet, nicht nachträglich umgedeutet.

## Budgetrahmen

Nur Eigenmittel, Totalverlust einkalkuliert, keine Nachschüsse. Bestätigt: **100 USDC gesamt** (Bestätigung der Studentin am 18.07.2026). Damit gilt der Regel-Freeze; Einsatz je Trade ein Zehntel = 10 USDC, maximal 10 Trades.

## Zeitplan

Regeln bestätigen und Watcher lauffähig: bis 18.07. Handelsfenster: bis 01.08. Auswertung: 02. bis 03.08. Einbau der Ergebnis-Box in Kapitel 4: bis 05.08. Abgabe: 07.08., 13:00 Uhr. Bei Zeitnot hat die Abgabe Vorrang.

## Dokumentation je Trade (Pflichtfelder)

Zeitstempel (UTC), Markt (ID und Frage), Arm, Signal (Regel und Auslösewert), Seite, Signalpreis, Ausführungspreis, Grösse, Gebühren, Slippage (Ausführung minus Signal), Orderbuchtiefe beim Einstieg, Exit (Zeit, Preis, Grund), Bemerkung. Ablage als CSV (`pilot/trades.csv`), die Tabelle geht ohne Wallet-Adresse in den Anhang.

## Abbruchkriterien

Budget aufgebraucht, Plattform- oder Zugangsproblem, kein Signal in beiden Armen bis 26.07., oder Gefährdung des Abgabetermins.

## Offener Nachweis-Punkt (unabhängig vom Piloten)

Für die Verteidigung muss auffindbar sein, worauf die Tabelle-6-Einstufungen beruhen (insbesondere die 28 Oracle-Fälle mit 26 Treffern). Claude Code soll die Forward-Replay-Artefakte oder Logs im Repo lokalisieren und den Fundort in `docs/project/REPLAY_NACHWEIS.md` dokumentieren. Falls sich kein Nachweis findet, muss die Arbeit die Stelle vorsichtiger formulieren. Das entscheidet die Studentin nach dem Befund.

## Risiken und Rahmen

Marktrisiko bis Totalverlust je Position, Auflösungs- und Orakel-Streit-Risiko, Plattformzugang und Nutzungsbedingungen, steuerliche Behandlung privater Kleinbeträge. Der Pilot ist eine private, vom Betreuer sanktionierte Forschungshandlung der Studentin und keine Anlageberatung. In der Arbeit wird er als solcher gekennzeichnet.

## Berichtsformat in Kapitel 4

Kompakte Box (acht bis zwölf Sätze) plus Mini-Tabelle: Signale und Trades je Arm, Regeltreue-Quote, Median-Slippage, Gebührenanteil, Differenz zwischen erwartetem und realem Fill, Hindernisse. Ausdrücklich: Regeln neu formalisiert, Stichprobe klein, keine Rendite-Behauptung.
