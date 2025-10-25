# Order Management System

**Version**: 2.6.0  
**Feature**: Intelligent Order Cancellation  
**Last Updated**: October 25, 2025

## Overview

The Order Management System automatically cancels pending orders that are no longer optimal based on market conditions. This prevents stale orders from being filled at unfavorable prices and ensures the bot adapts to changing market dynamics.

## Cancellation Criteria

### 1. Time-Based Cancellation

**Description**: Cancel orders that have been pending for too long.

**Configuration:**
```yaml
order_max_age_seconds: 300  # 5 minutes
```

**Logic:**
- Orders older than `order_max_age_seconds` are automatically cancelled
- Default: 300 seconds (5 minutes)
- Prevents stale orders from lingering

**Example:**
```
Order placed at: 10:00:00
Current time: 10:05:30
Order age: 330 seconds > 300 seconds
→ Cancel order (reason: "Order age 330s > 300s")
```

---

### 2. Price Drift Cancellation

**Description**: Cancel orders when price has moved significantly away from the order price.

**Configuration:**
```yaml
order_price_drift_threshold_pct: 2.0  # 2%
```

**Logic:**
- Calculate price drift: `|current_price - order_price| / order_price * 100`
- Cancel if drift > threshold
- Prevents orders from being filled at prices that are no longer competitive

**Example:**
```
Order: BUY @ $195.0
Current price: $199.0
Price drift: |199 - 195| / 195 * 100 = 2.05%
Threshold: 2.0%
→ Cancel order (reason: "Price drift 2.05% > 2.0%")
```

---

### 3. Volatility Spike Cancellation

**Description**: Cancel grid orders when volatility suddenly increases.

**Configuration:**
```yaml
order_cancel_on_volatility_spike: true
order_volatility_spike_threshold: 1.5  # 1.5x
```

**Logic:**
- Compare current ATR% with previous ATR%
- Cancel if `current_atr_pct > last_atr_pct * threshold`
- Only applies to **grid orders** (not DCA or TP)
- High volatility makes tight grid orders risky

**Example:**
```
Last ATR%: 1.0%
Current ATR%: 1.6%
Threshold: 1.5x
1.6% > 1.0% * 1.5 = 1.5%
→ Cancel grid orders (reason: "Volatility spike: 1.6% > 1.5%")
```

---

### 4. RSI Reversal Cancellation

**Description**: Cancel orders when RSI shows strong reversal signal.

**Configuration:**
```yaml
order_cancel_on_rsi_reversal: true
order_rsi_reversal_threshold: 20  # 20 points
```

**Logic:**

**For BUY orders:**
- Initial RSI < 40 (oversold)
- Current RSI > 60 (overbought)
- RSI change > threshold
- → Cancel (market reversed from oversold to overbought)

**For SELL orders:**
- Initial RSI > 60 (overbought)
- Current RSI < 40 (oversold)
- RSI change > threshold
- → Cancel (market reversed from overbought to oversold)

**Example:**
```
BUY order placed when RSI = 35 (oversold)
Current RSI = 65 (overbought)
RSI change = |65 - 35| = 30 > 20
→ Cancel BUY order (reason: "RSI reversal: 35.0 -> 65.0")
```

---

## Configuration

### Default Settings

```yaml
default_policy:
  # Order Management
  order_max_age_seconds: 300  # Cancel after 5 minutes
  order_price_drift_threshold_pct: 2.0  # Cancel if price drifts >2%
  order_cancel_on_volatility_spike: true  # Enable volatility cancellation
  order_volatility_spike_threshold: 1.5  # 1.5x normal volatility
  order_cancel_on_rsi_reversal: true  # Enable RSI reversal cancellation
  order_rsi_reversal_threshold: 20  # RSI change > 20 points
```

### Pair-Specific Overrides

```yaml
pairs:
  BTCUSDT:
    # BTC is less volatile, use tighter thresholds
    order_max_age_seconds: 600  # 10 minutes
    order_price_drift_threshold_pct: 1.0  # 1%
    order_volatility_spike_threshold: 1.3  # 1.3x
  
  SOLUSDT:
    # SOL is more volatile, use looser thresholds
    order_max_age_seconds: 180  # 3 minutes
    order_price_drift_threshold_pct: 3.0  # 3%
    order_volatility_spike_threshold: 2.0  # 2.0x
```

---

## How It Works

### Workflow

1. **Every trading loop** (default: 60 seconds):
   - Get current market prices
   - Get current market signals (RSI, ATR%)
   - Check all pending orders for each symbol

2. **For each pending order**:
   - Calculate order age
   - Calculate price drift
   - Check volatility spike (grid orders only)
   - Check RSI reversal (if enabled)

3. **If any cancellation criterion is met**:
   - Cancel order on exchange (testnet/mainnet)
   - Remove from pending orders list
   - Log cancellation with reason
   - Display cancellation message

4. **Grid recreation**:
   - Cancelled grid orders will be recreated in next loop
   - New orders will be placed at current market price
   - Ensures grid stays aligned with market

---

## Console Output

### Order Cancelled

```
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $194.0  [grid_buy_1]  Reason: Order age 330s > 300s
```

### Multiple Cancellations

```
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $194.0  [grid_buy_1]  Reason: Price drift 2.5% > 2.0%
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $193.1  [grid_buy_2]  Reason: Price drift 3.1% > 2.0%
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $192.2  [grid_buy_3]  Reason: Price drift 4.2% > 2.0%
```

---

## CSV Logging

Cancelled orders are logged to `orders_{session_id}.csv` with:

- **status**: `CANCELLED`
- **reason**: Cancellation reason (e.g., "GRID - Order age 330s > 300s")
- **timestamp**: When the order was cancelled
- **All order details**: symbol, side, price, quantity, tag, etc.

**Example:**
```csv
timestamp,session_id,symbol,order_id,client_order_id,type,side,action,price,quantity,value,status,strategy,tag,reason,mode
2025-10-25 10:05:30,20251025_100000,SOLUSDT,PAPER_1729850730123,,BUY,LONG,OPEN,194.0,0.1,19.4,CANCELLED,Hybrid,grid_buy_1,GRID - Order age 330s > 300s,testnet
```

---

## Benefits

### 1. Prevent Stale Orders

- Orders that are too old are cancelled automatically
- Ensures orders reflect current market conditions
- Reduces risk of fills at outdated prices

### 2. Adapt to Price Movement

- Orders are cancelled when price drifts too far
- New orders are placed at better prices
- Improves fill quality and reduces slippage

### 3. Respond to Volatility

- Grid orders are cancelled during volatility spikes
- Prevents tight grids from being swept in volatile markets
- Protects against rapid price swings

### 4. Follow Market Sentiment

- RSI reversal detection prevents counter-trend fills
- BUY orders cancelled when market becomes overbought
- SELL orders cancelled when market becomes oversold

### 5. Automatic Grid Refresh

- Cancelled grid orders are automatically recreated
- New grid is centered on current price
- Maintains optimal grid positioning

---

## Examples

### Example 1: Time-Based Cancellation

**Scenario:**
- Grid orders placed at 10:00:00
- Price hasn't moved much
- Orders still pending at 10:05:30

**Action:**
```
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $194.0  [grid_buy_1]  Reason: Order age 330s > 300s
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $193.1  [grid_buy_2]  Reason: Order age 330s > 300s
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $192.2  [grid_buy_3]  Reason: Order age 330s > 300s
```

**Next Loop:**
- New grid orders placed at current price
- Fresh orders with updated prices

---

### Example 2: Price Drift Cancellation

**Scenario:**
- Grid orders placed when price = $195
- Price suddenly jumps to $200 (+2.6%)
- BUY orders are now too far below market

**Action:**
```
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $194.0  [grid_buy_1]  Reason: Price drift 3.1% > 2.0%
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $193.1  [grid_buy_2]  Reason: Price drift 3.6% > 2.0%
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $192.2  [grid_buy_3]  Reason: Price drift 4.1% > 2.0%
```

**Next Loop:**
- New grid centered at $200
- BUY orders at $199, $198, $197

---

### Example 3: Volatility Spike

**Scenario:**
- Normal ATR% = 1.0%
- Sudden news causes ATR% to spike to 2.5%
- Grid orders become risky

**Action:**
```
🗑️  ORDER CANCELLED: GRID | BUY 0.10 SOLUSDT @ $194.0  [grid_buy_1]  Reason: Volatility spike: 2.5% > 1.5%
🗑️  ORDER CANCELLED: GRID | SELL 0.10 SOLUSDT @ $195.7  [grid_sell_1]  Reason: Volatility spike: 2.5% > 1.5%
```

**Next Loop:**
- Wider spread calculated based on new ATR%
- New grid with appropriate spacing for high volatility

---

### Example 4: RSI Reversal

**Scenario:**
- BUY order placed when RSI = 32 (oversold)
- Market recovers, RSI rises to 68 (overbought)
- BUY order no longer makes sense

**Action:**
```
🗑️  ORDER CANCELLED: DCA | BUY 0.10 SOLUSDT @ $193.0  [dca_oversold]  Reason: RSI reversal: 32.0 -> 68.0
```

**Result:**
- Prevents buying at the top after RSI reversal
- Protects against counter-trend entries

---

## Tuning Recommendations

### Conservative (Low Risk)

```yaml
order_max_age_seconds: 180  # 3 minutes
order_price_drift_threshold_pct: 1.0  # 1%
order_volatility_spike_threshold: 1.3  # 1.3x
order_rsi_reversal_threshold: 15  # 15 points
```

**Characteristics:**
- Frequent order cancellations
- Tight adaptation to market
- Lower risk of bad fills
- Higher exchange fees (more orders)

### Moderate (Balanced)

```yaml
order_max_age_seconds: 300  # 5 minutes
order_price_drift_threshold_pct: 2.0  # 2%
order_volatility_spike_threshold: 1.5  # 1.5x
order_rsi_reversal_threshold: 20  # 20 points
```

**Characteristics:**
- Balanced cancellation rate
- Good adaptation to market
- Moderate risk
- Moderate fees

### Aggressive (High Risk)

```yaml
order_max_age_seconds: 600  # 10 minutes
order_price_drift_threshold_pct: 3.0  # 3%
order_volatility_spike_threshold: 2.0  # 2.0x
order_rsi_reversal_threshold: 30  # 30 points
```

**Characteristics:**
- Infrequent cancellations
- Orders stay longer
- Higher risk of bad fills
- Lower fees

---

## Disabling Features

### Disable All Order Management

```yaml
order_max_age_seconds: 999999  # Effectively infinite
order_price_drift_threshold_pct: 999.0  # Never trigger
order_cancel_on_volatility_spike: false
order_cancel_on_rsi_reversal: false
```

### Disable Specific Features

```yaml
# Keep time-based, disable others
order_max_age_seconds: 300
order_price_drift_threshold_pct: 999.0  # Disabled
order_cancel_on_volatility_spike: false  # Disabled
order_cancel_on_rsi_reversal: false  # Disabled
```

---

## Monitoring

### Check Cancellation Rate

```bash
# Count cancelled orders
grep "CANCELLED" data/outputs/orders_*.csv | wc -l

# Show cancellation reasons
grep "CANCELLED" data/outputs/orders_*.csv | cut -d',' -f15 | sort | uniq -c
```

### Analyze Cancellation Impact

```python
import pandas as pd

# Load orders
orders = pd.read_csv('data/outputs/orders_20251025_100000.csv')

# Count by status
print(orders['status'].value_counts())

# Cancellation reasons
cancelled = orders[orders['status'] == 'CANCELLED']
print(cancelled['reason'].value_counts())

# Cancellation rate
cancel_rate = len(cancelled) / len(orders) * 100
print(f"Cancellation rate: {cancel_rate:.2f}%")
```

---

## Troubleshooting

### Too Many Cancellations

**Symptom:** Orders are cancelled too frequently

**Solutions:**
1. Increase `order_max_age_seconds`
2. Increase `order_price_drift_threshold_pct`
3. Increase `order_volatility_spike_threshold`
4. Disable specific features

### Too Few Cancellations

**Symptom:** Stale orders are not being cancelled

**Solutions:**
1. Decrease `order_max_age_seconds`
2. Decrease `order_price_drift_threshold_pct`
3. Enable all cancellation features
4. Check logs for errors

### Orders Not Being Recreated

**Symptom:** Cancelled grid orders are not replaced

**Solutions:**
1. Check grid cooldown: `grid_min_seconds_between`
2. Check grid kill_replace threshold
3. Verify strategy is in RUN state (not DEGRADED/PAUSED)

---

## Best Practices

1. **Start conservative** - Use tight thresholds initially
2. **Monitor cancellation rate** - Aim for 10-30% cancellation rate
3. **Adjust per pair** - Different pairs need different settings
4. **Consider volatility** - Volatile pairs need looser thresholds
5. **Review logs** - Analyze cancellation reasons regularly
6. **Test in paper mode** - Verify settings before live trading

---

## Version History

- **v2.6.0** (2025-10-25): Initial release
  - Time-based cancellation
  - Price drift cancellation
  - Volatility spike cancellation
  - RSI reversal cancellation

---

**Last Updated:** October 25, 2025  
**Status:** Production Ready ✅

