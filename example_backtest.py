"""
Simple backtest example
"""
from src.backtest.backtester import Backtester
from src.strategies import TrendFollowingStrategy, MeanReversionStrategy
from src.utils.config import config

# Initialize backtester
backtester = Backtester(
    initial_capital=10000.0,
    symbols=['BTCUSDT'],
    start_date='2023-01-01',
    end_date='2023-12-31'
)

# Load sample data (you need to download this first)
print("Loading historical data...")
try:
    backtester.load_data_from_csv('BTCUSDT', './data/BTCUSDT_15m.csv')
except FileNotFoundError:
    print("Error: Data file not found!")
    print("Please run: python download_data.py --symbols BTCUSDT")
    exit(1)

# Initialize strategies
print("Initializing strategies...")

# Trend Following Strategy
trend_config = {
    'enabled': True,
    'capital_allocation': 0.50,
    'ma_fast': 20,
    'ma_slow': 50,
    'adx_threshold': 25,
    'atr_multiplier': 2.0,
    'risk_reward_ratio': 2.0,
    'entry_method': 'ma_cross'
}

trend_strategy = TrendFollowingStrategy(
    'TrendFollowing',
    trend_config,
    backtester.portfolio,
    backtester.risk_manager
)
backtester.orchestrator.register_strategy(trend_strategy, priority=2)

# Mean Reversion Strategy
mean_rev_config = {
    'enabled': True,
    'capital_allocation': 0.30,
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'bb_period': 20,
    'bb_std': 2.0,
    'adx_max': 20,
    'atr_multiplier': 1.5,
    'entry_method': 'combined'
}

mean_rev_strategy = MeanReversionStrategy(
    'MeanReversion',
    mean_rev_config,
    backtester.portfolio,
    backtester.risk_manager
)
backtester.orchestrator.register_strategy(mean_rev_strategy, priority=3)

# Run backtest
print("\nRunning backtest...")
results = backtester.run()

# Print results
backtester.print_results()

# Save results
print("\nSaving results...")
backtester.save_results('./data/example_backtest_results.json')
backtester.get_equity_curve().to_csv('./data/example_equity_curve.csv')

trade_history = backtester.get_trade_history()
if not trade_history.empty:
    trade_history.to_csv('./data/example_trades.csv', index=False)
    print(f"Total trades: {len(trade_history)}")

print("\nBacktest completed!")

