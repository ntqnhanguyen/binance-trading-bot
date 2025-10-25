"""
Test Enhanced Logging Features

Demonstrates the new colored console output and order logging capabilities.
"""
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.logger import TradingLogger
from src.utils.console_logger import ConsoleLogger
from src.utils.order_logger import OrderLogger


def test_console_logger():
    """Test ConsoleLogger with various output types"""
    print("\n" + "="*80)
    print("TESTING ENHANCED CONSOLE LOGGER")
    print("="*80 + "\n")
    
    # Initialize logger
    logger = TradingLogger.get_logger('TestLogger')
    console = ConsoleLogger(logger, enable_colors=True)
    
    # Test header
    console.print_header("Trading Loop - 2025-10-25 14:30:00")
    
    # Test equity display
    console.print_equity(
        equity=10500.50,
        cash=8500.00,
        position_value=2000.50
    )
    
    # Test PnL states
    console.print_pnl_state("RUN", daily_pnl=2.5, gap_pnl=1.2)
    console.print_pnl_state("DEGRADED", daily_pnl=-3.2, gap_pnl=-2.1)
    console.print_pnl_state("PAUSED", daily_pnl=-6.5, gap_pnl=-8.2)
    
    # Test section
    console.print_section("BTCUSDT @ $67,850.00")
    
    # Test order plan
    console.print_order_plan(
        symbol="BTCUSDT",
        band="mid",
        spread_pct=0.5,
        grid_count=6,
        dca_count=2,
        tp_count=1
    )
    
    # Test order placement - Grid orders
    console.print_order_placed(
        order_type="GRID",
        side="BUY",
        symbol="BTCUSDT",
        qty=0.0147,
        price=67500.00,
        tag="grid_buy_1",
        order_id="12345678"
    )
    
    console.print_order_placed(
        order_type="GRID",
        side="SELL",
        symbol="BTCUSDT",
        qty=0.0147,
        price=68200.00,
        tag="grid_sell_1",
        order_id="12345679"
    )
    
    # Test DCA order
    console.print_order_placed(
        order_type="DCA",
        side="BUY",
        symbol="BTCUSDT",
        qty=0.0294,
        price=66800.00,
        tag="dca_oversold",
        order_id="12345680"
    )
    
    # Test TP order
    console.print_order_placed(
        order_type="TP",
        side="SELL",
        symbol="BTCUSDT",
        qty=0.0588,
        price=69500.00,
        tag="tp_overbought",
        order_id="12345681"
    )
    
    # Test order fills
    console.print_order_filled(
        order_type="GRID",
        side="BUY",
        symbol="BTCUSDT",
        qty=0.0147,
        price=67500.00,
        tag="grid_buy_1"
    )
    
    console.print_order_filled(
        order_type="GRID",
        side="SELL",
        symbol="BTCUSDT",
        qty=0.0147,
        price=68200.00,
        pnl=10.29,
        tag="grid_sell_1"
    )
    
    # Test position display
    console.print_position(
        symbol="BTCUSDT",
        qty=0.0294,
        avg_price=67200.00,
        current_price=67850.00,
        unrealized_pnl=19.11,
        unrealized_pnl_pct=0.97
    )
    
    # Test order rejection
    console.print_order_rejected(
        order_type="GRID",
        side="BUY",
        symbol="BTCUSDT",
        price=67000.00,
        reason="Insufficient balance"
    )
    
    # Test hard stop
    console.print_hard_stop(
        symbol="BTCUSDT",
        reason="Daily PnL <= -5.0%"
    )
    
    # Test auto-resume
    console.print_auto_resume(
        symbol="BTCUSDT",
        reason="RSI recovered > 40 and cooldown period elapsed"
    )
    
    # Test messages
    console.print_success("All orders placed successfully")
    console.print_warning("Market volatility detected - spread widened to 0.8%")
    console.print_error("Failed to connect to exchange API")
    console.print_info("Next trading loop in 60 seconds")
    
    print("\n" + "="*80)
    print("CONSOLE LOGGER TEST COMPLETED")
    print("="*80 + "\n")


def test_order_logger():
    """Test OrderLogger CSV tracking"""
    print("\n" + "="*80)
    print("TESTING ORDER LOGGER")
    print("="*80 + "\n")
    
    # Initialize order logger
    order_logger = OrderLogger(output_dir="./data/outputs/test")
    
    print(f"Session ID: {order_logger.session_id}")
    print(f"Orders file: {order_logger.orders_file}")
    print(f"Fills file: {order_logger.fills_file}")
    print()
    
    # Log some orders
    print("Logging sample orders...")
    
    # Grid buy order
    order_logger.log_order(
        symbol="BTCUSDT",
        order_type="BUY",
        side="LONG",
        action="OPEN",
        price=67500.00,
        quantity=0.0147,
        status="NEW",
        strategy="Hybrid",
        tag="grid_buy_1",
        reason="GRID",
        mode="paper",
        order_id="ORD_001"
    )
    
    # Grid sell order
    order_logger.log_order(
        symbol="BTCUSDT",
        order_type="SELL",
        side="LONG",
        action="CLOSE",
        price=68200.00,
        quantity=0.0147,
        status="NEW",
        strategy="Hybrid",
        tag="grid_sell_1",
        reason="GRID",
        mode="paper",
        order_id="ORD_002"
    )
    
    # DCA order
    order_logger.log_order(
        symbol="BTCUSDT",
        order_type="BUY",
        side="LONG",
        action="OPEN",
        price=66800.00,
        quantity=0.0294,
        status="NEW",
        strategy="Hybrid",
        tag="dca_oversold",
        reason="DCA",
        mode="paper",
        order_id="ORD_003"
    )
    
    print("✓ Orders logged\n")
    
    # Log some fills
    print("Logging sample fills...")
    
    # Grid buy fill
    order_logger.log_fill(
        symbol="BTCUSDT",
        order_id="ORD_001",
        fill_type="BUY",
        side="LONG",
        action="OPEN",
        price=67500.00,
        quantity=0.0147,
        fee=0.99225,
        fee_asset="USDT",
        pnl=0.0,
        pnl_pct=0.0,
        strategy="Hybrid",
        tag="grid_buy_1"
    )
    
    # Grid sell fill
    order_logger.log_fill(
        symbol="BTCUSDT",
        order_id="ORD_002",
        fill_type="SELL",
        side="LONG",
        action="CLOSE",
        price=68200.00,
        quantity=0.0147,
        fee=1.00254,
        fee_asset="USDT",
        pnl=10.29,
        pnl_pct=1.04,
        strategy="Hybrid",
        tag="grid_sell_1"
    )
    
    print("✓ Fills logged\n")
    
    # Update order status
    print("Updating order status...")
    order_logger.update_order_status("ORD_001", "FILLED")
    order_logger.update_order_status("ORD_002", "FILLED")
    print("✓ Status updated\n")
    
    # Print summary
    order_logger.print_summary()
    
    print("\n" + "="*80)
    print("ORDER LOGGER TEST COMPLETED")
    print("="*80 + "\n")


def test_combined_logging():
    """Test combined console and order logging"""
    print("\n" + "="*80)
    print("TESTING COMBINED LOGGING (Simulated Trading Loop)")
    print("="*80 + "\n")
    
    # Initialize loggers
    logger = TradingLogger.get_logger('CombinedTest')
    console = ConsoleLogger(logger, enable_colors=True)
    order_logger = OrderLogger(output_dir="./data/outputs/test")
    
    # Simulate trading loop
    console.print_header("Trading Loop - 2025-10-25 14:35:00")
    
    # Portfolio status
    console.print_equity(
        equity=10520.75,
        cash=8480.00,
        position_value=2040.75
    )
    
    # Symbol processing
    console.print_section("BTCUSDT @ $67,920.00")
    
    # Order plan
    console.print_order_plan(
        symbol="BTCUSDT",
        band="near",
        spread_pct=0.3,
        grid_count=6,
        dca_count=1,
        tp_count=1
    )
    
    # PnL state
    console.print_pnl_state("RUN", daily_pnl=1.8, gap_pnl=0.5)
    
    # Place orders
    orders = [
        {"type": "GRID", "side": "BUY", "price": 67700.00, "qty": 0.0147, "tag": "grid_buy_1"},
        {"type": "GRID", "side": "BUY", "price": 67500.00, "qty": 0.0147, "tag": "grid_buy_2"},
        {"type": "GRID", "side": "SELL", "price": 68100.00, "qty": 0.0147, "tag": "grid_sell_1"},
        {"type": "DCA", "side": "BUY", "price": 66900.00, "qty": 0.0294, "tag": "dca_oversold"},
        {"type": "TP", "side": "SELL", "price": 69200.00, "qty": 0.0588, "tag": "tp_overbought"},
    ]
    
    for i, order in enumerate(orders):
        order_id = f"ORD_{order_logger.session_id}_{i}"
        
        # Console log
        console.print_order_placed(
            order_type=order["type"],
            side=order["side"],
            symbol="BTCUSDT",
            qty=order["qty"],
            price=order["price"],
            tag=order["tag"],
            order_id=order_id
        )
        
        # CSV log
        order_logger.log_order(
            symbol="BTCUSDT",
            order_type=order["side"],
            side="LONG",
            action="OPEN" if order["side"] == "BUY" else "CLOSE",
            price=order["price"],
            quantity=order["qty"],
            status="NEW",
            strategy="Hybrid",
            tag=order["tag"],
            reason=order["type"],
            mode="paper",
            order_id=order_id
        )
    
    # Display position
    console.print_position(
        symbol="BTCUSDT",
        qty=0.0294,
        avg_price=67350.00,
        current_price=67920.00,
        unrealized_pnl=16.76,
        unrealized_pnl_pct=0.85
    )
    
    console.print_success("Trading loop completed successfully")
    
    print("\n" + "="*80)
    print("COMBINED LOGGING TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Run tests
    test_console_logger()
    test_order_logger()
    test_combined_logging()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")
    print("Check the following for output:")
    print("  - Console: Colored output above")
    print("  - CSV files: ./data/outputs/test/")
    print()

