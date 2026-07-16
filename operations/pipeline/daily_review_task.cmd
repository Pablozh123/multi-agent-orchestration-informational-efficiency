@echo off
REM Wrapper fuer den Windows-Task \MarketIntelDailyReview (Muster: watchdog_task.cmd).
REM   %1 = publish-dir (Website public\data)
REM   %2 = live-root   (Live-Repo data\live, z.B. C:\Users\chole\ba-thesis\data\live)
REM Ablauf: Clone aktualisieren -> Tageslauf -> Daten-Artefakte committen+pushen.
REM Lehre 16.7.: Der Task lief auf einem 10 Commits alten Clone, und der
REM manuelle Artefakt-Commit im veralteten Stand erzeugte Divergenz (Rebase).
setlocal
cd /d "%~dp0\..\.."
if not exist logs mkdir logs
set LOG=logs\daily_review_task.log
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
python -m operations.pipeline.daily_review_run --collect --publish-dir %1 >> %LOG% 2>&1
if errorlevel 1 echo [%date% %time%] WARN: daily_review_run Exit-Code %errorlevel% >> %LOG%

python -m operations.pipeline.run_dashboard --live-root %2 --fetch-resolutions --fetch-tape --publish-dir %1 >> %LOG% 2>&1
if errorlevel 1 echo [%date% %time%] WARN: run_dashboard Exit-Code %errorlevel% >> %LOG%

if /i not "%BRANCH%"=="main" goto :ende

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

:ende
echo [%date% %time%] ===== Tageslauf-Ende ===== >> %LOG%
endlocal
