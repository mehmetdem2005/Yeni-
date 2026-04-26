from __future__ import annotations

from typing import Callable, TypeVar

from crypto_paper_bot.log_channels import LogRecord
from crypto_paper_bot.rate_limiter import RateLimiter
from crypto_paper_bot.real_market import BinancePublicClient, normalize_symbol
from crypto_paper_bot.storage import BotStorage

T = TypeVar("T")


def store_logs(storage: BotStorage, logs: list[LogRecord]) -> None:
    for record in logs:
        storage.event(record.level.value, record.message, record.to_event_payload())


class RateLimitedBinance:
    """Small wrapper for Binance public calls with endpoint-level rate-limit keys."""

    def __init__(
        self,
        storage: BotStorage,
        client: BinancePublicClient | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.storage = storage
        self.client = client or BinancePublicClient()
        self.rate_limiter = rate_limiter or RateLimiter(min_interval_seconds=10)

    def _call(self, key: str, description: str, func: Callable[[], T]) -> T:
        waited = self.rate_limiter.wait_if_needed(key)
        try:
            result = func()
            self.rate_limiter.success(key)
            if waited > 0:
                self.storage.event(
                    "INFO",
                    "Rate-limit beklemesi uygulandı",
                    {
                        "channel": "rate_limit",
                        "source": "binance",
                        "key": key,
                        "description": description,
                        "waited_seconds": waited,
                    },
                )
            return result
        except Exception as exc:
            cooldown = self.rate_limiter.failure(key, exc)
            self.storage.event(
                "ERROR",
                "Binance isteği başarısız oldu",
                {
                    "channel": "error",
                    "source": "binance",
                    "key": key,
                    "description": description,
                    "error": str(exc),
                    "cooldown_seconds": cooldown,
                },
            )
            raise

    def klines(self, symbol: str, interval: str, limit: int):
        raw = normalize_symbol(symbol)
        key = f"binance:klines:{raw}:{interval}"
        return self._call(key, f"{raw} {interval} mum verisi", lambda: self.client.klines(raw, interval, limit))

    def order_book(self, symbol: str, limit: int = 50):
        raw = normalize_symbol(symbol)
        key = f"binance:book:{raw}:{limit}"
        return self._call(key, f"{raw} emir defteri", lambda: self.client.order_book(raw, limit))

    def snapshot(self):
        return self.rate_limiter.snapshot()
