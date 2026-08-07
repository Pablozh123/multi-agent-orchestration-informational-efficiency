@echo off
rem Notaus fuer ALLE Bots dieses Repos: legt data\live\STOP an.
rem Der earnings_bot beendet Chunk-Schleife und Nachlauf, faehrt aber
rem den Endcheck noch sauber. WICHTIG: STOP nach dem Lauf wieder
rem loeschen (bot_stop_aufheben.cmd), sonst startet kein Bot mehr.
cd /d %~dp0
type nul > data\live\STOP
echo STOP gesetzt: data\live\STOP
pause
