@echo off
rem Hand-Marker: Kaufpfad freigeben, sobald Trump am Pult ist.
rem (Noetig nur, wenn der Auto-Marker nicht greifen sollte.)
cd /d %~dp0
if not exist data\live\trump_michigan_july27 mkdir data\live\trump_michigan_july27
type nul > data\live\trump_michigan_july27\SPRECHER_AKTIV
echo Marker gesetzt: data\live\trump_michigan_july27\SPRECHER_AKTIV
pause
