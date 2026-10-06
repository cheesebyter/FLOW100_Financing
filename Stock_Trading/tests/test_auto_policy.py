"""
Tests fuer auto_policy.py -- die mechanische Regelschicht der
Automatisierung (siehe STRATEGY.md, "Automatisierungs-Policy").
Ohne pytest lauffaehig: python tests/test_auto_policy.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_policy import (
    MAX_OPEN_POSITIONS,
    compute_buy_quantity,
    count_open_positions,
    has_open_order,
    is_actionable_buy,
    is_drawdown_alert,
)
from signals import SignalResult


def _sig(signal="BUY", rsi14=60.0, pct_above_breakout=0.01) -> SignalResult:
    return SignalResult(
        t212_ticker="AAPL_US_EQ", yahoo_symbol="AAPL", signal=signal,
        close=200.0, sma50=190.0, sma200=180.0, high_20d_prev=198.0,
        rsi14=rsi14, reason="test", pct_above_breakout=pct_above_breakout,
    )


def test_actionable_clean_buy_is_ok():
    ok, reason = is_actionable_buy(_sig())
    assert ok is True, reason


def test_non_buy_signal_rejected():
    ok, reason = is_actionable_buy(_sig(signal="HOLD"))
    assert ok is False
    assert "Kein BUY" in reason


def test_extended_rsi_rejected():
    ok, reason = is_actionable_buy(_sig(rsi14=79.0))
    assert ok is False
    assert "RSI" in reason


def test_extended_breakout_distance_rejected():
    ok, reason = is_actionable_buy(_sig(pct_above_breakout=0.10))
    assert ok is False
    assert "Breakout" in reason


def test_count_open_positions_ignores_zero_and_dust():
    assert count_open_positions({"AAPL_US_EQ": 0.33, "AMD_US_EQ": 0.0, "TSLA_US_EQ": 1e-12}) == 1


def test_has_open_order_nested_instrument_format():
    orders = [{"instrument": {"ticker": "AAPL_US_EQ"}, "quantity": 0.1}]
    assert has_open_order(orders, "AAPL_US_EQ") is True
    assert has_open_order(orders, "AMD_US_EQ") is False


def test_has_open_order_true_false():
    orders = [{"ticker": "AAPL_US_EQ"}, {"ticker": "TSLA_US_EQ"}]
    assert has_open_order(orders, "AAPL_US_EQ") is True
    assert has_open_order(orders, "AMD_US_EQ") is False


def test_sizing_normal_case_uses_position_fraction():
    # Ledger-Gesamtwert 200, 45% davon = 90 CHF Ziel; genug Cash und API-Cash vorhanden.
    sizing = compute_buy_quantity(
        price_chf=100.0, ledger_cash_chf=150.0, ledger_total_value_chf=200.0,
        api_available_to_trade_chf=500.0,
    )
    assert sizing.quantity == 0.9
    assert sizing.skip_reason == ""


def test_sizing_capped_by_ledger_cash_reserve():
    # Ledger-Cash nur 20 CHF -> 90% davon = 18 CHF Ziel (kleiner als 45%-Ziel von 90).
    sizing = compute_buy_quantity(
        price_chf=100.0, ledger_cash_chf=20.0, ledger_total_value_chf=200.0,
        api_available_to_trade_chf=500.0,
    )
    assert sizing.quantity == 0.18


def test_sizing_capped_by_api_available_cash():
    sizing = compute_buy_quantity(
        price_chf=100.0, ledger_cash_chf=150.0, ledger_total_value_chf=200.0,
        api_available_to_trade_chf=10.0,  # * 0.95 = 9.5 CHF Ziel
    )
    assert sizing.quantity == 0.1  # round(9.5/100, 2)


def test_sizing_skips_below_min_notional():
    sizing = compute_buy_quantity(
        price_chf=100.0, ledger_cash_chf=150.0, ledger_total_value_chf=200.0,
        api_available_to_trade_chf=3.0,  # * 0.95 = 2.85 CHF < Mindestgroesse 5 CHF
    )
    assert sizing.quantity == 0.0
    assert "Mindestgroesse" in sizing.skip_reason


def test_sizing_invalid_price_rejected():
    sizing = compute_buy_quantity(
        price_chf=0.0, ledger_cash_chf=150.0, ledger_total_value_chf=200.0,
        api_available_to_trade_chf=500.0,
    )
    assert sizing.quantity == 0.0
    assert "Preis" in sizing.skip_reason


def test_drawdown_alert_threshold():
    assert is_drawdown_alert(-0.30) is True
    assert is_drawdown_alert(-0.25) is True
    assert is_drawdown_alert(-0.24) is False
    assert is_drawdown_alert(0.05) is False


def test_max_open_positions_constant_matches_strategy():
    assert MAX_OPEN_POSITIONS == 2


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
