"""
Backtest der FLOW100-Trading-Regeln (signals.py + auto_policy.py).

Bildet die LIVE-Logik moeglichst genau nach (Stand 06.10.2026):
- Signal wird auf dem Tagesschluss berechnet (wie auto_trade.py um 22:15),
  die Market-Order wird am NAECHSTEN Handelstag zur Eroeffnung gefuellt.
- Entry: signals.py-BUY + Extended-Filter (RSI<=75, <=5% ueber 20T-Hoch).
- Exit LIVE (seit 07.10.2026): "Kurs < SMA50" ODER Stop-Loss -12% ODER
  Trailing-Stop -10% (alles auf Tagesschluss, Order am Folgetag). Zum
  Vergleich laeuft auch der alte Stand "ohne Stops" (bis 06.10.2026).
- Max. 2 Positionen, 45% des Gesamtwerts je Position, 10% Cash-Reserve,
  Universum-Reihenfolge bei mehreren Signalen am selben Tag.
- Kosten pro Seite (FX-Gebuehr + Spread), Standard 0.20%.

Die Signal-Logik wird hier vektorisiert nachgebaut; tests/test_backtest.py
prueft, dass sie tag-genau mit signals.compute_signal_from_history
uebereinstimmt.

Aufruf (auf dem PC mit Internet, einmalig Daten holen und cachen):
    python backtest.py --years 6
Offline mit gecachten Daten:
    python backtest.py --offline
Positions-Slots testen (Sensitivitaet 2/3/4/5 Slots, Hauptlauf bleibt unveraendert):
    python backtest.py --offline --sensitivity
Einzelne Variante als Hauptlauf (z.B. 3 Slots mit je 30%):
    python backtest.py --offline --max-positions 3 --fraction 0.30

Einschraenkungen (bewusst, siehe Report): kein FX-Effekt (Rechnung in USD
als Naeherung fuer CHF), Survivorship-Bias im Universum, Fill zum
Eroeffnungskurs ohne Slippage-Modell ausser dem Kostenaufschlag.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import auto_policy as ap
from signals import UNIVERSE, _rsi

OUT_DIR = Path(__file__).resolve().parent / "backtest_output"
CACHE_PATH = Path(__file__).resolve().parent / "backtest_data" / "prices.csv"
BENCHMARKS = ["SPY", "QQQ"]


# --------------------------------------------------------------------------
# Indikatoren / Signale (vektorisiert, identisch zu signals.py)
# --------------------------------------------------------------------------
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """df: Spalten 'Open','Close', aufsteigend nach Datum."""
    close = df["Close"]
    out = pd.DataFrame(index=df.index)
    out["open"] = df["Open"]
    out["close"] = close
    out["sma50"] = close.rolling(50).mean()
    out["sma200"] = close.rolling(200).mean()
    out["high20_prev"] = close.rolling(20).max().shift(1)
    out["rsi"] = _rsi(close, 14)
    out["pct_above"] = close / out["high20_prev"] - 1

    valid = out[["sma200", "high20_prev", "rsi"]].notna().all(axis=1)
    buy = (
        (close > out["sma50"]) & (out["sma50"] > out["sma200"])
        & (close >= out["high20_prev"]) & out["rsi"].between(50, 80)
    )
    sell = (close < out["sma50"]) & ~buy
    actionable = (
        buy & (out["rsi"] <= ap.MAX_RSI_FOR_ENTRY)
        & (out["pct_above"] <= ap.MAX_PCT_ABOVE_BREAKOUT)
    )
    out["buy"] = (buy & valid).fillna(False)
    out["sell"] = (sell & valid).fillna(False)
    out["act_buy"] = (actionable & valid).fillna(False)
    out["valid"] = valid
    return out


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
@dataclass
class Params:
    start_capital: float = 324.50
    max_positions: int = ap.MAX_OPEN_POSITIONS
    position_fraction: float = ap.POSITION_FRACTION
    cash_reserve: float = ap.CASH_RESERVE_FRACTION
    api_cash_factor: float = ap.API_CASH_SAFETY_FACTOR
    min_notional: float = ap.MIN_TRADE_NOTIONAL_CHF
    cost_per_side: float = 0.0020
    stop_loss: Optional[float] = None      # z.B. 0.12
    trailing_stop: Optional[float] = None  # z.B. 0.10


@dataclass
class SimResult:
    equity: pd.Series
    trades: list = field(default_factory=list)       # abgeschlossene Trades
    open_positions: dict = field(default_factory=dict)
    cash: float = 0.0
    exposure: pd.Series = None                       # Anteil investiert je Tag
    max_open: int = 0                                # max. gleichzeitig offene Positionen


def simulate(ind: dict[str, pd.DataFrame], params: Params) -> SimResult:
    tickers = list(ind.keys())  # Reihenfolge = Universum-Reihenfolge
    dates = ind[tickers[0]].index
    for t in tickers:
        assert ind[t].index.equals(dates), "Alle Ticker brauchen denselben Datumsindex"

    start_k = int(min(np.argmax(ind[t]["valid"].to_numpy()) for t in tickers))
    arrays = {
        t: {c: ind[t][c].to_numpy() for c in ("open", "close", "sell", "act_buy", "valid")}
        for t in tickers
    }

    cash = params.start_capital
    positions: dict[str, dict] = {}
    pending: list[tuple] = []
    trades: list[dict] = []
    eq_vals, eq_dates, exp_vals = [], [], []
    max_open = 0

    for k in range(start_k, len(dates)):
        d = dates[k]

        # 1) Orders vom Vortag zur Eroeffnung fuellen
        for order in pending:
            kind, t = order[0], order[1]
            px = arrays[t]["open"][k]
            if kind == "sell" and t in positions:
                pos = positions.pop(t)
                fill = px * (1 - params.cost_per_side)
                cash += pos["qty"] * fill
                trades.append({
                    "ticker": t, "entry_date": pos["entry_date"], "entry_price": pos["entry_price"],
                    "exit_date": d, "exit_price": fill, "qty": pos["qty"],
                    "pnl": pos["qty"] * (fill - pos["entry_price"]),
                    "ret": fill / pos["entry_price"] - 1,
                    "days": (d - pos["entry_date"]).days, "reason": order[2],
                })
            elif kind == "buy" and t not in positions:
                qty = order[2]
                fill = px * (1 + params.cost_per_side)
                if qty * fill > cash:
                    qty = math.floor(cash / fill * 100) / 100
                if qty > 0 and qty * fill >= 0.0:
                    cash -= qty * fill
                    positions[t] = {"qty": qty, "entry_price": fill, "entry_date": d, "peak": fill}
        pending = []

        # 2) Bewertung zum Schluss, Peaks aktualisieren
        invested = 0.0
        for t, pos in positions.items():
            c = arrays[t]["close"][k]
            pos["peak"] = max(pos["peak"], c)
            invested += pos["qty"] * c
        equity = cash + invested
        max_open = max(max_open, len(positions))
        eq_dates.append(d)
        eq_vals.append(equity)
        exp_vals.append(invested / equity if equity > 0 else 0.0)

        # 3) Orders fuer den naechsten Tag aus den Schlusskurs-Signalen
        if k == len(dates) - 1:
            continue
        n_open = len(positions)
        planned_sells = set()
        avail_cash = cash
        for t in tickers:
            a = arrays[t]
            if not a["valid"][k]:
                continue
            if t in positions:
                pos = positions[t]
                c = a["close"][k]
                reason = None
                if a["sell"][k]:
                    reason = "SMA50"
                elif params.stop_loss and c <= pos["entry_price"] * (1 - params.stop_loss):
                    reason = "Stop-Loss"
                elif params.trailing_stop and c <= pos["peak"] * (1 - params.trailing_stop):
                    reason = "Trailing-Stop"
                if reason:
                    pending.append(("sell", t, reason))
                    planned_sells.add(t)
                continue
            if not a["act_buy"][k]:
                continue
            if n_open >= params.max_positions:
                continue
            target = min(
                params.position_fraction * equity,
                avail_cash * (1 - params.cash_reserve),
                avail_cash * params.api_cash_factor,
            )
            if target < params.min_notional:
                continue
            c = a["close"][k]
            qty = round(target / c, 2)
            if qty <= 0:
                continue
            pending.append(("buy", t, qty))
            avail_cash -= qty * c
            n_open += 1

    equity = pd.Series(eq_vals, index=pd.DatetimeIndex(eq_dates), name="equity")
    exposure = pd.Series(exp_vals, index=equity.index, name="exposure")
    return SimResult(equity=equity, trades=trades, open_positions=positions,
                     cash=cash, exposure=exposure, max_open=max_open)


# --------------------------------------------------------------------------
# Kennzahlen
# --------------------------------------------------------------------------
def max_drawdown(series: pd.Series) -> float:
    peak = series.cummax()
    return float((series / peak - 1).min())


def series_metrics(series: pd.Series) -> dict:
    series = series.dropna()
    years = (series.index[-1] - series.index[0]).days / 365.25
    total = series.iloc[-1] / series.iloc[0] - 1
    cagr = (series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1 if years > 0 and series.iloc[-1] > 0 else float("nan")
    rets = series.pct_change().dropna()
    vol = float(rets.std() * math.sqrt(252)) if len(rets) > 1 else float("nan")
    sharpe = float(rets.mean() / rets.std() * math.sqrt(252)) if len(rets) > 1 and rets.std() > 0 else float("nan")
    mdd = max_drawdown(series)
    return {"total": float(total), "cagr": float(cagr), "vol": vol, "sharpe": sharpe,
            "maxdd": mdd, "calmar": float(cagr / abs(mdd)) if mdd < 0 else float("nan"),
            "years": years}


def trade_stats(trades: list) -> dict:
    if not trades:
        return {"n": 0}
    pnl = np.array([t["pnl"] for t in trades])
    rets = np.array([t["ret"] for t in trades])
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    gross_win, gross_loss = wins.sum(), -losses.sum()
    top3 = np.sort(pnl)[::-1][:3].sum()
    total_pos_pnl = pnl[pnl > 0].sum()
    return {
        "n": len(trades),
        "win_rate": float((pnl > 0).mean()),
        "avg_win": float(rets[pnl > 0].mean()) if (pnl > 0).any() else 0.0,
        "avg_loss": float(rets[pnl <= 0].mean()) if (pnl <= 0).any() else 0.0,
        "expectancy": float(rets.mean()),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "best": float(rets.max()), "worst": float(rets.min()),
        "avg_days": float(np.mean([t["days"] for t in trades])),
        "top3_share_of_gross_profit": float(top3 / total_pos_pnl) if total_pos_pnl > 0 else float("nan"),
        "net_pnl": float(pnl.sum()),
    }


def yearly_returns(series: pd.Series) -> pd.Series:
    """Rendite je Kalenderjahr (erstes/letztes Jahr = Teiljahr)."""
    out = {}
    prev = series.iloc[0]
    for year, grp in series.groupby(series.index.year):
        out[year] = grp.iloc[-1] / prev - 1
        prev = grp.iloc[-1]
    return pd.Series(out)


def benchmark_equity(close: pd.DataFrame | pd.Series, index: pd.DatetimeIndex, start_capital: float) -> pd.Series:
    """Buy-and-hold ab erstem Simulationstag (Equal-Weight bei DataFrame)."""
    c = close.reindex(index).ffill()
    rel = c / c.iloc[0]
    if isinstance(rel, pd.DataFrame):
        rel = rel.mean(axis=1)
    return rel * start_capital


# --------------------------------------------------------------------------
# Daten
# --------------------------------------------------------------------------
def load_prices(years: int, offline: bool, cache: Path = CACHE_PATH) -> dict[str, pd.DataFrame]:
    symbols = list(dict.fromkeys(list(UNIVERSE.values()) + BENCHMARKS))
    if offline:
        if not cache.exists():
            raise SystemExit(f"--offline, aber kein Cache unter {cache}. Erst einmal ohne --offline laufen lassen.")
        raw = pd.read_csv(cache, header=[0, 1], index_col=0, parse_dates=True)
    else:
        import yfinance as yf  # lazy
        end = pd.Timestamp.today().normalize()
        start = end - pd.DateOffset(years=years) - pd.DateOffset(days=330)  # Warmup SMA200
        raw = yf.download(symbols, start=start.strftime("%Y-%m-%d"), auto_adjust=True,
                          group_by="ticker", progress=False)
        cache.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(cache)
    data = {}
    for s in symbols:
        df = raw[s][["Open", "Close"]].dropna()
        if len(df):
            data[s] = df
    missing = [s for s in symbols if s not in data]
    if missing:
        raise SystemExit(f"Keine Daten fuer: {missing}")
    return data


def prepare(data: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Gemeinsamen Datumsindex fuer das Universum bilden, Indikatoren rechnen."""
    uni_syms = [UNIVERSE[t] for t in UNIVERSE]
    common = data[uni_syms[0]].index
    for s in uni_syms[1:]:
        common = common.intersection(data[s].index)
    ind = {t: compute_indicators(data[UNIVERSE[t]].reindex(common)) for t in UNIVERSE}
    closes = pd.DataFrame({UNIVERSE[t]: ind[t]["close"] for t in UNIVERSE})
    return ind, closes


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def pct(x, d=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:+.{d}f}%"


NAME_NOSTOP = "ohne Stops (Stand bis 06.10.2026)"
NAME_LIVE = "LIVE-Regeln seit 07.10.2026 (SMA50 + Stop-Loss -12% / Trailing -10%)"


def build_report(
    data: dict[str, pd.DataFrame], capital: float, cost: float,
    max_positions: Optional[int] = None, fraction: Optional[float] = None,
    sensitivity: bool = False,
) -> str:
    ind, closes = prepare(data)
    extra = {}
    if max_positions is not None:
        extra["max_positions"] = max_positions
    if fraction is not None:
        extra["position_fraction"] = fraction
    variants = {
        NAME_NOSTOP: Params(start_capital=capital, cost_per_side=cost, **extra),
        NAME_LIVE: Params(start_capital=capital, cost_per_side=cost,
                          stop_loss=ap.STOP_LOSS_PCT, trailing_stop=ap.TRAILING_STOP_PCT, **extra),
    }
    results = {name: simulate(ind, p) for name, p in variants.items()}
    first = next(iter(results.values()))
    idx = first.equity.index

    curves = {name: r.equity for name, r in results.items()}
    curves["Buy&Hold Universum (Equal-Weight)"] = benchmark_equity(closes, idx, capital)
    for b in BENCHMARKS:
        if b in data:
            curves[f"Buy&Hold {b}"] = benchmark_equity(data[b]["Close"], idx, capital)

    L = []
    L.append("# Backtest FLOW100-Trading-Regeln")
    L.append("")
    p0 = next(iter(variants.values()))
    L.append(f"Zeitraum: {idx[0].date()} bis {idx[-1].date()} ({(idx[-1]-idx[0]).days/365.25:.1f} Jahre), "
             f"Startkapital {capital:.2f}, Kosten {cost*100:.2f}% je Seite, Universum {len(UNIVERSE)} Titel, "
             f"max. {p0.max_positions} Positionen a {p0.position_fraction*100:.0f}%.")
    L.append("")
    L.append("## Ergebnis (Gesamtkonto inkl. Cash)")
    L.append("")
    L.append("| Strategie | Gesamt | CAGR | Max. Drawdown | Sharpe | Calmar | Endwert |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for name, s in curves.items():
        m = series_metrics(s)
        L.append(f"| {name} | {pct(m['total'])} | {pct(m['cagr'])} | {pct(m['maxdd'])} | "
                 f"{m['sharpe']:.2f} | {m['calmar']:.2f} | {s.iloc[-1]:.2f} |")
    L.append("")
    for name, r in results.items():
        st = trade_stats(r.trades)
        L.append(f"## Trades: {name}")
        L.append("")
        if st["n"] == 0:
            L.append("Keine abgeschlossenen Trades.")
            L.append("")
            continue
        L.append(f"- Abgeschlossene Trades: {st['n']} (offen am Ende: {len(r.open_positions)})")
        L.append(f"- Trefferquote: {st['win_rate']*100:.0f}%  |  Ø Gewinn: {pct(st['avg_win'])}  |  Ø Verlust: {pct(st['avg_loss'])}")
        L.append(f"- Erwartungswert je Trade: {pct(st['expectancy'], 2)}  |  Profit Factor: {st['profit_factor']:.2f}")
        L.append(f"- Bester / schlechtester Trade: {pct(st['best'])} / {pct(st['worst'])}  |  Ø Haltedauer: {st['avg_days']:.0f} Tage")
        L.append(f"- Anteil der 3 besten Trades am Brutto-Gewinn: {pct(st['top3_share_of_gross_profit'], 0).lstrip('+')} "
                 f"(hoch = Ergebnis haengt an wenigen Ausreissern)")
        L.append(f"- Ø Investitionsgrad: {r.exposure.mean()*100:.0f}% des Kontos")
        L.append("")
    L.append("## Rendite je Kalenderjahr (Teiljahre am Rand)")
    L.append("")
    names = list(curves.keys())
    yr = pd.DataFrame({n: yearly_returns(curves[n]) for n in names})
    L.append("| Jahr | " + " | ".join(names) + " |")
    L.append("|---|" + "---:|" * len(names))
    for year, row in yr.iterrows():
        L.append(f"| {year} | " + " | ".join(pct(row[n]) for n in names) + " |")
    L.append("")
    L.append("## Einordnung / Grenzen")
    L.append("")
    L.append("- **Survivorship-Bias:** Das Universum wurde heute gewaehlt, Titel die gut liefen, sind dabei. "
             "Das Ergebnis ist tendenziell zu optimistisch.")
    L.append("- **Stops:** Seit 07.10.2026 live (`auto_trade.py`). Stop-Pruefung auf Tagesschluss, Fill am Folgetag; "
             "Luecken ueber die Schwelle fuellen zum Eroeffnungskurs.")
    L.append("- **Kein FX-Effekt**, Rechnung in USD. Kein Slippage-Modell ausser dem Kostenaufschlag. Fill zur Eroeffnung des Folgetags.")
    L.append("- **Stichprobe:** Wenige Trades -> grosse Streuung. Eine Trefferquote oder CAGR aus <30 Trades ist kein Beleg.")
    L.append("- **Kein Parameter-Fitting:** Die Regeln wurden unveraendert uebernommen. Nicht anhand dieses Reports nachjustieren, "
             "sonst wird er zur In-Sample-Optimierung.")
    L.append("")

    if sensitivity:
        L.append(slot_sensitivity(ind, capital, cost))
    OUT_DIR.mkdir(exist_ok=True)
    for name, r in results.items():
        slug = "live" if name == NAME_LIVE else "ohne_stops"
        pd.DataFrame(r.trades).to_csv(OUT_DIR / f"trades_{slug}.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT_DIR / "equity_curves.csv")
    return "\n".join(L)


SLOT_CONFIGS = [(2, 0.45), (3, 0.30), (4, 0.22), (5, 0.18)]


def slot_sensitivity(ind: dict[str, pd.DataFrame], capital: float, cost: float) -> str:
    """Wie verhalten sich die LIVE-Regeln (mit Stops) bei anderer Slot-Zahl?
    Aufteilung je Konfiguration ca. 90% / Slots (10% Cash-Reserve). Reine
    Sensitivitaet -- kein Optimierungsziel (siehe Hinweis im Report)."""
    L = ["## Sensitivitaet: Anzahl Positionen (Regeln inkl. Stops, sonst unveraendert)", ""]
    L.append("| Slots x Anteil | Gesamt | CAGR | Max. DD | Sharpe | Trades | Trefferquote | Profit Factor | Ø Investitionsgrad | Endwert |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for slots, frac in SLOT_CONFIGS:
        p = Params(start_capital=capital, cost_per_side=cost, max_positions=slots,
                   position_fraction=frac, stop_loss=ap.STOP_LOSS_PCT, trailing_stop=ap.TRAILING_STOP_PCT)
        r = simulate(ind, p)
        m = series_metrics(r.equity)
        st = trade_stats(r.trades)
        wr = f"{st['win_rate']*100:.0f}%" if st.get("n") else "n/a"
        pf = f"{st['profit_factor']:.2f}" if st.get("n") else "n/a"
        mark = "  (aktuell live)" if (slots, frac) == (ap.MAX_OPEN_POSITIONS, ap.POSITION_FRACTION) else ""
        L.append(f"| {slots} x {frac*100:.0f}%{mark} | {pct(m['total'])} | {pct(m['cagr'])} | {pct(m['maxdd'])} | "
                 f"{m['sharpe']:.2f} | {st.get('n', 0)} | {wr} | {pf} | {r.exposure.mean()*100:.0f}% | {r.equity.iloc[-1]:.2f} |")
    L.append("")
    L.append("Hinweis: Die Unterschiede zwischen den Zeilen sind meist klein gegenueber der Streuung einer "
             "6-Jahres-Stichprobe mit wenigen Dutzend Trades. Eine Aenderung nur dann erwaegen, wenn sie "
             "ueber mehrere Kennzahlen (Rendite UND Drawdown UND Sharpe) klar besser ist und auch mit "
             "hoeheren Kosten (`--cost 0.004`) bestehen bleibt.")
    L.append("")
    return "\n".join(L)


def main() -> None:
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--years", type=int, default=6)
    ap_.add_argument("--offline", action="store_true", help="gecachte Daten aus backtest_data/ nutzen")
    ap_.add_argument("--capital", type=float, default=324.50)
    ap_.add_argument("--cost", type=float, default=0.0020, help="Kosten je Seite als Bruch (0.002 = 0.20%%)")
    ap_.add_argument("--max-positions", type=int, default=None, help="Max. gleichzeitige Positionen (Standard: auto_policy)")
    ap_.add_argument("--fraction", type=float, default=None, help="Positionsgroesse als Anteil des Kontos (Standard: auto_policy)")
    ap_.add_argument("--sensitivity", action="store_true", help="Zusatztabelle: 2/3/4/5 Slots")
    args = ap_.parse_args()

    data = load_prices(args.years, args.offline)
    report = build_report(data, args.capital, args.cost, args.max_positions, args.fraction, args.sensitivity)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\n(Report + CSVs in {OUT_DIR})")


if __name__ == "__main__":
    main()
