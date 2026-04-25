from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

STATE_PATH = Path("data/rate_limits.json")


@dataclass
class RateLimitState:
    last_call: float = 0.0
    cooldown_until: float = 0.0
    failures: int = 0
    last_error: str | None = None


class RateLimiter:
    def __init__(self, min_interval_seconds: int = 10, state_path: str | Path = STATE_PATH) -> None:
        self.min_interval_seconds = max(10, int(min_interval_seconds))
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.states: dict[str, RateLimitState] = self._load()

    def _load(self) -> dict[str, RateLimitState]:
        if not self.state_path.exists():
            return {}
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            return {key: RateLimitState(**value) for key, value in raw.items()}
        except Exception:
            return {}

    def _save(self) -> None:
        raw = {key: asdict(value) for key, value in self.states.items()}
        self.state_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    def state(self, key: str) -> RateLimitState:
        if key not in self.states:
            self.states[key] = RateLimitState()
        return self.states[key]

    def wait_if_needed(self, key: str) -> float:
        state = self.state(key)
        now = time.time()
        wait_until = max(state.last_call + self.min_interval_seconds, state.cooldown_until)
        delay = max(0.0, wait_until - now)
        if delay > 0:
            time.sleep(delay)
        state.last_call = time.time()
        self._save()
        return delay

    def success(self, key: str) -> None:
        state = self.state(key)
        state.failures = 0
        state.last_error = None
        state.cooldown_until = 0.0
        self._save()

    def failure(self, key: str, error: Exception | str) -> float:
        state = self.state(key)
        state.failures += 1
        state.last_error = str(error)
        cooldown = min(self.min_interval_seconds * (2 ** state.failures), 300)
        state.cooldown_until = time.time() + cooldown
        self._save()
        return cooldown

    def snapshot(self) -> dict[str, Any]:
        return {key: asdict(value) for key, value in self.states.items()}
