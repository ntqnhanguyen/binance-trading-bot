# Trading Fees and Equity Tracking

Complete guide to fee calculation and equity tracking in backtesting and live trading.

## Overview

The bot now includes:
1. **Trading fees** on every order (maker/taker)
2. **Equity tracking** after each trade
3. **Net PnL** calculation (after fees)
4. **Fee impact** analysis

## Trading Fees

### Fee Structure

**Default Binance Fees:**
- Maker fee: 0.1%
- Taker fee: 0.1%
- BNB discount: 25% (optional)

**Configuration:** `config/config.yaml`

```yaml
fees:
  maker_fee_pct: 0.1    # Maker fee: 0.1%
  taker_fee_pct: 0.1    # Taker fee: 0.1%
  use_bnb_discount: false  # Use BNB for discount
  bnb_discount_pct: 25  # 25% discount with BNB
```

### Fee Calculation

**BUY Order:**
```python
order_value = price * quantity
fee = order_value * (maker_fee_pct / 100)
total_cost = order_value + fee
cash -= total_cost
```

**Example:**
```
Price: $50,000
Quantity: 0.001 BTC
Order Value: $50.00
Fee (0.1%): $0.05
Total Cost: $50.05
```

**SELL Order:**
```python
sell_value = price * quantity
fee = sell_value * (maker_fee_pct / 100)
proceeds = sell_value - fee
cash += proceeds
```

**Example:**
```
Price: $51,000
Quantity: 0.001 BTC
Sell Value: $51.00
Fee (0.1%): $0.051
Proceeds: $50.949
```

### Net PnL Calculation

```python
# Gross PnL (before fees)
pnl_gross = quantity * (exit_price - entry_price)

# Fee on exit
exit_fee = (quantity * exit_price) * (fee_pct / 100)

# Net PnL (after fees)
pnl_net = pnl_gross - exit_fee
```

**Example Trade:**
```
Entry: $50,000 x 0.001 = $50.00 (+ $0.05 fee)
Exit:  $51,000 x 0.001 = $51.00 (- $0.051 fee)

Gross PnL: $1.00
Exit Fee: $0.051
Net PnL: $0.949
```

## Equity Tracking

### What is Equity?

**Equity = Cash + Position Value**

```python
def calculate_equity(current_price):
    equity = cash
    for position in positions:
        equity += position.quantity * current_price
    return equity
```

### Tracking After Each Trade

**BUY Order:**
```
Before: Cash=$10,000, Position=0, Equity=$10,000
BUY: 0.001 BTC @ $50,000
After: Cash=$9,949.95, Position=0.001 BTC, Equity=$10,000
```

**SELL Order:**
```
Before: Cash=$9,949.95, Position=0.001 BTC @ $50k, Equity=$10,000
SELL: 0.001 BTC @ $51,000
After: Cash=$10,000.899, Position=0, Equity=$10,000.899
```

### Logging

**Console Output:**

```
✅ BUY filled: 0.0010 @ $50,000.00, Value=$50.00, Fee=$0.05, Equity=$10,000.00 [grid_buy_1]

🟢 SELL filled (close): 0.0010 @ $51,000.00, PnL=$0.95 (+1.90%), Fee=$0.05, Equity=$10,000.90 [grid_sell_1]
```

**CSV Output (fills):**
```csv
timestamp,symbol,order_id,fill_id,type,side,action,price,quantity,value,fee,fee_asset,pnl,pnl_pct,strategy,tag
2025-10-25 14:30:20,BTCUSDT,ORD_001,FILL_001,BUY,LONG,OPEN,50000.00,0.00100000,50.00,0.05000000,USDT,0.00,0.00,HybridStrategy,grid_buy_1
2025-10-25 14:35:15,BTCUSDT,ORD_002,FILL_002,SELL,LONG,CLOSE,51000.00,0.00100000,51.00,0.05100000,USDT,0.95,1.90,HybridStrategy,grid_sell_1
```

## Backtest Report

### Enhanced Report Output

```
======================================================================
HYBRID STRATEGY BACKTEST REPORT
======================================================================

Symbol: BTCUSDT
Initial Capital: $10,000.00
Final Equity: $10,234.56
Total Return: 2.35%

Trades: 45
Win Rate: 62.22%
Avg Win: $12.50
Avg Loss: $-8.30

PnL (Gross): $350.00
Total Fees: $115.44
PnL (Net): $234.56
Fee Impact: 1.15% of capital

State Distribution:
  RUN: 850 bars (85.0%)
  DEGRADED: 100 bars (10.0%)
  PAUSED: 50 bars (5.0%)

======================================================================
```

### Key Metrics

**1. PnL (Gross)**
- Total profit/loss before fees
- Shows raw trading performance

**2. Total Fees**
- Sum of all trading fees
- Both entry and exit fees

**3. PnL (Net)**
- Total profit/loss after fees
- Real performance metric

**4. Fee Impact**
- Fees as % of initial capital
- Shows cost of trading

## Fee Optimization

### Strategies to Reduce Fees

**1. Use BNB for Discount**
```yaml
fees:
  use_bnb_discount: true
  bnb_discount_pct: 25
```

**Savings:**
- 0.1% → 0.075% (25% off)
- On $10,000 volume: $10 → $7.50

**2. Reduce Trade Frequency**
- Wider grid spacing
- Longer DCA cooldown
- Higher TP thresholds

**3. Maker Orders**
- Use post-only orders
- Get maker rebates (if available)

**4. VIP Levels**
- Higher volume → lower fees
- 0.1% → 0.09% → 0.08% ...

### Fee Impact Analysis

**Example: 100 Trades**

```
Average trade size: $100
Total volume: $10,000

Fees @ 0.1%: $10.00
Fees @ 0.075% (BNB): $7.50
Fees @ 0.05% (VIP): $5.00

Savings with BNB: $2.50 (25%)
Savings with VIP: $5.00 (50%)
```

## Configuration Examples

### Conservative (Low Fees)

```yaml
default_policy:
  # Wider spacing = fewer trades
  grid_levels_per_side: 2
  spread_mid_pct: 0.8
  
  # Longer cooldowns
  grid_min_seconds_between: 600  # 10 min
  dca_cooldown_bars: 10
  
fees:
  use_bnb_discount: true
  maker_fee_pct: 0.075  # With BNB
```

### Aggressive (Higher Fees)

```yaml
default_policy:
  # Tighter spacing = more trades
  grid_levels_per_side: 5
  spread_mid_pct: 0.3
  
  # Shorter cooldowns
  grid_min_seconds_between: 180  # 3 min
  dca_cooldown_bars: 3
  
fees:
  use_bnb_discount: false
  maker_fee_pct: 0.1  # Standard
```

## Analysis

### Load and Analyze Fees

```python
import pandas as pd

# Load fills
fills_df = pd.read_csv('data/outputs/fills_20251025_143015.csv')

# Total fees
total_fees = fills_df['fee'].sum()
print(f"Total Fees: ${total_fees:.2f}")

# Fee by action
buy_fees = fills_df[fills_df['action'] == 'OPEN']['fee'].sum()
sell_fees = fills_df[fills_df['action'] == 'CLOSE']['fee'].sum()

print(f"Buy Fees: ${buy_fees:.2f}")
print(f"Sell Fees: ${sell_fees:.2f}")

# Fee by strategy component
grid_fees = fills_df[fills_df['tag'].str.contains('grid')]['fee'].sum()
dca_fees = fills_df[fills_df['tag'].str.contains('dca')]['fee'].sum()

print(f"Grid Fees: ${grid_fees:.2f}")
print(f"DCA Fees: ${dca_fees:.2f}")
```

### Net PnL Analysis

```python
# Load fills
fills_df = pd.read_csv('data/outputs/fills_20251025_143015.csv')

# Filter close orders
closes = fills_df[fills_df['action'] == 'CLOSE']

# Calculate metrics
total_pnl = closes['pnl'].sum()
total_fees = closes['fee'].sum()
net_return_pct = (total_pnl / 10000) * 100  # Assuming $10k capital

print(f"Net PnL: ${total_pnl:.2f}")
print(f"Fees Paid: ${total_fees:.2f}")
print(f"Net Return: {net_return_pct:.2f}%")
print(f"Fee/PnL Ratio: {(total_fees / total_pnl * 100):.1f}%")
```

### Equity Curve

```python
import matplotlib.pyplot as plt

# Load fills
fills_df = pd.read_csv('data/outputs/fills_20251025_143015.csv')
fills_df['timestamp'] = pd.to_datetime(fills_df['timestamp'])

# Calculate cumulative equity
initial_capital = 10000
fills_df['cumulative_pnl'] = fills_df['pnl'].cumsum()
fills_df['equity'] = initial_capital + fills_df['cumulative_pnl']

# Plot
plt.figure(figsize=(12, 6))
plt.plot(fills_df['timestamp'], fills_df['equity'])
plt.axhline(y=initial_capital, color='r', linestyle='--', label='Initial Capital')
plt.title('Equity Curve')
plt.xlabel('Time')
plt.ylabel('Equity ($)')
plt.legend()
plt.grid(True)
plt.show()
```

## Best Practices

### 1. Always Include Fees

**Don't:**
```python
pnl = exit_price - entry_price  # Missing fees!
```

**Do:**
```python
pnl_gross = exit_price - entry_price
pnl_net = pnl_gross - entry_fee - exit_fee
```

### 2. Track Total Fees

```python
# Keep running total
self.total_fees = 0.0

# Add each fee
self.total_fees += fee

# Report at end
print(f"Total Fees: ${self.total_fees:.2f}")
```

### 3. Use Net PnL for Metrics

```python
# Wrong
win_rate = trades[trades['pnl_gross'] > 0].count()

# Right
win_rate = trades[trades['pnl_net'] > 0].count()
```

### 4. Monitor Fee Impact

```python
fee_impact_pct = (total_fees / initial_capital) * 100

if fee_impact_pct > 2.0:
    print("WARNING: High fee impact!")
    print("Consider: wider spreads, longer cooldowns, BNB discount")
```

### 5. Optimize for Net Returns

- Backtest with realistic fees
- Compare strategies by net PnL
- Factor fees into strategy design
- Use BNB discount if beneficial

## Troubleshooting

### Fees Too High

**Symptoms:**
- Fee impact > 2% of capital
- Net PnL << Gross PnL
- Many small trades

**Solutions:**
1. Enable BNB discount
2. Widen grid spacing
3. Increase cooldown periods
4. Raise minimum order size
5. Reduce number of grid levels

### Equity Not Matching

**Check:**
1. Are fees deducted from cash?
2. Is position value calculated correctly?
3. Are all trades recorded?

**Debug:**
```python
# After each trade
equity = cash + position_value
print(f"Cash: ${cash:.2f}")
print(f"Position: ${position_value:.2f}")
print(f"Equity: ${equity:.2f}")
```

## Summary

Trading fees and equity tracking:
- ✅ Realistic fee calculation (0.1% default)
- ✅ Net PnL after fees
- ✅ Equity tracked after each trade
- ✅ Fee impact analysis
- ✅ Detailed logging
- ✅ CSV export with fees
- ✅ Configurable fee rates
- ✅ BNB discount support

**Fees matter! Always use net PnL for performance evaluation.** 💰

