# Strategie & Risikomanagement

Rahmenbedingungen: siehe `TRADING_PROMPT.md`. Infrastruktur: siehe `README.md`.
Entscheidung (gemeinsam getroffen): **reines Trading-Experiment mit hohem
Risiko**, **regelbasierte** Entry-/Exit-Logik (siehe unten, implementiert in
`signals.py`).

## Realitaetscheck (weiterhin gueltig -- bewusst in Kauf genommen)

Fakt: 250 USD Startkapital, Ziel 100'000 CHF, kein Hebel, keine
Optionen/Futures/Shorts, nur Aktien/ETFs -> Faktor ~400x.

| Angenommene CAGR | Jahre bis 100k CHF |
|---|---:|
| 20% (fuer Privatanleger ueber Jahre schon sehr gut) | ~33 Jahre |
| 50% (aggressiv, langfristig kaum durchhaltbar) | ~15 Jahre |
| 100% (jaehrliche Verdopplung) | ~9 Jahre |

Einschaetzung: Mit der jetzt gewaehlten Ausrichtung ("hohes Risiko",
konzentrierte Positionen statt breiter Diversifikation) wird bewusst
versucht, naeher an die oberen CAGR-Werte heranzukommen. Das erhoeht die
Chance auf eine schnellere Annaeherung an das Ziel, aber genauso das Risiko
eines Totalverlusts des Kapitals einzelner Positionen oder des gesamten
Kontos -- Konzentration auf 1-2 Titel bedeutet, dass ein einzelner starker
Kursrueckgang (z.B. -30% nach schlechten Quartalszahlen) das Konto deutlich
staerker trifft als bei Diversifikation. Das ist kein Fehler im Setup,
sondern die direkte, gewollte Konsequenz der Entscheidung fuer "hohes
Risiko" -- wird hier nur explizit festgehalten, damit sie bewusst bleibt.

## Handelsuniversum

Liquide US-Large-Caps mit hoher Beta/Volatilitaet (liquide + enge Spreads,
aber bewusst nicht "defensiv"): TSLA, AAPL, AMD, AMZN, GOOGL, AVGO, NFLX,
CRM. Liste ist in `signals.py::UNIVERSE` konfigurierbar (T212-Ticker ->
Yahoo-Finance-Symbol-Mapping).

**Bereinigt wegen Ueberschneidung mit privaten Bestaenden (Entscheidung
09.09.2026):** Urspruenglich enthielt das Universum NVDA, MSFT und META --
alle drei ueberschneiden sich mit bereits bestehenden privaten Positionen
auf dem Live-Konto (NVDA seit Juli 2025, MSFT seit Juli 2025, META
aktuell). Auf Andys Entscheidung hin wurden sie durch AVGO, NFLX und CRM
ersetzt (keine Ueberschneidung mit dem vollstaendigen `positions`-Abzug vom
09.09.2026). Damit ist die Trennung zwischen Experiment und Privatdepot
schon durch die Titelauswahl eindeutig -- der Ledger-Schutz (siehe unten)
bleibt trotzdem als zweite Sicherheitsebene bestehen, z.B. falls das
Universum spaeter wieder erweitert wird.

## Entry-/Exit-Regeln (regelbasiert, implementiert in `signals.py`)

**BUY**, wenn alle drei Bedingungen gleichzeitig gelten:
1. Aufwaertstrend: Schlusskurs > SMA50 > SMA200
2. Momentum-Breakout: Schlusskurs erreicht/uebertrifft das Hoch der
   vorherigen 20 Handelstage
3. RSI(14) zwischen 50 und 80 (Momentum vorhanden, aber nicht extrem
   ueberkauft)

**SELL** (Position schliessen), wenn:
- Schlusskurs faellt unter SMA50 (Trendbruch), ODER
- Stop-Loss erreicht: -12% vom Einstiegspreis, ODER
- Trailing-Stop erreicht: -10% vom hoechsten Kurs seit Einstieg

Sonst **HOLD**.

Signale werden woechentlich berechnet (`python t212_cli.py --env <live|demo>
signals`), jedes Signal wird automatisch als Entscheidungszeile geloggt.
Die tatsaechliche Order wird **nie automatisch ausgeloest** -- `signals`
gibt nur eine Empfehlung inkl. fertigem CLI-Befehl aus; ausgefuehrt wird nur
manuell per `buy`/`sell` mit `--confirm` (siehe README.md). Trennung von
Signal und Ausfuehrung ist bewusst so gebaut, auch bei "hohem Risiko".

## Positionsgroessen (hohes Risiko / konzentriert)

- Max. 3 gleichzeitig offene Positionen (seit 07.10.2026; vorher 2)
- Je Position bis zu 40-50% des Portfoliowerts
- Cash-Reserve: mind. 10-15% (Transaktionen, Nachkaeufe)
- Bewusster Trade-off: weniger Diversifikation als ein defensives Depot,
  dafuer groesserer Hebel auf einzelne Trendbewegungen

## Risikomanagement

- Stop-Loss je Position: -12% vom Einstiegspreis
- Trailing-Stop: -10% vom hoechsten Kurs seit Einstieg
- Max.-Drawdown-Trigger (Gesamtkonto): bei -25% seit letztem Hoch ->
  Handelspause + Strategie-Review (nicht automatisch, manuell zu pruefen)
- Kein Hebel = maximaler Verlust ist ohnehin auf den Kapitaleinsatz begrenzt,
  aber bei nur 1-2 Positionen mit je 40-50% Depotanteil kann ein einzelner
  Stop-Loss-Treffer trotzdem ~5-6% des Gesamtkontos kosten

## Reporting

Woechentliches Review (Kontostand, offene Positionen, ausgeloeste Signale,
getroffene Entscheidungen), Format angelehnt an `../PIPELINE.md`.

## Ledger (eigene Buchhaltung fuer das Experiment)

Wichtiger Kontext (Stand 09.09.2026): Das Live-Konto (ID 3852903) enthaelt
neben diesem Experiment noch anderes Kapital -- Gesamtwert 797.55 CHF, davon
~480 CHF bereits in Positionen, dazu ein historisch realisierter Verlust von
-78.70 CHF aus fruehrerer, von diesem Projekt unabhaengiger Aktivitaet.
Trading212 kennt keine echte Geld-Segregation innerhalb eines Kontos. Daher
fuehrt `ledger.py` (CLI: `t212_cli.py ledger ...`) eine EIGENE, rein
buchhalterische Nachverfolgung: Startkapital, jeder Trade dieses
Experiments, FIFO-Realisierung von Gewinn/Verlust, Fortschritt Richtung
100'000 CHF -- unabhaengig vom Rest des Kontos.

Andys Entscheidung (09.09.2026): Aktuell wird nur ein Teil des Kontos ("die
250 USD") diesem Experiment zugerechnet. "Das ganze Konto wird in Zukunft,
wenn es gut laeuft, benutzt." Ausserdem: "Der Account ist kein 'echtes'
Investment, sondern meine Moeglichkeit zu experimentieren" -- das aendert
nichts an der Kapitalerhaltungslogik der Regeln, aber es ordnet ein, wie
das Risiko (siehe Realitaetscheck oben) bewusst eingegangen wird.

**Korrektur (14.09.2026):** Es gibt GETRENNTE Ledger-Dateien fuer Demo und
Live (`ledger_demo.csv` / `ledger_live.csv`, gesteuert ueber den globalen
`--env`-Schalter). Der erste NVDA-Testtrade war faelschlich in einer
gemeinsamen `ledger.csv` gelandet -- das haette simulierte Demo-Performance
mit echter Live-Performance vermischt. Der Testtrade wurde nach
`ledger_demo.csv` migriert; nur `ledger_live.csv` zaehlt fuer den
tatsaechlichen Fortschritt Richtung 100'000 CHF.

Nutzung:

```bash
# Einmalig pro Umgebung: Startkapital erfassen (FX-Kurs manuell nachschauen, z.B. in der T212-App)
python t212_cli.py --env live ledger init --fx-usd-chf 0.81

# Nach jedem bestaetigten Fill (Preis aus 'positions'/'status' ablesen)
python t212_cli.py --env live ledger buy AAPL_US_EQ 0.2 --price 269.00 --rationale "Signal BUY" --order-id 12345
python t212_cli.py --env live ledger sell AAPL_US_EQ 0.2 --price 280.00 --rationale "Trendbruch"

# Freitext-Notizen (z.B. Entscheidung zur Kapitalerhoehung)
python t212_cli.py --env live ledger note "Entschieden: Experiment auf ganzes Konto ausweiten"

# Stand pruefen (immer mit passendem --env!)
python t212_cli.py --env live ledger report
python t212_cli.py --env demo ledger report
```

Bewusste Vereinfachung: Die Ledger-Buchungen erfolgen manuell nach
Bestaetigung eines Fills (nicht automatisch beim Platzieren einer Order,
da Market-Orders asynchron und ausserhalb der Handelszeiten erst spaeter
gefuellt werden -- siehe Erfahrung mit der ersten NVDA-Demo-Order). Das
Ledger ist damit bewusst einfach gehalten (ein Startkapital, kein
automatisches Top-up) -- eine spaetere Kapitalerhoehung braeuchte eine
neue Buchungsart (z.B. TOPUP), die noch nicht existiert.

**Sicherheitsmechanismus wegen der obigen Ueberschneidung:** `sell` in
`t212_cli.py` prueft vor jedem Verkauf sowohl die tatsaechlich gehaltene
T212-Menge als auch die im Ledger diesem Experiment zugeordnete Menge und
verwendet das Minimum (`_max_sellable_quantity()`). Damit kann das Tool nie
mehr verkaufen, als das Experiment selbst gekauft hat -- private Bestaende
(z.B. die 0.35 NVDA von 2025) bleiben geschuetzt, selbst wenn ein Verkauf
mengenmaessig innerhalb der gesamten Kontoposition liegen wuerde. Getestet
in `tests/test_sell_guardrail.py` mit dem exakten NVDA-Szenario.

## Offene Punkte / naechste Iterationen

- [ ] Nach den ersten Wochen pruefen, ob die Signalqualitaet (Trefferquote,
      durchschnittlicher Gewinn/Verlust pro Trade) plausibel ist, bevor
      Positionsgroessen weiter erhoeht werden
- [ ] Backtesting der Regeln auf historischen Daten, bevor grössere Summen
      eingesetzt werden (mit `signals.py` als Ausgangsbasis moeglich)


## Automatisierungs-Policy (22.09.2026)

Andys Entscheidung: Schritte 1-7 des Ablaufs (Signale lesen, beurteilen,
Positionsgroesse festlegen, Trockenlauf, Order platzieren, Fill pruefen,
Ledger verbuchen) laufen automatisiert, ohne Freigabe je Trade. Damit
faellt die bisherige "Signal != Ausfuehrung"-Bremse fuer den Kernentscheid
weg -- das ist ein bewusster Strategiewechsel, kein rein technisches Detail.

**Wichtiger technischer Befund (22.09.2026):** Eine Automatisierung ueber
einen Claude-Scheduled-Task (Ausfuehrung in der Claude-Sandbox/`device_bash`)
ist nicht moeglich -- die Sandbox hat aus Policy-Gruenden GAR KEINEN
Internetzugang (auch nicht zu Yahoo Finance fuer Schritt 1 allein).
Getestet mit direktem `curl`, Ergebnis: `403 Forbidden` selbst zu
`google.com`. Deshalb laeuft die Automatisierung stattdessen ueber die
native WINDOWS-AUFGABENPLANUNG direkt auf Andys Rechner (echter
Internetzugang) -- siehe README.md, Abschnitt "Automatisierung
einrichten". Claudes Rolle verschiebt sich dadurch von "urteilt live bei
jedem Trade" zu "regelmaessige nachtraegliche Pruefung/Review" (Logs/Ledger
lesen, das braucht kein Netzwerk und funktioniert ueber den Datei-Zugriff
weiterhin normal).

**Rollenverteilung:** Da kein Live-Urteil zur Ausfuehrungszeit moeglich
ist, sind die Beurteilungs-Kriterien (Punkt 2+3) vollstaendig in Code
gegossen (`auto_policy.py`) statt zur Laufzeit neu ueberlegt zu werden --
mechanisch, fest, getestet. Das ist die Sicherheitsschicht. Eine
gelegentliche Claude-Review (auf Zuruf oder informell) kann das Ergebnis
im Nachhinein pruefen und bei Auffaelligkeiten Aenderungsvorschlaege fuer
`auto_policy.py` machen -- aber niemals rueckwirkend einen bereits
ausgefuehrten Trade beeinflussen.

**Umfang:** BUY und SELL werden beide automatisch ausgefuehrt (Andys
Entscheidung -- SELL nutzt denselben Ledger-Schutz wie bisher, siehe
Abschnitt "Ledger" unten).

**Mechanische Regeln (`auto_policy.py`):**
- Max. `MAX_OPEN_POSITIONS = 3` gleichzeitig offene Positionen (Ledger-Zaehlung; seit 07.10.2026, vorher 2)
- Positionsgroesse: `POSITION_FRACTION = 0.30` (seit 07.10.2026, vorher 0.45) des
  Ledger-Gesamtwerts, gedeckelt durch (a) Ledger-Cash-Reserve
  (`CASH_RESERVE_FRACTION = 0.10`) und (b) tatsaechlich verfuegbares
  API-Cash mit Sicherheitsabschlag (`API_CASH_SAFETY_FACTOR = 0.95`)
- Mindestgroesse pro Trade: `MIN_TRADE_NOTIONAL_CHF = 5.0` (kleinere
  Betraege werden uebersprungen statt als Mini-Order ausgefuehrt)
- **Extended-Filter** (zusaetzlich zu den Entry-Regeln aus `signals.py`):
  BUY wird nur ausgefuehrt, wenn `RSI14 <= 75` (Puffer vor dem
  ueberkauften Rand) UND der Kurs maximal `5%` ueber dem 20-Tage-
  Breakout-Niveau liegt (`MAX_PCT_ABOVE_BREAKOUT`). Verhindert
  automatisches Nachkaufen in eine bereits weit gelaufene Bewegung hinein
  -- codifiziert, was bisher als Ad-hoc-Einschaetzung (z.B. beim
  AMD-Signal) manuell entschieden wurde.
- **Duplicate-Order-Guard:** keine neue Order fuer einen Ticker, der schon
  eine offene Order hat (`get_open_orders()`-Check) -- wichtig, da
  T212-Order-Endpunkte laut Doku nicht idempotent sind.
- **Drawdown-Alarm:** bei `>= -25%` seit letztem Hoch (`risk_monitor.py`,
  `equity_live.csv`/`equity_demo.csv`) wird das in jeder Zusammenfassung
  als Alarm ausgewiesen, pausiert die Automatisierung aber NICHT (Andys
  Entscheidung 22.09.2026 -- bewusst abweichend von der ansonsten
  manuellen Drawdown-Pruefung weiter oben in diesem Dokument).

**Ablauf in der Praxis (siehe README.md fuer die genauen Kommandos):**
1. `book_fills.py --env live` (1x taeglich, ca. 22:00, Windows-
   Aufgabenplanung): Schritte 6-7 -- prueft alle noch offenen, zuvor
   platzierten Orders auf Fill und bucht bei Erfolg automatisch in den
   Ledger. Laeuft bewusst ZUERST, damit Schritt 2 mit aktuellem
   Ledger-Stand rechnet. Bekannte Vereinfachung: Teil-Fills werden nur
   einmalig (mit der zu diesem Zeitpunkt gefuellten Menge) verbucht.
2. `auto_trade.py --env live --execute` (1x taeglich, ca. 22:15, direkt
   nach Schritt 1, Windows-Aufgabenplanung): Schritte 1-5 -- Signale
   lesen, Extended-/Guard-Filter anwenden, Positionsgroesse berechnen,
   Order platzieren. Bucht NICHT selbst in den Ledger (Fill oft erst
   Stunden/Tage spaeter, siehe Erfahrung mit dem ersten AAPL-Live-Trade;
   das uebernimmt am naechsten Tag wieder Schritt 1).
3. Benachrichtigung: Push+E-Mail nach jedem Lauf (Andys Entscheidung --
   volle Transparenz ueber ein System, das ohne Vorab-Freigabe handelt),
   siehe Scheduled-Task-Konfiguration.

**Frequenz-Entscheidung (23.09.2026):** Beide Skripte laufen bewusst nur
EINMAL taeglich, nicht mehrfach. Fuer `auto_trade.py` ist das kein
Komfort-, sondern ein Risikopunkt: Die Entry-/Exit-Regeln rechnen mit
TAEGLICHEN Schlusskursen (SMA50/SMA200/RSI). Mehrfach am Tag abgefragt,
liefert Yahoo Finance fuer den laufenden Tag keinen echten Schlusskurs,
sondern den aktuellen Zwischenstand als Platzhalter -- das haette das
System von "Trend-Following auf Tagesbasis" zu "intraday-reaktiv"
verschoben, mit hoeherem Risiko von Fehlkaeufen durch kurzfristige
Kursausschlaege (Whipsaws), ohne dass die Regeln dafuer ausgelegt sind.
Urspruenglich war sogar nur woechentlich vorgesehen (siehe Entry-/Exit-
Regeln oben) -- taeglich ist ein bewusster Mittelweg: schnellere Reaktion
auf neue Trends, aber weiterhin auf Basis gesetzter Tagesschlusskurse.

**Korrektur (25.09.2026):** `auto_trade.py` protokollierte die order_id
bisher NICHT im Trade-Log, weil `log_entry()` vor der Order-Platzierung
aufgerufen wurde (die order_id existiert zu dem Zeitpunkt noch nicht).
Folge: `book_fills.py` haette die Order nie gefunden (order_id-Feld leer),
identischer Fehlertyp wie beim AAPL-404-Vorfall, nur an anderer Stelle.
Entdeckt beim ersten automatischen AMD-Kauf (0.01 Stk, Order 57861561223,
24.09.2026 20:15 UTC). Behoben: `log_entry()` laeuft jetzt NACH der
Order-Platzierung. Der betroffene Log-Eintrag vom 24.09. wurde manuell mit
der order_id nachgetragen.

**Korrektur (29.09.2026):** Reale T212-Kontoprüfung ergab 120 CHF Restguthaben,
das im Ledger (Cash 4.72 CHF nach den AAPL/AMD-Kaeufen) nicht abgebildet war.
Ursache: Restguthaben, das bereits bei Kontoeroeffnung vorhanden war, aber nie
explizit erfasst wurde -- keine neue Einzahlung. Da `ledger.py` bis dahin nur
OPENING | BUY | SELL | NOTE kannte (siehe Docstring-Hinweis bei
record_opening_balance auf genau diese Luecke), wurde ein neuer, additiver
Buchungstyp DEPOSIT ergaenzt (`record_deposit()` in ledger.py,
`ledger deposit --amount-chf ...` in t212_cli.py) statt die historische
OPENING-Buchung rueckwirkend zu veraendern -- damit bleibt nachvollziehbar,
wann welches Kapital zur Verfuegung stand. Gebucht: +120 CHF am 29.09.2026,
neuer Ledger-Cash-Stand 124.72 CHF, Ledger-Gesamtwert 324.50 CHF. Die
Positionsanzahl-Obergrenze (MAX_OPEN_POSITIONS=2, beide Slots belegt)
bleibt unveraendert -- das zusaetzliche Cash liegt als Reserve, bis ein
Slot frei wird oder die Grenze bewusst erhoeht wird. 2 neue Tests in
tests/test_ledger.py.

**Notabschaltung:** Die Windows-Aufgabenplanung kann jederzeit direkt in
Windows pausiert/geloescht werden (`schtasks /change /tn <Name> /disable`)
-- das ist die schnellste Bremse, unabhaengig von Claude.


## Stop-Loss und Trailing-Stop live (07.10.2026)

Anlass: Der Backtest (06.10.2026, siehe `backtest.py`) zeigte, dass die
LIVE-Regeln ohne Stops einen Drawdown von -32% und einen schlechtesten Trade
von -23% hatten; die Variante mit Stops -23% bzw. bessere Sharpe/CAGR. Die
Stops standen bisher nur in diesem Dokument, aber nicht in `auto_trade.py`.
Andys Entscheidung: live einbauen.

**Regeln (`auto_policy.py`, Konstanten `STOP_LOSS_PCT=0.12`, `TRAILING_STOP_PCT=0.10`):**
- Stop-Loss: Tagesschluss <= Einstand * 0.88
- Trailing-Stop: Tagesschluss <= Hoechstschluss seit Einstieg * 0.90
  (Hoechstkurs startet mindestens beim Einstand, Einstiegstag zaehlt mit)
- Stop-Loss hat Vorrang vor Trailing. Beide gelten zusaetzlich zum SMA50-Exit.

**Ausfuehrung:** In `auto_trade.py` (taeglich 22:15 via Windows-Aufgabenplanung,
dieselbe Aufgabe wie bisher -- keine neue Aufgabe noetig). Die Pruefung laeuft
auf dem Tagesschlusskurs; die Verkaufsorder wird nach US-Boersenschluss als
Market-Order platziert und fuellt zur naechsten Eroeffnung (wie im Backtest
modelliert). Es ist KEIN Intraday-Stopp und KEIN Stop-Order bei T212: Ein
Gap ueber die Stop-Schwelle hinaus fuellt zum Eroeffnungskurs, nicht zur
Schwelle.

**Datenquellen:** Einstand = `averagePricePaid` und Einstiegsdatum =
`createdAt` der T212-Position (Instrumentenwaehrung USD, vergleichbar mit
Yahoo-Schlusskursen); Hoechstschluss aus der Yahoo-Historie seit Einstieg.
Rechnung in USD, FX-Effekt ausserhalb der Stops (wie im Backtest).

**Sicherheitsnetz:** Fehlen Kurshistorie, Einstandspreis oder Einstiegsdatum,
oder liegt Einstand/Schluss ausserhalb 1/3..3 (Waehrung/Daten verdaechtig),
wird die Stop-Pruefung uebersprungen und im Lauf als Hinweis ausgegeben --
nie ein Verkauf aufgrund unplausibler Daten. Der bestehende Ledger-Schutz
(nur verkaufen, was das Experiment besitzt) und der Duplicate-Order-Guard
gelten unveraendert.

**Transparenz:** Jeder Lauf druckt "Stop-Status offener Positionen" mit
Einstand, Hoechstschluss, Stop-Loss-Level und Trailing-Level (auch im
`SUMMARY_JSON` unter `stop_status`).

Tests: `tests/test_stops.py` (Schwellen, Peak-Berechnung, Plausibilitaets-
Guards, Integrationslauf mit Fake-Client).


## Slots 3 x 30% statt 2 x 45% (07.10.2026)

Entscheidung (Andy, 07.10.2026): `MAX_OPEN_POSITIONS = 3`, `POSITION_FRACTION = 0.30`
(3 x 30% = 90%, 10% Cash-Reserve bleibt moeglich). Ersetzt die in der
Strategie ueber der Automatisierungs-Policy genannten 2 Positionen mit 40-50%.

Grundlage (`backtest.py --sensitivity`, 2020-08-27 bis 2026-10-06, Regeln inkl. Stops):

| Kosten je Seite | 2 x 45% CAGR / Max.DD / Sharpe | 3 x 30% CAGR / Max.DD / Sharpe |
|---|---|---|
| 0.20% | 15.3% / -23.2% / 0.77 | 15.8% / -22.5% / 0.88 |
| 0.40% | 12.8% / -25.7% / 0.67 | 13.5% / -25.0% / 0.77 |

Einordnung: Der Vorteil ist klein, aber in beiden Kostenannahmen in allen drei
Kennzahlen gleichgerichtet; kleinere Einzelpositionen (schlechtester Backtest-Trade
bei 324 CHF: -31 statt -67 CHF) und kein blockierter Slot durch eine Mini-Position
(AMD 0.01 Stk. am 07.10.2026). Alternativen 4 x 22% / 5 x 18% senkten den
Drawdown staerker (-18%/-17%), kosteten aber ca. 0.6-0.7 Punkte CAGR (bei 0.40% Kosten).
Weiterhin gilt: Der Backtest liegt mit allen Varianten hinter SPY/QQQ und hinter
Buy&Hold auf dem Universum (Survivorship-Bias beachten); die Aenderung ist
Risikoverteilung, kein Renditeversprechen. Bestehende Positionen (AAPL ~194 CHF, AMD ~5 CHF)
bleiben unveraendert; das naechste BUY-Signal wird mit 30% des Ledger-Gesamtwerts gekauft.
