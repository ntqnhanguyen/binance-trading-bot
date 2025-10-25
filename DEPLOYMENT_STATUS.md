# Deployment Status

## ✅ Latest Version: v2.0.0

**Date**: October 25, 2025  
**Status**: Production Ready  
**Repository**: https://github.com/ntqnhanguyen/binance-trading-bot

## Recent Updates

### v2.0.0 (Latest) - Major Refactoring
- **Commit**: f081d1e
- **Date**: Oct 25, 2025
- **Changes**: Simplified codebase, removed old strategies
- **Status**: ✅ Deployed

### Key Fixes Applied
1. ✅ TradingLogger initialization (b8eb999)
2. ✅ IndicatorEngine method calls (1d5f0d1)
3. ✅ IndexError in backtest report (3169491)
4. ✅ Major refactoring (6eb7df8)
5. ✅ Documentation added (f081d1e)

## Current Structure

```
binance-trading-bot/
├── main.py                 # Live trading bot
├── run_backtest.py         # Backtesting
├── download_data.py        # Data downloader
├── test_api.py            # API tester
├── config/
│   └── config.yaml        # Strategy configuration
├── src/
│   ├── core/              # Exchange & Portfolio
│   ├── indicators/        # Technical Analysis
│   ├── risk/              # Risk Management
│   ├── strategies/        # Hybrid Strategy Engine
│   └── utils/             # Utilities
└── docs/                  # Documentation
```

## Quick Start

```bash
# Clone
git clone https://github.com/ntqnhanguyen/binance-trading-bot.git
cd binance-trading-bot

# Install
pip install -r requirements.txt

# Setup
cp .env.example .env
# Edit .env with your API keys

# Test
python test_api.py

# Download data
python download_data.py --symbol BTCUSDT --interval 1m --start 2024-01-01

# Backtest
python run_backtest.py --symbol BTCUSDT --capital 10000 --data ./data/BTCUSDT_1m.csv

# Paper trading
TRADING_MODE=paper python main.py

# Live trading (REAL MONEY!)
TRADING_MODE=mainnet python main.py
```

## Makefile Commands

```bash
make help           # Show all commands
make install        # Install dependencies
make setup-env      # Setup .env file
make test-api       # Test API connection
make download-data  # Download historical data
make backtest       # Run backtest
make paper          # Paper trading
make run            # Live trading
make clean          # Clean cache
```

## Configuration

### Environment (.env)
```bash
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TRADING_MODE=paper  # paper, testnet, mainnet
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
INITIAL_CAPITAL=10000
CONFIG_PATH=config/config.yaml
```

### Strategy (config/config.yaml)
```yaml
default_policy:
  # Dynamic Spread
  use_dynamic_spread: true
  spread_near_pct: 0.3
  spread_mid_pct: 0.5
  spread_far_pct: 0.8
  
  # Grid Trading
  grid_enabled: true
  grid_levels_per_side: 3
  
  # DCA
  dca_enabled: true
  dca_rsi_threshold: 35
  
  # TP
  tp_enabled: true
  tp_rsi_threshold: 65
  
  # PnL Gate
  gate_degraded_gap_pct: -3.0
  gate_paused_gap_pct: -5.0
  
  # Stop-Loss
  hard_stop_daily_pnl_pct: -5.0
  hard_stop_gap_pct: -8.0
```

## Features

### ✅ Hybrid Strategy Engine
- Dynamic spread based on ATR volatility
- Grid trading (2-sided)
- DCA on oversold conditions
- TP trailing suggestions
- PnL Gate (RUN/DEGRADED/PAUSED states)
- Hard stop-loss protection

### ✅ Operating Modes
- **Backtest**: Historical data testing
- **Paper**: Simulation with live data
- **Testnet**: Binance testnet trading
- **Mainnet**: Real trading

### ✅ Risk Management
- Per-trade risk limits
- Daily PnL limits
- Circuit breaker
- Trailing stop-loss
- Position size limits

### ✅ Monitoring
- Comprehensive logging
- Trade export (CSV)
- Equity curve tracking
- State history
- Performance metrics

## Documentation

- **README.md** - Main documentation
- **HYBRID_USAGE.md** - Complete usage guide
- **REFACTORING.md** - v2.0.0 changes
- **ARCHITECTURE.md** - System architecture
- **ENV_SETUP.md** - API keys setup
- **API_KEYS_GUIDE.txt** - Quick reference
- **DEPLOYMENT_STATUS.md** - This file

## Dependencies

Core packages:
- python-binance==1.0.19
- pandas==2.3.2
- numpy==2.2.6
- pandas-ta==0.3.14b
- pyyaml
- python-dotenv
- colorlog

## Testing

All tests passing:
- ✅ Syntax checks
- ✅ API connection
- ✅ Indicator calculations
- ✅ Strategy logic
- ✅ Backtest execution
- ✅ Trade export

## Known Issues

None currently. All critical bugs fixed.

## Support

- GitHub Issues: https://github.com/ntqnhanguyen/binance-trading-bot/issues
- Documentation: See docs/ folder
- Examples: See test_hybrid_strategy.py

## Changelog

### v2.0.0 (Oct 25, 2025)
- Major refactoring
- Removed old strategies
- Simplified codebase
- Clean naming
- Single config file

### v1.3.0 (Oct 25, 2025)
- Added Hybrid Strategy Engine
- PnL Gate implementation
- Dynamic spread

### v1.2.0 (Oct 24, 2025)
- Dynamic grid spread
- Improved PnL tracking

### v1.1.0 (Oct 24, 2025)
- Grid strategy improvements
- Trade export enhancements

### v1.0.0 (Oct 24, 2025)
- Initial release
- Multiple strategies
- Basic backtesting

## License

MIT License - See LICENSE file

## Disclaimer

**Trading involves risk of loss. This software is provided as-is with no guarantees. Always test thoroughly before using real money. Never invest more than you can afford to lose.**

---

**Last Updated**: October 25, 2025  
**Status**: ✅ Production Ready  
**Version**: 2.0.0
