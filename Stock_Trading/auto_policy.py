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

import pandas as pd

from signals import SignalResult

MAX_OPEN_POSITIONS = 3            # seit 07.10.2026 (vorher 2), siehe STRATEGY.md "Slots 3 x 30%"
POSITION_FRACTION = 0.30          # seit 07.10.2026 (vorher 0.45); MAX_OPEN_POSITIONS * POSITION_FRACTION <= 1 - CASH_RESERVE_FRACTION
CASH_RESERVE_FRACTION = 0.10      # mind. 10% Cash-Reserve im Ledger belassen
API_CASH_SAFETY_FACTOR = 0.95     # Puffer ggue. availableToTrade (Rundung/Settlement)
MIN_TRADE_NOTIONAL_CHF = 5.0

MAX_RSI_FOR_ENTRY = 75.0          # Puffer vor der oberen Signalgrenze (80)
MAX_PCT_ABOVE_BREAKOUT = 0.05     # "Extended"-Filter: max. 5% ueber 20T-Hoch

STOP_LOSS_PCT = 0.12              # Verkauf, wenn Schluss <= Einstand * (1 - 12%)
TRAILING_STOP_PCT = 0.10          # Verkauf, wenn Schluss <= Hoechstschluss seit Einstieg * (1 - 10%)
STOP_MAX_PRICE_RATIO = 3.0        # Plausibilitaet: Einstand/Schluss ausserhalb 1/3..3 -> Daten verdaechtig, kein Stop

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


@dataclass
class StopCheck:
    reason: Optional[str]      # None = kein Stop ausgeloest
    note: str = ""             # Hinweis (z.B. warum nicht pruefbar)
    entry_price: Optional[float] = None
    peak: Optional[float] = None
    stop_loss_level: Optional[float] = None
    trailing_level: Optional[float] = None
    close: Optional[float] = None


def peak_since(closes: pd.Series, entry_ts: str, entry_price: float) -> float:
    """Hoechster Tagesschluss seit dem Einstiegstag (inkl. Einstiegstag),
    mindestens der Einstandspreis -- wie im Backtest (peak startet beim Fill)."""
    entry_date = pd.Timestamp(entry_ts).tz_convert("UTC").date() if pd.Timestamp(entry_ts).tzinfo else pd.Timestamp(entry_ts).date()
    mask = [d >= entry_date for d in closes.index.date]
    since = closes[mask]
    return float(max(entry_price, since.max())) if len(since) else float(entry_price)


def check_stop(
    close: float, entry_price: float, peak: float,
    stop_loss: float = STOP_LOSS_PCT, trailing: float = TRAILING_STOP_PCT,
) -> Optional[str]:
    """Rein mechanisch, auf Tagesschlusskurs-Basis (Order dann am Folgetag
    zur Eroeffnung, wie im Backtest). Stop-Loss hat Vorrang vor Trailing."""
    if close <= entry_price * (1 - stop_loss):
        return (f"Stop-Loss: Schluss {close:.2f} <= {entry_price * (1 - stop_loss):.2f} "
                f"(-{stop_loss * 100:.0f}% vom Einstand {entry_price:.2f})")
    if close <= peak * (1 - trailing):
        return (f"Trailing-Stop: Schluss {close:.2f} <= {peak * (1 - trailing):.2f} "
                f"(-{trailing * 100:.0f}% vom Hoechstschluss {peak:.2f} seit Einstieg)")
    return None


def evaluate_stop(
    close: float, closes: Optional[pd.Series], avg_price: Optional[float], created_at: Optional[str],
) -> StopCheck:
    """Holt alles zusammen und degradiert sauber: fehlende/unplausible Daten
    fuehren NIE zu einem Verkauf, sondern zu einem Hinweis (note)."""
    if closes is None or len(closes) == 0:
        return StopCheck(None, "Stop-Pruefung uebersprungen: keine Kurshistorie", close=close)
    if not avg_price or not created_at:
        return StopCheck(None, "Stop-Pruefung uebersprungen: Einstandspreis/Einstiegsdatum fehlt", close=close)
    ratio = avg_price / close if close > 0 else float("inf")
    if not (1 / STOP_MAX_PRICE_RATIO <= ratio <= STOP_MAX_PRICE_RATIO):
        return StopCheck(
            None,
            f"Stop-Pruefung uebersprungen: Einstand {avg_price:.2f} vs. Schluss {close:.2f} unplausibel "
            f"(Waehrung/Daten pruefen)", close=close,
        )
    peak = peak_since(closes, created_at, avg_price)
    return StopCheck(
        reason=check_stop(close, avg_price, peak), entry_price=avg_price, peak=peak,
        stop_loss_level=avg_price * (1 - STOP_LOSS_PCT), trailing_level=peak * (1 - TRAILING_STOP_PCT),
        close=close,
    )
