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
- Orchestrator integration for Hybrid Strategy
- Live trading with Hybrid Strategy

## [1.3.0] - 2024-10-24

### Added - Hybrid Strategy Engine (Option-A)

**Advanced trading strategy combining Grid + DCA with dynamic spread, PnL Gate, and Stop-Loss.**

#### Components

**1. HybridStrategyEngine**
- Main strategy engine implementing Option-A interface
- `on_bar(bar, equity)` returns comprehensive plan dict
- Dynamic spread calculation based on ATR% and RSI
- Grid/DCA/TP order planning
- PnL Gate state management
- Stop-Loss evaluation

**2. IndicatorEngine**
- Technical indicator calculator and provider
- RSI, ATR, EMA, Bollinger Bands
- Caches latest signals for strategy consumption
- Updates from OHLCV data

**3. Configuration System**
- YAML-based policy configuration
- Default policy + pair-specific overrides
- Risk management parameters
- Execution settings

#### Features

**Dynamic Spread Calculation**
- **Band selection** based on ATR%:
  - near (ATR < 1.0%): 0.3% spread
  - mid (ATR < 2.0%): 0.5% spread
  - far (ATR >= 2.0%): 0.8% spread
- **RSI adjustment**: ±10% based on RSI level
- Tighter spread when oversold, wider when overbought

**Grid Orders Planning**
- Two-sided grid around reference price
- Configurable levels per side (default: 3)
- Kill & replace when price drifts >1%
- Cooldown: 5 minutes between updates

**DCA Orders Planning**
- Trigger when RSI < 35 (oversold)
- Optional EMA gate (price < EMA fast)
- Cooldown: 5 bars between DCA orders
- Min distance: 1% from last DCA fill
- Price offset: 0.1% below market

**TP Suggestions**
- Trigger when RSI > 65 (overbought)
- Price must be above EMA fast
- TP spread varies by band (0.5% to 1.2%)
- Trailing execution by Orchestrator

**PnL Gate States**
- **RUN**: Full operation (Gap > -3%, Daily PnL > -2%)
- **DEGRADED**: Reduced operation (Gap -3% to -5%, PnL -2% to -4%)
- **PAUSED**: No new orders (Gap < -5%, PnL < -4%)
- **Hard Stop**: Daily PnL <= -5% OR Gap <= -8%

**State Tracking**
- Last grid reference price and timestamp
- Last DCA timestamp and fill price
- Day open price and equity for PnL calculation
- Automatic daily reset

#### Interface (Option-A)

**Input:**
```python
on_bar(bar: Dict, equity: float) -> Dict
```

**Output Plan Dict:**
```python
{
    "pnl_gate_state": "RUN" | "DEGRADED" | "PAUSED",
    "sl_action": {"stop": bool, "reason": str},
    "grid_orders": [{"side", "price", "tag"}, ...],
    "dca_orders": [{"side", "price", "tag"}, ...],
    "tp_orders": [{"side", "price", "tag"}, ...],
    "band": "near" | "mid" | "far",
    "spread_pct": float,
    "ref_price": float,
    "kill_replace": bool
}
```

#### Configuration

```yaml
# config/hybrid_strategy.yaml
default_policy:
  use_dynamic_spread: true
  band_near_threshold: 1.0
  band_mid_threshold: 2.0
  spread_near_pct: 0.3
  spread_mid_pct: 0.5
  spread_far_pct: 0.8
  grid_enabled: true
  dca_enabled: true
  tp_enabled: true
  gate_degraded_gap_pct: -3.0
  hard_stop_daily_pnl_pct: -5.0

pairs:
  BTCUSDT:
    spread_near_pct: 0.2
    grid_levels_per_side: 4
```

#### Files
- `src/strategies/hybrid_strategy_engine.py` - Main engine
- `src/indicators/indicator_engine.py` - Indicator provider
- `config/hybrid_strategy.yaml` - Configuration
- `docs/HYBRID_STRATEGY.md` - Complete documentation
- `test_hybrid_strategy.py` - Test suite

#### Benefits
- ✅ Combines best of Grid and DCA strategies
- ✅ Adapts to market volatility automatically
- ✅ Risk management via PnL Gate
- ✅ Portfolio-level stop-loss
- ✅ Configurable per trading pair
- ✅ Clean separation of concerns
- ✅ Ready for orchestrator integration

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

