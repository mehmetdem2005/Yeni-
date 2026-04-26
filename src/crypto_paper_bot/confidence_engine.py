from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crypto_paper_bot.adaptive_confidence import (
    COMPONENTS,
    ComponentStats,
    adaptive_weights,
    component_stats_from_trades,
    compute_system_confidence,
)
from crypto_paper_bot.family_engine import FamilyName, FamilySnapshot
from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log


@dataclass(frozen=True)
class ConfidenceInput:
    indicator_score: float
    ai_prediction: float | None
    regime_score: float
    liquidity_score: float
    risk_reward_score: float
    portfolio_safety_score: float


@dataclass(frozen=True)
class TradeConfidenceSnapshot:
    symbol: str
    trade_confidence: float
    component_scores: dict[str, float]
    adaptive_weights: dict[str, float]
    contributions: dict[str, float]
    strongest_component: str
    weakest_component: str
    decision_zone: str
    explanation: str
    logs: list[LogRecord] = field(default_factory=list)


@dataclass(frozen=True)
class SystemConfidenceSnapshot:
    system_confidence: float
    data_health: float
    model_health: float
    api_health: float
    account_health: float
    risk_health: float
    status: str
    explanation: str
    logs: list[LogRecord] = field(default_factory=list)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_status(score: float) -> str:
    if score >= 0.75:
        return "Güçlü"
    if score >= 0.60:
        return "Orta-Güçlü"
    if score >= 0.45:
        return "Orta"
    return "Zayıf"


def decision_zone(score: float) -> str:
    if score >= 0.75:
        return "İşleme Yakın"
    if score >= 0.65:
        return "Dikkatli İzle"
    if score >= 0.50:
        return "Kararsız"
    return "İşlemden Uzak Dur"


def component_label(component: str) -> str:
    labels = {
        "indicator": "İndikatör Skoru",
        "ai_prediction": "Yapay Zekâ Tahmini",
        "regime": "Rejim Uyum Skoru",
        "liquidity": "Likidite Skoru",
        "risk_reward": "Risk/Ödül Skoru",
        "portfolio_safety": "Portföy Güvenliği Skoru",
    }
    return labels.get(component, component)


def build_confidence_input(
    family_snapshot: FamilySnapshot,
    liquidity_score: float = 0.70,
    risk_reward_score: float = 0.70,
    portfolio_safety_score: float = 1.0,
) -> ConfidenceInput:
    families = family_snapshot.families
    indicator_score = (
        families[FamilyName.TREND].score * 0.40
        + families[FamilyName.MOMENTUM].score * 0.35
        + families[FamilyName.VOLUME_LIQUIDITY].score * 0.25
    )
    ai_score = families[FamilyName.AI].score
    regime_score = families[FamilyName.REGIME].score
    return ConfidenceInput(
        indicator_score=clamp(indicator_score),
        ai_prediction=clamp(ai_score),
        regime_score=clamp(regime_score),
        liquidity_score=clamp(liquidity_score),
        risk_reward_score=clamp(risk_reward_score),
        portfolio_safety_score=clamp(portfolio_safety_score),
    )


def confidence_input_to_scores(data: ConfidenceInput) -> dict[str, float]:
    return {
        "indicator": clamp(data.indicator_score),
        "ai_prediction": 0.5 if data.ai_prediction is None else clamp(data.ai_prediction),
        "regime": clamp(data.regime_score),
        "liquidity": clamp(data.liquidity_score),
        "risk_reward": clamp(data.risk_reward_score),
        "portfolio_safety": clamp(data.portfolio_safety_score),
    }


def calculate_trade_confidence(
    symbol: str,
    data: ConfidenceInput,
    component_stats: dict[str, ComponentStats] | None = None,
) -> TradeConfidenceSnapshot:
    scores = confidence_input_to_scores(data)
    weights = adaptive_weights(component_stats)
    contributions: dict[str, float] = {}
    total = 0.0

    for component in COMPONENTS:
        contribution = scores[component] * weights[component]
        contributions[component] = contribution
        total += contribution

    total = clamp(total)
    strongest = max(contributions, key=contributions.get)
    weakest = min(contributions, key=contributions.get)
    zone = decision_zone(total)
    explanation = (
        f"İşlem özgüveni %{total * 100:.1f}. "
        f"En güçlü katkı: {component_label(strongest)}. "
        f"En zayıf katkı: {component_label(weakest)}. "
        "Ağırlıklar geçmiş sanal işlem başarısına göre otomatik ayarlanır."
    )

    logs = [
        make_log(
            LogChannel.CONFIDENCE,
            "İşlem özgüveni hesaplandı.",
            LogLevel.INFO,
            {
                "symbol": symbol,
                "trade_confidence": total,
                "component_scores": scores,
                "adaptive_weights": weights,
                "contributions": contributions,
                "strongest_component": strongest,
                "weakest_component": weakest,
                "decision_zone": zone,
            },
            explanation,
        )
    ]

    return TradeConfidenceSnapshot(
        symbol=symbol,
        trade_confidence=total,
        component_scores=scores,
        adaptive_weights=weights,
        contributions=contributions,
        strongest_component=strongest,
        weakest_component=weakest,
        decision_zone=zone,
        explanation=explanation,
        logs=logs,
    )


def trade_stats_to_component_stats(trades: list[dict[str, Any]]) -> dict[str, ComponentStats]:
    return component_stats_from_trades(trades)


def data_health_score(candle_count: int, min_expected: int = 500) -> float:
    if min_expected <= 0:
        return 1.0
    return clamp(candle_count / min_expected)


def model_health_score(model_state: dict[str, Any] | None) -> float:
    if not model_state:
        return 0.35
    metrics = model_state.get("metrics", {}) or {}
    accuracy = metrics.get("accuracy")
    trained_samples = float(model_state.get("trained_samples") or 0)
    sample_score = clamp(trained_samples / 500.0)
    if accuracy is None:
        return clamp(0.35 + sample_score * 0.40)
    return clamp((float(accuracy) * 0.70) + (sample_score * 0.30))


def api_health_score(latest_events: list[dict[str, Any]], lookback: int = 20) -> float:
    recent = latest_events[:lookback]
    if not recent:
        return 0.80
    errors = 0
    for event in recent:
        level = str(event.get("level") or "").upper()
        message = str(event.get("message") or "").lower()
        if level == "ERROR" or "hata" in message or "error" in message:
            errors += 1
    return clamp(1.0 - (errors / max(len(recent), 1)))


def account_health_score(wallet: dict[str, Any], trade_stats: dict[str, Any]) -> float:
    start = float(wallet.get("starting_balance") or 10000.0)
    cash = float(wallet.get("cash") or start)
    total_pnl = float(trade_stats.get("total_pnl") or 0.0)
    pnl_pct = total_pnl / start if start > 0 else 0.0
    cash_score = clamp(cash / start)
    pnl_score = clamp(0.50 + pnl_pct * 5.0)
    return clamp((cash_score * 0.45) + (pnl_score * 0.55))


def risk_health_score(open_positions: list[dict[str, Any]], max_open_positions: int = 2) -> float:
    count = len([position for position in open_positions if position.get("status") == "OPEN"])
    if count <= 0:
        return 1.0
    return clamp(1.0 - (count / max(max_open_positions + 1, 1)))


def calculate_system_confidence(
    candle_count: int,
    model_state: dict[str, Any] | None,
    latest_events: list[dict[str, Any]],
    wallet: dict[str, Any],
    trade_stats: dict[str, Any],
    open_positions: list[dict[str, Any]],
) -> SystemConfidenceSnapshot:
    data_health = data_health_score(candle_count)
    model_health = model_health_score(model_state)
    api_health = api_health_score(latest_events)
    account_health = account_health_score(wallet, trade_stats)
    risk_health = risk_health_score(open_positions)
    total = compute_system_confidence(
        data_health=data_health,
        model_health=model_health,
        api_health=api_health,
        account_health=account_health,
        risk_health=risk_health,
    )
    status = score_status(total)
    explanation = (
        f"Sistem genel özgüveni %{total * 100:.1f}. "
        f"Veri sağlığı %{data_health * 100:.1f}, model sağlığı %{model_health * 100:.1f}, "
        f"API sağlığı %{api_health * 100:.1f}, hesap sağlığı %{account_health * 100:.1f}, "
        f"risk sağlığı %{risk_health * 100:.1f}."
    )

    logs = [
        make_log(
            LogChannel.CONFIDENCE,
            "Sistem genel özgüveni hesaplandı.",
            LogLevel.INFO,
            {
                "system_confidence": total,
                "data_health": data_health,
                "model_health": model_health,
                "api_health": api_health,
                "account_health": account_health,
                "risk_health": risk_health,
                "status": status,
            },
            explanation,
        )
    ]

    return SystemConfidenceSnapshot(
        system_confidence=total,
        data_health=data_health,
        model_health=model_health,
        api_health=api_health,
        account_health=account_health,
        risk_health=risk_health,
        status=status,
        explanation=explanation,
        logs=logs,
    )


def confidence_snapshot_as_plain_dict(snapshot: TradeConfidenceSnapshot) -> dict[str, Any]:
    return {
        "symbol": snapshot.symbol,
        "trade_confidence": snapshot.trade_confidence,
        "component_scores": snapshot.component_scores,
        "adaptive_weights": snapshot.adaptive_weights,
        "contributions": snapshot.contributions,
        "strongest_component": snapshot.strongest_component,
        "weakest_component": snapshot.weakest_component,
        "decision_zone": snapshot.decision_zone,
        "explanation": snapshot.explanation,
    }


def system_confidence_as_plain_dict(snapshot: SystemConfidenceSnapshot) -> dict[str, Any]:
    return {
        "system_confidence": snapshot.system_confidence,
        "data_health": snapshot.data_health,
        "model_health": snapshot.model_health,
        "api_health": snapshot.api_health,
        "account_health": snapshot.account_health,
        "risk_health": snapshot.risk_health,
        "status": snapshot.status,
        "explanation": snapshot.explanation,
    }
