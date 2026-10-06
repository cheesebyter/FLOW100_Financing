"""
CSV-Logging fuer Trades und Entscheidungen (siehe TRADING_PROMPT.md).

Schreibt pro Tag eine CSV-Datei nach logs/trades_YYYY-MM-DD.csv.
Jede Order (auch Trockenlaeufe/abgelehnte/fehlgeschlagene Versuche) und
jede reine Entscheidungsnotiz landet als eigene Zeile darin.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_DIR = Path(__file__).resolve().parent / "logs"

FIELDNAMES = [
    "timestamp_utc",
    "environment",       # live | demo
    "action",            # decision | buy | sell | cancel
    "ticker",
    "name",
    "order_type",        # market | limit | stop | stop_limit | n/a
    "quantity",
    "price",
    "limit_price",
    "stop_price",
    "order_id",
    "status",            # dry_run | placed | filled | cancelled | rejected | rule_check_failed | note
    "rationale",
    "rule_check_ok",
]


def _today_log_path(today: Optional[datetime] = None) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    day = (today or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    return LOG_DIR / f"trades_{day}.csv"


def log_entry(
    *,
    environment: str,
    action: str,
    ticker: str = "",
    name: str = "",
    order_type: str = "n/a",
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    order_id: str = "",
    status: str = "",
    rationale: str = "",
    rule_check_ok: bool = True,
) -> Path:
    """Haengt einen Eintrag an die CSV-Datei des heutigen Tages (UTC) an."""
    path = _today_log_path()
    is_new = not path.exists()
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": environment,
        "action": action,
        "ticker": ticker,
        "name": name,
        "order_type": order_type,
        "quantity": quantity if quantity is not None else "",
        "price": price if price is not None else "",
        "limit_price": limit_price if limit_price is not None else "",
        "stop_price": stop_price if stop_price is not None else "",
        "order_id": order_id,
        "status": status,
        "rationale": rationale,
        "rule_check_ok": rule_check_ok,
    }
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return path
