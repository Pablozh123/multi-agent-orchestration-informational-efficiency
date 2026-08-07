@echo off
rem Schnelles Ohr: Graham-Stream in ffplay (Details in hoer_graham.py).
cd /d %~dp0
.venv\Scripts\python.exe -u hoer_graham.py
pause
