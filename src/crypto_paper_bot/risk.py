from __future__ import annotations

import pandas as pd

from crypto_paper_bot.config import RiskConfig, StrategyConfig
from crypto_paper_bot.models import RiskPlan, SignalSnapshot


def nearest_resistance_above(h1: pd.DataFrame, entry_price: float, lookback: int) -> float | None:
    if h1.empty or "high" not in h1.columns:
        return None
    recent = h1.sort_values("timestamp").tail(lookback)
    highs = recent["high"].astype(float)
    candidates = highs[highs > entry_price]
    if candidates.empty:
        return None
    return float(candidates.min())


def build_risk_plan(
    snapshot: SignalSnapshot,
    h1: pd.DataFrame,
    strategy: StrategyConfig,
    risk: RiskConfig,
) -> RiskPlan | None:
    entry = float(snapshot.entry_reference_price)
    if entry <= 0 or snapshot.atr <= 0:
        return None

    risk_distance = float(snapshot.atr * strategy.atr_multiplier)
    stop_loss = entry - risk_distance
    if stop_loss <= 0:
        return None

    raw_take_profit = entry + risk_distance * strategy.reward_risk
    resistance = nearest_resistance_above(h1, entry, strategy.resistance_lookback_h1)
    take_profit = raw_take_profit
    if resistance is not None and entry < resistance < raw_take_profit:
        take_profit = resistance

    actual_rr = (take_profit - entry) / risk_distance
    if actual_rr < strategy.min_reward_risk_after_resistance:
        return None

    stop_distance_pct = risk_distance / entry
    if stop_distance_pct <= 0:
        return None

    position_pct = risk.account_risk_per_trade / stop_distance_pct
    position_pct = min(position_pct, risk.max_position_pct)
    if position_pct < risk.min_position_pct:
        return None

    return RiskPlan(
        entry_price=entry,
        risk_distance=risk_distance,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_pct=position_pct,
        reward_risk=actual_rr,
    )


def open_risk_pct(position_pct: float, entry: float, stop: float) -> float:
    if entry <= 0:
        return 0.0
    return position_pct * max((entry - stop) / entry, 0.0)
