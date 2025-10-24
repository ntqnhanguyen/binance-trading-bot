"""
Trend Following Strategy
"""
from typing import Dict, Optional
import pandas as pd

from .base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend following strategy using MA, Donchian, and ADX
    """
    
    def __init__(self, name: str, config: Dict, portfolio, risk_manager):
        """
        Initialize trend following strategy
        
        Args:
            name: Strategy name
            config: Strategy configuration
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        super().__init__(name, config, portfolio, risk_manager)
        
        # Strategy parameters
        self.ma_fast = config.get('ma_fast', 20)
        self.ma_slow = config.get('ma_slow', 50)
        self.adx_threshold = config.get('adx_threshold', 25)
        self.atr_multiplier = config.get('atr_multiplier', 2.0)
        self.risk_reward_ratio = config.get('risk_reward_ratio', 2.0)
        
        # Entry method: 'ma_cross', 'donchian', 'rsi_pullback'
        self.entry_method = config.get('entry_method', 'ma_cross')
        
        # RSI parameters for pullback entry
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 40)
        self.rsi_overbought = config.get('rsi_overbought', 60)
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, 
                       current_price: float) -> Optional[Signal]:
        """
        Generate trend following signal
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            Signal or None
        """
        if not self.enabled:
            return None
        
        # Don't generate new signals if already have position
        if self.portfolio.get_position(symbol, self.name):
            return None
        
        # Check if we have enough data
        if len(df) < max(self.ma_slow, 50):
            return None
        
        # Check trend strength with ADX
        if not self._is_trending(df):
            return None
        
        # Generate signal based on entry method
        if self.entry_method == 'ma_cross':
            return self._ma_cross_signal(symbol, df, current_price)
        elif self.entry_method == 'donchian':
            return self._donchian_breakout_signal(symbol, df, current_price)
        elif self.entry_method == 'rsi_pullback':
            return self._rsi_pullback_signal(symbol, df, current_price)
        
        return None
    
    def should_exit(self, symbol: str, df: pd.DataFrame, 
                   current_price: float) -> bool:
        """
        Check if should exit trend following position
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            True if should exit
        """
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position:
            return False
        
        # Exit on MA cross reversal
        if f'SMA_{self.ma_fast}' in df.columns and f'SMA_{self.ma_slow}' in df.columns:
            ma_fast = df[f'SMA_{self.ma_fast}'].iloc[-1]
            ma_slow = df[f'SMA_{self.ma_slow}'].iloc[-1]
            ma_fast_prev = df[f'SMA_{self.ma_fast}'].iloc[-2]
            ma_slow_prev = df[f'SMA_{self.ma_slow}'].iloc[-2]
            
            # Bearish cross
            if ma_fast < ma_slow and ma_fast_prev >= ma_slow_prev:
                self.logger.info(f"MA bearish cross detected for {symbol}, exiting")
                return True
        
        # Exit if trend weakens (ADX drops significantly)
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            if adx < self.adx_threshold * 0.7:  # 30% below threshold
                self.logger.info(f"Trend weakened for {symbol}, exiting")
                return True
        
        return False
    
    def _is_trending(self, df: pd.DataFrame) -> bool:
        """Check if market is trending"""
        if 'ADX_14' not in df.columns:
            # Calculate ADX if not present
            adx_data = TechnicalIndicators.calculate_adx(df, 14)
            if adx_data is not None:
                df['ADX_14'] = adx_data['ADX_14']
        
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            return adx > self.adx_threshold
        
        return False
    
    def _ma_cross_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        """Generate signal based on MA crossover"""
        # Ensure MAs are calculated
        if f'SMA_{self.ma_fast}' not in df.columns:
            df[f'SMA_{self.ma_fast}'] = TechnicalIndicators.calculate_ma(df, self.ma_fast, 'SMA')
        if f'SMA_{self.ma_slow}' not in df.columns:
            df[f'SMA_{self.ma_slow}'] = TechnicalIndicators.calculate_ma(df, self.ma_slow, 'SMA')
        
        ma_fast = df[f'SMA_{self.ma_fast}'].iloc[-1]
        ma_slow = df[f'SMA_{self.ma_slow}'].iloc[-1]
        ma_fast_prev = df[f'SMA_{self.ma_fast}'].iloc[-2]
        ma_slow_prev = df[f'SMA_{self.ma_slow}'].iloc[-2]
        
        # Bullish cross
        if ma_fast > ma_slow and ma_fast_prev <= ma_slow_prev:
            return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _donchian_breakout_signal(self, symbol: str, df: pd.DataFrame,
                                  current_price: float) -> Optional[Signal]:
        """Generate signal based on Donchian channel breakout"""
        donchian_period = 20
        
        # Calculate Donchian channel if not present
        donchian = TechnicalIndicators.calculate_donchian_channel(df, donchian_period)
        
        if donchian is None:
            return None
        
        upper_channel = donchian[f'DCU_{donchian_period}_{donchian_period}'].iloc[-1]
        
        # Breakout above upper channel
        if current_price > upper_channel:
            # Confirm with volume increase
            if len(df) > 20:
                avg_volume = df['volume'].iloc[-20:].mean()
                current_volume = df['volume'].iloc[-1]
                
                if current_volume > avg_volume * 1.2:  # 20% above average
                    return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _rsi_pullback_signal(self, symbol: str, df: pd.DataFrame,
                            current_price: float) -> Optional[Signal]:
        """Generate signal based on RSI pullback in uptrend"""
        # Ensure we're in uptrend
        if f'SMA_{self.ma_fast}' not in df.columns:
            df[f'SMA_{self.ma_fast}'] = TechnicalIndicators.calculate_ma(df, self.ma_fast, 'SMA')
        if f'SMA_{self.ma_slow}' not in df.columns:
            df[f'SMA_{self.ma_slow}'] = TechnicalIndicators.calculate_ma(df, self.ma_slow, 'SMA')
        
        ma_fast = df[f'SMA_{self.ma_fast}'].iloc[-1]
        ma_slow = df[f'SMA_{self.ma_slow}'].iloc[-1]
        
        # Must be in uptrend
        if ma_fast <= ma_slow:
            return None
        
        # Calculate RSI if not present
        if f'RSI_{self.rsi_period}' not in df.columns:
            df[f'RSI_{self.rsi_period}'] = TechnicalIndicators.calculate_rsi(df, self.rsi_period)
        
        rsi = df[f'RSI_{self.rsi_period}'].iloc[-1]
        rsi_prev = df[f'RSI_{self.rsi_period}'].iloc[-2]
        
        # RSI pullback and bounce
        if rsi_prev < self.rsi_oversold and rsi > self.rsi_oversold:
            return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _create_entry_signal(self, symbol: str, df: pd.DataFrame,
                            current_price: float, side: str) -> Signal:
        """Create entry signal with SL and TP"""
        # Calculate ATR for stop loss
        if 'ATR_14' not in df.columns:
            df['ATR_14'] = TechnicalIndicators.calculate_atr(df, 14)
        
        atr = df['ATR_14'].iloc[-1]
        
        # Calculate stop loss
        stop_loss = self.risk_manager.calculate_stop_loss(
            current_price,
            atr,
            side,
            self.atr_multiplier
        )
        
        # Calculate take profit
        take_profit = self.risk_manager.calculate_take_profit(
            current_price,
            stop_loss,
            side,
            self.risk_reward_ratio
        )
        
        # Calculate position size
        quantity = self.calculate_position_size(symbol, current_price, stop_loss)
        
        self.signals_generated += 1
        
        return Signal(
            action='BUY' if side == 'LONG' else 'SELL',
            symbol=symbol,
            price=current_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'strategy': self.name,
                'entry_method': self.entry_method,
                'atr': atr
            }
        )
    
    def update_stops(self, symbol: str, df: pd.DataFrame, current_price: float):
        """Update trailing stop for trend following"""
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position:
            return
        
        # Use parent class trailing stop logic
        super().update_stops(symbol, df, current_price)
        
        # Additional: Move SL to breakeven after certain profit
        pnl_pct = position.get_pnl_percentage()
        
        if pnl_pct > 3.0 and position.stop_loss < position.entry_price:
            # Move to breakeven
            self.portfolio.update_stop_loss(symbol, self.name, position.entry_price)
            self.logger.info(f"Stop loss moved to breakeven for {symbol}")

