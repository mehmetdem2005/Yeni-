# Advanced Multi-AI ML Architecture Plan

This document upgrades the paper-trade core into a real machine-learning research system. It is still research/paper-trade first. No live-money execution is enabled by default.

## 0. Goal

Build a modular multi-model and multi-agent research platform for spot-only crypto paper trading.

The system must not be a simple indicator bot. It should become a machine-learning pipeline that learns from market data, order book data, regime shifts, execution quality, and past paper-trade outcomes.

## 1. Core Principles

- Research-first, paper-trade-first
- Spot-only and long-only in the first production-grade research phase
- No live online weight updates until enough evidence exists
- No model can bypass the risk engine
- Every prediction must be logged with features, model version, data version, and decision reason
- Every experiment must be reproducible
- Simple baseline models must stay available as control models

## 2. High-Level Architecture

```text
Market Data Ingestion
        ↓
Raw Data Lake
        ↓
Cleaned Time-Series Store
        ↓
Feature Store
        ↓
Model Zoo
        ↓
Ensemble / Meta-Model Layer
        ↓
Decision Policy Engine
        ↓
Risk Engine
        ↓
Paper Execution Simulator
        ↓
Trade Log + Feedback Store
        ↓
Evaluation + Research Agents
```

## 3. Main Services

### 3.1 Data Ingestion Service

Responsibilities:

- Pull OHLCV data
- Pull order book snapshots
- Pull spread and depth metrics
- Store raw data without modification
- Validate missing candles and duplicate timestamps

Initial technology:

- Python
- CCXT for exchange data
- PostgreSQL + TimescaleDB for time-series data
- Parquet files for historical research snapshots

Future technology:

- Kafka or Redpanda for streaming data
- MinIO or cloud object storage for raw lake

### 3.2 Feature Engineering Service

Responsibilities:

- Build technical features
- Build volatility features
- Build liquidity features
- Build market-regime features
- Build cross-asset correlation features
- Prevent lookahead bias

Feature groups:

- Trend features
- Momentum features
- Volatility features
- Volume and liquidity features
- Order book microstructure features
- BTC correlation and beta features
- Time/calendar features
- Regime and drawdown features

Technology:

- Pandas for initial version
- NumPy for vectorized math
- Polars optional for larger data
- Feast optional later as formal feature store

### 3.3 Labeling Service

The system needs labels. Without labels, machine learning is fake.

Possible labels:

- Future return after 3, 6, 12 H1 candles
- Whether TP hits before SL
- Maximum adverse excursion
- Maximum favorable excursion
- Realized reward/risk after costs
- Whether limit order would likely fill
- Market regime class

Label examples:

```text
label_tp_before_sl = 1 or 0
label_future_return_12h = percentage return after 12 hours
label_net_trade_quality = net pnl after fee, spread, and slippage
```

### 3.4 Model Zoo

The model zoo stores multiple model families. No single model is trusted alone.

Baseline models:

- Logistic Regression
- Ridge / Lasso
- Random Forest
- Gradient Boosting

Strong tabular models:

- LightGBM
- XGBoost
- CatBoost

Time-series models:

- Temporal CNN
- LSTM / GRU
- Transformer encoder for time-series windows
- PatchTST-style model later if data size supports it

Anomaly and regime models:

- Isolation Forest
- Gaussian Mixture Model
- Hidden Markov Model
- HDBSCAN for clustering regimes

Meta-models:

- Stacking classifier
- Calibrated probability model
- Ensemble ranker

### 3.5 Ensemble and Meta-Decision Layer

No model directly opens a trade.

Each model outputs:

```text
probability_of_good_trade
expected_return
expected_drawdown
expected_fill_quality
confidence
model_uncertainty
```

The ensemble layer combines outputs into:

```text
ml_edge_score
ml_confidence
model_agreement_score
uncertainty_penalty
```

A trade can be considered only if:

- Rule-based gates pass
- ML edge score passes
- Model agreement is high enough
- Uncertainty is not too high
- Risk engine approves

### 3.6 Decision Policy Engine

The policy engine combines:

- Rule-based filters
- ML prediction
- Market regime
- Risk state
- Portfolio state
- Cooldown state

Output:

```text
SKIP
WATCH
PAPER_BUY
PAPER_CLOSE
```

### 3.7 Risk Engine

The risk engine remains supreme.

It controls:

- Position size
- Stop distance
- Max portfolio risk
- Correlation lock
- Consecutive stop cooldown
- Drawdown circuit breaker
- Emergency halt

No AI or ML model may override this layer.

### 3.8 Paper Execution Engine

Responsibilities:

- Simulate aggressive limit orders
- Estimate queue position
- Simulate partial fills
- Track maker/taker status
- Track spread and slippage
- Produce realistic execution logs

Later:

- Execution-quality model predicts whether a limit order will fill
- Separate model decides maker-like or taker-like behavior in paper environment

## 4. Multi-Agent Research Architecture

This is not a chatbot swarm. Each agent has a narrow technical role.

### Agent 1: Data Quality Agent

Checks:

- Missing candles
- Duplicate records
- Broken OHLCV values
- Sudden zero volume
- Exchange data gaps

### Agent 2: Feature Research Agent

Tests new features and reports:

- Predictive power
- Correlation with existing features
- Stability across market regimes
- Leakage risk

### Agent 3: Label Research Agent

Compares labels:

- Future return label
- TP-before-SL label
- Net trade quality label
- Fill-quality label

### Agent 4: Model Trainer Agent

Trains models with fixed walk-forward splits.

Outputs:

- Model artifact
- Metrics
- Feature importance
- Calibration report
- Data version

### Agent 5: Backtest Agent

Runs strict walk-forward backtests.

Checks:

- Net Sharpe
- Max drawdown
- Fill rate
- Win rate
- Average win/loss
- BTC crash periods

### Agent 6: Risk Auditor Agent

Attempts to reject unsafe configurations.

Checks:

- Position sizing bugs
- Portfolio risk breaches
- Correlation rule breaches
- Drawdown rule breaches

### Agent 7: Execution Simulator Agent

Improves fill simulation realism.

Checks:

- Limit fill probability
- Partial fill bias
- Fee assumptions
- Spread assumptions

### Agent 8: Drift Monitor Agent

Monitors model decay.

Checks:

- Feature distribution drift
- Prediction confidence drift
- Performance drift
- Regime shift

### Agent 9: Experiment Judge Agent

Approves or rejects experiments.

Approval requires:

- Walk-forward improvement
- No drawdown explosion
- Stable results across coins
- No data leakage
- Reasonable complexity

### Agent 10: Documentation Agent

Keeps docs, configs, and experiment records synchronized.

## 5. Training Workflow

```text
1. Ingest raw market data
2. Clean and validate data
3. Build features using only past closed candles
4. Create labels using future outcomes
5. Split data with walk-forward windows
6. Train baseline models
7. Train stronger models
8. Calibrate probabilities
9. Build ensemble
10. Run strict backtest
11. Run paper-trade shadow mode
12. Compare with baseline rule strategy
13. Promote only if metrics improve safely
```

## 6. Experiment Tracking

Use MLflow or Weights & Biases.

Every run logs:

- Git commit SHA
- Config hash
- Data version
- Feature set version
- Label version
- Model parameters
- Metrics
- Artifacts
- Failure notes

Recommended initial tool:

- MLflow, because it can run locally and is simple to self-host.

## 7. Data Versioning

Recommended:

- DVC for dataset versioning
- Parquet snapshots for training data
- PostgreSQL/TimescaleDB for operational time-series

Each model artifact must point to exact data and feature versions.

## 8. Model Registry

Initial:

- MLflow Model Registry

Model stages:

- research
- candidate
- paper_shadow
- rejected
- archived

No model moves to paper_shadow unless all audits pass.

## 9. Technology Stack

### Core Language

- Python 3.11+

### Data

- PostgreSQL
- TimescaleDB
- Parquet
- Optional MinIO later

### ML

- scikit-learn
- LightGBM
- XGBoost
- CatBoost
- PyTorch
- PyTorch Forecasting optional later

### Feature Pipeline

- Pandas initial
- NumPy
- Polars optional
- Feast optional later

### Orchestration

- Prefect initial
- Airflow later only if workflows become heavy

### Experiment Tracking

- MLflow

### Data Versioning

- DVC

### Monitoring

- Grafana
- Prometheus
- Evidently AI for drift reports

### API / Services

- FastAPI for internal model serving
- Redis for lightweight queues
- Celery optional for distributed jobs

### Containers

- Docker Compose for local infra
- Later Kubernetes only if needed

## 10. Repository Structure Target

```text
src/crypto_paper_bot/
  data/
  features/
  labels/
  models/
  training/
  evaluation/
  ensemble/
  decision/
  risk/
  execution/
  agents/
  monitoring/
  registry/
  cli/

configs/
  base.yaml
  features.yaml
  labels.yaml
  models.yaml
  training.yaml
  agents.yaml

experiments/
  README.md

docs/
  ML_ARCHITECTURE.md
  FEATURE_SPEC.md
  LABEL_SPEC.md
  MODEL_GOVERNANCE.md
```

## 11. Build Phases

### Phase 1: Research Infrastructure

- Historical data downloader
- TimescaleDB schema
- Parquet exporter
- Feature builder
- Label builder
- Walk-forward splitter

### Phase 2: Baseline ML

- Logistic regression
- Random forest
- LightGBM
- Probability calibration
- Baseline-vs-rule comparison

### Phase 3: Ensemble System

- Multiple model outputs
- Meta-model
- Model agreement score
- Uncertainty penalty

### Phase 4: Multi-Agent Research Automation

- Data Quality Agent
- Feature Research Agent
- Model Trainer Agent
- Backtest Agent
- Risk Auditor Agent
- Experiment Judge Agent

### Phase 5: Monitoring and Drift

- Drift reports
- Model decay monitoring
- Paper-trade performance dashboard

## 12. Non-Negotiable Safety Rules

- No model bypasses risk engine
- No open-candle features
- No future data in features
- No paper result without fee and slippage
- No model promotion without walk-forward results
- No architecture change without tests
- No live learning in early phases

## 13. Next Implementation Step

Add the following modules first:

```text
features/builder.py
labels/builder.py
training/walk_forward.py
models/baselines.py
evaluation/metrics.py
registry/run_logger.py
agents/contracts.py
```

This converts the current rule-based paper core into a real ML research foundation.
