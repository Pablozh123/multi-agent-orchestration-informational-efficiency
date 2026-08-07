@echo off
rem Live-Sichtfenster: was der Bot hoert/zaehlt/kauft (Strg+C beendet).
cd /d %~dp0
.venv\Scripts\python.exe -u sichtfenster_graham.py
pause
