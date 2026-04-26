from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log


@dataclass(frozen=True)
class IndicatorConfig:
    ema_period: int = 50
    rsi_period: int = 14
    atr_period: int = 14
    volume_short_period: int = 5
    volume_long_period: int = 50


@dataclass(frozen=True)
class IndicatorSnapshot:
    symbol: str
    timestamp: str
    price: float
    ema_value: float | None
    ema_signal: float
    rsi_value: float | None
    rsi_signal: float
    atr_value: float | None
    atr_pct: float | None
    volume_ratio: float | None
    volume_signal: float
    indicator_score: float
    trend_comment: str
    momentum_comment: str
    volatility_comment: str
    volume_comment: str
    decision_comment: str
    logs: list[LogRecord] = field(default_factory=list)


def _value(candle: Any, key: str) -> float:
    if isinstance(candle, dict):
        return float(candle[key])
    return float(getattr(candle, key))


def _timestamp(candle: Any) -> str:
    if isinstance(candle, dict):
        return str(candle.get("timestamp", ""))
    value = getattr(candle, "timestamp", "")
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    if period <= 1:
        return list(values)
    alpha = 2.0 / (period + 1.0)
    result: list[float] = []
    current = float(values[0])
    for value in values:
        current = alpha * float(value) + (1.0 - alpha) * current
        result.append(current)
    return result


def rsi_value(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    recent = values[-(period + 1) :]
    for previous, current in zip(recent, recent[1:]):
        delta = current - previous
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def atr_value(candles: list[Any], period: int = 14) -> float | None:
    if len(candles) < period + 1:
        return None
    true_ranges: list[float] = []
    recent = candles[-(period + 1) :]
    for previous, current in zip(recent, recent[1:]):
        high = _value(current, "high")
        low = _value(current, "low")
        prev_close = _value(previous, "close")
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    if not true_ranges:
        return None
    return sum(true_ranges) / len(true_ranges)


def volume_ratio(candles: list[Any], short_period: int = 5, long_period: int = 50) -> float | None:
    if len(candles) < long_period:
        return None
    volumes = [_value(candle, "volume") for candle in candles]
    short_avg = sum(volumes[-short_period:]) / short_period
    long_avg = sum(volumes[-long_period:]) / long_period
    if long_avg <= 0:
        return None
    return short_avg / long_avg


def ema_signal(price: float, ema_now: float | None, ema_previous: float | None) -> float:
    if ema_now is None or ema_previous is None:
        return 0.5
    if price > ema_now and ema_now > ema_previous:
        return 1.0
    if price > ema_now:
        return 0.65
    if price < ema_now and ema_now < ema_previous:
        return 0.0
    return 0.35


def rsi_signal(value: float | None) -> float:
    if value is None:
        return 0.5
    if 45.0 <= value <= 65.0:
        return 1.0
    if 35.0 <= value < 45.0 or 65.0 < value <= 75.0:
        return 0.5
    return 0.0


def volume_signal(value: float | None) -> float:
    if value is None:
        return 0.5
    if value >= 1.20:
        return 1.0
    if value >= 0.80:
        return 0.65
    if value >= 0.50:
        return 0.35
    return 0.0


def atr_risk_comment(atr: float | None, price: float) -> tuple[float | None, str]:
    if atr is None or price <= 0:
        return None, "Volatilite ölçümü için yeterli veri yok."
    pct = atr / price
    if pct < 0.015:
        return pct, "Oynaklık düşük; stop mesafesi daha kontrollü olabilir."
    if pct < 0.04:
        return pct, "Oynaklık orta; pozisyon miktarı dikkatli ayarlanmalı."
    return pct, "Oynaklık yüksek; sistem daha küçük miktarla işlem düşünmeli."


def trend_comment(score: float) -> str:
    if score >= 0.90:
        return "Fiyat ana ortalamanın üstünde ve trend yukarı eğimli."
    if score >= 0.50:
        return "Fiyat ortalamanın üstünde ama trend gücü sınırlı."
    if score <= 0.10:
        return "Fiyat ortalamanın altında ve trend zayıf."
    return "Trend kararsız; tek başına güçlü alım sinyali değil."


def momentum_comment(value: float | None, score: float) -> str:
    if value is None:
        return "Momentum için yeterli veri yok."
    if score >= 0.90:
        return f"RSI {value:.1f}; momentum dengeli ve alım için sağlıklı bölgede."
    if score >= 0.50:
        return f"RSI {value:.1f}; momentum nötr/temkinli bölgede."
    return f"RSI {value:.1f}; momentum riskli bölgede."


def volume_comment(value: float | None, score: float) -> str:
    if value is None:
        return "Hacim karşılaştırması için yeterli veri yok."
    if score >= 0.90:
        return f"Hacim normalin üzerinde; hareket piyasa tarafından destekleniyor. Oran: {value:.2f}."
    if score >= 0.50:
        return f"Hacim normal seviyeye yakın. Oran: {value:.2f}."
    return f"Hacim zayıf; sinyalin güveni düşer. Oran: {value:.2f}."


def decision_comment(score: float) -> str:
    if score >= 0.70:
        return "İndikatörler genel olarak olumlu. Risk ve özgüven motoru da onaylarsa sanal işlem düşünülebilir."
    if score >= 0.50:
        return "İndikatörler karışık. Sistem izlemeli, acele etmemeli."
    return "İndikatörler zayıf. İşlem açmak için uygun teknik zemin yok."


def build_indicator_snapshot(
    symbol: str,
    candles: list[Any],
    config: IndicatorConfig | None = None,
) -> IndicatorSnapshot:
    config = config or IndicatorConfig()
    if not candles:
        logs = [
            make_log(
                LogChannel.INDICATOR,
                "İndikatör hesaplanamadı: mum verisi yok.",
                LogLevel.WARNING,
                {"symbol": symbol},
                "Sistem indikatör hesaplamak için yeterli piyasa verisi bulamadı.",
            )
        ]
        return IndicatorSnapshot(symbol, "", 0.0, None, 0.5, None, 0.5, None, None, None, 0.5, 0.5, "Veri yok.", "Veri yok.", "Veri yok.", "Veri yok.", "Veri yok.", logs)

    closes = [_value(candle, "close") for candle in candles]
    price = closes[-1]
    timestamp = _timestamp(candles[-1])

    ema_values = ema_series(closes, config.ema_period)
    ema_now = ema_values[-1] if ema_values else None
    ema_previous = ema_values[-2] if len(ema_values) >= 2 else None

    trend_score = ema_signal(price, ema_now, ema_previous)
    rsi_now = rsi_value(closes, config.rsi_period)
    momentum_score = rsi_signal(rsi_now)
    atr_now = atr_value(candles, config.atr_period)
    atr_pct, volatility_text = atr_risk_comment(atr_now, price)
    vol_ratio = volume_ratio(candles, config.volume_short_period, config.volume_long_period)
    vol_score = volume_signal(vol_ratio)

    # ATR is reported as risk context, not directly included in the entry indicator score.
    indicator_score = _clamp((trend_score * 0.40) + (momentum_score * 0.35) + (vol_score * 0.25))

    logs = [
        make_log(
            LogChannel.INDICATOR,
            "İndikatörler hesaplandı.",
            LogLevel.INFO,
            {
                "symbol": symbol,
                "price": price,
                "ema": ema_now,
                "ema_signal": trend_score,
                "rsi": rsi_now,
                "rsi_signal": momentum_score,
                "atr": atr_now,
                "atr_pct": atr_pct,
                "volume_ratio": vol_ratio,
                "volume_signal": vol_score,
                "indicator_score": indicator_score,
            },
            "Sistem EMA, RSI, ATR ve hacim göstergelerini hesapladı.",
        )
    ]

    return IndicatorSnapshot(
        symbol=symbol,
        timestamp=timestamp,
        price=price,
        ema_value=ema_now,
        ema_signal=trend_score,
        rsi_value=rsi_now,
        rsi_signal=momentum_score,
        atr_value=atr_now,
        atr_pct=atr_pct,
        volume_ratio=vol_ratio,
        volume_signal=vol_score,
        indicator_score=indicator_score,
        trend_comment=trend_comment(trend_score),
        momentum_comment=momentum_comment(rsi_now, momentum_score),
        volatility_comment=volatility_text,
        volume_comment=volume_comment(vol_ratio, vol_score),
        decision_comment=decision_comment(indicator_score),
        logs=logs,
    )
