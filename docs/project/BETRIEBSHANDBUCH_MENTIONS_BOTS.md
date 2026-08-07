# Betriebshandbuch Mentions-Bots

Kurzreferenz für den laufenden Betrieb: Wo liegt was, wer darf was ändern,
und wie setzt man eine neue Wochen-Wette auf. Stand 23.07.2026.

## 1. Das mentale Modell in vier Sätzen

1. **Es gibt genau einen echten Arbeitsordner:** `C:\Users\chole\ba-thesis`.
   Nur von dort laufen die Bots. Alles andere sind temporäre Kopien.
2. **Dieser Ordner steht immer auf `main`.** `main` ist der scharfe,
   getestete Stand — das, was die Bots wirklich ausführen.
3. **Änderungen entstehen nie direkt auf `main`,** sondern auf einem
   Branch (= Entwurf) in einer temporären Kopie, werden per Pull Request
   geprüft (CI muss grün sein) und erst dann nach `main` gemergt.
4. **Nach jedem Merge muss der Arbeitsordner `git pull` machen** — sonst
   laufen die Bots weiter auf dem alten Stand.

## 2. Die Ordner, die dir begegnen

| Pfad | Was es ist | Anfassen? |
| --- | --- | --- |
| `C:\Users\chole\ba-thesis` | Der echte Arbeitsordner. Bots laufen von hier, Daten unter `data\live\` liegen hier. | Ja, das ist dein Projekt |
| `...\ba-thesis\.claude\worktrees\<name>` | Temporäre Arbeitskopie einer parallelen Claude-Session (eigener Branch). Wird nach dem Merge gelöscht. | Nein, ignorieren |
| `%TEMP%\claude\...\scratchpad\wt-*` | Temporäre Arbeitskopie dieser Session. Wird nach dem Merge gelöscht. | Nein, ignorieren |

Eine „Arbeitskopie" (Worktree) ist ein zweiter Ordner mit demselben
Projekt in einem anderen Bearbeitungsstand. Sie existiert nur, damit an
einer Änderung gearbeitet werden kann, **ohne den laufenden Bots den
Boden unter den Füßen wegzuziehen**. Das ist der einzige Grund dafür.

## 3. Warum das so umständlich wirkt

Die Bots laden ihre Konfiguration **beim Start aus dem Arbeitsordner**.
Würde man dort einfach Dateien ändern oder den Branch wechseln, während
ein Bot läuft, könnte er beim nächsten Neustart eine halbfertige Version
laden — im schlimmsten Fall mit echtem Geld. Deshalb: Entwürfe immer in
einer Kopie, `main` bleibt jederzeit lauffähig.

## 4. Neue Wochen-Wette aufsetzen: der Ablauf

Immer dieselben sechs Schritte, egal ob All-In, Trump oder Lemonade:

1. Event-Regeln auf Polymarket lesen (was zählt, was nicht, Zeitfenster).
2. Neues Profil in `operations/pipeline/config.py` anlegen (Kopie der
   Vorwoche mit neuer `event_id`, neuem `live_dir`, neuer Periode).
3. Test dazu, komplette Testsuite und Lint laufen lassen.
4. Pull Request, CI abwarten, mergen.
5. Im Arbeitsordner `git pull`.
6. Eintrag in `data\live\watchdog.json` — der Watchdog startet den Bot
   dann binnen fünf Minuten selbst. (Alternativ das Startskript
   `data\live\starte_bots.ps1` — aber **nie beides gleichzeitig**.)

Schritte 1–5 macht Claude, Schritt 6 auch — du musst nur sagen, welches
Event.

## 5. Die häufigste Verwechslungsgefahr: ähnliche Märkte

Polymarket listet oft mehrere Märkte, die fast gleich heißen, aber
verschiedene Quellen bewerten. Beispiele:

- **„What will Trump POST this week"** (Serie 11341) wertet geschriebene
  Truth-Social-Posts → unser Textbot `trump_bot.py`.
- **„What will Trump SAY this week"** (Serie 11277) wertet nur
  **Gesprochenes**; geschriebene Posts zählen ausdrücklich nicht → dafür
  gibt es aktuell keinen Bot.
- MrBeast Hauptkanal vs. MrBeast Gaming: zwei getrennte Kanäle, zwei
  Events, zwei Profile.

Deshalb wird vor jeder Armierung der Regeltext gelesen und die
Event-ID im Profil festgeschrieben — nicht der Name.

## 6. Sessions: wann eine neue, wann diese?

Es dürfen mehrere Claude-Sessions parallel am Projekt arbeiten, aber:

- **Pro Aufgabe eine Session.** „All-In für morgen aufsetzen" kann in
  dieser Session laufen (sie kennt den Kontext) oder in einer neuen —
  beides ist in Ordnung, solange nicht zwei Sessions **dieselbe** Datei
  gleichzeitig ändern.
- **Sicherheitsnetz:** Jede Session arbeitet in ihrer eigenen Kopie und
  mergt über einen Pull Request. Konflikte fallen dann beim Merge auf,
  nicht im laufenden Betrieb.
- **Faustregel:** Läuft schon eine Session an einer Sache, gib
  Folgeaufträge dort. Für etwas Neues ist eine frische Session sauberer.

## 7. Betriebsbefehle (alles im Arbeitsordner)

```
git log -1 --oneline          # auf welchem Stand bin ich?
git status --short            # habe ich uncommittete Änderungen?
git worktree list             # welche Arbeitskopien existieren gerade?
gh pr list                    # welche Änderungen warten auf Merge?
```

Laufende Bots prüfen (Windows; `ps` aus Git-Bash lügt hier):

```
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'operations\.pipeline' -and
                 $_.ExecutablePath -notmatch '\.venv' }
```

**Not-Aus für alle Bots:** Datei `data\live\STOP` anlegen (beliebiger
Inhalt). Alle Bots beenden sich binnen Sekunden. Zum Wiederanlaufen die
Datei löschen und `data\live\starte_bots.ps1` ausführen.

## 8. Merksätze

- `main` = scharf. Branch = Entwurf. Merge = scharf schalten.
- Nach dem Merge immer `git pull` im Arbeitsordner.
- Watchdog **oder** Startskript, nie beides zeitgleich.
- Ähnliche Marktnamen sind verschiedene Märkte — Regeltext entscheidet.
- Bei Unsicherheit: `git log -1 --oneline` und `gh pr list` zeigen in
  zwei Zeilen, wo das Projekt steht.
