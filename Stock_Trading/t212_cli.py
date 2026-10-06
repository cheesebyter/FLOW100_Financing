"""
CLI fuer das FLOW100 Trading212-Setup.

Beispiele:
    python t212_cli.py --env demo status
    python t212_cli.py --env demo positions
    python t212_cli.py --env demo find AAPL
    python t212_cli.py --env live buy AAPL_US_EQ 1 --rationale "..."            (Trockenlauf)
    python t212_cli.py --env live buy AAPL_US_EQ 1 --rationale "..." --confirm  (echte Order)
    python t212_cli.py --env live log-decision --rationale "Kein Trade heute, Markt zu volatil"

Sicherheitsregeln:
- Standard-Umgebung ist 'demo'. '--env live' muss explizit gesetzt werden.
- Ohne --confirm wird JEDE buy/sell-Order nur simuliert (Trockenlauf) und geloggt,
  es wird keine echte Order an Trading212 gesendet.
- Verkaeufe werden gegen die aktuell gehaltene Menge geprueft -> kein Shorting.
- Jede Order, jeder Trockenlauf und jede Ablehnung wird in logs/trades_<Datum>.csv
  protokolliert (siehe trade_logger.py).
"""

from __future__ import annotations

import argparse
import sys

from t212_client import (RateLimitError, T212ApiError, T212Client,
                         find_position, position_price_chf, position_ticker)
from trade_logger import log_entry
from signals import get_signals
import ledger
from pathlib import Path


def cmd_status(args: argparse.Namespace) -> None:
    client = T212Client(environment=args.env)
    summary = client.get_account_summary()
    print(f"Account summary ({args.env}):")
    for k, v in summary.items():
        print(f"  {k}: {v}")


def cmd_positions(args: argparse.Namespace) -> None:
    client = T212Client(environment=args.env)
    positions = client.get_positions()
    if not positions:
        print("Keine offenen Positionen.")
        return
    for p in positions:
        print(p)


def cmd_find(args: argparse.Namespace) -> None:
    client = T212Client(environment=args.env)
    matches = client.find_instrument(args.needle)
    if not matches:
        print(f"Keine Instrumente gefunden fuer '{args.needle}'.")
        return
    for m in matches[:25]:
        print(f"  {m.get('ticker')} | {m.get('name')} | {m.get('currencyCode', m.get('currency', ''))}")
    if len(matches) > 25:
        print(f"  ... und {len(matches) - 25} weitere Treffer.")


def cmd_buy(args: argparse.Namespace) -> None:
    _place_order(args, side=1)


def cmd_sell(args: argparse.Namespace) -> None:
    _place_order(args, side=-1)



def _max_sellable_quantity(
    client: T212Client, ticker: str, ledger_path: Path,
) -> tuple[float, float, float]:
    """Wieviel darf fuer dieses Ticker maximal verkauft werden?

    Gibt (allowed_qty, held_qty_account, ledger_qty) zurueck. allowed_qty ist
    das Minimum aus (a) tatsaechlich im T212-Konto gehaltener Menge und
    (b) laut Ledger diesem Experiment zugeordneter Menge -- siehe
    STRATEGY.md "Ledger" fuer den Hintergrund (Konto haelt auch private
    Positionen, die nicht ueber dieses Tool verkauft werden duerfen).
    """
    positions = client.get_positions()
    held = find_position(positions, ticker)
    held_qty = held.get("quantity", 0) if held else 0.0
    ledger_qty = ledger.build_report(path=ledger_path).open_positions.get(ticker, 0.0)
    return min(held_qty, ledger_qty), held_qty, ledger_qty

def _place_order(args: argparse.Namespace, side: int) -> None:
    quantity = abs(args.quantity) * side
    action = "buy" if side > 0 else "sell"
    client = T212Client(environment=args.env)

    if side < 0:
        # Sicherheitscheck: nur verkaufen, was (a) tatsaechlich im Konto liegt
        # (kein Shorting) UND (b) laut Ledger tatsaechlich diesem Experiment
        # gehoert. Das Live-Konto haelt auch unabhaengige, private Positionen
        # (siehe STRATEGY.md "Ledger" -- z.B. NVDA/MSFT/META ueberschneiden
        # sich mit dem Handelsuniversum) -- die reine T212-Positionsabfrage
        # wuerde sonst erlauben, versehentlich private Bestaende zu verkaufen.
        allowed_qty, held_qty, ledger_qty = _max_sellable_quantity(
            client, args.ticker, ledger_path=ledger.path_for_env(args.env)
        )

        if abs(quantity) > allowed_qty + 1e-9:
            log_entry(
                environment=args.env, action=action, ticker=args.ticker,
                quantity=quantity, status="rule_check_failed",
                rationale=args.rationale, rule_check_ok=False,
            )
            print(
                f"Abgebrochen: Verkaufsmenge {abs(quantity)} > erlaubte Menge {allowed_qty:.6f} "
                f"fuer {args.ticker} (Ledger haelt {ledger_qty:.6f} fuer dieses Experiment, "
                f"Konto haelt insgesamt {held_qty:.6f} -- ggf. inkl. Positionen ausserhalb "
                f"dieses Experiments). Shorting bzw. Verkauf fremder Positionen ist nicht vorgesehen."
            )
            sys.exit(1)

    if not args.confirm:
        print(f"Trockenlauf (kein --confirm gesetzt), es wird NICHTS an Trading212 gesendet:")
        print(f"  {args.env} | {action} | {args.ticker} | quantity={quantity} | type={args.order_type}")
        log_entry(
            environment=args.env, action=action, ticker=args.ticker,
            order_type=args.order_type, quantity=quantity, limit_price=args.limit_price,
            status="dry_run", rationale=args.rationale,
        )
        return

    try:
        if args.order_type == "market":
            result = client.place_market_order(args.ticker, quantity)
        elif args.order_type == "limit":
            if args.limit_price is None:
                raise SystemExit("--limit-price ist fuer Limit-Orders erforderlich")
            result = client.place_limit_order(args.ticker, quantity, args.limit_price)
        else:
            raise SystemExit(f"Unbekannter order_type: {args.order_type}")
    except (T212ApiError, RateLimitError) as exc:
        log_entry(
            environment=args.env, action=action, ticker=args.ticker,
            order_type=args.order_type, quantity=quantity, limit_price=args.limit_price,
            status="rejected", rationale=f"{args.rationale} | Fehler: {exc}", rule_check_ok=False,
        )
        raise

    log_entry(
        environment=args.env, action=action, ticker=args.ticker,
        order_type=args.order_type, quantity=quantity, limit_price=args.limit_price,
        order_id=str(result.get("id", "")), status="placed", rationale=args.rationale,
    )
    print(result)



def cmd_signals(args: argparse.Namespace) -> None:
    """Berechnet regelbasierte BUY/SELL/HOLD-Signale (siehe STRATEGY.md) und
    loggt jedes Signal als Entscheidungszeile. Loest NIE selbst eine Order aus."""
    try:
        results = get_signals()
    except Exception as exc:  # z.B. fehlender Netzwerkzugriff auf Yahoo Finance
        print(f"Konnte keine Kursdaten laden: {exc}")
        print("Hinweis: signals braucht Internetzugang zu Yahoo Finance (yfinance).")
        return

    if not results:
        print("Keine Signale (zu wenig Kurshistorie geladen).")
        return

    for r in results:
        print(
            f"{r.t212_ticker:15s} {r.signal:5s} close={r.close:.2f} "
            f"sma50={r.sma50:.2f} sma200={r.sma200:.2f} rsi14={r.rsi14:.1f}  {r.reason}"
        )
        log_entry(
            environment=args.env, action="decision", ticker=r.t212_ticker,
            status=f"signal_{r.signal.lower()}", rationale=r.reason,
        )
        if r.signal in ("BUY", "SELL"):
            verb = "buy" if r.signal == "BUY" else "sell"
            print(
                f"  -> Vorschlag (manuell pruefen & ausfuehren): "
                f"python t212_cli.py --env {args.env} {verb} {r.t212_ticker} <MENGE> "
                f'--rationale "{r.reason}" --confirm'
            )



def cmd_orders(args: argparse.Namespace) -> None:
    """Zeigt alle aktuell offenen/unausgefuehrten Orders (z.B. Market-Orders,
    die ausserhalb der Handelszeiten noch auf Ausfuehrung warten)."""
    client = T212Client(environment=args.env)
    orders = client.get_open_orders()
    if not orders:
        print("Keine offenen Orders.")
        return
    for o in orders:
        print(o)


def cmd_order(args: argparse.Namespace) -> None:
    client = T212Client(environment=args.env)
    print(client.get_order(args.order_id))



def cmd_ledger_init(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    row = ledger.record_opening_balance(args.start_usd, args.fx_usd_chf, rationale=args.rationale, path=path)
    print(f"Ledger ({args.env}) initialisiert: {row['amount']} CHF Startkapital (cash_balance={row['cash_balance']}).")


def cmd_ledger_deposit(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    row = ledger.record_deposit(args.amount_chf, rationale=args.rationale, path=path)
    print(f"Ledger-Buchung ({args.env}) DEPOSIT: {row['amount']} CHF (cash_balance={row['cash_balance']}).")

def cmd_ledger_buy(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    row = ledger.record_buy(
        args.ticker, args.quantity, args.price, rationale=args.rationale, order_id=args.order_id, path=path
    )
    print(f"Ledger-Buchung ({args.env}) BUY: {row}")


def cmd_ledger_sell(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    row = ledger.record_sell(
        args.ticker, args.quantity, args.price, rationale=args.rationale, order_id=args.order_id, path=path
    )
    print(f"Ledger-Buchung ({args.env}) SELL: {row}")


def cmd_ledger_note(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    ledger.record_note(args.text, path=path)
    print(f"Notiz im Ledger ({args.env}) gespeichert.")


def cmd_ledger_report(args: argparse.Namespace) -> None:
    path = ledger.path_for_env(args.env)
    print(f"--- Ledger: {args.env} ---")
    prices = None
    try:
        positions = T212Client(environment=args.env).get_positions()

        # Kurs in Kontowaehrung (CHF) aus walletImpact, NICHT currentPrice (=USD)
        prices = {
            position_ticker(p): position_price_chf(p)
            for p in positions if position_ticker(p) and position_price_chf(p)
        }
        wanted = set(ledger.build_report(path=path).open_positions)
        missing = sorted(wanted - set(prices))
        if missing:
            print(f"(Hinweis: kein Kurs fuer {', '.join(missing)}; API lieferte {len(positions)} Position(en).)")
            if positions:
                print(f"(Diagnose: Felder der 1. Position: {sorted(positions[0].keys())})")
    except Exception as exc:  # Netz/API-Fehler duerfen den Report nicht verhindern
        print(f"(Hinweis: aktuelle Kurse nicht abrufbar: {type(exc).__name__}: {exc})")
    ledger.print_report(current_prices=prices, path=path)


def cmd_log_decision(args: argparse.Namespace) -> None:
    path = log_entry(environment=args.env, action="decision", status="note", rationale=args.rationale)
    print(f"Notiz gespeichert in {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FLOW100 Trading212 CLI")
    parser.add_argument("--env", choices=["live", "demo"], default="demo",
                         help="Trading212-Umgebung (Standard: demo)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Kontostand/Uebersicht anzeigen").set_defaults(func=cmd_status)
    sub.add_parser("positions", help="Offene Positionen anzeigen").set_defaults(func=cmd_positions)
    sub.add_parser("orders", help="Offene/unausgefuehrte Orders anzeigen").set_defaults(func=cmd_orders)
    p_order = sub.add_parser("order", help="Status einer einzelnen Order per ID abfragen")
    p_order.add_argument("order_id")
    p_order.set_defaults(func=cmd_order)
    sub.add_parser("signals", help="Regelbasierte BUY/SELL/HOLD-Signale berechnen (siehe STRATEGY.md)").set_defaults(func=cmd_signals)

    p_find = sub.add_parser("find", help="Instrument nach Ticker/Name suchen")
    p_find.add_argument("needle")
    p_find.set_defaults(func=cmd_find)

    for name, fn, help_text in (
        ("buy", cmd_buy, "Kauforder aufgeben (Trockenlauf ohne --confirm)"),
        ("sell", cmd_sell, "Verkaufsorder aufgeben (Trockenlauf ohne --confirm)"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("ticker", help="T212-Ticker/Instrument-Code, z.B. AAPL_US_EQ")
        p.add_argument("quantity", type=float)
        p.add_argument("--order-type", choices=["market", "limit"], default="market")
        p.add_argument("--limit-price", type=float, default=None)
        p.add_argument("--rationale", default="")
        p.add_argument("--confirm", action="store_true", help="Ohne dieses Flag nur Trockenlauf")
        p.set_defaults(func=fn)

    p_log = sub.add_parser("log-decision", help="Reine Entscheidungsnotiz protokollieren (kein Trade)")
    p_log.add_argument("--rationale", required=True)
    p_log.set_defaults(func=cmd_log_decision)

    p_ledger = sub.add_parser(
        "ledger",
        help="Eigenes Buchungs-Ledger fuer das Experiment (unabhaengig vom Rest des Kontos, siehe STRATEGY.md)",
    )
    ledger_sub = p_ledger.add_subparsers(dest="ledger_command", required=True)

    p_init = ledger_sub.add_parser("init", help="Einmalig Startkapital erfassen")
    p_init.add_argument("--start-usd", type=float, default=250.0)
    p_init.add_argument("--fx-usd-chf", type=float, required=True, help="Aktueller USD/CHF-Kurs, z.B. 0.82")
    p_init.add_argument("--rationale", default="")
    p_init.set_defaults(func=cmd_ledger_init)

    p_ldeposit = ledger_sub.add_parser("deposit", help="Kapitalerhoehung / nachtraeglich entdecktes Restguthaben erfassen (additiv zur Cash-Balance, siehe STRATEGY.md)")
    p_ldeposit.add_argument("--amount-chf", type=float, required=True)
    p_ldeposit.add_argument("--rationale", default="")
    p_ldeposit.set_defaults(func=cmd_ledger_deposit)

    p_lbuy = ledger_sub.add_parser("buy", help="Buy-Fill manuell im Ledger erfassen")
    p_lbuy.add_argument("ticker")
    p_lbuy.add_argument("quantity", type=float)
    p_lbuy.add_argument("--price", type=float, required=True, help="Ausfuehrungspreis pro Stueck in CHF")
    p_lbuy.add_argument("--rationale", default="")
    p_lbuy.add_argument("--order-id", default="")
    p_lbuy.set_defaults(func=cmd_ledger_buy)

    p_lsell = ledger_sub.add_parser("sell", help="Sell-Fill manuell im Ledger erfassen")
    p_lsell.add_argument("ticker")
    p_lsell.add_argument("quantity", type=float)
    p_lsell.add_argument("--price", type=float, required=True, help="Ausfuehrungspreis pro Stueck in CHF")
    p_lsell.add_argument("--rationale", default="")
    p_lsell.add_argument("--order-id", default="")
    p_lsell.set_defaults(func=cmd_ledger_sell)

    p_lnote = ledger_sub.add_parser("note", help="Freitext-Notiz im Ledger festhalten")
    p_lnote.add_argument("text")
    p_lnote.set_defaults(func=cmd_ledger_note)

    p_lreport = ledger_sub.add_parser("report", help="Ledger-Stand anzeigen (Cash, Positionen, realisiertes Ergebnis, Fortschritt)")
    p_lreport.set_defaults(func=cmd_ledger_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (T212ApiError, RateLimitError) as exc:
        print(f"Fehler: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
