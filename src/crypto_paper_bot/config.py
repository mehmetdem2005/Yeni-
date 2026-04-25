from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, PositiveFloat, field_validator


class ExchangeConfig(BaseModel):
    name: str = "binance"
    sandbox: bool = True
    api_key_env: str | None = None
    api_secret_env: str | None = None


class StrategyConfig(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    entry_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    ema_period: int = Field(default=50, ge=2)
    rsi_period: int = Field(default=14, ge=2)
    mfi_period: int = Field(default=14, ge=2)
    atr_period: int = Field(default=14, ge=2)
    atr_multiplier: PositiveFloat = 1.5
    reward_risk: PositiveFloat = 3.0
    min_reward_risk_after_resistance: PositiveFloat = 2.0
    resistance_lookback_h1: int = Field(default=20, ge=2)


class RiskConfig(BaseModel):
    account_risk_per_trade: float = Field(default=0.005, gt=0.0, le=0.05)
    max_position_pct: float = Field(default=0.05, gt=0.0, le=1.0)
    min_position_pct: float = Field(default=0.005, ge=0.0, le=1.0)
    max_open_positions: int = Field(default=2, ge=1)
    max_portfolio_open_risk: float = Field(default=0.01, gt=0.0, le=1.0)
    max_btc_corr: float = Field(default=0.80, ge=-1.0, le=1.0)
    consecutive_stop_cooldown_count: int = Field(default=5, ge=1)
    consecutive_stop_cooldown_hours: int = Field(default=24, ge=1)


class ExecutionConfig(BaseModel):
    aggressive_limit_offset_pct: float = Field(default=0.001, ge=0.0, le=0.02)
    order_timeout_seconds: int = Field(default=10, ge=1)
    default_fee_rate: float = Field(default=0.001, ge=0.0, le=0.02)
    depth_band_pct: float = Field(default=0.002, gt=0.0, le=0.05)
    required_depth_multiple: PositiveFloat = 5.0
    max_spread_pct_abs: float = Field(default=0.0015, gt=0.0, le=0.05)
    spread_avg_multiplier: PositiveFloat = 2.0
    volume_lookback_short: int = Field(default=5, ge=1)
    volume_lookback_long: int = Field(default=50, ge=2)
    min_volume_ratio: PositiveFloat = 0.50
    volatility_lookback: int = Field(default=50, ge=2)
    volatility_pause_multiplier: PositiveFloat = 3.0
    time_stop_hours: int = Field(default=12, ge=1)


class AppConfig(BaseModel):
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)

    @field_validator("strategy")
    @classmethod
    def symbols_must_exist(cls, value: StrategyConfig) -> StrategyConfig:
        if not value.symbols:
            raise ValueError("At least one symbol is required")
        return value


def load_config(path: str | Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(raw)


def default_config() -> AppConfig:
    return AppConfig()
