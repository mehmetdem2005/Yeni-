from __future__ import annotations

from typing import Any

from crypto_paper_bot.real_market import display_symbol
from crypto_paper_bot.service_utils import RateLimitedBinance
from crypto_paper_bot.storage import BotStorage

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
DEFAULT_INTERVALS = ["1h", "1d", "1w"]


class MarketDataService:
    def __init__(self, storage: BotStorage, market: RateLimitedBinance) -> None:
        self.storage = storage
        self.market = market

    def collect(
        self,
        symbols: list[str] | None = None,
        intervals: list[str] | None = None,
    ) -> dict[str, Any]:
        symbols = symbols or DEFAULT_SYMBOLS
        intervals = intervals or DEFAULT_INTERVALS
        rows = 0
        errors: list[dict[str, str]] = []

        for symbol in symbols:
            pretty = display_symbol(symbol)
            for interval in intervals:
                try:
                    limit = 500 if interval == "1h" else 160
                    candles = self.market.klines(symbol, interval, limit)
                    rows += self.storage.upsert_candles(pretty, interval, candles)
                except Exception as exc:
                    errors.append({"symbol": pretty, "interval": interval, "error": str(exc)})

        self.storage.event(
            "INFO",
            "Veri toplama tamamlandı",
            {"channel": "data", "rows": rows, "errors": errors},
        )
        return {"rows": rows, "errors": errors}
