@echo off
rem Fernstart Trump-Michigan-Lauf (LIVE): Stream-URL aufloesen, Bot starten.
rem Nur im Live-Klon (ba-thesis, .venv mit faster_whisper) sinnvoll.
rem Doppelklick ODER Scheduled Task; Abbruch: bot_stop.cmd.
cd /d %~dp0
set BOT_PROFIL=trump_michigan_july27
if not exist data\live\trump_michigan_july27 mkdir data\live\trump_michigan_july27
call .venv\Scripts\activate.bat
python -m operations.pipeline.trump_michigan_start --live --minuten 165 >> data\live\trump_michigan_july27\start_log.txt 2>&1
