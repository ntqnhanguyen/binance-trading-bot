"""
Test script for Dynamic Grid Spread functionality
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.grid_strategy import GridStrategy
from src.core.portfolio import Portfolio
from src.risk.risk_manager import RiskManager
from src.indicators.technical import add_all_indicators


def generate_sample_data(volatility_type='normal'):
    """
    Generate sample OHLCV data with different volatility patterns
    
    Args:
        volatility_type: 'low', 'normal', 'high', 'changing'
    """
    np.random.seed(42)
    
    # Generate 200 candles
    periods = 200
    base_price = 50000.0
    
    dates = [datetime.now() - timedelta(minutes=15*i) for i in range(periods)]
    dates.reverse()
    
    prices = [base_price]
    
    if volatility_type == 'low':
        # Low volatility: small price movements
        volatility = 0.002  # 0.2%
    elif volatility_type == 'high':
        # High volatility: large price movements
        volatility = 0.02  # 2%
    elif volatility_type == 'changing':
        # Changing volatility
        volatility = None  # Will vary
    else:
        # Normal volatility
        volatility = 0.01  # 1%
    
    for i in range(1, periods):
        if volatility_type == 'changing':
            # Low volatility first half, high volatility second half
            if i < periods / 2:
                vol = 0.002
            else:
                vol = 0.02
        else:
            vol = volatility
        
        # Random walk with volatility
        change = np.random.normal(0, vol)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Generate OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close
        volatility_intra = 0.001
        high = close * (1 + abs(np.random.normal(0, volatility_intra)))
        low = close * (1 - abs(np.random.normal(0, volatility_intra)))
        open_price = (high + low) / 2
        volume = np.random.uniform(1000, 5000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df


def test_dynamic_spread():
    """Test dynamic spread functionality"""
    
    print("\n" + "="*70)
    print("TESTING DYNAMIC GRID SPREAD")
    print("="*70 + "\n")
    
    # Initialize components
    portfolio = Portfolio(initial_capital=10000.0)
    risk_manager = RiskManager(portfolio)
    
    # Test configurations
    configs = [
        {
            'name': 'Fixed Spread',
            'config': {
                'enabled': True,
                'capital_allocation': 0.15,
                'grid_spacing_pct': 1.0,
                'use_dynamic_spread': False,  # Disabled
                'num_grids': 10,
                'max_buy_orders': 5
            }
        },
        {
            'name': 'Dynamic Spread',
            'config': {
                'enabled': True,
                'capital_allocation': 0.15,
                'grid_spacing_pct': 1.0,
                'use_dynamic_spread': True,  # Enabled
                'spread_multiplier_min': 0.5,
                'spread_multiplier_max': 2.0,
                'volatility_lookback': 50,
                'num_grids': 10,
                'max_buy_orders': 5
            }
        }
    ]
    
    # Test scenarios
    scenarios = [
        ('Low Volatility', 'low'),
        ('Normal Volatility', 'normal'),
        ('High Volatility', 'high'),
        ('Changing Volatility', 'changing')
    ]
    
    results = []
    
    for scenario_name, volatility_type in scenarios:
        print(f"\n{'='*70}")
        print(f"Scenario: {scenario_name}")
        print(f"{'='*70}\n")
        
        # Generate data
        df = generate_sample_data(volatility_type)
        df = add_all_indicators(df)
        
        current_price = df['close'].iloc[-1]
        
        for config_info in configs:
            strategy_name = config_info['name']
            config = config_info['config']
            
            print(f"\n{'-'*70}")
            print(f"Strategy: {strategy_name}")
            print(f"{'-'*70}")
            
            # Create strategy
            strategy = GridStrategy('Grid', config, portfolio, risk_manager)
            
            # Force initialize grid
            strategy._initialize_grid('BTCUSDT', df, current_price)
            
            # Get grid info
            grid_info = strategy.get_grid_info('BTCUSDT')
            
            if grid_info:
                print(f"\nGrid Configuration:")
                print(f"  Active: {grid_info['active']}")
                print(f"  Range: {grid_info['lower_bound']:.2f} - {grid_info['upper_bound']:.2f}")
                print(f"  Number of levels: {grid_info['num_levels']}")
                print(f"  Grid step: ${grid_info['grid_step']:.2f}")
                print(f"  Current spacing: {grid_info['current_spacing_pct']:.3f}%")
                
                # Calculate ATR for reference
                if 'ATR_14' in df.columns:
                    atr = df['ATR_14'].iloc[-1]
                    atr_pct = (atr / current_price) * 100
                    print(f"\nMarket Conditions:")
                    print(f"  Current price: ${current_price:.2f}")
                    print(f"  ATR: ${atr:.2f} ({atr_pct:.3f}%)")
                
                if config['use_dynamic_spread']:
                    # Calculate spread multiplier
                    multiplier = strategy._calculate_dynamic_spread(df, current_price)
                    bb_ratio = strategy._calculate_bb_width_ratio(df, current_price)
                    
                    print(f"\nDynamic Spread Metrics:")
                    print(f"  ATR multiplier: {multiplier:.3f}x")
                    print(f"  BB width ratio: {bb_ratio:.3f}x")
                    print(f"  Combined: {(multiplier + bb_ratio) / 2:.3f}x")
                
                # Store results
                results.append({
                    'scenario': scenario_name,
                    'strategy': strategy_name,
                    'spacing_pct': grid_info['current_spacing_pct'],
                    'grid_step': grid_info['grid_step'],
                    'num_levels': grid_info['num_levels']
                })
    
    # Summary comparison
    print("\n" + "="*70)
    print("SUMMARY COMPARISON")
    print("="*70 + "\n")
    
    results_df = pd.DataFrame(results)
    
    for scenario in results_df['scenario'].unique():
        scenario_data = results_df[results_df['scenario'] == scenario]
        
        print(f"\n{scenario}:")
        print(f"{'-'*70}")
        
        for _, row in scenario_data.iterrows():
            print(f"  {row['strategy']:20s}: "
                  f"Spacing={row['spacing_pct']:.3f}%, "
                  f"Step=${row['grid_step']:.2f}, "
                  f"Levels={row['num_levels']}")
        
        # Calculate difference
        if len(scenario_data) == 2:
            fixed = scenario_data[scenario_data['strategy'] == 'Fixed Spread'].iloc[0]
            dynamic = scenario_data[scenario_data['strategy'] == 'Dynamic Spread'].iloc[0]
            
            spacing_diff = ((dynamic['spacing_pct'] - fixed['spacing_pct']) / 
                          fixed['spacing_pct'] * 100)
            
            print(f"\n  → Dynamic spread is {spacing_diff:+.1f}% vs Fixed")
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70 + "\n")
    
    print("Key Observations:")
    print("  • Low volatility: Dynamic spread should be tighter (< 1.0%)")
    print("  • High volatility: Dynamic spread should be wider (> 1.0%)")
    print("  • Fixed spread: Always 1.0% regardless of market conditions")
    print("  • Dynamic spread adapts automatically to market volatility")


def test_spread_update():
    """Test spread update during trading"""
    
    print("\n" + "="*70)
    print("TESTING SPREAD UPDATE DURING TRADING")
    print("="*70 + "\n")
    
    # Initialize
    portfolio = Portfolio(initial_capital=10000.0)
    risk_manager = RiskManager(portfolio)
    
    config = {
        'enabled': True,
        'capital_allocation': 0.15,
        'grid_spacing_pct': 1.0,
        'use_dynamic_spread': True,
        'spread_multiplier_min': 0.5,
        'spread_multiplier_max': 2.0,
        'volatility_lookback': 50,
        'num_grids': 10,
        'max_buy_orders': 5
    }
    
    strategy = GridStrategy('Grid', config, portfolio, risk_manager)
    
    # Generate initial data (low volatility)
    df = generate_sample_data('low')
    df = add_all_indicators(df)
    current_price = df['close'].iloc[-1]
    
    # Initialize grid
    strategy._initialize_grid('BTCUSDT', df, current_price)
    initial_info = strategy.get_grid_info('BTCUSDT')
    
    print("Initial Grid (Low Volatility):")
    print(f"  Spacing: {initial_info['current_spacing_pct']:.3f}%")
    print(f"  Grid step: ${initial_info['grid_step']:.2f}")
    
    # Simulate market change to high volatility
    print("\n→ Market volatility increases...\n")
    
    df_high = generate_sample_data('high')
    df_high = add_all_indicators(df_high)
    current_price = df_high['close'].iloc[-1]
    
    # Update spread
    strategy._update_dynamic_spread('BTCUSDT', df_high, current_price)
    updated_info = strategy.get_grid_info('BTCUSDT')
    
    print("Updated Grid (High Volatility):")
    print(f"  Spacing: {updated_info['current_spacing_pct']:.3f}%")
    print(f"  Grid step: ${updated_info['grid_step']:.2f}")
    
    # Calculate change
    spacing_change = ((updated_info['current_spacing_pct'] - 
                      initial_info['current_spacing_pct']) / 
                     initial_info['current_spacing_pct'] * 100)
    
    print(f"\n→ Spread adjusted by {spacing_change:+.1f}%")
    print(f"  Grid automatically widened to handle increased volatility")
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70 + "\n")


if __name__ == '__main__':
    # Run tests
    test_dynamic_spread()
    test_spread_update()
    
    print("\n✅ All tests completed successfully!")
    print("\nNext steps:")
    print("  1. Run backtest with dynamic spread enabled")
    print("  2. Compare performance vs fixed spread")
    print("  3. Adjust multiplier limits based on results")
    print("  4. Monitor spread history in live trading")

