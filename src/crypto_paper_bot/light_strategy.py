from __future__ import annotations

from dataclasses import dataclass

from crypto_paper_bot.real_market import LightCandle


@dataclass(frozen=True)
class LightSignal:
    ema_signal: float
    rsi_signal: float
    volume_signal: float
    final_score: float
    atr: float
    close: float
    reason: str


def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    result: list[float] = []
    current = values[0]
    for value in values:
        current = alpha * value + (1.0 - alpha) * current
        result.append(current)
    return result


def rsi(values: list[float], period: int = 14) -> float:
    if len(values) < period + 1:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    recent = values[-(period + 1) :]
    for prev, cur in zip(recent, recent[1:]):
        delta = cur - prev
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def atr(candles: list[LightCandle], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs: list[float] = []
    recent = candles[-(period + 1) :]
    for prev, cur in zip(recent, recent[1:]):
        trs.append(max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close)))
    return sum(trs) / len(trs)


def build_light_signal(candles: list[LightCandle]) -> LightSignal:
    if len(candles) < 60:
        return LightSignal(0.0, 0.5, 0.0, 0.0, 0.0, 0.0, "not_enough_candles")
    closes = [c.close for c in candles]
    volumes = [c.volume for c in candles]
    ema50 = ema(closes, 50)
    ema_signal = 1.0 if closes[-1] > ema50[-1] and ema50[-1] > ema50[-2] else 0.0

    rsi_value = rsi(closes, 14)
    if 45.0 <= rsi_value <= 65.0:
        rsi_signal = 1.0
    elif 35.0 <= rsi_value < 45.0 or 65.0 < rsi_value <= 75.0:
        rsi_signal = 0.5
    else:
        rsi_signal = 0.0

    vol5 = sum(volumes[-5:]) / 5.0
    vol50 = sum(volumes[-50:]) / 50.0
    volume_signal = 1.0 if vol50 > 0 and vol5 > vol50 * 0.50 else 0.0

    final_score = (ema_signal + rsi_signal + volume_signal) / 3.0
    return LightSignal(
        ema_signal=ema_signal,
        rsi_signal=rsi_signal,
        volume_signal=volume_signal,
        final_score=final_score,
        atr=atr(candles, 14),
        close=closes[-1],
        reason=f"rsi={rsi_value:.2f}, vol5={vol5:.2f}, vol50={vol50:.2f}",
    )


def risk_plan(entry: float, atr_value: float, account_risk: float = 0.005) -> dict:
    risk_distance = atr_value * 1.5
    if entry <= 0 or risk_distance <= 0:
        return {"ok": False, "reason": "bad_entry_or_atr"}
    stop_loss = entry - risk_distance
    take_profit = entry + risk_distance * 3.0
    stop_pct = risk_distance / entry
    position_pct = min(account_risk / stop_pct, 0.05)
    if position_pct < 0.005:
        return {"ok": False, "reason": "position_below_minimum"}
    return {
        "ok": True,
        "entry": entry,
        "risk_distance": risk_distance,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_pct": position_pct,
    }
