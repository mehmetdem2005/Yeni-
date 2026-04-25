from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TimeFrame(str, Enum):
    W1 = "1w"
    D1 = "1d"
    H1 = "1h"


class CloseReason(str, Enum):
    TAKE_PROFIT = "TP"
    STOP_LOSS = "SL"
    TIME = "TIME"
    MANUAL = "MANUAL"


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_ohlcv(cls, row: list[float | int]) -> "Candle":
        ts_ms, open_, high, low, close, volume = row
        return cls(
            timestamp=datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=timezone.utc),
            open=float(open_),
            high=float(high),
            low=float(low),
            close=float(close),
            volume=float(volume),
        )


@dataclass(frozen=True)
class SignalSnapshot:
    symbol: str
    timestamp: datetime
    ema_signal: float
    rsi_signal: float
    mfi_signal: float
    final_score: float
    w1_gate_open: bool
    d1_gate_open: bool
    atr: float
    entry_reference_price: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskPlan:
    entry_price: float
    risk_distance: float
    stop_loss: float
    take_profit: float
    position_pct: float
    reward_risk: float
    reason: str = "ok"


@dataclass(frozen=True)
class PaperOrderResult:
    symbol: str
    requested_qty: float
    filled_qty: float
    fill_ratio: float
    avg_fill_price: float | None
    maker_taker: str
    fee_paid: float
    slippage_pct: float
    status: str


@dataclass
class TradeLog:
    signal_time: datetime
    entry_time: datetime | None
    close_time: datetime | None
    coin: str
    entry_price: float | None
    close_price: float | None
    position_pct: float
    sl_price: float | None
    tp_price: float | None
    close_reason: CloseReason | None
    spread_entry: float | None
    slippage: float | None
    commission_entry: float
    commission_close: float
    maker_taker: str | None
    net_pnl: float | None
    param_snapshot: dict[str, Any]
    fill_ratio: float
