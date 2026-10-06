"""Netzwerkfreie Tests fuer das Ledger (FIFO-Buchungslogik). Aufruf:
python tests/test_ledger.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ledger  # noqa: E402


def _tmp_path() -> Path:
    fd, name = tempfile.mkstemp(suffix=".csv")
    p = Path(name)
    p.unlink()  # nur den Pfad wollen, Datei soll von ledger.py neu angelegt werden
    return p


def test_opening_balance_sets_cash():
    path = _tmp_path()
    row = ledger.record_opening_balance(250, 0.82, path=path)
    assert row["cash_balance"] == 205.0
    r = ledger.build_report(path=path)
    assert r.cash_balance == 205.0
    assert r.total_ledger_value_at_cost == 205.0


def test_second_opening_balance_raises():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.82, path=path)
    try:
        ledger.record_opening_balance(250, 0.82, path=path)
        assert False, "sollte RuntimeError werfen"
    except RuntimeError:
        pass


def test_buy_reduces_cash_and_creates_position():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.82, path=path)  # 205.00 CHF
    ledger.record_buy("NVDA_US_EQ", 0.2, 188.80, path=path)  # -37.76
    r = ledger.build_report(path=path)
    assert abs(r.cash_balance - (205.0 - 37.76)) < 1e-6
    assert r.open_positions["NVDA_US_EQ"] == 0.2
    assert abs(r.open_positions_cost_basis["NVDA_US_EQ"] - 37.76) < 1e-6


def test_sell_without_position_raises():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.82, path=path)
    try:
        ledger.record_sell("NVDA_US_EQ", 0.1, 200.0, path=path)
        assert False, "sollte ValueError werfen (kein Bestand)"
    except ValueError:
        pass


def test_fifo_partial_sell_across_two_lots():
    path = _tmp_path()
    ledger.record_opening_balance(1000, 1.0, path=path)  # 1000.00 CHF
    ledger.record_buy("AAPL_US_EQ", 10, 100.0, path=path)   # Lot 1: 10 @ 100
    ledger.record_buy("AAPL_US_EQ", 10, 120.0, path=path)   # Lot 2: 10 @ 120
    # Verkauf von 15 Stueck: 10 aus Lot 1 (@100) + 5 aus Lot 2 (@120)
    row = ledger.record_sell("AAPL_US_EQ", 15, 150.0, path=path)
    expected_cost_basis = 10 * 100.0 + 5 * 120.0  # 1000 + 600 = 1600
    expected_proceeds = 15 * 150.0                 # 2250
    expected_realized_pl = expected_proceeds - expected_cost_basis  # 650
    assert abs(row["realized_pl"] - expected_realized_pl) < 1e-6

    r = ledger.build_report(path=path)
    # verbleibend: 5 Stueck aus Lot 2 @ 120
    assert abs(r.open_positions["AAPL_US_EQ"] - 5) < 1e-6
    assert abs(r.open_positions_cost_basis["AAPL_US_EQ"] - 5 * 120.0) < 1e-6
    assert abs(r.total_realized_pl - expected_realized_pl) < 1e-6


def test_sell_more_than_held_across_lots_raises():
    path = _tmp_path()
    ledger.record_opening_balance(1000, 1.0, path=path)
    ledger.record_buy("AAPL_US_EQ", 5, 100.0, path=path)
    try:
        ledger.record_sell("AAPL_US_EQ", 5.5, 150.0, path=path)
        assert False, "sollte ValueError werfen (Verkauf > Bestand)"
    except ValueError:
        pass


def test_deposit_adds_to_cash_without_touching_positions():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.82, path=path)  # 205.00 CHF
    ledger.record_buy("AAPL_US_EQ", 0.5, 190.0, path=path)  # -95.00 -> 110.00
    row = ledger.record_deposit(120.0, rationale="Restguthaben T212", path=path)
    assert row["type"] == "DEPOSIT"
    assert abs(row["cash_balance"] - 230.0) < 1e-6
    r = ledger.build_report(path=path)
    assert abs(r.cash_balance - 230.0) < 1e-6
    assert r.open_positions["AAPL_US_EQ"] == 0.5  # Position unveraendert


def test_deposit_without_opening_raises():
    path = _tmp_path()
    try:
        ledger.record_deposit(120.0, path=path)
        assert False, "sollte RuntimeError werfen"
    except RuntimeError:
        pass


def test_note_does_not_change_cash():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.82, path=path)
    before = ledger.build_report(path=path).cash_balance
    ledger.record_note("Testnotiz", path=path)
    after = ledger.build_report(path=path).cash_balance
    assert before == after


def _write_rows(path, rows):
    for r in rows:
        ledger._append(path, {**{k: "" for k in ledger.FIELDNAMES}, **r})


def test_market_value_and_none_when_price_missing():
    path = _tmp_path()
    ledger.record_opening_balance(1000, 1.0, path=path)
    ledger.record_buy("AAPL_US_EQ", 2, 100.0, path=path)  # cash 800
    r = ledger.build_report(path=path)
    assert ledger.market_value(r, {"AAPL_US_EQ": 110.0}) == 1020.0
    assert ledger.market_value(r, {}) is None


def test_total_contributions_includes_deposit():
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.8, path=path)  # 200
    ledger.record_deposit(120.0, path=path)
    r = ledger.build_report(path=path)
    assert abs(r.total_contributions - 320.0) < 1e-6


def test_modified_dietz_deposit_is_not_profit():
    from datetime import datetime, timezone
    path = _tmp_path()
    _write_rows(path, [
        {"timestamp_utc": "2026-01-01T00:00:00+00:00", "type": "OPENING",
         "amount": 100.0, "cash_balance": 100.0},
        {"timestamp_utc": "2026-01-11T00:00:00+00:00", "type": "DEPOSIT",
         "amount": 100.0, "cash_balance": 200.0},
    ])
    rows = ledger._read_all(path)
    end = datetime(2026, 1, 21, tzinfo=timezone.utc)
    # Ohne Gewinn: Endwert == Einzahlungen -> Rendite 0
    assert abs(ledger.modified_dietz(rows, 200.0, end)) < 1e-9
    # Gewinn 15: Nenner = 100 + 100*0.5 = 150 -> +10%
    assert abs(ledger.modified_dietz(rows, 215.0, end) - 0.10) < 1e-9


def test_modified_dietz_zero_span_is_none():
    from datetime import datetime, timezone
    path = _tmp_path()
    ledger.record_opening_balance(250, 0.8, path=path)
    rows = ledger._read_all(path)
    assert ledger.modified_dietz(rows, 200.0, datetime(2000, 1, 1, tzinfo=timezone.utc)) is None


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
