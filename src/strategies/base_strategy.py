"""
Base strategy class for all trading strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import pandas as pd

from ..utils.logger import TradingLogger
from ..core.portfolio import Portfolio
from ..risk.risk_manager import RiskManager


class Signal:
    """Trading signal"""
    
    def __init__(self, action: str, symbol: str, price: float, 
                 quantity: float = None, stop_loss: float = None,
                 take_profit: float = None, metadata: Dict = None):
        """
        Initialize trading signal
        
        Args:
            action: BUY, SELL, or HOLD
            symbol: Trading pair symbol
            price: Signal price
            quantity: Suggested quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
            metadata: Additional signal information
        """
        self.action = action
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.metadata = metadata or {}
    
    def __repr__(self):
        return (f"Signal(action={self.action}, symbol={self.symbol}, "
                f"price={self.price}, qty={self.quantity})")


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, config: Dict, portfolio: Portfolio, 
                 risk_manager: RiskManager):
        """
        Initialize strategy
        
        Args:
            name: Strategy name
            config: Strategy configuration
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        self.name = name
        self.config = config
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.logger = TradingLogger.get_logger(f"Strategy.{name}")
        
        # Strategy state
        self.enabled = config.get('enabled', True)
        self.capital_allocation = config.get('capital_allocation', 0.25)
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.total_pnl = 0.0
        
        self.logger.info(
            f"Strategy '{name}' initialized | "
            f"Enabled: {self.enabled} | "
            f"Capital allocation: {self.capital_allocation*100}%"
        )
    
    @abstractmethod
    def generate_signal(self, symbol: str, df: pd.DataFrame, 
                       current_price: float) -> Optional[Signal]:
        """
        Generate trading signal based on market data
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            Signal object or None
        """
        pass
    
    @abstractmethod
    def should_exit(self, symbol: str, df: pd.DataFrame, 
                   current_price: float) -> bool:
        """
        Check if existing position should be exited
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            True if should exit, False otherwise
        """
        pass
    
    def calculate_position_size(self, symbol: str, entry_price: float,
                                stop_loss: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Trading pair symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size
        """
        # Get allocated capital for this strategy
        total_capital = self.portfolio.initial_capital
        allocated_capital = total_capital * self.capital_allocation
        
        # Use available cash if less than allocation
        available_capital = min(allocated_capital, self.portfolio.cash)
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            available_capital,
            entry_price,
            stop_loss
        )
        
        return position_size
    
    def execute_signal(self, signal: Signal) -> bool:
        """
        Execute a trading signal
        
        Args:
            signal: Signal to execute
            
        Returns:
            True if executed successfully, False otherwise
        """
        if not self.enabled:
            self.logger.warning(f"Strategy disabled, signal not executed: {signal}")
            return False
        
        if signal.action == 'BUY':
            return self._execute_buy(signal)
        elif signal.action == 'SELL':
            return self._execute_sell(signal)
        else:
            self.logger.debug(f"HOLD signal, no action taken for {signal.symbol}")
            return False
    
    def _execute_buy(self, signal: Signal) -> bool:
        """Execute buy signal"""
        symbol = signal.symbol
        entry_price = signal.price
        stop_loss = signal.stop_loss
        
        # Calculate position size if not provided
        if signal.quantity is None:
            if stop_loss is None:
                self.logger.error("Cannot calculate position size without stop loss")
                return False
            
            quantity = self.calculate_position_size(symbol, entry_price, stop_loss)
        else:
            quantity = signal.quantity
        
        if quantity <= 0:
            self.logger.warning(f"Invalid position size: {quantity}")
            return False
        
        # Calculate position value
        position_value = entry_price * quantity
        
        # Check if trade is allowed
        allowed, reason = self.risk_manager.check_trade_allowed(
            symbol, self.name, position_value
        )
        
        if not allowed:
            self.logger.warning(f"Trade not allowed: {reason}")
            return False
        
        # Open position
        success = self.portfolio.open_position(
            symbol=symbol,
            side='LONG',
            quantity=quantity,
            entry_price=entry_price,
            strategy=self.name
        )
        
        if success:
            # Set stop loss and take profit
            if stop_loss:
                self.portfolio.update_stop_loss(symbol, self.name, stop_loss)
            if signal.take_profit:
                self.portfolio.update_take_profit(symbol, self.name, signal.take_profit)
            
            self.trades_executed += 1
            self.logger.info(
                f"BUY executed: {symbol} | Qty: {quantity} | "
                f"Price: {entry_price} | SL: {stop_loss} | TP: {signal.take_profit}"
            )
        
        return success
    
    def _execute_sell(self, signal: Signal) -> bool:
        """Execute sell signal"""
        symbol = signal.symbol
        exit_price = signal.price
        
        # Get position
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position:
            self.logger.warning(f"No position to sell for {symbol}")
            return False
        
        # Close position
        pnl = self.portfolio.close_position(
            symbol=symbol,
            strategy=self.name,
            exit_price=exit_price,
            quantity=signal.quantity
        )
        
        if pnl is not None:
            self.total_pnl += pnl
            self.logger.info(
                f"SELL executed: {symbol} | Price: {exit_price} | "
                f"PnL: {pnl:.4f}"
            )
            return True
        
        return False
    
    def update_stops(self, symbol: str, df: pd.DataFrame, current_price: float):
        """
        Update stop loss and take profit for existing positions
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
        """
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position:
            return
        
        # Calculate trailing stop if in profit
        if 'ATR_14' in df.columns:
            atr = df['ATR_14'].iloc[-1]
            trailing_stop = self.risk_manager.calculate_trailing_stop(
                position.entry_price,
                current_price,
                atr,
                position.side
            )
            
            if trailing_stop:
                # Only update if new stop is better
                if position.stop_loss is None or \
                   (position.side == 'LONG' and trailing_stop > position.stop_loss) or \
                   (position.side == 'SHORT' and trailing_stop < position.stop_loss):
                    self.portfolio.update_stop_loss(symbol, self.name, trailing_stop)
                    self.logger.info(f"Trailing stop updated for {symbol}: {trailing_stop}")
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss is hit
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            
        Returns:
            True if stop loss hit, False otherwise
        """
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position or not position.stop_loss:
            return False
        
        if position.side == 'LONG' and current_price <= position.stop_loss:
            self.logger.warning(f"Stop loss hit for {symbol}: {current_price} <= {position.stop_loss}")
            return True
        elif position.side == 'SHORT' and current_price >= position.stop_loss:
            self.logger.warning(f"Stop loss hit for {symbol}: {current_price} >= {position.stop_loss}")
            return True
        
        return False
    
    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        Check if take profit is hit
        
        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            
        Returns:
            True if take profit hit, False otherwise
        """
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position or not position.take_profit:
            return False
        
        if position.side == 'LONG' and current_price >= position.take_profit:
            self.logger.info(f"Take profit hit for {symbol}: {current_price} >= {position.take_profit}")
            return True
        elif position.side == 'SHORT' and current_price <= position.take_profit:
            self.logger.info(f"Take profit hit for {symbol}: {current_price} <= {position.take_profit}")
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Get strategy statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'signals_generated': self.signals_generated,
            'trades_executed': self.trades_executed,
            'total_pnl': self.total_pnl,
            'capital_allocation': self.capital_allocation
        }

