from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    name: str
    config_hash: str
    metrics: dict[str, Any]
    artifacts: dict[str, str]
    notes: str = ""


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class LocalRunLogger:
    """Small local experiment logger.

    This is intentionally simple. It can later be replaced by MLflow without changing
    training code too much.
    """

    def __init__(self, root: str | Path = "outputs/runs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def log_run(
        self,
        name: str,
        config: dict[str, Any],
        metrics: dict[str, Any],
        artifacts: dict[str, str] | None = None,
        notes: str = "",
    ) -> RunRecord:
        created_at = datetime.now(timezone.utc).isoformat()
        config_hash = stable_hash(config)
        run_id = f"{created_at.replace(':', '').replace('.', '')}-{config_hash}"
        record = RunRecord(
            run_id=run_id,
            created_at=created_at,
            name=name,
            config_hash=config_hash,
            metrics=metrics,
            artifacts=artifacts or {},
            notes=notes,
        )
        path = self.root / f"{run_id}.json"
        path.write_text(json.dumps(asdict(record), indent=2, ensure_ascii=False), encoding="utf-8")
        return record
