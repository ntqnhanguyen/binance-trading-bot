"""
Live Trading Bot with Hybrid Strategy Engine

Runs live trading using Grid + DCA hybrid strategy with dynamic spread,
PnL Gate, and Stop-Loss management.
"""
import os
import time
import yaml
import signal
from datetime import datetime
from typing import Dict, List

from src.utils.logger import TradingLogger
from src.utils.config import config
from src.core.exchange import BinanceExchange
from src.core.portfolio import Portfolio
from src.strategies.hybrid_strategy_engine import HybridStrategyEngine
from src.indicators.indicator_engine import IndicatorEngine
from src.indicators.technical import add_all_indicators


class HybridTradingBot:
    """
    Live trading bot using Hybrid Strategy Engine
    """
    
    def __init__(self, symbols: List[str], hybrid_config_path: str):
        """
        Initialize trading bot
        
        Args:
            symbols: List of trading pairs
            hybrid_config_path: Path to hybrid strategy config
        """
        self.symbols = symbols
        self.running = False
        
        # Initialize logger
        self.logger = TradingLogger.get_logger('HybridBot')
        
        # Load hybrid strategy config
        with open(hybrid_config_path, 'r') as f:
            self.hybrid_config = yaml.safe_load(f)
        
        # Initialize exchange
        self.exchange = BinanceExchange(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET'),
            testnet=(os.getenv('TRADING_MODE', 'paper') == 'testnet')
        )
        
        # Initialize portfolio
        initial_capital = float(os.getenv('INITIAL_CAPITAL', '10000'))
        self.portfolio = Portfolio(initial_capital=initial_capital)
        
        # Initialize strategy engines per symbol
        self.strategy_engines: Dict[str, HybridStrategyEngine] = {}
        self.indicator_engines: Dict[str, IndicatorEngine] = {}
        
        for symbol in symbols:
            # Get policy config
            policy_cfg = self._get_policy_config(symbol)
            
            # Initialize engines
            indicator_engine = IndicatorEngine(symbol)
            strategy_engine = HybridStrategyEngine(symbol, policy_cfg, indicator_engine)
            
            self.indicator_engines[symbol] = indicator_engine
            self.strategy_engines[symbol] = strategy_engine
        
        # Trading state
        self.pending_orders: Dict[str, List] = {symbol: [] for symbol in symbols}
        
        # Interval
        self.interval = int(os.getenv('TRADING_INTERVAL', '60'))  # seconds
        
        self.logger.info(f"HybridTradingBot initialized: {symbols}")
    
    def _get_policy_config(self, symbol: str) -> dict:
        """Get policy config for symbol"""
        default_policy = self.hybrid_config['default_policy']
        
        # Check for pair-specific config
        if symbol in self.hybrid_config.get('pairs', {}):
            policy_cfg = default_policy.copy()
            policy_cfg.update(self.hybrid_config['pairs'][symbol])
            self.logger.info(f"Using pair-specific config for {symbol}")
        else:
            policy_cfg = default_policy
            self.logger.info(f"Using default policy for {symbol}")
        
        return policy_cfg
    
    def run(self):
        """Run the trading bot"""
        self.running = True
        self.logger.info("Hybrid Trading Bot started")
        
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
            self.logger.info(f"Trading loop at {datetime.now()}")
            
            # Calculate current equity
            current_prices = {}
            for symbol in self.symbols:
                try:
                    ticker = self.exchange.get_ticker(symbol)
                    current_prices[symbol] = float(ticker['lastPrice'])
                except Exception as e:
                    self.logger.error(f"Error getting ticker for {symbol}: {e}")
                    continue
            
            equity = self.portfolio.get_equity(current_prices)
            
            self.logger.info(f"Portfolio Equity: ${equity:,.2f}")
            
            # Process each symbol
            for symbol in self.symbols:
                try:
                    self._process_symbol(symbol, current_prices.get(symbol), equity)
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)
            
            # Check fills
            self._check_fills()
            
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)
    
    def _process_symbol(self, symbol: str, current_price: float, equity: float):
        """Process a single symbol"""
        if current_price is None:
            return
        
        self.logger.info(f"Processing {symbol} @ ${current_price:.2f}")
        
        # Get market data
        df = self.exchange.get_klines(
            symbol,
            interval='1m',
            limit=200
        )
        
        if df.empty:
            self.logger.warning(f"No data for {symbol}")
            return
        
        # Add indicators
        df = add_all_indicators(df)
        
        # Update indicator engine
        self.indicator_engines[symbol].update(df)
        
        # Get current bar
        latest = df.iloc[-1]
        bar = {
            'timestamp': latest['timestamp'] if 'timestamp' in df.columns else datetime.now(),
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest['volume']
        }
        
        # Generate plan
        strategy_engine = self.strategy_engines[symbol]
        plan = strategy_engine.on_bar(bar, equity)
        
        self.logger.info(
            f"{symbol} Plan: State={plan['pnl_gate_state']}, "
            f"Band={plan['band']}, Spread={plan['spread_pct']:.3f}%, "
            f"Grid={len(plan['grid_orders'])}, DCA={len(plan['dca_orders'])}, "
            f"TP={len(plan['tp_orders'])}"
        )
        
        # Check hard stop
        if plan['sl_action']['stop']:
            self.logger.critical(
                f"Hard stop triggered for {symbol}: {plan['sl_action']['reason']}"
            )
            self._close_all_positions(symbol, current_price)
            return
        
        # Execute orders based on state
        if plan['pnl_gate_state'] == 'RUN':
            # Full operation
            if plan['kill_replace']:
                self._cancel_grid_orders(symbol)
            
            self._place_orders(symbol, plan['grid_orders'], current_price)
            self._place_orders(symbol, plan['dca_orders'], current_price)
            self._place_orders(symbol, plan['tp_orders'], current_price)
        
        elif plan['pnl_gate_state'] == 'DEGRADED':
            # Reduced operation
            self._place_orders(symbol, plan['dca_orders'], current_price)
            self._place_orders(symbol, plan['tp_orders'], current_price)
        
        # PAUSED: no new orders
        elif plan['pnl_gate_state'] == 'PAUSED':
            self.logger.warning(f"{symbol} in PAUSED state - no new orders")
    
    def _place_orders(self, symbol: str, orders: List[dict], current_price: float):
        """Place orders"""
        for order in orders:
            try:
                # Calculate quantity (1% of equity per order)
                equity = self.portfolio.get_equity({symbol: current_price})
                order_value = equity * 0.01
                qty = order_value / order['price']
                
                # Round to exchange precision
                qty = self._round_quantity(symbol, qty)
                
                # Check minimum order value
                min_notional = 11.0  # Binance minimum
                if qty * order['price'] < min_notional:
                    self.logger.debug(
                        f"Order too small: {qty} * {order['price']} < {min_notional}"
                    )
                    continue
                
                # Place order (limit order)
                side = order['side']
                price = order['price']
                tag = order.get('tag', '')
                
                # In paper/testnet mode, just track orders
                trading_mode = os.getenv('TRADING_MODE', 'paper')
                
                if trading_mode == 'paper':
                    # Paper trading - just track
                    pending_order = {
                        'symbol': symbol,
                        'side': side,
                        'price': price,
                        'qty': qty,
                        'tag': tag,
                        'timestamp': datetime.now()
                    }
                    self.pending_orders[symbol].append(pending_order)
                    
                    self.logger.info(
                        f"Paper order: {side} {qty:.4f} {symbol} @ ${price:.2f} [{tag}]"
                    )
                else:
                    # Real trading
                    order_result = self.exchange.place_limit_order(
                        symbol=symbol,
                        side=side,
                        quantity=qty,
                        price=price
                    )
                    
                    self.logger.info(
                        f"Order placed: {side} {qty:.4f} {symbol} @ ${price:.2f} "
                        f"[{tag}] OrderID={order_result.get('orderId')}"
                    )
            
            except Exception as e:
                self.logger.error(f"Error placing order: {e}")
    
    def _check_fills(self):
        """Check for filled orders"""
        trading_mode = os.getenv('TRADING_MODE', 'paper')
        
        if trading_mode == 'paper':
            # Paper trading - simulate fills
            for symbol in self.symbols:
                try:
                    current_price = float(self.exchange.get_ticker(symbol)['lastPrice'])
                    
                    filled_orders = []
                    for order in self.pending_orders[symbol]:
                        # Simple fill logic
                        if order['side'] == 'BUY' and current_price <= order['price']:
                            self._fill_order(order, order['price'])
                            filled_orders.append(order)
                        elif order['side'] == 'SELL' and current_price >= order['price']:
                            self._fill_order(order, order['price'])
                            filled_orders.append(order)
                    
                    # Remove filled orders
                    for order in filled_orders:
                        self.pending_orders[symbol].remove(order)
                
                except Exception as e:
                    self.logger.error(f"Error checking fills for {symbol}: {e}")
        else:
            # Real trading - check with exchange
            # TODO: Implement real order tracking
            pass
    
    def _fill_order(self, order: dict, fill_price: float):
        """Process filled order"""
        symbol = order['symbol']
        side = order['side']
        qty = order['qty']
        tag = order['tag']
        
        if side == 'BUY':
            # Open position
            self.portfolio.open_position(
                symbol=symbol,
                side='LONG',
                quantity=qty,
                entry_price=fill_price,
                strategy='Hybrid'
            )
            
            # Notify DCA fill
            if 'dca' in tag:
                self.strategy_engines[symbol].notify_dca_fill(fill_price)
            
            self.logger.info(
                f"BUY filled: {qty:.4f} {symbol} @ ${fill_price:.2f} [{tag}]"
            )
        else:
            # Close position
            self.portfolio.close_position(
                symbol=symbol,
                strategy='Hybrid',
                exit_price=fill_price
            )
            
            self.logger.info(
                f"SELL filled: {qty:.4f} {symbol} @ ${fill_price:.2f} [{tag}]"
            )
    
    def _cancel_grid_orders(self, symbol: str):
        """Cancel grid orders for symbol"""
        self.pending_orders[symbol] = [
            order for order in self.pending_orders[symbol]
            if 'grid' not in order['tag']
        ]
        self.logger.info(f"Grid orders cancelled for {symbol}")
    
    def _close_all_positions(self, symbol: str, price: float):
        """Close all positions for symbol"""
        position = self.portfolio.get_position(symbol, 'Hybrid')
        
        if position:
            self.portfolio.close_position(
                symbol=symbol,
                strategy='Hybrid',
                exit_price=price
            )
            self.logger.info(f"Position closed: {symbol} @ ${price:.2f}")
    
    def _round_quantity(self, symbol: str, qty: float) -> float:
        """Round quantity to exchange precision"""
        # Simple rounding to 4 decimals
        # TODO: Get actual lot size from exchange
        return round(qty, 4)
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        
        # Print final statistics
        stats = self.portfolio.get_statistics()
        
        self.logger.info("=" * 60)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Trades: {stats['total_trades']}")
        self.logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
        self.logger.info(f"Total PnL: ${stats['total_pnl']:.2f}")
        self.logger.info(f"Open Positions: {stats['open_positions']}")
        self.logger.info("=" * 60)
        
        # Export trades
        if self.portfolio.trade_history:
            from src.utils.trade_exporter import TradeExporter
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_prefix = f"./data/hybrid_live_trades_{timestamp}"
            TradeExporter.export_detailed_report(self.portfolio.trade_history, report_prefix)
            self.logger.info(f"Trade report exported: {report_prefix}")


def main():
    """Main entry point"""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get symbols
    symbols_str = os.getenv('TRADING_SYMBOLS', 'BTCUSDT')
    symbols = [s.strip() for s in symbols_str.split(',')]
    
    # Get config path
    hybrid_config = os.getenv('HYBRID_CONFIG', 'config/hybrid_strategy.yaml')
    
    print("\n" + "="*60)
    print("HYBRID STRATEGY LIVE TRADING BOT")
    print("="*60)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Config: {hybrid_config}")
    print(f"Mode: {os.getenv('TRADING_MODE', 'paper')}")
    print("="*60 + "\n")
    
    # Create bot
    bot = HybridTradingBot(symbols, hybrid_config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\nShutdown signal received...")
        bot.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run bot
    bot.run()


if __name__ == '__main__':
    main()

