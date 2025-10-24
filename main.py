"""
Main entry point for Binance Trading Bot
"""
import time
from datetime import datetime
from typing import Dict

from src.utils.logger import TradingLogger
from src.utils.config import config
from src.utils.trade_exporter import TradeExporter
from src.core.exchange import BinanceExchange
from src.core.portfolio import Portfolio
from src.risk.risk_manager import RiskManager
from src.orchestrator.strategy_orchestrator import StrategyOrchestrator
from src.strategies import (
    DCAStrategy,
    TrendFollowingStrategy,
    MeanReversionStrategy,
    GridStrategy
)
from src.indicators.technical import add_all_indicators


class TradingBot:
    """Main trading bot class"""
    
    def __init__(self):
        """Initialize trading bot"""
        self.logger = TradingLogger.get_logger(__name__)
        
        # Get trading mode
        self.mode = config.get_trading_mode()
        self.logger.info(f"Initializing Trading Bot in {self.mode.upper()} mode")
        
        # Initialize components
        self.exchange = BinanceExchange(self.mode)
        
        # Get initial capital
        if self.mode == 'backtest':
            initial_capital = config.get('backtest.initial_capital', 10000.0)
        else:
            # Get from account balance
            balances = self.exchange.get_account_balance()
            # Use USDT balance as initial capital
            initial_capital = balances.get('USDT', {}).get('total', 10000.0)
        
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(self.portfolio)
        self.orchestrator = StrategyOrchestrator(
            self.exchange,
            self.portfolio,
            self.risk_manager
        )
        
        # Initialize strategies
        self._initialize_strategies()
        
        # Trading symbols
        self.symbols = config.get('trading.symbols', ['BTCUSDT', 'ETHUSDT'])
        
        # Trading interval (in seconds)
        self.interval = config.get('trading.interval', 300)  # 5 minutes default
        
        self.running = False
        
        self.logger.info(
            f"Trading Bot initialized | Capital: {initial_capital} | "
            f"Symbols: {self.symbols}"
        )
    
    def _initialize_strategies(self):
        """Initialize and register trading strategies"""
        # Get strategy configs
        dca_config = config.get_strategy_config('dca')
        trend_config = config.get_strategy_config('trend_following')
        mean_rev_config = config.get_strategy_config('mean_reversion')
        grid_config = config.get_strategy_config('grid')
        
        # Create strategy instances
        strategies = []
        
        if dca_config.get('enabled', False):
            dca = DCAStrategy(
                'DCA',
                dca_config,
                self.portfolio,
                self.risk_manager
            )
            strategies.append((5, dca))  # Priority 5 (lowest)
        
        if trend_config.get('enabled', True):
            trend = TrendFollowingStrategy(
                'TrendFollowing',
                trend_config,
                self.portfolio,
                self.risk_manager
            )
            strategies.append((2, trend))  # Priority 2 (high)
        
        if mean_rev_config.get('enabled', True):
            mean_rev = MeanReversionStrategy(
                'MeanReversion',
                mean_rev_config,
                self.portfolio,
                self.risk_manager
            )
            strategies.append((3, mean_rev))  # Priority 3 (medium)
        
        if grid_config.get('enabled', False):
            grid = GridStrategy(
                'Grid',
                grid_config,
                self.portfolio,
                self.risk_manager
            )
            strategies.append((4, grid))  # Priority 4 (low)
        
        # Register strategies with orchestrator
        for priority, strategy in strategies:
            self.orchestrator.register_strategy(strategy, priority)
    
    def run(self):
        """Run the trading bot"""
        self.running = True
        self.logger.info("Trading Bot started")
        
        try:
            while self.running:
                self._trading_loop()
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _trading_loop(self):
        """Main trading loop iteration"""
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"Trading loop iteration at {datetime.now()}")
            
            # Get current prices
            current_prices = {}
            
            # Process each symbol
            for symbol in self.symbols:
                try:
                    # Get market data
                    df = self.exchange.get_klines(
                        symbol,
                        interval='15m',
                        limit=200
                    )
                    
                    if df.empty:
                        self.logger.warning(f"No data received for {symbol}")
                        continue
                    
                    # Add technical indicators
                    df = add_all_indicators(df)
                    
                    # Get current price
                    current_price = df['close'].iloc[-1]
                    current_prices[symbol] = current_price
                    
                    self.logger.info(f"Processing {symbol} @ {current_price}")
                    
                    # Generate and execute signals
                    signals = self.orchestrator.process_symbol(
                        symbol,
                        df,
                        current_price
                    )
                    
                    if signals:
                        executed = self.orchestrator.execute_signals(signals)
                        self.logger.info(
                            f"Executed {executed}/{len(signals)} signals for {symbol}"
                        )
                
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            # Update portfolio metrics
            equity = self.portfolio.get_equity(current_prices)
            stats = self.portfolio.get_statistics()
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # Log status
            self.logger.info(
                f"Portfolio | Equity: {equity:.2f} | Cash: {stats['cash']:.2f} | "
                f"Positions: {stats['open_positions']} | "
                f"Daily PnL: {stats['daily_pnl']:.2f}"
            )
            
            self.logger.info(
                f"Risk | Circuit Breaker: {risk_metrics['circuit_breaker_active']} | "
                f"Daily Limit Used: {risk_metrics['daily_limit_used']:.1f}% | "
                f"Cash Reserve: {risk_metrics['cash_reserve_pct']:.1f}%"
            )
            
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        
        # Export final trade report
        if self.portfolio.trade_history:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_prefix = f"./data/final_trades_{timestamp}"
            TradeExporter.export_detailed_report(self.portfolio.trade_history, report_prefix)
            self.logger.info(f"Final trade report exported: {report_prefix}")
        
        # Print final statistics
        stats = self.portfolio.get_statistics()
        orchestrator_stats = self.orchestrator.get_statistics()
        
        self.logger.info("=" * 60)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Trades: {stats['total_trades']}")
        self.logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
        self.logger.info(f"Total PnL: {stats['total_pnl']:.2f}")
        self.logger.info(f"Open Positions: {stats['open_positions']}")
        self.logger.info("=" * 60)
        
        # Print trade summary
        if self.portfolio.trade_history:
            TradeExporter.print_trade_summary(self.portfolio.trade_history)
        
        for strategy_name, strategy_stats in orchestrator_stats['strategies'].items():
            self.logger.info(
                f"{strategy_name}: Signals={strategy_stats['signals_generated']}, "
                f"Trades={strategy_stats['trades_executed']}, "
                f"PnL={strategy_stats['total_pnl']:.2f}"
            )
        
        self.logger.info("Trading Bot stopped")


def main():
    """Main function"""
    bot = TradingBot()
    bot.run()


if __name__ == '__main__':
    main()

