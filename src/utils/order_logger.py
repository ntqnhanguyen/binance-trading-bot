"""
Order logging and tracking system
"""
import os
import csv
from datetime import datetime
from typing import Dict, Optional
import pandas as pd


class OrderLogger:
    """
    Enhanced order logger that tracks all order activities
    and saves detailed logs to CSV files
    """
    
    def __init__(self, output_dir: str = "./data/outputs"):
        """
        Initialize OrderLogger
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate session ID
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV file paths
        self.orders_file = os.path.join(output_dir, f'orders_{self.session_id}.csv')
        self.fills_file = os.path.join(output_dir, f'fills_{self.session_id}.csv')
        self.summary_file = os.path.join(output_dir, f'summary_{self.session_id}.csv')
        
        # Initialize CSV files
        self._init_orders_csv()
        self._init_fills_csv()
        
        # In-memory tracking
        self.orders = []
        self.fills = []
        
    def _init_orders_csv(self):
        """Initialize orders CSV file with headers"""
        headers = [
            'timestamp',
            'session_id',
            'symbol',
            'order_id',
            'client_order_id',
            'type',  # BUY or SELL
            'side',  # LONG or SHORT
            'action',  # OPEN or CLOSE
            'price',
            'quantity',
            'value',
            'status',  # NEW, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
            'strategy',
            'tag',
            'reason',
            'mode'  # backtest, paper, testnet, mainnet
        ]
        
        with open(self.orders_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _init_fills_csv(self):
        """Initialize fills CSV file with headers"""
        headers = [
            'timestamp',
            'session_id',
            'symbol',
            'order_id',
            'fill_id',
            'type',  # BUY or SELL
            'side',  # LONG or SHORT
            'action',  # OPEN or CLOSE
            'price',
            'quantity',
            'value',
            'fee',
            'fee_asset',
            'pnl',
            'pnl_pct',
            'strategy',
            'tag'
        ]
        
        with open(self.fills_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def log_order(self, 
                  symbol: str,
                  order_type: str,  # BUY or SELL
                  side: str,  # LONG or SHORT
                  action: str,  # OPEN or CLOSE
                  price: float,
                  quantity: float,
                  status: str = 'NEW',
                  strategy: str = '',
                  tag: str = '',
                  reason: str = '',
                  mode: str = 'paper',
                  order_id: Optional[str] = None,
                  client_order_id: Optional[str] = None) -> Dict:
        """
        Log an order
        
        Args:
            symbol: Trading pair
            order_type: BUY or SELL
            side: LONG or SHORT
            action: OPEN or CLOSE
            price: Order price
            quantity: Order quantity
            status: Order status
            strategy: Strategy name
            tag: Order tag
            reason: Reason for order
            mode: Trading mode
            order_id: Exchange order ID
            client_order_id: Client order ID
            
        Returns:
            Order record dict
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        value = price * quantity
        
        if not order_id:
            order_id = f"ORD_{self.session_id}_{len(self.orders)}"
        
        if not client_order_id:
            client_order_id = f"CLI_{self.session_id}_{len(self.orders)}"
        
        order_record = {
            'timestamp': timestamp,
            'session_id': self.session_id,
            'symbol': symbol,
            'order_id': order_id,
            'client_order_id': client_order_id,
            'type': order_type,
            'side': side,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': value,
            'status': status,
            'strategy': strategy,
            'tag': tag,
            'reason': reason,
            'mode': mode
        }
        
        # Save to memory
        self.orders.append(order_record)
        
        # Append to CSV
        with open(self.orders_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                order_record['timestamp'],
                order_record['session_id'],
                order_record['symbol'],
                order_record['order_id'],
                order_record['client_order_id'],
                order_record['type'],
                order_record['side'],
                order_record['action'],
                f"{order_record['price']:.8f}",
                f"{order_record['quantity']:.8f}",
                f"{order_record['value']:.2f}",
                order_record['status'],
                order_record['strategy'],
                order_record['tag'],
                order_record['reason'],
                order_record['mode']
            ])
        
        return order_record
    
    def log_fill(self,
                 symbol: str,
                 order_id: str,
                 fill_type: str,  # BUY or SELL
                 side: str,  # LONG or SHORT
                 action: str,  # OPEN or CLOSE
                 price: float,
                 quantity: float,
                 fee: float = 0.0,
                 fee_asset: str = 'USDT',
                 pnl: float = 0.0,
                 pnl_pct: float = 0.0,
                 strategy: str = '',
                 tag: str = '',
                 fill_id: Optional[str] = None) -> Dict:
        """
        Log an order fill
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            fill_type: BUY or SELL
            side: LONG or SHORT
            action: OPEN or CLOSE
            price: Fill price
            quantity: Fill quantity
            fee: Trading fee
            fee_asset: Fee asset
            pnl: Profit/Loss
            pnl_pct: PnL percentage
            strategy: Strategy name
            tag: Fill tag
            fill_id: Fill ID
            
        Returns:
            Fill record dict
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        value = price * quantity
        
        if not fill_id:
            fill_id = f"FILL_{self.session_id}_{len(self.fills)}"
        
        fill_record = {
            'timestamp': timestamp,
            'session_id': self.session_id,
            'symbol': symbol,
            'order_id': order_id,
            'fill_id': fill_id,
            'type': fill_type,
            'side': side,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': value,
            'fee': fee,
            'fee_asset': fee_asset,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'strategy': strategy,
            'tag': tag
        }
        
        # Save to memory
        self.fills.append(fill_record)
        
        # Append to CSV
        with open(self.fills_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                fill_record['timestamp'],
                fill_record['session_id'],
                fill_record['symbol'],
                fill_record['order_id'],
                fill_record['fill_id'],
                fill_record['type'],
                fill_record['side'],
                fill_record['action'],
                f"{fill_record['price']:.8f}",
                f"{fill_record['quantity']:.8f}",
                f"{fill_record['value']:.2f}",
                f"{fill_record['fee']:.8f}",
                fill_record['fee_asset'],
                f"{fill_record['pnl']:.2f}",
                f"{fill_record['pnl_pct']:.2f}",
                fill_record['strategy'],
                fill_record['tag']
            ])
        
        return fill_record
    
    def update_order_status(self, order_id: str, status: str):
        """Update order status in CSV"""
        # Update in memory
        for order in self.orders:
            if order['order_id'] == order_id:
                order['status'] = status
                break
        
        # Rewrite CSV with updated status
        if os.path.exists(self.orders_file):
            df = pd.read_csv(self.orders_file)
            df.loc[df['order_id'] == order_id, 'status'] = status
            df.to_csv(self.orders_file, index=False)
    
    def generate_summary(self) -> Dict:
        """
        Generate trading summary
        
        Returns:
            Summary statistics dict
        """
        if not self.fills:
            return {
                'total_orders': len(self.orders),
                'total_fills': 0,
                'total_volume': 0.0,
                'total_fees': 0.0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_pnl': 0.0
            }
        
        fills_df = pd.DataFrame(self.fills)
        
        # Calculate metrics
        total_volume = fills_df['value'].sum()
        total_fees = fills_df['fee'].sum()
        total_pnl = fills_df['pnl'].sum()
        
        # Win rate (only for CLOSE actions)
        close_fills = fills_df[fills_df['action'] == 'CLOSE']
        if len(close_fills) > 0:
            winning_fills = close_fills[close_fills['pnl'] > 0]
            win_rate = (len(winning_fills) / len(close_fills)) * 100
            avg_pnl = close_fills['pnl'].mean()
        else:
            win_rate = 0.0
            avg_pnl = 0.0
        
        # Count by type
        buy_count = len(fills_df[fills_df['type'] == 'BUY'])
        sell_count = len(fills_df[fills_df['type'] == 'SELL'])
        
        # Count by action
        open_count = len(fills_df[fills_df['action'] == 'OPEN'])
        close_count = len(fills_df[fills_df['action'] == 'CLOSE'])
        
        summary = {
            'session_id': self.session_id,
            'total_orders': len(self.orders),
            'total_fills': len(self.fills),
            'buy_fills': buy_count,
            'sell_fills': sell_count,
            'open_fills': open_count,
            'close_fills': close_count,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl
        }
        
        # Save summary to CSV
        summary_df = pd.DataFrame([summary])
        summary_df.to_csv(self.summary_file, index=False)
        
        return summary
    
    def get_orders_df(self) -> pd.DataFrame:
        """Get orders as DataFrame"""
        if os.path.exists(self.orders_file):
            return pd.read_csv(self.orders_file)
        return pd.DataFrame()
    
    def get_fills_df(self) -> pd.DataFrame:
        """Get fills as DataFrame"""
        if os.path.exists(self.fills_file):
            return pd.read_csv(self.fills_file)
        return pd.DataFrame()
    
    def print_summary(self):
        """Print summary to console"""
        summary = self.generate_summary()
        
        print("\n" + "="*70)
        print("ORDER SUMMARY")
        print("="*70)
        print(f"Session ID: {summary['session_id']}")
        print(f"\nOrders:")
        print(f"  Total Orders: {summary['total_orders']}")
        print(f"  Total Fills: {summary['total_fills']}")
        print(f"  Buy Fills: {summary['buy_fills']}")
        print(f"  Sell Fills: {summary['sell_fills']}")
        print(f"  Open Fills: {summary['open_fills']}")
        print(f"  Close Fills: {summary['close_fills']}")
        print(f"\nPerformance:")
        print(f"  Total Volume: ${summary['total_volume']:,.2f}")
        print(f"  Total Fees: ${summary['total_fees']:.2f}")
        print(f"  Total PnL: ${summary['total_pnl']:,.2f}")
        print(f"  Win Rate: {summary['win_rate']:.2f}%")
        print(f"  Avg PnL: ${summary['avg_pnl']:.2f}")
        print(f"\nFiles:")
        print(f"  Orders: {self.orders_file}")
        print(f"  Fills: {self.fills_file}")
        print(f"  Summary: {self.summary_file}")
        print("="*70 + "\n")

