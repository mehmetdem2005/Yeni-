from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from crypto_paper_bot.indicators import atr, ema, mfi, rsi


@dataclass(frozen=True)
class FeatureConfig:
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    mfi_period: int = 14
    atr_period: int = 14
    return_windows: tuple[int, ...] = (1, 3, 6, 12, 24)
    rolling_windows: tuple[int, ...] = (12, 24, 48)


def _validate_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    clean = frame.copy().sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    clean = clean.dropna(subset=["open", "high", "low", "close", "volume"])
    return clean.reset_index(drop=True)


def build_features(frame: pd.DataFrame, cfg: FeatureConfig | None = None) -> pd.DataFrame:
    """Build closed-candle features.

    The returned row at time t uses only data available at or before candle t.
    Labels must be built separately with forward shifts.
    """

    cfg = cfg or FeatureConfig()
    df = _validate_ohlcv(frame)
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    out = pd.DataFrame({"timestamp": df["timestamp"], "close": close})

    out["ema_fast"] = ema(close, cfg.ema_fast)
    out["ema_slow"] = ema(close, cfg.ema_slow)
    out["ema_fast_above_slow"] = (out["ema_fast"] > out["ema_slow"]).astype(float)
    out["ema_slow_slope"] = out["ema_slow"].diff()
    out["rsi"] = rsi(close, cfg.rsi_period)
    out["mfi"] = mfi(high, low, close, volume, cfg.mfi_period)
    out["atr"] = atr(high, low, close, cfg.atr_period)
    out["atr_pct"] = out["atr"] / close.replace(0, np.nan)
    out["hl_range_pct"] = (high - low) / close.replace(0, np.nan)
    out["oc_return"] = (close - df["open"].astype(float)) / df["open"].replace(0, np.nan)
    out["volume_log"] = np.log1p(volume.clip(lower=0))

    for window in cfg.return_windows:
        out[f"ret_{window}"] = close.pct_change(window)

    for window in cfg.rolling_windows:
        returns = close.pct_change()
        out[f"volatility_{window}"] = returns.rolling(window, min_periods=window).std()
        out[f"volume_z_{window}"] = (volume - volume.rolling(window, min_periods=window).mean()) / volume.rolling(window, min_periods=window).std().replace(0, np.nan)
        out[f"drawdown_{window}"] = close / close.rolling(window, min_periods=window).max() - 1.0

    return out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def feature_columns(feature_frame: pd.DataFrame) -> list[str]:
    return [c for c in feature_frame.columns if c not in {"timestamp", "close"}]
