from crypto_paper_bot.config import default_config
from crypto_paper_bot.execution import PaperBuyRequest, simulate_aggressive_limit_buy
from crypto_paper_bot.filters import OrderBookSnapshot


def test_paper_buy_partial_fill_uses_book_depth() -> None:
    cfg = default_config()
    book = OrderBookSnapshot(
        bid=99.9,
        ask=100.0,
        bids=[(99.9, 10.0)],
        asks=[(100.0, 0.2)],
    )
    result = simulate_aggressive_limit_buy(
        PaperBuyRequest("BTC/USDT", quote_notional=100.0, reference_price=100.0),
        book,
        cfg.execution,
    )
    assert result.status == "partial"
    assert 0 < result.fill_ratio < 1
    assert result.maker_taker == "taker"


def test_paper_buy_expires_without_liquidity_inside_limit() -> None:
    cfg = default_config()
    book = OrderBookSnapshot(
        bid=99.0,
        ask=100.0,
        bids=[(99.0, 10.0)],
        asks=[(101.0, 10.0)],
    )
    result = simulate_aggressive_limit_buy(
        PaperBuyRequest("BTC/USDT", quote_notional=100.0, reference_price=100.0),
        book,
        cfg.execution,
    )
    assert result.fill_ratio == 0.0
