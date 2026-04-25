from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from crypto_paper_bot.services import AppServices, SYMBOLS
from crypto_paper_bot.storage import BotStorage

HOST = "127.0.0.1"
PORT = 8765

storage = BotStorage()
services = AppServices(storage)
background_state = {
    "running": False,
    "last_cycle_at": None,
    "last_cycle": None,
    "last_error": None,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_cycle_safe() -> dict:
    try:
        result = services.cycle()
        background_state["last_cycle_at"] = utc_now()
        background_state["last_cycle"] = result
        background_state["last_error"] = None
        return {"ok": True, "result": result}
    except Exception as exc:
        background_state["last_error"] = str(exc)
        storage.event("ERROR", "cycle_failed", {"error": str(exc)})
        return {"ok": False, "error": str(exc)}


def background_loop() -> None:
    while background_state["running"]:
        run_cycle_safe()
        for _ in range(60):
            if not background_state["running"]:
                break
            time.sleep(1)


def start_background() -> dict:
    if background_state["running"]:
        return {"ok": True, "message": "already_running"}
    background_state["running"] = True
    thread = threading.Thread(target=background_loop, daemon=True)
    thread.start()
    return {"ok": True, "message": "started"}


def stop_background() -> dict:
    background_state["running"] = False
    return {"ok": True, "message": "stopped"}


def app_status() -> dict:
    status = services.status()
    status["background"] = dict(background_state)
    return status


def esc(value) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt(value, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def signal_rows() -> str:
    rows = storage.latest_signals(30)
    if not rows:
        return "<tr><td colspan='5'>Henüz sinyal yok. Önce 'Veri Topla + Eğit + Analiz Et' tuşuna bas.</td></tr>"
    html = []
    for row in rows:
        html.append(
            "<tr>"
            f"<td>{esc(row['created_at'])}</td>"
            f"<td>{esc(row['symbol'])}</td>"
            f"<td>{fmt(row['score'], 3)}</td>"
            f"<td>{fmt(row['ml_probability'], 3)}</td>"
            f"<td><span class='pill'>{esc(row['decision'])}</span></td>"
            "</tr>"
        )
    return "".join(html)


def event_rows() -> str:
    rows = storage.latest_events(12)
    if not rows:
        return "<li>Henüz olay kaydı yok.</li>"
    return "".join(f"<li><b>{esc(row['level'])}</b> — {esc(row['message'])}</li>" for row in rows)


def analyses_cards() -> str:
    last = background_state.get("last_cycle") or {}
    analyses = last.get("analyses", []) if isinstance(last, dict) else []
    if not analyses:
        return "<div class='empty'>Henüz analiz yok. Büyük mavi tuşa bas.</div>"
    cards = []
    for item in analyses:
        decision = item.get("decision", "-")
        cls = "good" if decision == "PAPER_CANDIDATE" else "neutral"
        risk = item.get("risk_plan", {}) or {}
        cards.append(
            f"""
            <div class='coin-card'>
              <div class='coin-head'>
                <h3>{esc(item.get('symbol'))}</h3>
                <span class='badge {cls}'>{esc(decision)}</span>
              </div>
              <div class='mini-grid'>
                <div><b>Bid</b><span>{fmt(item.get('bid'), 4)}</span></div>
                <div><b>Ask</b><span>{fmt(item.get('ask'), 4)}</span></div>
                <div><b>Skor</b><span>{fmt(item.get('score'), 3)}</span></div>
                <div><b>ML</b><span>{fmt(item.get('ml_probability'), 3)}</span></div>
                <div><b>W1</b><span>{esc(item.get('w1_gate'))}</span></div>
                <div><b>D1</b><span>{esc(item.get('d1_gate'))}</span></div>
              </div>
              <div class='risk-line'>SL: {fmt(risk.get('stop_loss'), 4)} · TP: {fmt(risk.get('take_profit'), 4)} · Pozisyon: {fmt(risk.get('position_pct'), 4)}</div>
            </div>
            """
        )
    return "".join(cards)


def page(message: str = "") -> str:
    status = app_status()
    model = status.get("model") or {}
    model_metrics = model.get("metrics", {}) if isinstance(model, dict) else {}
    bg = status.get("background", {})
    running = bg.get("running", False)
    return f"""<!doctype html>
<html lang='tr'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <meta http-equiv='refresh' content='20'>
  <title>Crypto Paper Bot Pro</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Arial, sans-serif; background:#09111f; color:#e5e7eb; }}
    .wrap {{ max-width:1180px; margin:0 auto; padding:18px; }}
    .hero {{ background:linear-gradient(135deg,#16233f,#0f172a); border:1px solid #334155; border-radius:22px; padding:22px; box-shadow:0 18px 40px rgba(0,0,0,.28); }}
    h1 {{ margin:0 0 8px; font-size:27px; }}
    h2 {{ margin:0 0 14px; font-size:19px; color:#93c5fd; }}
    .sub {{ color:#a7b4c8; margin:0; }}
    .status {{ display:inline-block; padding:7px 11px; border-radius:999px; font-weight:700; margin-top:12px; }}
    .on {{ background:#064e3b; color:#86efac; }}
    .off {{ background:#3f1d1d; color:#fca5a5; }}
    .actions {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin:16px 0; }}
    button {{ width:100%; padding:13px 14px; border:0; border-radius:14px; background:#2563eb; color:white; font-weight:800; font-size:14px; }}
    button.secondary {{ background:#334155; }}
    button.danger {{ background:#dc2626; }}
    .card {{ background:#111827; border:1px solid #334155; border-radius:18px; padding:17px; margin:14px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }}
    .metric {{ background:#020617; border:1px solid #1f2937; border-radius:14px; padding:13px; }}
    .metric b {{ display:block; color:#94a3b8; font-size:13px; margin-bottom:6px; }}
    .metric span {{ font-size:20px; font-weight:800; }}
    .coins {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; }}
    .coin-card {{ background:#020617; border:1px solid #263244; border-radius:16px; padding:14px; }}
    .coin-head {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
    .coin-head h3 {{ margin:0; }}
    .badge,.pill {{ display:inline-block; padding:5px 9px; border-radius:999px; font-size:12px; background:#334155; color:#e5e7eb; }}
    .good {{ background:#065f46; color:#86efac; }}
    .neutral {{ background:#334155; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-top:12px; }}
    .mini-grid div {{ background:#0f172a; border-radius:12px; padding:9px; }}
    .mini-grid b {{ display:block; color:#94a3b8; font-size:12px; }}
    .mini-grid span {{ font-weight:800; }}
    .risk-line {{ color:#cbd5e1; font-size:13px; margin-top:10px; }}
    table {{ width:100%; border-collapse:collapse; overflow:hidden; border-radius:12px; }}
    th,td {{ text-align:left; padding:10px; border-bottom:1px solid #263244; font-size:13px; }}
    th {{ color:#93c5fd; }}
    .msg {{ background:#172554; border:1px solid #2563eb; color:#dbeafe; padding:10px 12px; border-radius:12px; margin-top:12px; }}
    .empty {{ color:#94a3b8; background:#020617; border-radius:14px; padding:18px; }}
    ul {{ margin:0; padding-left:18px; color:#cbd5e1; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <section class='hero'>
      <h1>Crypto Spot Bot — Professional Paper Lab</h1>
      <p class='sub'>Gerçek Binance public veri toplama, SQLite kayıt, hafif ML eğitimi ve paper-trade aday analizi.</p>
      <span class='status {'on' if running else 'off'}'>{'OTOMATİK ÇALIŞIYOR' if running else 'DURDU'}</span>
      {f"<div class='msg'>{esc(message)}</div>" if message else ""}
      <form class='actions' method='post'>
        <button name='action' value='cycle'>Veri Topla + Eğit + Analiz Et</button>
        <button name='action' value='start'>Otomatik Başlat</button>
        <button class='danger' name='action' value='stop'>Durdur</button>
        <button class='secondary' name='action' value='collect'>Sadece Veri Topla</button>
        <button class='secondary' name='action' value='train'>Sadece Eğit</button>
      </form>
    </section>

    <section class='card'>
      <h2>Durum</h2>
      <div class='grid'>
        <div class='metric'><b>Toplanan Mum</b><span>{status.get('db_rows', 0)}</span></div>
        <div class='metric'><b>Model Örneği</b><span>{model.get('trained_samples', 0) if isinstance(model, dict) else 0}</span></div>
        <div class='metric'><b>Model Doğruluk</b><span>{fmt(model_metrics.get('accuracy'), 3)}</span></div>
        <div class='metric'><b>Son Döngü</b><span>{esc(bg.get('last_cycle_at') or '-')}</span></div>
      </div>
    </section>

    <section class='card'>
      <h2>Canlı Analizler</h2>
      <div class='coins'>{analyses_cards()}</div>
    </section>

    <section class='card'>
      <h2>Son Sinyaller</h2>
      <table>
        <thead><tr><th>Zaman</th><th>Coin</th><th>Skor</th><th>ML</th><th>Karar</th></tr></thead>
        <tbody>{signal_rows()}</tbody>
      </table>
    </section>

    <section class='card'>
      <h2>Sistem Olayları</h2>
      <ul>{event_rows()}</ul>
    </section>
  </div>
</body>
</html>"""


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
        if parsed.path == "/api/status":
            self._send(json.dumps(app_status(), ensure_ascii=False), "application/json; charset=utf-8")
            return
        self._send(page())

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        action = data.get("action", [""])[0]
        msg = "İşlem tamamlandı."
        try:
            if action == "cycle":
                result = run_cycle_safe()
                msg = "Veri toplandı, model eğitildi, analiz üretildi." if result.get("ok") else result.get("error", "Hata")
            elif action == "collect":
                result = services.collect_market_data()
                msg = f"Veri toplandı: {result.get('rows', 0)} mum."
            elif action == "train":
                result = services.train_light_model("BTC/USDT")
                msg = f"Eğitim tamamlandı: {result.get('trained_samples', 0)} örnek."
            elif action == "start":
                start_background()
                msg = "Otomatik döngü başlatıldı."
            elif action == "stop":
                stop_background()
                msg = "Otomatik döngü durduruldu."
        except Exception as exc:
            msg = f"Hata: {exc}"
        self._send(page(msg))

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Crypto Paper Bot app running: http://{HOST}:{PORT}")
    print("Press CTRL+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
