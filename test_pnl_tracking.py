"""
Test script to demonstrate improved PnL tracking and trade export
"""
from src.core.portfolio import Portfolio
from src.utils.trade_exporter import TradeExporter


def test_pnl_tracking():
    """Test PnL tracking with sample trades"""
    
    print("\n" + "="*60)
    print("TESTING IMPROVED PNL TRACKING")
    print("="*60 + "\n")
    
    # Initialize portfolio
    portfolio = Portfolio(initial_capital=10000.0)
    print(f"Initial Capital: ${portfolio.initial_capital:,.2f}")
    print(f"Initial Cash: ${portfolio.cash:,.2f}\n")
    
    # Simulate some trades
    print("Simulating trades...\n")
    
    # Trade 1: Open LONG BTC
    print("1. Opening LONG position on BTCUSDT")
    portfolio.open_position(
        symbol='BTCUSDT',
        side='LONG',
        quantity=0.1,
        entry_price=50000.0,
        strategy='TrendFollowing'
    )
    
    # Trade 2: Open LONG ETH
    print("2. Opening LONG position on ETHUSDT")
    portfolio.open_position(
        symbol='ETHUSDT',
        side='LONG',
        quantity=2.0,
        entry_price=3000.0,
        strategy='MeanReversion'
    )
    
    # Trade 3: Close BTC with profit
    print("3. Closing BTCUSDT position with profit")
    portfolio.close_position(
        symbol='BTCUSDT',
        strategy='TrendFollowing',
        exit_price=52000.0  # +$200 profit
    )
    
    # Trade 4: Open SHORT SOL
    print("4. Opening SHORT position on SOLUSDT")
    portfolio.open_position(
        symbol='SOLUSDT',
        side='SHORT',
        quantity=50.0,
        entry_price=100.0,
        strategy='Grid'
    )
    
    # Trade 5: Close ETH with loss
    print("5. Closing ETHUSDT position with loss")
    portfolio.close_position(
        symbol='ETHUSDT',
        strategy='MeanReversion',
        exit_price=2900.0  # -$200 loss
    )
    
    # Trade 6: Close SOL with profit
    print("6. Closing SOLUSDT position with profit")
    portfolio.close_position(
        symbol='SOLUSDT',
        strategy='Grid',
        exit_price=95.0  # +$250 profit (SHORT)
    )
    
    print("\n" + "="*60)
    print("PORTFOLIO STATISTICS")
    print("="*60 + "\n")
    
    stats = portfolio.get_statistics()
    print(f"Final Cash: ${stats['cash']:,.2f}")
    print(f"Total PnL: ${stats['total_pnl']:,.2f}")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Winning Trades: {stats['winning_trades']}")
    print(f"Losing Trades: {stats['losing_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Avg Win: ${stats['avg_win']:,.2f}")
    print(f"Avg Loss: ${stats['avg_loss']:,.2f}")
    
    # Export trades
    print("\n" + "="*60)
    print("EXPORTING TRADE HISTORY")
    print("="*60 + "\n")
    
    # Export detailed report
    TradeExporter.export_detailed_report(
        portfolio.trade_history,
        './data/test_pnl_tracking'
    )
    
    # Print trade summary
    TradeExporter.print_trade_summary(portfolio.trade_history)
    
    # Show trade DataFrame
    print("\n" + "="*60)
    print("TRADE HISTORY DATAFRAME")
    print("="*60 + "\n")
    
    df = TradeExporter.format_trades_df(portfolio.trade_history)
    print(df.to_string())
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60 + "\n")
    
    print("Files generated:")
    print("  - ./data/test_pnl_tracking_trades.csv")
    print("  - ./data/test_pnl_tracking_summary.txt")
    print("\nCheck these files to see the improved format!")


if __name__ == '__main__':
    test_pnl_tracking()

