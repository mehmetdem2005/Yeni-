from __future__ import annotations

from typing import Any

from crypto_paper_bot.analysis_service import AnalysisService
from crypto_paper_bot.confidence_engine import calculate_system_confidence, system_confidence_as_plain_dict
from crypto_paper_bot.log_channels import normalize_legacy_event
from crypto_paper_bot.market_data_service import DEFAULT_SYMBOLS, MarketDataService
from crypto_paper_bot.news_feed import NewsFeedClient
from crypto_paper_bot.news_service import NewsService
from crypto_paper_bot.paper_trade_service import PaperTradeService
from crypto_paper_bot.rate_limiter import RateLimiter
from crypto_paper_bot.real_market import BinancePublicClient
from crypto_paper_bot.service_utils import RateLimitedBinance, store_logs
from crypto_paper_bot.storage import BotStorage
from crypto_paper_bot.training_service import TrainingService

SYMBOLS = DEFAULT_SYMBOLS


class AppServices:
    """Application facade.

    This class coordinates services but does not own the full business logic anymore.
    Heavy responsibilities are split into dedicated modules:
    - MarketDataService
    - TrainingService
    - AnalysisService
    - PaperTradeService
    - NewsService
    """

    def __init__(self, storage: BotStorage | None = None) -> None:
        self.storage = storage or BotStorage()
        self.rate_limiter = RateLimiter(min_interval_seconds=10)
        self.market = RateLimitedBinance(
            storage=self.storage,
            client=BinancePublicClient(),
            rate_limiter=self.rate_limiter,
        )
        self.market_data = MarketDataService(self.storage, self.market)
        self.training = TrainingService(self.storage)
        self.analysis = AnalysisService(self.storage, self.market)
        self.paper = PaperTradeService(self.storage, self.market)
        self.news = NewsService(self.storage, NewsFeedClient(rate_limiter=self.rate_limiter))

    def collect_market_data(self) -> dict[str, Any]:
        return self.market_data.collect()

    def train_light_model(self, symbol: str = "BTC/USDT") -> dict[str, Any]:
        return self.training.train_light_model(symbol=symbol, interval="1h")

    def current_system_confidence(self) -> dict[str, Any]:
        snapshot = calculate_system_confidence(
            candle_count=self.storage.candle_count(),
            model_state=self.storage.load_model_state(),
            latest_events=self.storage.latest_events(30),
            wallet=self.storage.wallet(),
            trade_stats=self.storage.trade_stats(),
            open_positions=self.storage.open_positions(),
        )
        store_logs(self.storage, snapshot.logs)
        return system_confidence_as_plain_dict(snapshot)

    def analyze_symbol(self, symbol: str, system_confidence: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.analysis.analyze_symbol(symbol, system_confidence or self.current_system_confidence())

    def analyze_symbols(self, symbols: list[str] | None = None, system_confidence: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        symbols = symbols or SYMBOLS
        confidence = system_confidence or self.current_system_confidence()
        return self.analysis.analyze_symbols(symbols, confidence)

    def maybe_open_paper_trade(self, analysis: dict[str, Any]) -> dict[str, Any] | None:
        return self.paper.maybe_open_from_analysis(analysis)

    def update_open_positions(self) -> dict[str, Any]:
        return self.paper.update_open_positions()

    def fetch_news(self) -> dict[str, Any]:
        return self.news.fetch_news()

    def cycle(self) -> dict[str, Any]:
        collected = self.collect_market_data()
        trained = self.train_light_model("BTC/USDT")
        system_conf = self.current_system_confidence()
        analyses = self.analyze_symbols(SYMBOLS, system_confidence=system_conf)
        opened = self.paper.maybe_open_many(analyses)
        positions = self.update_open_positions()
        news = self.fetch_news()
        return {
            "collected": collected,
            "trained": trained,
            "system_confidence": system_conf,
            "analyses": analyses,
            "indicator_snapshots": [item["indicator"] for item in analyses],
            "family_snapshots": [item["family"] for item in analyses],
            "risk_plans": [item["risk_plan"] for item in analyses],
            "opened": opened,
            "positions": positions,
            "news": news,
            "db_rows": self.storage.candle_count(),
        }

    def status(self) -> dict[str, Any]:
        legacy_logs = [normalize_legacy_event(row) for row in self.storage.latest_events(80)]
        return {
            "db_rows": self.storage.candle_count(),
            "model": self.storage.load_model_state(),
            "latest_signals": self.storage.latest_signals(10),
            "events": self.storage.latest_events(10),
            "logs": legacy_logs,
            "wallet": self.storage.wallet(),
            "equity": self.storage.equity_points(80),
            "trade_stats": self.storage.trade_stats(),
            "positions": self.storage.all_positions(30),
            "system_confidence": self.current_system_confidence(),
            "rate_limits": self.rate_limiter.snapshot(),
        }

    def reset_account(self) -> None:
        self.storage.reset_paper_account()
        self.storage.event("INFO", "Sanal hesap sıfırlandı", {"channel": "system"})
