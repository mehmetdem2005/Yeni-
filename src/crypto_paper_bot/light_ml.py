from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from crypto_paper_bot.storage import BotStorage


FEATURES = [
    "ret_1",
    "ret_3",
    "ret_6",
    "range_pct",
    "volume_ratio",
    "ema_distance",
]


@dataclass(frozen=True)
class TrainingResult:
    trained_samples: int
    accuracy: float
    positive_rate: float
    weights: dict[str, float]


def sigmoid(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def _close(row: dict[str, Any]) -> float:
    return float(row["close"])


def build_training_rows(candles: list[dict[str, Any]], horizon: int = 12, threshold: float = 0.003) -> list[tuple[dict[str, float], int]]:
    rows: list[tuple[dict[str, float], int]] = []
    if len(candles) < 80 + horizon:
        return rows
    closes = [_close(c) for c in candles]
    volumes = [float(c["volume"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    for i in range(50, len(candles) - horizon):
        close = closes[i]
        if close <= 0:
            continue
        vol5 = sum(volumes[i - 4 : i + 1]) / 5.0
        vol50 = sum(volumes[i - 49 : i + 1]) / 50.0
        ema20 = sum(closes[i - 19 : i + 1]) / 20.0
        ema50 = sum(closes[i - 49 : i + 1]) / 50.0
        future_return = closes[i + horizon] / close - 1.0
        features = {
            "ret_1": closes[i] / closes[i - 1] - 1.0,
            "ret_3": closes[i] / closes[i - 3] - 1.0,
            "ret_6": closes[i] / closes[i - 6] - 1.0,
            "range_pct": (highs[i] - lows[i]) / close,
            "volume_ratio": 0.0 if vol50 <= 0 else vol5 / vol50 - 1.0,
            "ema_distance": 0.0 if ema50 <= 0 else ema20 / ema50 - 1.0,
        }
        label = 1 if future_return > threshold else 0
        rows.append((features, label))
    return rows


class TinyOnlineLogisticModel:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {"bias": 0.0, **{name: 0.0 for name in FEATURES}}

    def predict_proba(self, features: dict[str, float]) -> float:
        z = self.weights.get("bias", 0.0)
        for name in FEATURES:
            z += self.weights.get(name, 0.0) * float(features.get(name, 0.0))
        return sigmoid(z)

    def train(self, rows: list[tuple[dict[str, float], int]], epochs: int = 5, lr: float = 0.05) -> TrainingResult:
        if not rows:
            return TrainingResult(0, 0.0, 0.0, dict(self.weights))
        correct = 0
        positives = 0
        for _ in range(epochs):
            for features, label in rows:
                p = self.predict_proba(features)
                error = float(label) - p
                self.weights["bias"] = self.weights.get("bias", 0.0) + lr * error
                for name in FEATURES:
                    value = max(min(float(features.get(name, 0.0)), 5.0), -5.0)
                    self.weights[name] = self.weights.get(name, 0.0) + lr * error * value
        for features, label in rows:
            p = self.predict_proba(features)
            pred = 1 if p >= 0.5 else 0
            correct += 1 if pred == label else 0
            positives += label
        return TrainingResult(
            trained_samples=len(rows),
            accuracy=correct / len(rows),
            positive_rate=positives / len(rows),
            weights=dict(self.weights),
        )


def latest_feature_from_candles(candles: list[dict[str, Any]]) -> dict[str, float] | None:
    rows = build_training_rows(candles, horizon=1, threshold=0.0)
    if not rows:
        return None
    return rows[-1][0]


def train_from_storage(storage: BotStorage, symbol: str = "BTC/USDT", interval: str = "1h") -> TrainingResult:
    candles = storage.get_candles(symbol, interval, limit=2000)
    rows = build_training_rows(candles)
    current = storage.load_model_state()
    model = TinyOnlineLogisticModel(current["weights"] if current else None)
    result = model.train(rows)
    storage.save_model_state(result.weights, {"accuracy": result.accuracy, "positive_rate": result.positive_rate}, result.trained_samples)
    return result


def predict_from_storage(storage: BotStorage, symbol: str = "BTC/USDT", interval: str = "1h") -> float | None:
    state = storage.load_model_state()
    if not state:
        return None
    candles = storage.get_candles(symbol, interval, limit=200)
    features = latest_feature_from_candles(candles)
    if features is None:
        return None
    return TinyOnlineLogisticModel(state["weights"]).predict_proba(features)
