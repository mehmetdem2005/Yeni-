from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from crypto_paper_bot.evaluation.metrics import classification_metrics
from crypto_paper_bot.features.builder import feature_columns
from crypto_paper_bot.models_ml.baselines import baseline_model_zoo, predict_positive_probability, train_model
from crypto_paper_bot.training.walk_forward import WalkForwardConfig, generate_walk_forward_splits


@dataclass(frozen=True)
class FoldResult:
    model_name: str
    fold: int
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str
    metrics: dict[str, Any]


def run_baseline_walk_forward(
    dataset: pd.DataFrame,
    label_col: str = "label_good_trade",
    cfg: WalkForwardConfig | None = None,
) -> list[FoldResult]:
    if label_col not in dataset.columns:
        raise ValueError(f"Missing label column: {label_col}")

    cols = feature_columns(dataset)
    if not cols:
        raise ValueError("No feature columns found")

    results: list[FoldResult] = []
    for fold, split in enumerate(generate_walk_forward_splits(dataset, cfg), start=1):
        train = dataset.iloc[split.train_index]
        validation = dataset.iloc[split.validation_index]
        test = dataset.iloc[split.test_index]
        x_train = train[cols]
        y_train = train[label_col].astype(int)
        x_test = test[cols]
        y_test = test[label_col].astype(int)

        for spec in baseline_model_zoo():
            model = train_model(spec, x_train, y_train)
            prob = predict_positive_probability(model, x_test)
            metrics = classification_metrics(y_test, prob).__dict__
            results.append(
                FoldResult(
                    model_name=spec.name,
                    fold=fold,
                    train_start=str(split.train_start),
                    train_end=str(split.train_end),
                    validation_start=str(split.validation_start),
                    validation_end=str(split.validation_end),
                    test_start=str(split.test_start),
                    test_end=str(split.test_end),
                    metrics=metrics,
                )
            )
    return results


def fold_results_to_frame(results: list[FoldResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        row = asdict(result)
        metrics = row.pop("metrics")
        row.update(metrics)
        rows.append(row)
    return pd.DataFrame(rows)
