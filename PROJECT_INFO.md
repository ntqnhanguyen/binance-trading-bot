# Binance Trading Bot - Project Information

## Project Overview

**Name**: Binance Trading Bot  
**Version**: 1.0.0  
**Language**: Python 3.11+  
**License**: MIT  

## Description

Hệ thống giao dịch tự động đa chiến lược trên Binance Spot với trọng tâm bảo toàn vốn. Bot triển khai 4 chiến lược chính (DCA, Trend Following, Mean Reversion, Grid) với hệ thống quản trị rủi ro nghiêm ngặt.

## Key Features

✅ **4 Trading Strategies**
- DCA (Dollar-Cost Averaging)
- Trend Following (MA Cross, Donchian, RSI Pullback)
- Mean Reversion (RSI, Bollinger Bands)
- Grid Trading

✅ **Risk Management**
- Per-trade risk limit (0.5% default)
- Daily loss limit (2%) → Circuit Breaker
- Weekly loss limit (5%)
- Trailing stop-loss
- Position size calculation

✅ **4 Operating Modes**
- Backtest: Historical data testing
- Testnet: Binance testnet trading
- Paper: Simulated trading with real data
- Mainnet: Real trading

✅ **Comprehensive Logging**
- Trade logs
- Error logs
- Performance metrics
- Risk alerts

✅ **Docker Support**
- Containerized deployment
- Easy configuration
- Production-ready

## Technology Stack

- **Python 3.11+**
- **python-binance**: Binance API client
- **pandas**: Data manipulation
- **pandas-ta**: Technical indicators
- **pyyaml**: Configuration
- **colorlog**: Colored logging
- **Docker**: Containerization

## Project Structure

```
binance-trading-bot/
├── src/                    # Source code
│   ├── core/              # Core components
│   ├── strategies/        # Trading strategies
│   ├── risk/              # Risk management
│   ├── indicators/        # Technical indicators
│   ├── orchestrator/      # Strategy coordination
│   ├── backtest/          # Backtesting engine
│   └── utils/             # Utilities
├── config/                # Configuration files
├── logs/                  # Log files
├── data/                  # Historical data
├── main.py               # Main entry point
├── run_backtest.py       # Backtest script
├── download_data.py      # Data download script
└── docker-compose.yml    # Docker configuration
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your settings

# 3. Download data (for backtest)
python download_data.py --symbols BTCUSDT ETHUSDT

# 4. Run backtest
python run_backtest.py

# 5. Run paper trading
TRADING_MODE=paper python main.py
```

## Documentation

- **README.md**: Complete documentation
- **QUICKSTART.md**: Quick start guide
- **ARCHITECTURE.md**: Architecture details
- **tai-lieu-chien-luoc-bot-trading-spot-binance.md**: Strategy document (Vietnamese)

## Configuration Files

- **.env**: Environment variables (API keys, mode)
- **config/config.yaml**: General settings
- **config/strategies.yaml**: Strategy parameters
- **config/risk_limits.yaml**: Risk management limits

## Safety Features

🛡️ **Circuit Breaker**: Auto-stop on excessive losses  
🛡️ **Stop Loss**: Mandatory for all positions  
🛡️ **Position Limits**: Max concurrent positions  
🛡️ **Cash Reserve**: Minimum cash requirement  
🛡️ **Risk Per Trade**: Limited to 0.5% default  

## Performance Metrics

Backtest metrics include:
- Total Return & CAGR
- Maximum Drawdown
- Sharpe Ratio
- Win Rate
- Profit Factor
- Average Win/Loss

## Deployment Options

### Local
```bash
python main.py
```

### Docker
```bash
docker-compose up -d
```

## Monitoring

- **Logs**: `logs/` directory
- **Metrics**: Portfolio statistics
- **Alerts**: Circuit breaker, errors

## Development Status

✅ Core trading engine  
✅ 4 strategies implemented  
✅ Risk management system  
✅ Backtesting engine  
✅ Docker support  
✅ Comprehensive logging  
✅ Documentation  

## Roadmap

🔲 Web dashboard  
🔲 Telegram notifications  
🔲 Database integration  
🔲 ML signal enhancement  
🔲 Multi-exchange support  

## Disclaimer

⚠️ **IMPORTANT**: This software is for educational purposes only. Cryptocurrency trading is highly risky. You may lose all invested capital. Always backtest and paper trade before using real money.

## License

MIT License - See LICENSE file

## Support

For issues or questions:
1. Check logs in `logs/`
2. Review configuration in `config/`
3. Read documentation
4. Create GitHub issue

## Author

Binance Trading Bot Team

## Last Updated

2024
