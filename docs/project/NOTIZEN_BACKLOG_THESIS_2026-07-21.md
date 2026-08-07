# Notizen und Backlog (Stand 21.07.2026, fortgeschrieben 22.07.)

Status 03.08.: Fazit A eingebaut, Kapitel 6 neu (Produktreife, Desk-Forschungslinie, Agenten live, wissenschaftliche Erweiterungen), damit sind die Punkte 4 (soweit thesis-seitig möglich) und 5 abgeschlossen. Offen: E283-Entscheid, Betreuer-Segen Titel, Formalia (Management Summary, Vorwort, Name Titelblatt, Zotero, exakte Testzahl).

Status 29.07.: Zweite Feldtest-Strecke (Live-Ereignisse 24.-29.07.) als Phase-2-Block in 4.7.4 eingebaut, Punkt 5 (Fazit) ist damit inhaltlich komplett vorbereitet, Entwurf für 5.1 liegt zur Freigabe im Chat.

Status 27.07.: Arbitrage-Feldtest (4.2.2) auf Wunsch der Studentin komplett aus der Arbeit gestrichen, die Pilot-Ergebnis-Box nach dem 01.08. entfällt damit, der Termin am 02.08. bleibt für Feldtest-Zahlen-Refresh und Fazit. Swisstony-Fallbeispiel auf die Kernlinie gekürzt, Copy-Widerlegung bleibt Fazit-Baustein.

Status 22.07. abends: Punkt 1 erledigt (neuer Untertitel «KI-Agenten-Orchestrierung, Research-Terminal und Live-Pipelines auf Polymarket», Betreuer-Segen noch einholen). Punkt 2 erledigt (Anhang bereinigt). Punkt 3 erledigt (Abbildung 13 durch aktuellen Review-Queue-Stand ersetzt, neue Abbildung 19 mit der Live-Runs-Timing-Ansicht, Backtester bewusst ohne Screenshot, Beschreibung genügt). Punkt 4 als CC-Auftrag übergeben, Ergebnis ausstehend. Punkt 5 offen (Fazit, nach dem Pilot-Fenster). Punkt 6 im Kern erledigt (Übersicht zuerst, Arbeitspfade, Markt-Werkzeuge, zwei Seiten-Portraits), offen bleibt nur Feintuning nach Lektüre.

Sechs gemerkte Punkte der Studentin vom 21.07. Ausdrücklich nur Notiz, Umsetzung erst nach Freigabe je Punkt. Kontext je Punkt von Cowork ergänzt, damit die spätere Umsetzung ohne Rückfragen starten kann.

## 1. Arbeitstitel stärker auf KI ausrichten

Der aktuelle Titel («Informationelle Effizienz dezentraler Prognosemärkte: Polymarket im Vergleich zu traditionellen Prognosequellen während der US-Präsidentschaftswahl 2024») betont die US-Wahl. Wunsch: näher am ursprünglichen Arbeitstitel (sinngemäss «Erstellung einer MCP-Multiagenten-Orchestrierung»), also KI, Agenten und Werkzeug sichtbarer machen, die US-Wahl weniger prominent. Zu beachten bei der Umsetzung: Der empirische Kern (H1 bis H3) beruht weiterhin auf den Wahldaten 2024, der Titel muss dazu ehrlich bleiben. Vorgehen: drei bis fünf Titelvorschläge mit Untertitel erarbeiten (z.B. Haupttitel zur KI-gestützten Beobachtung der Markteffizienz, Untertitel mit dem empirischen Fall), Studentin wählt, danach mit dem Betreuer kurz abstimmen und Titelblatt, Kopfzeilen und Management Summary nachziehen.

## 2. Anhang aufräumen

Interne Prozessdokumente wie PROZESS_ZUSAMMENFASSUNG_DOZENT.md gehören nicht in die Abgabe. Vorgehen: Anhang- und Beilagenverzeichnis der Thesis durchgehen, interne Dokumente (Prozess-Zusammenfassungen, Arbeitslogs, Briefings) aus der Abgabe nehmen, in docs/project bleiben sie natürlich erhalten. Prüfen, was die Wegleitung als Beilage verlangt (Hilfsmittelverzeichnis bleibt, Prompt-Log bleibt separat und ist nicht Teil der Abgabe).

## 3. Bild der Live-Runs-Seite einbauen

Der erklärende Absatz steht seit dem 21.07. in 4.8.4, der Screenshot ist aufgenommen (Kacheln 7 Läufe, 15 Wetten, +175.09 wallet-abgeglichen, E281-Karte mit «First on 6/6 fills» und «Median follower +18 min»). Fehlt nur die Bilddatei von der Studentin (Browser-Download vom 21.07. oder eigener Screenshot des offenen Tabs), dann Einbau als Abbildung 21 mit Bildunterschrift und Verweissatz.

## 4. Pipeline-Forward fertigstellen

Der beobachtende Paper-Forward-Test der Analyse-Pipeline ist als Seite und Artefakt (pipeline_forward.json) angelegt, aber inhaltlich noch nicht fertig. Arbeitspaket für Claude Code im Repo (Lauf-Logik und publizierte Kennzahlen vervollständigen), danach zieht Cowork den Stand in 4.5 und in die Anhang-Beschreibung nach (Abbildung A6). Stand im Kopf behalten: Im ersten Kettenlauf stand der Schritt noch auf «quelle_fehlt».

## 5. Fazit neu denken

Der erste Anleitung-Entwurf ist verworfen. Neue Zielrichtung der Studentin: Das Fazit soll spannend sein und konkret zeigen, welche Strategie für welchen Zweck die beste ist, mit Warnungen und Haupterkenntnissen (deckt sich mit dem Dozentenwunsch vom 11.07.). Material dafür liegt jetzt komplett vor: Mentions-Latenz-Bot als belegtes Speed-Play mit klaren Bedingungen (dünn beachtete Ränder, Sprecher-Verifikation, Nicht-Handeln als Normalfall), Arbitrage als praktisch nicht bewirtschaftbar (Tabelle 6), Tail-Fade und Oracle-Divergence als dokumentiert aber unbestätigt, Verdachts-Screening als Prüfwerkzeug statt Strategie, dazu die Pilot-Ergebnisse nach dem 01.08. Vorgehen: neuer Entwurf im Chat zur Freigabe, erst nach dem Pilot-Fenster, damit die Ergebnis-Box einfliessen kann.

## 6. Website-Inhalte weiter ausführen

Gefühl der Studentin: Die Website ist die präsentierte Lösung und darf im Text noch mehr Raum bekommen: welche Inhalte stecken in den Bereichen und wie nutzt man sie konkret. Vorgehen: 4.3 (und punktuell der Anhang A4) um Nutzungs-Perspektive erweitern, etwa je Gruppe ein kurzer Anwendungsfluss (Beispiel: Von einem Alert im Monitor über die Review-Queue zur Wallet-Ansicht und zum Verdachts-Screening, oder: Backtester mit eigenen Sizing-Regeln auf einem Leaderboard-Trader). Quellen: WORKSPACE_HELP-Texte, HANDOFF, eigene Nutzung der Studentin. Spannungsfeld beachten: Dozent will «weniger ist mehr», also Nutzung zeigen statt Feature-Listen verlängern.

## Reihenfolge-Vorschlag (wenn freigegeben)

Punkt 3 sofort nach Dateiübergabe. Punkte 1, 2 und 6 als nächste Textrunde zusammen. Punkt 4 parallel bei Claude Code. Punkt 5 nach dem 01.08. zusammen mit der Pilot-Ergebnis-Box (Erinnerung am 02.08. ist gesetzt und wird um diese Punkte ergänzt).
