"""
Einfache Equity-Kurve + Drawdown-Ueberwachung fuer das FLOW100-Experiment
(siehe STRATEGY.md, Abschnitt "Automatisierungs-Policy" und
"Risikomanagement" -- Max.-Drawdown-Trigger bei -25% seit letztem Hoch).

Andys Entscheidung (22.09.2026): Der Drawdown-Trigger pausiert die
Automatisierung NICHT automatisch -- er wird nur als Alarm in der
Zusammenfassung jedes automatischen Laufs gemeldet, die Entscheidung zur
Reaktion bleibt bewusst manuell.

Getrennte Dateien pro Umgebung (wie beim Ledger), damit Demo- und
Live-Werte nicht vermischt werden.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

FIELDNAMES = ["timestamp_utc", "total_value_chf", "peak_to_date_chf", "drawdown_pct"]


def path_for_env(env: str) -> Path:
    if env not in ("live", "demo"):
        raise ValueError("env muss 'live' oder 'demo' sein")
    return Path(__file__).resolve().parent / f"equity_{env}.csv"


def _read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def record_point(total_value_chf: float, path: Path) -> dict:
    """Haengt einen neuen Equity-Punkt an und aktualisiert den Peak.
    Gibt die neue Zeile (inkl. drawdown_pct) zurueck."""
    rows = _read_all(path)
    prior_peak = max((float(r["peak_to_date_chf"]) for r in rows), default=0.0)
    peak = max(prior_peak, total_value_chf)
    drawdown_pct = round((total_value_chf / peak - 1), 4) if peak > 0 else 0.0

    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_value_chf": round(total_value_chf, 2),
        "peak_to_date_chf": round(peak, 2),
        "drawdown_pct": drawdown_pct,
    }
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return row
