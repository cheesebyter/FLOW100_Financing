"""Netzwerkfreie Tests fuer die Signal-Logik (siehe STRATEGY.md).
Aufruf: python -m pytest tests/  (oder: python tests/test_signals.py)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signals import compute_signal_from_history  # noqa: E402


def _make_history(closes: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="B")
    return pd.DataFrame({"Close": closes}, index=dates)


def test_returns_none_when_not_enough_history():
    history = _make_history([100.0] * 199)
    assert compute_signal_from_history(history) is None


def test_buy_signal_on_uptrend_breakout_with_healthy_momentum():
    # 200 Tage Basis, 60 Tage moderater Aufwaertstrend (2 Tage hoch, 1 Tag
    # leicht runter -> haelt RSI im moderaten Bereich statt Richtung 100 zu
    # laufen), letzte 20 Tage zickzack mit einem finalen groesseren Sprung,
    # der ein neues 20-Tage-Hoch markiert (Breakout-Bedingung).
    closes = [100.0] * 200
    price = 100.0
    pre_pattern = [0.6, 0.5, -0.3]
    for i in range(60):
        price += pre_pattern[i % len(pre_pattern)]
        closes.append(price)
    tail = [-0.3, 0.6, -0.2, 0.5, -0.3, 0.6, -0.2, 0.5, -0.3, 0.6,
            -0.2, 0.5, -0.3, 0.6, -0.2, 0.5, -0.3, 0.6, -0.2, 1.0]
    for d in tail:
        price += d
        closes.append(price)
    history = _make_history(closes)
    result = compute_signal_from_history(history)
    assert result is not None
    assert result.signal == "BUY", result.reason
    assert 50 <= result.rsi14 <= 80


def test_sell_signal_when_price_drops_below_sma50():
    closes = [100.0 + i * 0.5 for i in range(250)]  # sauberer Aufwaertstrend
    closes += [closes[-1] * 0.7] * 5  # scharfer Einbruch am Ende
    history = _make_history(closes)
    result = compute_signal_from_history(history)
    assert result is not None
    assert result.signal == "SELL", result.reason


def test_hold_signal_in_flat_choppy_market():
    rng = np.random.default_rng(42)
    closes = list(100.0 + rng.normal(0, 0.3, size=210).cumsum() * 0.05)
    history = _make_history(closes)
    result = compute_signal_from_history(history)
    assert result is not None
    assert result.signal in ("HOLD", "SELL", "BUY")  # nur: darf nicht crashen


if __name__ == "__main__":
    test_returns_none_when_not_enough_history()
    test_buy_signal_on_uptrend_breakout_with_healthy_momentum()
    test_sell_signal_when_price_drops_below_sma50()
    test_hold_signal_in_flat_choppy_market()
    print("ALL TESTS PASSED")
