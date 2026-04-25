from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from crypto_paper_bot.config import default_config, load_config
from crypto_paper_bot.filters import OrderBookSnapshot
from crypto_paper_bot.execution import PaperBuyRequest, simulate_aggressive_limit_buy
from crypto_paper_bot.risk import build_risk_plan
from crypto_paper_bot.signals import TimeframeFrames, build_signal, passes_entry_threshold


def _synthetic_frame(rows: int, start: float = 100.0) -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-01", periods=rows, freq="h", tz="UTC")
    values = [start + i * 0.4 for i in range(rows)]
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": values,
            "high": [v + 1.0 for v in values],
            "low": [v - 1.0 for v in values],
            "close": [v + 0.5 for v in values],
            "volume": [1000.0 + i for i in range(rows)],
        }
    )


def demo() -> None:
    cfg = default_config()
    h1 = _synthetic_frame(120)
    d1 = _synthetic_frame(120)
    w1 = _synthetic_frame(120)
    snapshot = build_signal("BTC/USDT", TimeframeFrames(w1=w1, d1=d1, h1=h1), cfg.strategy)
    if snapshot is None:
        print("No signal: gates closed or insufficient data")
        return
    print(f"Signal score: {snapshot.final_score:.3f}")
    if not passes_entry_threshold(snapshot, cfg.strategy):
        print("Below entry threshold")
        return
    risk_plan = build_risk_plan(snapshot, h1, cfg.strategy, cfg.risk)
    if risk_plan is None:
        print("Risk plan rejected")
        return
    print(f"Entry={risk_plan.entry_price:.2f} SL={risk_plan.stop_loss:.2f} TP={risk_plan.take_profit:.2f} Pos={risk_plan.position_pct:.4f}")
    book = OrderBookSnapshot(
        bid=risk_plan.entry_price - 0.05,
        ask=risk_plan.entry_price + 0.05,
        bids=[(risk_plan.entry_price - 0.05, 10.0)],
        asks=[(risk_plan.entry_price + 0.05, 10.0), (risk_plan.entry_price + 0.10, 10.0)],
    )
    result = simulate_aggressive_limit_buy(
        PaperBuyRequest("BTC/USDT", quote_notional=100.0, reference_price=risk_plan.entry_price),
        book,
        cfg.execution,
    )
    print(f"Paper order: {result.status}, fill_ratio={result.fill_ratio:.2f}, avg={result.avg_fill_price}")


def validate_config(path: str) -> None:
    cfg = load_config(path)
    print(cfg.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="crypto-paper-bot")
    sub = parser.add_subparsers(dest="command", required=True)
    demo_parser = sub.add_parser("demo")
    validate = sub.add_parser("validate-config")
    validate.add_argument("path")
    args = parser.parse_args()
    if args.command == "demo":
        demo()
    elif args.command == "validate-config":
        validate_config(args.path)


if __name__ == "__main__":
    main()
