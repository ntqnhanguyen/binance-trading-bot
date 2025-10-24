"""
Portfolio management and position tracking
"""
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from ..utils.logger import TradingLogger


class Position:
    """Represents a trading position"""
    
    def __init__(self, symbol: str, side: str, quantity: float, 
                 entry_price: float, strategy: str):
        """
        Initialize a position
        
        Args:
            symbol: Trading pair symbol
            side: LONG or SHORT
            quantity: Position size
            entry_price: Entry price
            strategy: Strategy name that opened the position
        """
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.strategy = strategy
        self.entry_time = datetime.now()
        self.stop_loss = None
        self.take_profit = None
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
    
    def update_pnl(self, current_price: float):
        """
        Update unrealized PnL
        
        Args:
            current_price: Current market price
        """
        if self.side == 'LONG':
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
    
    def get_pnl_percentage(self) -> float:
        """
        Get PnL as percentage
        
        Returns:
            PnL percentage
        """
        position_value = self.entry_price * self.quantity
        if position_value == 0:
            return 0.0
        return (self.unrealized_pnl / position_value) * 100
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'strategy': self.strategy,
            'entry_time': self.entry_time.isoformat(),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'unrealized_pnl': self.unrealized_pnl,
            'pnl_pct': self.get_pnl_percentage()
        }


class Portfolio:
    """Portfolio manager for tracking positions and capital"""
    
    def __init__(self, initial_capital: float):
        """
        Initialize portfolio
        
        Args:
            initial_capital: Starting capital
        """
        self.logger = TradingLogger.get_logger(__name__)
        
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        
        # Trade history
        self.trade_history: List[Dict] = []
        
        # Reset timestamps
        self.last_daily_reset = datetime.now().date()
        self.last_weekly_reset = datetime.now().isocalendar()[1]
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value
        
        Args:
            current_prices: Dictionary of current prices for each symbol
            
        Returns:
            Total portfolio value
        """
        position_value = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.update_pnl(current_prices[symbol])
                position_value += position.entry_price * position.quantity + position.unrealized_pnl
        
        return self.cash + position_value
    
    def get_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Get current equity (total value)
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Current equity
        """
        return self.get_total_value(current_prices)
    
    def get_cash_percentage(self) -> float:
        """
        Get cash as percentage of total capital
        
        Returns:
            Cash percentage
        """
        total = self.cash
        for position in self.positions.values():
            total += position.entry_price * position.quantity
        
        if total == 0:
            return 100.0
        
        return (self.cash / total) * 100
    
    def open_position(self, symbol: str, side: str, quantity: float,
                     entry_price: float, strategy: str) -> bool:
        """
        Open a new position
        
        Args:
            symbol: Trading pair symbol
            side: LONG or SHORT
            quantity: Position size
            entry_price: Entry price
            strategy: Strategy name
            
        Returns:
            True if successful, False otherwise
        """
        position_cost = entry_price * quantity
        
        # Check if we have enough cash
        if position_cost > self.cash:
            self.logger.warning(
                f"Insufficient cash to open position: {symbol}. "
                f"Required: {position_cost}, Available: {self.cash}"
            )
            return False
        
        # Create position key (symbol + strategy)
        position_key = f"{symbol}_{strategy}"
        
        if position_key in self.positions:
            self.logger.warning(f"Position already exists: {position_key}")
            return False
        
        # Create new position
        position = Position(symbol, side, quantity, entry_price, strategy)
        self.positions[position_key] = position
        
        # Update cash
        self.cash -= position_cost
        
        self.logger.info(
            f"Opened {side} position: {symbol} | "
            f"Qty: {quantity} | Price: {entry_price} | "
            f"Strategy: {strategy} | Cost: {position_cost}"
        )
        
        return True
    
    def close_position(self, symbol: str, strategy: str, exit_price: float,
                      quantity: float = None) -> Optional[float]:
        """
        Close a position (fully or partially)
        
        Args:
            symbol: Trading pair symbol
            strategy: Strategy name
            exit_price: Exit price
            quantity: Quantity to close (None = close all)
            
        Returns:
            Realized PnL or None if failed
        """
        position_key = f"{symbol}_{strategy}"
        
        if position_key not in self.positions:
            self.logger.warning(f"Position not found: {position_key}")
            return None
        
        position = self.positions[position_key]
        
        # Determine quantity to close
        close_qty = quantity if quantity else position.quantity
        
        if close_qty > position.quantity:
            self.logger.warning(
                f"Close quantity ({close_qty}) exceeds position size ({position.quantity})"
            )
            close_qty = position.quantity
        
        # Calculate PnL
        if position.side == 'LONG':
            pnl = (exit_price - position.entry_price) * close_qty
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * close_qty
        
        # Update cash
        self.cash += exit_price * close_qty
        
        # Update position or remove if fully closed
        if close_qty >= position.quantity:
            del self.positions[position_key]
            self.logger.info(f"Fully closed position: {position_key}")
        else:
            position.quantity -= close_qty
            self.logger.info(
                f"Partially closed position: {position_key} | "
                f"Closed: {close_qty} | Remaining: {position.quantity}"
            )
        
        # Update statistics
        self.total_trades += 1
        self.total_pnl += pnl
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Record trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'strategy': strategy,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'quantity': close_qty,
            'pnl': pnl,
            'pnl_pct': (pnl / (position.entry_price * close_qty)) * 100
        }
        self.trade_history.append(trade_record)
        
        self.logger.info(
            f"Trade closed: {symbol} | PnL: {pnl:.4f} "
            f"({trade_record['pnl_pct']:.2f}%)"
        )
        
        return pnl
    
    def get_position(self, symbol: str, strategy: str) -> Optional[Position]:
        """
        Get a specific position
        
        Args:
            symbol: Trading pair symbol
            strategy: Strategy name
            
        Returns:
            Position object or None
        """
        position_key = f"{symbol}_{strategy}"
        return self.positions.get(position_key)
    
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions
        
        Returns:
            List of positions
        """
        return list(self.positions.values())
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """
        Get all positions for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            List of positions
        """
        return [p for p in self.positions.values() if p.symbol == symbol]
    
    def update_stop_loss(self, symbol: str, strategy: str, stop_loss: float):
        """
        Update stop loss for a position
        
        Args:
            symbol: Trading pair symbol
            strategy: Strategy name
            stop_loss: New stop loss price
        """
        position = self.get_position(symbol, strategy)
        if position:
            position.stop_loss = stop_loss
            self.logger.info(f"Updated SL for {symbol}_{strategy}: {stop_loss}")
    
    def update_take_profit(self, symbol: str, strategy: str, take_profit: float):
        """
        Update take profit for a position
        
        Args:
            symbol: Trading pair symbol
            strategy: Strategy name
            take_profit: New take profit price
        """
        position = self.get_position(symbol, strategy)
        if position:
            position.take_profit = take_profit
            self.logger.info(f"Updated TP for {symbol}_{strategy}: {take_profit}")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        current_date = datetime.now().date()
        if current_date > self.last_daily_reset:
            self.daily_pnl = 0.0
            self.last_daily_reset = current_date
            self.logger.info("Daily statistics reset")
    
    def reset_weekly_stats(self):
        """Reset weekly statistics"""
        current_week = datetime.now().isocalendar()[1]
        if current_week != self.last_weekly_reset:
            self.weekly_pnl = 0.0
            self.last_weekly_reset = current_week
            self.logger.info("Weekly statistics reset")
    
    def get_statistics(self) -> Dict:
        """
        Get portfolio statistics
        
        Returns:
            Dictionary with statistics
        """
        win_rate = 0.0
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
        
        avg_win = 0.0
        avg_loss = 0.0
        
        if self.trade_history:
            winning_trades = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
            losing_trades = [t['pnl'] for t in self.trade_history if t['pnl'] < 0]
            
            if winning_trades:
                avg_win = sum(winning_trades) / len(winning_trades)
            if losing_trades:
                avg_loss = sum(losing_trades) / len(losing_trades)
        
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'cash_pct': self.get_cash_percentage(),
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'open_positions': len(self.positions)
        }
    
    def get_trade_history_df(self) -> pd.DataFrame:
        """
        Get trade history as DataFrame
        
        Returns:
            DataFrame with trade history
        """
        if not self.trade_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.trade_history)

