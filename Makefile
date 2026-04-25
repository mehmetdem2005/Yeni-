.PHONY: setup test demo lint validate

setup:
	bash scripts/setup.sh

validate:
	python -m crypto_paper_bot.cli validate-config configs/config.local.yaml

demo:
	python -m crypto_paper_bot.cli demo

test:
	pytest

lint:
	ruff check src tests
