from __future__ import annotations

import json
import sys

from crypto_paper_bot.services import AppServices


def main() -> int:
    services = AppServices()
    status = services.status()
    required = ["db_rows", "wallet", "trade_stats", "database", "system_confidence"]
    missing = [key for key in required if key not in status]
    if missing:
        print(json.dumps({"ok": False, "missing": missing}, ensure_ascii=False, indent=2))
        return 1

    payload = {
        "ok": True,
        "database": status.get("database"),
        "db_rows": status.get("db_rows"),
        "wallet_cash": (status.get("wallet") or {}).get("cash"),
        "open_count": (status.get("trade_stats") or {}).get("open_count"),
        "system_confidence": (status.get("system_confidence") or {}).get("system_confidence"),
        "worker": status.get("worker"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
