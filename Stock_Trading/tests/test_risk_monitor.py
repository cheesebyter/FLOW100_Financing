"""
Tests fuer risk_monitor.py -- Equity-Kurve + Drawdown-Berechnung.
Ohne pytest lauffaehig: python tests/test_risk_monitor.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import risk_monitor


def _tmp_path() -> Path:
    fd = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    fd.close()
    p = Path(fd.name)
    p.unlink()  # record_point soll die Datei selbst anlegen
    return p


def test_first_point_has_zero_drawdown():
    path = _tmp_path()
    row = risk_monitor.record_point(100.0, path=path)
    assert row["peak_to_date_chf"] == 100.0
    assert row["drawdown_pct"] == 0.0
    path.unlink()


def test_new_high_updates_peak_and_zero_drawdown():
    path = _tmp_path()
    risk_monitor.record_point(100.0, path=path)
    row = risk_monitor.record_point(120.0, path=path)
    assert row["peak_to_date_chf"] == 120.0
    assert row["drawdown_pct"] == 0.0
    path.unlink()


def test_drop_below_peak_computes_negative_drawdown():
    path = _tmp_path()
    risk_monitor.record_point(100.0, path=path)
    risk_monitor.record_point(120.0, path=path)
    row = risk_monitor.record_point(90.0, path=path)
    assert row["peak_to_date_chf"] == 120.0
    # 90/120 - 1 = -0.25
    assert row["drawdown_pct"] == -0.25
    path.unlink()


def test_path_for_env_separates_live_and_demo():
    assert risk_monitor.path_for_env("live").name == "equity_live.csv"
    assert risk_monitor.path_for_env("demo").name == "equity_demo.csv"
    try:
        risk_monitor.path_for_env("prod")
        assert False, "sollte ValueError werfen"
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
