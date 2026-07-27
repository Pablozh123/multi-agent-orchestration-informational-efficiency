@echo off
rem Graham-Tribute: Marker AUS (Trump ist fertig / anderer Redner).
rem Wirkt NUR im --fenster-modus (dort pausiert er Zaehlung und
rem Kaeufe wieder); im Standard-Modus ist der Marker ein Latch.
cd /d %~dp0
if exist data\live\trump_graham_july28\SPRECHER_AKTIV del data\live\trump_graham_july28\SPRECHER_AKTIV
echo Marker AUS.
pause
