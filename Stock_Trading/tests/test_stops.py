"""Netzwerkfreie Tests fuer Stop-Loss/Trailing-Stop (auto_policy + auto_trade).
Aufruf: python tests/test_stops.py"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auto_policy as ap  # noqa: E402
import auto_trade  # noqa: E402
import ledger  # noqa: E402
import risk_monitor  # noqa: E402
from signals import SignalResult  # noqa: E402


def _closes(values, start="2026-09-10", tz=None):
    idx = pd.bdate_range(start, periods=len(values), tz=tz)
    return pd.Series(values, index=idx, dtype=float)


# ---- check_stop ---------------------------------------------------------
def test_stop_loss_boundary():
    assert ap.check_stop(88.0, 100.0, 100.0).startswith("Stop-Loss")      # genau -12%
    # knapp darueber: kein Stop-Loss (Trailing greift hier bei peak=100 ab 90, also nur Trailing-Hinweis)
    r = ap.check_stop(88.01, 100.0, 100.0)
    assert r is None or not r.startswith("Stop-Loss")
    assert ap.check_stop(90.01, 100.0, 100.0) is None


def test_trailing_boundary():
    # Einstand 100, Hoch 150 -> Trailing-Level 135 (Stop-Loss-Level 88 weit weg)
    assert ap.check_stop(135.0, 100.0, 150.0).startswith("Trailing-Stop")
    assert ap.check_stop(135.01, 100.0, 150.0) is None


def test_stop_loss_has_priority_over_trailing():
    assert ap.check_stop(80.0, 100.0, 100.0).startswith("Stop-Loss")


# ---- peak_since ---------------------------------------------------------
def test_peak_since_ignores_prices_before_entry_and_includes_entry_day():
    # 10.09. Hoch 500 (vor Einstieg), Einstieg 14.09., danach 330, 340, 335
    c = _closes([500, 400, 330, 340, 335], start="2026-09-10")  # 10.,11.,14.,15.,16.
    peak = ap.peak_since(c, "2026-09-14T16:30:00.000+03:00", 338.0)
    assert peak == 340.0


def test_peak_never_below_entry_price():
    c = _closes([300, 310, 305], start="2026-09-14")
    assert ap.peak_since(c, "2026-09-14T16:30:00.000+03:00", 338.0) == 338.0


def test_peak_since_works_with_tz_aware_index():
    c = _closes([330, 345, 335], start="2026-09-14", tz="America/New_York")
    assert ap.peak_since(c, "2026-09-14T16:30:00.000+03:00", 338.0) == 345.0


# ---- evaluate_stop (sauberes Degradieren) ------------------------------------
def test_evaluate_stop_degrades_without_data():
    r = ap.evaluate_stop(100.0, None, 100.0, "2026-09-14T10:00:00+00:00")
    assert r.reason is None and "keine Kurshistorie" in r.note
    r = ap.evaluate_stop(100.0, _closes([100, 101]), None, "2026-09-14T10:00:00+00:00")
    assert r.reason is None and "fehlt" in r.note


def test_evaluate_stop_skips_implausible_price_ratio():
    # z.B. Einstand in falscher Waehrung/Einheit -> darf NIE einen Verkauf ausloesen
    r = ap.evaluate_stop(5.07, _closes([5, 5.1]), 84.5, "2026-09-14T10:00:00+00:00")
    assert r.reason is None and "unplausibel" in r.note


def test_evaluate_stop_triggers_and_reports_levels():
    c = _closes([340, 345, 300], start="2026-09-14")
    r = ap.evaluate_stop(300.0, c, 338.0, "2026-09-14T16:30:00.000+03:00")
    assert r.reason and r.reason.startswith("Trailing-Stop")  # 300 <= 345*0.9=310.5
    assert abs(r.stop_loss_level - 338 * 0.88) < 1e-9
    assert abs(r.trailing_level - 345 * 0.9) < 1e-9


# ---- Integration: auto_trade.run mit Fake-Client ------------------------------------
class FakeClient:
    placed = []

    def __init__(self, environment="live"):
        pass

    def get_account_summary(self):
        return {"cash": {"availableToTrade": 100.0}, "totalValue": 800.0}

    def get_open_orders(self):
        return []

    def get_positions(self):
        return [{
            "instrument": {"ticker": "AAPL_US_EQ", "currency": "USD"},
            "quantity": 0.7, "currentPrice": 300.0, "averagePricePaid": 338.0,
            "createdAt": "2026-09-14T16:30:00.000+03:00",
            "walletImpact": {"currency": "CHF", "currentValue": 170.0, "totalCost": 194.0},
        }]

    def place_market_order(self, ticker, quantity):
        FakeClient.placed.append((ticker, quantity))
        return {"id": 4711, "status": "NEW"}


def _sig(signal, close):
    return SignalResult(
        t212_ticker="AAPL_US_EQ", yahoo_symbol="AAPL", signal=signal, close=close,
        sma50=290.0, sma200=250.0, high_20d_prev=340.0, rsi14=45.0, reason=f"Testsignal {signal}",
        closes=_closes([338, 345, 330, close], start="2026-09-14"),
    )


def _run(signal, close, execute):
    tmp = Path(tempfile.mkdtemp())
    lp = tmp / "ledger.csv"
    ledger.record_opening_balance(1000, 1.0, path=lp)
    ledger.record_buy("AAPL_US_EQ", 0.7, 280.0, path=lp)
    FakeClient.placed = []
    saved = (auto_trade.T212Client, auto_trade.get_signals, auto_trade.log_entry,
             ledger.path_for_env, risk_monitor.path_for_env)
    try:
        auto_trade.T212Client = FakeClient
        auto_trade.get_signals = lambda: [_sig(signal, close)]
        auto_trade.log_entry = lambda **kw: None
        ledger.path_for_env = lambda env: lp
        risk_monitor.path_for_env = lambda env: tmp / "equity.csv"
        return auto_trade.run("live", execute)
    finally:
        (auto_trade.T212Client, auto_trade.get_signals, auto_trade.log_entry,
         ledger.path_for_env, risk_monitor.path_for_env) = saved


def test_run_sells_on_trailing_stop_even_with_hold_signal():
    # Hoch 345, Schluss 300 <= 310.5 -> Trailing, obwohl Signal HOLD
    res = _run("HOLD", 300.0, execute=True)
    assert len(res["actions"]) == 1
    a = res["actions"][0]
    assert a["side"] == "sell" and a["reason"].startswith("Trailing-Stop")
    assert FakeClient.placed == [("AAPL_US_EQ", -0.7)]
    assert res["stop_status"][0]["triggered"]


def test_run_dry_run_sends_nothing():
    res = _run("HOLD", 300.0, execute=False)
    assert res["actions"] and FakeClient.placed == []


def test_run_no_stop_no_action():
    res = _run("HOLD", 335.0, execute=True)  # Hoch 345 -> Level 310.5, Schluss 335 ok
    assert res["actions"] == [] and FakeClient.placed == []
    assert res["stop_status"][0]["triggered"] is None


def test_run_sma50_sell_still_works():
    res = _run("SELL", 335.0, execute=True)
    assert res["actions"][0]["reason"] == "Testsignal SELL"
    assert FakeClient.placed == [("AAPL_US_EQ", -0.7)]


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
