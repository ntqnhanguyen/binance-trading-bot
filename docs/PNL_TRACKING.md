# Improved PnL Tracking & Trade Export

Hệ thống theo dõi PnL và xuất dữ liệu giao dịch đã được cải tiến với nhiều tính năng mới.

## Tính năng mới

### 1. Order Type Tracking (BUY/SELL)

Mỗi giao dịch giờ đây được ghi nhận với **order_type** rõ ràng:
- **BUY**: Mua vào (LONG entry hoặc SHORT exit)
- **SELL**: Bán ra (LONG exit hoặc SHORT entry)

### 2. Action Tracking (OPEN/CLOSE)

Phân biệt rõ ràng giữa:
- **OPEN**: Mở vị thế mới
- **CLOSE**: Đóng vị thế

### 3. Enhanced Trade Records

Mỗi trade record bao gồm:

```python
{
    'timestamp': '2025-10-24 13:39:47.369586',
    'symbol': 'BTCUSDT',
    'strategy': 'TrendFollowing',
    'action': 'OPEN',           # OPEN or CLOSE
    'order_type': 'BUY',        # BUY or SELL
    'side': 'LONG',             # LONG or SHORT
    'price': 50000.0,
    'quantity': 0.1,
    'value': 5000.0,            # Total value
    'pnl': 0.0,                 # Profit/Loss
    'pnl_pct': 0.0,             # PnL percentage
    'cumulative_pnl': 0.0,      # Running total PnL
    'cash_after': 5000.0,       # Cash balance after trade
    'entry_price': None,        # For CLOSE actions
    'entry_value': None,        # For CLOSE actions
    'win': None                 # 1 for win, 0 for loss
}
```

### 4. CSV Export Format

File CSV xuất ra có cấu trúc rõ ràng:

```csv
timestamp,symbol,strategy,action,order_type,side,price,quantity,value,pnl,pnl_pct,cumulative_pnl,cash_after,entry_price,entry_value,win
2025-10-24 13:39:47.369586,BTCUSDT,TrendFollowing,OPEN,BUY,LONG,50000.0,0.1,5000.0,0.0,0.0,0.0,5000.0,,,
2025-10-24 13:39:47.370067,BTCUSDT,TrendFollowing,CLOSE,SELL,LONG,52000.0,0.1,5200.0,200.0,4.0,200.0,10200.0,50000.0,5000.0,1.0
```

### 5. Trade Summary Report

Tự động tạo file summary với thống kê chi tiết:

```
============================================================
TRADE SUMMARY REPORT
============================================================

Generated: 2025-10-24 13:39:47

Orders:
  Total Orders:  4
  Open Orders:   2
  Close Orders:  2

Performance:
  Total PnL:     $450.0000
  Total Volume:  $19,950.0000

Trades:
  Winning:       2
  Losing:        0
  Win Rate:      100.00%

PnL Stats:
  Avg Win:       $225.0000
  Avg Loss:      $0.0000
  Best Trade:    $250.0000
  Worst Trade:   $200.0000
  Profit Factor: 0.00
============================================================
```

## Sử dụng

### 1. Trong Backtest

```python
from src.backtest.backtester import Backtester
from src.utils.trade_exporter import TradeExporter

# Chạy backtest
backtester = Backtester(...)
backtester.run(...)

# Export trades
trade_history = backtester.portfolio.trade_history
TradeExporter.export_detailed_report(trade_history, './data/backtest_20241024')

# Print summary
TradeExporter.print_trade_summary(trade_history)
```

Files được tạo:
- `./data/backtest_20241024_trades.csv` - Chi tiết từng giao dịch
- `./data/backtest_20241024_summary.txt` - Tóm tắt thống kê

### 2. Trong Live Trading

```python
from src.core.portfolio import Portfolio
from src.utils.trade_exporter import TradeExporter

# Portfolio tự động track trades
portfolio = Portfolio(initial_capital=10000)

# Mở vị thế
portfolio.open_position('BTCUSDT', 'LONG', 0.1, 50000.0, 'TrendFollowing')

# Đóng vị thế
portfolio.close_position('BTCUSDT', 'TrendFollowing', 52000.0)

# Export khi cần
TradeExporter.export_detailed_report(
    portfolio.trade_history,
    './data/live_trades_20241024'
)
```

### 3. Phân tích Trades

```python
from src.utils.trade_exporter import TradeExporter

# Get formatted DataFrame
df = TradeExporter.format_trades_df(trade_history)

# Filter chỉ CLOSE trades
closed_trades = df[df['action'] == 'CLOSE']

# Phân tích theo strategy
strategy_pnl = closed_trades.groupby('strategy')['pnl'].sum()

# Phân tích theo symbol
symbol_pnl = closed_trades.groupby('symbol')['pnl'].sum()

# Get summary statistics
summary = TradeExporter.get_trade_summary(trade_history)
print(f"Win Rate: {summary['win_rate']:.2f}%")
print(f"Total PnL: ${summary['total_pnl']:,.2f}")
```

## CSV Columns Explained

| Column | Description | Example |
|--------|-------------|---------|
| `timestamp` | Thời gian giao dịch | 2025-10-24 13:39:47.369586 |
| `symbol` | Cặp giao dịch | BTCUSDT |
| `strategy` | Chiến lược | TrendFollowing |
| `action` | Hành động | OPEN / CLOSE |
| `order_type` | Loại lệnh | BUY / SELL |
| `side` | Hướng vị thế | LONG / SHORT |
| `price` | Giá thực hiện | 50000.0 |
| `quantity` | Số lượng | 0.1 |
| `value` | Giá trị giao dịch | 5000.0 |
| `pnl` | Lãi/lỗ (chỉ CLOSE) | 200.0 |
| `pnl_pct` | % lãi/lỗ (chỉ CLOSE) | 4.0 |
| `cumulative_pnl` | Tổng PnL tích lũy | 200.0 |
| `cash_after` | Tiền mặt sau giao dịch | 10200.0 |
| `entry_price` | Giá vào (chỉ CLOSE) | 50000.0 |
| `entry_value` | Giá trị vào (chỉ CLOSE) | 5000.0 |
| `win` | Win/Loss flag (chỉ CLOSE) | 1.0 / 0.0 |

## Order Type Logic

### LONG Position
- **OPEN**: `order_type = BUY` (mua vào)
- **CLOSE**: `order_type = SELL` (bán ra)

### SHORT Position
- **OPEN**: `order_type = SELL` (bán khống)
- **CLOSE**: `order_type = BUY` (mua đóng)

## Examples

### Example 1: LONG Trade

```
# OPEN LONG
timestamp: 2025-10-24 13:39:47
symbol: BTCUSDT
action: OPEN
order_type: BUY      ← Mua vào
side: LONG
price: 50000.0
quantity: 0.1
value: 5000.0
pnl: 0.0

# CLOSE LONG
timestamp: 2025-10-24 13:40:15
symbol: BTCUSDT
action: CLOSE
order_type: SELL     ← Bán ra
side: LONG
price: 52000.0
quantity: 0.1
value: 5200.0
pnl: 200.0           ← Lãi $200
pnl_pct: 4.0         ← +4%
```

### Example 2: SHORT Trade

```
# OPEN SHORT
timestamp: 2025-10-24 13:41:00
symbol: SOLUSDT
action: OPEN
order_type: SELL     ← Bán khống
side: SHORT
price: 100.0
quantity: 50.0
value: 5000.0
pnl: 0.0

# CLOSE SHORT
timestamp: 2025-10-24 13:42:30
symbol: SOLUSDT
action: CLOSE
order_type: BUY      ← Mua đóng
side: SHORT
price: 95.0
quantity: 50.0
value: 4750.0
pnl: 250.0           ← Lãi $250
pnl_pct: 5.0         ← +5%
```

## Testing

Chạy test script để xem demo:

```bash
python test_pnl_tracking.py
```

Output:
- Console: Trade summary và statistics
- Files: 
  - `./data/test_pnl_tracking_trades.csv`
  - `./data/test_pnl_tracking_summary.txt`

## Integration

### Backtest
- Tự động export khi backtest hoàn thành
- Files: `./data/backtest_{timestamp}_trades.csv`

### Live Trading
- Export khi bot dừng
- Files: `./data/final_trades_{timestamp}_trades.csv`

### On-Demand
```python
TradeExporter.export_to_csv(trade_history, 'my_trades.csv')
```

## Benefits

1. **Rõ ràng hơn**: Biết chính xác BUY hay SELL
2. **Dễ phân tích**: CSV format chuẩn, dễ import vào Excel/Python
3. **Tracking đầy đủ**: Mọi thông tin quan trọng đều được ghi lại
4. **Summary tự động**: Không cần tính toán thủ công
5. **Cumulative PnL**: Theo dõi PnL tích lũy qua thời gian
6. **Win/Loss tracking**: Dễ dàng phân tích tỷ lệ thắng

## API Reference

### TradeExporter.export_to_csv()
```python
TradeExporter.export_to_csv(trade_history, filepath)
```
Export trades to CSV file.

### TradeExporter.export_detailed_report()
```python
TradeExporter.export_detailed_report(trade_history, filepath_prefix)
```
Export both CSV and summary text file.

### TradeExporter.format_trades_df()
```python
df = TradeExporter.format_trades_df(trade_history)
```
Convert trade history to formatted DataFrame.

### TradeExporter.get_trade_summary()
```python
summary = TradeExporter.get_trade_summary(trade_history)
```
Get summary statistics dictionary.

### TradeExporter.print_trade_summary()
```python
TradeExporter.print_trade_summary(trade_history)
```
Print formatted summary to console.

## Notes

- Tất cả giá trị numeric được làm tròn đến 8 chữ số thập phân
- Timestamp theo format ISO 8601
- PnL chỉ được tính cho CLOSE actions
- Cumulative PnL được cập nhật sau mỗi trade
- Win flag: 1 = winning trade, 0 = losing trade

