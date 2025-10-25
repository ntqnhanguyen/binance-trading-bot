# Auto-Resume After Hard Stop

Automatic resume trading after hard stop when market conditions improve.

## Overview

When a hard stop is triggered (due to excessive losses), the bot will:
1. **Pause trading** immediately
2. **Monitor market conditions** continuously
3. **Auto-resume trading** when conditions improve

This prevents the bot from staying paused indefinitely during temporary market downturns.

## Hard Stop Triggers

Hard stop is triggered when:

1. **Daily PnL drops below threshold**
   - Default: -5.0%
   - Config: `hard_stop_daily_pnl_pct`

2. **Gap (price vs open) drops below threshold**
   - Default: -8.0%
   - Config: `hard_stop_gap_pct`

**Example:**
```
HybridBacktest - CRITICAL - Hard stop triggered: Daily PnL -5.53% <= -5.0%
```

## Auto-Resume Conditions

Trading will resume when **ALL** conditions are met:

### 1. Cooldown Period Passed
- Default: 60 bars (60 minutes for 1m timeframe)
- Config: `resume_cooldown_bars`
- Prevents immediate resume after stop

### 2. RSI Recovery
- Default: RSI > 40
- Config: `resume_rsi_threshold`
- Indicates oversold condition is recovering

### 3. Price Recovery
- Default: Price recovers +2.0% from stop price
- Config: `resume_price_recovery_pct`
- Confirms market is bouncing back

## Configuration

**File:** `config/config.yaml`

```yaml
default_policy:
  # Stop-Loss Configuration
  hard_stop_daily_pnl_pct: -5.0  # Hard stop at -5% daily PnL
  hard_stop_gap_pct: -8.0        # Hard stop at -8% gap
  
  # Auto-Resume Configuration
  auto_resume_enabled: true      # Enable/disable auto-resume
  resume_rsi_threshold: 40       # RSI must be > 40
  resume_price_recovery_pct: 2.0 # Price must recover 2%
  resume_cooldown_bars: 60       # Wait 60 bars after stop
```

## Example Scenario

### 1. Hard Stop Triggered

```
2025-10-25 10:00:00 - CRITICAL - Hard stop activated: 
  Daily PnL -5.53% <= -5.0% at price=$48,500.00
```

**Bot State:**
- Trading: PAUSED
- Stop Price: $48,500.00
- Stop Time: 10:00:00

### 2. Monitoring Phase (60 minutes)

```
10:15:00 - DEBUG - Resume cooldown: 15/60 bars
10:30:00 - DEBUG - Resume cooldown: 30/60 bars
10:45:00 - DEBUG - Resume cooldown: 45/60 bars
```

**Bot continues to monitor but doesn't resume yet.**

### 3. Checking Resume Conditions (after 60 bars)

```
11:00:00 - DEBUG - Resume cooldown: 60/60 bars ✓
11:00:00 - DEBUG - Resume RSI check: 38.5 <= 40 ✗
```

**RSI not recovered yet, continue waiting.**

```
11:15:00 - DEBUG - Resume RSI check: 42.3 > 40 ✓
11:15:00 - DEBUG - Resume price check: +1.5% < 2.0% ✗
```

**RSI OK, but price not recovered enough.**

```
11:30:00 - DEBUG - Resume RSI check: 45.1 > 40 ✓
11:30:00 - DEBUG - Resume price check: +2.3% >= 2.0% ✓
```

**All conditions met!**

### 4. Auto-Resume

```
11:30:00 - WARNING - Auto-resume triggered: Good market signal detected.
  Resuming trading from hard stop.
11:30:00 - INFO - Resume conditions met:
  cooldown=90 bars, RSI=45.1, price_recovery=+2.3%
```

**Bot State:**
- Trading: RESUMED (RUN state)
- Stop cleared
- Normal trading resumes

## Benefits

### 1. Automatic Recovery
- No manual intervention needed
- Bot resumes when safe
- Captures recovery opportunities

### 2. Risk Management
- Cooldown prevents premature resume
- Multiple conditions ensure safety
- Only resumes on good signals

### 3. Flexibility
- Configurable thresholds
- Can be disabled if needed
- Per-pair customization

## Disabling Auto-Resume

If you prefer manual control:

```yaml
default_policy:
  auto_resume_enabled: false  # Disable auto-resume
```

**With auto-resume disabled:**
- Bot stays paused after hard stop
- Requires manual restart
- More conservative approach

## Advanced Configuration

### Conservative (Safer)

```yaml
default_policy:
  resume_rsi_threshold: 50       # Higher RSI required
  resume_price_recovery_pct: 3.0 # More price recovery
  resume_cooldown_bars: 120      # Longer cooldown (2 hours)
```

### Aggressive (Faster Resume)

```yaml
default_policy:
  resume_rsi_threshold: 35       # Lower RSI OK
  resume_price_recovery_pct: 1.0 # Less price recovery
  resume_cooldown_bars: 30       # Shorter cooldown (30 min)
```

### Per-Pair Customization

```yaml
pairs:
  BTCUSDT:
    # BTC more stable, can resume faster
    resume_rsi_threshold: 38
    resume_price_recovery_pct: 1.5
    resume_cooldown_bars: 45
  
  SOLUSDT:
    # SOL more volatile, be more careful
    resume_rsi_threshold: 45
    resume_price_recovery_pct: 3.0
    resume_cooldown_bars: 90
```

## Monitoring

### Check Hard Stop Status

In backtest logs:
```
CRITICAL - Hard stop activated: ...
WARNING - Auto-resume triggered: ...
```

In strategy state:
```python
state = strategy_engine.get_state()
print(f"Hard stop active: {state['hard_stop_active']}")
print(f"Stop reason: {state['hard_stop_reason']}")
print(f"Stop price: {state['hard_stop_price']}")
```

### Resume Logs

```
DEBUG - Resume cooldown: X/60 bars
DEBUG - Resume RSI check: X.X <= 40
DEBUG - Resume price check: +X.X% < 2.0%
INFO - Resume conditions met: cooldown=X bars, RSI=X.X, price_recovery=+X.X%
WARNING - Auto-resume triggered: Good market signal detected
```

## Best Practices

### 1. Set Appropriate Thresholds

**Hard Stop:**
- Not too tight (avoid frequent stops)
- Not too loose (protect capital)
- Recommended: -5% to -8%

**Resume:**
- Conservative thresholds
- Ensure market has recovered
- Recommended: RSI > 40, Price +2%

### 2. Monitor Performance

- Track hard stop frequency
- Analyze resume success rate
- Adjust thresholds if needed

### 3. Backtest First

```bash
python run_backtest.py \
  --symbol BTCUSDT \
  --capital 10000 \
  --data ./data/BTCUSDT_1m.csv
```

Check logs for:
- Hard stop triggers
- Resume events
- Performance impact

### 4. Consider Market Conditions

**Trending Market:**
- Tighter stops
- Faster resume

**Ranging Market:**
- Wider stops
- More conservative resume

**High Volatility:**
- Wider stops
- Longer cooldown

## Troubleshooting

### Bot Stays Paused Too Long

**Possible causes:**
1. RSI not recovering → Market still weak
2. Price not recovering → Downtrend continues
3. Cooldown too long → Reduce `resume_cooldown_bars`

**Solutions:**
- Lower `resume_rsi_threshold` (e.g., 35)
- Lower `resume_price_recovery_pct` (e.g., 1.0%)
- Reduce `resume_cooldown_bars` (e.g., 30)

### Bot Resumes Too Quickly

**Possible causes:**
1. Thresholds too loose
2. Cooldown too short
3. False recovery signals

**Solutions:**
- Raise `resume_rsi_threshold` (e.g., 45)
- Raise `resume_price_recovery_pct` (e.g., 3.0%)
- Increase `resume_cooldown_bars` (e.g., 90)

### Bot Never Resumes

**Possible causes:**
1. Auto-resume disabled
2. Conditions never met
3. Thresholds too strict

**Check:**
```yaml
auto_resume_enabled: true  # Make sure this is true
```

**Solutions:**
- Enable auto-resume
- Lower thresholds
- Check logs for condition failures

## Examples

### Example 1: Quick Recovery

```
10:00 - Hard stop: Daily PnL -5.2%
10:30 - Cooldown: 30/60 bars
11:00 - Cooldown complete
11:00 - RSI: 42 > 40 ✓
11:00 - Price: +2.5% ✓
11:00 - Auto-resume triggered ✓
```

**Result:** Resumed after 1 hour

### Example 2: Slow Recovery

```
10:00 - Hard stop: Daily PnL -5.8%
11:00 - Cooldown complete
11:00 - RSI: 35 < 40 ✗
12:00 - RSI: 38 < 40 ✗
13:00 - RSI: 41 > 40 ✓
13:00 - Price: +1.2% < 2.0% ✗
14:00 - Price: +2.3% ✓
14:00 - Auto-resume triggered ✓
```

**Result:** Resumed after 4 hours

### Example 3: No Recovery

```
10:00 - Hard stop: Daily PnL -6.5%
11:00 - Cooldown complete
11:00 - RSI: 28 < 40 ✗
12:00 - RSI: 25 < 40 ✗
13:00 - RSI: 22 < 40 ✗
...
```

**Result:** Stays paused (market still weak)

## Summary

Auto-resume feature:
- ✅ Automatically resumes trading after hard stop
- ✅ Only when market conditions improve
- ✅ Configurable thresholds
- ✅ Multiple safety conditions
- ✅ Can be disabled if needed

**Protects capital while capturing recovery opportunities!** 🛡️📈

