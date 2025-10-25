.PHONY: help install test clean run backtest download-data setup-env test-api testnet mainnet docker-build docker-run

help:  ## Show this help message
@echo "Available commands:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
pip3 install -r requirements.txt

setup-env:  ## Setup environment file
@if [ ! -f .env ]; then \
cp .env.example .env; \
echo "✓ .env file created. Please edit it with your API keys."; \
else \
echo "✓ .env file already exists"; \
fi

test-api:  ## Test API connection
python test_api.py

download-data:  ## Download historical data
python download_data.py --symbol BTCUSDT --interval 1m --start 2024-01-01

backtest:  ## Run backtest
python run_backtest.py --symbol BTCUSDT --capital 10000 --data ./data/BTCUSDT_1m.csv

run:  ## Run live trading bot
python main.py

paper:  ## Run paper trading
	TRADING_MODE=paper python main.py

testnet:  ## Run on Binance Testnet
	./scripts/run_live.sh --mode testnet

mainnet:  ## Run on Binance Mainnet (REAL MONEY)
	./scripts/run_live.sh --mode mainnet

docker-build:  ## Build Docker image
docker build -t binance-trading-bot .

docker-run:  ## Run with Docker
docker-compose up -d

docker-stop:  ## Stop Docker containers
docker-compose down

docker-logs:  ## View Docker logs
docker-compose logs -f

clean:  ## Clean up cache and temp files
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name ".DS_Store" -delete

test:  ## Run tests
python test_hybrid_strategy.py
