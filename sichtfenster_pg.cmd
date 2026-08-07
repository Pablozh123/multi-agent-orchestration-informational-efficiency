@echo off
rem Live-Sichtfenster P&G: was der Bot hoert/zaehlt/kauft (Strg+C beendet).
cd /d %~dp0
.venv\Scripts\python.exe -u sichtfenster_pg.py
pause
