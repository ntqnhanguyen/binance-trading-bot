"""
Backtesting engine for strategy testing
"""
from typing import Dict, List
import pandas as pd
from datetime import datetime
import json

from ..utils.logger import TradingLogger
from ..core.portfolio import Portfolio
from ..risk.risk_manager import RiskManager
from ..orchestrator.strategy_orchestrator import StrategyOrchestrator
from ..indicators.technical import add_all_indicators


class Backtester:
    """
    Backtesting engine for historical data testing
    """
    
    def __init__(self, initial_capital: float, symbols: List[str],
                 start_date: str, end_date: str):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital
            symbols: List of symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        self.logger = TradingLogger.get_logger(__name__)
        
        self.initial_capital = initial_capital
        self.symbols = symbols
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        
        # Initialize components
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(self.portfolio)
        self.orchestrator = StrategyOrchestrator(None, self.portfolio, self.risk_manager)
        
        # Historical data
        self.historical_data: Dict[str, pd.DataFrame] = {}
        
        # Performance tracking
        self.equity_curve = []
        self.trade_log = []
        
        self.logger.info(
            f"Backtester initialized | Capital: {initial_capital} | "
            f"Period: {start_date} to {end_date}"
        )
    
    def load_historical_data(self, symbol: str, df: pd.DataFrame):
        """
        Load historical data for a symbol
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV data
        """
        # Filter by date range
        df_filtered = df[
            (df.index >= self.start_date) & 
            (df.index <= self.end_date)
        ].copy()
        # Add technical indicators
        df_filtered = add_all_indicators(df_filtered)
        
        self.historical_data[symbol] = df_filtered
        
        self.logger.info(
            f"Loaded {len(df_filtered)} bars for {symbol} "
            f"({df_filtered.index[0]} to {df_filtered.index[-1]})"
        )
    
    def load_data_from_csv(self, symbol: str, filepath: str):
        """
        Load historical data from CSV file
        
        Args:
            symbol: Trading pair symbol
            filepath: Path to CSV file
        """
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        self.load_historical_data(symbol, df)
    
    def run(self) -> Dict:
        """
        Run backtest
        
        Returns:
            Backtest results dictionary
        """
        self.logger.info("Starting backtest...")
        
        if not self.historical_data:
            self.logger.error("No historical data loaded")
            return {}
        
        # Get common date range across all symbols
        all_dates = set()
        for df in self.historical_data.values():
            all_dates.update(df.index)
        
        dates = sorted(list(all_dates))
        
        # Iterate through each timestamp
        for i, current_date in enumerate(dates):
            # Reset daily/weekly stats if needed
            self.portfolio.reset_daily_stats()
            self.portfolio.reset_weekly_stats()
            
            # Get current prices
            current_prices = {}
            
            # Process each symbol
            for symbol in self.symbols:
                if symbol not in self.historical_data:
                    continue
                
                df = self.historical_data[symbol]
                
                # Get data up to current date
                historical_slice = df[df.index <= current_date]
                
                if len(historical_slice) < 50:  # Need minimum data
                    continue
                
                current_price = historical_slice['close'].iloc[-1]
                current_prices[symbol] = current_price
                
                # Generate and execute signals
                signals = self.orchestrator.process_symbol(
                    symbol,
                    historical_slice,
                    current_price
                )
                
                if signals:
                    self.orchestrator.execute_signals(signals)
            
            # Update portfolio value
            equity = self.portfolio.get_equity(current_prices)
            self.equity_curve.append({
                'date': current_date,
                'equity': equity,
                'cash': self.portfolio.cash,
                'positions': len(self.portfolio.positions)
            })
            
            # Log progress
            if i % 100 == 0:
                progress = (i / len(dates)) * 100
                self.logger.info(
                    f"Backtest progress: {progress:.1f}% | "
                    f"Date: {current_date.date()} | "
                    f"Equity: {equity:.2f}"
                )
        
        # Calculate results
        results = self._calculate_results()
        
        self.logger.info("Backtest completed")
        return results
    
    def _calculate_results(self) -> Dict:
        """Calculate backtest performance metrics"""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # Performance metrics
        total_return = (equity_df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Maximum drawdown
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Sharpe ratio (annualized, assuming daily data)
        mean_return = equity_df['returns'].mean()
        std_return = equity_df['returns'].std()
        sharpe_ratio = (mean_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
        
        # Win rate and trade stats
        portfolio_stats = self.portfolio.get_statistics()
        
        # CAGR
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 365.25
        cagr = ((equity_df['equity'].iloc[-1] / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        results = {
            'initial_capital': self.initial_capital,
            'final_equity': equity_df['equity'].iloc[-1],
            'total_return_pct': total_return,
            'cagr_pct': cagr,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': portfolio_stats['total_trades'],
            'winning_trades': portfolio_stats['winning_trades'],
            'losing_trades': portfolio_stats['losing_trades'],
            'win_rate_pct': portfolio_stats['win_rate'],
            'avg_win': portfolio_stats['avg_win'],
            'avg_loss': portfolio_stats['avg_loss'],
            'profit_factor': abs(portfolio_stats['avg_win'] / portfolio_stats['avg_loss']) if portfolio_stats['avg_loss'] != 0 else 0,
            'start_date': equity_df.index[0].isoformat(),
            'end_date': equity_df.index[-1].isoformat(),
            'days': days
        }
        
        return results
    
    def get_equity_curve(self) -> pd.DataFrame:
        """
        Get equity curve as DataFrame
        
        Returns:
            DataFrame with equity curve
        """
        return pd.DataFrame(self.equity_curve)
    
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get trade history
        
        Returns:
            DataFrame with trade history
        """
        return self.portfolio.get_trade_history_df()
    
    def save_results(self, filepath: str):
        """
        Save backtest results to file
        
        Args:
            filepath: Path to save results
        """
        results = self._calculate_results()
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to {filepath}")
    
    def print_results(self):
        """Print backtest results"""
        results = self._calculate_results()
        
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Period: {results['start_date']} to {results['end_date']} ({results['days']} days)")
        print(f"\nCapital:")
        print(f"  Initial: ${results['initial_capital']:,.2f}")
        print(f"  Final:   ${results['final_equity']:,.2f}")
        print(f"\nReturns:")
        print(f"  Total Return: {results['total_return_pct']:.2f}%")
        print(f"  CAGR:         {results['cagr_pct']:.2f}%")
        print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"\nTrades:")
        print(f"  Total:   {results['total_trades']}")
        print(f"  Winners: {results['winning_trades']}")
        print(f"  Losers:  {results['losing_trades']}")
        print(f"  Win Rate: {results['win_rate_pct']:.2f}%")
        print(f"\nP&L:")
        print(f"  Avg Win:  ${results['avg_win']:.2f}")
        print(f"  Avg Loss: ${results['avg_loss']:.2f}")
        print(f"  Profit Factor: {results['profit_factor']:.2f}")
        print("="*60 + "\n")

