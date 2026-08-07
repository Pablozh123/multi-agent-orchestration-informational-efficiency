# Claude-Code-Auftrag: Pipeline-Forward füllen (22.07.2026)

Vorher lesen: docs/project/SYNC_KONTEXT_2026-07-16.md und docs/project/PROJEKT_INVENTAR.md.

## Befund

Das publizierte Artefakt `prediction-market-terminal/public/data/pipeline_forward.json` ist leer. Eigener Hinweis im Artefakt: «Source decisions_log.jsonl not present on this machine -- empty artifact», Profil steht auf allin_july3. Ursache: Die tägliche Kette läuft in der Projects-Arbeitskopie, `data/live/` ist gitignored und die Rohdaten der Läufe liegen nur im ba-thesis-Checkout (dort existiert `data/live/<profil>/decisions_log.jsonl` für alle abgeschlossenen Läufe).

## Aufgaben

1. Quelle beheben, eine der beiden Varianten: (a) kuratierte Kopien der `decisions_log.jsonl` abgeschlossener Läufe ins Repo committen (sie enthalten Entscheidungsfelder und Buchpreise, keine Schlüssel; `deposit_wallet.json`, Audio und Wallet-Dateien bleiben draussen), oder (b) den Quellpfad der Kette konfigurierbar machen und auf das Checkout mit Daten zeigen.
2. Profil aktualisieren: statt allin_july3 den jüngsten Lauf mit Käufen (allin_july17) publizieren, oder besser eine Liste je Lauf.
3. Schema, Kennzeichnung (observed/paper, keine Wallet-Daten, keine Rendite-Aussage) und Redaktions-Gate unverändert lassen.
4. Nach dem nächsten Kettenlauf verifizieren, dass `pipeline_forward.json` Einträge und Wortzähler-Endstände enthält, danach PROJEKT_INVENTAR.md fortschreiben (Abschnitt Update genügt).

Basis ist main, kleine Commits, ein Test für den Quellpfad-Fallback (Quelle fehlt ergibt weiterhin ein valides, leeres Artefakt mit Hinweis).
