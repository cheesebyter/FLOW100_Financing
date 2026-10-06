@echo off
REM Woechentlicher Auto-Trade-Lauf (Schritte 1-5, siehe STRATEGY.md
REM "Automatisierungs-Policy"). Wird per Windows-Aufgabenplanung
REM aufgerufen, siehe README.md.
cd /d "%~dp0"
python auto_trade.py --env live --execute >> logs\auto_trade_run.log 2>&1
