# Vorregistrierung: Echtgeld-Mini-Pilot (Feldtest), Version 2

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

Nur Eigenmittel, Totalverlust einkalkuliert, keine Nachschüsse. Vorschlag: 100 bis 200 USDC gesamt. [Budgetzahl von der Studentin NACHZUTRAGEN, Datum der Bestätigung: ___]

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
