from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crypto_paper_bot.confidence_engine import TradeConfidenceSnapshot
from crypto_paper_bot.indicator_engine import IndicatorSnapshot
from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log


@dataclass(frozen=True)
class SmartRiskConfig:
    account_risk_pct: float = 0.005
    max_position_pct: float = 0.05
    min_position_pct: float = 0.005
    atr_stop_multiplier: float = 1.5
    reward_risk_target: float = 3.0
    min_reward_risk: float = 2.0
    swing_lookback: int = 20
    max_stop_distance_pct: float = 0.08
    min_stop_distance_pct: float = 0.002
    fee_buffer_pct: float = 0.002


@dataclass(frozen=True)
class SmartRiskPlan:
    symbol: str
    ok: bool
    reason: str
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    risk_distance: float | None
    stop_distance_pct: float | None
    reward_risk: float | None
    raw_position_notional: float | None
    final_position_notional: float | None
    position_pct: float | None
    confidence_multiplier: float
    system_multiplier: float
    volatility_multiplier: float
    explanation: str
    logs: list[LogRecord] = field(default_factory=list)


def _value(candle: Any, key: str) -> float:
    if isinstance(candle, dict):
        return float(candle[key])
    return float(getattr(candle, key))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def recent_swing_low(candles: list[Any], lookback: int) -> float | None:
    if not candles:
        return None
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    lows = [_value(candle, "low") for candle in recent]
    return min(lows) if lows else None


def recent_swing_high(candles: list[Any], lookback: int) -> float | None:
    if not candles:
        return None
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    highs = [_value(candle, "high") for candle in recent]
    return max(highs) if highs else None


def nearest_resistance_above(candles: list[Any], entry_price: float, lookback: int) -> float | None:
    if not candles:
        return None
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    highs = sorted({_value(candle, "high") for candle in recent if _value(candle, "high") > entry_price})
    return highs[0] if highs else None


def volatility_multiplier(atr_pct: float | None) -> float:
    if atr_pct is None:
        return 0.75
    if atr_pct < 0.015:
        return 1.0
    if atr_pct < 0.04:
        return 0.80
    if atr_pct < 0.08:
        return 0.60
    return 0.50


def confidence_multiplier(trade_confidence: float) -> float:
    # 0.50 - 1.25 range. Low confidence reduces size; very high confidence slightly increases.
    return clamp(0.50 + trade_confidence, 0.50, 1.25)


def system_multiplier(system_confidence: float) -> float:
    # 0.50 - 1.00 range. System health should never enlarge risk above base.
    return clamp(0.50 + (system_confidence / 2.0), 0.50, 1.00)


def stop_explanation(entry: float, atr_stop: float, swing_stop: float | None, selected_stop: float) -> str:
    if swing_stop is None:
        return "Zarar kes ATR oynaklığına göre belirlendi; anlamlı dip verisi bulunamadı."
    if selected_stop == swing_stop:
        return "Zarar kes seviyesi son anlamlı dip bölgesine göre seçildi."
    return "Zarar kes seviyesi ATR oynaklığına göre seçildi; son dip daha yakın/uygunsuz kaldı."


def tp_explanation(raw_tp: float, resistance: float | None, selected_tp: float) -> str:
    if resistance is None:
        return "Kâr al seviyesi risk mesafesinin 3 katına göre seçildi; yakın direnç bulunamadı."
    if selected_tp == resistance:
        return "Kâr al seviyesi yakındaki direnç bölgesine çekildi; risk/ödül oranı yeterli kaldı."
    return "Kâr al seviyesi risk mesafesinin 3 katına göre seçildi; direnç daha uzakta kaldı."


def build_smart_risk_plan(
    symbol: str,
    candles: list[Any],
    indicator: IndicatorSnapshot,
    trade_confidence: TradeConfidenceSnapshot,
    system_confidence: float,
    account_equity: float,
    open_risk_pct: float = 0.0,
    config: SmartRiskConfig | None = None,
) -> SmartRiskPlan:
    """Build smart position, stop-loss and take-profit plan.

    This module does not place an order. It only calculates whether a paper trade is
    allowed and how much virtual capital should be allocated.
    """

    config = config or SmartRiskConfig()
    entry = float(indicator.price)
    atr_value = indicator.atr_value
    atr_pct = indicator.atr_pct

    base_details = {
        "symbol": symbol,
        "entry": entry,
        "atr": atr_value,
        "atr_pct": atr_pct,
        "account_equity": account_equity,
        "trade_confidence": trade_confidence.trade_confidence,
        "system_confidence": system_confidence,
    }

    if entry <= 0 or account_equity <= 0:
        explanation = "Giriş fiyatı veya sanal hesap değeri geçersiz olduğu için risk planı üretilemedi."
        return SmartRiskPlan(symbol, False, "bad_entry_or_equity", entry, None, None, None, None, None, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details, explanation)])

    if atr_value is None or atr_value <= 0:
        explanation = "ATR verisi yok veya sıfır; akıllı stop-loss hesaplanamadı."
        return SmartRiskPlan(symbol, False, "missing_atr", entry, None, None, None, None, None, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details, explanation)])

    atr_stop = entry - (atr_value * config.atr_stop_multiplier)
    swing_low = recent_swing_low(candles, config.swing_lookback)

    # Long-only spot: stop must be below entry. Choose the more conservative lower stop,
    # but reject if it makes risk too wide.
    valid_stops = [atr_stop]
    if swing_low is not None and swing_low < entry:
        valid_stops.append(swing_low)
    stop_loss = min(valid_stops)

    if stop_loss <= 0 or stop_loss >= entry:
        explanation = "Zarar kes seviyesi giriş fiyatına göre geçersiz kaldı."
        return SmartRiskPlan(symbol, False, "invalid_stop", entry, None, None, None, None, None, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details, explanation)])

    risk_distance = entry - stop_loss
    stop_pct = risk_distance / entry

    if stop_pct < config.min_stop_distance_pct:
        explanation = "Stop mesafesi çok dar; küçük fiyat oynaklığı işlemi gereksiz yere kapatabilir."
        return SmartRiskPlan(symbol, False, "stop_too_close", entry, stop_loss, None, risk_distance, stop_pct, None, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details | {"stop_pct": stop_pct}, explanation)])

    if stop_pct > config.max_stop_distance_pct:
        explanation = "Stop mesafesi çok geniş; risk bütçesi verimli kullanılamıyor."
        return SmartRiskPlan(symbol, False, "stop_too_wide", entry, stop_loss, None, risk_distance, stop_pct, None, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details | {"stop_pct": stop_pct}, explanation)])

    raw_tp = entry + (risk_distance * config.reward_risk_target)
    resistance = nearest_resistance_above(candles, entry, config.swing_lookback)
    take_profit = raw_tp
    if resistance is not None and entry < resistance < raw_tp:
        take_profit = resistance

    reward_risk = (take_profit - entry) / risk_distance
    if reward_risk < config.min_reward_risk:
        explanation = "Kâr hedefi, zarar riskine göre yeterince avantajlı değil; minimum 1:2 risk/ödül sağlanmadı."
        return SmartRiskPlan(symbol, False, "reward_risk_too_low", entry, stop_loss, take_profit, risk_distance, stop_pct, reward_risk, None, None, None, 0.5, 0.5, 0.5, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details | {"reward_risk": reward_risk}, explanation)])

    account_risk = account_equity * config.account_risk_pct
    raw_position = account_risk / stop_pct

    c_mult = confidence_multiplier(trade_confidence.trade_confidence)
    s_mult = system_multiplier(system_confidence)
    v_mult = volatility_multiplier(atr_pct)
    adjusted_position = raw_position * c_mult * s_mult * v_mult

    max_position = account_equity * config.max_position_pct
    min_position = account_equity * config.min_position_pct
    final_position = min(adjusted_position, max_position)

    # Reduce when portfolio already carries risk.
    if open_risk_pct > 0.0:
        final_position *= clamp(1.0 - open_risk_pct, 0.25, 1.0)

    if final_position < min_position:
        explanation = "Akıllı miktar minimum işlem eşiğinin altında kaldı; işlem açmak verimli değil."
        return SmartRiskPlan(symbol, False, "position_below_minimum", entry, stop_loss, take_profit, risk_distance, stop_pct, reward_risk, raw_position, final_position, final_position / account_equity, c_mult, s_mult, v_mult, explanation, [make_log(LogChannel.RISK, "Risk planı reddedildi.", LogLevel.WARNING, base_details | {"final_position": final_position}, explanation)])

    position_pct = final_position / account_equity
    stop_text = stop_explanation(entry, atr_stop, swing_low, stop_loss)
    tp_text = tp_explanation(raw_tp, resistance, take_profit)
    explanation = (
        f"Sistem bu işlem için {final_position:.2f} USDT ayırdı. "
        f"Sebep: işlem özgüveni %{trade_confidence.trade_confidence * 100:.1f}, "
        f"sistem özgüveni %{system_confidence * 100:.1f}, stop mesafesi %{stop_pct * 100:.2f}. "
        f"{stop_text} {tp_text}"
    )

    details = base_details | {
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_distance": risk_distance,
        "stop_pct": stop_pct,
        "reward_risk": reward_risk,
        "raw_position": raw_position,
        "final_position": final_position,
        "position_pct": position_pct,
        "confidence_multiplier": c_mult,
        "system_multiplier": s_mult,
        "volatility_multiplier": v_mult,
        "atr_stop": atr_stop,
        "swing_low": swing_low,
        "resistance": resistance,
    }

    logs = [
        make_log(
            LogChannel.RISK,
            "Akıllı risk planı üretildi.",
            LogLevel.INFO,
            details,
            explanation,
        )
    ]

    return SmartRiskPlan(
        symbol=symbol,
        ok=True,
        reason="ok",
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_distance=risk_distance,
        stop_distance_pct=stop_pct,
        reward_risk=reward_risk,
        raw_position_notional=raw_position,
        final_position_notional=final_position,
        position_pct=position_pct,
        confidence_multiplier=c_mult,
        system_multiplier=s_mult,
        volatility_multiplier=v_mult,
        explanation=explanation,
        logs=logs,
    )


def risk_plan_as_plain_dict(plan: SmartRiskPlan) -> dict[str, Any]:
    return {
        "symbol": plan.symbol,
        "ok": plan.ok,
        "reason": plan.reason,
        "entry_price": plan.entry_price,
        "stop_loss": plan.stop_loss,
        "take_profit": plan.take_profit,
        "risk_distance": plan.risk_distance,
        "stop_distance_pct": plan.stop_distance_pct,
        "reward_risk": plan.reward_risk,
        "raw_position_notional": plan.raw_position_notional,
        "final_position_notional": plan.final_position_notional,
        "position_pct": plan.position_pct,
        "confidence_multiplier": plan.confidence_multiplier,
        "system_multiplier": plan.system_multiplier,
        "volatility_multiplier": plan.volatility_multiplier,
        "explanation": plan.explanation,
    }
