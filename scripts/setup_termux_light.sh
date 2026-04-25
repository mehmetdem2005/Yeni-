#!/usr/bin/env bash
set -euo pipefail

pkg update -y
pkg install git python clang make rust llvm lld python-numpy tur-repo -y
pkg install python-pandas -y

rm -rf .venv
python -m venv --system-site-packages .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest PyYAML pydantic

if [ ! -f configs/config.local.yaml ]; then
  cp configs/config.example.yaml configs/config.local.yaml
fi

python -m crypto_paper_bot.cli validate-config configs/config.local.yaml
python -m crypto_paper_bot.cli demo

echo "Termux light setup completed. ML training with scikit-learn should be run on cloud/desktop if it fails on phone."
