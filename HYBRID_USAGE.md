# Hybrid Strategy Usage Guide

Complete guide for using the Hybrid Strategy Engine (Grid + DCA) with dynamic spread, PnL Gate, and Stop-Loss.

## Quick Start

### 1. Backtest

Test the strategy on historical data:

```bash
# Download data first
python download_data.py --symbol BTCUSDT --interval 1m --start 2024-01-01

# Run backtest
python run_hybrid_backtest.py \
    --symbol BTCUSDT \
    --capital 10000 \
    --data ./data/BTCUSDT_1m.csv

# Or use the script
./scripts/run_hybrid_backtest.sh BTCUSDT 10000 ./data/BTCUSDT_1m.csv
```

### 2. Paper Trading

Simulate live trading without real money:

```bash
# Copy environment file
cp .env.hybrid.example .env

# Edit .env
nano .env
# Set TRADING_MODE=paper

# Run bot
python main_hybrid.py
```

### 3. Live Trading

**⚠️ WARNING: Real money involved!**

```bash
# Edit .env
nano .env
# Set TRADING_MODE=mainnet
# Add real API keys

# Run bot
python main_hybrid.py
```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# API Credentials
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret

# Trading Mode
TRADING_MODE=paper  # paper, testnet, mainnet

# Symbols
TRADING_SYMBOLS=BTCUSDT,ETHUSDT

# Capital
INITIAL_CAPITAL=10000

# Config
HYBRID_CONFIG=config/hybrid_strategy.yaml

# Interval
TRADING_INTERVAL=60  # seconds
```

### Strategy Configuration

Edit `config/hybrid_strategy.yaml`:

```yaml
default_policy:
  # Dynamic Spread
  use_dynamic_spread: true
  band_near_threshold: 1.0
  band_mid_threshold: 2.0
  spread_near_pct: 0.3
  spread_mid_pct: 0.5
  spread_far_pct: 0.8
  
  # Grid
  grid_enabled: true
  grid_levels_per_side: 3
  grid_kill_replace_threshold_pct: 1.0
  
  # DCA
  dca_enabled: true
  dca_rsi_threshold: 35
  dca_cooldown_bars: 5
  
  # TP
  tp_enabled: true
  tp_rsi_threshold: 65
  
  # PnL Gate
  gate_degraded_gap_pct: -3.0
  gate_paused_gap_pct: -5.0
  
  # Stop-Loss
  hard_stop_daily_pnl_pct: -5.0
  hard_stop_gap_pct: -8.0

# Pair-specific overrides
pairs:
  BTCUSDT:
    spread_near_pct: 0.2
    grid_levels_per_side: 4
```

## Backtest Examples

### Basic Backtest

```bash
python run_hybrid_backtest.py \
    --symbol BTCUSDT \
    --capital 10000 \
    --data ./data/BTCUSDT_1m.csv
```

### With Pair-Specific Config

```bash
python run_hybrid_backtest.py \
    --symbol BTCUSDT \
    --capital 10000 \
    --data ./data/BTCUSDT_1m.csv \
    --pair-config BTCUSDT
```

### Multiple Symbols

```bash
# Backtest each symbol separately
for symbol in BTCUSDT ETHUSDT SOLUSDT; do
    python run_hybrid_backtest.py \
        --symbol $symbol \
        --capital 10000 \
        --data ./data/${symbol}_1m.csv \
        --pair-config $symbol
done
```

## Live Trading Examples

### Single Symbol

```bash
# .env
TRADING_SYMBOLS=BTCUSDT

python main_hybrid.py
```

### Multiple Symbols

```bash
# .env
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT

python main_hybrid.py
```

### With Docker

```bash
# Build
docker build -t binance-hybrid-bot .

# Run
docker run -d \
    --name hybrid-bot \
    --env-file .env \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/data:/app/data \
    binance-hybrid-bot \
    python main_hybrid.py
```

## Monitoring

### Logs

Check logs in real-time:

```bash
tail -f logs/trading_*.log
```

### Results

Backtest results saved to:
- `./data/hybrid_backtest_equity_*.csv` - Equity curve
- `./data/hybrid_backtest_trades_*.csv` - Trade history
- `./data/hybrid_backtest_states_*.csv` - State history

Live trading results:
- `./data/hybrid_live_trades_*.csv` - Trade history
- `./logs/trading_*.log` - Detailed logs

## Understanding Output

### Backtest Report

```
======================================================================
HYBRID STRATEGY BACKTEST REPORT
======================================================================

Symbol: BTCUSDT
Initial Capital: $10,000.00
Final Equity: $11,234.56
Total Return: 12.35%

Trades: 45
Win Rate: 62.22%
Avg Win: $87.45
Avg Loss: -$45.23
Total PnL: $1,234.56

State Distribution:
  RUN: 850 bars (85.0%)
  DEGRADED: 120 bars (12.0%)
  PAUSED: 30 bars (3.0%)

======================================================================
```

### Live Trading Logs

```
2024-10-24 14:30:15 - HybridBot - INFO - ============================================================
2024-10-24 14:30:15 - HybridBot - INFO - Trading loop at 2024-10-24 14:30:15
2024-10-24 14:30:15 - HybridBot - INFO - Portfolio Equity: $10,234.56
2024-10-24 14:30:15 - HybridBot - INFO - Processing BTCUSDT @ $50,123.45
2024-10-24 14:30:15 - HybridBot - INFO - BTCUSDT Plan: State=RUN, Band=mid, Spread=0.500%, Grid=6, DCA=0, TP=0
2024-10-24 14:30:15 - HybridBot - INFO - Paper order: BUY 0.0020 BTCUSDT @ $50,000.00 [grid_buy_1]
2024-10-24 14:30:15 - HybridBot - INFO - Paper order: SELL 0.0020 BTCUSDT @ $50,250.00 [grid_sell_1]
```

## Strategy Behavior

### RUN State (Normal)

- Full operation
- Grid orders active
- DCA on oversold
- TP on overbought
- All features enabled

### DEGRADED State (Warning)

- Gap: -3% to -5%
- Daily PnL: -2% to -4%
- Grid disabled
- DCA and TP only
- Reduced risk exposure

### PAUSED State (Critical)

- Gap: < -5%
- Daily PnL: < -4%
- No new orders
- Existing positions held
- Wait for recovery

### Hard Stop (Emergency)

- Daily PnL: <= -5%
- Gap: <= -8%
- All positions closed
- Trading stopped
- Manual intervention required

## Performance Optimization

### Adjust Spread

For more aggressive trading:
```yaml
spread_near_pct: 0.2  # Tighter
spread_mid_pct: 0.3
spread_far_pct: 0.5
```

For more conservative:
```yaml
spread_near_pct: 0.5  # Wider
spread_mid_pct: 0.8
spread_far_pct: 1.2
```

### Adjust Grid Levels

More levels = more trades:
```yaml
grid_levels_per_side: 5  # 5 buy + 5 sell = 10 orders
```

Fewer levels = less capital used:
```yaml
grid_levels_per_side: 2  # 2 buy + 2 sell = 4 orders
```

### Adjust DCA

More aggressive DCA:
```yaml
dca_rsi_threshold: 40  # Trigger earlier
dca_cooldown_bars: 3   # Faster
```

More conservative:
```yaml
dca_rsi_threshold: 30  # Trigger later
dca_cooldown_bars: 10  # Slower
```

### Adjust Risk Limits

Tighter risk control:
```yaml
gate_degraded_gap_pct: -2.0
gate_paused_gap_pct: -3.0
hard_stop_daily_pnl_pct: -3.0
```

Looser risk control:
```yaml
gate_degraded_gap_pct: -5.0
gate_paused_gap_pct: -8.0
hard_stop_daily_pnl_pct: -8.0
```

## Troubleshooting

### No Trades

Check:
- Spread too wide?
- Grid levels too far?
- Insufficient capital?
- Market too stable?

### Too Many Trades

Check:
- Spread too tight?
- Too many grid levels?
- Kill_replace triggering often?

### Frequent DEGRADED State

Check:
- Risk limits too tight?
- Market trending down?
- Position sizing too large?

### Hard Stop Triggered

Check:
- Stop-loss limits appropriate?
- Market crash?
- Position sizing?
- Review strategy parameters

## Best Practices

1. **Always backtest first**
   - Test on historical data
   - Multiple time periods
   - Different market conditions

2. **Start with paper trading**
   - Run for 1-2 weeks
   - Monitor behavior
   - Verify logic

3. **Start small on mainnet**
   - Use small capital initially
   - Gradually increase
   - Monitor closely

4. **Monitor regularly**
   - Check logs daily
   - Review trades
   - Adjust parameters

5. **Use pair-specific configs**
   - BTC: tighter spreads
   - Altcoins: wider spreads
   - Adjust per volatility

6. **Respect risk limits**
   - Don't override stop-loss
   - Don't ignore PAUSED state
   - Take breaks when needed

## Advanced Usage

### Custom Indicators

Modify `src/indicators/indicator_engine.py`:

```python
def _calculate_indicators(self):
    # Add custom indicators
    self._df['CUSTOM'] = your_calculation()
```

### Custom Logic

Modify `src/strategies/hybrid_strategy_engine.py`:

```python
def _plan_grid(self, ...):
    # Add custom grid logic
    pass
```

### Multiple Strategies

Run multiple bots with different configs:

```bash
# Conservative bot
HYBRID_CONFIG=config/hybrid_conservative.yaml python main_hybrid.py &

# Aggressive bot
HYBRID_CONFIG=config/hybrid_aggressive.yaml python main_hybrid.py &
```

## Support

For issues or questions:
- Check documentation: `docs/HYBRID_STRATEGY.md`
- Review logs: `./logs/`
- GitHub issues: https://github.com/ntqnhanguyen/binance-trading-bot/issues

## Disclaimer

**Trading involves risk of loss. This software is provided as-is with no guarantees. Always test thoroughly before using real money. Never invest more than you can afford to lose.**

