@echo off
cd /d "%~dp0"
dotnet run --project DataBridge -- samples output
if errorlevel 1 goto failed
start "" "output\report.html"
exit /b 0
:failed
echo Die Demo konnte nicht ausgefuehrt werden. Bitte Fehlermeldung pruefen.
pause
exit /b 1
