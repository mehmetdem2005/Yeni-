from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crypto_paper_bot.automation_controller import AutomationController
from crypto_paper_bot.llm_router import GroqLLMRouter, llm_response_as_plain_dict, simple_assistant_prompt
from crypto_paper_bot.real_market import display_symbol
from crypto_paper_bot.services import AppServices
from crypto_paper_bot.settings import get_settings

settings = get_settings()
services = AppServices()
llm_router = GroqLLMRouter()
automation = AutomationController(services, interval_seconds=max(10, settings.min_api_interval_seconds))

app = FastAPI(title="Crypto Paper Bot API", version="0.3.0", description="Cloud-first API for the V3 crypto paper-trade control center.")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


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


def _safe_storage_list(method_name: str, symbol: str, limit: int) -> list[dict[str, Any]]:
    method = getattr(services.storage, method_name, None)
    if method is None:
        return []
    try:
        return list(method(symbol, limit))
    except Exception as exc:
        services.storage.event("ERROR", "Grafik olay verisi okunamadı", {"channel": "error", "method": method_name, "symbol": symbol, "error": str(exc)})
        return []


def _news_marker_color(news: dict[str, Any]) -> str:
    sentiment = str(news.get("sentiment") or "").lower()
    score = float(news.get("sentiment_score") or 0)
    if "neg" in sentiment or score < -0.15:
        return "#dc2626"
    if "pos" in sentiment or score > 0.15:
        return "#16a34a"
    return "#2563eb"


def _whale_marker_color(event: dict[str, Any]) -> str:
    side = str(event.get("side") or "").lower()
    if side == "sell":
        return "#dc2626"
    if side == "buy":
        return "#16a34a"
    return "#0f766e"


def chart_overlays(symbol: str) -> dict[str, Any]:
    markers: list[dict[str, Any]] = []
    price_lines: list[dict[str, Any]] = []
    for position in services.storage.all_positions(250):
        if position.get("symbol") != symbol:
            continue
        opened_at = position.get("opened_at")
        closed_at = position.get("closed_at")
        status = position.get("status")
        if opened_at:
            markers.append({"kind": "trade", "time": opened_at, "position": "belowBar", "shape": "arrowUp", "text": "AL", "color": "#16a34a", "price": position.get("entry_price")})
        if closed_at:
            pnl = float(position.get("pnl") or 0)
            markers.append({"kind": "trade", "time": closed_at, "position": "aboveBar" if pnl >= 0 else "belowBar", "shape": "arrowDown" if pnl >= 0 else "circle", "text": "KÂR" if pnl >= 0 else "ZARAR", "color": "#16a34a" if pnl >= 0 else "#dc2626", "price": position.get("close_price")})
        if status == "OPEN":
            price_lines.append({"price": position.get("stop_loss"), "title": "SL", "color": "#dc2626", "lineStyle": "dashed"})
            price_lines.append({"price": position.get("take_profit"), "title": "TP", "color": "#16a34a", "lineStyle": "dashed"})
            price_lines.append({"price": position.get("entry_price"), "title": "Giriş", "color": "#2563eb", "lineStyle": "solid"})
    for news in _safe_storage_list("latest_news_items", symbol, 80):
        marker_time = news.get("published_at") or news.get("created_at")
        if not marker_time:
            continue
        impact = float(news.get("impact_score") or 0)
        markers.append({"kind": "news", "time": marker_time, "position": "aboveBar" if impact >= 0 else "belowBar", "shape": "square", "text": "HABER", "color": _news_marker_color(news), "title": news.get("title"), "impact_score": news.get("impact_score"), "sentiment": news.get("sentiment")})
    for event in _safe_storage_list("latest_whale_events", symbol, 80):
        marker_time = event.get("created_at")
        if not marker_time:
            continue
        markers.append({"kind": "whale", "time": marker_time, "position": "aboveBar" if str(event.get("side") or "").lower() == "sell" else "belowBar", "shape": "circle", "text": "BALİNA", "color": _whale_marker_color(event), "price": event.get("price"), "event_type": event.get("event_type"), "score": event.get("score"), "notional": event.get("notional")})
    counts = {"trade": len([m for m in markers if m.get("kind") == "trade"]), "news": len([m for m in markers if m.get("kind") == "news"]), "whale": len([m for m in markers if m.get("kind") == "whale"])}
    return {"markers": markers, "price_lines": price_lines, "counts": counts}


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "env": settings.app_env}


@app.get("/api/status")
def status() -> dict[str, Any]:
    data = services.status()
    data["automation"] = automation.status()
    return json_safe(data)


@app.post("/api/cycle")
async def cycle() -> dict[str, Any]:
    return json_safe(await automation.run_once())


@app.post("/api/collect")
def collect() -> dict[str, Any]:
    return json_safe(services.collect_market_data())


@app.post("/api/train")
def train() -> dict[str, Any]:
    return json_safe(services.train_light_model("BTC/USDT"))


@app.post("/api/control/start")
async def control_start() -> dict[str, Any]:
    services.storage.event("INFO", "Otomasyon başlatma komutu alındı", {"channel": "system"})
    return json_safe(await automation.start())


@app.post("/api/control/stop")
async def control_stop() -> dict[str, Any]:
    services.storage.event("INFO", "Otomasyon durdurma komutu alındı", {"channel": "system"})
    return json_safe(await automation.stop())


@app.get("/api/control/status")
def control_status() -> dict[str, Any]:
    return json_safe(automation.status())


@app.post("/api/emergency/close-all")
async def emergency_close_all() -> dict[str, Any]:
    services.storage.event("WARNING", "Acil kapatma komutu alındı", {"channel": "risk"})
    await automation.stop()
    return json_safe(services.emergency_close_all())


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
            services.storage.event("ERROR", "Grafik canlı mum verisiyle doldurulamadı", {"channel": "error", "symbol": normalized_symbol, "timeframe": timeframe, "error": str(exc)})
    return {"symbol": normalized_symbol, "timeframe": timeframe, "candles": json_safe(candles), "live_filled": live_filled, "overlays": json_safe(chart_overlays(normalized_symbol))}


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
    return {"runtime": {"app_env": settings.app_env, "min_api_interval_seconds": settings.min_api_interval_seconds, "groq_key_present": bool(settings.groq_api_key), "supabase_url_present": bool(settings.supabase_url), "supabase_service_key_present": bool(settings.supabase_service_key), "database_url_present": bool(settings.database_url)}, "database": status_data.get("database"), "automation": automation.status()}
