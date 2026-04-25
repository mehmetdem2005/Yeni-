from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class ExchangeConfig:
    name: str = "binance"
    sandbox: bool = True
    api_key_env: str | None = None
    api_secret_env: str | None = None


@dataclass
class StrategyConfig:
    symbols: list[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    entry_threshold: float = 0.70
    ema_period: int = 50
    rsi_period: int = 14
    mfi_period: int = 14
    atr_period: int = 14
    atr_multiplier: float = 1.5
    reward_risk: float = 3.0
    min_reward_risk_after_resistance: float = 2.0
    resistance_lookback_h1: int = 20


@dataclass
class RiskConfig:
    account_risk_per_trade: float = 0.005
    max_position_pct: float = 0.05
    min_position_pct: float = 0.005
    max_open_positions: int = 2
    max_portfolio_open_risk: float = 0.01
    max_btc_corr: float = 0.80
    consecutive_stop_cooldown_count: int = 5
    consecutive_stop_cooldown_hours: int = 24


@dataclass
class ExecutionConfig:
    aggressive_limit_offset_pct: float = 0.001
    order_timeout_seconds: int = 10
    default_fee_rate: float = 0.001
    depth_band_pct: float = 0.002
    required_depth_multiple: float = 5.0
    max_spread_pct_abs: float = 0.0015
    spread_avg_multiplier: float = 2.0
    volume_lookback_short: int = 5
    volume_lookback_long: int = 50
    min_volume_ratio: float = 0.50
    volatility_lookback: int = 50
    volatility_pause_multiplier: float = 3.0
    time_stop_hours: int = 12


@dataclass
class AppConfig:
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    def model_dump_json(self, indent: int = 2) -> str:
        import json

        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)


def _merge_dataclass(instance: Any, values: dict[str, Any]) -> Any:
    if not values:
        return instance
    for key, value in values.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
    return instance


def _validate_config(cfg: AppConfig) -> None:
    if not cfg.strategy.symbols:
        raise ValueError("At least one symbol is required")
    if not 0.0 <= cfg.strategy.entry_threshold <= 1.0:
        raise ValueError("entry_threshold must be between 0 and 1")
    if cfg.risk.account_risk_per_trade <= 0:
        raise ValueError("account_risk_per_trade must be positive")
    if cfg.risk.max_position_pct <= 0:
        raise ValueError("max_position_pct must be positive")


def load_config(path: str | Path) -> AppConfig:
    if yaml is None:
        raise RuntimeError("PyYAML is required for load_config. Install with: python -m pip install PyYAML")
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cfg = AppConfig()
    _merge_dataclass(cfg.exchange, raw.get("exchange", {}))
    _merge_dataclass(cfg.strategy, raw.get("strategy", {}))
    _merge_dataclass(cfg.risk, raw.get("risk", {}))
    _merge_dataclass(cfg.execution, raw.get("execution", {}))
    _validate_config(cfg)
    return cfg


def default_config() -> AppConfig:
    cfg = AppConfig()
    _validate_config(cfg)
    return cfg
