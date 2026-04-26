from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AutomationState:
    running: bool = False
    interval_seconds: int = 60
    started_at: str | None = None
    stopped_at: str | None = None
    last_cycle_at: str | None = None
    last_error: str | None = None
    cycle_count: int = 0
    task_active: bool = False
    note: str = "Otomasyon beklemede."
    recent_results: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "interval_seconds": self.interval_seconds,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "last_cycle_at": self.last_cycle_at,
            "last_error": self.last_error,
            "cycle_count": self.cycle_count,
            "task_active": self.task_active,
            "note": self.note,
            "recent_results": self.recent_results[-5:],
        }


class AutomationController:
    """Small Render-friendly in-process paper-trade loop controller.

    This is not a distributed scheduler. It is enough for the web control panel MVP.
    For production, this should later move to a dedicated worker/cron service.
    """

    ALLOWED_INTERVALS = {10, 30, 60, 300}

    def __init__(self, services: Any, interval_seconds: int = 60) -> None:
        self.services = services
        self.state = AutomationState(interval_seconds=self._normalize_interval(interval_seconds))
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    def _normalize_interval(self, seconds: int) -> int:
        seconds = max(10, int(seconds))
        if seconds in self.ALLOWED_INTERVALS:
            return seconds
        return min(self.ALLOWED_INTERVALS, key=lambda item: abs(item - seconds))

    async def start(self) -> dict[str, Any]:
        async with self._lock:
            if self._task and not self._task.done():
                self.state.running = True
                self.state.note = "Otomasyon zaten çalışıyor."
                return self.state.as_dict()
            self.state.running = True
            self.state.started_at = utc_now()
            self.state.stopped_at = None
            self.state.last_error = None
            self.state.note = "Otomasyon başlatıldı."
            self._task = asyncio.create_task(self._loop(), name="paper_trade_automation_loop")
            return self.state.as_dict()

    async def stop(self) -> dict[str, Any]:
        async with self._lock:
            self.state.running = False
            self.state.stopped_at = utc_now()
            self.state.note = "Otomasyon durduruldu. Yeni cycle başlatılmayacak."
            if self._task and not self._task.done():
                self._task.cancel()
            return self.state.as_dict()

    async def set_interval(self, seconds: int) -> dict[str, Any]:
        async with self._lock:
            normalized = self._normalize_interval(seconds)
            self.state.interval_seconds = normalized
            self.state.note = f"Otomasyon aralığı {normalized} saniye olarak ayarlandı."
            self.services.storage.event(
                "INFO",
                "Otomasyon aralığı güncellendi",
                {"channel": "system", "interval_seconds": normalized},
            )
            return self.status()

    def status(self) -> dict[str, Any]:
        self.state.task_active = bool(self._task and not self._task.done())
        return self.state.as_dict()

    async def run_once(self) -> dict[str, Any]:
        result = await asyncio.to_thread(self.services.cycle)
        self._record_success(result)
        return result

    async def _loop(self) -> None:
        self.state.task_active = True
        try:
            while self.state.running:
                try:
                    result = await self.run_once()
                    self.services.storage.event(
                        "INFO",
                        "Otomatik paper-trade cycle tamamlandı",
                        {"channel": "system", "cycle_count": self.state.cycle_count, "result_keys": list(result.keys())},
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self.state.last_error = str(exc)
                    self.state.note = "Otomatik cycle hata aldı. Sistem çalışmaya devam etmeyi deneyecek."
                    self.services.storage.event(
                        "ERROR",
                        "Otomatik paper-trade cycle hata aldı",
                        {"channel": "error", "error": str(exc)},
                    )
                await asyncio.sleep(self.state.interval_seconds)
        except asyncio.CancelledError:
            self.state.note = "Otomasyon görevi iptal edildi."
        finally:
            self.state.task_active = False

    def _record_success(self, result: dict[str, Any]) -> None:
        self.state.cycle_count += 1
        self.state.last_cycle_at = utc_now()
        self.state.last_error = None
        self.state.note = "Son cycle başarıyla tamamlandı."
        summary = {
            "at": self.state.last_cycle_at,
            "db_rows": result.get("db_rows"),
            "opened_count": len(result.get("opened") or []) if isinstance(result.get("opened"), list) else None,
        }
        self.state.recent_results.append(summary)
        self.state.recent_results = self.state.recent_results[-10:]
