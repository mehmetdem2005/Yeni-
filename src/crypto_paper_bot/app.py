from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from crypto_paper_bot.services import AppServices
from crypto_paper_bot.settings import get_settings
from crypto_paper_bot.storage import BotStorage
from crypto_paper_bot.tabbed_dashboard import DashboardContext, render_dashboard

settings = get_settings()
HOST = settings.host
PORT = settings.port

storage = BotStorage()
services = AppServices(storage)
background_state = {"running": False, "last_cycle_at": None, "last_cycle": None, "last_error": None}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_json_safe(value):
    if is_dataclass(value):
        return make_json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    if hasattr(value, "value") and value.__class__.__module__ == "enum":
        return value.value
    return value


def run_cycle_safe() -> dict:
    try:
        result = services.cycle()
        background_state["last_cycle_at"] = now()
        background_state["last_cycle"] = result
        background_state["last_error"] = None
        return {"ok": True, "result": result}
    except Exception as exc:
        background_state["last_error"] = str(exc)
        storage.event("ERROR", "Döngü hatası", {"channel": "error", "error": str(exc)})
        return {"ok": False, "error": str(exc)}


def loop() -> None:
    while background_state["running"]:
        run_cycle_safe()
        for _ in range(60):
            if not background_state["running"]:
                break
            time.sleep(1)


def start_background() -> None:
    if background_state["running"]:
        return
    background_state["running"] = True
    threading.Thread(target=loop, daemon=True).start()


def stop_background() -> None:
    background_state["running"] = False


def app_status() -> dict:
    status = services.status()
    status["background"] = dict(background_state)
    status["runtime"] = {"env": settings.app_env, "host": HOST, "port": PORT}
    return status


def build_context(active_tab: str = "ana", message: str = "") -> DashboardContext:
    status = app_status()
    last_cycle = background_state.get("last_cycle") or {}
    news = last_cycle.get("news") or {}
    return DashboardContext(
        active_tab=active_tab,
        system_confidence=last_cycle.get("system_confidence") or status.get("system_confidence"),
        wallet=status.get("wallet") or {},
        trade_stats=status.get("trade_stats") or {},
        equity_points=status.get("equity") or [],
        analyses=last_cycle.get("analyses") or [],
        indicator_snapshots=last_cycle.get("indicator_snapshots") or [],
        family_snapshots=last_cycle.get("family_snapshots") or [],
        model_state=status.get("model"),
        risk_plans=last_cycle.get("risk_plans") or [],
        logs=status.get("logs") or [],
        news_items=news.get("items") or [],
        background=status.get("background") or {},
        message=message,
    )


def render_page(active_tab: str = "ana", message: str = "") -> str:
    return render_dashboard(build_context(active_tab=active_tab, message=message))


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        active_tab = query.get("tab", ["ana"])[0]
        if parsed.path == "/api/status":
            self._send(
                json.dumps(make_json_safe(app_status()), ensure_ascii=False),
                "application/json; charset=utf-8",
            )
            return
        self._send(render_page(active_tab=active_tab))

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        action = data.get("action", [""])[0]
        active_tab = data.get("tab", ["ana"])[0]
        try:
            if action == "cycle":
                result = run_cycle_safe()
                message = "Bir tur tamamlandı: veri toplandı, eğitim yapıldı, analiz üretildi."
                if not result.get("ok"):
                    message = f"Hata: {result.get('error')}"
            elif action == "collect":
                result = services.collect_market_data()
                message = f"Veri toplandı: {result.get('rows', 0)} mum kaydedildi."
            elif action == "train":
                result = services.train_light_model("BTC/USDT")
                message = f"Eğitim tamamlandı: {result.get('trained_samples', 0)} örnek işlendi."
            elif action == "news":
                result = services.fetch_news()
                message = f"Haber akışı güncellendi: {len(result.get('items', []))} haber işlendi."
                if background_state.get("last_cycle"):
                    background_state["last_cycle"]["news"] = result
            elif action == "start":
                start_background()
                message = "Otomatik çalışma başlatıldı. Her 60 saniyede bir yeni tur çalışır."
            elif action == "stop":
                stop_background()
                message = "Otomatik çalışma durduruldu."
            elif action == "reset":
                services.reset_account()
                background_state["last_cycle"] = None
                message = "Sanal hesap 10.000 USDT'ye sıfırlandı."
            else:
                message = "Bilinmeyen işlem."
        except Exception as exc:
            message = f"Hata: {exc}"
        self._send(render_page(active_tab=active_tab, message=message))

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Uygulama açık: http://{HOST}:{PORT}")
    print("Kapatmak için CTRL+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
