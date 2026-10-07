"""Netzwerkfreie Tests fuer backtest.py. Aufruf: python tests/test_backtest.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import backtest as bt  # noqa: E402
from signals import compute_signal_from_history  # noqa: E402


def _synthetic(n=900, seed=1, drift=0.0006, vol=0.02) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    close = 100 * np.exp(np.cumsum(rets))
    open_ = close * (1 + rng.normal(0, 0.003, n))
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.DataFrame({"Open": open_, "Close": close}, index=idx)


def test_vectorised_signals_match_signals_py():
    df = _synthetic(600, seed=3)
    ind = bt.compute_indicators(df)
    checked = 0
    for i in range(199, len(df), 7):
        res = compute_signal_from_history(df.iloc[: i + 1])
        row = ind.iloc[i]
        expected = "BUY" if row["buy"] else ("SELL" if row["sell"] else "HOLD")
        assert res.signal == expected, (i, res.signal, expected)
        assert abs(res.pct_above_breakout - row["pct_above"]) < 1e-9
        checked += 1
    assert checked > 40


def test_signals_invalid_before_warmup():
    ind = bt.compute_indicators(_synthetic(300))
    assert not ind["valid"].iloc[:199].any()
    assert ind["valid"].iloc[199:].all()
    assert not ind["buy"].iloc[:199].any()


def _universe(n=900, drift=0.0006):
    return {t: bt.compute_indicators(_synthetic(n, seed=10 + i, drift=drift))
            for i, t in enumerate(["A", "B", "C", "D", "E"])}


def test_simulation_invariants():
    ind = _universe()
    res = bt.simulate(ind, bt.Params(start_capital=1000.0))
    assert res.equity.notna().all()
    assert res.cash > -1e-6
    assert len(res.open_positions) <= 2
    assert res.exposure.max() <= 1.0 + 1e-9
    # Endwert == Cash + offene Positionen zum letzten Schluss
    last_close = {t: ind[t]["close"].iloc[-1] for t in ind}
    expected = res.cash + sum(p["qty"] * last_close[t] for t, p in res.open_positions.items())
    assert abs(res.equity.iloc[-1] - expected) < 1e-6


def test_max_two_positions_at_any_time():
    ind = _universe(1200, drift=0.001)
    res = bt.simulate(ind, bt.Params(start_capital=1000.0))
    assert res.max_open <= bt.ap.MAX_OPEN_POSITIONS
    assert len(res.trades) > 0


def test_trade_accounting_matches_equity_with_zero_costs():
    ind = _universe(1200, drift=0.001)
    p = bt.Params(start_capital=1000.0, cost_per_side=0.0)
    res = bt.simulate(ind, p)
    realized = sum(t["pnl"] for t in res.trades)
    last_close = {t: ind[t]["close"].iloc[-1] for t in ind}
    unrealized = sum(pos["qty"] * (last_close[t] - pos["entry_price"])
                     for t, pos in res.open_positions.items())
    assert abs(res.equity.iloc[-1] - (1000.0 + realized + unrealized)) < 1e-6


def test_costs_reduce_result():
    ind = _universe(1200, drift=0.001)
    free = bt.simulate(ind, bt.Params(start_capital=1000.0, cost_per_side=0.0))
    paid = bt.simulate(ind, bt.Params(start_capital=1000.0, cost_per_side=0.01))
    if free.trades:
        assert paid.equity.iloc[-1] <= free.equity.iloc[-1] + 1e-9


def test_stops_exit_reason_present():
    ind = _universe(1500, drift=0.0003, )
    res = bt.simulate(ind, bt.Params(start_capital=1000.0, stop_loss=0.05, trailing_stop=0.04))
    reasons = {t["reason"] for t in res.trades}
    assert reasons <= {"SMA50", "Stop-Loss", "Trailing-Stop"}


def test_max_drawdown_known_series():
    s = pd.Series([100, 120, 90, 110], index=pd.bdate_range("2024-01-01", periods=4))
    assert abs(bt.max_drawdown(s) - (90 / 120 - 1)) < 1e-12


def test_trade_stats_basic():
    trades = [
        {"pnl": 10.0, "ret": 0.10, "days": 10},
        {"pnl": -5.0, "ret": -0.05, "days": 20},
        {"pnl": 5.0, "ret": 0.05, "days": 30},
    ]
    st = bt.trade_stats(trades)
    assert st["n"] == 3
    assert abs(st["win_rate"] - 2 / 3) < 1e-12
    assert abs(st["profit_factor"] - 15 / 5) < 1e-12
    assert abs(st["avg_days"] - 20) < 1e-12


def test_yearly_returns_chain_to_total():
    idx = pd.bdate_range("2022-06-01", "2024-03-01")
    s = pd.Series(np.linspace(100, 160, len(idx)), index=idx)
    yr = bt.yearly_returns(s)
    total = (1 + yr).prod() - 1
    assert abs(total - (s.iloc[-1] / s.iloc[0] - 1)) < 1e-9


def test_report_runs_end_to_end_on_synthetic_data():
    # Voll-Report mit synthetischen Daten fuer alle Ticker + Benchmarks
    from signals import UNIVERSE
    data = {}
    for i, sym in enumerate(list(UNIVERSE.values()) + bt.BENCHMARKS):
        data[sym] = _synthetic(1300, seed=100 + i, drift=0.0007)
    import tempfile
    bt.OUT_DIR = Path(tempfile.mkdtemp())
    text = bt.build_report(data, 324.5, 0.002)
    assert "# Backtest" in text and "LIVE-Regeln" in text and "Buy&Hold SPY" in text
    assert (bt.OUT_DIR / "equity_curves.csv").exists()


def _synthetic_data(n=1300):
    from signals import UNIVERSE
    return {sym: _synthetic(n, seed=100 + i, drift=0.0007)
            for i, sym in enumerate(list(UNIVERSE.values()) + bt.BENCHMARKS)}


def test_slot_parameters_are_respected():
    ind = _universe(1300, drift=0.001)
    for slots, frac in [(1, 0.8), (3, 0.30), (4, 0.22)]:
        res = bt.simulate(ind, bt.Params(start_capital=1000.0, max_positions=slots, position_fraction=frac))
        assert res.max_open <= slots, (slots, res.max_open)
        assert res.cash > -1e-6


def test_sensitivity_table_has_all_configs_and_report_flags_work():
    import tempfile
    bt.OUT_DIR = Path(tempfile.mkdtemp())
    text = bt.build_report(_synthetic_data(), 324.5, 0.002, max_positions=3, fraction=0.30, sensitivity=True)
    assert "max. 3 Positionen a 30%" in text
    assert "## Sensitivitaet" in text
    for slots, frac in bt.SLOT_CONFIGS:
        assert f"| {slots} x {frac*100:.0f}%" in text


def test_default_report_has_no_sensitivity_and_uses_policy_defaults():
    import tempfile
    bt.OUT_DIR = Path(tempfile.mkdtemp())
    text = bt.build_report(_synthetic_data(), 324.5, 0.002)
    assert "## Sensitivitaet" not in text
    assert f"max. {bt.ap.MAX_OPEN_POSITIONS} Positionen a {bt.ap.POSITION_FRACTION*100:.0f}%" in text
    assert (bt.OUT_DIR / "trades_live.csv").exists()


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
