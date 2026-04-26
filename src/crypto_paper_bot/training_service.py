from __future__ import annotations

from dataclasses import asdict
from typing import Any

from crypto_paper_bot.light_ml import train_from_storage
from crypto_paper_bot.storage import BotStorage


class TrainingService:
    def __init__(self, storage: BotStorage) -> None:
        self.storage = storage

    def train_light_model(self, symbol: str = "BTC/USDT", interval: str = "1h") -> dict[str, Any]:
        result = train_from_storage(self.storage, symbol=symbol, interval=interval)
        payload = asdict(result)
        self.storage.event("INFO", "Yapay zekâ eğitimi tamamlandı", {"channel": "ai", **payload})
        return payload
