from __future__ import annotations

import signal
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from crypto_paper_bot.services import AppServices
from crypto_paper_bot.settings import get_settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class WorkerRuntime:
    running: bool = True
    cycle_count: int = 0
    last_error: str | None = None


class PaperTradeWorker:
    """Standalone worker process for Render/Cron style deployments.

    The FastAPI web panel can still run manual actions, but production automation should
    run in this separate worker process so the trading loop is not tied to web requests.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.interval_seconds = max(10, int(self.settings.min_api_interval_seconds))
        self.services = AppServices()
        self.runtime = WorkerRuntime()

    def install_signal_handlers(self) -> None:
        def stop_handler(signum: int, _frame: object) -> None:
            self.runtime.running = False
            self.services.storage.event(
                "WARNING",
                "Worker durdurma sinyali aldı",
                {"channel": "system", "signal": signum},
            )

        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)

    def run_forever(self) -> None:
        self.install_signal_handlers()
        self.services.storage.event(
            "INFO",
            "Paper-trade worker başlatıldı",
            {"channel": "system", "interval_seconds": self.interval_seconds, "app_env": self.settings.app_env},
        )
        print(f"[{utc_now()}] worker started interval={self.interval_seconds}s env={self.settings.app_env}", flush=True)

        while self.runtime.running:
            started = time.monotonic()
            try:
                result = self.services.cycle()
                self.runtime.cycle_count += 1
                self.runtime.last_error = None
                self.services.storage.event(
                    "INFO",
                    "Worker cycle tamamlandı",
                    {
                        "channel": "system",
                        "cycle_count": self.runtime.cycle_count,
                        "db_rows": result.get("db_rows"),
                        "opened_count": len(result.get("opened") or []) if isinstance(result.get("opened"), list) else None,
                    },
                )
                print(f"[{utc_now()}] cycle ok count={self.runtime.cycle_count} db_rows={result.get('db_rows')}", flush=True)
            except Exception as exc:
                self.runtime.last_error = str(exc)
                self.services.storage.event(
                    "ERROR",
                    "Worker cycle hata aldı",
                    {"channel": "error", "error": str(exc), "cycle_count": self.runtime.cycle_count},
                )
                print(f"[{utc_now()}] cycle error: {exc}", flush=True)

            elapsed = time.monotonic() - started
            sleep_for = max(1.0, self.interval_seconds - elapsed)
            end_sleep = time.monotonic() + sleep_for
            while self.runtime.running and time.monotonic() < end_sleep:
                time.sleep(min(1.0, end_sleep - time.monotonic()))

        self.services.storage.event(
            "WARNING",
            "Paper-trade worker durdu",
            {"channel": "system", "cycle_count": self.runtime.cycle_count},
        )
        print(f"[{utc_now()}] worker stopped count={self.runtime.cycle_count}", flush=True)


def main() -> None:
    PaperTradeWorker().run_forever()


if __name__ == "__main__":
    main()
