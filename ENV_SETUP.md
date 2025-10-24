# Environment Setup Guide

Hướng dẫn chi tiết cách cấu hình API keys và environment variables cho Binance Trading Bot.

## Bước 1: Tạo file .env

```bash
# Copy file mẫu
cp .env.example .env
```

## Bước 2: Lấy Binance API Keys

### Option A: Testnet (Khuyến nghị cho người mới)

Testnet cho phép bạn test bot với tiền ảo, hoàn toàn miễn phí và an toàn.

**Các bước:**

1. Truy cập https://testnet.binance.vision/
2. Click "GitHub" để đăng nhập bằng GitHub account
3. Sau khi đăng nhập, click vào email/username ở góc phải
4. Chọn "API Keys"
5. Click "Generate HMAC_SHA256 Key"
6. Đặt tên cho API key (ví dụ: "TradingBot")
7. Copy **API Key** và **Secret Key**
8. Paste vào file `.env`:

```bash
BINANCE_TESTNET_API_KEY=your_copied_api_key
BINANCE_TESTNET_API_SECRET=your_copied_secret_key
TRADING_MODE=testnet
```

**Lưu ý Testnet:**
- Testnet cung cấp tiền ảo miễn phí để test
- Không cần KYC
- Dữ liệu thị trường giống mainnet nhưng có thể có độ trễ
- Hoàn hảo để test bot trước khi dùng tiền thật

### Option B: Mainnet (Giao dịch thật - CẨN THẬN!)

⚠️ **CHỈ SỬ DỤNG SAU KHI ĐÃ TEST KỸ TRÊN TESTNET!**

**Các bước:**

1. Đăng nhập vào https://www.binance.com
2. Hover vào icon profile (góc phải) → "API Management"
3. Nhập label cho API key (ví dụ: "TradingBot")
4. Click "Create API"
5. Xác thực bằng 2FA/Email
6. **QUAN TRỌNG**: Cấu hình quyền:
   - ✅ **Enable Spot & Margin Trading** (Bật)
   - ❌ **Enable Withdrawals** (TẮT - rất quan trọng!)
   - ❌ **Enable Futures** (Tắt nếu không dùng)
7. **IP Whitelist** (Khuyến nghị):
   - Click "Edit restrictions"
   - Chọn "Restrict access to trusted IPs only"
   - Thêm IP của server/máy tính chạy bot
   - Để trống nếu IP động (ít an toàn hơn)
8. Copy **API Key** và **Secret Key**
9. Paste vào file `.env`:

```bash
BINANCE_API_KEY=your_copied_api_key
BINANCE_API_SECRET=your_copied_secret_key
TRADING_MODE=mainnet
```

**Lưu ý Mainnet:**
- Đây là giao dịch thật với tiền thật
- Bắt đầu với số vốn nhỏ
- Luôn bật IP whitelist nếu có thể
- KHÔNG BAO GIỜ bật quyền Withdrawals
- Theo dõi bot thường xuyên

## Bước 3: Cấu hình Trading Mode

File `.env` hỗ trợ 4 modes:

### 1. Backtest Mode (Không cần API key)

```bash
TRADING_MODE=backtest
```

- Test chiến lược với dữ liệu lịch sử
- Không cần API keys
- Cần download dữ liệu trước: `python download_data.py`

### 2. Paper Trading Mode (Chỉ cần API key để lấy dữ liệu)

```bash
TRADING_MODE=paper
BINANCE_API_KEY=your_key  # Hoặc testnet key
BINANCE_API_SECRET=your_secret
```

- Mô phỏng giao dịch với dữ liệu thực
- Không đặt lệnh thật
- An toàn để test logic

### 3. Testnet Mode

```bash
TRADING_MODE=testnet
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret
```

- Giao dịch trên testnet với tiền ảo
- Đặt lệnh thật nhưng không mất tiền
- Giống mainnet nhất

### 4. Mainnet Mode (THẬT!)

```bash
TRADING_MODE=mainnet
BINANCE_API_KEY=your_real_key
BINANCE_API_SECRET=your_real_secret
```

- Giao dịch thật với tiền thật
- Chỉ dùng sau khi test kỹ
- Bắt đầu với vốn nhỏ

## Bước 4: Cấu hình Risk Management

Điều chỉnh các giới hạn rủi ro trong `.env`:

```bash
# Rủi ro tối đa mỗi lệnh (0.5% = 0.005)
MAX_RISK_PER_TRADE=0.005

# Lỗ tối đa trong ngày (2% = 0.02)
MAX_DAILY_LOSS=0.02

# Lỗ tối đa trong tuần (5% = 0.05)
MAX_WEEKLY_LOSS=0.05

# Dự trữ tiền mặt tối thiểu (30% = 0.30)
MIN_CASH_RESERVE=0.30

# Số lệnh đồng thời tối đa
MAX_POSITIONS=7

# Số chiến lược tối đa cho 1 cặp
MAX_STRATEGIES_PER_PAIR=2
```

**Khuyến nghị cho người mới:**
- Giữ nguyên giá trị mặc định
- Giảm `MAX_RISK_PER_TRADE` xuống 0.002 (0.2%) nếu muốn an toàn hơn
- Tăng `MIN_CASH_RESERVE` lên 0.40 (40%) nếu muốn bảo thủ hơn

## Bước 5: Kiểm tra cấu hình

### Test kết nối API

Tạo file `test_api.py`:

```python
from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

mode = os.getenv('TRADING_MODE')
print(f"Testing {mode} mode...")

if mode == 'testnet':
    api_key = os.getenv('BINANCE_TESTNET_API_KEY')
    api_secret = os.getenv('BINANCE_TESTNET_API_SECRET')
    client = Client(api_key, api_secret, testnet=True)
elif mode == 'mainnet':
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
else:
    print("Backtest/Paper mode - no API test needed")
    exit(0)

# Test connection
try:
    account = client.get_account()
    print("✓ API connection successful!")
    print(f"Account status: {account['accountType']}")
    
    # Show balances
    balances = {b['asset']: b['free'] for b in account['balances'] if float(b['free']) > 0}
    print(f"Balances: {balances}")
except Exception as e:
    print(f"✗ API connection failed: {e}")
```

Chạy test:

```bash
python test_api.py
```

## Bước 6: Bảo mật

### ✅ Checklist Bảo mật

- [ ] File `.env` đã được thêm vào `.gitignore`
- [ ] KHÔNG commit API keys vào Git
- [ ] Đã TẮT quyền Withdrawals trên Binance
- [ ] Đã bật IP whitelist (nếu có IP tĩnh)
- [ ] API keys được lưu an toàn
- [ ] Sử dụng API keys riêng cho bot (không dùng chung)
- [ ] Thường xuyên kiểm tra hoạt động API trên Binance

### 🔒 Best Practices

1. **Tách API keys**: Dùng API key riêng cho bot, không dùng chung với trading thủ công
2. **Rotate keys**: Thay đổi API keys định kỳ (mỗi 3-6 tháng)
3. **Monitor activity**: Kiểm tra API activity trên Binance thường xuyên
4. **Backup .env**: Lưu file `.env` an toàn, không để public
5. **Use testnet first**: Luôn test trên testnet trước khi dùng mainnet

## Bước 7: Chạy Bot

Sau khi cấu hình xong:

```bash
# Kiểm tra cấu hình
cat .env | grep TRADING_MODE

# Chạy bot
python main.py

# Hoặc với Docker
docker-compose up -d
```

## Troubleshooting

### Lỗi "API key invalid"

```
Error: Invalid API-key, IP, or permissions for action
```

**Giải pháp:**
1. Kiểm tra API key và secret đã copy đúng chưa
2. Kiểm tra không có khoảng trắng thừa trong `.env`
3. Kiểm tra đã bật quyền "Spot Trading" chưa
4. Nếu dùng IP whitelist, kiểm tra IP hiện tại

### Lỗi "Timestamp for this request"

```
Error: Timestamp for this request is outside of the recvWindow
```

**Giải pháp:**
1. Đồng bộ thời gian hệ thống:
   ```bash
   # Linux/Mac
   sudo ntpdate -s time.nist.gov
   
   # Windows: Settings → Time & Language → Sync now
   ```

### Lỗi "IP not whitelisted"

```
Error: This IP cannot use this key
```

**Giải pháp:**
1. Thêm IP hiện tại vào whitelist trên Binance
2. Hoặc tắt IP whitelist (ít an toàn hơn)

### File .env không được load

```
Error: BINANCE_API_KEY not found
```

**Giải pháp:**
1. Kiểm tra file `.env` có trong thư mục gốc không
2. Cài đặt python-dotenv: `pip install python-dotenv`
3. Kiểm tra tên biến trong `.env` (không có khoảng trắng)

## Tài liệu tham khảo

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [Binance Testnet](https://testnet.binance.vision/)
- [python-binance Documentation](https://python-binance.readthedocs.io/)

## Support

Nếu gặp vấn đề:
1. Kiểm tra logs: `tail -f logs/trading_bot.log`
2. Xem lại file `.env`
3. Test API connection với script trên
4. Tạo issue trên GitHub

