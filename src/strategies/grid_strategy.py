"""
Grid Trading Strategy with Dynamic Spread
"""
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class GridStrategy(BaseStrategy):
    """
    Grid trading strategy for ranging markets with dynamic spread adjustment
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
        self.base_grid_spacing_pct = config.get('grid_spacing_pct', 1.0)  # Base % spacing
        self.tp_per_grid = config.get('tp_per_grid', 0.5)  # % profit per grid
        
        # Dynamic spread parameters
        self.use_dynamic_spread = config.get('use_dynamic_spread', True)
        self.spread_multiplier_min = config.get('spread_multiplier_min', 0.5)
        self.spread_multiplier_max = config.get('spread_multiplier_max', 2.0)
        self.volatility_lookback = config.get('volatility_lookback', 50)
        
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
        
        # Spread tracking
        self.spread_history: Dict[str, List[float]] = {}  # symbol -> spread history
    
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
        
        # Update grid spread dynamically
        if self.use_dynamic_spread:
            self._update_dynamic_spread(symbol, df, current_price)
        
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
    
    def _calculate_dynamic_spread(self, df: pd.DataFrame, current_price: float) -> float:
        """
        Calculate dynamic spread based on market volatility
        
        Args:
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            Spread multiplier (0.5 to 2.0)
        """
        # Calculate ATR-based volatility
        if 'ATR_14' not in df.columns:
            df['ATR_14'] = TechnicalIndicators.calculate_atr(df, 14)
        
        if 'ATR_14' not in df.columns or df['ATR_14'].iloc[-1] == 0:
            return 1.0  # Default multiplier
        
        # Current volatility
        current_atr = df['ATR_14'].iloc[-1]
        current_volatility = (current_atr / current_price) * 100
        
        # Historical volatility (lookback period)
        lookback = min(self.volatility_lookback, len(df))
        atr_series = df['ATR_14'].iloc[-lookback:]
        price_series = df['close'].iloc[-lookback:]
        historical_volatility = ((atr_series / price_series) * 100).values
        
        # Calculate volatility percentile
        volatility_percentile = np.percentile(historical_volatility, 50)  # Median
        volatility_std = np.std(historical_volatility)
        
        # Calculate spread multiplier based on volatility
        if volatility_std == 0:
            spread_multiplier = 1.0
        else:
            # Z-score of current volatility
            z_score = (current_volatility - volatility_percentile) / volatility_std
            
            # Map z-score to multiplier
            # High volatility (z > 1) -> wider spread (multiplier > 1)
            # Low volatility (z < -1) -> tighter spread (multiplier < 1)
            if z_score > 1:
                # High volatility: increase spread
                spread_multiplier = 1.0 + min(z_score * 0.3, 1.0)
            elif z_score < -1:
                # Low volatility: decrease spread
                spread_multiplier = 1.0 + max(z_score * 0.3, -0.5)
            else:
                # Normal volatility
                spread_multiplier = 1.0
        
        # Clamp to min/max
        spread_multiplier = max(
            self.spread_multiplier_min,
            min(self.spread_multiplier_max, spread_multiplier)
        )
        
        return spread_multiplier
    
    def _calculate_bb_width_ratio(self, df: pd.DataFrame, current_price: float) -> float:
        """
        Calculate Bollinger Band width ratio
        
        Args:
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            BB width ratio (current / median)
        """
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is None:
            return 1.0
        
        # Current BB width
        upper = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
        lower = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
        current_width = ((upper - lower) / current_price) * 100
        
        # Historical BB width
        lookback = min(self.volatility_lookback, len(bbands))
        bb_widths = []
        for i in range(lookback):
            u = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-(i+1)]
            l = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-(i+1)]
            p = df['close'].iloc[-(i+1)]
            bb_widths.append(((u - l) / p) * 100)
        
        median_width = np.median(bb_widths)
        
        if median_width == 0:
            return 1.0
        
        return current_width / median_width
    
    def _update_dynamic_spread(self, symbol: str, df: pd.DataFrame, current_price: float):
        """
        Update grid spread dynamically based on market conditions
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
        """
        if symbol not in self.grids:
            return
        
        grid_config = self.grids[symbol]
        
        # Calculate dynamic spread multiplier
        atr_multiplier = self._calculate_dynamic_spread(df, current_price)
        bb_ratio = self._calculate_bb_width_ratio(df, current_price)
        
        # Combine both factors
        # If BB is expanding (ratio > 1), increase spread
        # If BB is contracting (ratio < 1), decrease spread
        combined_multiplier = (atr_multiplier + bb_ratio) / 2
        
        # Clamp to limits
        combined_multiplier = max(
            self.spread_multiplier_min,
            min(self.spread_multiplier_max, combined_multiplier)
        )
        
        # Update grid spacing
        new_spacing_pct = self.base_grid_spacing_pct * combined_multiplier
        
        # Recalculate grid levels if spread changed significantly (>10%)
        old_spacing = grid_config.get('current_spacing_pct', self.base_grid_spacing_pct)
        if abs(new_spacing_pct - old_spacing) / old_spacing > 0.1:
            self._recalculate_grid_levels(symbol, df, current_price, new_spacing_pct)
            
            # Track spread history
            if symbol not in self.spread_history:
                self.spread_history[symbol] = []
            self.spread_history[symbol].append(combined_multiplier)
            
            # Keep only recent history
            if len(self.spread_history[symbol]) > 100:
                self.spread_history[symbol] = self.spread_history[symbol][-100:]
            
            self.logger.info(
                f"Dynamic spread updated for {symbol}: "
                f"{old_spacing:.3f}% -> {new_spacing_pct:.3f}% "
                f"(ATR: {atr_multiplier:.2f}x, BB: {bb_ratio:.2f}x)"
            )
    
    def _recalculate_grid_levels(self, symbol: str, df: pd.DataFrame, 
                                 current_price: float, new_spacing_pct: float):
        """
        Recalculate grid levels with new spacing
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            new_spacing_pct: New grid spacing percentage
        """
        if symbol not in self.grids:
            return
        
        grid_config = self.grids[symbol]
        
        # Keep the same range bounds
        upper_bound = grid_config['upper_bound']
        lower_bound = grid_config['lower_bound']
        
        # Calculate new grid step based on spacing percentage
        grid_step = current_price * (new_spacing_pct / 100)
        
        # Calculate new grid levels
        grid_levels = []
        
        # Generate levels below current price
        level = current_price
        while level > lower_bound:
            grid_levels.insert(0, level)
            level -= grid_step
        
        # Generate levels above current price
        level = current_price + grid_step
        while level < upper_bound:
            grid_levels.append(level)
            level += grid_step
        
        # Update grid configuration
        grid_config['grid_levels'] = grid_levels
        grid_config['grid_step'] = grid_step
        grid_config['current_spacing_pct'] = new_spacing_pct
        
        self.logger.debug(
            f"Grid levels recalculated for {symbol}: "
            f"{len(grid_levels)} levels, step: {grid_step:.4f}"
        )
    
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
            upper = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
            lower = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
            bb_width = ((upper - lower) / current_price) * 100
            
            # Historical BB width
            bb_width_history = []
            for i in range(min(50, len(bbands))):
                u = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-(i+1)]
                l = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-(i+1)]
                p = df['close'].iloc[-(i+1)]
                bb_width_history.append(((u - l) / p) * 100)
            
            median_width = np.median(bb_width_history)
            
            # Start grid when BB is contracting
            if bb_width < median_width * 0.8:
                return True
        
        return False
    
    def _initialize_grid(self, symbol: str, df: pd.DataFrame, current_price: float):
        """Initialize grid levels with dynamic spread"""
        # Determine grid range using Bollinger Bands or historical range
        bbands = TechnicalIndicators.calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        
        if bbands is not None:
            upper_bound = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
            lower_bound = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
        else:
            # Fallback to recent high/low
            upper_bound = df['high'].iloc[-self.range_period:].max()
            lower_bound = df['low'].iloc[-self.range_period:].min()
        
        # Calculate initial spread multiplier
        if self.use_dynamic_spread:
            spread_multiplier = self._calculate_dynamic_spread(df, current_price)
            initial_spacing_pct = self.base_grid_spacing_pct * spread_multiplier
        else:
            initial_spacing_pct = self.base_grid_spacing_pct
        
        # Calculate grid step
        grid_step = current_price * (initial_spacing_pct / 100)
        
        # Calculate grid levels
        grid_levels = []
        
        # Generate levels below current price
        level = current_price
        while level > lower_bound:
            grid_levels.insert(0, level)
            level -= grid_step
        
        # Generate levels above current price
        level = current_price + grid_step
        while level < upper_bound:
            grid_levels.append(level)
            level += grid_step
        
        # Store grid configuration
        self.grids[symbol] = {
            'active': True,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound,
            'grid_levels': grid_levels,
            'grid_step': grid_step,
            'current_spacing_pct': initial_spacing_pct,
            'buy_count': 0
        }
        
        self.active_grids[symbol] = []
        self.spread_history[symbol] = []
        
        self.logger.info(
            f"Grid initialized for {symbol} | "
            f"Range: {lower_bound:.4f} - {upper_bound:.4f} | "
            f"Levels: {len(grid_levels)} | Step: {grid_step:.4f} | "
            f"Spacing: {initial_spacing_pct:.3f}%"
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
        grid_step = grid_config['grid_step']
        take_profit = price + grid_step
        
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
                'grid_count': grid_config['buy_count'],
                'grid_spacing': grid_config['current_spacing_pct']
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
        
        upper_band = bbands[f'BBU_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
        lower_band = bbands[f'BBL_{self.bb_period}_{self.bb_std}_{self.bb_std}'].iloc[-1]
        
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
    
    def get_grid_info(self, symbol: str) -> Optional[Dict]:
        """
        Get current grid information for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Grid info dictionary or None
        """
        if symbol not in self.grids:
            return None
        
        grid_config = self.grids[symbol]
        
        return {
            'active': grid_config['active'],
            'upper_bound': grid_config['upper_bound'],
            'lower_bound': grid_config['lower_bound'],
            'num_levels': len(grid_config['grid_levels']),
            'grid_step': grid_config['grid_step'],
            'current_spacing_pct': grid_config.get('current_spacing_pct', self.base_grid_spacing_pct),
            'buy_count': grid_config['buy_count'],
            'active_levels': len(self.active_grids.get(symbol, [])),
            'spread_history': self.spread_history.get(symbol, [])
        }

