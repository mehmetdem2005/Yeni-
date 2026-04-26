from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, TypeVar

from crypto_paper_bot.confidence_engine import (
    build_confidence_input,
    calculate_system_confidence,
    calculate_trade_confidence,
    confidence_snapshot_as_plain_dict,
    system_confidence_as_plain_dict,
    trade_stats_to_component_stats,
)
from crypto_paper_bot.family_engine import build_family_scores, family_scores_as_plain_dict
from crypto_paper_bot.indicator_engine import build_indicator_snapshot
from crypto_paper_bot.light_ml import predict_from_storage, train_from_storage
from crypto_paper_bot.log_channels import LogRecord, normalize_legacy_event
from crypto_paper_bot.news_feed import NewsFeedClient, news_items_as_plain_dict
from crypto_paper_bot.rate_limiter import RateLimiter
from crypto_paper_bot.real_market import BinancePublicClient, display_symbol
from crypto_paper_bot.smart_risk_engine import build_smart_risk_plan, risk_plan_as_plain_dict
from crypto_paper_bot.storage import BotStorage

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
INTERVALS = ["1h", "1d", "1w"]
MIN_TRADE_CONFIDENCE = 0.70

T = TypeVar("T")


class AppServices:
    def __init__(self, storage: BotStorage | None = None) -> None:
        self.storage = storage or BotStorage()
        self.client = BinancePublicClient()
        self.rate_limiter = RateLimiter(min_interval_seconds=10)
        self.news = NewsFeedClient(rate_limiter=self.rate_limiter)

    def _store_logs(self, logs: list[LogRecord]) -> None:
        for record in logs:
            self.storage.event(record.level.value, record.message, record.to_event_payload())

    def _binance_call(self, description: str, func: Callable[[], T]) -> T:
        key = "binance:public"
        waited = self.rate_limiter.wait_if_needed(key)
        try:
            result = func()
            self.rate_limiter.success(key)
            if waited > 0:
                self.storage.event(
                    "INFO",
                    "Rate-limit beklemesi uygulandı",
                    {"channel": "rate_limit", "source": "binance", "description": description, "waited_seconds": waited},
                )
            return result
        except Exception as exc:
            cooldown = self.rate_limiter.failure(key, exc)
            self.storage.event(
                "ERROR",
                "Binance isteği başarısız oldu",
                {"channel": "error", "source": "binance", "description": description, "error": str(exc), "cooldown_seconds": cooldown},
            )
            raise

    def collect_market_data(self) -> dict[str, Any]:
        rows = 0
        errors = []
        for symbol in SYMBOLS:
            pretty = display_symbol(symbol)
            for interval in INTERVALS:
                try:
                    limit = 500 if interval == "1h" else 160
                    candles = self._binance_call(
                        f"{pretty} {interval} mum verisi",
                        lambda symbol=symbol, interval=interval, limit=limit: self.client.klines(symbol, interval, limit=limit),
                    )
                    rows += self.storage.upsert_candles(pretty, interval, candles)
                except Exception as exc:
                    errors.append({"symbol": pretty, "interval": interval, "error": str(exc)})
        self.storage.event("INFO", "Veri toplama tamamlandı", {"channel": "data", "rows": rows, "errors": errors})
        return {"rows": rows, "errors": errors}

    def train_light_model(self, symbol: str = "BTC/USDT") -> dict[str, Any]:
        result = train_from_storage(self.storage, symbol=symbol, interval="1h")
        payload = asdict(result)
        self.storage.event("INFO", "Yapay zekâ eğitimi tamamlandı", {"channel": "ai", **payload})
        return payload

    def _current_system_confidence(self) -> dict[str, Any]:
        snapshot = calculate_system_confidence(
            candle_count=self.storage.candle_count(),
            model_state=self.storage.load_model_state(),
            latest_events=self.storage.latest_events(30),
            wallet=self.storage.wallet(),
            trade_stats=self.storage.trade_stats(),
            open_positions=self.storage.open_positions(),
        )
        self._store_logs(snapshot.logs)
        return system_confidence_as_plain_dict(snapshot)

    def analyze_symbol(self, symbol: str, system_confidence: dict[str, Any] | None = None) -> dict[str, Any]:
        pretty = display_symbol(symbol)
        h1_raw = self._binance_call(f"{pretty} saatlik mum verisi", lambda: self.client.klines(symbol, "1h", 200))
        d1_raw = self._binance_call(f"{pretty} günlük mum verisi", lambda: self.client.klines(symbol, "1d", 120))
        w1_raw = self._binance_call(f"{pretty} haftalık mum verisi", lambda: self.client.klines(symbol, "1w", 80))
        self.storage.upsert_candles(pretty, "1h", h1_raw)
        self.storage.upsert_candles(pretty, "1d", d1_raw)
        self.storage.upsert_candles(pretty, "1w", w1_raw)

        h1_indicator = build_indicator_snapshot(pretty, h1_raw)
        d1_indicator = build_indicator_snapshot(pretty, d1_raw)
        w1_indicator = build_indicator_snapshot(pretty, w1_raw)
        self._store_logs(h1_indicator.logs + d1_indicator.logs + w1_indicator.logs)

        weekly_ok = w1_indicator.ema_signal >= 0.65
        daily_ok = d1_indicator.ema_signal >= 0.65
        book = self._binance_call(f"{pretty} emir defteri", lambda: self.client.order_book(symbol, 50))
        ml_probability = predict_from_storage(self.storage, pretty, "1h")

        family_snapshot = build_family_scores(
            h1_indicator,
            ai_probability=ml_probability,
            weekly_ok=weekly_ok,
            daily_ok=daily_ok,
        )
        self._store_logs(family_snapshot.logs)

        liquidity_score = max(0.0, min(1.0, 1.0 - (book.spread_pct / 0.003)))
        component_stats = trade_stats_to_component_stats(self.storage.all_positions(1000))
        confidence_input = build_confidence_input(
            family_snapshot,
            liquidity_score=liquidity_score,
            risk_reward_score=0.70,
            portfolio_safety_score=1.0 if not self.storage.open_positions() else 0.60,
        )
        trade_conf = calculate_trade_confidence(pretty, confidence_input, component_stats)
        self._store_logs(trade_conf.logs)

        sys_conf = system_confidence or self._current_system_confidence()
        risk_plan = build_smart_risk_plan(
            pretty,
            h1_raw,
            h1_indicator,
            trade_conf,
            float(sys_conf.get("system_confidence") or 0.5),
            float((self.storage.equity_points(1)[-1]["equity"] if self.storage.equity_points(1) else self.storage.wallet().get("cash", 10000.0))),
        )
        self._store_logs(risk_plan.logs)

        rr_score = 0.5
        if risk_plan.reward_risk is not None:
            rr_score = max(0.0, min(1.0, (risk_plan.reward_risk - 1.0) / 2.0))
        confidence_input = build_confidence_input(
            family_snapshot,
            liquidity_score=liquidity_score,
            risk_reward_score=rr_score,
            portfolio_safety_score=1.0 if not self.storage.open_positions() else 0.60,
        )
        trade_conf = calculate_trade_confidence(pretty, confidence_input, component_stats)
        self._store_logs(trade_conf.logs)
        risk_plan = build_smart_risk_plan(
            pretty,
            h1_raw,
            h1_indicator,
            trade_conf,
            float(sys_conf.get("system_confidence") or 0.5),
            float((self.storage.equity_points(1)[-1]["equity"] if self.storage.equity_points(1) else self.storage.wallet().get("cash", 10000.0))),
        )
        self._store_logs(risk_plan.logs)

        decision = "İZLE"
        explanation = "Sistem izliyor; işlem özgüveni veya risk planı henüz yeterli değil."
        if trade_conf.trade_confidence >= MIN_TRADE_CONFIDENCE and risk_plan.ok and weekly_ok and daily_ok:
            decision = "SANAL ALIM ADAYI"
            explanation = "İndikatörler, aile skorları, özgüven ve risk planı sanal işlem için yeterli."

        payload = {
            "symbol": pretty,
            "bid": book.bid,
            "ask": book.ask,
            "spread_pct": book.spread_pct,
            "score": h1_indicator.indicator_score,
            "ml_probability": ml_probability,
            "weekly_ok": weekly_ok,
            "daily_ok": daily_ok,
            "decision": decision,
            "explanation": explanation,
            "indicator": {
                "symbol": h1_indicator.symbol,
                "timestamp": h1_indicator.timestamp,
                "price": h1_indicator.price,
                "ema_value": h1_indicator.ema_value,
                "ema_signal": h1_indicator.ema_signal,
                "rsi_value": h1_indicator.rsi_value,
                "rsi_signal": h1_indicator.rsi_signal,
                "atr_value": h1_indicator.atr_value,
                "atr_pct": h1_indicator.atr_pct,
                "volume_ratio": h1_indicator.volume_ratio,
                "volume_signal": h1_indicator.volume_signal,
                "indicator_score": h1_indicator.indicator_score,
                "decision_comment": h1_indicator.decision_comment,
            },
            "family": family_scores_as_plain_dict(family_snapshot),
            "confidence": confidence_snapshot_as_plain_dict(trade_conf),
            "risk_plan": risk_plan_as_plain_dict(risk_plan),
        }
        self.storage.log_signal(pretty, h1_indicator.indicator_score, ml_probability, decision, payload)
        return payload

    def maybe_open_paper_trade(self, analysis: dict[str, Any]) -> dict[str, Any] | None:
        if analysis.get("decision") != "SANAL ALIM ADAYI":
            return None
        if self.storage.open_positions():
            return None
        plan = analysis.get("risk_plan") or {}
        if not plan.get("ok"):
            return None
        entry = float(analysis["ask"])
        notional = float(plan.get("final_position_notional") or 0.0)
        if notional <= 0:
            return None
        qty = notional / entry
        opened = self.storage.open_position(
            analysis["symbol"],
            entry,
            qty,
            notional,
            float(plan["stop_loss"]),
            float(plan["take_profit"]),
        )
        if opened:
            self.storage.event("INFO", "Sanal işlem açıldı", {"channel": "trade", "symbol": analysis["symbol"], "entry": entry, "notional": notional})
            return {"opened": True, "symbol": analysis["symbol"], "entry": entry, "notional": notional}
        return {"opened": False, "reason": "Sanal bakiye yetersiz"}

    def update_open_positions(self) -> dict[str, Any]:
        closed = []
        prices: dict[str, float] = {}
        for pos in self.storage.open_positions():
            try:
                book = self._binance_call(f"{pos['symbol']} açık pozisyon fiyatı", lambda pos=pos: self.client.order_book(pos["symbol"], 10))
                price = float(book.bid)
                prices[pos["symbol"]] = price
                reason = None
                if price <= float(pos["stop_loss"]):
                    reason = "ZARAR KES"
                elif price >= float(pos["take_profit"]):
                    reason = "KÂR AL"
                if reason:
                    pnl = (price - float(pos["entry_price"])) * float(pos["qty"])
                    self.storage.close_position(int(pos["id"]), price, pnl, reason)
                    closed.append({"symbol": pos["symbol"], "reason": reason, "pnl": pnl})
                    self.storage.event("INFO", "Sanal işlem kapandı", {"channel": "trade", "symbol": pos["symbol"], "reason": reason, "pnl": pnl})
            except Exception as exc:
                self.storage.event("ERROR", "Açık işlem güncellenemedi", {"channel": "error", "error": str(exc), "position": pos})
        equity = self.storage.record_equity(prices)
        return {"closed": closed, "equity": equity}

    def fetch_news(self) -> dict[str, Any]:
        result = self.news.fetch(max_items_per_source=8)
        self._store_logs(result.logs)
        return {
            "items": news_items_as_plain_dict(result.items),
            "source_count": result.source_count,
            "errors": result.errors,
        }

    def cycle(self) -> dict[str, Any]:
        collected = self.collect_market_data()
        trained = self.train_light_model("BTC/USDT")
        system_conf = self._current_system_confidence()
        analyses = [self.analyze_symbol(symbol, system_confidence=system_conf) for symbol in SYMBOLS]
        opened = []
        for analysis in analyses:
            result = self.maybe_open_paper_trade(analysis)
            if result:
                opened.append(result)
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
            "system_confidence": self._current_system_confidence(),
            "rate_limits": self.rate_limiter.snapshot(),
        }

    def reset_account(self) -> None:
        self.storage.reset_paper_account()
        self.storage.event("INFO", "Sanal hesap sıfırlandı", {"channel": "system"})
