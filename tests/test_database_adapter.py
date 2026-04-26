from __future__ import annotations

from pathlib import Path

from crypto_paper_bot.database_adapter import (
    DatabaseBackend,
    create_storage,
    detect_database_config,
    storage_runtime_info,
)
from crypto_paper_bot.storage import BotStorage


def test_detects_sqlite_when_database_url_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "bot.sqlite3"))

    config = detect_database_config()

    assert config.backend == DatabaseBackend.SQLITE
    assert config.sqlite_path.endswith("bot.sqlite3")


def test_create_storage_returns_sqlite_storage_without_database_url(monkeypatch, tmp_path: Path) -> None:
    sqlite_path = tmp_path / "bot.sqlite3"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(sqlite_path))

    storage = create_storage()

    assert isinstance(storage, BotStorage)
    assert storage.candle_count() == 0
    assert sqlite_path.exists()


def test_storage_runtime_info_for_sqlite(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "bot.sqlite3"))

    info = storage_runtime_info()

    assert info["backend"] == "sqlite"
    assert info["postgres_ready"] is False
    assert info["database_url_present"] is False
    assert "SQLite" in info["note"]


def test_detects_postgres_when_database_url_present(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com:5432/db")

    config = detect_database_config()
    info = storage_runtime_info(config)

    assert config.backend == DatabaseBackend.POSTGRES
    assert info["backend"] == "postgres"
    assert info["database_url_present"] is True
    assert info["postgres_ready"] is True


def test_postgres_storage_requires_driver_or_attempts_connection(monkeypatch) -> None:
    # This test does not require a real Supabase database. It only checks that the
    # factory selects the Postgres path when DATABASE_URL is set. In environments
    # without psycopg, it raises a clear dependency error. In environments with
    # psycopg, it may raise a connection/schema error, which is still acceptable
    # because no real DB is provided here.
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@127.0.0.1:1/db")

    try:
        create_storage()
    except Exception as exc:
        message = str(exc).lower()
        assert "psycopg" in message or "connection" in message or "refused" in message or "database" in message
    else:
        raise AssertionError("Postgres storage unexpectedly connected to a fake database URL")
