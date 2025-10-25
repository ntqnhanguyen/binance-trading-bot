# Troubleshooting Guide

Common issues and solutions for the Binance Trading Bot.

## Orders Not Being Placed

### Symptom
```
📊 SOLUSDT Plan: Band=NEAR  Spread=0.440%  |  Grid=6  DCA=0  TP=1
✓ PnL State: RUN
```
But no "ORDER PLACED" logs appear, and equity doesn't change.

### Cause
**Order size is below Binance minimum notional value ($11 USD).**

### Diagnosis

Check your order size calculation:
```
Order Value = Equity × Order Size %
Quantity = Order Value / Price
Order Notional = Quantity × Price

Example with $1000 equity, SOL @ $195:
- Order Value = $1000 × 1% = $10
- Quantity = $10 / $195 = 0.0513 SOL
- Order Notional = 0.0513 × $195 = $10.01
- Result: $10.01 < $11.00 ❌ (Order skipped)
```

### Solution

**Option 1: Increase Capital** (Recommended)
```bash
# Use at least $1100 for 1% order size
./scripts/run_live.sh --mode testnet --symbol SOLUSDT --capital 1100
```

**Option 2: Use Cheaper Pairs**
```bash
# Trade pairs with lower prices
./scripts/run_live.sh --mode testnet --symbol DOGEUSDT --capital 1000
```

**Option 3: Already Fixed in v2.5.1**

The bot now uses 2% order size instead of 1%, which works with $1000 capital:
```
Order Value = $1000 × 2% = $20
Quantity = $20 / $195 = 0.1025 SOL
Order Notional = 0.1025 × $195 = $20.00 ✓
```

### Verification

After the fix, you should see:
```
📈 ORDER PLACED: GRID | BUY 0.1025 SOLUSDT @ $194.24  [grid_buy_1]
📉 ORDER PLACED: GRID | SELL 0.1025 SOLUSDT @ $195.96  [grid_sell_1]
```

If orders are still skipped, you'll see a warning:
```
⚠️  Order skipped (too small): 0.0513 SOLUSDT @ $195.10 = $10.01 < $11.00
```

---

## Grid Orders = 0

### Symptom
```
📊 BTCUSDT Plan: Band=MID  Spread=0.500%  |  Grid=0  DCA=0  TP=0
```

### Cause 1: Grid Cooldown Active

Grid orders are only created every 5 minutes (300 seconds) by default.

**Check logs for:**
```
Grid cooldown active: 60s < 300s
```

**Solution:** Wait for cooldown to expire, or reduce `grid_min_seconds_between` in config:
```yaml
default_policy:
  grid_min_seconds_between: 60  # Reduce from 300 to 60 seconds
```

### Cause 2: Price Drift Too Small

Grid is only recreated when price drifts more than 1% from last grid center.

**Solution:** Reduce threshold in config:
```yaml
default_policy:
  grid_kill_replace_threshold_pct: 0.5  # Reduce from 1.0 to 0.5%
```

### Cause 3: Grid Disabled

**Check config:**
```yaml
default_policy:
  grid_enabled: false  # Should be true
```

**Solution:** Set `grid_enabled: true`

---

## Config File Not Found

### Symptom
```
FileNotFoundError: config/hybrid_strategy.yaml
```

### Cause
The bot is looking for `hybrid_strategy.yaml` but only `config.yaml` exists.

### Solution

**Option 1: Use Environment Variable**
```bash
export CONFIG_PATH=config/config.yaml
./scripts/run_live.sh --mode testnet
```

**Option 2: Already Fixed in v2.5.1**

The default config path is now `config/config.yaml`.

---

## API Connection Issues

### Symptom
```
❌ Error getting ticker for BTCUSDT: Invalid API key
```

### Solution

**1. Check API Keys in .env:**
```bash
# For testnet
BINANCE_TESTNET_API_KEY=your_key_here
BINANCE_TESTNET_SECRET_KEY=your_secret_here

# For mainnet
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
```

**2. Verify API Permissions:**
- ✅ Read Info
- ✅ Enable Spot & Margin Trading
- ❌ Enable Withdrawals (should be disabled)

**3. Test Connection:**
```bash
python3 test_api.py
```

---

## Equity Not Updating

### Symptom
Equity stays at initial capital even after orders are placed.

### Cause 1: Orders Not Actually Placed

See "Orders Not Being Placed" section above.

### Cause 2: Orders Not Filled Yet

In testnet/mainnet, orders are limit orders that need to be filled by market.

**Check:**
```
📈 ORDER PLACED: GRID | BUY 0.1025 SOLUSDT @ $194.24
```
But no:
```
✅ ORDER FILLED: GRID | BUY 0.1025 SOLUSDT @ $194.24
```

**Solution:** Wait for market to reach your limit price, or use tighter spreads.

### Cause 3: Paper Trading Fill Logic

In paper mode, orders are simulated and only fill when price crosses the limit price.

**Solution:** This is expected behavior. Wait for price movement.

---

## PnL State Stuck in DEGRADED/PAUSED

### Symptom
```
⚠ PnL State: DEGRADED  |  Daily PnL: -3.20%  |  Gap PnL: -2.10%
```
or
```
⏸ PnL State: PAUSED  |  Daily PnL: -6.50%  |  Gap PnL: -8.20%
```

### Cause
PnL Gate has triggered due to losses.

**States:**
- **DEGRADED**: -2% daily PnL or -3% gap → Grid disabled, DCA/TP only
- **PAUSED**: -4% daily PnL or -5% gap → All new orders disabled

### Solution

**Option 1: Wait for Recovery**

The bot will automatically resume when:
- Cooldown period passes (60 bars = 60 minutes)
- RSI recovers above 40
- Price recovers 2% from stop price

**Option 2: Adjust Thresholds**

Make PnL Gate less sensitive:
```yaml
default_policy:
  gate_degraded_daily_pnl_pct: -5.0  # More lenient
  gate_paused_daily_pnl_pct: -10.0
  gate_degraded_gap_pct: -5.0
  gate_paused_gap_pct: -10.0
```

**Option 3: Disable PnL Gate**

Not recommended, but possible by setting very low thresholds:
```yaml
default_policy:
  gate_degraded_daily_pnl_pct: -50.0
  gate_paused_daily_pnl_pct: -90.0
```

---

## Hard Stop Triggered

### Symptom
```
🛑 HARD STOP TRIGGERED: BTCUSDT  |  Reason: Daily PnL <= -5.0%
```

### Cause
Safety mechanism activated due to significant losses.

**Triggers:**
- Daily PnL ≤ -5%
- Gap ≤ -8%

### What Happens
1. All positions are closed immediately
2. Trading is paused
3. Bot monitors for recovery conditions

### Recovery

**Automatic Resume** (if enabled):
```yaml
default_policy:
  auto_resume_enabled: true
  resume_rsi_threshold: 40
  resume_price_recovery_pct: 2.0
  resume_cooldown_bars: 60
```

Bot will resume when ALL conditions are met:
- ✅ 60 bars (60 minutes) have passed
- ✅ RSI > 40 (oversold recovery)
- ✅ Price recovered 2% from stop price

**Manual Resume:**

Restart the bot:
```bash
# Stop bot
Ctrl+C

# Restart
./scripts/run_live.sh --mode testnet
```

---

## CSV Files Not Created

### Symptom
No files in `data/outputs/` directory.

### Solution

**1. Check Directory Exists:**
```bash
mkdir -p data/outputs
chmod 755 data/outputs
```

**2. Check OUTPUT_DIR Variable:**
```bash
echo $OUTPUT_DIR
# Should be empty or point to valid directory
```

**3. Check Permissions:**
```bash
ls -la data/
# Should show outputs directory with write permissions
```

---

## Colors Not Showing

### Symptom
Console shows ANSI codes instead of colors:
```
[32mORDER PLACED[0m
```

### Cause
Terminal doesn't support ANSI colors.

### Solution

**Disable colors:**
```bash
export ENABLE_COLORS=false
./scripts/run_live.sh --mode testnet
```

---

## High Memory Usage

### Symptom
Bot uses excessive memory over time.

### Cause
Historical data accumulation in memory.

### Solution

**1. Reduce Indicator Lookback:**
```yaml
# In config.yaml, reduce bar limit
```

**2. Restart Bot Periodically:**
```bash
# Use cron to restart daily
0 0 * * * pkill -f main.py && ./scripts/run_live.sh --mode testnet
```

**3. Monitor Memory:**
```bash
# Check memory usage
ps aux | grep python3
```

---

## Bot Crashes Unexpectedly

### Symptom
Bot exits without warning.

### Diagnosis

**1. Check Logs:**
```bash
tail -100 logs/trading_*.log
```

**2. Look for Errors:**
```bash
grep ERROR logs/trading_*.log
grep CRITICAL logs/trading_*.log
```

### Common Causes

**1. Network Issues:**
```
❌ Error getting ticker: Connection timeout
```
**Solution:** Check internet connection, try again.

**2. API Rate Limits:**
```
❌ Error: Too many requests
```
**Solution:** Increase `TRADING_INTERVAL` to reduce API calls.

**3. Insufficient Disk Space:**
```bash
df -h
```
**Solution:** Free up disk space, clean old logs.

**4. Out of Memory:**
```bash
free -h
```
**Solution:** Restart bot, reduce memory usage.

---

## Test Script Errors

### Symptom
```bash
python3 test_enhanced_logging.py
# Error: ModuleNotFoundError
```

### Solution

**1. Install Dependencies:**
```bash
pip3 install -r requirements.txt
```

**2. Check Python Version:**
```bash
python3 --version
# Should be 3.8+
```

**3. Run from Project Root:**
```bash
cd /home/ubuntu/binance-trading-bot
python3 test_enhanced_logging.py
```

---

## Getting Help

If your issue isn't covered here:

1. **Check Documentation:**
   - `README.md`
   - `docs/LIVE_TRADING.md`
   - `docs/ENHANCED_LOGGING.md`
   - `CHANGELOG.md`

2. **Enable Debug Logging:**
   ```yaml
   logging:
     level: DEBUG
   ```

3. **Check GitHub Issues:**
   https://github.com/ntqnhanguyen/binance-trading-bot/issues

4. **Create New Issue:**
   Include:
   - Bot version
   - Trading mode (paper/testnet/mainnet)
   - Config file
   - Log output
   - Steps to reproduce

---

**Last Updated:** October 25, 2025  
**Version:** 2.5.1

