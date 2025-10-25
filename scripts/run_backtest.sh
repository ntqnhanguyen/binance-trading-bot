#!/bin/bash
# Quick script to run hybrid strategy backtest

# Default parameters
SYMBOL="${1:-BTCUSDT}"
CAPITAL="${2:-10000}"
DATA_FILE="${3:-./data/BTCUSDT_1m.csv}"

echo "=========================================="
echo "Backtest"
echo "=========================================="
echo "Symbol: $SYMBOL"
echo "Capital: \$$CAPITAL"
echo "Data: $DATA_FILE"
echo "=========================================="
echo ""

# Check if data file exists
if [ ! -f "$DATA_FILE" ]; then
    echo "Error: Data file not found: $DATA_FILE"
    echo "Please download data first:"
    echo "  python download_data.py --symbol $SYMBOL --interval 1m --start 2024-01-01"
    exit 1
fi

# Run backtest
python run_backtest.py \
    --symbol "$SYMBOL" \
    --capital "$CAPITAL" \
    --data "$DATA_FILE" \
    --config config/hybrid_strategy.yaml

echo ""
echo "Backtest completed!"
echo "Check ./data/ for results"

