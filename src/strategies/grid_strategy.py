"""
Grid Trading Strategy
"""
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class GridStrategy(BaseStrategy):
    """
    Grid trading strategy for ranging markets
    """
    
    def __init__(self, name: str, config: Dict, portfolio, risk_manager):
        """
        Initialize grid strategy
        
        Args:
            name: Strategy name
            config: Strategy configuration
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        super().__init__(name, config, portfolio, risk_manager)
        
        # Grid parameters
        self.num_grids = config.get('num_grids', 10)
        self.grid_spacing_pct = config.get('grid_spacing_pct', 1.0)  # % spacing between grids
        self.tp_per_grid = config.get('tp_per_grid', 0.5)  # % profit per grid
        
        # Range detection
        self.range_period = config.get('range_period', 50)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        
        # Safety
        self.max_buy_orders = config.get('max_buy_orders', 5)
        self.catastrophic_sl_pct = config.get('catastrophic_sl_pct', 10)
        
        # Grid state
        self.grids: Dict[str, Dict] = {}  # symbol -> grid config
        self.active_grids: Dict[str, List] = {}  # symbol -> list of active grid levels
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, 
                       current_price: float) -> Optional[Signal]:
        """
        Generate grid trading signal
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            Signal or None
        """
        if not self.enabled:
            return None
        
        # Initialize grid if not exists
        if symbol not in self.grids:
            if self._should_start_grid(symbol, df, current_price):
                self._initialize_grid(symbol, df, current_price)
        
        # Check if grid is active
        if symbol not in self.grids or not self.grids[symbol]['active']:
            return None
        
        # Generate buy signal if price hits grid level
        return self._check_grid_levels(symbol, current_price)
    
    def should_exit(self, symbol: str, df: pd.DataFrame, 
                   current_price: float) -> bool:
        """
        Check if should exit grid position
        
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
        
        # Check catastrophic stop loss
        if symbol in self.grids:
            grid_config = self.grids[symbol]
            lower_bound = grid_config['lower_bound']
            
            # Exit if price breaks below grid with confirmation
            if current_price < lower_bound * (1 - self.catastrophic_sl_pct / 100):
                self.logger.warning(
                    f"Catastrophic SL hit for grid {symbol}: "
                    f"{current_price} < {lower_bound}"
                )
                self._deactivate_grid(symbol)
                return True
        
        # Check if range breaks out
        if self._detect_breakout(df, current_price):
            self.logger.warning(f"Breakout detected for {symbol}, closing grid")
            self._deactivate_grid(symbol)
            return True
        
        # Check individual grid take profits
        if self._check_grid_take_profit(symbol, current_price):
            return True
        
        return False
    
    def _should_start_grid(self, symbol: str, df: pd.DataFrame,
                          current_price: float) -> bool:
        """Check if should start grid trading"""
        # Check if market is ranging
        if 'ADX_14' not in df.columns:
            adx_data = TechnicalIndicators.calculate_adx(df, 14)
            if adx_data is not None:
                df['ADX_14'] = adx_data['ADX_14']
        
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            if adx > 25:  # Too trending
                return False
        
        # Check volatility stability
        if 'ATR_14' not in df.columns:
            df['ATR_14'] = TechnicalIndicators.calculate_atr(df, 14)
        
        if 'ATR_14' in df.columns:
            atr = df['ATR_14'].iloc[-1]
            atr_pct = (atr / current_price) * 100
            
            # Get ATR history
            atr_pct_series = (df['ATR_14'] / df['close']) * 100
            atr_median = atr_pct_series.iloc[-50:].median()
            atr_std = atr_pct_series.iloc[-50:].std()
            
            # Don't start if volatility is too high or unstable
            if atr_pct > atr_median + atr_std:
                return False
        
        # Check Bollinger Band width (should be relatively narrow)
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        if bbands is not None:
            upper = bbands[f'BBU_{self.bb_period}_{self.bb_std}'].iloc[-1]
            lower = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
            bb_width = ((upper - lower) / current_price) * 100
            
            # Historical BB width
            bb_width_history = []
            for i in range(min(50, len(bbands))):
                u = bbands[f'BBU_{self.bb_period}_{self.bb_std}'].iloc[-(i+1)]
                l = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-(i+1)]
                p = df['close'].iloc[-(i+1)]
                bb_width_history.append(((u - l) / p) * 100)
            
            median_width = np.median(bb_width_history)
            
            # Start grid when BB is contracting
            if bb_width < median_width * 0.8:
                return True
        
        return False
    
    def _initialize_grid(self, symbol: str, df: pd.DataFrame, current_price: float):
        """Initialize grid levels"""
        # Determine grid range using Bollinger Bands or historical range
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is not None:
            upper_bound = bbands[f'BBU_{self.bb_period}_{self.bb_std}'].iloc[-1]
            lower_bound = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
        else:
            # Fallback to recent high/low
            upper_bound = df['high'].iloc[-self.range_period:].max()
            lower_bound = df['low'].iloc[-self.range_period:].min()
        
        # Calculate grid levels
        grid_range = upper_bound - lower_bound
        grid_step = grid_range / self.num_grids
        
        grid_levels = []
        for i in range(self.num_grids + 1):
            level = lower_bound + (i * grid_step)
            grid_levels.append(level)
        
        # Store grid configuration
        self.grids[symbol] = {
            'active': True,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound,
            'grid_levels': grid_levels,
            'grid_step': grid_step,
            'buy_count': 0
        }
        
        self.active_grids[symbol] = []
        
        self.logger.info(
            f"Grid initialized for {symbol} | "
            f"Range: {lower_bound:.4f} - {upper_bound:.4f} | "
            f"Levels: {self.num_grids} | Step: {grid_step:.4f}"
        )
    
    def _check_grid_levels(self, symbol: str, current_price: float) -> Optional[Signal]:
        """Check if price hits any grid level"""
        if symbol not in self.grids:
            return None
        
        grid_config = self.grids[symbol]
        grid_levels = grid_config['grid_levels']
        
        # Check if we've hit max buy orders
        if grid_config['buy_count'] >= self.max_buy_orders:
            return None
        
        # Find nearest grid level below current price
        buy_levels = [level for level in grid_levels if level < current_price]
        
        if not buy_levels:
            return None
        
        nearest_level = max(buy_levels)
        
        # Check if we're close to this level (within 0.1%)
        if abs(current_price - nearest_level) / nearest_level < 0.001:
            # Check if we haven't already bought at this level
            if nearest_level not in self.active_grids[symbol]:
                return self._create_grid_buy_signal(symbol, nearest_level, grid_config)
        
        return None
    
    def _create_grid_buy_signal(self, symbol: str, price: float, 
                               grid_config: Dict) -> Signal:
        """Create buy signal for grid level"""
        # Calculate stop loss (below grid range)
        lower_bound = grid_config['lower_bound']
        stop_loss = lower_bound * (1 - self.catastrophic_sl_pct / 100)
        
        # Calculate take profit (one grid step up)
        take_profit = price * (1 + self.tp_per_grid / 100)
        
        # Calculate position size (divide allocated capital by max buy orders)
        total_capital = self.portfolio.initial_capital * self.capital_allocation
        position_value = total_capital / self.max_buy_orders
        quantity = position_value / price
        
        # Track this grid level
        self.active_grids[symbol].append(price)
        grid_config['buy_count'] += 1
        
        self.signals_generated += 1
        
        return Signal(
            action='BUY',
            symbol=symbol,
            price=price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'strategy': self.name,
                'grid_level': price,
                'grid_count': grid_config['buy_count']
            }
        )
    
    def _check_grid_take_profit(self, symbol: str, current_price: float) -> bool:
        """Check if any grid level hit take profit"""
        if symbol not in self.active_grids:
            return False
        
        position = self.portfolio.get_position(symbol, self.name)
        if not position or not position.take_profit:
            return False
        
        # Check if current price reached TP
        if current_price >= position.take_profit:
            # Remove this grid level from active
            if self.active_grids[symbol]:
                self.active_grids[symbol].pop(0)
            
            if symbol in self.grids:
                self.grids[symbol]['buy_count'] -= 1
            
            return True
        
        return False
    
    def _detect_breakout(self, df: pd.DataFrame, current_price: float) -> bool:
        """Detect range breakout"""
        # Use Bollinger Bands
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is None:
            return False
        
        upper_band = bbands[f'BBU_{self.bb_period}_{self.bb_std}'].iloc[-1]
        lower_band = bbands[f'BBL_{self.bb_period}_{self.bb_std}'].iloc[-1]
        
        # Breakout if price closes significantly outside bands with volume
        if current_price > upper_band * 1.03 or current_price < lower_band * 0.97:
            if len(df) > 20:
                avg_volume = df['volume'].iloc[-20:].mean()
                current_volume = df['volume'].iloc[-1]
                
                if current_volume > avg_volume * 1.5:
                    return True
        
        return False
    
    def _deactivate_grid(self, symbol: str):
        """Deactivate grid for symbol"""
        if symbol in self.grids:
            self.grids[symbol]['active'] = False
            self.logger.info(f"Grid deactivated for {symbol}")
        
        if symbol in self.active_grids:
            self.active_grids[symbol] = []

