"""
Logging system for the trading bot
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import colorlog


class TradingLogger:
    """Centralized logging system"""
    
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
        """
        Get or create a logger with the specified name
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Configured logger instance
        """
        if name in TradingLogger._loggers:
            return TradingLogger._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_format = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler for all logs
        log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # General log file
        general_log_file = os.path.join(log_dir, 'trading_bot.log')
        file_handler = RotatingFileHandler(
            general_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Trade-specific log file
        if 'trade' in name.lower() or 'order' in name.lower():
            trade_log_file = os.path.join(log_dir, f'trades_{datetime.now().strftime("%Y%m%d")}.log')
            trade_handler = RotatingFileHandler(
                trade_log_file,
                maxBytes=10*1024*1024,
                backupCount=10
            )
            trade_handler.setLevel(logging.INFO)
            trade_handler.setFormatter(file_format)
            logger.addHandler(trade_handler)
        
        # Error log file
        error_log_file = os.path.join(log_dir, 'errors.log')
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        logger.addHandler(error_handler)
        
        TradingLogger._loggers[name] = logger
        return logger


def log_trade(logger: logging.Logger, action: str, symbol: str, quantity: float, 
              price: float, strategy: str, **kwargs):
    """
    Log trade execution with structured format
    
    Args:
        logger: Logger instance
        action: BUY or SELL
        symbol: Trading pair
        quantity: Order quantity
        price: Order price
        strategy: Strategy name
        **kwargs: Additional information
    """
    log_msg = (
        f"TRADE | {action} | {symbol} | "
        f"Qty: {quantity} | Price: {price} | "
        f"Strategy: {strategy}"
    )
    
    if kwargs:
        extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        log_msg += f" | {extra_info}"
    
    logger.info(log_msg)


def log_order(logger: logging.Logger, order_type: str, symbol: str, side: str,
              quantity: float, price: float = None, status: str = "PENDING", **kwargs):
    """
    Log order placement with structured format
    
    Args:
        logger: Logger instance
        order_type: LIMIT, MARKET, STOP_LOSS, etc.
        symbol: Trading pair
        side: BUY or SELL
        quantity: Order quantity
        price: Order price (optional for market orders)
        status: Order status
        **kwargs: Additional information
    """
    log_msg = (
        f"ORDER | {order_type} | {side} | {symbol} | "
        f"Qty: {quantity}"
    )
    
    if price:
        log_msg += f" | Price: {price}"
    
    log_msg += f" | Status: {status}"
    
    if kwargs:
        extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        log_msg += f" | {extra_info}"
    
    logger.info(log_msg)


def log_pnl(logger: logging.Logger, symbol: str, pnl: float, pnl_pct: float,
            strategy: str, **kwargs):
    """
    Log profit/loss information
    
    Args:
        logger: Logger instance
        symbol: Trading pair
        pnl: Profit/Loss amount
        pnl_pct: Profit/Loss percentage
        strategy: Strategy name
        **kwargs: Additional information
    """
    log_msg = (
        f"PNL | {symbol} | "
        f"Amount: {pnl:.4f} | Pct: {pnl_pct:.2f}% | "
        f"Strategy: {strategy}"
    )
    
    if kwargs:
        extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
        log_msg += f" | {extra_info}"
    
    if pnl >= 0:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

