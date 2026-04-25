from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pandas as pd


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    train_index: list[int]
    validation_index: list[int]
    test_index: list[int]


@dataclass(frozen=True)
class WalkForwardConfig:
    train_months: int = 6
    validation_months: int = 2
    test_months: int = 1
    step_months: int = 1


def generate_walk_forward_splits(
    frame: pd.DataFrame,
    cfg: WalkForwardConfig | None = None,
    timestamp_col: str = "timestamp",
) -> Iterator[WalkForwardSplit]:
    cfg = cfg or WalkForwardConfig()
    if timestamp_col not in frame.columns:
        raise ValueError(f"Missing timestamp column: {timestamp_col}")

    df = frame.copy().sort_values(timestamp_col).reset_index(drop=True)
    timestamps = pd.to_datetime(df[timestamp_col], utc=True)
    start = timestamps.min()
    final = timestamps.max()

    cursor = start
    while True:
        train_start = cursor
        train_end = train_start + pd.DateOffset(months=cfg.train_months)
        validation_start = train_end
        validation_end = validation_start + pd.DateOffset(months=cfg.validation_months)
        test_start = validation_end
        test_end = test_start + pd.DateOffset(months=cfg.test_months)
        if test_end > final:
            break

        train_mask = (timestamps >= train_start) & (timestamps < train_end)
        val_mask = (timestamps >= validation_start) & (timestamps < validation_end)
        test_mask = (timestamps >= test_start) & (timestamps < test_end)

        if train_mask.any() and val_mask.any() and test_mask.any():
            yield WalkForwardSplit(
                train_start=train_start,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
                test_start=test_start,
                test_end=test_end,
                train_index=df.index[train_mask].tolist(),
                validation_index=df.index[val_mask].tolist(),
                test_index=df.index[test_mask].tolist(),
            )

        cursor = cursor + pd.DateOffset(months=cfg.step_months)
