#!/bin/bash
# Run Binance Trading Bot in Live Mode
# Supports: testnet, paper, mainnet

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
MODE="${TRADING_MODE:-testnet}"
SYMBOL="${SYMBOL:-BTCUSDT}"
CAPITAL="${INITIAL_CAPITAL:-1000}"
CONFIG="${CONFIG_FILE:-config/config.yaml}"

# Help message
show_help() {
    echo -e "${BLUE}Binance Trading Bot - Live Trading${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE       Trading mode: testnet, paper, mainnet (default: testnet)"
    echo "  -s, --symbol SYMBOL   Trading pair (default: BTCUSDT)"
    echo "  -c, --capital AMOUNT  Initial capital (default: 1000)"
    echo "  --config FILE         Config file path (default: config/config.yaml)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  TRADING_MODE          Trading mode (testnet/paper/mainnet)"
    echo "  SYMBOL                Trading pair"
    echo "  INITIAL_CAPITAL       Initial capital"
    echo "  CONFIG_FILE           Config file path"
    echo ""
    echo "Examples:"
    echo "  # Run on testnet (safe)"
    echo "  $0 --mode testnet --symbol BTCUSDT --capital 1000"
    echo ""
    echo "  # Run paper trading (simulation with real data)"
    echo "  $0 --mode paper --symbol ETHUSDT --capital 5000"
    echo ""
    echo "  # Run on mainnet (REAL MONEY!)"
    echo "  $0 --mode mainnet --symbol SOLUSDT --capital 100"
    echo ""
    echo "  # Using environment variables"
    echo "  TRADING_MODE=testnet SYMBOL=BTCUSDT ./scripts/run_live.sh"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -s|--symbol)
            SYMBOL="$2"
            shift 2
            ;;
        -c|--capital)
            CAPITAL="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate mode
if [[ ! "$MODE" =~ ^(testnet|paper|mainnet)$ ]]; then
    echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
    echo "Valid modes: testnet, paper, mainnet"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env file with your API credentials"
    echo "Example: cp .env.example .env"
    exit 1
fi

# Check if config exists
if [ ! -f "$CONFIG" ]; then
    echo -e "${RED}Error: Config file not found: $CONFIG${NC}"
    exit 1
fi

# Warning for mainnet
if [ "$MODE" == "mainnet" ]; then
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    ⚠️  WARNING ⚠️                          ║${NC}"
    echo -e "${RED}║                                                            ║${NC}"
    echo -e "${RED}║  You are about to run the bot with REAL MONEY!            ║${NC}"
    echo -e "${RED}║                                                            ║${NC}"
    echo -e "${RED}║  - Trading on mainnet uses real funds                     ║${NC}"
    echo -e "${RED}║  - You can lose money                                     ║${NC}"
    echo -e "${RED}║  - Make sure you have tested on testnet first             ║${NC}"
    echo -e "${RED}║  - Start with small capital                               ║${NC}"
    echo -e "${RED}║  - Monitor the bot closely                                ║${NC}"
    echo -e "${RED}║                                                            ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    read -p "Type 'YES' to continue with mainnet: " confirm
    if [ "$confirm" != "YES" ]; then
        echo -e "${YELLOW}Cancelled.${NC}"
        exit 0
    fi
fi

# Print configuration
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Binance Trading Bot - Live Trading               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Mode:           $MODE"
echo "  Symbol:         $SYMBOL"
echo "  Capital:        \$$CAPITAL"
echo "  Config:         $CONFIG"
echo ""

# Set environment variables
export TRADING_MODE="$MODE"
export SYMBOL="$SYMBOL"
export INITIAL_CAPITAL="$CAPITAL"
export CONFIG_FILE="$CONFIG"

# Create logs directory
mkdir -p logs

# Log file
LOG_FILE="logs/trading_${MODE}_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}Starting bot...${NC}"
echo "Log file: $LOG_FILE"
echo ""

# Check Python dependencies
if ! python3 -c "import yaml" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -r requirements.txt
fi

# Run the bot
echo -e "${GREEN}Bot is running. Press Ctrl+C to stop.${NC}"
echo ""

# Run with output to both console and log file
python3 main.py 2>&1 | tee "$LOG_FILE"

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}Bot stopped successfully.${NC}"
else
    echo -e "${RED}Bot exited with error code: $EXIT_CODE${NC}"
fi

echo "Log saved to: $LOG_FILE"
exit $EXIT_CODE

