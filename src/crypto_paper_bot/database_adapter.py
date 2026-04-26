from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from crypto_paper_bot.storage import BotStorage


class DatabaseBackend(str, Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


@dataclass(frozen=True)
class DatabaseConfig:
    backend: DatabaseBackend
    sqlite_path: str = "data/bot.sqlite3"
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_service_key: str | None = None


class StoragePort(Protocol):
    def upsert_candles(self, symbol: str, interval: str, candles: list[Any]) -> int: ...
    def candle_count(self) -> int: ...
    def get_candles(self, symbol: str, interval: str, limit: int = 1000) -> list[dict[str, Any]]: ...
    def save_model_state(self, weights: dict[str, float], metrics: dict[str, Any], trained_samples: int) -> None: ...
    def load_model_state(self) -> dict[str, Any] | None: ...
    def log_signal(self, symbol: str, score: float, ml_probability: float | None, decision: str, payload: dict[str, Any]) -> None: ...
    def latest_signals(self, limit: int = 20) -> list[dict[str, Any]]: ...
    def open_positions(self) -> list[dict[str, Any]]: ...
    def all_positions(self, limit: int = 50) -> list[dict[str, Any]]: ...
    def wallet(self) -> dict[str, float]: ...
    def open_position(self, symbol: str, entry_price: float, qty: float, notional: float, stop_loss: float, take_profit: float) -> bool: ...
    def close_position(self, position_id: int, close_price: float, pnl: float, reason: str) -> None: ...
    def record_equity(self, prices: dict[str, float]) -> dict[str, float]: ...
    def equity_points(self, limit: int = 100) -> list[dict[str, Any]]: ...
    def trade_stats(self) -> dict[str, Any]: ...
    def event(self, level: str, message: str, payload: dict[str, Any] | None = None) -> None: ...
    def latest_events(self, limit: int = 20) -> list[dict[str, Any]]: ...
    def reset_paper_account(self) -> None: ...


class PostgresStorageNotReady:
    """Placeholder adapter for the cloud DB path.

    The Supabase schema exists, but the runtime storage implementation is not yet
    safe to switch on. Raising loudly is better than pretending cloud persistence
    works while still writing locally.
    """

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        raise RuntimeError(
            "Postgres/Supabase storage adapter is planned but not implemented yet. "
            "Unset DATABASE_URL to use SQLite, or implement postgres_storage.py before cloud production."
        )


def detect_database_config() -> DatabaseConfig:
    database_url = os.environ.get("DATABASE_URL", "").strip() or None
    sqlite_path = os.environ.get("SQLITE_PATH", "data/bot.sqlite3")
    supabase_url = os.environ.get("SUPABASE_URL", "").strip() or None
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip() or None

    if database_url and database_url.startswith(("postgres://", "postgresql://")):
        backend = DatabaseBackend.POSTGRES
    else:
        backend = DatabaseBackend.SQLITE

    return DatabaseConfig(
        backend=backend,
        sqlite_path=sqlite_path,
        database_url=database_url,
        supabase_url=supabase_url,
        supabase_service_key=supabase_service_key,
    )


def create_storage(config: DatabaseConfig | None = None) -> StoragePort:
    config = config or detect_database_config()
    if config.backend == DatabaseBackend.SQLITE:
        return BotStorage(Path(config.sqlite_path))
    if not config.database_url:
        raise RuntimeError("DATABASE_URL is required for Postgres backend.")
    return PostgresStorageNotReady(config.database_url)


def storage_runtime_info(config: DatabaseConfig | None = None) -> dict[str, Any]:
    config = config or detect_database_config()
    return {
        "backend": config.backend.value,
        "sqlite_path": config.sqlite_path if config.backend == DatabaseBackend.SQLITE else None,
        "database_url_present": bool(config.database_url),
        "supabase_url_present": bool(config.supabase_url),
        "supabase_service_key_present": bool(config.supabase_service_key),
        "postgres_ready": False,
        "note": (
            "SQLite runtime active."
            if config.backend == DatabaseBackend.SQLITE
            else "Postgres schema exists, but runtime adapter is intentionally not enabled yet."
        ),
    }
