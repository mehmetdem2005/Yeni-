#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  echo "Virtual environment was created, but activation script was not found."
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

mkdir -p outputs/runs logs

if [ ! -f configs/config.local.yaml ]; then
  cp configs/config.example.yaml configs/config.local.yaml
fi

python -m crypto_paper_bot.cli validate-config configs/config.local.yaml
python -m crypto_paper_bot.cli demo
pytest

echo "Setup completed."
