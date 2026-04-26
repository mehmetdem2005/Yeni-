from __future__ import annotations

from typing import Any

from crypto_paper_bot.confidence_engine import (
    build_confidence_input,
    calculate_trade_confidence,
    confidence_snapshot_as_plain_dict,
    trade_stats_to_component_stats,
)
from crypto_paper_bot.family_engine import build_family_scores, family_scores_as_plain_dict
from crypto_paper_bot.indicator_engine import build_indicator_snapshot
from crypto_paper_bot.light_ml import predict_from_storage
from crypto_paper_bot.real_market import display_symbol
from crypto_paper_bot.service_utils import RateLimitedBinance, store_logs
from crypto_paper_bot.smart_risk_engine import build_smart_risk_plan, risk_plan_as_plain_dict
from crypto_paper_bot.storage import BotStorage

MIN_TRADE_CONFIDENCE = 0.70


class AnalysisService:
    def __init__(self, storage: BotStorage, market: RateLimitedBinance) -> None:
        self.storage = storage
        self.market = market

    def _latest_equity(self) -> float:
        points = self.storage.equity_points(1)
        if points:
            return float(points[-1]["equity"])
        return float(self.storage.wallet().get("cash", 10000.0))

    def analyze_symbol(self, symbol: str, system_confidence: dict[str, Any]) -> dict[str, Any]:
        pretty = display_symbol(symbol)
        h1_raw = self.market.klines(symbol, "1h", 200)
        d1_raw = self.market.klines(symbol, "1d", 120)
        w1_raw = self.market.klines(symbol, "1w", 80)

        self.storage.upsert_candles(pretty, "1h", h1_raw)
        self.storage.upsert_candles(pretty, "1d", d1_raw)
        self.storage.upsert_candles(pretty, "1w", w1_raw)

        h1_indicator = build_indicator_snapshot(pretty, h1_raw)
        d1_indicator = build_indicator_snapshot(pretty, d1_raw)
        w1_indicator = build_indicator_snapshot(pretty, w1_raw)
        store_logs(self.storage, h1_indicator.logs + d1_indicator.logs + w1_indicator.logs)

        weekly_ok = w1_indicator.ema_signal >= 0.65
        daily_ok = d1_indicator.ema_signal >= 0.65
        book = self.market.order_book(symbol, 50)
        ml_probability = predict_from_storage(self.storage, pretty, "1h")

        family_snapshot = build_family_scores(
            h1_indicator,
            ai_probability=ml_probability,
            weekly_ok=weekly_ok,
            daily_ok=daily_ok,
        )
        store_logs(self.storage, family_snapshot.logs)

        liquidity_score = max(0.0, min(1.0, 1.0 - (book.spread_pct / 0.003)))
        component_stats = trade_stats_to_component_stats(self.storage.all_positions(1000))

        # First pass: neutral RR score; then risk engine returns real R/R and we recompute.
        confidence_input = build_confidence_input(
            family_snapshot,
            liquidity_score=liquidity_score,
            risk_reward_score=0.70,
            portfolio_safety_score=1.0 if not self.storage.open_positions() else 0.60,
        )
        trade_conf = calculate_trade_confidence(pretty, confidence_input, component_stats)
        store_logs(self.storage, trade_conf.logs)

        sys_conf_value = float(system_confidence.get("system_confidence") or 0.0)
        risk_plan = build_smart_risk_plan(
            pretty,
            h1_raw,
            h1_indicator,
            trade_conf,
            sys_conf_value,
            self._latest_equity(),
        )
        store_logs(self.storage, risk_plan.logs)

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
        store_logs(self.storage, trade_conf.logs)

        risk_plan = build_smart_risk_plan(
            pretty,
            h1_raw,
            h1_indicator,
            trade_conf,
            sys_conf_value,
            self._latest_equity(),
        )
        store_logs(self.storage, risk_plan.logs)

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

    def analyze_symbols(self, symbols: list[str], system_confidence: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for symbol in symbols:
            results.append(self.analyze_symbol(symbol, system_confidence))
        return results
