.PHONY: help install run backtest download-data docker-build docker-run docker-stop clean test-api setup-env

help:
	@echo "Binance Trading Bot - Available Commands"
	@echo "========================================"
	@echo "setup-env        - Create .env file from template"
	@echo "test-api         - Test Binance API connection"
	@echo "install          - Install dependencies"
	@echo "run              - Run the trading bot"
	@echo "backtest         - Run backtest"
	@echo "download-data    - Download historical data"
	@echo "docker-build     - Build Docker image"
	@echo "docker-run       - Run with Docker Compose"
	@echo "docker-stop      - Stop Docker containers"
	@echo "docker-logs      - View Docker logs"
	@echo "clean            - Clean logs and cache files"

setup-env:
	@cp .env.example .env
	@echo "✓ Created .env file"
	@echo "Please edit .env and add your API keys"

test-api:
	python test_api.py

install:
	pip install -r requirements.txt

run:
	python main.py

backtest:
	python run_backtest.py

download-data:
	python download_data.py --symbols BTCUSDT ETHUSDT BNBUSDT

docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f trading-bot

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf logs/*.log
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage


# Hybrid Strategy Commands
.PHONY: hybrid-backtest hybrid-run hybrid-paper

hybrid-backtest:  ## Run hybrid strategy backtest
@echo "Running hybrid strategy backtest..."
python run_hybrid_backtest.py --symbol BTCUSDT --capital 10000 --data ./data/BTCUSDT_1m.csv

hybrid-paper:  ## Run hybrid strategy in paper trading mode
@echo "Starting hybrid strategy paper trading..."
@cp .env.hybrid.example .env 2>/dev/null || true
TRADING_MODE=paper python main_hybrid.py

hybrid-run:  ## Run hybrid strategy live (REAL MONEY!)
@echo "⚠️  WARNING: Running with REAL MONEY!"
@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
TRADING_MODE=mainnet python main_hybrid.py

