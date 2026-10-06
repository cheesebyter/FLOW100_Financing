"""
Tests fuer book_fills.py -- reine Entscheidungs-/Hilfsfunktionen, ohne
Netzwerk (siehe book_fills.py Docstring fuer die Gesamtlogik).
Ohne pytest lauffaehig: python tests/test_book_fills.py
"""

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from book_fills import _booked_order_ids, _extract_fill_price, _flatten_history_entry, classify_order


def test_classify_filled():
    order = {"status": "FILLED", "filledQuantity": 0.33}
    assert classify_order(order, expected_qty=0.33) == "filled"


def test_classify_open_when_zero_filled():
    order = {"status": "NEW", "filledQuantity": 0}
    assert classify_order(order, expected_qty=0.33) == "open"


def test_classify_cancelled():
    for status in ("CANCELLED", "REJECTED", "EXPIRED"):
        order = {"status": status, "filledQuantity": 0}
        assert classify_order(order, expected_qty=0.33) == "cancelled"


def test_classify_partial_fill_counts_as_filled():
    order = {"status": "NEW", "filledQuantity": 0.1}
    assert classify_order(order, expected_qty=0.33) == "filled"


def test_extract_fill_price_prefers_first_matching_key():
    order = {"averagePrice": 269.5, "price": 999}
    price, source = _extract_fill_price(order)
    assert price == 269.5
    assert "averagePrice" in source


def test_extract_fill_price_none_when_absent():
    price, source = _extract_fill_price({"status": "FILLED"})
    assert price is None


def test_booked_order_ids_reads_existing_ledger():
    fd = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(fd, fieldnames=["order_id", "ticker"])
    writer.writeheader()
    writer.writerow({"order_id": "123", "ticker": "AAPL_US_EQ"})
    writer.writerow({"order_id": "", "ticker": "AMD_US_EQ"})
    fd.close()
    path = Path(fd.name)
    try:
        assert _booked_order_ids(path) == {"123"}
    finally:
        path.unlink()


def test_booked_order_ids_missing_file_returns_empty_set():
    path = Path(tempfile.gettempdir()) / "does_not_exist_ledger.csv"
    if path.exists():
        path.unlink()
    assert _booked_order_ids(path) == set()


def test_flatten_history_entry_matches_real_t212_response():
    # Reale Antwort von get_order_history() vom 24.09.2026 (Order 57762436136,
    # die faelschlich als 404 quittiert worden war -- siehe STRATEGY.md).
    entry = {
        "order": {
            "id": 57762436136, "ticker": "AAPL_US_EQ", "quantity": 0.33,
            "filledQuantity": 0.33, "status": "FILLED", "side": "BUY",
        },
        "fill": {
            "quantity": 0.33, "price": 341.26,
            "walletImpact": {"currency": "CHF", "netValue": 92.79, "fxRate": 1.21549703},
        },
    }
    flat = _flatten_history_entry(entry)
    assert flat["id"] == 57762436136
    assert flat["status"] == "FILLED"
    assert flat["filledQuantity"] == 0.33
    # 92.79 / 0.33 = 281.1818... CHF pro Stueck (inkl. FX-Gebuehr), NICHT
    # der USD-Rohpreis 341.26 aus fill.price.
    assert abs(flat["price_chf_per_share"] - (92.79 / 0.33)) < 1e-9

    price, source = _extract_fill_price(flat)
    assert abs(price - (92.79 / 0.33)) < 1e-9
    assert "price_chf_per_share" in source

    assert classify_order(flat, expected_qty=0.33) == "filled"


def test_flatten_history_entry_handles_sell_side_negative_quantity():
    entry = {
        "order": {"id": 1, "ticker": "AAPL_US_EQ", "quantity": -0.36, "filledQuantity": -0.36, "status": "FILLED", "side": "SELL"},
        "fill": {"quantity": -0.36, "price": 312.22, "walletImpact": {"currency": "CHF", "netValue": 91.55}},
    }
    flat = _flatten_history_entry(entry)
    assert flat["price_chf_per_share"] > 0  # abs() angewandt, kein negativer Preis


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
