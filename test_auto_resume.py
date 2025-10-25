#!/usr/bin/env python3
"""
Test Auto-Resume Feature

This script tests the auto-resume functionality after hard stop.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data():
    """Create test data with a crash and recovery"""
    
    # Start date
    start_date = datetime(2025, 1, 1)
    
    # 1000 bars = ~16 hours at 1m
    timestamps = [start_date + timedelta(minutes=i) for i in range(1000)]
    
    # Price simulation
    prices = []
    base_price = 250.0
    
    for i in range(1000):
        if i < 200:
            # Normal trading
            price = base_price + np.random.normal(0, 2)
        elif i < 300:
            # Crash -6% (trigger hard stop at -5%)
            crash_pct = (i - 200) / 100 * 6
            price = base_price * (1 - crash_pct / 100) + np.random.normal(0, 1)
        elif i < 400:
            # Stay low (RSI oversold, but not recovering)
            price = base_price * 0.94 + np.random.normal(0, 0.5)
        elif i < 500:
            # Start recovery (RSI improving, price recovering)
            recovery_pct = (i - 400) / 100 * 3
            price = base_price * 0.94 * (1 + recovery_pct / 100) + np.random.normal(0, 1)
        else:
            # Back to normal
            price = base_price + np.random.normal(0, 2)
        
        prices.append(max(price, 200))  # Floor at $200
    
    # Create OHLCV data
    data = []
    for i, (ts, close) in enumerate(zip(timestamps, prices)):
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_price = close + np.random.normal(0, 0.5)
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    return df

def main():
    """Run test"""
    print("Creating test data with crash and recovery...")
    df = create_test_data()
    
    # Save to CSV
    output_file = './data/test_auto_resume.csv'
    df.to_csv(output_file, index=False)
    print(f"Test data saved to: {output_file}")
    
    print(f"\nData summary:")
    print(f"  Bars: {len(df)}")
    print(f"  Start price: ${df.iloc[0]['close']:.2f}")
    print(f"  Min price: ${df['close'].min():.2f} (at bar {df['close'].idxmin()})")
    print(f"  End price: ${df.iloc[-1]['close']:.2f}")
    print(f"  Crash depth: {((df['close'].min() / df.iloc[0]['close']) - 1) * 100:.1f}%")
    
    print(f"\nExpected behavior:")
    print(f"  1. Hard stop triggers around bar 200-300 (when daily PnL < -5%)")
    print(f"  2. Bot stays paused for 60+ bars (cooldown)")
    print(f"  3. Bot checks RSI and price recovery")
    print(f"  4. Auto-resume when conditions met (around bar 400-500)")
    print(f"  5. Trading resumes normally")
    
    print(f"\nRun backtest:")
    print(f"  python run_backtest.py --symbol SOLUSDT --capital 10000 --data {output_file}")
    
    print(f"\nWatch for logs:")
    print(f"  - CRITICAL: Hard stop activated")
    print(f"  - DEBUG: Resume cooldown checks")
    print(f"  - DEBUG: Resume RSI/price checks")
    print(f"  - INFO: Resume conditions met")
    print(f"  - WARNING: Trading resumed from hard stop")

if __name__ == '__main__':
    main()

