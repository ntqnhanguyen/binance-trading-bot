# Live Trading Guide

Complete guide to running the bot in live trading mode (testnet, paper, mainnet).

## Overview

The bot supports 3 live trading modes:

1. **Testnet** - Safe testing with fake money on Binance Testnet
2. **Paper** - Simulation with real market data, no real trades
3. **Mainnet** - Real trading with real money ⚠️

## Quick Start

### 1. Setup API Keys

**For Testnet:**
```bash
# Get testnet API keys from:
# https://testnet.binance.vision/

# Add to .env:
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
```

**For Mainnet:**
```bash
# Get mainnet API keys from:
# https://www.binance.com/en/my/settings/api-management

# Add to .env:
BINANCE_API_KEY=your_mainnet_key
BINANCE_SECRET_KEY=your_mainnet_secret
```

### 2. Run Bot

**Testnet (Recommended for testing):**
```bash
./scripts/run_live.sh --mode testnet --symbol BTCUSDT --capital 1000
```

**Paper Trading:**
```bash
./scripts/run_live.sh --mode paper --symbol ETHUSDT --capital 5000
```

**Mainnet (REAL MONEY):**
```bash
./scripts/run_live.sh --mode mainnet --symbol SOLUSDT --capital 100
```

## Script Options

### run_live.sh

```bash
Usage: ./scripts/run_live.sh [OPTIONS]

Options:
  -m, --mode MODE       Trading mode: testnet, paper, mainnet
  -s, --symbol SYMBOL   Trading pair (default: BTCUSDT)
  -c, --capital AMOUNT  Initial capital (default: 1000)
  --config FILE         Config file path
  -h, --help            Show help message
```

### Examples

**1. Testnet with BTC:**
```bash
./scripts/run_live.sh \
  --mode testnet \
  --symbol BTCUSDT \
  --capital 1000
```

**2. Paper trading with ETH:**
```bash
./scripts/run_live.sh \
  --mode paper \
  --symbol ETHUSDT \
  --capital 5000
```

**3. Mainnet with SOL (small capital):**
```bash
./scripts/run_live.sh \
  --mode mainnet \
  --symbol SOLUSDT \
  --capital 100
```

**4. Using environment variables:**
```bash
TRADING_MODE=testnet \
SYMBOL=BTCUSDT \
INITIAL_CAPITAL=1000 \
./scripts/run_live.sh
```

**5. Custom config:**
```bash
./scripts/run_live.sh \
  --mode testnet \
  --config config/my_config.yaml
```

## Trading Modes

### Testnet

**What it is:**
- Binance Testnet environment
- Fake money, real-like trading
- Safe for testing

**Use cases:**
- Test strategy logic
- Verify order execution
- Practice without risk

**Setup:**
1. Get testnet API keys: https://testnet.binance.vision/
2. Add to `.env`:
   ```
   BINANCE_TESTNET_API_KEY=...
   BINANCE_TESTNET_SECRET_KEY=...
   ```
3. Run: `./scripts/run_live.sh --mode testnet`

**Limitations:**
- Testnet may have different liquidity
- Some pairs may not be available
- Testnet can be reset

### Paper Trading

**What it is:**
- Simulation mode
- Real market data
- No actual orders placed

**Use cases:**
- Test with real market conditions
- No API keys needed
- Monitor strategy performance

**Setup:**
1. No API keys needed
2. Run: `./scripts/run_live.sh --mode paper`

**Limitations:**
- Simulated fills (may not match reality)
- No slippage modeling
- No order book depth

### Mainnet

**What it is:**
- Real Binance trading
- Real money
- Real profits/losses

**⚠️ WARNING:**
- You can lose money
- Start with small capital
- Monitor closely
- Test on testnet first

**Setup:**
1. Get mainnet API keys: https://www.binance.com/en/my/settings/api-management
2. **Important:** Set API restrictions:
   - ✅ Enable: Read Info
   - ✅ Enable: Enable Spot & Margin Trading
   - ❌ Disable: Enable Withdrawals
   - ✅ Enable: IP Access Restrictions (recommended)
3. Add to `.env`:
   ```
   BINANCE_API_KEY=...
   BINANCE_SECRET_KEY=...
   ```
4. Run: `./scripts/run_live.sh --mode mainnet`

**Best Practices:**
- Start with $50-100
- Test for 1-2 weeks
- Monitor daily
- Scale up gradually

## Monitoring

### Console Output

```
╔════════════════════════════════════════════════════════════╗
║          Binance Trading Bot - Live Trading               ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  Mode:           testnet
  Symbol:         BTCUSDT
  Capital:        $1000
  Config:         config/config.yaml

Starting bot...
Log file: logs/trading_testnet_20251025_143015.log

Bot is running. Press Ctrl+C to stop.

2025-10-25 14:30:15 - INFO - Bot started in testnet mode
2025-10-25 14:30:15 - INFO - Symbol: BTCUSDT, Capital: $1000.00
2025-10-25 14:30:20 - INFO - ✅ BUY filled: 0.0010 @ $50,000.00, Fee=$0.05
2025-10-25 14:35:15 - INFO - 🟢 SELL filled: 0.0010 @ $51,000.00, PnL=$0.95
```

### Log Files

**Location:** `logs/trading_{mode}_{timestamp}.log`

**Example:** `logs/trading_testnet_20251025_143015.log`

**View logs:**
```bash
# Tail logs
tail -f logs/trading_testnet_*.log

# Search for errors
grep ERROR logs/trading_testnet_*.log

# Search for fills
grep "filled" logs/trading_testnet_*.log
```

### Output Files

**Location:** `data/outputs/`

**Files:**
- `orders_{session_id}.csv` - All orders
- `fills_{session_id}.csv` - All fills
- `summary_{session_id}.csv` - Summary stats

**Monitor:**
```bash
# Watch fills in real-time
watch -n 5 'tail -20 data/outputs/fills_*.csv'

# Check summary
cat data/outputs/summary_*.csv
```

## Configuration

### Trading Parameters

**File:** `config/config.yaml`

```yaml
default_policy:
  # Grid Trading
  grid_enabled: true
  grid_levels_per_side: 3
  spread_mid_pct: 0.5
  
  # DCA
  dca_enabled: true
  dca_rsi_threshold: 35
  dca_cooldown_bars: 5
  
  # Take Profit
  tp_enabled: true
  tp_rsi_threshold: 65
  
  # Risk Management
  hard_stop_daily_pnl_pct: -5.0
  hard_stop_gap_pct: -8.0
  
  # Auto-Resume
  auto_resume_enabled: true
  resume_rsi_threshold: 40
  resume_price_recovery_pct: 2.0
  resume_cooldown_bars: 60

# Fees
fees:
  maker_fee_pct: 0.1
  taker_fee_pct: 0.1
  use_bnb_discount: false
```

### Per-Pair Configuration

```yaml
pairs:
  BTCUSDT:
    spread_mid_pct: 0.4
    grid_levels_per_side: 4
    dca_rsi_threshold: 30
  
  ETHUSDT:
    spread_mid_pct: 0.45
    grid_levels_per_side: 4
  
  SOLUSDT:
    spread_mid_pct: 0.6
    grid_levels_per_side: 3
    dca_rsi_threshold: 35
```

## Safety Features

### 1. Hard Stop

**Triggers:**
- Daily PnL < -5% (default)
- Gap < -8% (default)

**Action:**
- Close all positions
- Pause trading
- Monitor for recovery

### 2. Auto-Resume

**Conditions:**
- Cooldown passed (60 bars)
- RSI > 40
- Price recovered +2%

**Action:**
- Resume trading automatically
- Log resume event

### 3. PnL Gate

**States:**
- **RUN**: Full operation (grid + DCA + TP)
- **DEGRADED**: Reduced operation (DCA + TP only)
- **PAUSED**: No new orders

**Thresholds:**
- DEGRADED: -2% daily PnL or -3% gap
- PAUSED: -4% daily PnL or -5% gap

### 4. Risk Limits

```yaml
risk:
  max_position_size_pct: 20.0
  max_total_exposure_pct: 80.0
  min_cash_reserve_pct: 20.0
```

### 5. Order Limits

```yaml
execution:
  max_orders_per_symbol: 10
  min_order_value_usdt: 11.0
```

## Stopping the Bot

### Graceful Shutdown

```bash
# Press Ctrl+C
^C

# Bot will:
# 1. Cancel all pending orders
# 2. Close open positions (optional)
# 3. Save final state
# 4. Export trades to CSV
```

### Force Stop

```bash
# Find process
ps aux | grep main.py

# Kill process
kill <PID>
```

### Emergency Stop

```bash
# Kill immediately
pkill -9 -f main.py

# Or
killall -9 python3
```

## Troubleshooting

### API Connection Issues

**Problem:** Cannot connect to Binance

**Solutions:**
1. Check API keys in `.env`
2. Verify API permissions
3. Check IP restrictions
4. Test with `python test_api.py`

### Insufficient Balance

**Problem:** Insufficient balance for orders

**Solutions:**
1. Check account balance
2. Reduce `INITIAL_CAPITAL`
3. Increase `min_order_value_usdt`
4. Reduce `grid_levels_per_side`

### Orders Not Filling

**Problem:** Orders placed but not filled

**Causes:**
- Price moved away
- Spread too wide
- Low liquidity

**Solutions:**
1. Tighten spread
2. Use market orders (not recommended)
3. Increase order size
4. Choose more liquid pairs

### Hard Stop Triggered

**Problem:** Hard stop triggered frequently

**Solutions:**
1. Widen stop thresholds
2. Reduce position sizes
3. Choose less volatile pairs
4. Adjust strategy parameters

### Bot Crashes

**Problem:** Bot exits unexpectedly

**Solutions:**
1. Check logs: `tail -100 logs/trading_*.log`
2. Look for errors
3. Verify dependencies: `pip3 install -r requirements.txt`
4. Check disk space
5. Check memory usage

## Best Practices

### 1. Testing Progression

```
1. Backtest (1 week)
   ↓
2. Paper trading (1 week)
   ↓
3. Testnet (1-2 weeks)
   ↓
4. Mainnet (small capital)
   ↓
5. Scale up gradually
```

### 2. Capital Management

**Start Small:**
- Testnet: $1,000 (fake)
- Mainnet: $50-100 (real)

**Scale Up:**
- Week 1: $50
- Week 2: $100 (if profitable)
- Week 3: $200 (if profitable)
- Week 4: $500 (if profitable)

**Never:**
- Don't invest more than you can afford to lose
- Don't use leverage
- Don't trade with borrowed money

### 3. Monitoring Schedule

**Daily:**
- Check PnL
- Review trades
- Monitor logs

**Weekly:**
- Analyze performance
- Adjust parameters
- Review strategy

**Monthly:**
- Calculate returns
- Compare to benchmarks
- Decide to continue/stop

### 4. Risk Management

**Set Limits:**
- Max daily loss: 2-5%
- Max weekly loss: 5-10%
- Max monthly loss: 10-15%

**Stop Trading If:**
- Consecutive losses > 5
- Weekly loss > 10%
- Strategy not working

### 5. Security

**API Keys:**
- Never share API keys
- Use IP restrictions
- Disable withdrawals
- Rotate keys monthly

**Server:**
- Use VPS/cloud
- Enable firewall
- Keep software updated
- Use SSH keys

## Performance Tracking

### Daily Checklist

```bash
# 1. Check if bot is running
ps aux | grep main.py

# 2. View recent logs
tail -50 logs/trading_*.log

# 3. Check fills
tail -20 data/outputs/fills_*.csv

# 4. Check PnL
grep "PnL" logs/trading_*.log | tail -10
```

### Weekly Analysis

```python
import pandas as pd

# Load fills
fills = pd.read_csv('data/outputs/fills_20251025_143015.csv')

# Calculate metrics
total_pnl = fills[fills['action'] == 'CLOSE']['pnl'].sum()
win_rate = (fills[fills['pnl'] > 0].shape[0] / fills.shape[0]) * 100
total_fees = fills['fee'].sum()

print(f"Total PnL: ${total_pnl:.2f}")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Total Fees: ${total_fees:.2f}")
```

## FAQ

### Q: Which mode should I start with?

**A:** Start with backtest, then paper, then testnet, finally mainnet.

### Q: How much capital do I need?

**A:** Minimum $50 for mainnet, but $100-500 recommended.

### Q: Can I run multiple bots?

**A:** Yes, but use different symbols or accounts.

### Q: How long should I test?

**A:** At least 1-2 weeks on testnet before mainnet.

### Q: What if I lose money?

**A:** Stop the bot, analyze logs, adjust strategy, test again.

### Q: Can I run 24/7?

**A:** Yes, use VPS/cloud server for continuous operation.

### Q: How do I update the bot?

**A:** `git pull`, then restart the bot.

### Q: Where are my trades saved?

**A:** `data/outputs/` directory with CSV files.

## Support

**Documentation:**
- README.md
- HYBRID_USAGE.md
- AUTO_RESUME.md
- FEES_AND_EQUITY.md

**Issues:**
- GitHub: https://github.com/ntqnhanguyen/binance-trading-bot/issues

**Community:**
- Discussions: https://github.com/ntqnhanguyen/binance-trading-bot/discussions

## Disclaimer

⚠️ **IMPORTANT:**

- Trading cryptocurrencies involves risk
- You can lose money
- Past performance ≠ future results
- This bot is provided "as is"
- No guarantees of profit
- Use at your own risk
- Always test before live trading

**The authors are not responsible for any losses incurred while using this bot.**

---

**Ready to trade? Start with testnet!** 🚀

