from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeSettings:
    app_env: str
    host: str
    port: int
    database_url: str | None
    supabase_url: str | None
    supabase_service_key: str | None
    groq_api_key: str | None
    min_api_interval_seconds: int

    @property
    def is_cloud(self) -> bool:
        return self.app_env.lower() in {"render", "cloud", "production", "prod"}


def get_settings() -> RuntimeSettings:
    app_env = os.environ.get("APP_ENV", "local")
    default_host = "0.0.0.0" if app_env.lower() in {"render", "cloud", "production", "prod"} else "127.0.0.1"
    return RuntimeSettings(
        app_env=app_env,
        host=os.environ.get("HOST", default_host),
        port=int(os.environ.get("PORT", "8765")),
        database_url=os.environ.get("DATABASE_URL"),
        supabase_url=os.environ.get("SUPABASE_URL"),
        supabase_service_key=os.environ.get("SUPABASE_SERVICE_KEY"),
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        min_api_interval_seconds=max(10, int(os.environ.get("MIN_API_INTERVAL_SECONDS", "10"))),
    )
