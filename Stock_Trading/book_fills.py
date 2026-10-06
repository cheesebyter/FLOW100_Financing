"""
Prueft alle vom automatisierten Lauf (auto_trade.py --execute) platzierten,
aber noch nicht im Ledger verbuchten Orders auf ihren Fuellstatus und
verbucht sie bei Fill automatisch (Schritte 6+7 aus README.md).

Gedacht fuer einen TAEGLICHEN Lauf per Windows-Aufgabenplanung, getrennt
vom WOECHENTLICHEN auto_trade.py-Lauf -- Market-Orders ausserhalb der
Handelszeiten fuellen sich oft erst Stunden/einen Tag spaeter (siehe
Erfahrung mit den ersten Live-Tests, Sept. 2026).

Erkennung "noch nicht verbucht": Eintrag in logs/trades_*.csv mit
status=='placed_pending' UND dessen order_id (noch) nicht als order_id in
ledger_<env>.csv auftaucht UND kein vorheriger 'ack_*'-Eintrag fuer dieselbe
order_id existiert (verhindert wiederholte Alarme fuer bereits zur
Kenntnis genommene Cancel/Reject-Faelle).

Bekannte Vereinfachung: Bei einem TEIL-Fill wird nur die zu diesem
Zeitpunkt gefuellte Menge einmalig gebucht; ein spaeterer Nachfuell-Fill
auf dieselbe Order-ID wird NICHT automatisch nachgebucht (die order_id
gilt danach als "verbucht"). Das ist bei kleinen Bruchstueck-Aktien-Orders
auf liquide Large-Caps ein seltener Fall -- wird hier bewusst nicht
weiter automatisiert, um die Logik einfach/nachvollziehbar zu halten.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
import time
from pathlib import Path

import ledger
import risk_monitor
from t212_client import (RateLimitError, T212ApiError, T212Client,
                         find_position, position_price_chf)
from trade_logger import LOG_DIR, log_entry

# 'price_chf_per_share' kommt aus _flatten_history_entry() (echter CHF-Preis
# inkl. FX-Gebuehr) -- hat Vorrang vor den anderen Kandidaten, die aus
# Live-Order-Antworten stammen und ggf. in Fremdwaehrung vorliegen.
FILL_PRICE_CANDIDATE_KEYS = ("price_chf_per_share", "fillPrice", "averageFillPrice", "averagePrice", "filledPrice", "price")


def _read_all_trade_logs(env: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(glob.glob(str(LOG_DIR / "trades_*.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("environment") == env:
                    rows.append(row)
    return rows


def _booked_order_ids(ledger_path: Path) -> set[str]:
    if not ledger_path.exists():
        return set()
    with ledger_path.open(newline="", encoding="utf-8") as f:
        return {r["order_id"] for r in csv.DictReader(f) if r.get("order_id")}


# Live-Orders (get_order()) fuehren 'filledQuantity'. Historische Orders
# (get_order_history(), Fallback bei 404) koennten laut oeffentlicher Doku
# stattdessen 'quantity' oder 'executedQuantity' fuer die tatsaechlich
# ausgefuehrte Menge nutzen -- ungetestet gegen die echte API (siehe
# t212_client.get_order_history()-Docstring), deshalb mehrere Kandidaten.
FILLED_QUANTITY_CANDIDATE_KEYS = ("filledQuantity", "executedQuantity", "quantity")


def _filled_quantity(order: dict) -> float:
    for key in FILLED_QUANTITY_CANDIDATE_KEYS:
        val = order.get(key)
        if val:
            return abs(float(val))
    return 0.0


def _flatten_history_entry(entry: dict) -> dict:
    """Normalisiert einen Eintrag aus get_order_history() (verschachtelt:
    {'order': {...}, 'fill': {...}}, bestaetigt gegen die echte API am
    24.09.2026) in ein flaches Dict mit denselben Feldnamen wie eine
    Live-Order aus get_order() -- damit classify_order()/_filled_quantity()/
    _extract_fill_price() beide Formate verarbeiten koennen. Der Preis wird
    aus fill.walletImpact.netValue / fill.quantity berechnet (echter
    CHF-Preis pro Stueck INKL. Waehrungsumrechnungsgebuehr, Kontowaehrung)
    statt fill.price zu nehmen, das in der Instrumentenwaehrung (z.B. USD)
    vorliegt und ohne Gebuehr ist."""
    order = dict(entry.get("order", {}))
    fill = entry.get("fill", {})
    fill_qty = fill.get("quantity")
    net_value = fill.get("walletImpact", {}).get("netValue")
    if fill_qty:
        order.setdefault("filledQuantity", fill_qty)
    if fill_qty and net_value:
        order["price_chf_per_share"] = abs(net_value / fill_qty)
    return order


def classify_order(order: dict, expected_qty: float) -> str:
    """Reine Entscheidungsfunktion (testbar ohne Netzwerk): 'filled',
    'cancelled' oder 'open', je nach Order-Status/Fuellmenge."""
    status = str(order.get("status", "")).upper()
    if status in ("CANCELLED", "REJECTED", "EXPIRED"):
        return "cancelled"
    if _filled_quantity(order) > 1e-9:
        return "filled"
    return "open"


def _extract_fill_price(order: dict) -> tuple[float | None, str]:
    for key in FILL_PRICE_CANDIDATE_KEYS:
        val = order.get(key)
        if val:
            return float(val), f"aus Order-Feld '{key}'"
    return None, ""


def _fallback_price_from_position(client: T212Client, ticker: str) -> float | None:
    try:
        positions = client.get_positions()
    except (T212ApiError, RateLimitError):
        return None
    held = find_position(positions, ticker)
    if not held:
        return None
    price_chf = position_price_chf(held)  # CHF/Stueck (walletImpact), nicht USD-currentPrice
    return price_chf if price_chf else None


def run(env: str) -> dict:
    client = T212Client(environment=env)
    ledger_path = ledger.path_for_env(env)

    summary = client.get_account_summary()
    equity_point = risk_monitor.record_point(
        float(summary.get("totalValue", 0.0)), path=risk_monitor.path_for_env(env)
    )

    trade_rows = _read_all_trade_logs(env)
    booked_ids = _booked_order_ids(ledger_path)
    acked_ids = {r["order_id"] for r in trade_rows if r.get("status", "").startswith("ack_") and r.get("order_id")}

    # 'placed_pending' kommt von auto_trade.py, 'placed' vom manuellen
    # 'buy'/'sell'-Befehl in t212_cli.py -- book_fills.py bucht beides,
    # damit auch manuell abgesetzte Orders automatisch nachverbucht werden.
    pending = [
        r for r in trade_rows
        if r.get("status") in ("placed_pending", "placed")
        and r.get("order_id")
        and r["order_id"] not in booked_ids
        and r["order_id"] not in acked_ids
    ]

    booked: list[dict] = []
    still_open: list[dict] = []
    problems: list[dict] = []

    for i, row in enumerate(pending):
        order_id = row["order_id"]
        ticker = row["ticker"]
        action = row["action"]  # buy | sell
        expected_qty = float(row["quantity"])

        # T212 begrenzt Order-Detail-Abfragen recht eng (in der Praxis reicht
        # schon der zweite Call unmittelbar nacheinander fuer ein Rate-Limit-
        # 429) -- deshalb Pause zwischen mehreren Orders + ein Retry bei
        # RateLimitError, bevor der Fall als "problem" liegen bleibt.
        if i > 0:
            time.sleep(2.5)

        order = None
        not_found = False
        for attempt in range(2):
            try:
                order = client.get_order(order_id)
                break
            except RateLimitError:
                if attempt == 0:
                    time.sleep(5.0)
                    continue
                problems.append({"order_id": order_id, "ticker": ticker, "reason": "Rate-Limit erreicht, wird beim naechsten Lauf erneut geprueft"})
            except T212ApiError as exc:
                if exc.status_code == 404:
                    not_found = True
                else:
                    problems.append({"order_id": order_id, "ticker": ticker, "reason": f"Order-Abfrage fehlgeschlagen: {exc}"})
                break

        if not_found:
            # WICHTIG (korrigiert 24.09.2026): Ein 404 bei get_order() heisst
            # NICHT zuverlaessig "nie ausgefuehrt" -- bei den ersten Live-
            # Tests stellte sich heraus, dass laengst GEFUELLTE Orders vom
            # Live-Order-Endpunkt in die Historie wandern und dort 404
            # liefern. Deshalb zuerst in get_order_history() nachschauen,
            # bevor die Order als 'nicht auffindbar' quittiert wird.
            try:
                history = client.get_order_history(ticker=ticker, limit=50)
            except (T212ApiError, RateLimitError) as exc:
                problems.append({"order_id": order_id, "ticker": ticker, "reason": f"Order-Historie-Abfrage fehlgeschlagen: {exc}"})
                continue

            hist_entry = next(
                (o for o in history if str(o.get("order", {}).get("id", "")) == str(order_id)), None
            )
            hist_order = _flatten_history_entry(hist_entry) if hist_entry is not None else None
            if hist_order is None:
                # Wirklich nirgends auffindbar -- erst dann als vermutlich
                # abgelaufen quittieren.
                log_entry(
                    environment=env, action=action, ticker=ticker, order_id=order_id,
                    status="ack_not_found",
                    rationale=(
                        f"Order {order_id} weder live noch in der Historie (letzte {len(history)} "
                        f"Eintraege fuer {ticker}) auffindbar -- vermutlich unausgefuehrt abgelaufen. "
                        "Kein Fill, keine Ledger-Buchung. Einmalig quittiert."
                    ),
                )
                problems.append({"order_id": order_id, "ticker": ticker, "reason": "Weder live noch in Historie auffindbar -- vermutlich abgelaufen ohne Fill, quittiert"})
                continue

            order = hist_order

        if order is None:
            continue

        outcome = classify_order(order, expected_qty)

        if outcome == "cancelled":
            status = order.get("status", "")
            log_entry(
                environment=env, action=action, ticker=ticker, order_id=order_id,
                status=f"ack_{status.lower()}",
                rationale=f"Order {order_id} wurde {status} -- kein Fill, keine Ledger-Buchung. Manuell pruefen.",
            )
            problems.append({"order_id": order_id, "ticker": ticker, "reason": f"Order-Status {status}, nicht gefuellt"})
            continue

        if outcome == "open":
            still_open.append({"order_id": order_id, "ticker": ticker, "status": order.get("status", "")})
            continue

        filled_qty = _filled_quantity(order)
        price, source = _extract_fill_price(order)
        if price is None:
            price = _fallback_price_from_position(client, ticker)
            source = "Naeherung aus aktueller Position (averagePrice/currentPrice)"
        if price is None:
            problems.append({"order_id": order_id, "ticker": ticker, "reason": "Gefuellt, aber kein Preis ermittelbar -- manuell im Ledger nachtragen"})
            continue

        book_qty = round(min(filled_qty, expected_qty), 6)
        rationale = f"Auto-Booking nach Fill (Order {order_id}, Preis {source})"
        if action == "buy":
            ledger_row = ledger.record_buy(ticker, book_qty, price, rationale=rationale, order_id=order_id, path=ledger_path)
        else:
            ledger_row = ledger.record_sell(ticker, book_qty, price, rationale=rationale, order_id=order_id, path=ledger_path)

        log_entry(
            environment=env, action=action, ticker=ticker, order_id=order_id, quantity=book_qty,
            price=price, status="booked", rationale=rationale,
        )
        booked.append({"order_id": order_id, "ticker": ticker, "action": action, "quantity": book_qty, "price": price, "ledger_row": ledger_row})

        if filled_qty + 1e-9 < expected_qty:
            problems.append({
                "order_id": order_id, "ticker": ticker,
                "reason": (
                    f"Nur Teil-Fill: {filled_qty}/{expected_qty} gebucht. Restmenge wird NICHT "
                    f"automatisch nachgebucht (bekannte Vereinfachung) -- bei Bedarf manuell per "
                    f"'ledger {action} ... --order-id {order_id}' ergaenzen."
                ),
            })

    return {
        "env": env, "equity": equity_point,
        "booked": booked, "still_open": still_open, "problems": problems,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill-Status pruefen und offene Auto-Trades im Ledger verbuchen")
    parser.add_argument("--env", choices=["live", "demo"], default="demo")
    args = parser.parse_args()

    try:
        result = run(args.env)
    except (T212ApiError, RateLimitError) as exc:
        print(f"Fehler: {exc}")
        sys.exit(1)

    print(f"=== Book-Fills Lauf ({result['env']}) ===")
    print(f"Equity: {result['equity']['total_value_chf']} CHF (Drawdown: {result['equity']['drawdown_pct'] * 100:.2f}%)")
    print()
    if result["booked"]:
        print("Neu verbucht:")
        for b in result["booked"]:
            print(f"  {b['ticker']:15s} {b['action']:4s} {b['quantity']} @ {b['price']} (Order {b['order_id']})")
    else:
        print("Nichts neu zu verbuchen.")
    if result["still_open"]:
        print()
        print("Noch offen (naechster Lauf prueft erneut):")
        for o in result["still_open"]:
            print(f"  {o['ticker']:15s} Order {o['order_id']} Status={o['status']}")
    if result["problems"]:
        print()
        print("ACHTUNG -- manuell pruefen:")
        for p in result["problems"]:
            print(f"  {p['ticker']:15s} Order {p['order_id']} -- {p['reason']}")

    print()
    print("SUMMARY_JSON: " + json.dumps(result))


if __name__ == "__main__":
    main()
