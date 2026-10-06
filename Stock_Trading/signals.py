"""
Regelbasierte Signalgenerierung (Trend-Following/Momentum) fuer das
FLOW100-Trading-Experiment. Regeln siehe STRATEGY.md.

Datenquelle: Yahoo Finance via yfinance (kein API-Key noetig). Trading212
liefert laut oeffentlicher API-Doku (Stand Sept. 2026) keine historischen
Kursdaten/Candles, nur Account-/Order-/Instrumenten-Metadaten -- daher
getrennte Datenquelle fuer Signale, T212 nur fuer Konto/Ausfuehrung.

WICHTIG: Diese Sandbox-Umgebung hat keinen Netzwerkzugriff auf Yahoo
Finance. get_signals()/main() muessen auf einem Rechner mit normalem
Internetzugang laufen (z.B. deinem PC direkt, ausserhalb der Claude-VM).
compute_signal_from_history() ist netzwerkfrei und wird per Unit-Test mit
synthetischen Daten abgedeckt (siehe tests/test_signals.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import pandas as pd

Signal = Literal["BUY", "SELL", "HOLD"]

# T212-Ticker -> Yahoo-Finance-Symbol. Liquide, hochvolatile Large-Caps
# (bewusst konzentriertes/aggressives Universum, siehe STRATEGY.md).
#
# Bewusst OHNE NVDA/MSFT/META: diese ueberschneiden sich mit bereits
# bestehenden privaten Positionen auf dem Live-Konto (siehe STRATEGY.md,
# Abschnitt "Handelsuniversum" / "Ledger", Stand 09.09.2026) -- ausserhalb
# des Universums bleibt die Trennung zwischen Experiment und Privatdepot
# eindeutig, ganz ohne auf den Ledger-Schutz angewiesen zu sein.
UNIVERSE: dict[str, str] = {
    "TSLA_US_EQ": "TSLA",
    "AAPL_US_EQ": "AAPL",
    "AMD_US_EQ": "AMD",
    "AMZN_US_EQ": "AMZN",
    "GOOGL_US_EQ": "GOOGL",
    "AVGO_US_EQ": "AVGO",
    "NFLX_US_EQ": "NFLX",
    "CRM_US_EQ": "CRM",
}


@dataclass
class SignalResult:
    t212_ticker: str
    yahoo_symbol: str
    signal: Signal
    close: float
    sma50: float
    sma200: float
    high_20d_prev: float
    rsi14: float
    reason: str
    # Wie weit (in %) liegt der Kurs ueber dem 20-Tage-Breakout-Niveau?
    # 0.0 = genau am Breakout, 0.05 = 5% darueber. Nur bei BUY-Signalen
    # aussagekraeftig -- wird von auto_policy.is_actionable_buy() als
    # "Extended"-Filter genutzt (siehe STRATEGY.md, Automatisierungs-Policy).
    pct_above_breakout: float = 0.0


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def compute_signal_from_history(history: pd.DataFrame) -> Optional[SignalResult]:
    """history: DataFrame mit Spalte 'Close', aufsteigend nach Datum sortiert
    (aeltestes zuerst) -- so wie yfinance sie liefert. Gibt None zurueck, wenn
    zu wenig Historie fuer SMA200 vorhanden ist."""
    if len(history) < 200:
        return None

    close = history["Close"]
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    high_20d = close.rolling(20).max()
    rsi14 = _rsi(close, 14)

    last_close = float(close.iloc[-1])
    last_sma50 = float(sma50.iloc[-1])
    last_sma200 = float(sma200.iloc[-1])
    # Hoch der 20 Tage VOR heute (Breakout = heutiger Kurs erreicht/uebertrifft das)
    prev_high_20d = float(high_20d.iloc[-2])
    last_rsi = float(rsi14.iloc[-1])

    uptrend = last_close > last_sma50 > last_sma200
    breakout = last_close >= prev_high_20d
    momentum_ok = 50 <= last_rsi <= 80

    if uptrend and breakout and momentum_ok:
        signal: Signal = "BUY"
        reason = "Aufwaertstrend (Kurs>SMA50>SMA200) + 20T-Hoch-Breakout + RSI in [50,80]"
    elif last_close < last_sma50:
        signal = "SELL"
        reason = "Trendbruch: Kurs < SMA50"
    else:
        signal = "HOLD"
        reason = "Keine Entry-/Exit-Bedingung erfuellt"

    pct_above_breakout = (last_close / prev_high_20d - 1) if prev_high_20d > 0 else 0.0

    return SignalResult(
        t212_ticker="", yahoo_symbol="", signal=signal, close=last_close,
        sma50=last_sma50, sma200=last_sma200, high_20d_prev=prev_high_20d,
        rsi14=last_rsi, reason=reason, pct_above_breakout=pct_above_breakout,
    )


def get_signals(universe: dict[str, str] = UNIVERSE) -> list[SignalResult]:
    import yfinance as yf  # lazy import: nur noetig, wenn wirklich Daten geholt werden

    results = []
    for t212_ticker, yahoo_symbol in universe.items():
        history = yf.Ticker(yahoo_symbol).history(period="1y", interval="1d")
        result = compute_signal_from_history(history)
        if result is None:
            continue
        result.t212_ticker = t212_ticker
        result.yahoo_symbol = yahoo_symbol
        results.append(result)
    return results


if __name__ == "__main__":
    for r in get_signals():
        print(
            f"{r.t212_ticker:15s} {r.signal:5s} close={r.close:.2f} "
            f"sma50={r.sma50:.2f} sma200={r.sma200:.2f} rsi14={r.rsi14:.1f}  {r.reason}"
        )
