@echo off
rem Fernstart Graham-Tribute-Lauf (LIVE): Stream aufloesen, Bot starten.
rem Zeremonie 28.07. 14:00 ET = 20:00 CEST; Trumps Slot liegt darin.
rem Nur im Live-Klon (ba-thesis). Abbruch: bot_stop.cmd.
cd /d %~dp0
set BOT_PROFIL=trump_graham_july28
if not exist data\live\trump_graham_july28 mkdir data\live\trump_graham_july28
call .venv\Scripts\activate.bat
python -m operations.pipeline.trump_michigan_start --live --minuten 240 >> data\live\trump_graham_july28\start_log.txt 2>&1
