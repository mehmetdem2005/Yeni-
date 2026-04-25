from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from crypto_paper_bot.services import AppServices
from crypto_paper_bot.storage import BotStorage

HOST = "127.0.0.1"
PORT = 8765

storage = BotStorage()
services = AppServices(storage)
background_state = {"running": False, "last_cycle_at": None, "last_cycle": None, "last_error": None}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_cycle_safe() -> dict:
    try:
        result = services.cycle()
        background_state["last_cycle_at"] = now()
        background_state["last_cycle"] = result
        background_state["last_error"] = None
        return {"ok": True, "result": result}
    except Exception as exc:
        background_state["last_error"] = str(exc)
        storage.event("ERROR", "Döngü hatası", {"error": str(exc)})
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
    return status


def esc(value) -> str:
    text = "" if value is None else str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def money(value) -> str:
    try:
        return f"{float(value):,.2f} USDT"
    except Exception:
        return "-"


def pct(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "-"


def num(value, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def signal_name(score) -> str:
    if score is None:
        return "Veri yok"
    score = float(score)
    if score >= 0.70:
        return "Güçlü"
    if score >= 0.50:
        return "Orta"
    return "Zayıf"


def chart_svg(points: list[dict], width: int = 760, height: int = 180) -> str:
    if len(points) < 2:
        return "<div class='empty'>Grafik için henüz yeterli veri yok.</div>"
    values = [float(p["equity"]) for p in points]
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1
    coords = []
    for i, value in enumerate(values):
        x = i * (width / max(len(values) - 1, 1))
        y = height - ((value - lo) / (hi - lo)) * (height - 20) - 10
        coords.append(f"{x:.1f},{y:.1f}")
    return f"<svg viewBox='0 0 {width} {height}' class='chart'><polyline points='{' '.join(coords)}' fill='none' stroke='#60a5fa' stroke-width='4'/><text x='8' y='20' fill='#94a3b8'>{money(hi)}</text><text x='8' y='{height-8}' fill='#94a3b8'>{money(lo)}</text></svg>"


def analysis_cards() -> str:
    last = background_state.get("last_cycle") or {}
    analyses = last.get("analyses", []) if isinstance(last, dict) else []
    if not analyses:
        return "<div class='empty'>Henüz analiz yok. Önce 'Sistemi Bir Tur Çalıştır' tuşuna bas.</div>"
    html = []
    for item in analyses:
        risk = item.get("risk_plan", {}) or {}
        decision = item.get("decision", "İZLE")
        cls = "buy" if decision == "SANAL ALIM ADAYI" else "wait"
        html.append(f"""
        <div class='coin-card'>
          <div class='coin-top'><h3>{esc(item.get('symbol'))}</h3><span class='badge {cls}'>{esc(decision)}</span></div>
          <p class='explain'>{esc(item.get('explanation'))}</p>
          <div class='mini-grid'>
            <div><b>Piyasa alış fiyatı</b><span>{num(item.get('bid'), 4)}</span></div>
            <div><b>Piyasa satış fiyatı</b><span>{num(item.get('ask'), 4)}</span></div>
            <div><b>Sinyal gücü</b><span>{signal_name(item.get('score'))}</span></div>
            <div><b>Yapay zekâ tahmini</b><span>{pct(item.get('ml_probability'))}</span></div>
            <div><b>Büyük yön</b><span>{'Olumlu' if item.get('weekly_ok') else 'Zayıf'}</span></div>
            <div><b>Günlük yön</b><span>{'Olumlu' if item.get('daily_ok') else 'Zayıf'}</span></div>
          </div>
          <div class='risk'>Plan: Giriş {num(risk.get('entry'),4)} · Zarar kes {num(risk.get('stop_loss'),4)} · Kâr al {num(risk.get('take_profit'),4)}</div>
        </div>""")
    return "".join(html)


def trades_table() -> str:
    rows = storage.all_positions(30)
    if not rows:
        return "<tr><td colspan='6'>Henüz sanal işlem yok. Sistem uygun fırsat bulunca 250 USDT ile sanal işlem açar.</td></tr>"
    html = []
    for r in rows:
        html.append(f"<tr><td>{esc(r['symbol'])}</td><td>{esc(r['status'])}</td><td>{num(r['entry_price'],4)}</td><td>{num(r.get('close_price'),4)}</td><td>{money(r.get('pnl') or 0)}</td><td>{esc(r.get('reason') or '-')}</td></tr>")
    return "".join(html)


def signals_table() -> str:
    rows = storage.latest_signals(20)
    if not rows:
        return "<tr><td colspan='4'>Henüz sinyal yok.</td></tr>"
    html = []
    for r in rows:
        html.append(f"<tr><td>{esc(r['created_at'])}</td><td>{esc(r['symbol'])}</td><td>{signal_name(r['score'])}</td><td>{esc(r['decision'])}</td></tr>")
    return "".join(html)


def event_feed() -> str:
    rows = storage.latest_events(15)
    if not rows:
        return "<li>Henüz canlı akış yok.</li>"
    return "".join(f"<li><span>{esc(r['created_at'])}</span> {esc(r['message'])}</li>" for r in rows)


def page(message: str = "") -> str:
    status = app_status()
    wallet = status.get("wallet", {})
    stats = status.get("trade_stats", {})
    model = status.get("model") or {}
    metrics = model.get("metrics", {}) if isinstance(model, dict) else {}
    bg = status.get("background", {})
    running = bool(bg.get("running"))
    equity_points = status.get("equity", [])
    last_equity = equity_points[-1]["equity"] if equity_points else wallet.get("cash", 10000)
    pnl = float(last_equity) - float(wallet.get("starting_balance", 10000))
    pnl_pct = pnl / float(wallet.get("starting_balance", 10000)) if wallet else 0
    return f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='refresh' content='20'><title>Kripto Sanal Alım Satım Laboratuvarı</title><style>
    *{{box-sizing:border-box}} body{{margin:0;background:#08111f;color:#e5e7eb;font-family:Arial,sans-serif}} .wrap{{max-width:1180px;margin:0 auto;padding:16px}} .hero,.card{{background:#111827;border:1px solid #334155;border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 14px 34px rgba(0,0,0,.28)}} h1{{font-size:25px;margin:0 0 8px}} h2{{color:#93c5fd;margin:0 0 12px;font-size:20px}} .sub,.muted{{color:#a7b4c8}} .status{{display:inline-block;padding:8px 12px;border-radius:999px;font-weight:800;margin:10px 0}} .on{{background:#064e3b;color:#86efac}} .off{{background:#3f1d1d;color:#fca5a5}} .actions{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-top:14px}} button{{width:100%;padding:14px;border:0;border-radius:14px;background:#2563eb;color:white;font-weight:900;font-size:14px}} .secondary{{background:#334155}} .danger{{background:#dc2626}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}} .metric{{background:#020617;border:1px solid #1f2937;border-radius:16px;padding:14px}} .metric b{{display:block;color:#94a3b8;font-size:13px;margin-bottom:8px}} .metric span{{font-size:22px;font-weight:900}} .profit{{color:#86efac}} .loss{{color:#fca5a5}} .coins{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}} .coin-card{{background:#020617;border:1px solid #263244;border-radius:18px;padding:14px}} .coin-top{{display:flex;justify-content:space-between;gap:8px;align-items:center}} .coin-top h3{{margin:0}} .badge{{border-radius:999px;padding:6px 9px;font-size:12px;font-weight:800}} .buy{{background:#065f46;color:#86efac}} .wait{{background:#334155;color:#e5e7eb}} .explain{{color:#cbd5e1}} .mini-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}} .mini-grid div{{background:#0f172a;border-radius:12px;padding:10px}} .mini-grid b{{display:block;color:#94a3b8;font-size:12px}} .mini-grid span{{font-weight:900}} .risk{{margin-top:10px;color:#cbd5e1;font-size:13px}} table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;border-bottom:1px solid #263244;padding:10px;font-size:13px}} th{{color:#93c5fd}} .chart{{width:100%;height:190px;background:#020617;border-radius:16px;padding:8px}} .msg{{background:#172554;border:1px solid #2563eb;border-radius:12px;padding:10px;margin-top:10px}} .empty{{background:#020617;border-radius:14px;padding:16px;color:#94a3b8}} ul{{margin:0;padding-left:18px}} li{{margin:7px 0;color:#cbd5e1}} li span{{color:#94a3b8;font-size:12px}}
    </style></head><body><div class='wrap'>
    <section class='hero'><h1>Kripto Sanal Alım-Satım Kontrol Merkezi</h1><p class='sub'>Sistem gerçek Binance verisi toplar, yapay zekâ modelini eğitir, 10.000 USDT sanal parayla kâr etmeye çalışır.</p><span class='status {'on' if running else 'off'}'>{'Otomatik çalışıyor' if running else 'Durduruldu'}</span>{f"<div class='msg'>{esc(message)}</div>" if message else ''}<form class='actions' method='post'><button name='action' value='cycle'>Sistemi Bir Tur Çalıştır</button><button name='action' value='start'>Otomatik Çalıştır</button><button class='danger' name='action' value='stop'>Durdur</button><button class='secondary' name='action' value='collect'>Sadece Veri Topla</button><button class='secondary' name='action' value='train'>Sadece Eğit</button><button class='danger' name='action' value='reset'>Sanal Hesabı Sıfırla</button></form></section>
    <section class='card'><h2>Sanal Para Durumu</h2><div class='grid'><div class='metric'><b>Toplam Sanal Para</b><span>{money(last_equity)}</span></div><div class='metric'><b>Nakit</b><span>{money(wallet.get('cash',0))}</span></div><div class='metric'><b>Toplam Kâr/Zarar</b><span class='{'profit' if pnl>=0 else 'loss'}'>{money(pnl)} ({pct(pnl_pct)})</span></div><div class='metric'><b>Kapanan İşlem</b><span>{stats.get('closed_count',0)}</span></div><div class='metric'><b>Başarı Oranı</b><span>{pct(stats.get('win_rate',0))}</span></div><div class='metric'><b>Model Doğruluğu</b><span>{pct(metrics.get('accuracy'))}</span></div></div></section>
    <section class='card'><h2>Kâr Grafiği</h2>{chart_svg(equity_points)}</section>
    <section class='card'><h2>Canlı Akış Açıklaması</h2><ul>{event_feed()}</ul></section>
    <section class='card'><h2>Coin Analizleri</h2><p class='muted'>Büyük yön = haftalık piyasa yönü. Günlük yön = kısa dönem ana yön. Sinyal gücü = sistemin şu anki alım isteği. Yapay zekâ tahmini = modelin olumlu sonuç ihtimali.</p><div class='coins'>{analysis_cards()}</div></section>
    <section class='card'><h2>Sanal İşlem Geçmişi</h2><table><thead><tr><th>Coin</th><th>Durum</th><th>Giriş</th><th>Çıkış</th><th>Kâr/Zarar</th><th>Neden</th></tr></thead><tbody>{trades_table()}</tbody></table></section>
    <section class='card'><h2>Son Kararlar</h2><table><thead><tr><th>Zaman</th><th>Coin</th><th>Sinyal</th><th>Karar</th></tr></thead><tbody>{signals_table()}</tbody></table></section>
    </div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/status":
            self._send(json.dumps(app_status(), ensure_ascii=False), "application/json; charset=utf-8")
        else:
            self._send(page())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        action = data.get("action", [""])[0]
        try:
            if action == "cycle":
                result = run_cycle_safe(); msg = "Bir tur tamamlandı: veri toplandı, eğitim yapıldı, analiz üretildi."
                if not result.get("ok"): msg = f"Hata: {result.get('error')}"
            elif action == "collect":
                r = services.collect_market_data(); msg = f"Veri toplandı: {r.get('rows',0)} mum kaydedildi."
            elif action == "train":
                r = services.train_light_model("BTC/USDT"); msg = f"Eğitim tamamlandı: {r.get('trained_samples',0)} örnek işlendi."
            elif action == "start":
                start_background(); msg = "Otomatik çalışma başlatıldı. Her 60 saniyede bir yeni tur çalışır."
            elif action == "stop":
                stop_background(); msg = "Otomatik çalışma durduruldu."
            elif action == "reset":
                services.reset_account(); msg = "Sanal hesap 10.000 USDT'ye sıfırlandı."
            else:
                msg = "Bilinmeyen işlem."
        except Exception as exc:
            msg = f"Hata: {exc}"
        self._send(page(msg))

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Uygulama açık: http://{HOST}:{PORT}")
    print("Kapatmak için CTRL+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
