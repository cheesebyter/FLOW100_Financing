"""
Automatisierte Ausfuehrung des regelbasierten Trading-Systems (siehe
STRATEGY.md, Abschnitt "Automatisierungs-Policy"). Deckt die Schritte
1-5 des in README.md beschriebenen Ablaufs in einem Lauf ab:

  1. Signale lesen        (signals.get_signals())
  2. Beurteilen           (auto_policy.is_actionable_buy() + Sell-Guard)
  3. Positionsgroesse     (auto_policy.compute_buy_quantity())
  4. Trockenlauf          (immer geloggt, auch ohne --execute)
  5. Order platzieren     (nur mit --execute)

Bewusst NICHT Teil dieses Skripts: Warten auf den Fill und die
Ledger-Buchung (Schritt 6/7). Market-Orders ausserhalb der Handelszeiten
fuellen sich verzoegert -- das uebernimmt die aufrufende Claude-Session
im Scheduled Task (pollt 'python t212_cli.py --env <env> order <id>' und
bucht danach ueber 'python t212_cli.py --env <env> ledger buy/sell ...').

Ausgabe: menschenlesbarer Bericht + letzte Zeile 'SUMMARY_JSON: {...}'
(maschinenlesbar fuer die aufrufende Session).

Ohne --execute: reiner Trockenlauf, es wird NICHTS an Trading212
gesendet (wird trotzdem wie gewohnt geloggt/berichtet).

Rollenverteilung (Andys Entscheidung, 22.09.2026): Dieses Skript ist die
mechanische Sicherheitsschicht -- Filter-Schwellen sind feste Zahlen,
keine Ad-hoc-Einschaetzung zur Laufzeit. Die ausfuehrende Claude-Session
legt zusaetzlich eine kurze Plausibilitaetspruefung auf das Ergebnis
(z.B. offensichtlich fehlerhafte Kursdaten) und kann einen mechanisch
erlaubten Trade ablehnen, aber nie einen mechanisch verbotenen Trade
erlauben.
"""

from __future__ import annotations

import argparse
import json
import sys

import ledger
import risk_monitor
from auto_policy import (
    MAX_OPEN_POSITIONS,
    compute_buy_quantity,
    count_open_positions,
    has_open_order,
    is_actionable_buy,
    is_drawdown_alert,
)
from signals import get_signals
from t212_client import (RateLimitError, T212ApiError, T212Client,
                         find_position, position_price_chf)
from trade_logger import log_entry


def _current_price_chf(client: T212Client, ticker: str, fallback_close_usd: float) -> float:
    """Bester verfuegbarer Referenzpreis (Kontowaehrung CHF) fuer die
    Sizing-Berechnung. Existiert bereits eine Position fuer den Ticker,
    wird deren currentPrice (Kontowaehrung) verwendet. Sonst wird der
    Yahoo-Schlusskurs (USD) unveraendert als Naeherung uebernommen.

    Bewusste Vereinfachung: Bei USD/CHF < 1 (aktuell ~0.81) ist der
    USD-Zahlenwert GROESSER als der wahre CHF-Preis. Wird er faelschlich
    als CHF-Preis verwendet, ergibt die Sizing-Formel eine KLEINERE Menge
    als eigentlich zum Zielanteil gehoeren wuerde -- der Fehler wirkt also
    konservativ (zu wenig investiert, nie zu viel). Die tatsaechliche
    Order wird ohnehin zu Marktpreis ausgefuehrt; nur die Sizing-Schaetzung
    ist betroffen."""
    try:
        positions = client.get_positions()
        held = find_position(positions, ticker)
        if held:
            price_chf = position_price_chf(held)
            if price_chf:
                return price_chf
    except (T212ApiError, RateLimitError):
        pass
    return fallback_close_usd


def run(env: str, execute: bool) -> dict:
    client = T212Client(environment=env)
    ledger_path = ledger.path_for_env(env)
    equity_path = risk_monitor.path_for_env(env)

    summary = client.get_account_summary()
    available_to_trade = float(summary.get("cash", {}).get("availableToTrade", 0.0))
    total_value = float(summary.get("totalValue", 0.0))

    equity_point = risk_monitor.record_point(total_value, path=equity_path)
    drawdown_alert = is_drawdown_alert(equity_point["drawdown_pct"])

    report = ledger.build_report(path=ledger_path)
    open_orders = client.get_open_orders()

    try:
        signal_results = get_signals()
    except Exception as exc:  # z.B. kein Netzwerkzugriff auf Yahoo Finance
        return {
            "env": env, "execute": execute,
            "error": f"Signale konnten nicht geladen werden: {exc}",
            "equity": equity_point, "drawdown_alert": drawdown_alert,
        }

    actions: list[dict] = []
    skipped: list[dict] = []
    open_positions_count = count_open_positions(report.open_positions)

    for sig in signal_results:
        ticker = sig.t212_ticker
        held_qty = report.open_positions.get(ticker, 0.0)

        # --- SELL: Position dieses Experiments schliessen ---
        if sig.signal == "SELL" and held_qty > 1e-9:
            if has_open_order(open_orders, ticker):
                skipped.append({"ticker": ticker, "side": "sell", "reason": "Bereits offene Order fuer diesen Ticker"})
                continue
            positions = client.get_positions()
            held = find_position(positions, ticker)
            account_qty = held.get("quantity", 0.0) if held else 0.0
            sell_qty = round(min(account_qty, held_qty), 6)
            if sell_qty <= 1e-9:
                skipped.append({"ticker": ticker, "side": "sell", "reason": "Kein tatsaechlicher Bestand mehr (Konto=0 oder Ledger=0)"})
                continue

            action = {"ticker": ticker, "side": "sell", "quantity": sell_qty, "reason": sig.reason}
            order_id = ""
            if execute:
                result = client.place_market_order(ticker, -sell_qty)
                order_id = str(result.get("id", ""))
                action["order_id"] = order_id
                action["order_status"] = result.get("status", "")
            # WICHTIG: log_entry() erst NACH der Order-Platzierung, damit die
            # order_id mitgeschrieben wird -- sonst kann book_fills.py die
            # Order spaeter nicht finden (Bug, behoben 25.09.2026, siehe
            # STRATEGY.md).
            log_entry(
                environment=env, action="sell", ticker=ticker, order_type="market",
                quantity=sell_qty, order_id=order_id,
                status="dry_run" if not execute else "placed_pending",
                rationale=f"Auto-Trade: {sig.reason}",
            )
            actions.append(action)
            continue

        # --- BUY: neue Position eroeffnen ---
        if sig.signal == "BUY":
            ok, reason = is_actionable_buy(sig)
            if not ok:
                skipped.append({"ticker": ticker, "side": "buy", "reason": reason})
                continue
            if held_qty > 1e-9:
                skipped.append({"ticker": ticker, "side": "buy", "reason": "Bereits offene Position fuer diesen Ticker im Ledger"})
                continue
            if open_positions_count >= MAX_OPEN_POSITIONS:
                skipped.append({"ticker": ticker, "side": "buy", "reason": f"Max. {MAX_OPEN_POSITIONS} offene Positionen bereits erreicht"})
                continue
            if has_open_order(open_orders, ticker):
                skipped.append({"ticker": ticker, "side": "buy", "reason": "Bereits offene Order fuer diesen Ticker"})
                continue

            price_ref = _current_price_chf(client, ticker, sig.close)
            sizing = compute_buy_quantity(
                price_chf=price_ref, ledger_cash_chf=report.cash_balance,
                ledger_total_value_chf=report.total_ledger_value_at_cost,
                api_available_to_trade_chf=available_to_trade,
            )
            if sizing.quantity <= 0:
                skipped.append({"ticker": ticker, "side": "buy", "reason": sizing.skip_reason})
                continue

            action = {
                "ticker": ticker, "side": "buy", "quantity": sizing.quantity,
                "notional_chf_est": sizing.notional_chf, "reason": sig.reason,
            }
            order_id = ""
            if execute:
                result = client.place_market_order(ticker, sizing.quantity)
                order_id = str(result.get("id", ""))
                action["order_id"] = order_id
                action["order_status"] = result.get("status", "")
                open_positions_count += 1
            # WICHTIG: log_entry() erst NACH der Order-Platzierung, siehe
            # Kommentar im SELL-Zweig oben.
            log_entry(
                environment=env, action="buy", ticker=ticker, order_type="market",
                quantity=sizing.quantity, order_id=order_id,
                status="dry_run" if not execute else "placed_pending",
                rationale=f"Auto-Trade: {sig.reason}",
            )
            actions.append(action)
            continue

    return {
        "env": env,
        "execute": execute,
        "equity": equity_point,
        "drawdown_alert": drawdown_alert,
        "available_to_trade_chf": available_to_trade,
        "open_positions_count": open_positions_count,
        "signals": [
            {"ticker": s.t212_ticker, "signal": s.signal, "close": s.close, "rsi14": s.rsi14, "reason": s.reason}
            for s in signal_results
        ],
        "actions": actions,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatisierter Signal->Order-Lauf (siehe STRATEGY.md)")
    parser.add_argument("--env", choices=["live", "demo"], default="demo")
    parser.add_argument("--execute", action="store_true", help="Echte Orders senden (ohne dieses Flag: reiner Trockenlauf)")
    args = parser.parse_args()

    try:
        result = run(args.env, args.execute)
    except (T212ApiError, RateLimitError) as exc:
        print(f"Fehler: {exc}")
        sys.exit(1)

    print(f"=== Auto-Trade Lauf ({result['env']}, execute={result['execute']}) ===")
    if "error" in result:
        print(result["error"])
        print("SUMMARY_JSON: " + json.dumps(result))
        sys.exit(1)

    dd_note = "  *** DRAWDOWN-ALARM (-25%-Trigger) ***" if result["drawdown_alert"] else ""
    print(
        f"Equity: {result['equity']['total_value_chf']} CHF "
        f"(Peak: {result['equity']['peak_to_date_chf']} CHF, "
        f"Drawdown: {result['equity']['drawdown_pct'] * 100:.2f}%){dd_note}"
    )
    print(
        f"Verfuegbares Cash (API): {result['available_to_trade_chf']:.2f} CHF | "
        f"Offene Ledger-Positionen: {result['open_positions_count']}"
    )
    print()
    print("Signale:")
    for s in result["signals"]:
        print(f"  {s['ticker']:15s} {s['signal']:5s} close={s['close']:.2f} rsi14={s['rsi14']:.1f}  {s['reason']}")
    print()
    if result["actions"]:
        print("Ausgefuehrte/vorgeschlagene Aktionen:")
        for a in result["actions"]:
            print(f"  {a}")
    else:
        print("Keine Aktionen (kein aktionables Signal).")
    if result["skipped"]:
        print()
        print("Uebersprungen:")
        for s in result["skipped"]:
            print(f"  {s['ticker']:15s} {s['side']:4s} -- {s['reason']}")

    print()
    print("SUMMARY_JSON: " + json.dumps(result))


if __name__ == "__main__":
    main()
