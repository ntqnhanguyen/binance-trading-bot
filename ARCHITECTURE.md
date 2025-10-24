# Architecture Documentation

## Tổng quan kiến trúc

Binance Trading Bot được thiết kế theo kiến trúc modular với các thành phần độc lập, dễ bảo trì và mở rộng.

## Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Entry Point                      │
│                          (main.py)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Trading Bot Core                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Exchange   │  │  Portfolio   │  │ Risk Manager │      │
│  │   Wrapper    │  │  Management  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Strategy Orchestrator                       │
│         (Điều phối chiến lược theo thứ tự ưu tiên)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     DCA      │    │    Trend     │    │     Mean     │
│   Strategy   │    │  Following   │    │  Reversion   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Technical Indicators                        │
│         (ATR, ADX, MA, RSI, Bollinger, etc.)                │
└─────────────────────────────────────────────────────────────┘
```

## Các thành phần chính

### 1. Core Components (`src/core/`)

#### Exchange Wrapper (`exchange.py`)
- **Mục đích**: Giao tiếp với Binance API
- **Chức năng**:
  - Kết nối API (mainnet/testnet)
  - Lấy dữ liệu thị trường (klines, ticker)
  - Đặt/hủy lệnh
  - Quản lý account balance
- **Modes**:
  - `backtest`: Không kết nối API
  - `paper`: Kết nối API, không đặt lệnh thật
  - `testnet`: Kết nối Testnet API
  - `mainnet`: Kết nối API thật

#### Portfolio Manager (`portfolio.py`)
- **Mục đích**: Quản lý vị thế và vốn
- **Chức năng**:
  - Theo dõi positions
  - Tính toán PnL
  - Quản lý cash/equity
  - Lưu trade history
- **Classes**:
  - `Position`: Đại diện cho một vị thế
  - `Portfolio`: Quản lý tất cả positions

### 2. Risk Management (`src/risk/`)

#### Risk Manager (`risk_manager.py`)
- **Mục đích**: Quản trị rủi ro và bảo vệ vốn
- **Chức năng**:
  - Tính toán position size
  - Kiểm tra risk limits
  - Circuit breaker
  - Stop-loss/Take-profit calculation
  - Trailing stop management
- **Risk Controls**:
  - Per-trade risk limit
  - Daily/weekly loss limits
  - Maximum positions
  - Minimum cash reserve
  - Correlation risk

### 3. Strategies (`src/strategies/`)

#### Base Strategy (`base_strategy.py`)
- **Mục đích**: Abstract base class cho tất cả strategies
- **Interface**:
  - `generate_signal()`: Tạo tín hiệu giao dịch
  - `should_exit()`: Kiểm tra điều kiện thoát
  - `execute_signal()`: Thực thi tín hiệu
  - `update_stops()`: Cập nhật stop-loss/take-profit

#### DCA Strategy (`dca_strategy.py`)
- **Logic**: Tích lũy phân lớp theo giá giảm hoặc thời gian
- **Entry**: Thêm lớp khi giá giảm X%
- **Exit**: TP ladder hoặc catastrophic SL
- **Parameters**:
  - `max_layers`: Số lớp tối đa
  - `layer_drop_pct`: % giảm để thêm lớp
  - `tp_ladder_pct`: % lợi nhuận cho TP

#### Trend Following (`trend_following.py`)
- **Logic**: Bắt theo xu hướng trung-dài hạn
- **Entry Methods**:
  - MA Cross: MA nhanh cắt MA chậm
  - Donchian Breakout: Phá vỡ kênh
  - RSI Pullback: Hồi về trong uptrend
- **Exit**: MA reversal, ADX giảm
- **Parameters**:
  - `ma_fast/slow`: Chu kỳ MA
  - `adx_threshold`: Ngưỡng xác nhận trend
  - `atr_multiplier`: Hệ số ATR cho SL

#### Mean Reversion (`mean_reversion.py`)
- **Logic**: Mua thấp bán cao trong range
- **Entry Methods**:
  - RSI oversold/overbought
  - Bollinger Bands touch
  - Combined (cả hai)
- **Exit**: Về midline, RSI opposite extreme
- **Conditions**: Chỉ hoạt động khi ADX thấp (ranging)

#### Grid Strategy (`grid_strategy.py`)
- **Logic**: Đặt lưới lệnh trong range
- **Setup**: Xác định range bằng Bollinger/ATR
- **Execution**: Mua ở grid levels, bán khi lên
- **Safety**: Catastrophic SL khi breakout

### 4. Orchestrator (`src/orchestrator/`)

#### Strategy Orchestrator (`strategy_orchestrator.py`)
- **Mục đích**: Điều phối đa chiến lược
- **Workflow**:
  1. Kiểm tra system safety (circuit breaker)
  2. Phân tích market regime
  3. Điều chỉnh capital allocation
  4. Ưu tiên exit signals
  5. Generate entry signals (theo priority)
  6. Resolve conflicts
  7. Update trailing stops

- **Priority System**:
  1. Exit/Reduce risk (highest)
  2. Trend Following
  3. Mean Reversion
  4. Grid
  5. DCA (lowest)

- **Market Regime Detection**:
  - `trending_high_vol`: Tăng trend, giảm grid/mean rev
  - `trending_low_vol`: Tăng trend
  - `ranging_high_vol`: Giảm tất cả
  - `ranging_low_vol`: Tăng grid/mean rev

### 5. Indicators (`src/indicators/`)

#### Technical Indicators (`technical.py`)
- **Trend**: MA, EMA, MACD
- **Momentum**: RSI, Stochastic
- **Volatility**: ATR, Bollinger Bands
- **Trend Strength**: ADX
- **Channels**: Donchian
- **Support/Resistance**: Detection algorithms

### 6. Backtest (`src/backtest/`)

#### Backtester (`backtester.py`)
- **Mục đích**: Kiểm thử chiến lược trên dữ liệu lịch sử
- **Features**:
  - Load historical data
  - Simulate trading
  - Calculate performance metrics
  - Generate reports
- **Metrics**:
  - Total Return, CAGR
  - Max Drawdown
  - Sharpe Ratio
  - Win Rate, Profit Factor

### 7. Utilities (`src/utils/`)

#### Logger (`logger.py`)
- **Features**:
  - Colored console output
  - File logging with rotation
  - Separate logs for trades/errors
  - Structured logging functions

#### Config (`config.py`)
- **Features**:
  - YAML config loading
  - Environment variable management
  - Strategy config access
  - Risk limits access

## Data Flow

### 1. Trading Loop Flow

```
Start
  │
  ▼
Get Market Data (OHLCV)
  │
  ▼
Add Technical Indicators
  │
  ▼
Orchestrator.process_symbol()
  │
  ├─► Check Circuit Breaker
  │
  ├─► Analyze Market Regime
  │
  ├─► Adjust Strategy Allocations
  │
  ├─► Check Exit Conditions (Priority 1)
  │   └─► If exits → Execute & Return
  │
  ├─► Generate Entry Signals (by priority)
  │
  ├─► Resolve Conflicts
  │
  └─► Update Trailing Stops
  │
  ▼
Execute Signals
  │
  ├─► Check Risk Limits
  │
  ├─► Calculate Position Size
  │
  ├─► Place Order (if allowed)
  │
  └─► Update Portfolio
  │
  ▼
Log Results
  │
  ▼
Sleep (interval)
  │
  └─► Loop
```

### 2. Signal Generation Flow

```
Strategy.generate_signal()
  │
  ├─► Check if already have position
  │   └─► If yes → Return None
  │
  ├─► Check market conditions
  │   └─► If not suitable → Return None
  │
  ├─► Calculate indicators
  │
  ├─► Check entry conditions
  │   └─► If not met → Return None
  │
  ├─► Calculate SL/TP
  │
  ├─► Calculate position size
  │
  └─► Return Signal
```

### 3. Risk Check Flow

```
RiskManager.check_trade_allowed()
  │
  ├─► Check Circuit Breaker
  │   └─► If active → Reject
  │
  ├─► Check Daily Loss Limit
  │   └─► If exceeded → Activate CB & Reject
  │
  ├─► Check Weekly Loss Limit
  │   └─► If exceeded → Activate CB & Reject
  │
  ├─► Check Max Positions
  │   └─► If at limit → Reject
  │
  ├─► Check Strategies per Pair
  │   └─► If at limit → Reject
  │
  ├─► Check Cash Reserve
  │   └─► If insufficient → Reject
  │
  └─► Allow Trade
```

## Configuration System

### Hierarchy
1. **Environment Variables** (.env)
   - API credentials
   - Trading mode
   - Override risk limits

2. **YAML Configs** (config/)
   - `config.yaml`: General settings
   - `strategies.yaml`: Strategy parameters
   - `risk_limits.yaml`: Risk management

3. **Code Defaults**
   - Fallback values in code

### Priority
Environment Variables > YAML Config > Code Defaults

## Logging System

### Log Levels
- **DEBUG**: Detailed diagnostic info
- **INFO**: General operational info
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical failures

### Log Files
- `trading_bot.log`: All logs
- `trades_YYYYMMDD.log`: Trade-specific logs
- `errors.log`: Error logs only

### Log Format
```
YYYY-MM-DD HH:MM:SS - module_name - LEVEL - message
```

## Extensibility

### Adding New Strategy

1. Create new file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `generate_signal()`
   - `should_exit()`
4. Add config to `config/strategies.yaml`
5. Register in `main.py` or orchestrator

### Adding New Indicator

1. Add static method to `TechnicalIndicators` class
2. Use pandas-ta or implement custom logic
3. Return pandas Series or DataFrame

### Adding New Risk Control

1. Add method to `RiskManager`
2. Call in `check_trade_allowed()`
3. Add config to `risk_limits.yaml`

## Performance Considerations

### Optimization Points
- **Indicator Calculation**: Cache results, avoid recalculation
- **Data Fetching**: Batch requests, use appropriate intervals
- **Position Tracking**: In-memory, minimal DB access
- **Logging**: Async logging for high-frequency

### Scalability
- **Horizontal**: Run multiple instances for different symbols
- **Vertical**: Optimize indicator calculations
- **Data**: Use time-series database for large datasets

## Security Considerations

### API Security
- Never commit API keys
- Use environment variables
- Restrict API permissions
- Enable IP whitelist

### Code Security
- Input validation
- Error handling
- No hardcoded secrets
- Secure configuration management

## Testing Strategy

### Unit Tests
- Test individual components
- Mock external dependencies
- Test edge cases

### Integration Tests
- Test component interactions
- Test with sample data
- Test error scenarios

### Backtest
- Historical data validation
- Strategy performance
- Risk control verification

### Paper Trading
- Real-time data testing
- Order simulation
- System stability

## Deployment

### Development
```bash
python main.py
```

### Production (Docker)
```bash
docker-compose up -d
```

### Monitoring
- Check logs regularly
- Monitor circuit breaker status
- Track PnL and drawdown
- Alert on errors

## Future Enhancements

1. **Web Dashboard**: Real-time monitoring UI
2. **Telegram Bot**: Notifications and control
3. **Database**: Persistent storage for trades
4. **ML Integration**: Signal enhancement
5. **Multi-Exchange**: Support other exchanges
6. **Advanced Orders**: OCO, trailing orders
7. **Portfolio Optimization**: Dynamic allocation
8. **Backtesting Improvements**: Walk-forward analysis

