"""
Indicator Engine - Technical Indicator Calculator

Provides technical signals for strategy engines.
Calculates and caches indicators from OHLCV data.
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from .technical import TechnicalIndicators


class IndicatorEngine:
    """
    Engine for calculating and providing technical indicators
    """
    
    def __init__(self, symbol: str):
        """
        Initialize Indicator Engine
        
        Args:
            symbol: Trading pair symbol
        """
        self.symbol = symbol
        self._latest_signals: Optional[Dict] = None
        self._df: Optional[pd.DataFrame] = None
    
    def update(self, df: pd.DataFrame):
        """
        Update indicators with new OHLCV data
        
        Args:
            df: DataFrame with OHLCV data
        """
        if df is None or df.empty:
            return
        
        self._df = df.copy()
        
        # Calculate all indicators
        self._calculate_indicators()
        
        # Extract latest signals
        self._extract_latest_signals()
    
    def _calculate_indicators(self):
        """Calculate technical indicators on DataFrame"""
        if self._df is None or len(self._df) < 50:
            return
        
        # RSI
        if 'RSI_14' not in self._df.columns:
            rsi_data = TechnicalIndicators.calculate_rsi(self._df, 14)
            if rsi_data is not None:
                self._df['RSI_14'] = rsi_data['RSI_14']
        
        # ATR
        if 'ATR_14' not in self._df.columns:
            self._df['ATR_14'] = TechnicalIndicators.calculate_atr(self._df, 14)
        
        # EMAs
        if 'EMA_9' not in self._df.columns:
            ema_data = TechnicalIndicators.calculate_ema(self._df, 9)
            if ema_data is not None:
                self._df['EMA_9'] = ema_data['EMA_9']
        
        if 'EMA_21' not in self._df.columns:
            ema_data = TechnicalIndicators.calculate_ema(self._df, 21)
            if ema_data is not None:
                self._df['EMA_21'] = ema_data['EMA_21']
        
        if 'EMA_50' not in self._df.columns:
            ema_data = TechnicalIndicators.calculate_ema(self._df, 50)
            if ema_data is not None:
                self._df['EMA_50'] = ema_data['EMA_50']
        
        # Bollinger Bands
        if 'BBU_20_2.0_2.0' not in self._df.columns:
            bb_data = TechnicalIndicators.calculate_bollinger_bands(self._df, 20, 2.0)
            if bb_data is not None:
                self._df['BBU_20_2.0_2.0'] = bb_data['BBU_20_2.0_2.0']
                self._df['BBM_20_2.0_2.0'] = bb_data['BBM_20_2.0_2.0']
                self._df['BBL_20_2.0_2.0'] = bb_data['BBL_20_2.0_2.0']
    
    def _extract_latest_signals(self):
        """Extract latest signals from DataFrame"""
        if self._df is None or self._df.empty:
            return
        
        try:
            latest = self._df.iloc[-1]
            close = latest['close']
            
            # Calculate ATR%
            atr = latest.get('ATR_14', 0)
            atr_pct = (atr / close * 100) if close > 0 else 0
            
            self._latest_signals = {
                'close': close,
                'open': latest.get('open', close),
                'high': latest.get('high', close),
                'low': latest.get('low', close),
                'volume': latest.get('volume', 0),
                'rsi': latest.get('RSI_14', 50.0),
                'atr': atr,
                'atr_pct': atr_pct,
                'ema_fast': latest.get('EMA_9', close),
                'ema_mid': latest.get('EMA_21', close),
                'ema_slow': latest.get('EMA_50', close),
                'bb_upper': latest.get('BBU_20_2.0_2.0', close * 1.02),
                'bb_middle': latest.get('BBM_20_2.0_2.0', close),
                'bb_lower': latest.get('BBL_20_2.0_2.0', close * 0.98)
            }
        
        except Exception as e:
            print(f"Error extracting signals: {e}")
            self._latest_signals = None
    
    def latest(self) -> Optional[Dict]:
        """
        Get latest technical signals
        
        Returns:
            Dictionary with latest signals or None
        """
        return self._latest_signals
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get full DataFrame with indicators
        
        Returns:
            DataFrame or None
        """
        return self._df

