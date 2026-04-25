from __future__ import annotations

from dataclasses import asdict
from typing import Any

from crypto_paper_bot.light_ml import predict_from_storage, train_from_storage
from crypto_paper_bot.light_strategy import build_light_signal, risk_plan
from crypto_paper_bot.real_market import BinancePublicClient, display_symbol
from crypto_paper_bot.storage import BotStorage

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
INTERVALS = ["1h", "1d", "1w"]
PAPER_TRADE_NOTIONAL = 250.0


class AppServices:
    def __init__(self, storage: BotStorage | None = None) -> None:
        self.storage = storage or BotStorage()
        self.client = BinancePublicClient()

    def collect_market_data(self) -> dict[str, Any]:
        rows = 0
        errors = []
        for symbol in SYMBOLS:
            pretty = display_symbol(symbol)
            for interval in INTERVALS:
                try:
                    limit = 500 if interval == "1h" else 160
                    candles = self.client.klines(symbol, interval, limit=limit)
                    rows += self.storage.upsert_candles(pretty, interval, candles)
                except Exception as exc:
                    errors.append({"symbol": pretty, "interval": interval, "error": str(exc)})
        self.storage.event("INFO", "Veri toplama tamamlandı", {"rows": rows, "errors": errors})
        return {"rows": rows, "errors": errors}

    def train_light_model(self, symbol: str = "BTC/USDT") -> dict[str, Any]:
        result = train_from_storage(self.storage, symbol=symbol, interval="1h")
        payload = asdict(result)
        self.storage.event("INFO", "Yapay zekâ eğitimi tamamlandı", payload)
        return payload

    def analyze_symbol(self, symbol: str) -> dict[str, Any]:
        pretty = display_symbol(symbol)
        h1_raw = self.client.klines(symbol, "1h", 200)
        d1_raw = self.client.klines(symbol, "1d", 120)
        w1_raw = self.client.klines(symbol, "1w", 80)
        self.storage.upsert_candles(pretty, "1h", h1_raw)
        self.storage.upsert_candles(pretty, "1d", d1_raw)
        self.storage.upsert_candles(pretty, "1w", w1_raw)

        h1 = build_light_signal(h1_raw)
        d1 = build_light_signal(d1_raw)
        w1 = build_light_signal(w1_raw)
        book = self.client.order_book(symbol, 50)
        ml_probability = predict_from_storage(self.storage, pretty, "1h")
        plan = risk_plan(h1.close, h1.atr)
        decision = "İZLE"
        explanation = "Şartlar işlem için yeterince güçlü değil."
        if w1.ema_signal == 1.0 and d1.ema_signal == 1.0 and h1.final_score >= 0.70 and plan.get("ok"):
            decision = "SANAL ALIM ADAYI"
            explanation = "Haftalık ve günlük yön olumlu, saatlik skor eşiği geçti."
        payload = {
            "symbol": pretty,
            "bid": book.bid,
            "ask": book.ask,
            "spread_pct": book.spread_pct,
            "score": h1.final_score,
            "ml_probability": ml_probability,
            "weekly_ok": w1.ema_signal == 1.0,
            "daily_ok": d1.ema_signal == 1.0,
            "decision": decision,
            "risk_plan": plan,
            "explanation": explanation,
            "reason": h1.reason,
        }
        self.storage.log_signal(pretty, h1.final_score, ml_probability, decision, payload)
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
        notional = PAPER_TRADE_NOTIONAL
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
            self.storage.event("INFO", "Sanal işlem açıldı", {"symbol": analysis["symbol"], "entry": entry, "notional": notional})
            return {"opened": True, "symbol": analysis["symbol"], "entry": entry, "notional": notional}
        return {"opened": False, "reason": "Sanal bakiye yetersiz"}

    def update_open_positions(self) -> dict[str, Any]:
        closed = []
        prices: dict[str, float] = {}
        for pos in self.storage.open_positions():
            try:
                book = self.client.order_book(pos["symbol"], 10)
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
            except Exception as exc:
                self.storage.event("ERROR", "Açık işlem güncellenemedi", {"error": str(exc), "position": pos})
        equity = self.storage.record_equity(prices)
        return {"closed": closed, "equity": equity}

    def cycle(self) -> dict[str, Any]:
        collected = self.collect_market_data()
        trained = self.train_light_model("BTC/USDT")
        analyses = [self.analyze_symbol(symbol) for symbol in SYMBOLS]
        opened = []
        for analysis in analyses:
            result = self.maybe_open_paper_trade(analysis)
            if result:
                opened.append(result)
        positions = self.update_open_positions()
        return {
            "collected": collected,
            "trained": trained,
            "analyses": analyses,
            "opened": opened,
            "positions": positions,
            "db_rows": self.storage.candle_count(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "db_rows": self.storage.candle_count(),
            "model": self.storage.load_model_state(),
            "latest_signals": self.storage.latest_signals(10),
            "events": self.storage.latest_events(10),
            "wallet": self.storage.wallet(),
            "equity": self.storage.equity_points(80),
            "trade_stats": self.storage.trade_stats(),
            "positions": self.storage.all_positions(30),
        }

    def reset_account(self) -> None:
        self.storage.reset_paper_account()
        self.storage.event("INFO", "Sanal hesap sıfırlandı", {})
