from __future__ import annotations

from dataclasses import dataclass

from crypto_paper_bot.config import ExecutionConfig
from crypto_paper_bot.filters import OrderBookSnapshot
from crypto_paper_bot.models import PaperOrderResult


@dataclass(frozen=True)
class PaperBuyRequest:
    symbol: str
    quote_notional: float
    reference_price: float


def simulate_aggressive_limit_buy(
    request: PaperBuyRequest,
    book: OrderBookSnapshot,
    cfg: ExecutionConfig,
) -> PaperOrderResult:
    """Simulate a long-only aggressive limit buy.

    Paper-trade rule: touching the limit price is not enough. We consume visible asks
    up to the limit, then apply a conservative queue factor.
    """

    if request.quote_notional <= 0 or request.reference_price <= 0:
        return PaperOrderResult(request.symbol, 0.0, 0.0, 0.0, None, "none", 0.0, 0.0, "rejected")

    limit_price = book.ask * (1 + cfg.aggressive_limit_offset_pct)
    target_qty = request.quote_notional / request.reference_price
    remaining_quote = request.quote_notional
    filled_qty = 0.0
    spent = 0.0

    # Conservative queue factor: only half of visible liquidity is assumed accessible.
    queue_factor = 0.50
    for price, qty in book.asks:
        if price > limit_price or remaining_quote <= 0:
            break
        usable_qty = qty * queue_factor
        quote_here = min(remaining_quote, price * usable_qty)
        qty_here = quote_here / price
        filled_qty += qty_here
        spent += quote_here
        remaining_quote -= quote_here

    fill_ratio = 0.0 if target_qty <= 0 else min(filled_qty / target_qty, 1.0)
    avg_price = None if filled_qty <= 0 else spent / filled_qty
    fee = spent * cfg.default_fee_rate
    slippage = 0.0
    if avg_price is not None:
        slippage = (avg_price - request.reference_price) / request.reference_price

    status = "filled" if fill_ratio >= 0.999 else "partial" if fill_ratio > 0 else "expired"
    maker_taker = "taker" if fill_ratio > 0 else "none"
    return PaperOrderResult(
        symbol=request.symbol,
        requested_qty=target_qty,
        filled_qty=filled_qty,
        fill_ratio=fill_ratio,
        avg_fill_price=avg_price,
        maker_taker=maker_taker,
        fee_paid=fee,
        slippage_pct=slippage,
        status=status,
    )


def simulate_exit_fee(notional: float, cfg: ExecutionConfig) -> float:
    return max(notional, 0.0) * cfg.default_fee_rate
