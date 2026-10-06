# FLOW100 Stock Trading – Infrastruktur

Rahmenbedingungen: siehe `TRADING_PROMPT.md`.

## Setup

```bash
cd Stock_Trading
pip install -r requirements.txt
```

Die `.env` enthaelt bereits die Live- und Demo-Keys (`LIVE_API_KEY`,
`LIVE_SECRET`, `DEMO_API_KEY`, `DEMO_SECRET`). Diese Datei nicht committen
oder teilen.

## Dateien

- `ledger.py` – eigenes Buchungs-Ledger für das Experiment (FIFO,
  unabhängig vom Rest des Live-Kontos, siehe `STRATEGY.md` Abschnitt
  "Ledger"). CLI: `t212_cli.py --env <live|demo> ledger init|buy|sell|note|report`.
  Getrennte Dateien `ledger_live.csv` / `ledger_demo.csv` – nur
  `ledger_live.csv` zählt für den echten Fortschritt Richtung 100'000 CHF.
- `t212_client.py` – Trading212-API-Client (Account, Positionen, Instrumente,
  Market-/Limit-/Stop-Orders). Auth per HTTP Basic (Base64 `API_KEY:API_SECRET`).
- `trade_logger.py` – haengt jede Order/jeden Trockenlauf/jede Entscheidung als
  Zeile an `logs/trades_<Datum-UTC>.csv` an (ein CSV pro Tag).
- `t212_cli.py` – Kommandozeilen-Tool fuer den taeglichen Gebrauch.
- `auto_policy.py` – mechanische Regelschicht der Automatisierung
  (Positionsgroessen, Extended-Filter, Duplicate-Order-Guard,
  Drawdown-Alarm). Siehe STRATEGY.md, Abschnitt "Automatisierungs-Policy".
- `risk_monitor.py` – Equity-Kurve + Drawdown-Tracking
  (`equity_live.csv` / `equity_demo.csv`).
- `auto_trade.py` – automatisierter Signal->Order-Lauf (Schritte 1-5:
  Signale lesen, beurteilen, Positionsgroesse festlegen, Trockenlauf,
  Order platzieren). Fuer den woechentlichen Lauf via Windows-
  Aufgabenplanung, siehe unten.
- `book_fills.py` – prueft offene, von `auto_trade.py` platzierte Orders
  auf Fill und bucht sie automatisch in den Ledger (Schritte 6-7). Fuer
  den taeglichen Lauf via Windows-Aufgabenplanung, siehe unten.
- `run_auto_trade.bat` / `run_book_fills.bat` – Wrapper-Skripte fuer die
  Windows-Aufgabenplanung (setzen das Arbeitsverzeichnis, schreiben nach
  `logs/auto_trade_run.log` bzw. `logs/book_fills_run.log`).

## Nutzung

```bash
# Standard-Umgebung ist "demo" – "live" muss explizit gesetzt werden
python t212_cli.py --env demo status
python t212_cli.py --env demo positions
python t212_cli.py --env live find "S&P 500"

# Kauf/Verkauf: ohne --confirm nur Trockenlauf (wird trotzdem geloggt)
python t212_cli.py --env live buy AAPL_US_EQ 1 --rationale "Begruendung hier"
python t212_cli.py --env live buy AAPL_US_EQ 1 --rationale "Begruendung hier" --confirm

# Reine Entscheidungsnotiz ohne Trade
python t212_cli.py --env live log-decision --rationale "Kein Trade heute, Markt zu volatil"
```

## Eingebaute Sicherheitsregeln

- **Trockenlauf per Default**: Kauf-/Verkaufsbefehle senden nur dann eine
  echte Order an Trading212, wenn `--confirm` explizit gesetzt ist.
- **Kein Shorting**: Vor jedem Verkauf wird die aktuell gehaltene Menge per
  API geprueft; ein Verkauf ueber den Bestand hinaus wird abgelehnt und
  geloggt statt ausgefuehrt.
- **Nur Market-/Limit-/Stop-Orders auf Aktien/ETFs** – es gibt in diesem Setup
  keine Funktionen fuer Optionen, Futures, CFDs oder Margin-Handel.
- **Vollstaendiges Logging**: jede Order, jeder Trockenlauf, jede Ablehnung
  und jede reine Entscheidungsnotiz landet in `logs/trades_<Datum>.csv`.

## Bekannte Einschraenkungen (Stand: Trading212-API-Doku, Beta, Sept. 2026)

- Rate Limits u.a.: Account-Summary 1 Req/5s, Positionen 1 Req/1s,
  Market-Order 50 Req/min, Limit-/Stop-Order 1 Req/2s, Instrumente 1 Req/50s.
- Order-Endpunkte sind laut Doku **nicht idempotent** – keine automatischen
  Retries auf Order-Endpunkten einbauen, ohne vorher zu pruefen, ob die Order
  schon existiert (`get_open_orders` / `get_order`).
- Orders werden nur in der Kontowaehrung ausgefuehrt, Multi-Currency-Konten
  werden nicht unterstuetzt.
- Diese Umgebung (Claude-Sandbox) hat keinen Zugriff auf `live.trading212.com`
  / `demo.trading212.com` – Client und CLI sind ungetestet gegen die echte
  API. Vor dem ersten `--confirm`-Trade unbedingt zuerst mit `--env demo`
  gegen das Demokonto testen.

## Automatisierung einrichten (Windows-Aufgabenplanung)

Hintergrund: Eine Automatisierung ueber einen Claude-Scheduled-Task ist
nicht moeglich (die Claude-Sandbox hat keinen Internetzugang zu
Trading212/Yahoo Finance, siehe STRATEGY.md "Automatisierungs-Policy").
Die Automatisierung laeuft deshalb direkt auf diesem Rechner ueber die
native Windows-Aufgabenplanung -- zwei getrennte, je EINMAL taeglich
laufende Aufgaben (Andys Entscheidung 23.09.2026: eine Abfrage pro Tag
reicht, siehe Begruendung unten):

```powershell
# Taeglich, kurz vor Marktschluss-Auswertung: offene Orders pruefen &
# Ledger buchen -- LAEUFT ZUERST, damit auto_trade.py mit einem
# aktuellen Ledger-Stand rechnet (Cash/offene Positionen).
schtasks /create /tn "FLOW100_BookFills_Daily" ^
  /tr "C:\Users\Andy\Documents\FLOW100\01_Financing\Stock_Trading\run_book_fills.bat" ^
  /sc daily /st 22:00

# Taeglich, nach US-Marktschluss: Signale -> ggf. neue Order. Nutzt den
# bereits GESETZTEN Tagesschlusskurs (kein Intraday-Rauschen).
schtasks /create /tn "FLOW100_AutoTrade_Daily" ^
  /tr "C:\Users\Andy\Documents\FLOW100\01_Financing\Stock_Trading\run_auto_trade.bat" ^
  /sc daily /st 22:15
```

Warum nur 1x/Tag fuer beide, statt mehrfach:
- **`auto_trade.py` (neue Order):** Die Entry-/Exit-Regeln (SMA50/SMA200/
  RSI, siehe `signals.py`) sind auf taeglichen Schlusskursen berechnet.
  Mehrfach am Tag wuerde zwangslaeufig einen unfertigen Intraday-Kurs als
  "Schlusskurs" verwenden und das Risiko von Fehlkaeufen durch kurzfristige
  Kursausschlaege (Whipsaws) erhoehen -- deshalb bewusst nur einmal, nach
  Marktschluss.
- **`book_fills.py` (Fill-Pruefung/Ledger-Buchung):** Platziert keine
  Orders, waere also technisch auch mehrfach taeglich unkritisch gewesen --
  Andys Entscheidung: eine Abfrage pro Tag reicht, haelt es einfach.

Hinweise:
- Zeiten sind lokale Zeit (Schweiz) und ein Kompromiss ueber Sommer-/
  Winterzeit-Verschiebungen der US-Marktzeiten hinweg -- unkritisch, da
  Market-Orders ausserhalb der Handelszeiten einfach bis zur naechsten
  Oeffnung als `NEW` warten (siehe Erfahrung mit dem ersten AAPL-Trade).
- Vor dem ersten scharfen Lauf beide Skripte manuell im eigenen Terminal
  testen (siehe "Manuelle Tests" unten) -- NICHT ueber die
  Claude-Geraetebruecke, die hat keinen Internetzugang zu diesen APIs.
- Pruefen/Anpassen: `schtasks /query /tn "FLOW100_AutoTrade_Daily" /v /fo LIST`
- Pausieren (schnellste Notbremse, unabhaengig von Claude):
  `schtasks /change /tn "FLOW100_AutoTrade_Daily" /disable`
  `schtasks /change /tn "FLOW100_BookFills_Daily" /disable`
- Loeschen: `schtasks /delete /tn "FLOW100_AutoTrade_Daily" /f` (analog fuer
  `FLOW100_BookFills_Daily`)

### Manuelle Tests (im eigenen PowerShell-Terminal, nicht in der Claude-Sandbox)

```powershell
# Trockenlauf -- sendet nichts an Trading212, zeigt nur was passieren wuerde
python auto_trade.py --env live

# Erst wenn der Trockenlauf plausibel aussieht: echter automatischer Lauf
python auto_trade.py --env live --execute

# Offene Orders pruefen & bei Fill in den Ledger buchen
python book_fills.py --env live
```

## Naechste sinnvolle Schritte

- Erste Tests mit `--env demo` fahren, bis Account-Summary/Positionen/eine
  Test-Order sauber funktionieren.
- Auswahlkriterien fuer Titel (liquide Aktien/ETFs, Spreads) und
  Positionsgroessen/Risikomanagement als Regelwerk ergaenzen.
