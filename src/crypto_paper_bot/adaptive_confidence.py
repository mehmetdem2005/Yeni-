from __future__ import annotations

from dataclasses import dataclass
from typing import Any

COMPONENTS = [
    "indicator",
    "ai_prediction",
    "regime",
    "liquidity",
    "risk_reward",
    "portfolio_safety",
]

BASE_WEIGHTS = {
    "indicator": 0.30,
    "ai_prediction": 0.30,
    "regime": 0.15,
    "liquidity": 0.10,
    "risk_reward": 0.10,
    "portfolio_safety": 0.05,
}


@dataclass(frozen=True)
class ComponentStats:
    total: int = 0
    wins: int = 0
    pnl_sum: float = 0.0

    @property
    def adjusted_success(self) -> float:
        return (self.wins + 1.0) / (self.total + 2.0)


@dataclass(frozen=True)
class ConfidenceResult:
    trade_confidence: float
    weights: dict[str, float]
    contributions: dict[str, float]
    explanation: str


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_weights(raw: dict[str, float], min_weight: float = 0.05, max_weight: float = 0.45) -> dict[str, float]:
    if not raw:
        return dict(BASE_WEIGHTS)
    total = sum(max(v, 0.0) for v in raw.values())
    if total <= 0:
        weights = dict(BASE_WEIGHTS)
    else:
        weights = {k: max(v, 0.0) / total for k, v in raw.items()}
    weights = {k: clamp(v, min_weight, max_weight) for k, v in weights.items()}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def adaptive_weights(stats: dict[str, ComponentStats] | None = None) -> dict[str, float]:
    stats = stats or {}
    raw: dict[str, float] = {}
    for name in COMPONENTS:
        stat = stats.get(name, ComponentStats())
        raw[name] = BASE_WEIGHTS[name] * stat.adjusted_success
    return normalize_weights(raw)


def compute_trade_confidence(scores: dict[str, float], stats: dict[str, ComponentStats] | None = None) -> ConfidenceResult:
    weights = adaptive_weights(stats)
    contributions: dict[str, float] = {}
    total = 0.0
    for name in COMPONENTS:
        score = clamp(float(scores.get(name, 0.5)), 0.0, 1.0)
        contribution = score * weights[name]
        contributions[name] = contribution
        total += contribution
    strongest = max(contributions, key=contributions.get)
    weakest = min(contributions, key=contributions.get)
    explanation = f"En güçlü katkı: {strongest}. En zayıf katkı: {weakest}. Ağırlıklar başarı geçmişine göre ayarlanır."
    return ConfidenceResult(total, weights, contributions, explanation)


def compute_system_confidence(
    data_health: float,
    model_health: float,
    api_health: float,
    account_health: float,
    risk_health: float,
) -> float:
    return clamp(
        data_health * 0.25
        + model_health * 0.20
        + api_health * 0.20
        + account_health * 0.20
        + risk_health * 0.15,
        0.0,
        1.0,
    )


def component_stats_from_trades(trades: list[dict[str, Any]]) -> dict[str, ComponentStats]:
    # First version: every closed trade updates all components equally.
    # Later we will update only components that strongly contributed.
    stats = {name: {"total": 0, "wins": 0, "pnl_sum": 0.0} for name in COMPONENTS}
    for trade in trades:
        if trade.get("status") != "CLOSED":
            continue
        pnl = float(trade.get("pnl") or 0.0)
        win = pnl > 0
        for name in COMPONENTS:
            stats[name]["total"] += 1
            stats[name]["wins"] += 1 if win else 0
            stats[name]["pnl_sum"] += pnl
    return {name: ComponentStats(**value) for name, value in stats.items()}
