# Binance Trading Bot

Hệ thống giao dịch tự động đa chiến lược trên Binance Spot với trọng tâm bảo toàn vốn và quản trị rủi ro nghiêm ngặt.

## Tính năng

### Chiến lược giao dịch
- **DCA (Dollar-Cost Averaging)**: Tích lũy phân lớp có kiểm soát
- **Trend Following**: Bắt theo xu hướng với MA Cross, Donchian Breakout
- **Mean Reversion**: Kiếm lợi trong thị trường đi ngang với RSI/Bollinger
- **Grid Trading**: Khai thác dao động trong biên giá

### Quản trị rủi ro
- Giới hạn rủi ro mỗi lệnh: 0.5% vốn
- Giới hạn lỗ ngày: 2% → Circuit Breaker
- Giới hạn lỗ tuần: 5% → Ngừng giao dịch
- Dự trữ tiền mặt tối thiểu: 30%
- Trailing Stop-Loss theo ATR

### Chế độ hoạt động
- **Backtest**: Kiểm thử trên dữ liệu lịch sử
- **Testnet**: Giao dịch thử nghiệm trên Binance Testnet
- **Paper**: Giao dịch giả lập với dữ liệu thực
- **Mainnet**: Giao dịch thực với vốn thật

### Hệ thống logging
- Log chi tiết mọi quyết định giao dịch
- Log đặt lệnh và thực thi
- Log PnL theo chiến lược
- Log cảnh báo rủi ro và lỗi hệ thống

## Cài đặt

### Yêu cầu
- Python 3.11+
- Docker & Docker Compose (tùy chọn)
- Binance API Key (cho testnet/mainnet)

### Cài đặt thủ công

```bash
# Clone repository
git clone <repository-url>
cd binance-trading-bot

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Copy và cấu hình environment variables
cp .env.example .env
# Chỉnh sửa .env với API keys của bạn
```

### Cài đặt với Docker

```bash
# Build image
docker-compose build

# Chạy bot
docker-compose up -d

# Xem logs
docker-compose logs -f
```

## Cấu hình

### 1. Environment Variables (.env)

```bash
# Binance API Keys
BINANCE_API_KEY=your_mainnet_api_key
BINANCE_API_SECRET=your_mainnet_api_secret
BINANCE_TESTNET_API_KEY=your_testnet_api_key
BINANCE_TESTNET_API_SECRET=your_testnet_api_secret

# Trading Mode
TRADING_MODE=paper  # backtest, testnet, paper, mainnet

# Risk Management
MAX_RISK_PER_TRADE=0.005
MAX_DAILY_LOSS=0.02
MAX_WEEKLY_LOSS=0.05
MIN_CASH_RESERVE=0.30
```

### 2. Cấu hình chiến lược (config/strategies.yaml)

Điều chỉnh tham số cho từng chiến lược:
- Bật/tắt chiến lược
- Phân bổ vốn
- Tham số kỹ thuật (MA, RSI, ATR, etc.)

### 3. Cấu hình rủi ro (config/risk_limits.yaml)

Thiết lập hạn mức rủi ro:
- Rủi ro mỗi lệnh
- Lỗ tối đa ngày/tuần
- Số lệnh đồng thời
- Circuit breaker

## Sử dụng

### Chạy Backtest

```bash
# Backtest với dữ liệu mặc định
python run_backtest.py

# Backtest với tham số tùy chỉnh
python run_backtest.py \
  --capital 10000 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --symbols BTCUSDT ETHUSDT
```

**Lưu ý**: Cần chuẩn bị dữ liệu lịch sử ở định dạng CSV trong thư mục `data/`:
- `data/BTCUSDT_15m.csv`
- `data/ETHUSDT_15m.csv`

### Chạy Paper Trading

```bash
# Cấu hình mode trong .env
TRADING_MODE=paper

# Chạy bot
python main.py
```

### Chạy Testnet

```bash
# Cấu hình mode và API keys trong .env
TRADING_MODE=testnet
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret

# Chạy bot
python main.py
```

### Chạy Mainnet (Thực tế)

⚠️ **CẢNH BÁO**: Chỉ sử dụng sau khi đã kiểm thử kỹ lưỡng!

```bash
# Cấu hình mode và API keys trong .env
TRADING_MODE=mainnet
BINANCE_API_KEY=your_real_api_key
BINANCE_API_SECRET=your_real_api_secret

# Chạy bot
python main.py
```

### Chạy với Docker

```bash
# Paper mode (mặc định)
docker-compose up -d

# Testnet mode
TRADING_MODE=testnet docker-compose up -d

# Mainnet mode
TRADING_MODE=mainnet docker-compose up -d

# Xem logs
docker-compose logs -f trading-bot

# Dừng bot
docker-compose down
```

## Cấu trúc thư mục

```
binance-trading-bot/
├── src/
│   ├── core/              # Core components
│   │   ├── exchange.py    # Binance API wrapper
│   │   └── portfolio.py   # Portfolio management
│   ├── strategies/        # Trading strategies
│   │   ├── dca_strategy.py
│   │   ├── trend_following.py
│   │   ├── mean_reversion.py
│   │   └── grid_strategy.py
│   ├── risk/              # Risk management
│   │   └── risk_manager.py
│   ├── indicators/        # Technical indicators
│   │   └── technical.py
│   ├── orchestrator/      # Strategy coordination
│   │   └── strategy_orchestrator.py
│   ├── backtest/          # Backtesting engine
│   │   └── backtester.py
│   └── utils/             # Utilities
│       ├── logger.py
│       └── config.py
├── config/                # Configuration files
│   ├── config.yaml
│   ├── strategies.yaml
│   └── risk_limits.yaml
├── logs/                  # Log files
├── data/                  # Historical data & results
├── main.py               # Main entry point
├── run_backtest.py       # Backtest script
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Logs

Hệ thống tạo các file log sau:

- `logs/trading_bot.log`: Log tổng hợp
- `logs/trades_YYYYMMDD.log`: Log giao dịch theo ngày
- `logs/errors.log`: Log lỗi

## Giám sát

### Kiểm tra trạng thái

```python
# Trong code hoặc console
from src.core.portfolio import Portfolio
from src.risk.risk_manager import RiskManager

# Xem portfolio stats
stats = portfolio.get_statistics()
print(stats)

# Xem risk metrics
risk_metrics = risk_manager.get_risk_metrics()
print(risk_metrics)
```

### Metrics quan trọng

- **Equity**: Tổng giá trị danh mục
- **Daily PnL**: Lãi/lỗ trong ngày
- **Win Rate**: Tỷ lệ thắng
- **Circuit Breaker Status**: Trạng thái ngắt mạch
- **Cash Reserve**: Dự trữ tiền mặt

## An toàn & Bảo mật

### API Key Security
- ✅ Chỉ cấp quyền Spot Trading (không Withdraw)
- ✅ Sử dụng IP whitelist nếu có thể
- ✅ Không commit API keys vào Git
- ✅ Sử dụng environment variables

### Risk Controls
- ✅ Circuit breaker tự động
- ✅ Giới hạn rủi ro mỗi lệnh
- ✅ Stop-loss bắt buộc
- ✅ Giới hạn số lệnh đồng thời

### Best Practices
1. **Luôn backtest trước**: Kiểm thử chiến lược với dữ liệu lịch sử
2. **Bắt đầu với testnet**: Thử nghiệm với tiền ảo
3. **Paper trading**: Chạy giả lập với dữ liệu thực
4. **Bắt đầu nhỏ**: Dùng vốn nhỏ khi chuyển sang mainnet
5. **Giám sát thường xuyên**: Theo dõi logs và metrics
6. **Cập nhật tham số**: Điều chỉnh dựa trên kết quả thực tế

## Troubleshooting

### Lỗi kết nối API
```
Error: Unable to connect to Binance API
```
- Kiểm tra API key và secret
- Kiểm tra kết nối internet
- Kiểm tra IP whitelist (nếu có)

### Circuit Breaker kích hoạt
```
Circuit breaker activated
```
- Kiểm tra lỗ ngày/tuần
- Xem lại các giao dịch gần đây
- Đợi cooldown period hết

### Insufficient balance
```
Insufficient cash to open position
```
- Kiểm tra cash reserve setting
- Giảm position size
- Đóng một số positions

## Disclaimer

⚠️ **QUAN TRỌNG**: 

- Hệ thống này chỉ nhằm mục đích nghiên cứu và giáo dục
- Giao dịch tiền mã hóa có rủi ro cao
- Bạn có thể mất toàn bộ vốn đầu tư
- Luôn backtest và paper trade trước khi dùng vốn thật
- Tác giả không chịu trách nhiệm về mọi tổn thất

## License

MIT License - Xem file LICENSE để biết chi tiết

## Support

Nếu gặp vấn đề hoặc có câu hỏi:
1. Kiểm tra logs trong thư mục `logs/`
2. Xem lại cấu hình trong `config/`
3. Tạo issue trên GitHub

## Roadmap

- [ ] Thêm Telegram notifications
- [ ] Web dashboard để giám sát
- [ ] Thêm chiến lược arbitrage
- [ ] Hỗ trợ futures trading
- [ ] Machine learning signal enhancement
- [ ] Backtesting optimization với walk-forward analysis

