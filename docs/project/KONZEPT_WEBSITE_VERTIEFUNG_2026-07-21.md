# Konzept: Website-Vertiefung in Kapitel 4 (Vorschlag vom 21.07.2026, noch nicht eingebaut)

Leitidee: Die Website ist die präsentierte Lösung. Statt die Feature-Aufzählung zu verlängern (Dozent: weniger ist mehr), zeigt die Arbeit das Terminal im Einsatz. Zwei durchgespielte Arbeitspfade ersetzen zehn Einzelbeschreibungen, denn sie zeigen zugleich, wie die Bereiche ineinandergreifen.

## Baustein A: Neuer Unterabschnitt «Das Terminal im Einsatz: zwei Arbeitspfade» (in 4.3, rund zwei Drittel Seite)

**Pfad 1, Verdachtsfall (Research-Nutzung):** Ein Monitor-Alert (mit Telegram-Zustellung) führt zur Fallkarte in der Review-Queue mit Prioritäts-Band, Prüf-Empfehlung und deterministischer Begründung. Von dort ins Wallet-Profil (Positionen, Aktivität, Verlauf), weiter in den Suspicious-Kontext (Score-Band, Verhaltens-Etiketten, Co-Trading-Cluster) und bei Bedarf auf die Track-Liste zur weiteren Beobachtung. Aussage: Vom Roh-Alert zur begründeten menschlichen Prüfung in vier Schritten, ohne dass das Werkzeug je selbst urteilt. Darstellung: Prosa mit Verweis auf die bestehenden Abbildungen 12 und 13, kein neuer Screenshot nötig.

**Pfad 2, Trader-Research (Trading-Nutzung, paper):** Vom Leaderboard (Trefferquoten, Podium, Schnell-Trader) ins Wallet-Detail, von dort in den Backtester, der die Handels-Historie des Traders mit eigenen Sizing-Regeln nachspielt (vier Sizing-Modi, Exposure-Deckel), dann ins Paper-Copytrading mit WebSocket-Erkennung und zur Copy-Fidelity-Messung (Latenz zwischen Original und Kopie, übersprungene Trades, Kapital-Recycling, Abrechnungs-Zuordnung). Aussage: Die Kette misst genau das, woran Nachbildung in der Praxis scheitert. Darstellung: Prosa plus ein neuer Screenshot (Backtester-Replay oder Copy-Fidelity-Tab) als neue Abbildung.

## Baustein B: Kurzer Absatz Markt-Werkzeuge (in 4.3, drei bis vier Sätze)

Live-Trades-Tape (Echtzeit-Abschlüsse beider Börsen), Cross-Venue-Ansicht (dieselbe Frage auf Polymarket und Kalshi, knüpft direkt an das Matching-Problem aus 4.2 an), Whale Flow (grosse Abschlüsse und ihre Adressen), Resolved (frisch aufgelöste Märkte als Realitäts-Abgleich). Eine Zeile je Werkzeug, kein Screenshot.

## Baustein C: Live-Runs-Seite als Fenster in den Feldtest (in 4.8.4, ein bis zwei Sätze plus Abbildung 21)

Der erklärende Absatz steht bereits, Abbildung 21 (Track-Record-Ansicht) folgt nach Übergabe der Bilddatei. Ergänzend ein Satz zu den Nebentabs der Seite (Timing und Repricing, Sizing-Simulator, Einstiegs-Kalibrierung, Track Record), die die Tiefe der Nachauswertung zeigen.

## Bewusst nicht vertieft

Overview, Search, Portfolio, Settings und Resolved bleiben bei ihrer Zeile in Tabelle A4. Grund: keine eigenständige Aussage für die Forschungsfrage, und der Dozent hat Kürze angemahnt.

## Umfang und offene Entscheidungen

Netto rund eine Seite plus ein neuer Screenshot (zusätzlich zu Abbildung 21). Zu entscheiden: (1) Baustein B ja oder nein (kleinste Variante ist nur Baustein A und C), (2) welcher Screenshot für Pfad 2 (Backtester oder Copy-Fidelity), (3) ob die 4.8.4-Überschrift analog zum neuen Titel-Wording von «Feldtest» auf «Live-Pipeline» wechselt.
