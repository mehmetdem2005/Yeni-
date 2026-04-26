from __future__ import annotations

from typing import Any

from crypto_paper_bot.service_utils import RateLimitedBinance
from crypto_paper_bot.storage import BotStorage


class PaperTradeService:
    def __init__(self, storage: BotStorage, market: RateLimitedBinance) -> None:
        self.storage = storage
        self.market = market

    def maybe_open_from_analysis(self, analysis: dict[str, Any]) -> dict[str, Any] | None:
        if analysis.get("decision") != "SANAL ALIM ADAYI":
            return None
        if self.storage.open_positions():
            return None

        plan = analysis.get("risk_plan") or {}
        if not plan.get("ok"):
            return None

        entry = float(analysis["ask"])
        notional = float(plan.get("final_position_notional") or 0.0)
        if entry <= 0 or notional <= 0:
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
        if not opened:
            return {"opened": False, "reason": "Sanal bakiye yetersiz"}

        payload = {"symbol": analysis["symbol"], "entry": entry, "notional": notional, "qty": qty}
        self.storage.event("INFO", "Sanal işlem açıldı", {"channel": "trade", **payload})
        return {"opened": True, **payload}

    def maybe_open_many(self, analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        opened: list[dict[str, Any]] = []
        for analysis in analyses:
            result = self.maybe_open_from_analysis(analysis)
            if result:
                opened.append(result)
        return opened

    def update_open_positions(self) -> dict[str, Any]:
        closed: list[dict[str, Any]] = []
        prices: dict[str, float] = {}

        for pos in self.storage.open_positions():
            try:
                book = self.market.order_book(pos["symbol"], 10)
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
                    record = {"symbol": pos["symbol"], "reason": reason, "pnl": pnl, "close_price": price}
                    closed.append(record)
                    self.storage.event("INFO", "Sanal işlem kapandı", {"channel": "trade", **record})
            except Exception as exc:
                self.storage.event(
                    "ERROR",
                    "Açık işlem güncellenemedi",
                    {"channel": "error", "error": str(exc), "position": pos},
                )

        equity = self.storage.record_equity(prices)
        return {"closed": closed, "equity": equity}
