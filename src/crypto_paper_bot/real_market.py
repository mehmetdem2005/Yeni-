from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from crypto_paper_bot.book import OrderBookSnapshot


BINANCE_SPOT_BASE = "https://api.binance.com"


@dataclass(frozen=True)
class LightCandle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def _get_json(path: str, params: dict[str, str | int] | None = None, timeout: int = 15):
    query = "" if not params else "?" + urllib.parse.urlencode(params)
    url = BINANCE_SPOT_BASE + path + query
    request = urllib.request.Request(url, headers={"User-Agent": "crypto-paper-bot/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("-", "").upper()


def display_symbol(symbol: str) -> str:
    raw = normalize_symbol(symbol)
    if raw.endswith("USDT"):
        return raw[:-4] + "/USDT"
    return raw


class BinancePublicClient:
    def ticker_book(self, symbol: str) -> dict[str, float | str]:
        raw_symbol = normalize_symbol(symbol)
        data = _get_json("/api/v3/ticker/bookTicker", {"symbol": raw_symbol})
        return {
            "symbol": display_symbol(raw_symbol),
            "bid": float(data["bidPrice"]),
            "bid_qty": float(data["bidQty"]),
            "ask": float(data["askPrice"]),
            "ask_qty": float(data["askQty"]),
        }

    def order_book(self, symbol: str, limit: int = 50) -> OrderBookSnapshot:
        raw_symbol = normalize_symbol(symbol)
        data = _get_json("/api/v3/depth", {"symbol": raw_symbol, "limit": limit})
        bids = [(float(price), float(qty)) for price, qty in data.get("bids", [])]
        asks = [(float(price), float(qty)) for price, qty in data.get("asks", [])]
        if not bids or not asks:
            raise RuntimeError("Empty order book")
        return OrderBookSnapshot(bid=bids[0][0], ask=asks[0][0], bids=bids, asks=asks)

    def klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> list[LightCandle]:
        raw_symbol = normalize_symbol(symbol)
        rows = _get_json("/api/v3/klines", {"symbol": raw_symbol, "interval": interval, "limit": limit})
        candles: list[LightCandle] = []
        for row in rows:
            candles.append(
                LightCandle(
                    timestamp=datetime.fromtimestamp(int(row[0]) / 1000.0, tz=timezone.utc),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        return candles

    def server_time(self) -> datetime:
        data = _get_json("/api/v3/time")
        return datetime.fromtimestamp(int(data["serverTime"]) / 1000.0, tz=timezone.utc)
