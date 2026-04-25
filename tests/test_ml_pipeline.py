import pandas as pd

from crypto_paper_bot.features.builder import build_features
from crypto_paper_bot.labels.builder import build_forward_return_labels
from crypto_paper_bot.training.walk_forward import WalkForwardConfig, generate_walk_forward_splits


def _ohlcv(rows: int = 3000) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=rows, freq="h", tz="UTC")
    base = [100 + i * 0.01 + (i % 24) * 0.02 for i in range(rows)]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": base,
            "high": [v + 0.5 for v in base],
            "low": [v - 0.5 for v in base],
            "close": [v + 0.1 for v in base],
            "volume": [1000 + (i % 50) for i in range(rows)],
        }
    )


def test_features_and_labels_are_built() -> None:
    features = build_features(_ohlcv())
    labeled = build_forward_return_labels(features)
    assert not features.empty
    assert "rsi" in features.columns
    assert "label_good_trade" in labeled.columns


def test_walk_forward_generates_splits() -> None:
    features = build_features(_ohlcv(7000))
    labeled = build_forward_return_labels(features)
    splits = list(generate_walk_forward_splits(labeled, WalkForwardConfig()))
    assert splits
    first = splits[0]
    assert first.train_index
    assert first.validation_index
    assert first.test_index
