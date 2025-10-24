# Quick Start Guide

Hướng dẫn nhanh để bắt đầu sử dụng Binance Trading Bot.

## Bước 1: Cài đặt

### Option A: Cài đặt thủ công

```bash
# Clone project
cd binance-trading-bot

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Option B: Sử dụng Docker

```bash
# Build image
docker-compose build
```

## Bước 2: Cấu hình API Keys

### Tạo file .env

```bash
# Sử dụng Makefile
make setup-env

# Hoặc thủ công
cp .env.example .env
```

### Lấy Binance API Keys

**Khuyến nghị: Bắt đầu với Testnet**

#### Option A: Testnet (An toàn, miễn phí)

1. Truy cập https://testnet.binance.vision/
2. Đăng nhập bằng GitHub
3. Vào API Keys → Generate HMAC_SHA256 Key
4. Copy API Key và Secret Key
5. Paste vào `.env`:

```bash
BINANCE_TESTNET_API_KEY=your_testnet_key_here
BINANCE_TESTNET_API_SECRET=your_testnet_secret_here
TRADING_MODE=testnet
```

#### Option B: Mainnet (Thật - Cẩn thận!)

1. Đăng nhập https://www.binance.com
2. Profile → API Management
3. Create API
4. **QUAN TRỌNG**: 
   - ✅ Enable Spot Trading
   - ❌ DISABLE Withdrawals
   - ✅ Enable IP Whitelist (khuyến nghị)
5. Copy keys và paste vào `.env`:

```bash
BINANCE_API_KEY=your_real_key_here
BINANCE_API_SECRET=your_real_secret_here
TRADING_MODE=mainnet
```

**Chi tiết đầy đủ**: Xem [ENV_SETUP.md](ENV_SETUP.md)

### Test kết nối API

```bash
# Test API connection
make test-api

# Hoặc
python test_api.py
```

Nếu thành công, bạn sẽ thấy:
```
✓ ALL TESTS PASSED!
```

## Bước 3: Backtest (Khuyến nghị bắt đầu từ đây)

### Tải dữ liệu lịch sử

```bash
python download_data.py \
  --symbols BTCUSDT ETHUSDT \
  --interval 15m \
  --start 2023-01-01 \
  --end 2023-12-31
```

### Chạy backtest

```bash
python run_backtest.py \
  --capital 10000 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --symbols BTCUSDT ETHUSDT
```

### Xem kết quả

Kết quả sẽ được lưu trong thư mục `data/`:
- `backtest_results_*.json`: Metrics tổng hợp
- `equity_curve_*.csv`: Đường cong vốn
- `trades_*.csv`: Lịch sử giao dịch

## Bước 4: Paper Trading

```bash
# Cấu hình trong .env
TRADING_MODE=paper

# Chạy bot
python main.py
```

Bot sẽ:
- Kết nối Binance API để lấy dữ liệu thực
- Mô phỏng giao dịch (không đặt lệnh thật)
- Ghi log vào `logs/`

## Bước 5: Testnet (Tùy chọn)

### Lấy Testnet API Key

1. Truy cập https://testnet.binance.vision/
2. Đăng ký và tạo API key
3. Copy API key và secret vào `.env`

### Chạy trên Testnet

```bash
# Cấu hình trong .env
TRADING_MODE=testnet
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret

# Chạy bot
python main.py
```

## Bước 6: Mainnet (Thực tế)

⚠️ **CẢNH BÁO**: Chỉ thực hiện sau khi:
- Đã backtest kỹ lưỡng
- Đã chạy paper trading thành công
- Đã test trên testnet
- Hiểu rõ rủi ro

### Lấy Mainnet API Key

1. Đăng nhập Binance
2. Vào Account > API Management
3. Tạo API key mới với quyền:
   - ✅ Enable Spot & Margin Trading
   - ❌ Enable Withdrawals (KHÔNG bật)
4. Thiết lập IP whitelist (khuyến nghị)

### Chạy trên Mainnet

```bash
# Cấu hình trong .env
TRADING_MODE=mainnet
BINANCE_API_KEY=your_real_key
BINANCE_API_SECRET=your_real_secret

# BẮT ĐẦU VỚI VỐN NHỎ!
# Chạy bot
python main.py
```

## Sử dụng Docker

### Paper Trading

```bash
docker-compose up -d
docker-compose logs -f
```

### Testnet/Mainnet

```bash
# Chỉnh sửa .env trước
TRADING_MODE=testnet docker-compose up -d
# hoặc
TRADING_MODE=mainnet docker-compose up -d
```

## Giám sát

### Xem logs

```bash
# Real-time logs
tail -f logs/trading_bot.log

# Trade logs
tail -f logs/trades_*.log

# Error logs
tail -f logs/errors.log
```

### Với Docker

```bash
docker-compose logs -f trading-bot
```

## Dừng Bot

### Thủ công
```bash
# Nhấn Ctrl+C
```

### Docker
```bash
docker-compose down
```

## Điều chỉnh Chiến lược

Chỉnh sửa `config/strategies.yaml`:

```yaml
strategies:
  trend_following:
    enabled: true          # Bật/tắt
    capital_allocation: 0.30  # 30% vốn
    ma_fast: 20
    ma_slow: 50
    # ... các tham số khác
```

## Điều chỉnh Rủi Ro

Chỉnh sửa `config/risk_limits.yaml`:

```yaml
risk:
  max_risk_per_trade: 0.005  # 0.5% mỗi lệnh
  max_daily_loss: 0.02       # 2% lỗ/ngày
  max_weekly_loss: 0.05      # 5% lỗ/tuần
```

## Troubleshooting

### Lỗi "No module named 'src'"
```bash
# Đảm bảo đang ở thư mục gốc
cd binance-trading-bot
python main.py
```

### Lỗi "API key invalid"
```bash
# Kiểm tra .env
cat .env | grep API_KEY

# Đảm bảo không có khoảng trắng thừa
```

### Circuit Breaker kích hoạt
```bash
# Xem logs để biết lý do
tail -f logs/trading_bot.log

# Đợi cooldown period (24h mặc định)
# Hoặc điều chỉnh risk_limits.yaml
```

## Các lệnh hữu ích

```bash
# Xem tất cả lệnh có sẵn
make help

# Cài đặt dependencies
make install

# Chạy bot
make run

# Chạy backtest
make backtest

# Tải dữ liệu
make download-data

# Build Docker
make docker-build

# Chạy Docker
make docker-run

# Dừng Docker
make docker-stop

# Xem logs Docker
make docker-logs

# Dọn dẹp
make clean
```

## Next Steps

1. ✅ Chạy backtest với nhiều khoảng thời gian khác nhau
2. ✅ Điều chỉnh tham số chiến lược dựa trên kết quả backtest
3. ✅ Chạy paper trading ít nhất 1-2 tuần
4. ✅ Kiểm tra logs thường xuyên
5. ✅ Bắt đầu với vốn nhỏ trên mainnet
6. ✅ Tăng dần vốn khi đã ổn định

## Tài liệu thêm

- [README.md](README.md): Tài liệu đầy đủ
- [Tài liệu chiến lược](tai-lieu-chien-luoc-bot-trading-spot-binance.md): Chi tiết chiến lược
- Logs: `logs/` directory
- Config: `config/` directory

## Support

Nếu gặp vấn đề:
1. Kiểm tra logs
2. Xem lại cấu hình
3. Tạo issue trên GitHub

