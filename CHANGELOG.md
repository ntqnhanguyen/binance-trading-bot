# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHANGELOG.md file to track version changes

## [1.0.0] - 2024-10-24

### Added
- Initial release of Binance Trading Bot
- 4 trading strategies (DCA, Trend Following, Mean Reversion, Grid)
- Risk management system with Circuit Breaker
- 4 operating modes (Backtest, Testnet, Paper, Mainnet)
- Comprehensive logging system
- Docker support with Dockerfile and docker-compose.yml
- Full documentation (README, QUICKSTART, ARCHITECTURE, ENV_SETUP)
- API setup guides (API_KEYS_GUIDE.txt)
- Test scripts (test_api.py, example_backtest.py)
- Makefile with common commands
- Configuration files (config.yaml, strategies.yaml, risk_limits.yaml)
- GitHub repository setup with topics and release

### Changed (Latest Update - 2024-10-24)
- Updated requirements.txt with specific package versions
- Enabled Grid strategy in config/strategies.yaml
- Fixed import issues in backtester.py
- Improved technical indicators calculations
- Optimized grid_strategy.py and mean_reversion.py
- Updated run_backtest.py default parameters

### Added (Latest Update)
- Shell scripts for quick operations:
  - scripts/download_data.sh - Download SOLUSDT data
  - scripts/run_backtest.sh - Run backtest with SOLUSDT

### Fixed
- Technical indicators calculation edge cases
- Strategy execution logic improvements
- Code formatting and consistency

## Version History

### v1.0.0 (2024-10-24)
- First stable release
- Complete trading bot with 4 strategies
- Full documentation and setup guides
- Docker support
- GitHub repository published

---

## Update Summary (Latest Pull)

**Date**: 2024-10-24  
**Commit**: 3f5e417  
**Author**: Hoang Dang Tuan (SDCAI)

**Files Changed**: 9 files
- config/strategies.yaml (Grid strategy enabled)
- requirements.txt (Updated package versions)
- run_backtest.py (Updated defaults)
- scripts/download_data.sh (New)
- scripts/run_backtest.sh (New)
- src/backtest/backtester.py (Import fix)
- src/indicators/technical.py (Calculation improvements)
- src/strategies/grid_strategy.py (Optimizations)
- src/strategies/mean_reversion.py (Improvements)

**Key Changes**:
- ✅ Grid strategy now enabled by default
- ✅ Added convenience shell scripts
- ✅ Fixed technical indicator edge cases
- ✅ Improved strategy execution logic
- ✅ Updated package dependencies

---

## How to Update

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Check what changed
git log --oneline -5
git diff HEAD~1 --stat
```

## Breaking Changes

None in current version.

## Migration Guide

No migration needed for v1.0.0 → latest update.

## Contributors

- ntqnhanguyen - Initial development
- Hoang Dang Tuan (SDCAI) - Updates and improvements

---

For more details, see the [GitHub Releases](https://github.com/ntqnhanguyen/binance-trading-bot/releases).

