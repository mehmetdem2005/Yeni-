from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from crypto_paper_bot.services import AppServices


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    cycle_seconds = max(10, int(os.environ.get("WORKER_CYCLE_SECONDS", "600")))
    services = AppServices()
    print(f"Worker started. cycle_seconds={cycle_seconds}", flush=True)

    while True:
        started = time.time()
        try:
            result = services.cycle()
            print(
                f"{utc_now()} cycle ok: db_rows={result.get('db_rows')} opened={len(result.get('opened', []))}",
                flush=True,
            )
        except Exception as exc:
            print(f"{utc_now()} cycle error: {exc}", flush=True)

        elapsed = time.time() - started
        sleep_for = max(cycle_seconds - elapsed, 10)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
