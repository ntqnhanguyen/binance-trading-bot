"""
Technical indicators for trading strategies
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


class TechnicalIndicators:
    """Collection of technical indicators"""
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            ATR series
        """
        return ta.atr(df['high'], df['low'], df['close'], length=period)
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average Directional Index (ADX)
        
        Args:
            df: DataFrame with OHLC data
            period: ADX period
            
        Returns:
            DataFrame with ADX, +DI, -DI
        """
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=period)
        return adx_data
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, period: int = 20, ma_type: str = 'SMA') -> pd.Series:
        """
        Calculate Moving Average
        
        Args:
            df: DataFrame with price data
            period: MA period
            ma_type: Type of MA (SMA, EMA, WMA)
            
        Returns:
            MA series
        """
        if ma_type == 'SMA':
            return ta.sma(df['close'], length=period)
        elif ma_type == 'EMA':
            return ta.ema(df['close'], length=period)
        elif ma_type == 'WMA':
            return ta.wma(df['close'], length=period)
        else:
            return ta.sma(df['close'], length=period)
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            df: DataFrame with price data
            period: RSI period
            
        Returns:
            RSI series
        """
        return ta.rsi(df['close'], length=period)
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, 
                                  std_dev: float = 2.0) -> pd.DataFrame:
        """
        Calculate Bollinger Bands
        
        Args:
            df: DataFrame with price data
            period: BB period
            std_dev: Standard deviation multiplier
            
        Returns:
            DataFrame with upper, middle, lower bands
        """
        bbands = ta.bbands(df['close'], length=period, std=std_dev)
        return bbands
    
    @staticmethod
    def calculate_donchian_channel(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Donchian Channel
        
        Args:
            df: DataFrame with OHLC data
            period: Channel period
            
        Returns:
            DataFrame with upper, middle, lower channel
        """
        donchian = ta.donchian(df['high'], df['low'], length=period)
        return donchian
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD
        
        Args:
            df: DataFrame with price data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            DataFrame with MACD, signal, histogram
        """
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        return macd
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, 
                            d_period: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator
        
        Args:
            df: DataFrame with OHLC data
            k_period: %K period
            d_period: %D period
            
        Returns:
            DataFrame with %K and %D
        """
        stoch = ta.stoch(df['high'], df['low'], df['close'], 
                        k=k_period, d=d_period)
        return stoch
    
    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
        """
        Calculate volume profile
        
        Args:
            df: DataFrame with price and volume data
            bins: Number of price bins
            
        Returns:
            DataFrame with volume distribution by price level
        """
        price_range = df['close'].max() - df['close'].min()
        bin_size = price_range / bins
        
        df['price_bin'] = ((df['close'] - df['close'].min()) / bin_size).astype(int)
        volume_profile = df.groupby('price_bin')['volume'].sum()
        
        return volume_profile
    
    @staticmethod
    def detect_support_resistance(df: pd.DataFrame, window: int = 20, 
                                  threshold: float = 0.02) -> Dict[str, List[float]]:
        """
        Detect support and resistance levels
        
        Args:
            df: DataFrame with OHLC data
            window: Window for local extrema
            threshold: Minimum distance between levels (as percentage)
            
        Returns:
            Dictionary with support and resistance levels
        """
        # Find local maxima (resistance)
        resistance_levels = []
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window].max():
                resistance_levels.append(df['high'].iloc[i])
        
        # Find local minima (support)
        support_levels = []
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window].min():
                support_levels.append(df['low'].iloc[i])
        
        # Cluster nearby levels
        def cluster_levels(levels, threshold):
            if not levels:
                return []
            
            levels = sorted(levels)
            clustered = [levels[0]]
            
            for level in levels[1:]:
                if (level - clustered[-1]) / clustered[-1] > threshold:
                    clustered.append(level)
            
            return clustered
        
        return {
            'support': cluster_levels(support_levels, threshold),
            'resistance': cluster_levels(resistance_levels, threshold)
        }
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate historical volatility (standard deviation of returns)
        
        Args:
            df: DataFrame with price data
            period: Lookback period
            
        Returns:
            Volatility series
        """
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=period).std()
        return volatility
    
    @staticmethod
    def identify_trend(df: pd.DataFrame, ma_fast: int = 20, ma_slow: int = 50) -> str:
        """
        Identify current trend based on moving averages
        
        Args:
            df: DataFrame with price data
            ma_fast: Fast MA period
            ma_slow: Slow MA period
            
        Returns:
            Trend direction: 'uptrend', 'downtrend', or 'sideways'
        """
        fast_ma = ta.sma(df['close'], length=ma_fast)
        slow_ma = ta.sma(df['close'], length=ma_slow)
        
        if fast_ma.iloc[-1] > slow_ma.iloc[-1]:
            # Check if trend is strong
            if fast_ma.iloc[-1] > fast_ma.iloc[-5]:
                return 'uptrend'
        elif fast_ma.iloc[-1] < slow_ma.iloc[-1]:
            if fast_ma.iloc[-1] < fast_ma.iloc[-5]:
                return 'downtrend'
        
        return 'sideways'
    
    @staticmethod
    def calculate_market_regime(df: pd.DataFrame, atr_period: int = 14,
                               adx_period: int = 14, adx_threshold: float = 25) -> str:
        """
        Determine market regime based on volatility and trend strength
        
        Args:
            df: DataFrame with OHLC data
            atr_period: ATR period
            adx_period: ADX period
            adx_threshold: ADX threshold for trending market
            
        Returns:
            Market regime: 'trending_high_vol', 'trending_low_vol', 
                          'ranging_high_vol', 'ranging_low_vol'
        """
        atr = TechnicalIndicators.calculate_atr(df, atr_period)
        adx_data = TechnicalIndicators.calculate_adx(df, adx_period)
        
        # Normalize ATR by price
        atr_pct = (atr / df['close']) * 100
        
        # Determine volatility (high if ATR > median of last 50 periods)
        atr_median = atr_pct.iloc[-50:].median()
        is_high_vol = atr_pct.iloc[-1] > atr_median
        
        # Determine if trending
        adx_value = adx_data[f'ADX_{adx_period}'].iloc[-1]
        is_trending = adx_value > adx_threshold
        
        if is_trending:
            return 'trending_high_vol' if is_high_vol else 'trending_low_vol'
        else:
            return 'ranging_high_vol' if is_high_vol else 'ranging_low_vol'


# Convenience functions
def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all common technical indicators to DataFrame
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with added indicators
    """
    indicators = TechnicalIndicators()
    
    # Trend indicators
    df['SMA_20'] = indicators.calculate_ma(df, 20, 'SMA')
    df['SMA_50'] = indicators.calculate_ma(df, 50, 'SMA')
    df['EMA_20'] = indicators.calculate_ma(df, 20, 'EMA')
    
    # Momentum indicators
    df['RSI_14'] = indicators.calculate_rsi(df, 14)
    
    # Volatility indicators
    df['ATR_14'] = indicators.calculate_atr(df, 14)
    bbands = indicators.calculate_bollinger_bands(df, 20, 2.0)
    if bbands is not None:
        df = pd.concat([df, bbands], axis=1)
    
    # Trend strength
    adx = indicators.calculate_adx(df, 14)
    if adx is not None:
        df = pd.concat([df, adx], axis=1)
    
    # MACD
    macd = indicators.calculate_macd(df)
    if macd is not None:
        df = pd.concat([df, macd], axis=1)
    
    return df

