from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LabelConfig:
    horizon: int = 12
    good_trade_return_threshold: float = 0.003
    fee_buffer: float = 0.002
    tp_multiple: float = 3.0
    sl_multiple: float = 1.0


def build_forward_return_labels(feature_frame: pd.DataFrame, cfg: LabelConfig | None = None) -> pd.DataFrame:
    cfg = cfg or LabelConfig()
    if "close" not in feature_frame.columns or "timestamp" not in feature_frame.columns:
        raise ValueError("feature_frame must contain timestamp and close")
    df = feature_frame.copy().sort_values("timestamp").reset_index(drop=True)
    future_close = df["close"].shift(-cfg.horizon)
    df["label_future_return"] = future_close / df["close"] - 1.0
    df["label_good_trade"] = (df["label_future_return"] > cfg.good_trade_return_threshold + cfg.fee_buffer).astype(int)
    return df.dropna(subset=["label_future_return"]).reset_index(drop=True)


def build_tp_before_sl_label(
    ohlcv: pd.DataFrame,
    entry_price_col: str = "close",
    atr_col: str = "atr",
    cfg: LabelConfig | None = None,
) -> pd.DataFrame:
    """Build a path-dependent TP-before-SL label from already-featured rows.

    This uses future high/low path, so it must only be used as a label, never as a feature.
    """

    cfg = cfg or LabelConfig()
    required = {"timestamp", "high", "low", entry_price_col, atr_col}
    missing = required - set(ohlcv.columns)
    if missing:
        raise ValueError(f"Missing columns for TP/SL label: {sorted(missing)}")

    df = ohlcv.copy().sort_values("timestamp").reset_index(drop=True)
    labels: list[float] = []
    for idx, row in df.iterrows():
        entry = float(row[entry_price_col])
        risk = float(row[atr_col]) * cfg.sl_multiple
        if not np.isfinite(entry) or not np.isfinite(risk) or risk <= 0:
            labels.append(np.nan)
            continue
        tp = entry + risk * cfg.tp_multiple
        sl = entry - risk
        future = df.iloc[idx + 1 : idx + 1 + cfg.horizon]
        outcome = np.nan
        for _, future_row in future.iterrows():
            hit_sl = float(future_row["low"]) <= sl
            hit_tp = float(future_row["high"]) >= tp
            if hit_sl and hit_tp:
                outcome = 0.0
                break
            if hit_tp:
                outcome = 1.0
                break
            if hit_sl:
                outcome = 0.0
                break
        labels.append(outcome)
    df["label_tp_before_sl"] = labels
    return df.dropna(subset=["label_tp_before_sl"]).reset_index(drop=True)
