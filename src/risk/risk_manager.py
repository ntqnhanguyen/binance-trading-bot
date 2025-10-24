"""
Risk management system
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from ..utils.logger import TradingLogger
from ..utils.config import config


class RiskManager:
    """Risk management and position sizing"""
    
    def __init__(self, portfolio):
        """
        Initialize risk manager
        
        Args:
            portfolio: Portfolio instance
        """
        self.logger = TradingLogger.get_logger(__name__)
        self.portfolio = portfolio
        
        # Load risk limits from config
        risk_limits = config.get_risk_limits()
        self.max_risk_per_trade = risk_limits['max_risk_per_trade']
        self.max_daily_loss = risk_limits['max_daily_loss']
        self.max_weekly_loss = risk_limits['max_weekly_loss']
        self.min_cash_reserve = risk_limits['min_cash_reserve']
        self.max_positions = risk_limits['max_positions']
        self.max_strategies_per_pair = risk_limits['max_strategies_per_pair']
        
        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        
        self.logger.info(
            f"Risk Manager initialized | "
            f"Max risk/trade: {self.max_risk_per_trade*100}% | "
            f"Max daily loss: {self.max_daily_loss*100}% | "
            f"Max weekly loss: {self.max_weekly_loss*100}%"
        )
    
    def calculate_position_size(self, capital: float, entry_price: float,
                               stop_loss: float, risk_pct: float = None) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_pct: Risk percentage (uses default if None)
            
        Returns:
            Position size in base currency
        """
        if risk_pct is None:
            risk_pct = self.max_risk_per_trade
        
        # Calculate risk amount
        risk_amount = capital * risk_pct
        
        # Calculate price risk per unit
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            self.logger.warning("Stop loss equals entry price, cannot calculate position size")
            return 0.0
        
        # Calculate position size
        position_size = risk_amount / price_risk
        
        # Ensure we don't exceed available capital
        max_position_value = capital * (1 - self.min_cash_reserve)
        max_position_size = max_position_value / entry_price
        
        position_size = min(position_size, max_position_size)
        
        self.logger.debug(
            f"Position size calculated: {position_size} | "
            f"Risk: {risk_pct*100}% | Entry: {entry_price} | SL: {stop_loss}"
        )
        
        return position_size
    
    def check_trade_allowed(self, symbol: str, strategy: str, 
                           position_value: float) -> Tuple[bool, str]:
        """
        Check if a trade is allowed based on risk rules
        
        Args:
            symbol: Trading pair symbol
            strategy: Strategy name
            position_value: Value of the proposed position
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check circuit breaker
        if self.circuit_breaker_active:
            if datetime.now() < self.circuit_breaker_until:
                return False, "Circuit breaker active"
            else:
                self.deactivate_circuit_breaker()
        
        # Check daily loss limit
        daily_loss_pct = abs(self.portfolio.daily_pnl / self.portfolio.initial_capital)
        if self.portfolio.daily_pnl < 0 and daily_loss_pct >= self.max_daily_loss:
            self.activate_circuit_breaker(duration_hours=24)
            return False, f"Daily loss limit reached: {daily_loss_pct*100:.2f}%"
        
        # Check weekly loss limit
        weekly_loss_pct = abs(self.portfolio.weekly_pnl / self.portfolio.initial_capital)
        if self.portfolio.weekly_pnl < 0 and weekly_loss_pct >= self.max_weekly_loss:
            self.activate_circuit_breaker(duration_hours=168)  # 1 week
            return False, f"Weekly loss limit reached: {weekly_loss_pct*100:.2f}%"
        
        # Check maximum number of positions
        if len(self.portfolio.positions) >= self.max_positions:
            return False, f"Maximum positions reached: {self.max_positions}"
        
        # Check strategies per pair limit
        positions_on_symbol = self.portfolio.get_positions_by_symbol(symbol)
        if len(positions_on_symbol) >= self.max_strategies_per_pair:
            return False, f"Maximum strategies per pair reached: {self.max_strategies_per_pair}"
        
        # Check minimum cash reserve
        required_cash = position_value
        remaining_cash = self.portfolio.cash - required_cash
        total_value = self.portfolio.cash
        for pos in self.portfolio.positions.values():
            total_value += pos.entry_price * pos.quantity
        
        if total_value > 0:
            cash_pct = (remaining_cash / total_value) * 100
            if cash_pct < self.min_cash_reserve * 100:
                return False, f"Insufficient cash reserve: {cash_pct:.1f}% < {self.min_cash_reserve*100}%"
        
        return True, "Trade allowed"
    
    def activate_circuit_breaker(self, duration_hours: int = 24):
        """
        Activate circuit breaker to stop trading
        
        Args:
            duration_hours: Duration in hours
        """
        self.circuit_breaker_active = True
        self.circuit_breaker_until = datetime.now() + timedelta(hours=duration_hours)
        
        self.logger.critical(
            f"CIRCUIT BREAKER ACTIVATED | "
            f"Duration: {duration_hours}h | "
            f"Until: {self.circuit_breaker_until.isoformat()}"
        )
    
    def deactivate_circuit_breaker(self):
        """Deactivate circuit breaker"""
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        self.logger.info("Circuit breaker deactivated")
    
    def calculate_stop_loss(self, entry_price: float, atr: float, 
                           side: str, multiplier: float = 2.0) -> float:
        """
        Calculate stop loss based on ATR
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            side: LONG or SHORT
            multiplier: ATR multiplier
            
        Returns:
            Stop loss price
        """
        if side == 'LONG':
            stop_loss = entry_price - (atr * multiplier)
        else:  # SHORT
            stop_loss = entry_price + (atr * multiplier)
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                             side: str, risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit based on risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: LONG or SHORT
            risk_reward_ratio: Risk-reward ratio
            
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if side == 'LONG':
            take_profit = entry_price + reward
        else:  # SHORT
            take_profit = entry_price - reward
        
        return take_profit
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float,
                                atr: float, side: str, multiplier: float = 2.0) -> Optional[float]:
        """
        Calculate trailing stop loss
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            atr: Average True Range
            side: LONG or SHORT
            multiplier: ATR multiplier
            
        Returns:
            New trailing stop price or None if not in profit
        """
        if side == 'LONG':
            if current_price > entry_price:
                trailing_stop = current_price - (atr * multiplier)
                return max(trailing_stop, entry_price)  # Never below entry
            return None
        else:  # SHORT
            if current_price < entry_price:
                trailing_stop = current_price + (atr * multiplier)
                return min(trailing_stop, entry_price)  # Never above entry
            return None
    
    def check_correlation_risk(self, symbol: str, correlation_threshold: float = 0.7) -> bool:
        """
        Check if adding position would create correlation risk
        
        Args:
            symbol: Trading pair symbol to check
            correlation_threshold: Maximum allowed correlation
            
        Returns:
            True if correlation risk is acceptable, False otherwise
        """
        # Simplified correlation check based on base currency
        # In production, use actual price correlation
        
        base_currency = symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '')
        
        correlated_count = 0
        for position in self.portfolio.positions.values():
            pos_base = position.symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '')
            
            # Simple check: same base currency or known correlations
            if base_currency == pos_base:
                correlated_count += 1
        
        # Allow maximum 2 highly correlated positions
        if correlated_count >= 2:
            self.logger.warning(
                f"Correlation risk: {correlated_count} positions correlated with {symbol}"
            )
            return False
        
        return True
    
    def get_risk_metrics(self) -> Dict:
        """
        Get current risk metrics
        
        Returns:
            Dictionary with risk metrics
        """
        stats = self.portfolio.get_statistics()
        
        daily_loss_pct = 0.0
        weekly_loss_pct = 0.0
        
        if self.portfolio.initial_capital > 0:
            daily_loss_pct = (self.portfolio.daily_pnl / self.portfolio.initial_capital) * 100
            weekly_loss_pct = (self.portfolio.weekly_pnl / self.portfolio.initial_capital) * 100
        
        return {
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_until': self.circuit_breaker_until.isoformat() if self.circuit_breaker_until else None,
            'daily_pnl_pct': daily_loss_pct,
            'weekly_pnl_pct': weekly_loss_pct,
            'daily_limit_used': abs(daily_loss_pct / (self.max_daily_loss * 100)) * 100,
            'weekly_limit_used': abs(weekly_loss_pct / (self.max_weekly_loss * 100)) * 100,
            'positions_used': len(self.portfolio.positions),
            'positions_limit': self.max_positions,
            'cash_reserve_pct': stats['cash_pct'],
            'min_cash_reserve_pct': self.min_cash_reserve * 100
        }

