from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, precision_score, recall_score, roc_auc_score


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    roc_auc: float | None
    average_precision: float | None
    brier: float


@dataclass(frozen=True)
class TradeMetrics:
    total_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    average_win: float
    average_loss: float
    average_win_loss_ratio: float | None
    trade_count: int


def classification_metrics(y_true: pd.Series, prob: np.ndarray, threshold: float = 0.5) -> ClassificationMetrics:
    y = y_true.astype(int).to_numpy()
    pred = (prob >= threshold).astype(int)
    roc_auc = None
    avg_precision = None
    if len(set(y.tolist())) > 1:
        roc_auc = float(roc_auc_score(y, prob))
        avg_precision = float(average_precision_score(y, prob))
    return ClassificationMetrics(
        accuracy=float(accuracy_score(y, pred)),
        precision=float(precision_score(y, pred, zero_division=0)),
        recall=float(recall_score(y, pred, zero_division=0)),
        roc_auc=roc_auc,
        average_precision=avg_precision,
        brier=float(brier_score_loss(y, prob)),
    )


def max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    running_max = equity_curve.cummax()
    dd = equity_curve / running_max.replace(0, np.nan) - 1.0
    return float(dd.min())


def trade_metrics(returns: pd.Series, periods_per_year: int = 365 * 24) -> TradeMetrics:
    clean = returns.dropna().astype(float)
    if clean.empty:
        return TradeMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, 0)
    equity = (1.0 + clean).cumprod()
    std = clean.std(ddof=0)
    sharpe = 0.0 if std == 0 else float(clean.mean() / std * np.sqrt(periods_per_year))
    wins = clean[clean > 0]
    losses = clean[clean < 0]
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(abs(losses.mean())) if not losses.empty else 0.0
    ratio = None if avg_loss == 0 else avg_win / avg_loss
    return TradeMetrics(
        total_return=float(equity.iloc[-1] - 1.0),
        sharpe=sharpe,
        max_drawdown=max_drawdown(equity),
        win_rate=float((clean > 0).mean()),
        average_win=avg_win,
        average_loss=avg_loss,
        average_win_loss_ratio=ratio,
        trade_count=int(len(clean)),
    )
