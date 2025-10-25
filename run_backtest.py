"""
Backtest script for Hybrid Strategy Engine

Runs backtest with Grid + DCA hybrid strategy using dynamic spread,
PnL Gate, and Stop-Loss management.
"""
import argparse
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path

from src.strategies.hybrid_strategy_engine import HybridStrategyEngine
from src.indicators.indicator_engine import IndicatorEngine
from src.indicators.technical import add_all_indicators
from src.utils.logger import TradingLogger
from src.utils.order_logger import OrderLogger


class HybridBacktester:
    """Backtester for Hybrid Strategy"""
    
    def __init__(self, symbol: str, policy_cfg: dict, initial_capital: float):
        """
        Initialize backtester
        
        Args:
            symbol: Trading pair symbol
            policy_cfg: Policy configuration
            initial_capital: Starting capital
        """
        self.symbol = symbol
        self.policy_cfg = policy_cfg
        self.initial_capital = initial_capital
        
        # Initialize logger
        self.logger = TradingLogger.get_logger('HybridBacktest')
        self.order_logger = OrderLogger(output_dir='./data/outputs')
        
        # Initialize engines
        self.indicator_engine = IndicatorEngine(symbol)
        self.strategy_engine = HybridStrategyEngine(symbol, policy_cfg, self.indicator_engine)
        
        # Portfolio state
        self.cash = initial_capital
        self.positions = {}  # symbol -> {qty, entry_price, side}
        self.pending_orders = []
        
        # Performance tracking
        self.trades = []
        self.equity_curve = []
        self.state_history = []
        self.total_fees = 0.0
        
        # Fee configuration
        self.maker_fee_pct = 0.1  # 0.1% default
        self.taker_fee_pct = 0.1  # 0.1% default
        
        self.logger.info(f"HybridBacktester initialized: {symbol}, capital=${initial_capital:,.2f}")
    
    def run(self, df: pd.DataFrame):
        """
        Run backtest on historical data
        
        Args:
            df: DataFrame with OHLCV data and indicators
        """
        self.logger.info(f"Starting backtest: {len(df)} bars")
        
        # Add indicators
        df = add_all_indicators(df)
        
        # Process each bar
        for i in range(50, len(df)):  # Start after warmup period
            bar_df = df.iloc[:i+1]
            
            # Update indicator engine
            self.indicator_engine.update(bar_df)
            
            # Get current bar
            current_bar = {
                'timestamp': df.iloc[i]['timestamp'],
                'open': df.iloc[i]['open'],
                'high': df.iloc[i]['high'],
                'low': df.iloc[i]['low'],
                'close': df.iloc[i]['close'],
                'volume': df.iloc[i]['volume']
            }
            
            # Calculate current equity
            equity = self._calculate_equity(current_bar['close'])
            
            # Generate plan
            plan = self.strategy_engine.on_bar(current_bar, equity)
            
            # Check hard stop
            if plan['sl_action']['stop']:
                # Hard stop triggered, but don't break - continue monitoring for auto-resume
                if not hasattr(self, '_hard_stop_logged') or not self._hard_stop_logged:
                    self.logger.critical(f"Hard stop triggered: {plan['sl_action']['reason']}")
                    self._close_all_positions(current_bar['close'])
                    self._hard_stop_logged = True
                # Continue to next bar to check for auto-resume
                # No new orders will be placed while in hard stop
            else:
                # Hard stop not active or resumed
                if hasattr(self, '_hard_stop_logged') and self._hard_stop_logged:
                    self.logger.warning(f"Trading resumed from hard stop at ${current_bar['close']:.2f}")
                    self._hard_stop_logged = False
            
            # Execute orders based on state (only if not in hard stop)
            if not plan['sl_action']['stop']:
                if plan['pnl_gate_state'] == 'RUN':
                    # Full operation
                    if plan['kill_replace']:
                        self._cancel_grid_orders()
                    
                    self._execute_orders(plan['grid_orders'], current_bar)
                    self._execute_orders(plan['dca_orders'], current_bar)
                    self._execute_orders(plan['tp_orders'], current_bar)
                
                elif plan['pnl_gate_state'] == 'DEGRADED':
                    # Reduced operation
                    self._execute_orders(plan['dca_orders'], current_bar)
                    self._execute_orders(plan['tp_orders'], current_bar)
                
                # PAUSED: no new orders
            else:
                # Hard stop active: no new orders, just monitor
                pass
            
            # Check pending orders for fills
            self._check_fills(current_bar)
            
            # Record state
            self._record_state(current_bar, equity, plan)
            
            # Log progress
            if i % 100 == 0:
                self.logger.info(
                    f"Bar {i}/{len(df)}: Price=${current_bar['close']:.2f}, "
                    f"Equity=${equity:.2f}, State={plan['pnl_gate_state']}, "
                    f"Positions={len(self.positions)}"
                )
        
        self.logger.info("Backtest completed")
        
        # Generate report
        self._generate_report()
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current portfolio equity"""
        equity = self.cash
        
        for symbol, pos in self.positions.items():
            if pos['side'] == 'LONG':
                equity += pos['qty'] * current_price
            else:  # SHORT
                pnl = pos['qty'] * (pos['entry_price'] - current_price)
                equity += pnl
        
        return equity
    
    def _execute_orders(self, orders: list, bar: dict):
        """Execute orders (add to pending)"""
        for order in orders:
            # Simple order structure
            pending_order = {
                'side': order['side'],
                'price': order['price'],
                'tag': order.get('tag', ''),
                'timestamp': bar['timestamp']
            }
            self.pending_orders.append(pending_order)
            
            # Log order
            order_type = 'BUY' if order['side'] == 'BUY' else 'SELL'
            action = 'OPEN' if order['side'] == 'BUY' else 'CLOSE'
            self.order_logger.log_order(
                symbol=self.symbol,
                order_type=order_type,
                side='LONG',
                action=action,
                price=order['price'],
                quantity=0.0,  # Will be calculated on fill
                status='NEW',
                strategy='HybridStrategy',
                tag=order.get('tag', ''),
                reason=f"Plan: {order.get('tag', '')}",
                mode='backtest'
            )
            
            self.logger.info(
                f"📝 Order placed: {order_type} @ ${order['price']:.2f} [{order.get('tag', '')}]"
            )    
    def _check_fills(self, bar: dict):
        """Check if pending orders are filled"""
        filled_orders = []
        
        for order in self.pending_orders:
            filled = False
            
            # Simple fill logic: if price touches order price
            if order['side'] == 'BUY':
                if bar['low'] <= order['price']:
                    filled = True
                    fill_price = order['price']
            else:  # SELL
                if bar['high'] >= order['price']:
                    filled = True
                    fill_price = order['price']
            
            if filled:
                self._fill_order(order, fill_price, bar['timestamp'])
                filled_orders.append(order)
        
        # Remove filled orders
        for order in filled_orders:
            self.pending_orders.remove(order)
    
    def _fill_order(self, order: dict, fill_price: float, timestamp: datetime):
        """Fill an order"""
        # Calculate quantity (simple: 1% of equity per order)
        equity = self._calculate_equity(fill_price)
        order_value = equity * 0.01  # 1% per order
        qty = order_value / fill_price
        
        if order['side'] == 'BUY':
            # Open or add to position
            if self.symbol not in self.positions:
                self.positions[self.symbol] = {
                    'qty': qty,
                    'entry_price': fill_price,
                    'side': 'LONG'
                }
            else:
                # Average up
                pos = self.positions[self.symbol]
                total_qty = pos['qty'] + qty
                avg_price = (pos['qty'] * pos['entry_price'] + qty * fill_price) / total_qty
                pos['qty'] = total_qty
                pos['entry_price'] = avg_price
            
            # Calculate and deduct fee
            fee = order_value * (self.maker_fee_pct / 100)
            self.cash -= (order_value + fee)
            self.total_fees += fee
            
            # Calculate equity after trade
            equity_after = self._calculate_equity(fill_price)
            
            # Log fill
            self.order_logger.log_fill(
                symbol=self.symbol,
                order_id=f"ORD_{timestamp}",
                fill_type='BUY',
                side='LONG',
                action='OPEN',
                price=fill_price,
                quantity=qty,
                fee=fee,
                fee_asset='USDT',
                strategy='HybridStrategy',
                tag=order['tag']
            )
            
            # Notify DCA fill
            if 'dca' in order['tag']:
                self.strategy_engine.notify_dca_fill(fill_price)
            
            self.logger.info(
                f"✅ BUY filled: {qty:.4f} @ ${fill_price:.2f}, "
                f"Value=${order_value:.2f}, Fee=${fee:.2f}, "
                f"Equity=${equity_after:,.2f} [{order['tag']}]"
            )
        
        else:  # SELL
            # Close or reduce position
            if self.symbol in self.positions:
                pos = self.positions[self.symbol]
                
                if qty >= pos['qty']:
                    # Close entire position
                    sell_value = pos['qty'] * fill_price
                    fee = sell_value * (self.maker_fee_pct / 100)
                    pnl_gross = pos['qty'] * (fill_price - pos['entry_price'])
                    pnl_net = pnl_gross - fee  # Net PnL after fee
                    
                    self.cash += (sell_value - fee)
                    self.total_fees += fee
                    
                    # Calculate equity after trade
                    equity_after = self._calculate_equity(fill_price)
                    
                    # Record trade
                    self.trades.append({
                        'timestamp': timestamp,
                        'side': 'LONG',
                        'entry_price': pos['entry_price'],
                        'exit_price': fill_price,
                        'qty': pos['qty'],
                        'pnl_gross': pnl_gross,
                        'pnl_net': pnl_net,
                        'fee': fee,
                        'tag': order['tag']
                    })
                    
                    del self.positions[self.symbol]
                    
                    # Log fill
                    pnl_pct = (pnl_net / (pos['qty'] * pos['entry_price'])) * 100
                    self.order_logger.log_fill(
                        symbol=self.symbol,
                        order_id=f"ORD_{timestamp}",
                        fill_type='SELL',
                        side='LONG',
                        action='CLOSE',
                        price=fill_price,
                        quantity=pos['qty'],
                        fee=fee,
                        fee_asset='USDT',
                        pnl=pnl_net,
                        pnl_pct=pnl_pct,
                        strategy='HybridStrategy',
                        tag=order['tag']
                    )
                    
                    emoji = "🟢" if pnl_net > 0 else "🔴"
                    self.logger.info(
                        f"{emoji} SELL filled (close): {pos['qty']:.4f} @ ${fill_price:.2f}, "
                        f"PnL=${pnl_net:.2f} ({pnl_pct:+.2f}%), Fee=${fee:.2f}, "
                        f"Equity=${equity_after:,.2f} [{order['tag']}]"
                    )
                else:
                    # Partial close
                    pnl = qty * (fill_price - pos['entry_price'])
                    self.cash += qty * fill_price
                    pos['qty'] -= qty
                    
                    self.trades.append({
                        'timestamp': timestamp,
                        'side': 'LONG',
                        'entry_price': pos['entry_price'],
                        'exit_price': fill_price,
                        'qty': qty,
                        'pnl': pnl,
                        'tag': order['tag']
                    })
                    
                    self.logger.debug(
                        f"SELL filled (partial): {qty:.4f} @ ${fill_price:.2f}, "
                        f"PnL=${pnl:.2f} [{order['tag']}]"
                    )
    
    def _cancel_grid_orders(self):
        """Cancel all grid orders"""
        self.pending_orders = [
            order for order in self.pending_orders 
            if 'grid' not in order['tag']
        ]
        self.logger.debug("Grid orders cancelled")
    
    def _close_all_positions(self, price: float):
        """Close all positions"""
        for symbol, pos in list(self.positions.items()):
            pnl = pos['qty'] * (price - pos['entry_price'])
            self.cash += pos['qty'] * price
            
            self.trades.append({
                'timestamp': datetime.now(),
                'side': 'LONG',
                'entry_price': pos['entry_price'],
                'exit_price': price,
                'qty': pos['qty'],
                'pnl': pnl,
                'tag': 'hard_stop'
            })
            
            del self.positions[symbol]
        
        self.logger.info(f"All positions closed at ${price:.2f}")
    
    def _record_state(self, bar: dict, equity: float, plan: dict):
        """Record state for analysis"""
        self.equity_curve.append({
            'timestamp': bar['timestamp'],
            'equity': equity,
            'cash': self.cash,
            'price': bar['close']
        })
        
        self.state_history.append({
            'timestamp': bar['timestamp'],
            'state': plan['pnl_gate_state'],
            'hard_stop': plan['sl_action']['stop'],
            'band': plan['band'],
            'spread_pct': plan['spread_pct'],
            'grid_orders': len(plan['grid_orders']),
            'dca_orders': len(plan['dca_orders']),
            'tp_orders': len(plan['tp_orders'])
        })
    
    def _generate_report(self):
        """Generate backtest report"""
        # Check if we have any data
        if not self.equity_curve:
            self.logger.warning("No equity data recorded")
            final_equity = self.initial_capital
            total_return = 0.0
        else:
            final_equity = self._calculate_equity(self.equity_curve[-1]['price'])
            total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate metrics
        trades_df = pd.DataFrame(self.trades)
        
        if len(trades_df) > 0:
            # Use pnl_net (after fees) for metrics
            winning_trades = trades_df[trades_df['pnl_net'] > 0]
            losing_trades = trades_df[trades_df['pnl_net'] < 0]
            
            win_rate = (len(winning_trades) / len(trades_df)) * 100
            avg_win = winning_trades['pnl_net'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl_net'].mean() if len(losing_trades) > 0 else 0
            total_pnl_gross = trades_df['pnl_gross'].sum()
            total_pnl_net = trades_df['pnl_net'].sum()
            total_trade_fees = trades_df['fee'].sum()
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            total_pnl_gross = 0
            total_pnl_net = 0
            total_trade_fees = 0
        
        # Print report
        print("\n" + "="*70)
        print("HYBRID STRATEGY BACKTEST REPORT")
        print("="*70)
        print(f"\nSymbol: {self.symbol}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Equity: ${final_equity:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"\nTrades: {len(trades_df)}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Avg Win: ${avg_win:.2f}")
        print(f"Avg Loss: ${avg_loss:.2f}")
        print(f"\nPnL (Gross): ${total_pnl_gross:.2f}")
        print(f"Total Fees: ${self.total_fees:.2f}")
        print(f"PnL (Net): ${total_pnl_net:.2f}")
        print(f"Fee Impact: {(self.total_fees / self.initial_capital * 100):.2f}% of capital")
        
        # State distribution
        state_df = pd.DataFrame(self.state_history)
        if len(state_df) > 0:
            print(f"\nState Distribution:")
            state_counts = state_df['state'].value_counts()
            for state, count in state_counts.items():
                pct = (count / len(state_df)) * 100
                print(f"  {state}: {count} bars ({pct:.1f}%)")
            
            # Hard stop stats
            hard_stop_bars = state_df[state_df['hard_stop'] == True]
            if len(hard_stop_bars) > 0:
                print(f"\nHard Stop Events:")
                print(f"  Total bars in hard stop: {len(hard_stop_bars)} ({len(hard_stop_bars)/len(state_df)*100:.1f}%)")
                
                # Find resume events (hard_stop changes from True to False)
                resume_count = 0
                for i in range(1, len(state_df)):
                    if state_df.iloc[i-1]['hard_stop'] and not state_df.iloc[i]['hard_stop']:
                        resume_count += 1
                
                if resume_count > 0:
                    print(f"  Auto-resume events: {resume_count}")
                    print(f"  Average time in hard stop: {len(hard_stop_bars)/resume_count:.0f} bars")
                else:
                    print(f"  No auto-resume (hard stop remained active)")
            else:
                print(f"\nNo hard stop events")
        
        print("\n" + "="*70)
        
        # Print order summary
        self.order_logger.print_summary()
        
        # Note: All detailed order/fill data is saved to data/outputs/ by OrderLogger
        # No need to save duplicate files here


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Hybrid Strategy Backtest')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading pair')
    parser.add_argument('--capital', type=float, default=10000.0, help='Initial capital')
    parser.add_argument('--data', type=str, required=True, help='Path to OHLCV CSV file')
    parser.add_argument('--config', type=str, default='config/config.yaml', 
                       help='Path to config file')
    parser.add_argument('--pair-config', type=str, default=None,
                       help='Use pair-specific config (e.g., BTCUSDT)')
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get policy config
    if args.pair_config and args.pair_config in config.get('pairs', {}):
        # Merge pair-specific with default
        policy_cfg = config['default_policy'].copy()
        policy_cfg.update(config['pairs'][args.pair_config])
        print(f"Using pair-specific config for {args.pair_config}")
    else:
        policy_cfg = config['default_policy']
        print("Using default policy config")
    
    # Load data
    print(f"\nLoading data from {args.data}...")
    df = pd.read_csv(args.data)
    
    # Parse timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
    
    print(f"Loaded {len(df)} bars")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Create backtester
    backtester = HybridBacktester(args.symbol, policy_cfg, args.capital)
    
    # Run backtest
    backtester.run(df)


if __name__ == '__main__':
    main()

