"""
Einfaches Buchungs-Ledger fuer das FLOW100-Trading-Experiment.

Hintergrund: Das Live-Konto enthaelt daneben noch anderes Kapital/andere
Positionen (Stand 09.09.2026: Gesamtwert 797.55 CHF, davon ~480 CHF bereits
in Positionen, -78.70 CHF historisch realisierter Verlust aus frueherer,
von diesem Projekt unabhaengiger Aktivitaet). Trading212 selbst kennt keine
"echte" Geldsegregation innerhalb eines Kontos (keine isolierten
Unterkonten fuer einzelne Strategien). Dieses Ledger bildet deshalb eine
EIGENE, rein buchhalterische Nachverfolgung: Startkapital, jeder Trade
dieses Experiments, realisierte Gewinne/Verluste (FIFO), Fortschritt
Richtung 100'000 CHF -- unabhaengig davon, was sonst noch im Konto passiert.

Andys Entscheidung (09.09.2026): aktuell wird nur ein Teil des Kontos
("die 250 USD") diesem Experiment zugerechnet; "das ganze Konto wird in
Zukunft, wenn es gut laeuft, benutzt". Das Ledger ist bewusst so einfach
gehalten, dass es bei Bedarf spaeter erweitert werden kann (z.B. um eine
TOPUP-Buchungsart fuer eine spaetere Kapitalerhoehung) -- siehe
STRATEGY.md, Abschnitt "Ledger".

Buchungslogik: FIFO-Lots pro Ticker, damit realisierte Gewinne/Verluste bei
Teilverkaeufen korrekt zugeordnet werden. Alle Betraege in Kontowaehrung
(CHF), da Trading212 Kaeufe/Verkaeufe auslaendischer Instrumente intern in
die Kontowaehrung umrechnet.

WICHTIG (Korrektur 14.09.2026): Es gibt GETRENNTE Ledger-Dateien fuer
Demo und Live (`ledger_demo.csv` / `ledger_live.csv`, ueber `path_for_env()`).
Vorher landete ein Demo-Testtrade (NVDA) versehentlich in derselben Datei,
die eigentlich das reale Live-Experiment tracken sollte -- das haette echte
und simulierte Performance vermischt. Nur `ledger_live.csv` zaehlt fuer den
tatsaechlichen Fortschritt Richtung 100'000 CHF.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "ledger.csv"  # veraltet, siehe path_for_env()


def path_for_env(env: str) -> Path:
    """Liefert die Ledger-Datei fuer 'live' oder 'demo' -- niemals dieselbe
    Datei fuer beide, damit simulierte und echte Performance nicht
    vermischt werden."""
    if env not in ("live", "demo"):
        raise ValueError("env muss 'live' oder 'demo' sein")
    return Path(__file__).resolve().parent / f"ledger_{env}.csv"

FIELDNAMES = [
    "timestamp_utc",
    "type",         # OPENING | DEPOSIT | BUY | SELL | NOTE
    "ticker",
    "quantity",
    "price",        # Preis pro Stueck in CHF
    "amount",       # Cash-Effekt dieser Buchung (negativ=Abfluss), CHF
    "realized_pl",  # nur bei SELL gefuellt
    "cash_balance", # Ledger-Cash (virtuell) nach dieser Buchung, CHF
    "rationale",
    "order_id",
]


@dataclass
class Lot:
    quantity: float
    price: float  # Einstandspreis pro Stueck, CHF


def _read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _append(path: Path, row: dict) -> None:
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def _current_cash_balance(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return float(rows[-1]["cash_balance"])


def _open_lots(rows: list[dict]) -> dict[str, list[Lot]]:
    """Baut die aktuell offenen FIFO-Lots je Ticker aus der Historie neu auf."""
    lots: dict[str, list[Lot]] = {}
    for row in rows:
        if row["type"] == "BUY":
            ticker = row["ticker"]
            lots.setdefault(ticker, []).append(
                Lot(quantity=float(row["quantity"]), price=float(row["price"]))
            )
        elif row["type"] == "SELL":
            ticker = row["ticker"]
            remaining = float(row["quantity"])
            ticker_lots = lots.get(ticker, [])
            while remaining > 1e-9 and ticker_lots:
                lot = ticker_lots[0]
                take = min(lot.quantity, remaining)
                lot.quantity -= take
                remaining -= take
                if lot.quantity <= 1e-9:
                    ticker_lots.pop(0)
            lots[ticker] = ticker_lots
    return {t: ls for t, ls in lots.items() if ls}


def record_opening_balance(
    amount_usd: float, fx_usd_chf: float, rationale: str = "",
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    rows = _read_all(path)
    if any(r["type"] == "OPENING" for r in rows):
        raise RuntimeError(
            "Es existiert bereits eine OPENING-Buchung im Ledger. Für eine "
            "spätere Kapitalerhöhung (siehe STRATEGY.md) müsste eine neue "
            "Buchungsart ergänzt werden statt einfach zu überschreiben."
        )
    amount_chf = round(amount_usd * fx_usd_chf, 2)
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "OPENING", "ticker": "", "quantity": "", "price": "",
        "amount": amount_chf, "realized_pl": "",
        "cash_balance": amount_chf,
        "rationale": rationale or f"Startkapital {amount_usd} USD @ FX {fx_usd_chf}",
        "order_id": "",
    }
    _append(path, row)
    return row


def record_deposit(
    amount_chf: float, rationale: str = "",
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    """Kapitalerhoehung/nachtraeglich entdecktes Restguthaben. Im Unterschied
    zu record_opening_balance() wiederholbar und additiv zur bestehenden
    Cash-Balance -- verfaelscht nicht die historische OPENING-Buchung,
    sondern haengt eine datierte, auditierbare Korrektur an."""
    rows = _read_all(path)
    if not any(r["type"] == "OPENING" for r in rows):
        raise RuntimeError(
            "Kein OPENING-Eintrag vorhanden -- zuerst 'ledger init' ausführen."
        )
    new_cash = round(_current_cash_balance(rows) + amount_chf, 2)
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "DEPOSIT", "ticker": "", "quantity": "", "price": "",
        "amount": round(amount_chf, 2), "realized_pl": "",
        "cash_balance": new_cash,
        "rationale": rationale or f"Kapitalerhoehung {amount_chf} CHF",
        "order_id": "",
    }
    _append(path, row)
    return row

def record_buy(
    ticker: str, quantity: float, price: float, rationale: str = "",
    order_id: str = "", path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    rows = _read_all(path)
    if not rows:
        raise RuntimeError("Kein Ledger vorhanden. Zuerst 'ledger init' ausführen.")
    cash_before = _current_cash_balance(rows)
    cost = round(quantity * price, 2)
    cash_after = round(cash_before - cost, 2)
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "BUY", "ticker": ticker, "quantity": quantity, "price": price,
        "amount": -cost, "realized_pl": "", "cash_balance": cash_after,
        "rationale": rationale, "order_id": order_id,
    }
    _append(path, row)
    return row


def record_sell(
    ticker: str, quantity: float, price: float, rationale: str = "",
    order_id: str = "", path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    rows = _read_all(path)
    if not rows:
        raise RuntimeError("Kein Ledger vorhanden. Zuerst 'ledger init' ausführen.")

    lots = _open_lots(rows).get(ticker, [])
    total_held = sum(l.quantity for l in lots)
    if quantity > total_held + 1e-9:
        raise ValueError(
            f"Verkaufsmenge {quantity} > im Ledger gehaltene Menge {total_held} "
            f"für {ticker}. Shorting ist laut TRADING_PROMPT.md nicht vorgesehen -- "
            "Ledger und echtes Konto prüfen, bevor weitergemacht wird."
        )

    remaining = quantity
    cost_basis = 0.0
    for lot in lots:
        if remaining <= 1e-9:
            break
        take = min(lot.quantity, remaining)
        cost_basis += take * lot.price
        remaining -= take

    proceeds = round(quantity * price, 2)
    realized_pl = round(proceeds - cost_basis, 2)
    cash_before = _current_cash_balance(rows)
    cash_after = round(cash_before + proceeds, 2)

    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "SELL", "ticker": ticker, "quantity": quantity, "price": price,
        "amount": proceeds, "realized_pl": realized_pl, "cash_balance": cash_after,
        "rationale": rationale, "order_id": order_id,
    }
    _append(path, row)
    return row


def record_note(text: str, path: Path = DEFAULT_LEDGER_PATH) -> dict:
    rows = _read_all(path)
    cash = _current_cash_balance(rows)
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": "NOTE", "ticker": "", "quantity": "", "price": "",
        "amount": "", "realized_pl": "", "cash_balance": cash,
        "rationale": text, "order_id": "",
    }
    _append(path, row)
    return row


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def contribution_events(rows: list[dict]) -> list[tuple[datetime, float]]:
    """Alle Kapitalzufluesse (OPENING + DEPOSIT) als (Zeitpunkt, CHF)."""
    return [
        (_parse_ts(r["timestamp_utc"]), float(r["amount"]))
        for r in rows
        if r["type"] in ("OPENING", "DEPOSIT") and r["amount"] not in ("", None)
    ]


def total_contributions(rows: list[dict]) -> float:
    return sum(a for _, a in contribution_events(rows))


def market_value(report: "LedgerReport", current_prices: dict) -> Optional[float]:
    """Cash + Marktwert offener Positionen. None, wenn fuer eine offene
    Position kein aktueller Preis vorliegt (dann waere die Zahl falsch)."""
    total = report.cash_balance
    for ticker, qty in report.open_positions.items():
        price = current_prices.get(ticker)
        if price is None:
            return None
        total += qty * price
    return round(total, 2)


def modified_dietz(
    rows: list[dict], end_value: float, end_time: Optional[datetime] = None,
) -> Optional[float]:
    """Kapitalgewichtete Rendite (Modified Dietz) seit OPENING, als Bruch
    (0.05 = +5%). Einzahlungen zaehlen NICHT als Gewinn, sondern werden
    nach der Zeit gewichtet, die sie im Ledger waren.

        R = (Endwert - Summe Einzahlungen) / (Startkapital + Sum(w_i * Einzahlung_i))
        w_i = (Ende - t_i) / (Ende - Start)

    Naeherung: braucht nur Start- und Endwert (keine historischen
    Marktwerte). None, wenn die Laufzeit 0 ist."""
    events = contribution_events(rows)
    if not events:
        return None
    end = end_time or datetime.now(timezone.utc)
    start = events[0][0]
    span = (end - start).total_seconds()
    if span <= 0:
        return None
    weighted = sum(a * (end - t).total_seconds() / span for t, a in events)
    if weighted <= 0:
        return None
    return (end_value - sum(a for _, a in events)) / weighted


@dataclass
class LedgerReport:
    cash_balance: float
    open_positions: dict           # ticker -> quantity
    open_positions_cost_basis: dict  # ticker -> Summe Einstandskosten CHF
    total_realized_pl: float
    invested_cost_basis: float
    total_ledger_value_at_cost: float  # cash + Summe Einstandskosten offener Positionen
    total_contributions: float = 0.0   # OPENING + alle DEPOSITs (eingebrachtes Kapital), CHF


def build_report(path: Path = DEFAULT_LEDGER_PATH) -> LedgerReport:
    rows = _read_all(path)
    if not rows:
        return LedgerReport(0.0, {}, {}, 0.0, 0.0, 0.0)

    cash = _current_cash_balance(rows)
    lots_by_ticker = _open_lots(rows)
    open_qty = {t: sum(l.quantity for l in ls) for t, ls in lots_by_ticker.items()}
    open_cost = {t: sum(l.quantity * l.price for l in ls) for t, ls in lots_by_ticker.items()}
    total_realized = sum(
        float(r["realized_pl"]) for r in rows if r["type"] == "SELL" and r["realized_pl"]
    )
    invested_cost_basis = sum(open_cost.values())

    return LedgerReport(
        cash_balance=cash,
        open_positions=open_qty,
        open_positions_cost_basis=open_cost,
        total_realized_pl=round(total_realized, 2),
        invested_cost_basis=round(invested_cost_basis, 2),
        total_ledger_value_at_cost=round(cash + invested_cost_basis, 2),
        total_contributions=round(total_contributions(rows), 2),
    )


def print_report(current_prices: Optional[dict] = None, path: Path = DEFAULT_LEDGER_PATH) -> None:
    rows = _read_all(path)
    if not rows:
        print("Ledger ist leer. Zuerst 'ledger init' ausführen.")
        return
    r = build_report(path)
    print(f"Cash (Ledger, virtuell):         {r.cash_balance:>10.2f} CHF")
    for ticker, qty in r.open_positions.items():
        cost = r.open_positions_cost_basis[ticker]
        line = f"  {ticker:15s} {qty:>8.4f} Stk, Einstand {cost:>8.2f} CHF"
        if current_prices and ticker in current_prices:
            value = qty * current_prices[ticker]
            line += f", akt. Wert {value:>8.2f} CHF ({value - cost:+.2f}, {(value / cost - 1) * 100:+.1f}%)"
        print(line)
    print(f"Einstandswert offener Positionen: {r.invested_cost_basis:>10.2f} CHF")
    print(f"Realisiertes Ergebnis bisher:     {r.total_realized_pl:>+10.2f} CHF")
    print(f"Ledger-Gesamtwert (zu Einstand):  {r.total_ledger_value_at_cost:>10.2f} CHF")
    print(f"Eingebrachtes Kapital:            {r.total_contributions:>10.2f} CHF (Startkapital + Einzahlungen)")

    mv = market_value(r, current_prices) if current_prices is not None else None
    if mv is None:
        print("Marktwert / Rendite:              n/a (keine aktuellen Kurse verfuegbar)")
        value_for_progress, basis = r.total_ledger_value_at_cost, "zu Einstandswerten"
    else:
        pl = mv - r.total_contributions
        print(f"Ledger-Gesamtwert (Marktwert):    {mv:>10.2f} CHF")
        print(f"Netto-Ergebnis (Marktwert - Kapital): {pl:>+7.2f} CHF")
        dietz = modified_dietz(rows, mv)
        if dietz is not None:
            print(f"Rendite (kapitalgewichtet):       {dietz * 100:>+9.2f}%  (Modified Dietz, Einzahlungen nicht als Gewinn)")
        value_for_progress, basis = mv, "zum Marktwert"
    print("Ziel:                             100'000.00 CHF")
    if value_for_progress > 0:
        print(f"Fortschritt ({basis}): {value_for_progress / 100000 * 100:.3f}%")
