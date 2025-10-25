# Order Logging System

Complete order tracking and logging system with CSV export.

## Overview

The OrderLogger system provides detailed tracking of all trading activities:
- Order placement
- Order fills
- Order status updates
- Performance metrics
- CSV export for analysis

## Features

### 1. Order Tracking
- Every order is logged with full details
- Status tracking (NEW, FILLED, CANCELLED, REJECTED)
- Type tracking (BUY/SELL)
- Side tracking (LONG/SHORT)
- Action tracking (OPEN/CLOSE)

### 2. Fill Tracking
- Every fill is logged separately
- PnL calculation
- Fee tracking
- Entry/exit price tracking

### 3. CSV Export
All data saved to `data/outputs/`:
- `orders_{session_id}.csv` - All orders
- `fills_{session_id}.csv` - All fills
- `summary_{session_id}.csv` - Session summary

### 4. Real-time Logging
- Console output with emojis
- Detailed info for every order/fill
- Summary statistics

## Usage

### In Backtest

```python
from src.utils.order_logger import OrderLogger

# Initialize
order_logger = OrderLogger(output_dir='./data/outputs')

# Log order
order_logger.log_order(
    symbol='BTCUSDT',
    order_type='BUY',  # BUY or SELL
    side='LONG',       # LONG or SHORT
    action='OPEN',     # OPEN or CLOSE
    price=50000.0,
    quantity=0.001,
    status='NEW',
    strategy='HybridStrategy',
    tag='grid_buy_1',
    reason='Grid level 1',
    mode='backtest'
)

# Log fill
order_logger.log_fill(
    symbol='BTCUSDT',
    order_id='ORD_123',
    fill_type='BUY',
    side='LONG',
    action='OPEN',
    price=50000.0,
    quantity=0.001,
    fee=0.00001,
    fee_asset='BNB',
    strategy='HybridStrategy',
    tag='grid_buy_1'
)

# Generate summary
summary = order_logger.generate_summary()
order_logger.print_summary()
```

### In Live Trading

```python
# Same API as backtest
order_logger = OrderLogger(output_dir='./data/outputs')

# Log real orders
order_logger.log_order(
    symbol='BTCUSDT',
    order_type='BUY',
    side='LONG',
    action='OPEN',
    price=50000.0,
    quantity=0.001,
    status='NEW',
    mode='mainnet',  # paper, testnet, or mainnet
    order_id=binance_order_id,
    client_order_id=client_id
)

# Update status when filled
order_logger.update_order_status(order_id, 'FILLED')

# Log fill
order_logger.log_fill(
    symbol='BTCUSDT',
    order_id=order_id,
    fill_type='BUY',
    side='LONG',
    action='OPEN',
    price=fill_price,
    quantity=fill_qty,
    fee=fill_fee,
    fee_asset='BNB'
)
```

## CSV Formats

### orders_{session_id}.csv

```csv
timestamp,session_id,symbol,order_id,client_order_id,type,side,action,price,quantity,value,status,strategy,tag,reason,mode
2025-10-25 14:30:15,20251025_143015,BTCUSDT,ORD_001,CLI_001,BUY,LONG,OPEN,50000.00,0.00100000,50.00,NEW,HybridStrategy,grid_buy_1,Grid level 1,backtest
```

**Fields:**
- `timestamp` - When order was placed
- `session_id` - Trading session ID
- `symbol` - Trading pair
- `order_id` - Order ID
- `client_order_id` - Client order ID
- `type` - **BUY** or **SELL**
- `side` - LONG or SHORT
- `action` - **OPEN** or **CLOSE**
- `price` - Order price
- `quantity` - Order quantity
- `value` - Order value (price × quantity)
- `status` - NEW, FILLED, CANCELLED, REJECTED
- `strategy` - Strategy name
- `tag` - Order tag (grid_buy_1, dca_1, tp_1, etc.)
- `reason` - Reason for order
- `mode` - backtest, paper, testnet, mainnet

### fills_{session_id}.csv

```csv
timestamp,session_id,symbol,order_id,fill_id,type,side,action,price,quantity,value,fee,fee_asset,pnl,pnl_pct,strategy,tag
2025-10-25 14:30:20,20251025_143015,BTCUSDT,ORD_001,FILL_001,BUY,LONG,OPEN,50000.00,0.00100000,50.00,0.00001000,BNB,0.00,0.00,HybridStrategy,grid_buy_1
2025-10-25 14:35:15,20251025_143015,BTCUSDT,ORD_002,FILL_002,SELL,LONG,CLOSE,50500.00,0.00100000,50.50,0.00001000,BNB,0.50,1.00,HybridStrategy,grid_sell_1
```

**Fields:**
- `timestamp` - When fill occurred
- `session_id` - Trading session ID
- `symbol` - Trading pair
- `order_id` - Order ID
- `fill_id` - Fill ID
- `type` - **BUY** or **SELL**
- `side` - LONG or SHORT
- `action` - **OPEN** or **CLOSE**
- `price` - Fill price
- `quantity` - Fill quantity
- `value` - Fill value
- `fee` - Trading fee
- `fee_asset` - Fee asset (BNB, USDT, etc.)
- `pnl` - Profit/Loss (for CLOSE)
- `pnl_pct` - PnL percentage (for CLOSE)
- `strategy` - Strategy name
- `tag` - Fill tag

### summary_{session_id}.csv

```csv
session_id,total_orders,total_fills,buy_fills,sell_fills,open_fills,close_fills,total_volume,total_fees,total_pnl,win_rate,avg_pnl
20251025_143015,45,42,22,20,22,20,105000.50,1.05,1234.56,65.00,61.73
```

**Fields:**
- `session_id` - Trading session ID
- `total_orders` - Total orders placed
- `total_fills` - Total fills executed
- `buy_fills` - Number of BUY fills
- `sell_fills` - Number of SELL fills
- `open_fills` - Number of OPEN fills
- `close_fills` - Number of CLOSE fills
- `total_volume` - Total trading volume
- `total_fees` - Total fees paid
- `total_pnl` - Total profit/loss
- `win_rate` - Win rate percentage
- `avg_pnl` - Average PnL per close

## Console Output

### Order Placed
```
📝 Order placed: BUY @ $50000.00 [grid_buy_1]
```

### Order Filled (BUY)
```
✅ BUY filled: 0.0010 @ $50000.00, Value=$50.00 [grid_buy_1]
```

### Order Filled (SELL - Profit)
```
🟢 SELL filled (close): 0.0010 @ $50500.00, PnL=$0.50 (+1.00%) [grid_sell_1]
```

### Order Filled (SELL - Loss)
```
🔴 SELL filled (close): 0.0010 @ $49500.00, PnL=$-0.50 (-1.00%) [stop_loss]
```

### Summary
```
======================================================================
ORDER SUMMARY
======================================================================
Session ID: 20251025_143015

Orders:
  Total Orders: 45
  Total Fills: 42
  Buy Fills: 22
  Sell Fills: 20
  Open Fills: 22
  Close Fills: 20

Performance:
  Total Volume: $105,000.50
  Total Fees: $1.05
  Total PnL: $1,234.56
  Win Rate: 65.00%
  Avg PnL: $61.73

Files:
  Orders: ./data/outputs/orders_20251025_143015.csv
  Fills: ./data/outputs/fills_20251025_143015.csv
  Summary: ./data/outputs/summary_20251025_143015.csv
======================================================================
```

## Analysis Examples

### Load and Analyze Orders

```python
import pandas as pd

# Load orders
orders_df = pd.read_csv('data/outputs/orders_20251025_143015.csv')

# Filter by type
buy_orders = orders_df[orders_df['type'] == 'BUY']
sell_orders = orders_df[orders_df['type'] == 'SELL']

# Filter by status
filled_orders = orders_df[orders_df['status'] == 'FILLED']
cancelled_orders = orders_df[orders_df['status'] == 'CANCELLED']

# Filter by tag
grid_orders = orders_df[orders_df['tag'].str.contains('grid')]
dca_orders = orders_df[orders_df['tag'].str.contains('dca')]
```

### Load and Analyze Fills

```python
# Load fills
fills_df = pd.read_csv('data/outputs/fills_20251025_143015.csv')

# Calculate metrics
total_pnl = fills_df[fills_df['action'] == 'CLOSE']['pnl'].sum()
win_rate = (fills_df[fills_df['pnl'] > 0].shape[0] / fills_df[fills_df['action'] == 'CLOSE'].shape[0]) * 100

# Analyze by tag
grid_fills = fills_df[fills_df['tag'].str.contains('grid')]
dca_fills = fills_df[fills_df['tag'].str.contains('dca')]

print(f"Grid PnL: ${grid_fills['pnl'].sum():.2f}")
print(f"DCA PnL: ${dca_fills['pnl'].sum():.2f}")
```

### Visualize Performance

```python
import matplotlib.pyplot as plt

# Load fills
fills_df = pd.read_csv('data/outputs/fills_20251025_143015.csv')
fills_df['timestamp'] = pd.to_datetime(fills_df['timestamp'])

# Cumulative PnL
fills_df['cumulative_pnl'] = fills_df['pnl'].cumsum()

# Plot
plt.figure(figsize=(12, 6))
plt.plot(fills_df['timestamp'], fills_df['cumulative_pnl'])
plt.title('Cumulative PnL Over Time')
plt.xlabel('Time')
plt.ylabel('PnL ($)')
plt.grid(True)
plt.show()
```

## Integration

### Backtest
Already integrated in `run_backtest.py`

### Live Trading
Add to `main.py`:

```python
from src.utils.order_logger import OrderLogger

# Initialize
order_logger = OrderLogger(output_dir='./data/outputs')

# In trading loop, log every order
order_logger.log_order(...)

# On fill callback
order_logger.log_fill(...)

# On shutdown
order_logger.print_summary()
```

## Benefits

1. **Complete Audit Trail**
   - Every order tracked
   - Every fill recorded
   - Full transparency

2. **Performance Analysis**
   - Win rate calculation
   - PnL tracking
   - Fee analysis
   - Volume tracking

3. **Strategy Analysis**
   - Compare grid vs DCA
   - Analyze by tag
   - Optimize parameters

4. **Compliance**
   - Full records for tax
   - Audit-ready logs
   - Timestamp everything

5. **Debugging**
   - Track order flow
   - Find issues
   - Verify logic

## Best Practices

1. **Always log orders** - Even if they fail
2. **Log fills separately** - Track execution
3. **Use meaningful tags** - Easy to analyze
4. **Generate summary** - At end of session
5. **Archive logs** - Keep historical data
6. **Analyze regularly** - Improve strategy

## File Management

### Auto-cleanup
```python
# Keep only last 30 days
import os
import time
from pathlib import Path

output_dir = Path('./data/outputs')
cutoff = time.time() - (30 * 86400)

for file in output_dir.glob('*.csv'):
    if file.stat().st_mtime < cutoff:
        file.unlink()
```

### Archive
```bash
# Archive old logs
tar -czf logs_2025_10.tar.gz data/outputs/*_202510*.csv
rm data/outputs/*_202510*.csv
```

## Summary

OrderLogger provides:
- ✅ Complete order tracking
- ✅ Detailed fill logging
- ✅ CSV export
- ✅ Performance metrics
- ✅ Console output
- ✅ Easy analysis

**Every order matters. Track them all!** 📊

