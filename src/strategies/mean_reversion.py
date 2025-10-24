"""
Mean Reversion Strategy
"""
from typing import Dict, Optional
import pandas as pd

from .base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy using RSI, Bollinger Bands, and range detection
    """
    
    def __init__(self, name: str, config: Dict, portfolio, risk_manager):
        """
        Initialize mean reversion strategy
        
        Args:
            name: Strategy name
            config: Strategy configuration
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        super().__init__(name, config, portfolio, risk_manager)
        
        # Strategy parameters
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        
        self.adx_max = config.get('adx_max', 20)  # Max ADX for ranging market
        self.atr_multiplier = config.get('atr_multiplier', 1.5)
        
        # Entry method: 'rsi', 'bollinger', 'combined'
        self.entry_method = config.get('entry_method', 'combined')
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, 
                       current_price: float) -> Optional[Signal]:
        """
        Generate mean reversion signal
        
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
        if len(df) < max(self.bb_period, 50):
            return None
        
        # Only trade in ranging market (low ADX)
        if not self._is_ranging(df):
            return None
        
        # Generate signal based on entry method
        if self.entry_method == 'rsi':
            return self._rsi_signal(symbol, df, current_price)
        elif self.entry_method == 'bollinger':
            return self._bollinger_signal(symbol, df, current_price)
        elif self.entry_method == 'combined':
            return self._combined_signal(symbol, df, current_price)
        
        return None
    
    def should_exit(self, symbol: str, df: pd.DataFrame, 
                   current_price: float) -> bool:
        """
        Check if should exit mean reversion position
        
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
        
        # Exit at midline (mean)
        if f'BBM_{self.bb_period}_{self.bb_std}' in df.columns:
            midline = df[f'BBM_{self.bb_period}_{self.bb_std}'].iloc[-1]
            
            # If price crosses midline, take profit
            if position.side == 'LONG' and current_price >= midline:
                self.logger.info(f"Price reached midline for {symbol}, taking profit")
                return True
        
        # Exit if RSI reaches opposite extreme
        if f'RSI_{self.rsi_period}' in df.columns:
            rsi = df[f'RSI_{self.rsi_period}'].iloc[-1]
            
            if position.side == 'LONG' and rsi >= self.rsi_overbought:
                self.logger.info(f"RSI overbought for {symbol}, taking profit")
                return True
        
        # Exit if market starts trending (ADX increases)
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            if adx > self.adx_max * 1.3:  # 30% above threshold
                self.logger.info(f"Market trending for {symbol}, exiting range strategy")
                return True
        
        # Exit on range breakout
        if self._detect_breakout(df, current_price):
            self.logger.warning(f"Range breakout detected for {symbol}, exiting")
            return True
        
        return False
    
    def _is_ranging(self, df: pd.DataFrame) -> bool:
        """Check if market is ranging (not trending)"""
        if 'ADX_14' not in df.columns:
            adx_data = TechnicalIndicators.calculate_adx(df, 14)
            if adx_data is not None:
                df['ADX_14'] = adx_data['ADX_14']
        
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            return adx < self.adx_max
        
        return False
    
    def _rsi_signal(self, symbol: str, df: pd.DataFrame,
                   current_price: float) -> Optional[Signal]:
        """Generate signal based on RSI"""
        # Calculate RSI if not present
        if f'RSI_{self.rsi_period}' not in df.columns:
            df[f'RSI_{self.rsi_period}'] = TechnicalIndicators.calculate_rsi(df, self.rsi_period)
        
        rsi = df[f'RSI_{self.rsi_period}'].iloc[-1]
        rsi_prev = df[f'RSI_{self.rsi_period}'].iloc[-2]
        
        # Buy on RSI oversold and turning up
        if rsi_prev < self.rsi_oversold and rsi > self.rsi_oversold:
            return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _bollinger_signal(self, symbol: str, df: pd.DataFrame,
                         current_price: float) -> Optional[Signal]:
        """Generate signal based on Bollinger Bands"""
        # Calculate Bollinger Bands if not present
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is None:
            return None
        
        lower_band = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
        
        # Buy when price touches lower band
        if current_price <= lower_band * 1.01:  # Within 1% of lower band
            # Confirm with price bouncing back
            prev_close = df['close'].iloc[-2]
            if current_price > prev_close:
                return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _combined_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        """Generate signal using both RSI and Bollinger Bands"""
        # Calculate indicators
        if f'RSI_{self.rsi_period}' not in df.columns:
            df[f'RSI_{self.rsi_period}'] = TechnicalIndicators.calculate_rsi(df, self.rsi_period)
        
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is None:
            return None
        
        rsi = df[f'RSI_{self.rsi_period}'].iloc[-1]
        lower_band = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
        
        # Both conditions must be met
        rsi_oversold = rsi < self.rsi_oversold
        at_lower_band = current_price <= lower_band * 1.02
        
        if rsi_oversold and at_lower_band:
            return self._create_entry_signal(symbol, df, current_price, 'LONG')
        
        return None
    
    def _detect_breakout(self, df: pd.DataFrame, current_price: float) -> bool:
        """Detect if price breaks out of range"""
        # Use Bollinger Bands to define range
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is None:
            return False
        
        upper_band = bbands[f'BBU_{self.bb_period}_{self.bb_std}'].iloc[-1]
        lower_band = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
        
        # Breakout if price closes significantly outside bands
        if current_price > upper_band * 1.05 or current_price < lower_band * 0.95:
            # Confirm with volume
            if len(df) > 20:
                avg_volume = df['volume'].iloc[-20:].mean()
                current_volume = df['volume'].iloc[-1]
                
                if current_volume > avg_volume * 1.3:
                    return True
        
        return False
    
    def _create_entry_signal(self, symbol: str, df: pd.DataFrame,
                            current_price: float, side: str) -> Signal:
        """Create entry signal with SL and TP"""
        # Calculate ATR for stop loss
        if 'ATR_14' not in df.columns:
            df['ATR_14'] = TechnicalIndicators.calculate_atr(df, 14)
        
        atr = df['ATR_14'].iloc[-1]
        
        # Stop loss just outside the range
        stop_loss = current_price - (atr * self.atr_multiplier)
        
        # Take profit at midline
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        if bbands is not None:
            take_profit = bbands[f'BBM_{self.bb_period}_{self.bb_std}'].iloc[-1]
        else:
            # Fallback to R:R ratio
            take_profit = self.risk_manager.calculate_take_profit(
                current_price, stop_loss, side, 1.5
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
                'rsi': df[f'RSI_{self.rsi_period}'].iloc[-1] if f'RSI_{self.rsi_period}' in df.columns else None
            }
        )

