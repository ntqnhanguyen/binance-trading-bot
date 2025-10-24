"""
Binance Exchange wrapper for unified interface
"""
from typing import Dict, List, Optional, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime

from ..utils.logger import TradingLogger
from ..utils.config import config


class BinanceExchange:
    """Wrapper for Binance API client"""
    
    def __init__(self, mode: str = None):
        """
        Initialize Binance exchange connection
        
        Args:
            mode: Trading mode (backtest, testnet, paper, mainnet)
        """
        self.logger = TradingLogger.get_logger(__name__)
        self.mode = mode or config.get_trading_mode()
        
        # Initialize client based on mode
        if self.mode in ['mainnet', 'testnet', 'paper']:
            credentials = config.get_binance_credentials()
            
            if self.mode == 'testnet':
                self.client = Client(
                    credentials['api_key'],
                    credentials['api_secret'],
                    testnet=True
                )
                self.logger.info("Connected to Binance Testnet")
            else:
                self.client = Client(
                    credentials['api_key'],
                    credentials['api_secret']
                )
                if self.mode == 'mainnet':
                    self.logger.warning("Connected to Binance MAINNET - Real trading enabled")
                else:
                    self.logger.info("Connected to Binance API in PAPER mode")
        else:
            # Backtest mode - no real connection needed
            self.client = None
            self.logger.info("Running in BACKTEST mode - No API connection")
        
        self.is_paper_mode = (self.mode == 'paper')
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balances
        
        Returns:
            Dictionary of asset balances
        """
        if self.mode == 'backtest':
            return {}
        
        try:
            account_info = self.client.get_account()
            balances = {}
            
            for balance in account_info['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get trading rules for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Symbol information dictionary
        """
        if self.mode == 'backtest':
            return None
        
        try:
            exchange_info = self.client.get_exchange_info()
            
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            
            return None
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """
        Get current ticker price
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current price
        """
        if self.mode == 'backtest':
            return None
        
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting ticker price for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500,
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """
        Get historical klines/candlestick data
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of klines to retrieve
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            DataFrame with OHLCV data
        """
        if self.mode == 'backtest':
            return pd.DataFrame()
        
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_time,
                endTime=end_time
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to appropriate types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def create_order(self, symbol: str, side: str, order_type: str,
                     quantity: float, price: float = None, **kwargs) -> Optional[Dict]:
        """
        Create a new order
        
        Args:
            symbol: Trading pair symbol
            side: BUY or SELL
            order_type: LIMIT, MARKET, STOP_LOSS_LIMIT, etc.
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            **kwargs: Additional order parameters
            
        Returns:
            Order response dictionary
        """
        if self.mode == 'backtest':
            return None
        
        # In paper mode, log the order but don't execute
        if self.is_paper_mode:
            self.logger.info(
                f"PAPER ORDER: {side} {quantity} {symbol} @ {price} ({order_type})"
            )
            return {
                'symbol': symbol,
                'orderId': f"PAPER_{datetime.now().timestamp()}",
                'side': side,
                'type': order_type,
                'price': price,
                'origQty': quantity,
                'status': 'FILLED',
                'executedQty': quantity,
                'time': int(datetime.now().timestamp() * 1000)
            }
        
        try:
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            if order_type == 'LIMIT':
                order_params['price'] = price
                order_params['timeInForce'] = kwargs.get('timeInForce', 'GTC')
            
            # Add any additional parameters
            order_params.update(kwargs)
            
            # Create the order
            order = self.client.create_order(**order_params)
            
            self.logger.info(
                f"Order created: {side} {quantity} {symbol} @ {price} "
                f"(ID: {order['orderId']})"
            )
            
            return order
        
        except BinanceAPIException as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel an existing order
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        if self.mode in ['backtest', 'paper']:
            self.logger.info(f"PAPER: Cancelled order {order_id} for {symbol}")
            return True
        
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order {order_id} cancelled for {symbol}")
            return True
        
        except BinanceAPIException as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Get all open orders
        
        Args:
            symbol: Trading pair symbol (optional, gets all if not specified)
            
        Returns:
            List of open orders
        """
        if self.mode in ['backtest', 'paper']:
            return []
        
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()
            
            return orders
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting open orders: {e}")
            return []
    
    def get_order_status(self, symbol: str, order_id: int) -> Optional[Dict]:
        """
        Get order status
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order status dictionary
        """
        if self.mode in ['backtest', 'paper']:
            return None
        
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return order
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting order status: {e}")
            return None
    
    def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get 24-hour ticker statistics
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            24h ticker data
        """
        if self.mode == 'backtest':
            return None
        
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            return ticker
        
        except BinanceAPIException as e:
            self.logger.error(f"Error getting 24h ticker for {symbol}: {e}")
            return None

