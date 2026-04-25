# Install Guide

## Desktop / Linux / Cloud VM

```bash
git clone https://github.com/mehmetdem2005/Yeni-.git
cd Yeni-
bash scripts/setup.sh
```

Manual setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp configs/config.example.yaml configs/config.local.yaml
python -m crypto_paper_bot.cli validate-config configs/config.local.yaml
python -m crypto_paper_bot.cli demo
pytest
```

## Termux / Android

Recommended packages:

```bash
pkg update
pkg install git python clang make rust binutils-is-llvm
```

Then:

```bash
git clone https://github.com/mehmetdem2005/Yeni-.git
cd Yeni-
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp configs/config.example.yaml configs/config.local.yaml
python -m crypto_paper_bot.cli demo
pytest
```

If `scikit-learn` build fails on Termux, use a cloud VM or GitHub Codespaces for the ML training phase. The core pure-Python parts can still be edited on phone.

## Commands

```bash
make setup
make demo
make test
make lint
```

## Current status

This is a research and paper-trade codebase. It does not include live-money execution.
