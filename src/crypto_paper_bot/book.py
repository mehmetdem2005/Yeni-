from __future__ import annotations

from dataclasses import dataclass


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
