@echo off
rem Der eine Handgriff im Betriebsordner: den getesteten Stand holen.
rem Doppelklick nach jedem Merge. Bricht ab, statt etwas zu reparieren:
rem jede Abweichung, die er meldet, ist ein Befund (Handbuch Abschnitt 9).
setlocal
cd /d "%~dp0"

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%b
if not "%BRANCH%"=="main" (
    echo FEHLER: dieser Ordner steht auf "%BRANCH%", nicht auf main.
    echo Nicht selbst wechseln, solange Bots laufen - Handbuch Abschnitt 9.
    exit /b 1
)

for /f "delims=" %%s in ('git status --porcelain 2^>nul ^| findstr /v "^??"') do (
    echo FEHLER: getrackte Dateien sind lokal veraendert:
    git status --short | findstr /v "^??"
    echo Das ist seit 07.08. ein Befund, kein Grundrauschen. Erst klaeren.
    exit /b 1
)

git pull --ff-only origin main
if errorlevel 1 (
    echo FEHLER: Pull war kein Fast-Forward. Nichts veraendert.
    exit /b 1
)

echo.
echo Stand jetzt:
git log -1 --oneline

if exist "data\live\watchdog.json" (
    echo.
    echo Wachkontrolle:
    ".venv\Scripts\python.exe" -m operations.pipeline.wachkontrolle --live-root data/live
)
endlocal
