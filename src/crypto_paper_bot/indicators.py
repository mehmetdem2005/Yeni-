from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    value = 100 - (100 / (1 + rs))
    return value.fillna(50.0)


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    typical = (high + low + close) / 3.0
    raw_flow = typical * volume
    direction = typical.diff()
    positive = raw_flow.where(direction > 0, 0.0)
    negative = raw_flow.where(direction < 0, 0.0).abs()
    pos_sum = positive.rolling(period, min_periods=period).sum()
    neg_sum = negative.rolling(period, min_periods=period).sum()
    ratio = pos_sum / neg_sum.replace(0, np.nan)
    value = 100 - (100 / (1 + ratio))
    return value.fillna(50.0)


def ema_trend_signal(close: pd.Series, period: int = 50) -> pd.Series:
    ema_value = ema(close, period)
    slope = ema_value.diff()
    return ((close > ema_value) & (slope > 0)).astype(float).fillna(0.0)


def rsi_long_signal(rsi_value: pd.Series) -> pd.Series:
    # Long-only: avoid overbought exhaustion, prefer constructive momentum.
    score = pd.Series(0.5, index=rsi_value.index, dtype=float)
    score[(rsi_value >= 45) & (rsi_value <= 65)] = 1.0
    score[(rsi_value > 65) & (rsi_value <= 75)] = 0.5
    score[rsi_value < 35] = 0.0
    score[rsi_value > 75] = 0.0
    return score


def mfi_long_signal(mfi_value: pd.Series) -> pd.Series:
    score = pd.Series(0.5, index=mfi_value.index, dtype=float)
    score[(mfi_value >= 45) & (mfi_value <= 70)] = 1.0
    score[mfi_value < 25] = 0.0
    score[mfi_value > 80] = 0.0
    return score


def candles_to_frame(rows: list) -> pd.DataFrame:
    data = [
        {
            "timestamp": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in rows
    ]
    frame = pd.DataFrame(data)
    if not frame.empty:
        frame = frame.sort_values("timestamp").reset_index(drop=True)
    return frame
