from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crypto_paper_bot.config import StrategyConfig
from crypto_paper_bot.indicators import atr, ema, ema_trend_signal, mfi, mfi_long_signal, rsi, rsi_long_signal
from crypto_paper_bot.models import SignalSnapshot


@dataclass(frozen=True)
class TimeframeFrames:
    w1: pd.DataFrame
    d1: pd.DataFrame
    h1: pd.DataFrame


def _require_columns(frame: pd.DataFrame, name: str) -> None:
    missing = {"timestamp", "open", "high", "low", "close", "volume"} - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")


def _gate_open(frame: pd.DataFrame, ema_period: int) -> bool:
    _require_columns(frame, "gate_frame")
    if len(frame) < ema_period + 2:
        return False
    close = frame["close"].astype(float)
    ema_value = ema(close, ema_period)
    return bool(close.iloc[-1] > ema_value.iloc[-1] and ema_value.iloc[-1] > ema_value.iloc[-2])


def build_signal(symbol: str, frames: TimeframeFrames, cfg: StrategyConfig) -> SignalSnapshot | None:
    """Build one closed-candle signal snapshot.

    W1 and D1 are hard gates. H1 calculates final score.
    ATR is not part of the score; it is returned for risk planning.
    """

    _require_columns(frames.h1, "h1")
    w1_open = _gate_open(frames.w1, cfg.ema_period)
    d1_open = _gate_open(frames.d1, cfg.ema_period)
    if not (w1_open and d1_open):
        return None

    h1 = frames.h1.copy().sort_values("timestamp").reset_index(drop=True)
    min_needed = max(cfg.ema_period, cfg.rsi_period, cfg.mfi_period, cfg.atr_period) + 2
    if len(h1) < min_needed:
        return None

    close = h1["close"].astype(float)
    high = h1["high"].astype(float)
    low = h1["low"].astype(float)
    volume = h1["volume"].astype(float)

    ema_sig = ema_trend_signal(close, cfg.ema_period)
    rsi_value = rsi(close, cfg.rsi_period)
    mfi_value = mfi(high, low, close, volume, cfg.mfi_period)
    atr_value = atr(high, low, close, cfg.atr_period)

    rsi_sig = rsi_long_signal(rsi_value)
    mfi_sig = mfi_long_signal(mfi_value)

    final_score = float((ema_sig.iloc[-1] + rsi_sig.iloc[-1] + mfi_sig.iloc[-1]) / 3.0)
    return SignalSnapshot(
        symbol=symbol,
        timestamp=pd.Timestamp(h1["timestamp"].iloc[-1]).to_pydatetime(),
        ema_signal=float(ema_sig.iloc[-1]),
        rsi_signal=float(rsi_sig.iloc[-1]),
        mfi_signal=float(mfi_sig.iloc[-1]),
        final_score=final_score,
        w1_gate_open=w1_open,
        d1_gate_open=d1_open,
        atr=float(atr_value.iloc[-1]),
        entry_reference_price=float(close.iloc[-1]),
        metadata={
            "rsi": float(rsi_value.iloc[-1]),
            "mfi": float(mfi_value.iloc[-1]),
            "threshold": cfg.entry_threshold,
        },
    )


def passes_entry_threshold(snapshot: SignalSnapshot, cfg: StrategyConfig) -> bool:
    return snapshot.final_score >= cfg.entry_threshold
