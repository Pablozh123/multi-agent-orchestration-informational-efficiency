# Sync-Kontext: Projekte, Speicherorte und Arbeitsteilung

Stand 16.07.2026. Dieses Dokument ist die gemeinsame Referenz für alle Beteiligten: die Studentin, die Cowork-Session (Textarbeit an der Thesis) und die Claude-Code-Sessions (Code in den Repos). Es gehört ins Repo nach `docs/project/` und wird bei jedem Meilenstein nachgeführt. Jede neue Claude-Code-Session soll es zu Beginn lesen (Verweis dazu in CLAUDE.md bzw. AGENTS.md des Repos eintragen).

## 1. Wo liegen die Dateien wirklich

**Cowork (diese Chat-Session)** arbeitet in einem eigenen Cloud-Arbeitsbereich bei Anthropic. Dort liegen die Arbeitskopien der Thesis (entpackt), alle Versionsstände (v1 bis v14) und die Projektdateien. Dieser Bereich ist nicht dein Computer. Nichts davon landet automatisch auf deiner Festplatte.

**Dein Computer:** Die Thesis-Datei existiert nur dort, wo du sie beim Herunterladen aus dem Chat ablegst (bisher offenbar als Bachelorarbeit_FHNW_AKTUELL_n.docx ausserhalb des Repos). Das Repo `C:\Users\chole\ba-thesis` enthält den Analysecode und `docs\project\` für die Projektdokumente, aber nicht die Thesis-docx.

**Gelernte Regel seit 16.07.:** Der Schreibweg von Cowork auf deine Festplatte über die Ordner-Verbindung ist unzuverlässig (Dateien landeten nur in einer Sitzungskopie und gingen verloren). Darum gilt: Cowork liefert alles über den Chat, du legst es selbst ab. Umgekehrt bekomme ich neue Stände nur, wenn du sie hochlädst.

**Kanonische Ablage:** (Ordnerkarte mit Stand 07.08. in Abschnitt 7)

| Was | Kanonischer Ort | Wer pflegt |
| --- | --- | --- |
| Thesis (docx) | dein Ablageort, Upload in den Chat bei jeder Arbeitsrunde | du (Versionierung im Dateinamen), Cowork diffed bei jedem Upload |
| Projektdokumente (Pläne, Logs, Protokolle, Pilot, Briefings) | `ba-thesis\docs\project\` | Cowork erstellt via Chat, du legst ab, Claude Code liest |
| Code Analyse und Pilot | Repo ba-thesis | Claude Code |
| Code Terminal/Website | Terminal-Repo (Pfad siehe Inventar) | Claude Code |
| Dieses Sync-Dokument und PROJEKT_INVENTAR.md | `ba-thesis\docs\project\` | alle, Claude Code aktualisiert das Inventar |

## 2. Projektlandschaft (Stand des Wissens von Cowork)

**Projekt A: Thesis-Analyse-Repo** (`C:\Users\chole\ba-thesis`, im Sprachgebrauch auch «multiagentorchestrationinformationalefficiency»). Python-Stack mit SQLite (`data/thesis.db`), DuckDB, pytest (Stand Juni: 640 Tests), deterministischer Analysekern für H1 bis H3, tägliche Publikations-Kette seit 09.07.2026 (Collector, Anomalie-Kandidaten, read-only Agenten-Schicht mit Mock-Backend, sechs schema-validierte JSON-Artefakte hinter Redaktions-Gate). Branches: `main`, `feat/live-bot-x-feed-ev-sizing` (Mentions-Bot: X-Feed-Wächter, EV-Sizing, Märkte wie Elon/All-In, nicht Teil der Thesis-Guardrails), `backup`. Neu entstehend auf `pilot/feldtest-2026-07`: Watcher, Trade-Journal und Auswertung für den vorregistrierten Echtgeld-Feldtest (Spez: PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md, Version 2).

**Projekt B: Prediction-Market-Terminal** (Website, eigenes Repo, genauer Pfad im Inventar nachzutragen). Laut Thesis-Kapitel 4: Arbeitsbereiche Marktsuche, Trader-Leaderboard und Wallet-Profile, Live-Trade-Flow, Whale Flow, Verdachts-Screening, Cross-Venue-Vergleich, Backtester, Paper-Copytrading, Monitor und Portfolio, dazu Research-Seiten, auf die die tägliche Kette publiziert. Der Arbitrage-Scanner (TypeScript/Node) gehört in diesen Umkreis. Die Website hat laut Studentin inzwischen viele neue Inhalte, die in der Thesis noch nicht abgebildet sind.

**Gebaute Pipelines, die die Thesis beschreibt:** die Mentions-Pipeline (Feed-Wächter, faster-whisper-Transkription, deterministische Zählung, Paper-Protokoll, zwei dokumentierte Live-Läufe mit je 35 Entscheidungen, Abbildung 18), der Arbitrage-Scanner mit Forward-Replay und Strategie-Einstufungen (Tabelle 6), die Wallet-Tier- und Anomalie-Diagnostik, die Agenten-Review-Schicht, die Kategorien-Diagnostik über fünf Marktkategorien.

**Bekannte Lücken in meinem Wissen (füllt das Inventar):** exakter Pfad und Stand des Terminal-Repos, aktuelle Website-Seitenliste, aktuelle Testzahl, Lauf-Statistik der täglichen Kette seit 09.07., Fundort der Forward-Replay-Nachweise (26/28-Fälle), Stand des Piloten (Watcher, Signale, Trades), Stand und Zweck des Mentions-Bot-Branches.

## 3. Sync-Regeln ab jetzt

1. Dateiaustausch nur über den Chat. Ablage durch dich gemäss Tabelle oben.
2. In CLAUDE.md bzw. AGENTS.md beider Repos einen Hinweis eintragen: «Vor Arbeitsbeginn docs/project/SYNC_KONTEXT_2026-07-16.md und PROJEKT_INVENTAR.md lesen.»
3. Nach jedem Claude-Code-Meilenstein aktualisiert Claude Code PROJEKT_INVENTAR.md. Du lädst die Datei danach hier hoch, damit Cowork denselben Stand hat.
4. Thesis-Uploads hier werden immer zuerst gegen den letzten Cowork-Stand gedifft, bevor editiert wird (Schutz vor Versions-Divergenz).
5. Inhalte aus den Repos gelangen nur über geprüfte Kennzahlen in die Thesis (Artefakte, Inventar), nie aus dem Gedächtnis.

## 4. Inventar-Auftrag für Claude Code (einmalig, danach fortschreiben)

In das Repo ba-thesis wechseln und folgenden Auftrag geben:

«Lies docs/project/SYNC_KONTEXT_2026-07-16.md. Erstelle docs/project/PROJEKT_INVENTAR.md mit dem tatsächlichen Ist-Zustand beider Projekte: (1) ba-thesis: Modul-Übersicht, Branch-Stände inkl. Zweck des Mentions-Bot-Branches, aktuelle Testzahl, Lauf-Statistik der täglichen Publikations-Kette seit 09.07. aus den publizierten JSON-Artefakten (Anzahl Läufe, Alerts gesamt, Review-Fälle nach Priorität, Gate- oder Lauf-Abbrüche), Fundort der Forward-Replay-Artefakte für die Tabelle-6-Einstufungen (insbesondere die 28 Oracle-Divergence-Fälle) oder die Feststellung, dass es keinen gibt, Stand des Pilot-Branches. (2) Prediction-Market-Terminal: Repo-Pfad, Seiten- und Feature-Liste der Website mit Stand heute, was seit Anfang Juli neu ist, welche Research-Artefakte öffentlich sind. Nur dokumentieren, nichts verändern. Kompakt, mit Dateipfaden und Zahlen.»

Das Ergebnis schliesst direkt die offenen Review-Punkte 4, 5, 7 und 9 der Thesis-Prüfung vom 16.07. auf: Lauf-Statistik für 4.5, Scanner-Fortschreibung, Stand-Angaben in Kapitel 6 und die Website-Inhalte für 4.3/4.5.

## 5. Offene Thesis-Bausteine (zur Erinnerung)

Pilot-Ankündigung in 4.2 und Ergebnis-Box (nach Pilotstart bzw. Fensterende), Lauf-Statistik in 4.5 (nach Inventar), Website-Absatz in 4.5 plus Workspace-Abgleich in 4.3 (nach Inventar), Fazit-Anleitung in Kapitel 5 (neuer Anlauf, Feedback der Studentin zum ersten Entwurf offen), Management Summary und öffentliches Summary (Formalia, gegen Abgabe).

## 6. Update 18.07.2026 (Inventar Teil B erhoben, drei Korrekturen)

Das PROJEKT_INVENTAR.md enthält jetzt beide Teile und ist die massgebliche Faktenquelle. Drei Angaben weiter oben sind damit überholt. Erstens: Der Pilot wurde direkt auf main gebaut, einen Branch pilot/feldtest-2026-07 gibt es nicht. Zweitens: `C:\Users\chole\ba-thesis` und `C:\Users\chole\Projects\multi-agent-orchestration-informational-efficiency` sind zwei Klone desselben GitHub-Repos (Pablozh123/multi-agent-orchestration-informational-efficiency). Synchronisiert wird über git push und pull, gearbeitet wird immer nur in einer Kopie. Drittens: Das Terminal-Repo liegt unter `C:\Users\chole\Projects\prediction-market-terminal`, die tägliche Kette publiziert dorthin (public/data mit neun JSON-Artefakten). Zahlen und Fundorte stehen im Inventar.

## 7. Ordnerkarte und Arbeitsregeln (Stand 07.08.2026, ersetzt die Tabelle in §1 wo abweichend)

Drei GitHub-Repositories, sechs lokale Ordner. Die Verwirrung entstand, weil
vier der sechs Ordner dasselbe Repository zeigen — in verschiedenen Rollen.

| Ordner | Ist | Rolle |
| --- | --- | --- |
| `C:\Users\chole\ba-thesis` | Klon von `multi-agent-orchestration-informational-efficiency` | **Betriebsordner.** Bots laufen NUR hier, `data\live\` liegt nur hier. Steht immer auf `main`, niemand entwickelt hier. |
| `C:\Users\chole\Projects\multi-agent-orchestration-informational-efficiency` | zweiter Klon desselben Repos | **Entwicklungsordner.** Taegliche Kette laeuft hier (liest `data\live` des Betriebsordners ueber `THESIS_LIVE_ROOT`), Commits und PRs entstehen hier. |
| `C:\Users\chole\Projects\wt-elon` | Worktree des Entwicklungsordners | **Parallel-Werkbank 1.** Eigener Branch je Feature, Rest wie Entwicklungsordner. |
| `C:\Users\chole\Projects\wt-ukraine` | Worktree des Entwicklungsordners | **Parallel-Werkbank 2.** Dito. |
| `C:\Users\chole\Projects\prediction-market-terminal` | eigenes Repo (public) | **Terminal/Website.** Die taegliche Kette publiziert JSON nach `public/data`. |
| `C:\Users\chole\Projects\prediction-alpha-bot` | eigenes Repo (public) | **Arbitrage-Scanner** (TypeScript, paper-only). Unabhaengig, kein Datenaustausch zur Laufzeit. |

Warum zwei Klone plus zwei Worktrees vom selben Repo: Der Betriebsordner darf
sich nur durch `git pull` bewegen, weil laufende Bots beim Neustart laden, was
dort liegt. Entwickelt wird deshalb woanders — und zwar parallel, ein Branch
pro Werkbank, ohne dass sich zwei Straenge gegenseitig die Dateien wechseln.

**Der eine Kreislauf, der alles synchron haelt:**

1. Feature bauen in einer Werkbank (wt-elon, wt-ukraine oder Entwicklungsordner)
   auf einem `feat/*`- oder `fix/*`-Branch.
2. Push. Die CI prueft seit 07.08. jeden Push auf `feat/**` und `fix/**`,
   nicht mehr erst den PR.
3. PR nach `main`, CI gruen, mergen. Branch danach loeschen.
4. Betriebsordner nachziehen: `hole_main.cmd` dort ausfuehren. Das macht die
   Session, die gemergt hat, selbst (Regel in CLAUDE.md); der Doppelklick
   bleibt der manuelle Knopf, die Montagsroutine das Netz. Laufende Bots
   uebernehmen den neuen Stand bei ihrem naechsten Neustart.

**Regeln, die aus Vorfaellen stammen (nicht aus Vorsicht):**

- Betriebsordner nie auf einem Feature-Branch stehen lassen. Er stand 12
  Commits zurueck auf `feat/earnings-bot`; die am 07.08. gemergte Feuerkette
  war deshalb auf GitHub scharf und im Betrieb nicht vorhanden.
- Getrackte Dateien, die pro Maschine abweichen, gibt es nicht mehr:
  `.claude/settings.local.json` ist seit 07.08. enttrackt, Testlaeufe
  schreiben seit a5d3a63 nicht mehr in die Audit-Beweisdatei. Wenn `git
  status` im Betriebsordner etwas Getracktes als geaendert zeigt, ist das ab
  jetzt ein Befund, kein Grundrauschen.
- `data\live\watchdog.json` vor jedem Ueberschreiben mit dem aktiven Satz
  vergleichen (Vorfall 07.08.: Juli-Stand eingespielt, jre_august3 und
  elon_august3 starben unbetreut).
- Fernzweige nach dem Merge loeschen. Am 07.08. wurden 19 vollstaendig
  gemergte Zweige geloescht; uebrig ist nur, was echte offene Arbeit traegt.

**Rollenverteilung der Repos fuers Vorzeigen:** `prediction-market-terminal`
(public) ist das Produkt, `prediction-alpha-bot` (public) die
Scanner-Forschung, dieses Repo (privat) traegt Bots, Messreihen und Thesis.
Die Gesamtsicht fuer Externe liegt als Einseiter im Terminal-Repo unter
`docs/research/ONE_PAGER.md`.
