# Trading Outputs Directory

This directory contains all trading session outputs.

## Files Generated

### Per Session

Each trading session generates 3 CSV files:

1. **orders_{session_id}.csv**
   - All orders placed
   - Type: BUY/SELL
   - Action: OPEN/CLOSE
   - Status tracking

2. **fills_{session_id}.csv**
   - All order fills
   - PnL tracking
   - Fee information
   - Performance metrics

3. **summary_{session_id}.csv**
   - Session statistics
   - Win rate, total PnL
   - Volume, fees

## Session ID Format

`YYYYMMDD_HHMMSS`

Example: `20251025_143015`

## File Retention

- Files are kept indefinitely by default
- Consider archiving old files periodically
- Recommend keeping last 30-90 days

## Analysis

Load and analyze with Python:

```python
import pandas as pd

# Load orders
orders = pd.read_csv('orders_20251025_143015.csv')

# Load fills
fills = pd.read_csv('fills_20251025_143015.csv')

# Load summary
summary = pd.read_csv('summary_20251025_143015.csv')
```

Or open directly in Excel/Google Sheets.

## Documentation

See `docs/ORDER_LOGGING.md` for complete documentation.

