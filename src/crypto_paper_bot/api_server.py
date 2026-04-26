from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crypto_paper_bot.llm_router import GroqLLMRouter, llm_response_as_plain_dict, simple_assistant_prompt
from crypto_paper_bot.real_market import display_symbol
from crypto_paper_bot.services import AppServices
from crypto_paper_bot.settings import get_settings

settings = get_settings()
services = AppServices()
llm_router = GroqLLMRouter()

app = FastAPI(
    title="Crypto Paper Bot API",
    version="0.3.0",
    description="Cloud-first API for the V3 crypto paper-trade control center.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if hasattr(value, "value"):
        return value.value
    return value


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "env": settings.app_env}


@app.get("/api/status")
def status() -> dict[str, Any]:
    return json_safe(services.status())


@app.post("/api/cycle")
def cycle() -> dict[str, Any]:
    return json_safe(services.cycle())


@app.post("/api/collect")
def collect() -> dict[str, Any]:
    return json_safe(services.collect_market_data())


@app.post("/api/train")
def train() -> dict[str, Any]:
    return json_safe(services.train_light_model("BTC/USDT"))


@app.post("/api/news/refresh")
def refresh_news() -> dict[str, Any]:
    return json_safe(services.fetch_news())


@app.post("/api/reset-paper-account")
def reset_paper_account() -> dict[str, Any]:
    services.reset_account()
    return {"ok": True, "message": "Paper account reset."}


@app.get("/api/chart/{symbol}/{timeframe}")
def chart_data(symbol: str, timeframe: str, limit: int = 300) -> dict[str, Any]:
    if limit < 1 or limit > 2000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 2000")
    normalized_symbol = display_symbol(symbol)
    candles = services.storage.get_candles(normalized_symbol, timeframe, limit)
    live_filled = False
    if not candles:
        try:
            live_candles = services.market.klines(normalized_symbol, timeframe, limit)
            services.storage.upsert_candles(normalized_symbol, timeframe, live_candles)
            candles = services.storage.get_candles(normalized_symbol, timeframe, limit)
            live_filled = True
        except Exception as exc:
            services.storage.event(
                "ERROR",
                "Grafik canlı mum verisiyle doldurulamadı",
                {"channel": "error", "symbol": normalized_symbol, "timeframe": timeframe, "error": str(exc)},
            )
    return {"symbol": normalized_symbol, "timeframe": timeframe, "candles": json_safe(candles), "live_filled": live_filled}


@app.post("/api/assistant/ask")
def assistant_ask(request: AssistantRequest) -> dict[str, Any]:
    context = request.context or services.status()
    response = llm_router.complete(simple_assistant_prompt(request.question, json_safe(context)))
    for log in response.logs:
        services.storage.event(log.level.value, log.message, log.to_event_payload())
    return llm_response_as_plain_dict(response)


@app.get("/api/settings/runtime")
def runtime_settings() -> dict[str, Any]:
    status_data = services.status()
    return {
        "runtime": {
            "app_env": settings.app_env,
            "min_api_interval_seconds": settings.min_api_interval_seconds,
            "groq_key_present": bool(settings.groq_api_key),
            "supabase_url_present": bool(settings.supabase_url),
            "supabase_service_key_present": bool(settings.supabase_service_key),
            "database_url_present": bool(settings.database_url),
        },
        "database": status_data.get("database"),
    }
