from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from crypto_paper_bot.config import default_config
from crypto_paper_bot.execution import PaperBuyRequest, simulate_aggressive_limit_buy
from crypto_paper_bot.light_strategy import build_light_signal, risk_plan
from crypto_paper_bot.real_market import BinancePublicClient, display_symbol, normalize_symbol


HOST = "127.0.0.1"
PORT = 8765
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


def analyze_symbol(symbol: str) -> dict:
    cfg = default_config()
    client = BinancePublicClient()
    raw_symbol = normalize_symbol(symbol)
    book = client.order_book(raw_symbol, limit=50)
    h1 = client.klines(raw_symbol, "1h", 200)
    d1 = client.klines(raw_symbol, "1d", 120)
    w1 = client.klines(raw_symbol, "1w", 80)

    h1_signal = build_light_signal(h1)
    d1_signal = build_light_signal(d1)
    w1_signal = build_light_signal(w1)
    w1_gate = w1_signal.ema_signal == 1.0
    d1_gate = d1_signal.ema_signal == 1.0
    entry_ok = w1_gate and d1_gate and h1_signal.final_score >= cfg.strategy.entry_threshold
    plan = risk_plan(h1_signal.close, h1_signal.atr, cfg.risk.account_risk_per_trade)

    paper = None
    if plan.get("ok"):
        paper_result = simulate_aggressive_limit_buy(
            PaperBuyRequest(
                display_symbol(raw_symbol),
                quote_notional=100.0,
                reference_price=float(plan["entry"]),
            ),
            book,
            cfg.execution,
        )
        paper = {
            "status": paper_result.status,
            "fill_ratio": paper_result.fill_ratio,
            "avg_fill_price": paper_result.avg_fill_price,
            "maker_taker": paper_result.maker_taker,
            "fee_paid": paper_result.fee_paid,
            "slippage_pct": paper_result.slippage_pct,
        }

    return {
        "symbol": display_symbol(raw_symbol),
        "mode": "real_binance_public_data_paper_trade",
        "server": client.server_time().isoformat(),
        "market": {
            "bid": book.bid,
            "ask": book.ask,
            "mid": book.mid,
            "spread_pct": book.spread_pct,
            "top_ask_notional": book.asks[0][0] * book.asks[0][1],
        },
        "gates": {
            "w1_gate": w1_gate,
            "d1_gate": d1_gate,
            "entry_ok": entry_ok,
        },
        "signals": {
            "h1_score": h1_signal.final_score,
            "h1_ema": h1_signal.ema_signal,
            "h1_rsi": h1_signal.rsi_signal,
            "h1_volume": h1_signal.volume_signal,
            "h1_atr": h1_signal.atr,
            "h1_close": h1_signal.close,
            "h1_reason": h1_signal.reason,
            "d1_score": d1_signal.final_score,
            "w1_score": w1_signal.final_score,
        },
        "risk_plan": plan,
        "paper_order_preview": paper,
        "decision": "PAPER_BUY_CANDIDATE" if entry_ok and plan.get("ok") else "SKIP",
    }


def dashboard_payload(symbol: str) -> dict:
    analyses = []
    errors = []
    for item in [symbol] + [s for s in DEFAULT_SYMBOLS if normalize_symbol(s) != normalize_symbol(symbol)]:
        try:
            analyses.append(analyze_symbol(item))
        except Exception as exc:
            errors.append({"symbol": item, "error": str(exc)})
    return {"status": "ok" if analyses else "error", "analyses": analyses, "errors": errors}


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def html_page(symbol: str) -> str:
    payload = dashboard_payload(symbol)
    pretty = json.dumps(payload, indent=2, ensure_ascii=False)
    cards = []
    for item in payload.get("analyses", []):
        risk = item["risk_plan"]
        paper = item.get("paper_order_preview") or {}
        cards.append(
            f"""
    <div class='card'>
      <h2>{item['symbol']} <span class='badge'>{item['decision']}</span></h2>
      <div class='grid'>
        <div class='metric'><b>Bid</b><span>{item['market']['bid']}</span></div>
        <div class='metric'><b>Ask</b><span>{item['market']['ask']}</span></div>
        <div class='metric'><b>Spread</b><span>{_fmt_pct(item['market']['spread_pct'])}</span></div>
        <div class='metric'><b>H1 Score</b><span>{item['signals']['h1_score']:.3f}</span></div>
        <div class='metric'><b>W1 Gate</b><span>{item['gates']['w1_gate']}</span></div>
        <div class='metric'><b>D1 Gate</b><span>{item['gates']['d1_gate']}</span></div>
        <div class='metric'><b>ATR</b><span>{item['signals']['h1_atr']:.4f}</span></div>
        <div class='metric'><b>Paper Fill</b><span>{paper.get('fill_ratio', 'n/a')}</span></div>
      </div>
      <pre>{json.dumps({'risk_plan': risk, 'paper': paper, 'signals': item['signals']}, indent=2, ensure_ascii=False)}</pre>
    </div>"""
        )
    cards_html = "\n".join(cards)
    return f"""<!doctype html>
<html lang='tr'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <meta http-equiv='refresh' content='30'>
  <title>Crypto Paper Bot Pro</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#0f172a; color:#e5e7eb; margin:0; padding:20px; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; }}
    .card {{ background:#111827; border:1px solid #334155; border-radius:16px; padding:18px; margin:14px 0; box-shadow:0 12px 28px rgba(0,0,0,.25); }}
    h1 {{ margin-top:0; font-size:26px; }}
    h2 {{ font-size:18px; color:#93c5fd; }}
    .ok {{ color:#22c55e; font-weight:bold; }}
    .warn {{ color:#fbbf24; font-weight:bold; }}
    .badge {{ font-size:12px; color:#0f172a; background:#93c5fd; border-radius:999px; padding:4px 8px; margin-left:8px; }}
    pre {{ background:#020617; color:#d1d5db; border-radius:12px; padding:12px; overflow:auto; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
    .metric {{ background:#020617; border-radius:12px; padding:12px; }}
    .metric b {{ display:block; font-size:13px; color:#94a3b8; }}
    .metric span {{ font-size:18px; }}
    input {{ padding:10px; border-radius:10px; border:1px solid #334155; background:#020617; color:#e5e7eb; }}
    button {{ padding:10px 14px; border-radius:10px; border:0; background:#2563eb; color:white; font-weight:bold; }}
    a {{ color:#60a5fa; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <div class='card'>
      <h1>Crypto Spot Bot — Professional Paper Dashboard</h1>
      <p class='ok'>Gerçek Binance public market data ile çalışıyor. Mock fiyat yok.</p>
      <p class='warn'>Bu hâlâ paper-trade modudur; gerçek para emri göndermez.</p>
      <form method='get'>
        <input name='symbol' value='{display_symbol(symbol)}' placeholder='BTCUSDT'>
        <button type='submit'>Analiz Et</button>
      </form>
      <p>Otomatik yenileme: 30 saniye. API: <a href='/api/status?symbol={normalize_symbol(symbol)}'>/api/status</a></p>
    </div>
    {cards_html}
    <div class='card'>
      <h2>Raw JSON</h2>
      <pre>{pretty}</pre>
    </div>
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
        query = parse_qs(parsed.query)
        symbol = query.get("symbol", ["BTCUSDT"])[0]
        if parsed.path == "/api/status":
            self._send(json.dumps(dashboard_payload(symbol), ensure_ascii=False), "application/json; charset=utf-8")
            return
        self._send(html_page(symbol))

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Crypto Paper Bot web app running: http://{HOST}:{PORT}")
    print("Press CTRL+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
