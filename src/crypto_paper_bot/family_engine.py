from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from crypto_paper_bot.indicator_engine import IndicatorSnapshot
from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log


class FamilyName(str, Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY_RISK = "volatility_risk"
    VOLUME_LIQUIDITY = "volume_liquidity"
    REGIME = "regime"
    AI = "ai"


FAMILY_TITLES: dict[FamilyName, str] = {
    FamilyName.TREND: "Trend Ailesi",
    FamilyName.MOMENTUM: "Momentum Ailesi",
    FamilyName.VOLATILITY_RISK: "Volatilite / Risk Ailesi",
    FamilyName.VOLUME_LIQUIDITY: "Hacim / Likidite Ailesi",
    FamilyName.REGIME: "Rejim / Piyasa Yönü Ailesi",
    FamilyName.AI: "Yapay Zekâ Ailesi",
}


@dataclass(frozen=True)
class FamilyScore:
    name: FamilyName
    title: str
    score: float
    contribution_hint: float
    status: str
    comment: str
    inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FamilySnapshot:
    symbol: str
    timestamp: str
    families: dict[FamilyName, FamilyScore]
    family_average_score: float
    strongest_family: FamilyName
    weakest_family: FamilyName
    summary: str
    logs: list[LogRecord] = field(default_factory=list)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _status(score: float) -> str:
    if score >= 0.70:
        return "Güçlü"
    if score >= 0.50:
        return "Orta"
    return "Zayıf"


def _score_or_neutral(value: float | None) -> float:
    if value is None:
        return 0.5
    return _clamp(float(value))


def _volatility_risk_score(atr_pct: float | None) -> float:
    """Return a high score when volatility is tradable, not necessarily low.

    Too little volatility can mean no opportunity; too much volatility can make stop-loss wide.
    The best region is moderate volatility.
    """

    if atr_pct is None:
        return 0.5
    if atr_pct < 0.005:
        return 0.45
    if atr_pct < 0.015:
        return 0.85
    if atr_pct < 0.04:
        return 0.65
    if atr_pct < 0.08:
        return 0.30
    return 0.10


def _regime_score(weekly_ok: bool | None, daily_ok: bool | None) -> float:
    if weekly_ok is True and daily_ok is True:
        return 1.0
    if weekly_ok is True and daily_ok is False:
        return 0.55
    if weekly_ok is False and daily_ok is True:
        return 0.45
    if weekly_ok is False and daily_ok is False:
        return 0.0
    return 0.5


def _ai_score(ai_probability: float | None) -> float:
    if ai_probability is None:
        return 0.5
    return _clamp(float(ai_probability))


def _comment(name: FamilyName, score: float) -> str:
    status = _status(score)

    if name == FamilyName.TREND:
        if status == "Güçlü":
            return "Trend ailesi fiyatın yukarı eğilimde olduğunu söylüyor."
        if status == "Orta":
            return "Trend ailesi kararsız; fiyat yönü net değil."
        return "Trend ailesi zayıf; fiyat ana ortalamanın altında veya eğim güçsüz."

    if name == FamilyName.MOMENTUM:
        if status == "Güçlü":
            return "Momentum ailesi hareketin sağlıklı bölgede olduğunu gösteriyor."
        if status == "Orta":
            return "Momentum ailesi nötr; tek başına işlem için yeterli değil."
        return "Momentum ailesi riskli bölgede; aşırı zayıf veya aşırı ısınmış olabilir."

    if name == FamilyName.VOLATILITY_RISK:
        if status == "Güçlü":
            return "Volatilite işlem için yönetilebilir görünüyor."
        if status == "Orta":
            return "Volatilite orta; pozisyon miktarı dikkatli seçilmeli."
        return "Volatilite riskli; stop mesafesi veya ani hareket riski yüksek."

    if name == FamilyName.VOLUME_LIQUIDITY:
        if status == "Güçlü":
            return "Hacim ailesi hareketin piyasa katılımıyla desteklendiğini gösteriyor."
        if status == "Orta":
            return "Hacim normal seviyede; sinyali destekliyor ama çok güçlü değil."
        return "Hacim zayıf; sinyalin güvenilirliği düşer."

    if name == FamilyName.REGIME:
        if status == "Güçlü":
            return "Büyük yön ve günlük yön uyumlu."
        if status == "Orta":
            return "Büyük yön ile günlük yön tam uyumlu değil."
        return "Rejim zayıf; ana yön işlem açmak için uygun değil."

    if name == FamilyName.AI:
        if status == "Güçlü":
            return "Yapay zekâ geçmiş örneklere göre olumlu ihtimali yüksek görüyor."
        if status == "Orta":
            return "Yapay zekâ kararsız; tek başına güçlü onay vermiyor."
        return "Yapay zekâ olumlu sonuç ihtimalini düşük görüyor."

    return "Aile skoru hesaplandı."


def build_family_scores(
    indicator: IndicatorSnapshot,
    ai_probability: float | None = None,
    weekly_ok: bool | None = None,
    daily_ok: bool | None = None,
) -> FamilySnapshot:
    """Build family-level scores from indicator and context snapshots.

    This file does not make trade decisions. It only groups signals into visible
    families so the dashboard can explain the system cleanly.
    """

    trend = _score_or_neutral(indicator.ema_signal)
    momentum = _score_or_neutral(indicator.rsi_signal)
    volatility = _volatility_risk_score(indicator.atr_pct)
    volume = _score_or_neutral(indicator.volume_signal)
    regime = _regime_score(weekly_ok, daily_ok)
    ai = _ai_score(ai_probability)

    raw_scores: dict[FamilyName, tuple[float, dict[str, Any]]] = {
        FamilyName.TREND: (
            trend,
            {
                "ema_signal": indicator.ema_signal,
                "ema_value": indicator.ema_value,
                "price": indicator.price,
            },
        ),
        FamilyName.MOMENTUM: (
            momentum,
            {
                "rsi_signal": indicator.rsi_signal,
                "rsi_value": indicator.rsi_value,
            },
        ),
        FamilyName.VOLATILITY_RISK: (
            volatility,
            {
                "atr_value": indicator.atr_value,
                "atr_pct": indicator.atr_pct,
            },
        ),
        FamilyName.VOLUME_LIQUIDITY: (
            volume,
            {
                "volume_signal": indicator.volume_signal,
                "volume_ratio": indicator.volume_ratio,
            },
        ),
        FamilyName.REGIME: (
            regime,
            {
                "weekly_ok": weekly_ok,
                "daily_ok": daily_ok,
            },
        ),
        FamilyName.AI: (
            ai,
            {
                "ai_probability": ai_probability,
            },
        ),
    }

    family_objects: dict[FamilyName, FamilyScore] = {}
    total = 0.0
    for name, (score, inputs) in raw_scores.items():
        score = _clamp(score)
        total += score
        family_objects[name] = FamilyScore(
            name=name,
            title=FAMILY_TITLES[name],
            score=score,
            contribution_hint=0.0,
            status=_status(score),
            comment=_comment(name, score),
            inputs=inputs,
        )

    average = total / len(raw_scores)
    strongest = max(family_objects, key=lambda key: family_objects[key].score)
    weakest = min(family_objects, key=lambda key: family_objects[key].score)

    # Contribution hint is not the final confidence weight. It is a simple visual share
    # inside the family panel. The adaptive confidence engine will calculate real weights.
    score_sum = sum(item.score for item in family_objects.values()) or 1.0
    with_contributions: dict[FamilyName, FamilyScore] = {}
    for name, item in family_objects.items():
        with_contributions[name] = FamilyScore(
            name=item.name,
            title=item.title,
            score=item.score,
            contribution_hint=item.score / score_sum,
            status=item.status,
            comment=item.comment,
            inputs=item.inputs,
        )

    summary = (
        f"En güçlü aile: {FAMILY_TITLES[strongest]}. "
        f"En zayıf aile: {FAMILY_TITLES[weakest]}. "
        f"Aile ortalaması: %{average * 100:.1f}."
    )

    logs = [
        make_log(
            LogChannel.FAMILY,
            "Aile skorları hesaplandı.",
            LogLevel.INFO,
            {
                "symbol": indicator.symbol,
                "family_average_score": average,
                "strongest_family": strongest.value,
                "weakest_family": weakest.value,
                "families": {
                    name.value: {
                        "score": score.score,
                        "status": score.status,
                        "contribution_hint": score.contribution_hint,
                    }
                    for name, score in with_contributions.items()
                },
            },
            summary,
        )
    ]

    return FamilySnapshot(
        symbol=indicator.symbol,
        timestamp=indicator.timestamp,
        families=with_contributions,
        family_average_score=average,
        strongest_family=strongest,
        weakest_family=weakest,
        summary=summary,
        logs=logs,
    )


def family_title(name: FamilyName | str) -> str:
    if isinstance(name, str):
        name = FamilyName(name)
    return FAMILY_TITLES[name]


def family_scores_as_plain_dict(snapshot: FamilySnapshot) -> dict[str, Any]:
    return {
        "symbol": snapshot.symbol,
        "timestamp": snapshot.timestamp,
        "family_average_score": snapshot.family_average_score,
        "strongest_family": snapshot.strongest_family.value,
        "weakest_family": snapshot.weakest_family.value,
        "summary": snapshot.summary,
        "families": {
            name.value: {
                "title": score.title,
                "score": score.score,
                "status": score.status,
                "contribution_hint": score.contribution_hint,
                "comment": score.comment,
                "inputs": score.inputs,
            }
            for name, score in snapshot.families.items()
        },
    }
