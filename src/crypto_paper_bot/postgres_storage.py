from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterator

START_BALANCE = 10000.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: Any) -> str:
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


class PostgresStorage:
    """Postgres/Supabase implementation of the BotStorage interface.

    This adapter intentionally mirrors the existing SQLite BotStorage public methods
    so the rest of the app can switch storage backends through database_adapter.py.
    """

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_driver()
        self.init_db_minimum()

    def _ensure_driver(self) -> None:
        try:
            import psycopg  # noqa: F401
            from psycopg.rows import dict_row  # noqa: F401
        except Exception as exc:
            raise RuntimeError(
                "PostgresStorage requires psycopg. Install cloud dependencies with: "
                "python -m pip install -r requirements-cloud.txt"
            ) from exc

    @contextmanager
    def connect(self) -> Iterator[Any]:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(self.database_url, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db_minimum(self) -> None:
        """Create only the absolutely required wallet row.

        The full schema should be created through supabase/schema.sql. This method
        does not try to own migrations; it only makes the default wallet row idempotent.
        """
        with self.connect() as conn:
            conn.execute(
                """
                insert into paper_wallets(name, starting_balance, cash)
                values ('default', %s, %s)
                on conflict (name) do nothing
                """,
                (START_BALANCE, START_BALANCE),
            )

    def upsert_candles(self, symbol: str, interval: str, candles: list[Any]) -> int:
        rows = []
        for candle in candles:
            rows.append(
                (
                    symbol,
                    interval,
                    candle.timestamp.isoformat() if hasattr(candle.timestamp, "isoformat") else str(candle.timestamp),
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume,
                )
            )
        if not rows:
            return 0
        with self.connect() as conn:
            conn.executemany(
                """
                insert into candles(symbol, timeframe, open_time, open, high, low, close, volume)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (symbol, timeframe, open_time)
                do update set
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume
                """,
                rows,
            )
        return len(rows)

    def candle_count(self) -> int:
        with self.connect() as conn:
            row = conn.execute("select count(*) as n from candles").fetchone()
        return int(row["n"])

    def get_candles(self, symbol: str, interval: str, limit: int = 1000) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select
                    symbol,
                    timeframe as interval,
                    open_time as timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume
                from candles
                where symbol = %s and timeframe = %s
                order by open_time desc
                limit %s
                """,
                (symbol, interval, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            item = dict(row)
            item["timestamp"] = item["timestamp"].isoformat() if hasattr(item["timestamp"], "isoformat") else str(item["timestamp"])
            for key in ("open", "high", "low", "close", "volume"):
                item[key] = float(item[key])
            result.append(item)
        return result

    def save_model_state(self, weights: dict[str, float], metrics: dict[str, Any], trained_samples: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                insert into app_settings(key, value_json, is_secret)
                values ('model_state', %s::jsonb, false)
                on conflict (key) do update set value_json = excluded.value_json, updated_at = now()
                """,
                (_json({"updated_at": utc_now(), "weights": weights, "metrics": metrics, "trained_samples": trained_samples}),),
            )

    def load_model_state(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("select value_json from app_settings where key = 'model_state'").fetchone()
        if row is None:
            return None
        return _loads(row["value_json"])

    def log_signal(self, symbol: str, score: float, ml_probability: float | None, decision: str, payload: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                insert into signal_log(symbol, indicator_score, ai_prediction, trade_confidence, system_confidence, decision, explanation, payload_json)
                values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    symbol,
                    score,
                    ml_probability,
                    (payload.get("confidence") or {}).get("trade_confidence"),
                    (payload.get("system_confidence") or {}).get("system_confidence"),
                    decision,
                    payload.get("explanation"),
                    _json(payload),
                ),
            )

    def latest_signals(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select
                    id,
                    signal_time as created_at,
                    symbol,
                    indicator_score as score,
                    ai_prediction as ml_probability,
                    decision,
                    payload_json
                from signal_log
                order by signal_time desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"])
            if item.get("score") is not None:
                item["score"] = float(item["score"])
            if item.get("ml_probability") is not None:
                item["ml_probability"] = float(item["ml_probability"])
            item["payload_json"] = _json(_loads(item.get("payload_json")) or {})
            result.append(item)
        return result

    def open_positions(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select * from paper_positions
                where status = 'OPEN'
                order by opened_at desc
                """
            ).fetchall()
        return [self._position_row(row) for row in rows]

    def all_positions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select * from paper_positions
                order by opened_at desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        return [self._position_row(row) for row in rows]

    def _position_row(self, row: dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        item["id"] = str(item["id"])
        for tkey in ("opened_at", "closed_at", "created_at", "updated_at"):
            if item.get(tkey) is not None and hasattr(item[tkey], "isoformat"):
                item[tkey] = item[tkey].isoformat()
        for key in ("entry_price", "close_price", "qty", "notional", "stop_loss", "take_profit", "pnl"):
            if item.get(key) is not None:
                item[key] = float(item[key])
        return item

    def wallet(self) -> dict[str, float]:
        with self.connect() as conn:
            row = conn.execute("select * from paper_wallets where name = 'default'").fetchone()
        if row is None:
            return {"cash": START_BALANCE, "starting_balance": START_BALANCE}
        return {
            "cash": float(row["cash"]),
            "starting_balance": float(row["starting_balance"]),
            "updated_at": row["updated_at"].isoformat() if hasattr(row.get("updated_at"), "isoformat") else str(row.get("updated_at")),
        }

    def realized_pnl(self) -> float:
        with self.connect() as conn:
            row = conn.execute("select coalesce(sum(pnl), 0) as pnl from paper_positions where status = 'CLOSED'").fetchone()
        return float(row["pnl"])

    def open_position(self, symbol: str, entry_price: float, qty: float, notional: float, stop_loss: float, take_profit: float) -> bool:
        with self.connect() as conn:
            wallet = conn.execute("select cash from paper_wallets where name = 'default' for update").fetchone()
            if wallet is None or float(wallet["cash"]) < notional:
                return False
            conn.execute("update paper_wallets set cash = cash - %s, updated_at = now() where name = 'default'", (notional,))
            conn.execute(
                """
                insert into paper_positions(wallet_name, symbol, status, entry_price, qty, notional, stop_loss, take_profit)
                values ('default', %s, 'OPEN', %s, %s, %s, %s, %s)
                """,
                (symbol, entry_price, qty, notional, stop_loss, take_profit),
            )
        return True

    def close_position(self, position_id: int | str, close_price: float, pnl: float, reason: str) -> None:
        with self.connect() as conn:
            pos = conn.execute("select * from paper_positions where id = %s for update", (str(position_id),)).fetchone()
            if pos is None or pos["status"] != "OPEN":
                return
            cash_back = float(pos["notional"]) + pnl
            conn.execute("update paper_wallets set cash = cash + %s, updated_at = now() where name = 'default'", (cash_back,))
            conn.execute(
                """
                update paper_positions
                set status='CLOSED', closed_at=now(), close_price=%s, pnl=%s, reason=%s
                where id=%s
                """,
                (close_price, pnl, reason, str(position_id)),
            )

    def record_equity(self, prices: dict[str, float]) -> dict[str, float]:
        wallet = self.wallet()
        open_value = 0.0
        for pos in self.open_positions():
            price = prices.get(pos["symbol"], float(pos["entry_price"]))
            open_value += float(pos["qty"]) * price
        equity = float(wallet["cash"]) + open_value
        pnl = self.realized_pnl()
        with self.connect() as conn:
            conn.execute(
                """
                insert into equity_points(wallet_name, equity, cash, open_value, realized_pnl)
                values ('default', %s, %s, %s, %s)
                """,
                (equity, wallet["cash"], open_value, pnl),
            )
        return {"equity": equity, "cash": float(wallet["cash"]), "open_value": open_value, "realized_pnl": pnl}

    def equity_points(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select * from equity_points
                where wallet_name = 'default'
                order by created_at desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        result = []
        for row in reversed(rows):
            item = dict(row)
            item["id"] = str(item["id"])
            item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"])
            for key in ("equity", "cash", "open_value", "realized_pnl"):
                item[key] = float(item[key])
            result.append(item)
        return result

    def trade_stats(self) -> dict[str, Any]:
        positions = self.all_positions(1000)
        closed = [p for p in positions if p["status"] == "CLOSED"]
        wins = [p for p in closed if (p.get("pnl") or 0) > 0]
        total_pnl = sum(float(p.get("pnl") or 0) for p in closed)
        return {
            "closed_count": len(closed),
            "open_count": len([p for p in positions if p["status"] == "OPEN"]),
            "win_rate": 0 if not closed else len(wins) / len(closed),
            "total_pnl": total_pnl,
        }

    def event(self, level: str, message: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        channel = str(payload.get("channel") or "system")
        user_explanation = payload.get("user_explanation")
        with self.connect() as conn:
            conn.execute(
                """
                insert into event_logs(channel, level, message, user_explanation, payload_json)
                values (%s, %s, %s, %s, %s::jsonb)
                """,
                (channel, level, message, user_explanation, _json(payload)),
            )

    def latest_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, created_at, level, message, payload_json
                from event_logs
                order by created_at desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["id"] = str(item["id"])
            item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"])
            item["payload_json"] = _json(_loads(item.get("payload_json")) or {})
            result.append(item)
        return result

    def reset_paper_account(self) -> None:
        with self.connect() as conn:
            conn.execute("delete from paper_positions")
            conn.execute("delete from equity_points")
            conn.execute("delete from signal_log")
            conn.execute(
                """
                update paper_wallets
                set cash = %s, starting_balance = %s, updated_at = now()
                where name = 'default'
                """,
                (START_BALANCE, START_BALANCE),
            )
