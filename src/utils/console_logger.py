"""
Enhanced Console Logger with Colors

Provides colored console output for better visibility of trading activities.
"""
import logging
from datetime import datetime
from typing import Optional


class Colors:
    """ANSI color codes for console output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


class ConsoleLogger:
    """
    Enhanced console logger with colored output
    """
    
    def __init__(self, logger: logging.Logger, enable_colors: bool = True):
        """
        Initialize ConsoleLogger
        
        Args:
            logger: Base logger instance
            enable_colors: Enable colored output
        """
        self.logger = logger
        self.enable_colors = enable_colors
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text"""
        if not self.enable_colors:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    def print_header(self, text: str):
        """Print a header line"""
        line = "=" * 80
        self.logger.info(self._colorize(line, Colors.CYAN))
        self.logger.info(self._colorize(f"  {text}", Colors.BOLD + Colors.CYAN))
        self.logger.info(self._colorize(line, Colors.CYAN))
    
    def print_section(self, text: str):
        """Print a section divider"""
        line = "-" * 80
        self.logger.info(self._colorize(line, Colors.BLUE))
        self.logger.info(self._colorize(f"  {text}", Colors.BOLD + Colors.BLUE))
        self.logger.info(self._colorize(line, Colors.BLUE))
    
    def print_equity(self, equity: float, cash: float, position_value: float):
        """Print equity information"""
        text = (
            f"💰 EQUITY: ${equity:,.2f}  |  "
            f"Cash: ${cash:,.2f}  |  "
            f"Position: ${position_value:,.2f}"
        )
        self.logger.info(self._colorize(text, Colors.BOLD + Colors.BRIGHT_CYAN))
    
    def print_pnl_state(self, state: str, daily_pnl: Optional[float] = None, 
                       gap_pnl: Optional[float] = None):
        """Print PnL Gate state"""
        if state == "RUN":
            color = Colors.BRIGHT_GREEN
            icon = "✓"
        elif state == "DEGRADED":
            color = Colors.BRIGHT_YELLOW
            icon = "⚠"
        else:  # PAUSED
            color = Colors.BRIGHT_RED
            icon = "⏸"
        
        text = f"{icon} PnL State: {state}"
        
        if daily_pnl is not None:
            text += f"  |  Daily PnL: {daily_pnl:+.2f}%"
        
        if gap_pnl is not None:
            text += f"  |  Gap PnL: {gap_pnl:+.2f}%"
        
        self.logger.info(self._colorize(text, Colors.BOLD + color))
    
    def print_order_plan(self, symbol: str, band: str, spread_pct: float,
                        grid_count: int, dca_count: int, tp_count: int):
        """Print order plan summary"""
        band_color = {
            'near': Colors.GREEN,
            'mid': Colors.YELLOW,
            'far': Colors.RED
        }.get(band, Colors.WHITE)
        
        text = (
            f"📊 {symbol} Plan: "
            f"Band={self._colorize(band.upper(), band_color)}  "
            f"Spread={spread_pct:.3f}%  |  "
            f"Grid={grid_count}  DCA={dca_count}  TP={tp_count}"
        )
        self.logger.info(text)
    
    def print_order_placed(self, order_type: str, side: str, symbol: str,
                          qty: float, price: float, tag: str = "",
                          order_id: Optional[str] = None):
        """Print order placement"""
        # Color based on side
        if side == "BUY":
            side_color = Colors.BRIGHT_GREEN
            icon = "📈"
        else:  # SELL
            side_color = Colors.BRIGHT_RED
            icon = "📉"
        
        # Color based on order type
        type_colors = {
            'GRID': Colors.CYAN,
            'DCA': Colors.YELLOW,
            'TP': Colors.MAGENTA,
            'SL': Colors.RED
        }
        type_color = type_colors.get(order_type, Colors.WHITE)
        
        text = (
            f"{icon} ORDER PLACED: "
            f"{self._colorize(order_type, Colors.BOLD + type_color)} | "
            f"{self._colorize(side, Colors.BOLD + side_color)} "
            f"{qty:.6f} {symbol} @ ${price:.2f}"
        )
        
        if tag:
            text += f"  [{tag}]"
        
        if order_id:
            text += f"  (ID: {order_id})"
        
        self.logger.info(text)
    
    def print_order_filled(self, order_type: str, side: str, symbol: str,
                          qty: float, price: float, pnl: Optional[float] = None,
                          tag: str = ""):
        """Print order fill"""
        # Color based on side
        if side == "BUY":
            side_color = Colors.BRIGHT_GREEN
            icon = "✅"
        else:  # SELL
            side_color = Colors.BRIGHT_RED
            icon = "✅"
        
        text = (
            f"{icon} ORDER FILLED: "
            f"{self._colorize(order_type, Colors.BOLD + Colors.CYAN)} | "
            f"{self._colorize(side, Colors.BOLD + side_color)} "
            f"{qty:.6f} {symbol} @ ${price:.2f}"
        )
        
        if tag:
            text += f"  [{tag}]"
        
        if pnl is not None:
            pnl_color = Colors.BRIGHT_GREEN if pnl >= 0 else Colors.BRIGHT_RED
            text += f"  PnL: {self._colorize(f'{pnl:+.2f}', pnl_color)}"
        
        self.logger.info(text)
    
    def print_order_rejected(self, order_type: str, side: str, symbol: str,
                           price: float, reason: str):
        """Print order rejection"""
        text = (
            f"❌ ORDER REJECTED: "
            f"{self._colorize(order_type, Colors.BOLD + Colors.RED)} | "
            f"{side} {symbol} @ ${price:.2f}  "
            f"Reason: {reason}"
        )
        self.logger.warning(text)
    
    def print_position(self, symbol: str, qty: float, avg_price: float,
                      current_price: float, unrealized_pnl: float,
                      unrealized_pnl_pct: float):
        """Print position status"""
        pnl_color = Colors.BRIGHT_GREEN if unrealized_pnl >= 0 else Colors.BRIGHT_RED
        
        text = (
            f"📍 POSITION: {symbol}  |  "
            f"Qty: {qty:.6f}  |  "
            f"Avg: ${avg_price:.2f}  |  "
            f"Current: ${current_price:.2f}  |  "
            f"Unrealized PnL: {self._colorize(f'{unrealized_pnl:+,.2f}', pnl_color)} "
            f"({self._colorize(f'{unrealized_pnl_pct:+.2f}%', pnl_color)})"
        )
        self.logger.info(text)
    
    def print_hard_stop(self, symbol: str, reason: str):
        """Print hard stop alert"""
        text = (
            f"🛑 HARD STOP TRIGGERED: {symbol}  |  "
            f"Reason: {reason}"
        )
        self.logger.critical(self._colorize(text, Colors.BOLD + Colors.BG_RED + Colors.WHITE))
    
    def print_auto_resume(self, symbol: str, reason: str):
        """Print auto-resume notification"""
        text = (
            f"🔄 AUTO-RESUME: {symbol}  |  "
            f"Reason: {reason}"
        )
        self.logger.info(self._colorize(text, Colors.BOLD + Colors.BRIGHT_GREEN))
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.logger.warning(self._colorize(f"⚠️  {message}", Colors.BRIGHT_YELLOW))
    
    def print_error(self, message: str):
        """Print error message"""
        self.logger.error(self._colorize(f"❌ {message}", Colors.BRIGHT_RED))
    
    def print_success(self, message: str):
        """Print success message"""
        self.logger.info(self._colorize(f"✓ {message}", Colors.BRIGHT_GREEN))
    
    def print_info(self, message: str):
        """Print info message"""
        self.logger.info(self._colorize(f"ℹ️  {message}", Colors.BRIGHT_BLUE))

