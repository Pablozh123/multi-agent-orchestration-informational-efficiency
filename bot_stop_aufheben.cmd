@echo off
rem Hebt den Notaus wieder auf (loescht data\live\STOP).
cd /d %~dp0
if exist data\live\STOP del data\live\STOP
echo STOP entfernt.
pause
