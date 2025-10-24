"""
Run backtest on historical data
"""
import argparse
from datetime import datetime

from src.backtest.backtester import Backtester
from src.strategies import (
    DCAStrategy,
    TrendFollowingStrategy,
    MeanReversionStrategy,
    GridStrategy
)
from src.utils.config import config


def main():
    """Main backtest function"""
    parser = argparse.ArgumentParser(description='Run backtest')
    parser.add_argument('--capital', type=float, default=10000.0,
                       help='Initial capital')
    parser.add_argument('--start', type=str, default='2023-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2023-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT', 'ETHUSDT'],
                       help='Trading symbols')
    parser.add_argument('--data-dir', type=str, default='./data',
                       help='Directory containing historical data CSV files')
    
    args = parser.parse_args()
    
    print("="*60)
    print("BINANCE TRADING BOT - BACKTEST MODE")
    print("="*60)
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Symbols: {', '.join(args.symbols)}")
    print("="*60 + "\n")
    
    # Initialize backtester
    backtester = Backtester(
        initial_capital=args.capital,
        symbols=args.symbols,
        start_date=args.start,
        end_date=args.end
    )
    
    # Load historical data
    print("Loading historical data...")
    for symbol in args.symbols:
        csv_file = f"{args.data_dir}/{symbol}_15m.csv"
        try:
            backtester.load_data_from_csv(symbol, csv_file)
            print(f"  ✓ Loaded {symbol}")
        except FileNotFoundError:
            print(f"  ✗ File not found: {csv_file}")
            print(f"    Please download historical data for {symbol}")
            continue
        except Exception as e:
            print(f"  ✗ Error loading {symbol}: {e}")
            continue
    
    # Initialize strategies
    print("\nInitializing strategies...")
    
    # Get strategy configs
    trend_config = config.get_strategy_config('trend_following')
    mean_rev_config = config.get_strategy_config('mean_reversion')
    dca_config = config.get_strategy_config('dca')
    grid_config = config.get_strategy_config('grid')
    
    # Enable strategies for backtest
    trend_config['enabled'] = True
    mean_rev_config['enabled'] = True
    
    # Create and register strategies
    if trend_config.get('enabled'):
        trend = TrendFollowingStrategy(
            'TrendFollowing',
            trend_config,
            backtester.portfolio,
            backtester.risk_manager
        )
        backtester.orchestrator.register_strategy(trend, priority=2)
        print("  ✓ Trend Following Strategy")
    
    if mean_rev_config.get('enabled'):
        mean_rev = MeanReversionStrategy(
            'MeanReversion',
            mean_rev_config,
            backtester.portfolio,
            backtester.risk_manager
        )
        backtester.orchestrator.register_strategy(mean_rev, priority=3)
        print("  ✓ Mean Reversion Strategy")
    
    if dca_config.get('enabled'):
        dca = DCAStrategy(
            'DCA',
            dca_config,
            backtester.portfolio,
            backtester.risk_manager
        )
        backtester.orchestrator.register_strategy(dca, priority=5)
        print("  ✓ DCA Strategy")
    
    if grid_config.get('enabled'):
        grid = GridStrategy(
            'Grid',
            grid_config,
            backtester.portfolio,
            backtester.risk_manager
        )
        backtester.orchestrator.register_strategy(grid, priority=4)
        print("  ✓ Grid Strategy")
    
    # Run backtest
    print("\nRunning backtest...\n")
    results = backtester.run()
    
    # Print results
    backtester.print_results()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"./data/backtest_results_{timestamp}.json"
    backtester.save_results(results_file)
    print(f"Results saved to: {results_file}")
    
    # Save equity curve
    equity_curve = backtester.get_equity_curve()
    equity_file = f"./data/equity_curve_{timestamp}.csv"
    equity_curve.to_csv(equity_file)
    print(f"Equity curve saved to: {equity_file}")
    
    # Save trade history
    trade_history = backtester.get_trade_history()
    if not trade_history.empty:
        trades_file = f"./data/trades_{timestamp}.csv"
        trade_history.to_csv(trades_file, index=False)
        print(f"Trade history saved to: {trades_file}")


if __name__ == '__main__':
    main()

