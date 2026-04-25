from __future__ import annotations

from typing import Protocol

from crypto_paper_bot.filters import OrderBookSnapshot
from crypto_paper_bot.models import Candle, TimeFrame


class MarketDataClient(Protocol):
    """Read-only market data interface used by the strategy engine."""

    def fetch_candles(self, symbol: str, timeframe: TimeFrame, limit: int = 200) -> list[Candle]:
        ...

    def fetch_book(self, symbol: str, limit: int = 50) -> OrderBookSnapshot:
        ...

    def fetch_status(self) -> dict | None:
        ...
