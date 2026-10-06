"""
Mechanisches Regelwerk fuer die automatisierte Ausfuehrung (siehe
STRATEGY.md, Abschnitt "Automatisierungs-Policy"). Bewusst als eigenes,
getestetes Modul: Positionsgroessen/Filter-Schwellen sind Zahlen, keine
Ad-hoc-Einschaetzung zur Laufzeit -- damit jeder automatische Lauf
nachvollziehbar dieselben Regeln anwendet.

Rollenverteilung (Andys Entscheidung, 22.09.2026): Diese Regeln sind die
mechanische Sicherheitsschicht. Die ausfuehrende Claude-Session (im
Scheduled Task) legt zusaetzlich eine kurze Plausibilitaetspruefung
("Gutcheck") auf das Ergebnis -- z.B. offensichtlich fehlerhafte
Kursdaten, ein Ticker mit Earnings am selben Tag o.ae. -- und kann einen
mechanisch erlaubten Trade ablehnen, aber niemals einen mechanisch
verbotenen Trade erlauben.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from signals import SignalResult

MAX_OPEN_POSITIONS = 2
POSITION_FRACTION = 0.45          # Mittelwert des 40-50%-Bands aus STRATEGY.md
CASH_RESERVE_FRACTION = 0.10      # mind. 10% Cash-Reserve im Ledger belassen
API_CASH_SAFETY_FACTOR = 0.95     # Puffer ggue. availableToTrade (Rundung/Settlement)
MIN_TRADE_NOTIONAL_CHF = 5.0

MAX_RSI_FOR_ENTRY = 75.0          # Puffer vor der oberen Signalgrenze (80)
MAX_PCT_ABOVE_BREAKOUT = 0.05     # "Extended"-Filter: max. 5% ueber 20T-Hoch

DRAWDOWN_ALERT_THRESHOLD = -0.25  # STRATEGY.md: -25% seit letztem Hoch


def is_actionable_buy(signal: SignalResult) -> tuple[bool, str]:
    """Zusaetzlicher Filter ueber die reinen Entry-Regeln aus signals.py
    hinaus: verhindert automatisches Nachkaufen in einen bereits weit
    gelaufenen ("extended") Breakout hinein. Rein mechanisch, damit die
    automatisierte Ausfuehrung nicht von einer variablen Tageseinschaetzung
    abhaengt."""
    if signal.signal != "BUY":
        return False, f"Kein BUY-Signal (aktuell: {signal.signal})"
    if signal.rsi14 > MAX_RSI_FOR_ENTRY:
        return False, (
            f"RSI {signal.rsi14:.1f} > {MAX_RSI_FOR_ENTRY} (zu nah am ueberkauften "
            f"Rand, 'extended')"
        )
    if signal.pct_above_breakout > MAX_PCT_ABOVE_BREAKOUT:
        return False, (
            f"Kurs {signal.pct_above_breakout * 100:.1f}% ueber 20T-Breakout-Niveau "
            f"(Grenze {MAX_PCT_ABOVE_BREAKOUT * 100:.0f}%, 'extended')"
        )
    return True, "Signal BUY, innerhalb der Extended-Filter-Grenzen"


def count_open_positions(open_positions: dict[str, float]) -> int:
    return sum(1 for qty in open_positions.values() if qty > 1e-9)


def _order_ticker(o: dict):
    """Ticker einer Order -- flach ('ticker') oder verschachtelt
    ('instrument.ticker', wie bei den Positionen). Das genaue Order-Format
    der API ist nicht verifiziert (Stand 30.09.2026), daher beide Formen."""
    return o.get("ticker") or (o.get("instrument") or {}).get("ticker")


def has_open_order(open_orders: list[dict], ticker: str) -> bool:
    return any(_order_ticker(o) == ticker for o in open_orders)


@dataclass
class SizingResult:
    quantity: float
    notional_chf: float
    skip_reason: str = ""


def compute_buy_quantity(
    *, price_chf: float, ledger_cash_chf: float, ledger_total_value_chf: float,
    api_available_to_trade_chf: float,
) -> SizingResult:
    """Positionsgroesse nach STRATEGY.md: bis zu POSITION_FRACTION des
    Ledger-Gesamtwerts, gedeckelt durch (a) die im Ledger einzuhaltende
    Cash-Reserve und (b) das tatsaechlich am Konto verfuegbare Cash
    (mit Sicherheitsabschlag). Rundet auf 2 Nachkommastellen (Bruchstueck-
    Aktien), analog zur bisherigen manuellen Praxis."""
    if price_chf <= 0:
        return SizingResult(0.0, 0.0, "Ungueltiger Preis <= 0")

    target_by_position_size = POSITION_FRACTION * ledger_total_value_chf
    target_by_ledger_cash = ledger_cash_chf * (1 - CASH_RESERVE_FRACTION)
    target_by_api_cash = api_available_to_trade_chf * API_CASH_SAFETY_FACTOR

    target_notional = min(target_by_position_size, target_by_ledger_cash, target_by_api_cash)
    if target_notional < MIN_TRADE_NOTIONAL_CHF:
        return SizingResult(
            0.0, 0.0,
            f"Zielbetrag {target_notional:.2f} CHF < Mindestgroesse {MIN_TRADE_NOTIONAL_CHF} CHF "
            f"(limitiert durch Positionsgroesse={target_by_position_size:.2f}, "
            f"Ledger-Cash-Reserve={target_by_ledger_cash:.2f}, "
            f"API-Cash={target_by_api_cash:.2f})",
        )

    quantity = round(target_notional / price_chf, 2)
    if quantity <= 0:
        return SizingResult(0.0, 0.0, "Berechnete Menge rundet auf 0")

    return SizingResult(quantity=quantity, notional_chf=round(quantity * price_chf, 2))


def is_drawdown_alert(drawdown_pct: float, threshold: float = DRAWDOWN_ALERT_THRESHOLD) -> bool:
    return drawdown_pct <= threshold
