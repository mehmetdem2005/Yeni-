from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crypto_paper_bot.config import ExecutionConfig


@dataclass(frozen=True)
class OrderBookSnapshot:
    bid: float
    ask: float
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread_pct(self) -> float:
        if self.mid <= 0:
            return 1.0
        return (self.ask - self.bid) / self.mid


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    reason: str
    details: dict[str, float | str | bool]


def spread_filter(book: OrderBookSnapshot, avg_spread_pct_30d: float, cfg: ExecutionConfig) -> FilterResult:
    limit = min(cfg.max_spread_pct_abs, avg_spread_pct_30d * cfg.spread_avg_multiplier)
    passed = book.spread_pct < limit
    return FilterResult(
        passed=passed,
        reason="ok" if passed else "spread_too_wide",
        details={"spread_pct": book.spread_pct, "limit": limit},
    )


def volume_filter(h1: pd.DataFrame, cfg: ExecutionConfig) -> FilterResult:
    if len(h1) < cfg.volume_lookback_long:
        return FilterResult(False, "not_enough_volume_history", {})
    volume = h1.sort_values("timestamp")["volume"].astype(float)
    short_avg = float(volume.tail(cfg.volume_lookback_short).mean())
    long_avg = float(volume.tail(cfg.volume_lookback_long).mean())
    passed = long_avg > 0 and short_avg > long_avg * cfg.min_volume_ratio
    return FilterResult(
        passed=passed,
        reason="ok" if passed else "volume_too_low",
        details={"short_avg": short_avg, "long_avg": long_avg},
    )


def depth_filter(book: OrderBookSnapshot, notional: float, cfg: ExecutionConfig) -> FilterResult:
    upper = book.ask * (1 + cfg.depth_band_pct)
    available = sum(price * qty for price, qty in book.asks if price <= upper)
    required = notional * cfg.required_depth_multiple
    passed = available >= required
    return FilterResult(
        passed=passed,
        reason="ok" if passed else "insufficient_order_book_depth",
        details={"available": available, "required": required},
    )


def volatility_filter(h1: pd.DataFrame, cfg: ExecutionConfig) -> FilterResult:
    if len(h1) < cfg.volatility_lookback + 1:
        return FilterResult(False, "not_enough_volatility_history", {})
    frame = h1.sort_values("timestamp").copy()
    body_range = (frame["high"].astype(float) - frame["low"].astype(float)).abs()
    current = float(body_range.iloc[-1])
    avg = float(body_range.tail(cfg.volatility_lookback).mean())
    passed = avg > 0 and current <= avg * cfg.volatility_pause_multiplier
    return FilterResult(
        passed=passed,
        reason="ok" if passed else "extreme_volatility_pause",
        details={"current_range": current, "average_range": avg},
    )
