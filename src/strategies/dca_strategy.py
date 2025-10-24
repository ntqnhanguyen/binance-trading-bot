"""
Dollar-Cost Averaging (DCA) Strategy
"""
from typing import Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

from .base_strategy import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class DCAStrategy(BaseStrategy):
    """
    DCA strategy with defensive position building
    """
    
    def __init__(self, name: str, config: Dict, portfolio, risk_manager):
        """
        Initialize DCA strategy
        
        Args:
            name: Strategy name
            config: Strategy configuration
            portfolio: Portfolio instance
            risk_manager: Risk manager instance
        """
        super().__init__(name, config, portfolio, risk_manager)
        
        # DCA specific parameters
        self.max_layers = config.get('max_layers', 4)
        self.layer_drop_pct = config.get('layer_drop_pct', [5, 8, 12, 18])  # % drops for each layer
        self.tp_ladder_pct = config.get('tp_ladder_pct', [5, 8, 12])  # % gains for TP
        self.catastrophic_sl_pct = config.get('catastrophic_sl_pct', 20)  # % loss to exit all
        
        # Time-based DCA
        self.time_based = config.get('time_based', False)
        self.interval_days = config.get('interval_days', 7)
        
        # Track layers
        self.layers: Dict[str, list] = {}  # symbol -> list of layer info
        self.last_buy_time: Dict[str, datetime] = {}
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, 
                       current_price: float) -> Optional[Signal]:
        """
        Generate DCA signal
        
        Args:
            symbol: Trading pair symbol
            df: DataFrame with OHLCV and indicators
            current_price: Current market price
            
        Returns:
            Signal or None
        """
        if not self.enabled:
            return None
        
        # Check if we should start DCA or add layer
        position = self.portfolio.get_position(symbol, self.name)
        
        if position is None:
            # No position yet, check if we should start
            if self._should_start_dca(symbol, df, current_price):
                return self._create_entry_signal(symbol, df, current_price, layer=0)
        else:
            # Have position, check if we should add layer
            if self._should_add_layer(symbol, df, current_price, position):
                current_layer = len(self.layers.get(symbol, []))
                if current_layer < self.max_layers:
                    return self._create_entry_signal(symbol, df, current_price, current_layer)
        
        return None
    
    def should_exit(self, symbol: str, df: pd.DataFrame, 
                   current_price: float) -> bool:
        """
        Check if should exit DCA position
        
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
        avg_price = position.entry_price
        loss_pct = ((current_price - avg_price) / avg_price) * 100
        
        if loss_pct <= -self.catastrophic_sl_pct:
            self.logger.warning(
                f"Catastrophic SL hit for {symbol}: {loss_pct:.2f}% loss"
            )
            return True
        
        # Check take profit ladder
        gain_pct = ((current_price - avg_price) / avg_price) * 100
        
        for tp_pct in self.tp_ladder_pct:
            if gain_pct >= tp_pct:
                self.logger.info(
                    f"TP ladder hit for {symbol}: {gain_pct:.2f}% >= {tp_pct}%"
                )
                return True
        
        # Check trend reversal (MA cross)
        if 'SMA_50' in df.columns and len(df) > 50:
            sma_50 = df['SMA_50'].iloc[-1]
            if current_price < sma_50 * 0.95:  # 5% below long-term MA
                self.logger.info(
                    f"Trend reversal detected for {symbol}, exiting DCA"
                )
                return True
        
        return False
    
    def _should_start_dca(self, symbol: str, df: pd.DataFrame, 
                         current_price: float) -> bool:
        """Check if should start DCA"""
        # Check market regime - only start in favorable conditions
        if 'ADX_14' in df.columns:
            adx = df['ADX_14'].iloc[-1]
            # Don't start DCA in strong downtrend
            if adx > 25 and df['close'].iloc[-1] < df['SMA_50'].iloc[-1]:
                return False
        
        # Check volatility - don't start during high volatility
        if 'ATR_14' in df.columns:
            atr = df['ATR_14'].iloc[-1]
            atr_pct = (atr / current_price) * 100
            
            # Get historical ATR median
            atr_pct_series = (df['ATR_14'] / df['close']) * 100
            atr_median = atr_pct_series.iloc[-50:].median()
            
            if atr_pct > atr_median * 1.5:  # 50% above median
                self.logger.debug(f"Volatility too high to start DCA: {atr_pct:.2f}%")
                return False
        
        # Time-based check
        if self.time_based:
            last_buy = self.last_buy_time.get(symbol)
            if last_buy:
                days_since = (datetime.now() - last_buy).days
                if days_since < self.interval_days:
                    return False
        
        return True
    
    def _should_add_layer(self, symbol: str, df: pd.DataFrame,
                         current_price: float, position) -> bool:
        """Check if should add DCA layer"""
        layers = self.layers.get(symbol, [])
        current_layer = len(layers)
        
        if current_layer >= self.max_layers:
            return False
        
        # Calculate price drop from entry
        avg_price = position.entry_price
        drop_pct = ((avg_price - current_price) / avg_price) * 100
        
        # Check if drop threshold reached
        if current_layer < len(self.layer_drop_pct):
            threshold = self.layer_drop_pct[current_layer]
            if drop_pct >= threshold:
                self.logger.info(
                    f"DCA layer {current_layer + 1} triggered for {symbol}: "
                    f"{drop_pct:.2f}% drop"
                )
                return True
        
        # Time-based layer addition
        if self.time_based:
            last_buy = self.last_buy_time.get(symbol)
            if last_buy:
                days_since = (datetime.now() - last_buy).days
                if days_since >= self.interval_days:
                    return True
        
        return False
    
    def _create_entry_signal(self, symbol: str, df: pd.DataFrame,
                            current_price: float, layer: int) -> Signal:
        """Create entry signal for DCA layer"""
        # Calculate stop loss (catastrophic)
        stop_loss = current_price * (1 - self.catastrophic_sl_pct / 100)
        
        # Calculate position size (decreasing per layer - anti-martingale)
        base_size = self.calculate_position_size(symbol, current_price, stop_loss)
        
        # Reduce size for each layer
        layer_multiplier = 1.0 / (layer + 1)
        quantity = base_size * layer_multiplier
        
        # Calculate take profit (first TP level)
        take_profit = current_price * (1 + self.tp_ladder_pct[0] / 100)
        
        # Track layer
        if symbol not in self.layers:
            self.layers[symbol] = []
        
        self.layers[symbol].append({
            'layer': layer,
            'price': current_price,
            'quantity': quantity,
            'timestamp': datetime.now()
        })
        
        self.last_buy_time[symbol] = datetime.now()
        self.signals_generated += 1
        
        return Signal(
            action='BUY',
            symbol=symbol,
            price=current_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'strategy': self.name,
                'layer': layer,
                'total_layers': len(self.layers[symbol])
            }
        )
    
    def _execute_sell(self, signal: Signal) -> bool:
        """Override to handle partial exits (TP ladder)"""
        symbol = signal.symbol
        position = self.portfolio.get_position(symbol, self.name)
        
        if not position:
            return False
        
        # For TP ladder, sell in portions
        current_price = signal.price
        avg_price = position.entry_price
        gain_pct = ((current_price - avg_price) / avg_price) * 100
        
        # Determine sell percentage based on TP level
        sell_pct = 0.3  # Default 30%
        
        for i, tp_pct in enumerate(self.tp_ladder_pct):
            if gain_pct >= tp_pct:
                if i == 0:
                    sell_pct = 0.3  # 30% at first TP
                elif i == 1:
                    sell_pct = 0.3  # 30% at second TP
                else:
                    sell_pct = 1.0  # 100% at final TP
                break
        
        # Calculate quantity to sell
        sell_quantity = position.quantity * sell_pct
        
        # Close position (partial or full)
        pnl = self.portfolio.close_position(
            symbol=symbol,
            strategy=self.name,
            exit_price=current_price,
            quantity=sell_quantity
        )
        
        if pnl is not None:
            self.total_pnl += pnl
            
            # If fully closed, reset layers
            if sell_pct >= 1.0:
                if symbol in self.layers:
                    del self.layers[symbol]
            
            self.logger.info(
                f"DCA SELL executed: {symbol} | {sell_pct*100}% | "
                f"Price: {current_price} | PnL: {pnl:.4f}"
            )
            return True
        
        return False

