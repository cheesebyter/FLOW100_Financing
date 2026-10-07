"""
Trading212 API Client fuer das FLOW100 Stock-Trading-Setup.

Rahmenbedingungen (siehe TRADING_PROMPT.md):
- Broker: Trading212, Startkapital 250 USD, Ziel 100'000 CHF
- Nur Aktien und ETFs, long only
- Keine CFDs, kein Margin/Hebel, keine Optionen/Futures/Shorts
- Bevorzugt liquide Titel mit engen Spreads

Auth: HTTP Basic mit Base64(API_KEY:API_SECRET) im Authorization-Header.
Doku: https://docs.trading212.com/api (Stand: Beta, Sept. 2026)

WICHTIG: Die Order-Endpunkte sind laut Doku (Beta) nicht idempotent -
doppelte Requests koennen doppelte Orders erzeugen. Vorsicht bei Retries.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests

ENV_PATH = Path(__file__).resolve().parent / ".env"


def position_ticker(p: dict) -> Optional[str]:
    """Ticker einer Position -- aktuelle API: verschachtelt unter
    'instrument', aeltere/flache Form: direkt unter 'ticker'."""
    return p.get("ticker") or (p.get("instrument") or {}).get("ticker")


def find_position(positions: list, ticker: str) -> Optional[dict]:
    return next((p for p in positions if position_ticker(p) == ticker), None)


def position_avg_price(p: dict) -> Optional[float]:
    """Durchschnittlicher Einstandspreis pro Stueck in INSTRUMENTENWAEHRUNG
    (z.B. USD) -- vergleichbar mit Yahoo-Schlusskursen, nicht mit CHF-Ledger."""
    v = p.get("averagePricePaid")
    return float(v) if v else None


def position_created_at(p: dict) -> Optional[str]:
    return p.get("createdAt")


def position_price_chf(p: dict) -> Optional[float]:
    """Aktueller Kurs pro Stueck in KONTOWAEHRUNG (CHF). 'currentPrice' der
    API ist in der Instrumentenwaehrung (z.B. USD) und darf NICHT mit
    CHF-Einstandspreisen verglichen werden. Korrekt ist
    walletImpact.currentValue / quantity (bereits in Kontowaehrung)."""
    wi = p.get("walletImpact") or {}
    qty = p.get("quantity") or 0
    if wi.get("currentValue") is not None and qty:
        return float(wi["currentValue"]) / float(qty)
    return None

BASE_URLS = {
    "live": "https://live.trading212.com/api/v0",
    "demo": "https://demo.trading212.com/api/v0",
}


def _load_env(path: Path = ENV_PATH) -> dict[str, str]:
    """Liest die .env-Datei. Unterstuetzt 'KEY=VALUE' und 'KEY:VALUE'."""
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f".env nicht gefunden: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        sep = "=" if "=" in line else (":" if ":" in line else None)
        if sep is None:
            continue
        key, _, value = line.partition(sep)
        values[key.strip().upper()] = value.strip()
    return values


class RateLimitError(RuntimeError):
    pass


class T212ApiError(RuntimeError):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"T212 API Fehler {status_code}: {body}")
        self.status_code = status_code
        self.body = body


@dataclass
class T212Client:
    environment: str = "demo"  # "live" oder "demo"
    timeout: float = 15.0

    def __post_init__(self) -> None:
        if self.environment not in BASE_URLS:
            raise ValueError("environment muss 'live' oder 'demo' sein")
        env = _load_env()
        prefix = "LIVE" if self.environment == "live" else "DEMO"
        api_key = env.get(f"{prefix}_API_KEY")
        api_secret = env.get(f"{prefix}_SECRET")
        if not api_key or not api_secret:
            raise RuntimeError(
                f"API Key/Secret fuer '{self.environment}' fehlen in .env "
                f"(erwartet {prefix}_API_KEY / {prefix}_SECRET)"
            )
        credentials = f"{api_key}:{api_secret}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(credentials).decode("utf-8")
        self._base_url = BASE_URLS[self.environment]
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": self._auth_header, "Content-Type": "application/json"}
        )

    # -- low-level -----------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        response = self._session.request(method, url, timeout=self.timeout, **kwargs)
        if response.status_code == 429:
            raise RateLimitError(f"Rate limit erreicht fuer {method} {path}")
        if not response.ok:
            raise T212ApiError(response.status_code, response.text)
        if response.text:
            return response.json()
        return None

    # -- account -------------------------------------------------------
    def get_account_summary(self) -> dict:
        return self._request("GET", "/equity/account/summary")

    def get_positions(self) -> list:
        return self._request("GET", "/equity/positions")

    # -- instruments -----------------------------------------------------
    def get_instruments(self) -> list:
        return self._request("GET", "/equity/metadata/instruments")

    def find_instrument(self, needle: str) -> list:
        """Sucht Instrumente, deren Ticker oder Name 'needle' enthaelt (case-insensitive)."""
        needle_low = needle.lower()
        instruments = self.get_instruments()
        return [
            i for i in instruments
            if needle_low in str(i.get("ticker", "")).lower()
            or needle_low in str(i.get("name", "")).lower()
        ]

    # -- orders ----------------------------------------------------------
    def get_open_orders(self) -> list:
        return self._request("GET", "/equity/orders")

    def get_order(self, order_id: str) -> dict:
        return self._request("GET", f"/equity/orders/{order_id}")

    def get_order_history(self, ticker: Optional[str] = None, limit: int = 50) -> list:
        """Historische (bereits abgeschlossene: gefuellte/stornierte/
        abgelaufene) Orders -- ANDERER Endpunkt als get_order()/
        get_open_orders(), die nur LEBENDE Orders kennen. Wichtig: bei
        den ersten Live-Tests (Sept. 2026) lieferte get_order() fuer
        laengst gefuellte Orders ein 404 zurueck, statt den finalen
        Status zu zeigen -- die Order war offenbar bereits in die
        Historie gewandert. book_fills.py nutzt diesen Endpunkt deshalb
        als Fallback, bevor eine Order als 'nicht auffindbar' quittiert
        wird. Format laut oeffentlicher T212-API-Doku (Beta, Stand
        Sept. 2026); falls sich das Antwortformat unterscheidet, bitte
        eine Beispielantwort an Claude weitergeben, um das Feld-Mapping
        in book_fills.py._extract_fill_price() nachzuziehen."""
        params: dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        result = self._request("GET", "/equity/history/orders", params=params)
        if isinstance(result, dict):
            return result.get("items", result.get("data", []))
        return result or []

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", f"/equity/orders/{order_id}")

    def place_market_order(self, ticker: str, quantity: float) -> dict:
        """quantity > 0 = Kauf, quantity < 0 = Verkauf einer bestehenden Position."""
        self._assert_nonzero(quantity)
        body = {"ticker": ticker, "quantity": quantity}
        return self._request("POST", "/equity/orders/market", json=body)

    def place_limit_order(
        self, ticker: str, quantity: float, limit_price: float, time_validity: str = "DAY"
    ) -> dict:
        self._assert_nonzero(quantity)
        body = {
            "ticker": ticker,
            "quantity": quantity,
            "limitPrice": limit_price,
            "timeValidity": time_validity,
        }
        return self._request("POST", "/equity/orders/limit", json=body)

    def place_stop_order(
        self, ticker: str, quantity: float, stop_price: float, time_validity: str = "DAY"
    ) -> dict:
        """Fuer Stop-Loss-Absicherung bestehender Long-Positionen (quantity < 0)."""
        self._assert_nonzero(quantity)
        body = {
            "ticker": ticker,
            "quantity": quantity,
            "stopPrice": stop_price,
            "timeValidity": time_validity,
        }
        return self._request("POST", "/equity/orders/stop", json=body)

    @staticmethod
    def _assert_nonzero(quantity: float) -> None:
        if quantity == 0:
            raise ValueError("quantity darf nicht 0 sein")
