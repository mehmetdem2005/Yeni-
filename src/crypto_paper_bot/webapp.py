from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from crypto_paper_bot.book import OrderBookSnapshot
from crypto_paper_bot.config import default_config
from crypto_paper_bot.execution import PaperBuyRequest, simulate_aggressive_limit_buy


HOST = "127.0.0.1"
PORT = 8765


def run_smoke_payload() -> dict:
    cfg = default_config()
    book = OrderBookSnapshot(
        bid=99.9,
        ask=100.0,
        bids=[(99.9, 10.0)],
        asks=[(100.0, 2.0), (100.1, 2.0)],
    )
    result = simulate_aggressive_limit_buy(
        PaperBuyRequest("BTC/USDT", quote_notional=100.0, reference_price=100.0),
        book,
        cfg.execution,
    )
    return {
        "status": "ok",
        "mode": "termux_light_web_app",
        "paper_order": {
            "symbol": result.symbol,
            "status": result.status,
            "fill_ratio": result.fill_ratio,
            "avg_fill_price": result.avg_fill_price,
            "maker_taker": result.maker_taker,
            "fee_paid": result.fee_paid,
            "slippage_pct": result.slippage_pct,
        },
        "config": {
            "entry_threshold": cfg.strategy.entry_threshold,
            "account_risk_per_trade": cfg.risk.account_risk_per_trade,
            "max_position_pct": cfg.risk.max_position_pct,
            "max_open_positions": cfg.risk.max_open_positions,
        },
    }


def html_page() -> str:
    payload = run_smoke_payload()
    pretty = json.dumps(payload, indent=2, ensure_ascii=False)
    return f"""<!doctype html>
<html lang='tr'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Crypto Paper Bot</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#0f172a; color:#e5e7eb; margin:0; padding:20px; }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    .card {{ background:#111827; border:1px solid #334155; border-radius:16px; padding:18px; margin:14px 0; }}
    h1 {{ margin-top:0; font-size:26px; }}
    h2 {{ font-size:18px; color:#93c5fd; }}
    .ok {{ color:#22c55e; font-weight:bold; }}
    .warn {{ color:#fbbf24; font-weight:bold; }}
    code, pre {{ background:#020617; color:#d1d5db; border-radius:12px; padding:12px; overflow:auto; display:block; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
    .metric {{ background:#020617; border-radius:12px; padding:12px; }}
    .metric b {{ display:block; font-size:13px; color:#94a3b8; }}
    .metric span {{ font-size:20px; }}
    a {{ color:#60a5fa; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <div class='card'>
      <h1>Crypto Spot Bot — Paper Trade Dashboard</h1>
      <p class='ok'>Çekirdek uygulama çalışıyor.</p>
      <p class='warn'>Bu panel Termux-light modudur. Gerçek veri, ML eğitim ve ağır pandas/scikit katmanları telefonda kapalıdır.</p>
    </div>

    <div class='card'>
      <h2>Paper Order Smoke</h2>
      <div class='grid'>
        <div class='metric'><b>Status</b><span>{payload['paper_order']['status']}</span></div>
        <div class='metric'><b>Fill Ratio</b><span>{payload['paper_order']['fill_ratio']:.2f}</span></div>
        <div class='metric'><b>Avg Price</b><span>{payload['paper_order']['avg_fill_price']}</span></div>
        <div class='metric'><b>Maker/Taker</b><span>{payload['paper_order']['maker_taker']}</span></div>
      </div>
    </div>

    <div class='card'>
      <h2>Risk Config</h2>
      <div class='grid'>
        <div class='metric'><b>Entry Threshold</b><span>{payload['config']['entry_threshold']}</span></div>
        <div class='metric'><b>Risk / Trade</b><span>{payload['config']['account_risk_per_trade']}</span></div>
        <div class='metric'><b>Max Position</b><span>{payload['config']['max_position_pct']}</span></div>
        <div class='metric'><b>Max Open</b><span>{payload['config']['max_open_positions']}</span></div>
      </div>
    </div>

    <div class='card'>
      <h2>Raw JSON</h2>
      <pre>{pretty}</pre>
      <p>API: <a href='/api/status'>/api/status</a></p>
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
        path = urlparse(self.path).path
        if path == "/api/status":
            self._send(json.dumps(run_smoke_payload(), ensure_ascii=False), "application/json; charset=utf-8")
            return
        self._send(html_page())

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Crypto Paper Bot web app running: http://{HOST}:{PORT}")
    print("Press CTRL+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
