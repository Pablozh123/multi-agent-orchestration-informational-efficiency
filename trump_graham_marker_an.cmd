@echo off
rem Graham-Tribute: Marker AN (Trump beginnt zu sprechen).
rem Standard-Modus: gibt den Kaufpfad frei (Latch).
rem Fenster-Modus: oeffnet das Zaehl- und Kauf-Fenster.
cd /d %~dp0
if not exist data\live\trump_graham_july28 mkdir data\live\trump_graham_july28
type nul > data\live\trump_graham_july28\SPRECHER_AKTIV
echo Marker AN: data\live\trump_graham_july28\SPRECHER_AKTIV
pause
