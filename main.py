"""
Live Trading Bot with Hybrid Strategy Engine

Runs live trading using Grid + DCA hybrid strategy with dynamic spread,
PnL Gate, and Stop-Loss management.

Version: 2.5.0 - Enhanced logging with colored console output
"""
import os
import time
import yaml
import signal
from datetime import datetime
from typing import Dict, List

from src.utils.logger import TradingLogger
from src.utils.config import config
from src.utils.console_logger import ConsoleLogger
from src.utils.order_logger import OrderLogger
from src.core.exchange import BinanceExchange
from src.core.portfolio import Portfolio
from src.strategies.hybrid_strategy_engine import HybridStrategyEngine
from src.indicators.indicator_engine import IndicatorEngine
from src.indicators.technical import add_all_indicators


class HybridTradingBot:
    """
    Live trading bot using Hybrid Strategy Engine with enhanced logging
    """
    
    def __init__(self, symbols: List[str], config_path_path: str):
        """
        Initialize trading bot
        
        Args:
            symbols: List of trading pairs
            config_path_path: Path to hybrid strategy config
        """
        self.symbols = symbols
        self.running = False
        
        # Initialize logger
        self.logger = TradingLogger.get_logger('HybridBot')
        
        # Initialize console logger (colored output)
        enable_colors = os.getenv('ENABLE_COLORS', 'true').lower() == 'true'
        self.console = ConsoleLogger(self.logger, enable_colors=enable_colors)
        
        # Initialize order logger
        output_dir = os.getenv('OUTPUT_DIR', './data/outputs')
        self.order_logger = OrderLogger(output_dir=output_dir)
        
        # Load hybrid strategy config
        with open(config_path_path, 'r') as f:
            self.config_path = yaml.safe_load(f)
        
        # Initialize exchange
        trading_mode = os.getenv('TRADING_MODE', 'paper')
        self.exchange = BinanceExchange(mode=trading_mode)
        
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
        
        # Trading mode
        self.trading_mode = trading_mode
        
        self.console.print_success(f"HybridTradingBot initialized: {symbols}")
        self.console.print_info(f"Trading Mode: {trading_mode.upper()}")
        self.console.print_info(f"Initial Capital: ${initial_capital:,.2f}")
    
    def _get_policy_config(self, symbol: str) -> dict:
        """Get policy config for symbol"""
        default_policy = self.config_path['default_policy']
        
        # Check for pair-specific config
        if symbol in self.config_path.get('pairs', {}):
            policy_cfg = default_policy.copy()
            policy_cfg.update(self.config_path['pairs'][symbol])
            self.logger.info(f"Using pair-specific config for {symbol}")
        else:
            policy_cfg = default_policy
            self.logger.info(f"Using default policy for {symbol}")
        
        return policy_cfg
    
    def run(self):
        """Run the trading bot"""
        self.running = True
        self.console.print_header("HYBRID TRADING BOT STARTED")
        
        try:
            while self.running:
                self._trading_loop()
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            self.console.print_warning("Received shutdown signal")
        except Exception as e:
            self.console.print_error(f"Unexpected error: {e}")
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _trading_loop(self):
        """Main trading loop iteration"""
        try:
            self.console.print_header(f"Trading Loop - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Calculate current equity
            current_prices = {}
            for symbol in self.symbols:
                try:
                    ticker = self.exchange.get_ticker(symbol)
                    current_prices[symbol] = float(ticker['price'])
                except Exception as e:
                    self.console.print_error(f"Error getting ticker for {symbol}: {e}")
                    continue
            
            # Get portfolio metrics
            equity = self.portfolio.get_equity(current_prices)
            cash = self.portfolio.cash
            
            # Calculate position value
            position_value = 0.0
            for symbol in self.symbols:
                position = self.portfolio.get_position(symbol, 'Hybrid')
                if position and symbol in current_prices:
                    position_value += position['quantity'] * current_prices[symbol]
            
            # Display equity
            self.console.print_equity(equity, cash, position_value)
            
            # Process each symbol
            for symbol in self.symbols:
                try:
                    self._process_symbol(symbol, current_prices.get(symbol), equity)
                except Exception as e:
                    self.console.print_error(f"Error processing {symbol}: {e}")
                    self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)
            
            # Manage pending orders (cancel stale orders)
            self._manage_pending_orders(current_prices)
            
            # Check fills
            self._check_fills()
            
            # Display positions
            self._display_positions(current_prices)
            
        except Exception as e:
            self.console.print_error(f"Error in trading loop: {e}")
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)
    
    def _process_symbol(self, symbol: str, current_price: float, equity: float):
        """Process a single symbol"""
        if current_price is None:
            return
        
        self.console.print_section(f"{symbol} @ ${current_price:.2f}")
        
        # Get market data
        df = self.exchange.get_klines(
            symbol,
            interval='1m',
            limit=200
        )
        
        if df.empty:
            self.console.print_warning(f"No data for {symbol}")
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
        
        # Display plan summary
        self.console.print_order_plan(
            symbol=symbol,
            band=plan['band'],
            spread_pct=plan['spread_pct'],
            grid_count=len(plan['grid_orders']),
            dca_count=len(plan['dca_orders']),
            tp_count=len(plan['tp_orders'])
        )
        
        # Display PnL state
        self.console.print_pnl_state(plan['pnl_gate_state'])
        
        # Check hard stop
        if plan['sl_action']['stop']:
            self.console.print_hard_stop(symbol, plan['sl_action']['reason'])
            self._close_all_positions(symbol, current_price)
            return
        
        # Execute orders based on state
        if plan['pnl_gate_state'] == 'RUN':
            # Full operation
            if plan['kill_replace']:
                self._cancel_grid_orders(symbol)
            
            self._place_orders(symbol, plan['grid_orders'], current_price, 'GRID')
            self._place_orders(symbol, plan['dca_orders'], current_price, 'DCA')
            self._place_orders(symbol, plan['tp_orders'], current_price, 'TP')
        
        elif plan['pnl_gate_state'] == 'DEGRADED':
            # Reduced operation
            self.console.print_warning(f"{symbol} in DEGRADED mode - Grid orders disabled")
            self._place_orders(symbol, plan['dca_orders'], current_price, 'DCA')
            self._place_orders(symbol, plan['tp_orders'], current_price, 'TP')
        
        # PAUSED: no new orders
        elif plan['pnl_gate_state'] == 'PAUSED':
            self.console.print_warning(f"{symbol} in PAUSED state - No new orders")
    
    def _place_orders(self, symbol: str, orders: List[dict], current_price: float, order_type: str):
        """
        Place orders with enhanced logging
        
        Args:
            symbol: Trading pair
            orders: List of order dicts
            current_price: Current market price
            order_type: Type of orders (GRID, DCA, TP)
        """
        if not orders:
            return
        
        for order in orders:
            try:
                # Calculate quantity (2% of equity per order to meet minimum notional)
                equity = self.portfolio.get_equity({symbol: current_price})
                order_value = equity * 0.02  # Increased from 1% to 2% to meet $11 minimum
                qty = order_value / order['price']
                
                # Round to exchange precision
                qty = self._round_quantity(symbol, qty)
                
                # Check minimum order value
                min_notional = 11.0  # Binance minimum
                order_notional = qty * order['price']
                if order_notional < min_notional:
                    self.console.print_warning(
                        f"Order skipped (too small): {qty:.4f} {symbol} @ ${order['price']:.2f} = ${order_notional:.2f} < ${min_notional}"
                    )
                    self.logger.debug(
                        f"Order too small: {qty} * {order['price']} < {min_notional}"
                    )
                    continue
                
                # Place order (limit order)
                side = order['side']
                price = self._round_price(symbol, order['price'])  # Round price to tick size
                tag = order.get('tag', '')
                
                # In paper/testnet mode, just track orders
                if self.trading_mode == 'paper':
                    # Paper trading - just track
                    order_id = f"PAPER_{int(datetime.now().timestamp() * 1000)}"
                    pending_order = {
                        'symbol': symbol,
                        'side': side,
                        'price': price,
                        'qty': qty,
                        'tag': tag,
                        'order_type': order_type,
                        'order_id': order_id,
                        'timestamp': datetime.now()
                    }
                    self.pending_orders[symbol].append(pending_order)
                    
                    # Enhanced console logging
                    self.console.print_order_placed(
                        order_type=order_type,
                        side=side,
                        symbol=symbol,
                        qty=qty,
                        price=price,
                        tag=tag
                    )
                    
                    # Log to CSV
                    self.order_logger.log_order(
                        symbol=symbol,
                        order_type=side,
                        side='LONG' if side == 'BUY' else 'SHORT',
                        action='OPEN' if side == 'BUY' else 'CLOSE',
                        price=price,
                        quantity=qty,
                        status='NEW',
                        strategy='Hybrid',
                        tag=tag,
                        reason=order_type,
                        mode=self.trading_mode
                    )
                else:
                    # Real trading (testnet or mainnet)
                    try:
                        order_result = self.exchange.create_order(
                            symbol=symbol,
                            side=side,
                            order_type='LIMIT',
                            quantity=qty,
                            price=price
                        )
                        
                        # Check if order was created successfully
                        if order_result is None:
                            raise Exception("Order creation failed - returned None")
                        
                        order_id = order_result.get('orderId', 'N/A')
                        
                        # Track order in pending_orders for testnet/mainnet
                        pending_order = {
                            'symbol': symbol,
                            'side': side,
                            'price': price,
                            'qty': qty,
                            'tag': tag,
                            'order_type': order_type,
                            'order_id': str(order_id),
                            'timestamp': datetime.now()
                        }
                        self.pending_orders[symbol].append(pending_order)
                        
                        # Enhanced console logging
                        self.console.print_order_placed(
                            order_type=order_type,
                            side=side,
                            symbol=symbol,
                            qty=qty,
                            price=price,
                            tag=tag,
                            order_id=str(order_id)
                        )
                        
                        # Log to CSV
                        self.order_logger.log_order(
                            symbol=symbol,
                            order_type=side,
                            side='LONG' if side == 'BUY' else 'SHORT',
                            action='OPEN' if side == 'BUY' else 'CLOSE',
                            price=price,
                            quantity=qty,
                            status='NEW',
                            strategy='Hybrid',
                            tag=tag,
                            reason=order_type,
                            mode=self.trading_mode,
                            order_id=str(order_id)
                        )
                    
                    except Exception as e:
                        # Order rejected
                        self.console.print_order_rejected(
                            order_type=order_type,
                            side=side,
                            symbol=symbol,
                            price=price,
                            reason=str(e)
                        )
                        
                        # Log rejection
                        self.order_logger.log_order(
                            symbol=symbol,
                            order_type=side,
                            side='LONG' if side == 'BUY' else 'SHORT',
                            action='OPEN' if side == 'BUY' else 'CLOSE',
                            price=price,
                            quantity=qty,
                            status='REJECTED',
                            strategy='Hybrid',
                            tag=tag,
                            reason=f"{order_type} - {str(e)}",
                            mode=self.trading_mode
                        )
                        raise
            
            except Exception as e:
                self.console.print_error(f"Error placing {order_type} order: {e}")
    
    def _manage_pending_orders(self, current_prices: Dict[str, float]):
        """
        Manage pending orders - cancel stale orders based on market conditions
        
        Cancellation criteria:
        1. Time-based: Orders older than max_age_seconds
        2. Price drift: Price moved too far from order
        3. Volatility spike: Sudden increase in volatility
        4. RSI reversal: Strong reversal signal
        """
        for symbol in self.symbols:
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            # Get policy config
            policy_cfg = self._get_policy_config(symbol)
            
            # Get order management settings
            max_age = policy_cfg.get('order_max_age_seconds', 300)
            price_drift_threshold = policy_cfg.get('order_price_drift_threshold_pct', 2.0)
            cancel_on_volatility = policy_cfg.get('order_cancel_on_volatility_spike', True)
            volatility_threshold = policy_cfg.get('order_volatility_spike_threshold', 1.5)
            cancel_on_rsi_reversal = policy_cfg.get('order_cancel_on_rsi_reversal', True)
            rsi_reversal_threshold = policy_cfg.get('order_rsi_reversal_threshold', 20)
            
            # Get current market signals
            indicator_engine = self.indicator_engines.get(symbol)
            if indicator_engine:
                signals = indicator_engine.get_latest_signals()
                current_rsi = signals.get('rsi', 50)
                current_atr_pct = signals.get('atr_pct', 1.0)
            else:
                current_rsi = 50
                current_atr_pct = 1.0
            
            # Track orders to cancel
            orders_to_cancel = []
            
            for order in self.pending_orders[symbol]:
                order_age = (datetime.now() - order['timestamp']).total_seconds()
                order_price = order['price']
                order_side = order['side']
                order_tag = order.get('tag', '')
                
                cancel_reason = None
                
                # 1. Check time-based cancellation
                if order_age > max_age:
                    cancel_reason = f"Order age {order_age:.0f}s > {max_age}s"
                
                # 2. Check price drift
                elif order_price > 0:
                    price_drift_pct = abs(current_price - order_price) / order_price * 100
                    if price_drift_pct > price_drift_threshold:
                        cancel_reason = f"Price drift {price_drift_pct:.2f}% > {price_drift_threshold}%"
                
                # 3. Check volatility spike (only for grid orders)
                elif cancel_on_volatility and 'grid' in order_tag.lower():
                    # Get historical ATR for comparison
                    if hasattr(self, '_last_atr_pct'):
                        last_atr_pct = self._last_atr_pct.get(symbol, current_atr_pct)
                        if current_atr_pct > last_atr_pct * volatility_threshold:
                            cancel_reason = f"Volatility spike: {current_atr_pct:.2f}% > {last_atr_pct:.2f}% * {volatility_threshold}"
                
                # 4. Check RSI reversal
                elif cancel_on_rsi_reversal:
                    # Store initial RSI when order was placed
                    if 'initial_rsi' not in order:
                        order['initial_rsi'] = current_rsi
                    else:
                        rsi_change = abs(current_rsi - order['initial_rsi'])
                        
                        # Cancel BUY orders if RSI reversed from oversold
                        if order_side == 'BUY' and order['initial_rsi'] < 40 and current_rsi > 60:
                            if rsi_change > rsi_reversal_threshold:
                                cancel_reason = f"RSI reversal: {order['initial_rsi']:.1f} -> {current_rsi:.1f}"
                        
                        # Cancel SELL orders if RSI reversed from overbought
                        elif order_side == 'SELL' and order['initial_rsi'] > 60 and current_rsi < 40:
                            if rsi_change > rsi_reversal_threshold:
                                cancel_reason = f"RSI reversal: {order['initial_rsi']:.1f} -> {current_rsi:.1f}"
                
                # Cancel order if any condition met
                if cancel_reason:
                    orders_to_cancel.append((order, cancel_reason))
            
            # Cancel orders
            for order, reason in orders_to_cancel:
                self._cancel_order(symbol, order, reason)
            
            # Store current ATR for next iteration
            if not hasattr(self, '_last_atr_pct'):
                self._last_atr_pct = {}
            self._last_atr_pct[symbol] = current_atr_pct
    
    def _cancel_order(self, symbol: str, order: dict, reason: str):
        """
        Cancel a pending order
        
        Args:
            symbol: Trading pair
            order: Order dict
            reason: Cancellation reason
        """
        try:
            order_id = order.get('order_id', 'N/A')
            order_type = order.get('order_type', 'UNKNOWN')
            side = order['side']
            price = order['price']
            qty = order['qty']
            tag = order.get('tag', '')
            
            # Cancel on exchange (testnet/mainnet only)
            if self.trading_mode != 'paper':
                try:
                    # Cancel on exchange
                    success = self.exchange.cancel_order(symbol, int(order_id))
                    if not success:
                        self.logger.warning(f"Failed to cancel order {order_id} on exchange")
                except Exception as e:
                    self.logger.error(f"Error cancelling order {order_id}: {e}")
            
            # Remove from pending orders
            if order in self.pending_orders[symbol]:
                self.pending_orders[symbol].remove(order)
            
            # Log cancellation
            self.console.print_warning(
                f"🗑️  ORDER CANCELLED: {order_type} | {side} {qty:.4f} {symbol} @ ${price:.2f}  [{tag}]  Reason: {reason}"
            )
            
            self.order_logger.log_order(
                symbol=symbol,
                order_type=side,
                side='LONG' if side == 'BUY' else 'SHORT',
                action='OPEN' if side == 'BUY' else 'CLOSE',
                price=price,
                quantity=qty,
                status='CANCELLED',
                strategy='Hybrid',
                tag=tag,
                reason=f"{order_type} - {reason}",
                mode=self.trading_mode,
                order_id=str(order_id)
            )
            
        except Exception as e:
            self.logger.error(f"Error in _cancel_order: {e}", exc_info=True)
    
    def _check_fills(self):
        """Check for filled orders"""
        if self.trading_mode == 'paper':
            # Paper trading - simulate fills
            for symbol in self.symbols:
                try:
                    current_price = float(self.exchange.get_ticker(symbol)['price'])
                    
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
                    self.console.print_error(f"Error checking fills for {symbol}: {e}")
        else:
            # Real trading - check with exchange
            # TODO: Implement real order tracking
            pass
    
    def _fill_order(self, order: dict, fill_price: float):
        """Process filled order with enhanced logging"""
        symbol = order['symbol']
        side = order['side']
        qty = order['qty']
        tag = order['tag']
        order_type = order.get('order_type', 'UNKNOWN')
        
        pnl = None
        
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
            if 'dca' in tag.lower():
                self.strategy_engines[symbol].notify_dca_fill(fill_price)
            
            # Enhanced console logging
            self.console.print_order_filled(
                order_type=order_type,
                side=side,
                symbol=symbol,
                qty=qty,
                price=fill_price,
                tag=tag
            )
            
            # Log fill to CSV
            self.order_logger.log_fill(
                symbol=symbol,
                order_id=f"ORD_{symbol}_{int(datetime.now().timestamp())}",
                fill_type=side,
                side='LONG',
                action='OPEN',
                price=fill_price,
                quantity=qty,
                fee=fill_price * qty * 0.001,  # 0.1% fee
                fee_asset='USDT',
                pnl=0.0,
                pnl_pct=0.0,
                strategy='Hybrid',
                tag=tag
            )
        else:
            # Close position
            position = self.portfolio.get_position(symbol, 'Hybrid')
            
            if position:
                # Calculate PnL
                entry_price = position['entry_price']
                pnl = (fill_price - entry_price) * qty
                pnl_pct = ((fill_price - entry_price) / entry_price) * 100
                
                self.portfolio.close_position(
                    symbol=symbol,
                    strategy='Hybrid',
                    exit_price=fill_price
                )
                
                # Enhanced console logging
                self.console.print_order_filled(
                    order_type=order_type,
                    side=side,
                    symbol=symbol,
                    qty=qty,
                    price=fill_price,
                    pnl=pnl,
                    tag=tag
                )
                
                # Log fill to CSV
                self.order_logger.log_fill(
                    symbol=symbol,
                    order_id=f"ORD_{symbol}_{int(datetime.now().timestamp())}",
                    fill_type=side,
                    side='LONG',
                    action='CLOSE',
                    price=fill_price,
                    quantity=qty,
                    fee=fill_price * qty * 0.001,  # 0.1% fee
                    fee_asset='USDT',
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    strategy='Hybrid',
                    tag=tag
                )
    
    def _display_positions(self, current_prices: Dict[str, float]):
        """Display current positions"""
        for symbol in self.symbols:
            position = self.portfolio.get_position(symbol, 'Hybrid')
            
            if position and symbol in current_prices:
                qty = position['quantity']
                avg_price = position['entry_price']
                current_price = current_prices[symbol]
                
                unrealized_pnl = (current_price - avg_price) * qty
                unrealized_pnl_pct = ((current_price - avg_price) / avg_price) * 100
                
                self.console.print_position(
                    symbol=symbol,
                    qty=qty,
                    avg_price=avg_price,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct
                )
    
    def _cancel_grid_orders(self, symbol: str):
        """Cancel grid orders for symbol"""
        cancelled_count = 0
        
        # Filter out grid orders
        new_pending = []
        for order in self.pending_orders[symbol]:
            if 'grid' in order['tag'].lower():
                cancelled_count += 1
            else:
                new_pending.append(order)
        
        self.pending_orders[symbol] = new_pending
        
        if cancelled_count > 0:
            self.console.print_info(f"Cancelled {cancelled_count} grid orders for {symbol}")
    
    def _close_all_positions(self, symbol: str, price: float):
        """Close all positions for symbol"""
        position = self.portfolio.get_position(symbol, 'Hybrid')
        
        if position:
            qty = position['quantity']
            entry_price = position['entry_price']
            pnl = (price - entry_price) * qty
            
            self.portfolio.close_position(
                symbol=symbol,
                strategy='Hybrid',
                exit_price=price
            )
            
            self.console.print_order_filled(
                order_type='HARD_STOP',
                side='SELL',
                symbol=symbol,
                qty=qty,
                price=price,
                pnl=pnl,
                tag='hard_stop'
            )
    
    def _round_quantity(self, symbol: str, qty: float) -> float:
        """Round quantity to exchange lot size (step size)"""
        # Different symbols have different lot sizes
        # TODO: Get actual lot size from exchange info
        
        # Determine step size based on symbol
        if 'BTC' in symbol:
            step_size = 0.00001  # BTC: 5 decimals
            decimals = 5
        elif symbol in ['SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']:
            step_size = 0.01  # Most altcoins: 2 decimals
            decimals = 2
        elif 'ETH' in symbol:
            step_size = 0.0001  # ETH: 4 decimals
            decimals = 4
        else:
            step_size = 0.01  # Default: 2 decimals
            decimals = 2
        
        # Round to avoid floating point precision issues
        return round(round(qty / step_size) * step_size, decimals)
    
    def _round_price(self, symbol: str, price: float) -> float:
        """Round price to exchange tick size"""
        # For most USDT pairs, tick size is 0.01
        # For high-value pairs like BTC, might be 0.1 or 1.0
        # TODO: Get actual tick size from exchange info
        
        # Determine tick size and decimal places based on price magnitude
        if price >= 1000:
            tick_size = 1.0  # BTC, ETH high prices
            decimals = 0
        elif price >= 100:
            tick_size = 0.1  # SOL, BNB
            decimals = 1
        elif price >= 1:
            tick_size = 0.01  # Most altcoins
            decimals = 2
        else:
            tick_size = 0.0001  # Low price coins
            decimals = 4
        
        # Round to avoid floating point precision issues
        return round(round(price / tick_size) * tick_size, decimals)
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        
        self.console.print_header("SHUTTING DOWN")
        
        # Print final statistics
        stats = self.portfolio.get_statistics()
        
        self.console.print_section("FINAL STATISTICS")
        self.logger.info(f"Total Trades: {stats['total_trades']}")
        self.logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
        self.logger.info(f"Total PnL: ${stats['total_pnl']:.2f}")
        self.logger.info(f"Open Positions: {stats['open_positions']}")
        
        # Print order summary
        self.order_logger.print_summary()
        
        # Export trades
        if self.portfolio.trade_history:
            from src.utils.trade_exporter import TradeExporter
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_prefix = f"./data/hybrid_live_trades_{timestamp}"
            TradeExporter.export_detailed_report(self.portfolio.trade_history, report_prefix)
            self.console.print_success(f"Trade report exported: {report_prefix}")
        
        self.console.print_success("Bot stopped successfully")


def main():
    """Main entry point"""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get symbols
    symbols_str = os.getenv('TRADING_SYMBOLS', 'BTCUSDT')
    symbols = [s.strip() for s in symbols_str.split(',')]
    
    # Get config path
    config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
    
    print("\n" + "="*80)
    print("HYBRID STRATEGY LIVE TRADING BOT v2.5.0")
    print("Enhanced Logging Edition")
    print("="*80)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Config: {config_path}")
    print(f"Mode: {os.getenv('TRADING_MODE', 'paper').upper()}")
    print(f"Interval: {os.getenv('TRADING_INTERVAL', '60')}s")
    print("="*80 + "\n")
    
    # Create bot
    bot = HybridTradingBot(symbols, config_path)
    
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

