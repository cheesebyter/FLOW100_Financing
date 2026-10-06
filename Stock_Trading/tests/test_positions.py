"""Netzwerkfreie Tests fuer die Positions-Helfer (echtes API-Format, Stand 09/2026).
Aufruf: python tests/test_positions.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from t212_client import find_position, position_price_chf, position_ticker  # noqa: E402

AAPL = {  # gekuerzt aus echter API-Antwort
    "instrument": {"ticker": "AAPL_US_EQ", "currency": "USD"},
    "quantity": 0.7, "currentPrice": 329.93,
    "walletImpact": {"currency": "CHF", "totalCost": 194.21, "currentValue": 192.62},
}
FLAT = {"ticker": "AMD_US_EQ", "quantity": 0.01, "currentPrice": 607.41}


def test_ticker_nested_and_flat():
    assert position_ticker(AAPL) == "AAPL_US_EQ"
    assert position_ticker(FLAT) == "AMD_US_EQ"


def test_find_position():
    assert find_position([AAPL, FLAT], "AAPL_US_EQ") is AAPL
    assert find_position([AAPL, FLAT], "TSLA_US_EQ") is None


def test_price_chf_uses_wallet_impact_not_usd_current_price():
    price = position_price_chf(AAPL)
    assert abs(price - 192.62 / 0.7) < 1e-9
    assert abs(price - 329.93) > 50  # nicht der USD-Kurs


def test_price_chf_none_without_wallet_impact():
    assert position_price_chf(FLAT) is None


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t(); print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
