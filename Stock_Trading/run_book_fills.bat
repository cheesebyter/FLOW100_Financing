@echo off
REM Taeglicher Fill-Check + Ledger-Buchung (Schritte 6-7, siehe
REM STRATEGY.md "Automatisierungs-Policy"). Wird per
REM Windows-Aufgabenplanung aufgerufen, siehe README.md.
cd /d "%~dp0"
python book_fills.py --env live >> logs\book_fills_run.log 2>&1
