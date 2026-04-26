from __future__ import annotations

from typing import Any

from crypto_paper_bot.news_feed import NewsFeedClient, news_items_as_plain_dict
from crypto_paper_bot.service_utils import store_logs
from crypto_paper_bot.storage import BotStorage


class NewsService:
    def __init__(self, storage: BotStorage, news_client: NewsFeedClient) -> None:
        self.storage = storage
        self.news_client = news_client

    def fetch_news(self, max_items_per_source: int = 8) -> dict[str, Any]:
        result = self.news_client.fetch(max_items_per_source=max_items_per_source)
        store_logs(self.storage, result.logs)
        return {
            "items": news_items_as_plain_dict(result.items),
            "source_count": result.source_count,
            "errors": result.errors,
        }
