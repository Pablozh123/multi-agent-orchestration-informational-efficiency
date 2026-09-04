@echo off
REM Wrapper fuer den Windows-Task \MarketIntelDailyReview (Muster: watchdog_task.cmd).
REM   %1 = publish-dir (Website public\data)
REM   %2 = live-root   (Live-Repo data\live, z.B. C:\Users\chole\ba-thesis\data\live)
REM        Geht an Tageslauf UND Dashboard: die Rohdaten der Laeufe liegen nur
REM        dort, data\live dieser Arbeitskopie ist gitignored und leer.
REM Ablauf: Clone aktualisieren -> Wachkontrolle -> Tageslauf -> Daten-Artefakte
REM         committen+pushen.
REM Lehre 16.7.: Der Task lief auf einem 10 Commits alten Clone, und der
REM manuelle Artefakt-Commit im veralteten Stand erzeugte Divergenz (Rebase).
setlocal
cd /d "%~dp0\..\.."
if not exist logs mkdir logs
set LOG=logs\daily_review_task.log
REM Absoluter Log-Pfad fuer Schritte, die per pushd in einem anderen
REM Arbeitsverzeichnis laufen (Website-Commit-Block unten).
set LOGABS=%CD%\%LOG%
echo [%date% %time%] ===== Tageslauf-Start ===== >> %LOG%

REM Git-Schritte nur auf main: steht der Clone auf einem Feature-Branch
REM (parallele Session), laeuft die Pipeline trotzdem, aber ohne Pull/Commit.
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%b
if /i not "%BRANCH%"=="main" (
  echo [%date% %time%] WARN: Clone steht auf '%BRANCH%' statt main - Pull/Auto-Commit uebersprungen >> %LOG%
  goto :pipeline
)

REM Vor dem Lauf auf origin/main aktualisieren; bei Konflikt sauber
REM abbrechen und auf dem alten Stand weiterlaufen (Lauf geht vor).
git pull --rebase --autostash origin main >> %LOG% 2>&1
if errorlevel 1 (
  git rebase --abort >> %LOG% 2>&1
  echo [%date% %time%] WARN: pull/rebase fehlgeschlagen - Lauf auf altem Stand >> %LOG%
)

:pipeline
REM Ohne %2 (anderer Rechner, anderes Checkout) bleibt --live-root weg; der Lauf
REM faellt dann auf data\live und danach auf data\live_curated zurueck.
set LIVEARG=
if not "%~2"=="" set LIVEARG=--live-root %2

REM Zweiter, unabhaengiger Ausloeser der Wachkontrolle (anderer Task, anderer
REM Clone als der Watchdog): meldet Messposten, die aus watchdog.json
REM verschwunden sind. Der Watchdog prueft dasselbe alle 5 Min, teilt aber das
REM Schicksal seines eigenen Tasks - faellt der aus, meldet nur noch dieser
REM Lauf. Laeuft direkt nach dem Pull, damit die versionierte Sollbesetzung
REM data/wachposten.json aktuell ist. Ohne %2 uebersprungen: dieser Clone hat
REM kein eigenes data\live, die Kontrolle wuerde nur Phantom-Befunde melden.
if "%~2"=="" goto :tageslauf
python -m operations.pipeline.wachkontrolle --live-root %2 >> %LOG% 2>&1
if errorlevel 1 echo [%date% %time%] ALARM: Wachkontrolle - Befunde, siehe oben (1=kritisch, 2=Warnung, 3=Sollbesetzung unlesbar) >> %LOG%

:tageslauf
python -m operations.pipeline.daily_review_run --collect --publish-dir %1 %LIVEARG% >> %LOG% 2>&1
if errorlevel 1 echo [%date% %time%] WARN: daily_review_run Exit-Code %errorlevel% >> %LOG%

python -m operations.pipeline.run_dashboard --live-root %2 --fetch-resolutions --fetch-tape --publish-dir %1 >> %LOG% 2>&1
if errorlevel 1 echo [%date% %time%] WARN: run_dashboard Exit-Code %errorlevel% >> %LOG%

if /i not "%BRANCH%"=="main" goto :website

REM Nur Pipeline-Artefakte unter data/ committen - nie Code-WIP anderer
REM Sessions (Parallel-Session-Regel in CLAUDE.md). Push mit einmaligem
REM Rebase-Retry, falls origin sich seit dem Pull bewegt hat.
git add -- data >> %LOG% 2>&1
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "chore(data): daily pipeline artifacts (auto)" >> %LOG% 2>&1
  git push origin main >> %LOG% 2>&1
  if errorlevel 1 (
    git pull --rebase --autostash origin main >> %LOG% 2>&1
    git push origin main >> %LOG% 2>&1
  )
)

:website
REM Website-Repo (prediction-market-terminal): %1 = <repo>\public\data. Die
REM dorthin publizierten Artefakte wurden bisher nie automatisch committet
REM (Befund 04.09.: neun Dateien seit 01.09. nur lokal). Die oeffentliche
REM Seite wird aus main ausgeliefert, also muessen sie nach origin/main.
REM Das Checkout dort steht oft auf einem Feature-Branch mit Code-WIP anderer
REM Sessions, deshalb kein checkout, kein stash, kein pull: Der Commit wird
REM ueber einen temporaeren Index (GIT_INDEX_FILE) direkt auf origin/main
REM gebaut und als <commit>:main gepusht. Arbeitsbaum und lokaler Branch
REM bleiben unberuehrt; nur public\data geht in den Commit.
if "%~1"=="" goto :ende
pushd "%~1\..\.." 2>nul || goto :ende
if not exist .git goto :website_ende
git fetch origin main >> "%LOGABS%" 2>&1
if errorlevel 1 (
  echo [%date% %time%] WARN: Website-Repo fetch fehlgeschlagen - Daten-Commit uebersprungen >> "%LOGABS%"
  goto :website_ende
)
set GIT_INDEX_FILE=%CD%\.git\daily-data-index
if exist "%GIT_INDEX_FILE%" del "%GIT_INDEX_FILE%"
git read-tree origin/main >> "%LOGABS%" 2>&1
git add -- public/data >> "%LOGABS%" 2>&1
git diff-index --cached --quiet origin/main
if not errorlevel 1 (
  echo [%date% %time%] Website-Daten unveraendert gegen origin/main >> "%LOGABS%"
  goto :website_index_ende
)
for /f "delims=" %%t in ('git write-tree') do set WEBTREE=%%t
if "%WEBTREE%"=="" goto :website_index_ende
for /f "delims=" %%c in ('git commit-tree %WEBTREE% -p origin/main -m "chore(data): daily pipeline artifacts (auto)"') do set WEBCOMMIT=%%c
if "%WEBCOMMIT%"=="" goto :website_index_ende
git push origin %WEBCOMMIT%:main >> "%LOGABS%" 2>&1
if errorlevel 1 (
  echo [%date% %time%] WARN: Website-Daten-Push fehlgeschlagen - naechster Lauf versucht es erneut >> "%LOGABS%"
) else (
  echo [%date% %time%] Website-Daten committet und gepusht: %WEBCOMMIT% >> "%LOGABS%"
)
:website_index_ende
set GIT_INDEX_FILE=
if exist ".git\daily-data-index" del ".git\daily-data-index"
set WEBTREE=
set WEBCOMMIT=
:website_ende
popd

:ende
echo [%date% %time%] ===== Tageslauf-Ende ===== >> %LOG%
endlocal
