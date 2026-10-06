"""Netzwerkfreier Test fuer den Verkaufs-Schutz in t212_cli.py.

Hintergrund (siehe STRATEGY.md "Ledger"): Das Live-Konto haelt auch private
Positionen, u.a. bereits 0.35 NVDA seit Juli 2025 -- unabhaengig von diesem
Experiment. Der Schutz muss verhindern, dass ueber dieses Tool mehr verkauft
wird, als das Experiment laut Ledger tatsaechlich selbst gekauft hat, selbst
wenn das Konto insgesamt mehr haelt.

Aufruf: python tests/test_sell_guardrail.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ledger  # noqa: E402
from t212_cli import _max_sellable_quantity  # noqa: E402


class FakeClient:
    """Simuliert T212Client.get_positions() ohne Netzwerkaufruf."""

    def __init__(self, positions):
        self._positions = positions

    def get_positions(self):
        return self._positions


def _tmp_ledger_path() -> Path:
    fd, name = tempfile.mkstemp(suffix=".csv")
    p = Path(name)
    p.unlink()
    return p


def test_overlap_with_preexisting_private_position_caps_at_ledger_qty():
    # Exakt das reale Szenario: Konto haelt 0.35 NVDA privat + 0.2 aus dem
    # Experiment (insgesamt 0.55), Ledger kennt nur die 0.2 aus dem Experiment.
    path = _tmp_ledger_path()
    ledger.record_opening_balance(250, 0.81, path=path)
    ledger.record_buy("NVDA_US_EQ", 0.2, 188.80, path=path)

    client = FakeClient([{"ticker": "NVDA_US_EQ", "quantity": 0.55}])
    allowed, held, ledger_qty = _max_sellable_quantity(client, "NVDA_US_EQ", ledger_path=path)

    assert held == 0.55
    assert abs(ledger_qty - 0.2) < 1e-9
    assert abs(allowed - 0.2) < 1e-9, "Erlaubte Menge muss auf die Ledger-Menge begrenzt sein"


def test_selling_more_than_ledger_owns_would_be_rejected_by_caller():
    path = _tmp_ledger_path()
    ledger.record_opening_balance(250, 0.81, path=path)
    ledger.record_buy("NVDA_US_EQ", 0.2, 188.80, path=path)

    client = FakeClient([{"ticker": "NVDA_US_EQ", "quantity": 0.55}])
    allowed, _, _ = _max_sellable_quantity(client, "NVDA_US_EQ", ledger_path=path)

    requested = 0.5  # weniger als das Konto haelt, aber mehr als das Ledger dem Experiment zuordnet
    assert requested > allowed, "Der Aufrufer (_place_order) muss diesen Fall ablehnen"


def test_no_ledger_position_means_nothing_sellable_even_if_account_holds_shares():
    path = _tmp_ledger_path()
    ledger.record_opening_balance(250, 0.81, path=path)  # keine Kaeufe

    # Konto haelt privat 0.16 MSFT, das Experiment hat aber nie MSFT gekauft.
    client = FakeClient([{"ticker": "MSFT_US_EQ", "quantity": 0.16}])
    allowed, held, ledger_qty = _max_sellable_quantity(client, "MSFT_US_EQ", ledger_path=path)

    assert held == 0.16
    assert ledger_qty == 0.0
    assert allowed == 0.0


def test_ticker_not_held_at_all():
    path = _tmp_ledger_path()
    ledger.record_opening_balance(250, 0.81, path=path)
    client = FakeClient([])
    allowed, held, ledger_qty = _max_sellable_quantity(client, "TSLA_US_EQ", ledger_path=path)
    assert (allowed, held, ledger_qty) == (0.0, 0.0, 0.0)


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASSED")
