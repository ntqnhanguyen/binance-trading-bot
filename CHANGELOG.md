# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Excel export with formatting
- Interactive HTML reports
- Trade visualization charts
- Performance attribution by strategy
- Database integration
- Real-time dashboard

## [1.2.0] - 2024-10-24

### Added - Dynamic Grid Spread

**Grid Trading Strategy now supports dynamic spread adjustment based on market volatility.**

#### Features
- **Dynamic spread calculation** using ATR and Bollinger Bands
- **Automatic grid recalculation** when spread changes >10%
- **Spread history tracking** for analysis
- **Configurable multiplier limits** (0.5x to 2.0x)
- **Volatility-based adaptation** to market conditions

#### Implementation
- `_calculate_dynamic_spread()` - ATR z-score based multiplier
- `_calculate_bb_width_ratio()` - BB expansion/contraction ratio
- `_update_dynamic_spread()` - Combine both factors
- `_recalculate_grid_levels()` - Update grid with new spacing
- `get_grid_info()` - Get current grid configuration

#### Configuration
```yaml
grid:
  use_dynamic_spread: true
  spread_multiplier_min: 0.5
  spread_multiplier_max: 2.0
  volatility_lookback: 50
```

#### Benefits
- ✅ Wider spread in high volatility → reduce stop loss risk
- ✅ Tighter spread in low volatility → more trading opportunities
- ✅ Automatic adaptation to market conditions
- ✅ Better risk management

#### Files
- `src/strategies/grid_strategy.py` - Enhanced with dynamic spread
- `config/strategies.yaml` - Added dynamic spread configuration
- `docs/DYNAMIC_GRID_SPREAD.md` - Complete documentation
- `test_dynamic_grid.py` - Test script

## [1.1.0] - 2024-10-24

### Added - Improved PnL Tracking

**Enhanced trade tracking and export system with detailed order information.**

#### Features
- **Order type tracking** (BUY/SELL) for each trade
- **Action tracking** (OPEN/CLOSE) to distinguish entries and exits
- **Enhanced trade records** with cumulative PnL, cash tracking
- **TradeExporter module** for better CSV export
- **Detailed trade summary reports**
- **Automatic export** in backtest and live trading

#### Trade Record Fields
- `timestamp` - Trade execution time
- `symbol` - Trading pair
- `strategy` - Strategy name
- `action` - OPEN or CLOSE
- `order_type` - **BUY or SELL** ⭐
- `side` - LONG or SHORT
- `price` - Execution price
- `quantity` - Trade quantity
- `value` - Total value
- `pnl` - Profit/Loss
- `pnl_pct` - PnL percentage
- `cumulative_pnl` - Running total PnL ⭐
- `cash_after` - Cash balance after trade ⭐
- `entry_price` - Entry price (for CLOSE)
- `entry_value` - Entry value (for CLOSE)
- `win` - Win/Loss flag (1/0)

#### CSV Export Format
```csv
timestamp,symbol,strategy,action,order_type,side,price,quantity,value,pnl,pnl_pct,cumulative_pnl,cash_after
2025-10-24 13:39:47,BTCUSDT,TrendFollowing,OPEN,BUY,LONG,50000.0,0.1,5000.0,0.0,0.0,0.0,5000.0
2025-10-24 13:39:47,BTCUSDT,TrendFollowing,CLOSE,SELL,LONG,52000.0,0.1,5200.0,200.0,4.0,200.0,10200.0
```

#### Files Changed
- `src/core/portfolio.py` - Enhanced trade recording
- `src/utils/trade_exporter.py` - **NEW** export module
- `run_backtest.py` - Use TradeExporter
- `main.py` - Export trades on stop
- `docs/PNL_TRACKING.md` - Full documentation
- `test_pnl_tracking.py` - Demo script
- `IMPROVEMENTS.md` - Feature overview

## [1.0.0] - 2024-10-24

### Added - Initial Release

**First stable release of Binance Trading Bot.**

#### Trading Strategies
- **DCA (Dollar-Cost Averaging)** - Accumulation with layer management
- **Trend Following** - MA Cross, Donchian Breakout, RSI Pullback
- **Mean Reversion** - RSI and Bollinger Bands based
- **Grid Trading** - Range-bound trading with fixed spread

#### Risk Management
- Circuit Breaker system
- Per-trade risk limits (0.5% default)
- Daily/weekly loss limits
- Trailing stop-loss with ATR
- Position sizing
- Cash reserve management

#### Operating Modes
- **Backtest** - Historical data testing
- **Testnet** - Safe testing environment
- **Paper** - Simulated trading with real-time data
- **Mainnet** - Real trading

#### Core Features
- Binance API integration
- Portfolio management
- Technical indicators (ATR, ADX, MA, RSI, BB, etc.)
- Strategy orchestrator
- Comprehensive logging system
- Docker support

#### Documentation
- README.md - Complete guide
- QUICKSTART.md - Quick start guide
- ARCHITECTURE.md - Architecture details
- ENV_SETUP.md - API keys setup
- API_KEYS_GUIDE.txt - Quick reference

#### Configuration
- YAML-based configuration
- Environment variables support
- Risk limits configuration
- Strategy parameters

#### Files
- 43 Python files
- 7,000+ lines of code
- Full test coverage
- Docker configuration
- Makefile for common commands

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| **1.2.0** | 2024-10-24 | Dynamic Grid Spread |
| **1.1.0** | 2024-10-24 | Improved PnL Tracking |
| **1.0.0** | 2024-10-24 | Initial Release |

---

## How to Update

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Check what changed
git log --oneline -10
```

## Breaking Changes

### v1.2.0
- None. Dynamic spread is optional and backward compatible.

### v1.1.0
- None. Enhanced trade records are additive, old code still works.

### v1.0.0
- Initial release, no breaking changes.

## Migration Guide

### To v1.2.0 (Dynamic Grid Spread)

No migration needed. To enable:

```yaml
# config/strategies.yaml
grid:
  use_dynamic_spread: true  # Enable feature
```

### To v1.1.0 (Improved PnL Tracking)

No migration needed. To use new export:

```python
from src.utils.trade_exporter import TradeExporter

# Instead of:
# df.to_csv('trades.csv')

# Use:
TradeExporter.export_detailed_report(trade_history, 'trades')
```

## Contributors

- **ntqnhanguyen** - Initial development and all features
- **Hoang Dang Tuan (SDCAI)** - Code improvements and testing

---

For more details, see:
- [GitHub Releases](https://github.com/ntqnhanguyen/binance-trading-bot/releases)
- [Documentation](docs/)
- [Issues](https://github.com/ntqnhanguyen/binance-trading-bot/issues)

