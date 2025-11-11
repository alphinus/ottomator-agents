from __future__ import annotations

import datetime as dt
from typing import Any

import requests


class PriceFetchError(RuntimeError):
    pass


class BTCPriceFetcher:
    API_URL = "https://www.bitstamp.net/api/v2/ticker/{pair}"

    def __init__(self, coin_symbol: str = "bitcoin", vs_currency: str = "usd") -> None:
        self.coin_symbol = coin_symbol
        self.vs_currency = vs_currency

    def fetch_last_24h(self) -> dict[str, Any]:
        pair = f"{self._coin_ticker()}{self.vs_currency.lower()}"
        response = requests.get(
            self.API_URL.format(pair=pair),
            timeout=15,
        )
        try:
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise PriceFetchError(f"Bitstamp response error: {exc}") from exc

        last = float(data["last"])
        high = float(data["high"])
        low = float(data["low"])
        vwap = float(data.get("vwap", last))
        open_price = float(data.get("open", last))
        timestamp = int(data.get("timestamp", dt.datetime.utcnow().timestamp()))

        return {
            "current_price": last,
            "high": high,
            "low": low,
            "average": vwap,
            "change_percentage": self._percent_change(open_price, last),
            "sample_points": int(float(data.get("volume", 0)) or 0),
            "from_timestamp": self._seconds_to_iso(timestamp - 86400),
            "to_timestamp": self._seconds_to_iso(timestamp),
        }

    @staticmethod
    def _percent_change(start: float, end: float) -> float:
        if start == 0:
            return 0.0
        return ((end - start) / start) * 100

    @staticmethod
    def _seconds_to_iso(timestamp_s: int | float) -> str:
        return dt.datetime.utcfromtimestamp(timestamp_s).isoformat() + "Z"

    def _coin_ticker(self) -> str:
        mapping = {
            "bitcoin": "btc",
            "ethereum": "eth",
        }
        return mapping.get(self.coin_symbol.lower(), self.coin_symbol[:3].lower())
