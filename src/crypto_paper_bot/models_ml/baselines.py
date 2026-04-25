from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class ProbabilisticModel(Protocol):
    def fit(self, x: pd.DataFrame, y: pd.Series) -> "ProbabilisticModel":
        ...

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        ...


@dataclass(frozen=True)
class ModelSpec:
    name: str
    model: ProbabilisticModel


def baseline_model_zoo(random_state: int = 42) -> list[ModelSpec]:
    return [
        ModelSpec(
            name="logistic_regression",
            model=Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
                ]
            ),
        ),
        ModelSpec(
            name="random_forest",
            model=RandomForestClassifier(
                n_estimators=200,
                max_depth=6,
                min_samples_leaf=20,
                class_weight="balanced_subsample",
                random_state=random_state,
                n_jobs=-1,
            ),
        ),
        ModelSpec(
            name="gradient_boosting",
            model=GradientBoostingClassifier(random_state=random_state),
        ),
    ]


def train_model(spec: ModelSpec, x_train: pd.DataFrame, y_train: pd.Series) -> ProbabilisticModel:
    model = spec.model
    model.fit(x_train, y_train)
    return model


def predict_positive_probability(model: ProbabilisticModel, x: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(x)
    if proba.shape[1] == 1:
        return np.zeros(len(x), dtype=float)
    return proba[:, 1]
