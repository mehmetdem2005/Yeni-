from datetime import datetime, timezone

import pandas as pd

from crypto_paper_bot.config import default_config
from crypto_paper_bot.models import SignalSnapshot
from crypto_paper_bot.risk import build_risk_plan


def _snapshot(price: float = 100.0, atr: float = 2.0) -> SignalSnapshot:
    return SignalSnapshot(
        symbol="BTC/USDT",
        timestamp=datetime.now(timezone.utc),
        ema_signal=1.0,
        rsi_signal=1.0,
        mfi_signal=1.0,
        final_score=1.0,
        w1_gate_open=True,
        d1_gate_open=True,
        atr=atr,
        entry_reference_price=price,
    )


def test_risk_plan_uses_atr_distance_and_caps_position() -> None:
    cfg = default_config()
    h1 = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=30, freq="h", tz="UTC"),
            "high": [200.0] * 30,
        }
    )
    plan = build_risk_plan(_snapshot(), h1, cfg.strategy, cfg.risk)
    assert plan is not None
    assert plan.stop_loss == 97.0
    assert plan.take_profit == 109.0
    assert plan.position_pct <= cfg.risk.max_position_pct
    assert plan.reward_risk == 3.0


def test_resistance_rejects_bad_reward_risk() -> None:
    cfg = default_config()
    h1 = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=30, freq="h", tz="UTC"),
            "high": [104.0] * 30,
        }
    )
    plan = build_risk_plan(_snapshot(), h1, cfg.strategy, cfg.risk)
    assert plan is None
