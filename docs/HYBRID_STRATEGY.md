# Hybrid Strategy Engine (Option-A)

Advanced trading strategy combining Grid Trading + DCA with dynamic spread adjustment, PnL Gate, and Stop-Loss management.

## Overview

The Hybrid Strategy Engine implements a sophisticated trading approach that:
- Combines **Grid Trading** for range-bound markets
- Adds **DCA (Dollar-Cost Averaging)** for oversold conditions
- Suggests **TP (Take Profit)** trailing for overbought conditions
- Uses **dynamic spread** based on market volatility
- Implements **PnL Gate** for risk management
- Applies **Stop-Loss** at portfolio level

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Hybrid Strategy Engine                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Indicator   │───▶│   Strategy   │───▶│ Orchestrator │  │
│  │   Engine     │    │    Engine    │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         │                    │                    │          │
│    Technical            Plan Orders          Execute         │
│    Signals              (Grid/DCA/TP)        Orders          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Technical Signal Collection

Uses **IndicatorEngine** to calculate and provide:
- **RSI** (Relative Strength Index)
- **ATR** (Average True Range) and ATR%
- **EMA** (Exponential Moving Averages) - Fast/Mid/Slow
- **Bollinger Bands**

### 2. Dynamic Spread Calculation

Spread adjusts automatically based on:

**Band Selection (ATR%):**
- `ATR% < 1.0%` → **near** band (tight spread: 0.3%)
- `ATR% < 2.0%` → **mid** band (medium spread: 0.5%)
- `ATR% >= 2.0%` → **far** band (wide spread: 0.8%)

**RSI Adjustment:**
- `RSI < 30` → Tighten spread by 10% (more aggressive buying)
- `RSI > 70` → Widen spread by 10% (more conservative)

**Formula:**
```python
base_spread = spread_by_band[band]  # near/mid/far
rsi_factor = 1.0 ± 0.1  # Based on RSI
final_spread = base_spread * rsi_factor
```

### 3. Grid Orders Planning

**Two-sided grid** around reference price:

```
Sell Grid:  ref_price * (1 + spread% * 3)  ← grid_sell_3
            ref_price * (1 + spread% * 2)  ← grid_sell_2
            ref_price * (1 + spread% * 1)  ← grid_sell_1
─────────────────────────────────────────
            ref_price                      ← current price
─────────────────────────────────────────
Buy Grid:   ref_price * (1 - spread% * 1)  ← grid_buy_1
            ref_price * (1 - spread% * 2)  ← grid_buy_2
            ref_price * (1 - spread% * 3)  ← grid_buy_3
```

**Kill & Replace Logic:**
- Grid is recreated if price drifts >1% from last grid center
- Prevents stale orders far from market
- Cooldown: 5 minutes between grid updates

### 4. DCA Orders Planning

**Trigger Conditions:**
- `RSI < 35` (oversold)
- `Price < EMA Fast` (optional gate)
- Cooldown: 5 bars since last DCA
- Min distance: 1% from last DCA fill

**Order Placement:**
- Price: `ref_price * (1 - 0.1%)` (slightly below market)
- Increases fill probability on 1m timeframe

### 5. TP (Take Profit) Suggestions

**Trigger Conditions:**
- `RSI > 65` (overbought)
- `Price > EMA Fast` (uptrend confirmation)

**TP Price by Band:**
- **near** band: `ref_price * (1 + 0.5%)`
- **mid** band: `ref_price * (1 + 0.8%)`
- **far** band: `ref_price * (1 + 1.2%)`

*Note: Actual trailing execution handled by Orchestrator/TP Engine*

### 6. PnL Gate States

**Three states based on Gap% and Daily PnL%:**

| State | Gap% | Daily PnL% | Behavior |
|-------|------|------------|----------|
| **RUN** | > -3% | > -2% | Full operation (Grid + DCA + TP) |
| **DEGRADED** | -3% to -5% | -2% to -4% | Reduced (DCA + TP only) |
| **PAUSED** | < -5% | < -4% | No new orders |

**Gap%:** `(current_price - open_price_day) / open_price_day * 100`

**Daily PnL%:** `(current_equity - equity_open) / equity_open * 100`

### 7. Stop-Loss (Hard Stop)

**Immediate stop if:**
- `Daily PnL% <= -5%` OR
- `Gap% <= -8%`

Returns:
```python
{
    "stop": True,
    "reason": "Daily PnL -5.2% <= -5.0%"
}
```

## Interface (Option-A)

### Input

```python
on_bar(bar: Dict, equity: float) -> Dict
```

**bar:**
```python
{
    'timestamp': datetime,
    'open': float,
    'high': float,
    'low': float,
    'close': float,
    'volume': float
}
```

**equity:** Current portfolio value (for PnL Gate calculation)

### Output (Plan Dictionary)

```python
{
    "pnl_gate_state": "RUN" | "DEGRADED" | "PAUSED",
    "sl_action": {
        "stop": bool,
        "reason": str  # Optional
    },
    "grid_orders": [
        {
            "side": "BUY" | "SELL",
            "price": float,
            "qty": float,  # Optional (calculated by Orchestrator)
            "tag": str     # e.g., "grid_buy_1"
        },
        ...
    ],
    "dca_orders": [
        {
            "side": "BUY",
            "price": float,
            "tag": str  # e.g., "dca_rsi32"
        }
    ],
    "tp_orders": [
        {
            "side": "SELL",
            "price": float,
            "tag": str  # e.g., "tp_rsi68_bandmid"
        }
    ],
    "band": "near" | "mid" | "far",
    "spread_pct": float,
    "ref_price": float,
    "kill_replace": bool
}
```

## Configuration

### YAML Structure

```yaml
# config/hybrid_strategy.yaml

default_policy:
  # Spread Configuration
  use_dynamic_spread: true
  fixed_spread_pct: 0.5
  
  # Band Thresholds
  band_near_threshold: 1.0
  band_mid_threshold: 2.0
  
  # Spread by Band
  spread_near_pct: 0.3
  spread_mid_pct: 0.5
  spread_far_pct: 0.8
  
  # RSI Adjustment
  rsi_adjust_enabled: true
  rsi_adjust_factor: 0.1
  
  # Grid Configuration
  grid_enabled: true
  grid_levels_per_side: 3
  grid_kill_replace_threshold_pct: 1.0
  grid_min_seconds_between: 300
  
  # DCA Configuration
  dca_enabled: true
  dca_rsi_threshold: 35
  dca_use_ema_gate: true
  dca_cooldown_bars: 5
  dca_min_distance_from_last_fill_pct: 1.0
  dca_price_offset_pct: 0.1
  
  # TP Configuration
  tp_enabled: true
  tp_rsi_threshold: 65
  tp_spread_near_pct: 0.5
  tp_spread_mid_pct: 0.8
  tp_spread_far_pct: 1.2
  
  # PnL Gate
  gate_degraded_gap_pct: -3.0
  gate_paused_gap_pct: -5.0
  gate_degraded_daily_pnl_pct: -2.0
  gate_paused_daily_pnl_pct: -4.0
  
  # Stop-Loss
  hard_stop_daily_pnl_pct: -5.0
  hard_stop_gap_pct: -8.0
  
  # Timeframe
  bar_timeframe: "1m"

# Pair-specific overrides
pairs:
  BTCUSDT:
    spread_near_pct: 0.2
    grid_levels_per_side: 4
```

## Usage Example

```python
from src.strategies.hybrid_strategy_engine import HybridStrategyEngine
from src.indicators.indicator_engine import IndicatorEngine
import yaml

# Load configuration
with open('config/hybrid_strategy.yaml') as f:
    config = yaml.safe_load(f)

policy_cfg = config['default_policy']

# Initialize engines
indicator_engine = IndicatorEngine('BTCUSDT')
strategy_engine = HybridStrategyEngine('BTCUSDT', policy_cfg, indicator_engine)

# Update indicators with OHLCV data
indicator_engine.update(df)

# Generate trading plan
bar = {
    'timestamp': datetime.now(),
    'open': 50000.0,
    'high': 50100.0,
    'low': 49900.0,
    'close': 50050.0,
    'volume': 1000.0
}

equity = 10000.0  # Current portfolio value

plan = strategy_engine.on_bar(bar, equity)

# Process plan
print(f"State: {plan['pnl_gate_state']}")
print(f"Grid Orders: {len(plan['grid_orders'])}")
print(f"DCA Orders: {len(plan['dca_orders'])}")
print(f"TP Orders: {len(plan['tp_orders'])}")

# Notify fills
if dca_filled:
    strategy_engine.notify_dca_fill(fill_price)
```

## State Management

### Internal State

The engine tracks:
- `_last_grid_ref_price` - Last grid center price
- `_last_grid_timestamp` - Last grid creation time
- `_last_dca_timestamp` - Last DCA order time
- `_last_dca_fill_price` - Last DCA fill price
- `_open_price_day` - Day open price (for Gap%)
- `_equity_open` - Day open equity (for Daily PnL%)
- `_last_date` - Last trading date

### Get State

```python
state = strategy_engine.get_state()
print(state)
```

## Decision Flow

```
┌─────────────────┐
│   New Bar       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Technical   │
│ Signals         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compute Band &  │
│ Spread          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Evaluate PnL    │
│ Gate & SL       │
└────────┬────────┘
         │
         ├─ Hard Stop? ──▶ Return (stop=True)
         │
         ├─ PAUSED? ─────▶ Return (no orders)
         │
         ├─ DEGRADED? ───▶ Plan DCA + TP only
         │
         └─ RUN ─────────▶ Plan Grid + DCA + TP
                           │
                           ▼
                    ┌─────────────────┐
                    │ Return Plan     │
                    └─────────────────┘
```

## Best Practices

### 1. Pair-Specific Configuration

Different assets need different settings:

```yaml
pairs:
  BTCUSDT:
    # BTC: Lower volatility, tighter spreads
    spread_near_pct: 0.2
    spread_mid_pct: 0.4
    grid_levels_per_side: 4
    dca_rsi_threshold: 30
  
  SOLUSDT:
    # SOL: Higher volatility, wider spreads
    spread_near_pct: 0.4
    spread_mid_pct: 0.6
    grid_levels_per_side: 3
    dca_rsi_threshold: 35
```

### 2. Monitor PnL Gate

Track state transitions:
- RUN → DEGRADED: Reduce exposure
- DEGRADED → PAUSED: Stop new positions
- PAUSED → RUN: Resume trading

### 3. DCA Fill Notification

Always notify engine of DCA fills:
```python
if order_filled and order.tag.startswith('dca_'):
    strategy_engine.notify_dca_fill(fill_price)
```

### 4. Respect Cooldowns

Don't override cooldowns:
- Grid: 5 minutes minimum
- DCA: 5 bars minimum

### 5. Backtest First

Test with different market conditions:
- Ranging markets (Grid should work well)
- Trending down (DCA should trigger)
- Trending up (TP should trigger)
- High volatility (Spread should widen)

## Performance Metrics

Expected behavior:

| Market Condition | Grid | DCA | TP | Spread |
|------------------|------|-----|----|----|
| Ranging | ✓ Active | Rare | Rare | Near/Mid |
| Trending Down | ✓ Active | ✓ Active | ✗ | Mid/Far |
| Trending Up | ✓ Active | ✗ | ✓ Active | Mid/Far |
| High Volatility | ✓ Active | Varies | Varies | Far |
| Low Volatility | ✓ Active | Varies | Varies | Near |

## Troubleshooting

### Grid Not Updating

Check:
- Cooldown period (5 minutes)
- Price drift < threshold (1%)

### DCA Not Triggering

Check:
- RSI < threshold (35)
- Price < EMA Fast (if gate enabled)
- Cooldown (5 bars)
- Distance from last fill (1%)

### TP Not Triggering

Check:
- RSI > threshold (65)
- Price > EMA Fast

### PnL Gate Stuck in PAUSED

Check:
- Daily PnL% must recover above -4%
- Gap% must recover above -5%
- May need to wait for new trading day

## Integration with Orchestrator

The Orchestrator should:
1. Call `on_bar()` on each new bar
2. Check `sl_action['stop']` - if true, close all positions
3. Respect `pnl_gate_state` - adjust order execution
4. Apply `kill_replace` - cancel old grid orders
5. Calculate `qty` for each order (not done by engine)
6. Apply tick size, lot size, min_notional
7. Limit total number of orders
8. Handle order execution and fills
9. Notify engine of DCA fills

## Version

- **Version**: 1.3.0
- **Date**: 2024-10-24
- **Spec**: Option-A v1.1.2
- **Status**: ✅ Production Ready

## References

- Grid Trading: Range-bound strategy
- DCA: Dollar-Cost Averaging
- RSI: Relative Strength Index
- ATR: Average True Range
- EMA: Exponential Moving Average
- PnL Gate: Risk management state machine

