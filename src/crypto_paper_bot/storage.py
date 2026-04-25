from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DB_PATH = Path("data/bot.sqlite3")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)


class BotStorage:
    def __init__(self, path: str | Path = DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS candles (
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    PRIMARY KEY(symbol, interval, timestamp)
                );

                CREATE TABLE IF NOT EXISTS model_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    updated_at TEXT NOT NULL,
                    weights_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    trained_samples INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS signal_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    score REAL NOT NULL,
                    ml_probability REAL,
                    decision TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    qty REAL NOT NULL,
                    notional REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    close_price REAL,
                    pnl REAL,
                    reason TEXT
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT
                );
                """
            )

    def upsert_candles(self, symbol: str, interval: str, candles: list[Any]) -> int:
        rows = [
            (
                symbol,
                interval,
                c.timestamp.isoformat(),
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
            )
            for c in candles
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO candles(symbol, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def candle_count(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM candles").fetchone()
            return int(row["n"])

    def get_candles(self, symbol: str, interval: str, limit: int = 1000) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM candles WHERE symbol = ? AND interval = ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (symbol, interval, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def save_model_state(self, weights: dict[str, float], metrics: dict[str, Any], trained_samples: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_state(id, updated_at, weights_json, metrics_json, trained_samples)
                VALUES (1, ?, ?, ?, ?)
                """,
                (utc_now(), _json(weights), _json(metrics), trained_samples),
            )

    def load_model_state(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_state WHERE id = 1").fetchone()
        if row is None:
            return None
        return {
            "updated_at": row["updated_at"],
            "weights": json.loads(row["weights_json"]),
            "metrics": json.loads(row["metrics_json"]),
            "trained_samples": row["trained_samples"],
        }

    def log_signal(self, symbol: str, score: float, ml_probability: float | None, decision: str, payload: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_log(created_at, symbol, score, ml_probability, decision, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (utc_now(), symbol, score, ml_probability, decision, _json(payload)),
            )

    def latest_signals(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM signal_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def open_positions(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM paper_positions WHERE status = 'OPEN' ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def all_positions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM paper_positions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def open_position(self, symbol: str, entry_price: float, qty: float, notional: float, stop_loss: float, take_profit: float) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO paper_positions(opened_at, symbol, status, entry_price, qty, notional, stop_loss, take_profit)
                VALUES (?, ?, 'OPEN', ?, ?, ?, ?, ?)
                """,
                (utc_now(), symbol, entry_price, qty, notional, stop_loss, take_profit),
            )

    def close_position(self, position_id: int, close_price: float, pnl: float, reason: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE paper_positions
                SET status='CLOSED', closed_at=?, close_price=?, pnl=?, reason=?
                WHERE id=?
                """,
                (utc_now(), close_price, pnl, reason, position_id),
            )

    def event(self, level: str, message: str, payload: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events(created_at, level, message, payload_json) VALUES (?, ?, ?, ?)",
                (utc_now(), level, message, _json(payload or {})),
            )

    def latest_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
