@echo off
REM Wrapper fuer den Windows-Scheduled-Task (siehe watchdog.py).
REM Setzt das Arbeitsverzeichnis und ruft einen Einzeldurchlauf auf.
cd /d "%~dp0\..\.."
".venv\Scripts\python.exe" -m operations.pipeline.watchdog
