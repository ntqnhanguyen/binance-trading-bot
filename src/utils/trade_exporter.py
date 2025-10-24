"""
Trade exporter with improved formatting and analysis
"""
import pandas as pd
from typing import List, Dict
from datetime import datetime


class TradeExporter:
    """Export and format trade history"""
    
    @staticmethod
    def format_trades_df(trade_history: List[Dict]) -> pd.DataFrame:
        """
        Format trade history into a well-structured DataFrame
        
        Args:
            trade_history: List of trade records
            
        Returns:
            Formatted DataFrame
        """
        if not trade_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(trade_history)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Reorder columns for better readability
        column_order = [
            'timestamp',
            'symbol',
            'strategy',
            'action',
            'order_type',
            'side',
            'price',
            'quantity',
            'value',
            'pnl',
            'pnl_pct',
            'cumulative_pnl',
            'cash_after'
        ]
        
        # Add optional columns if they exist
        optional_cols = ['entry_price', 'entry_value', 'win']
        for col in optional_cols:
            if col in df.columns:
                column_order.append(col)
        
        # Select only existing columns
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        # Round numeric columns
        numeric_cols = ['price', 'quantity', 'value', 'pnl', 'pnl_pct', 
                       'cumulative_pnl', 'cash_after']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].round(8)
        
        return df
    
    @staticmethod
    def export_to_csv(trade_history: List[Dict], filepath: str):
        """
        Export trades to CSV with improved format
        
        Args:
            trade_history: List of trade records
            filepath: Output file path
        """
        df = TradeExporter.format_trades_df(trade_history)
        
        if df.empty:
            print(f"No trades to export")
            return
        
        df.to_csv(filepath, index=False)
        print(f"Exported {len(df)} trade records to {filepath}")
    
    @staticmethod
    def get_trade_summary(trade_history: List[Dict]) -> Dict:
        """
        Get summary statistics from trade history
        
        Args:
            trade_history: List of trade records
            
        Returns:
            Dictionary with summary statistics
        """
        df = TradeExporter.format_trades_df(trade_history)
        
        if df.empty:
            return {}
        
        # Filter only CLOSE actions for PnL analysis
        closed_trades = df[df['action'] == 'CLOSE'].copy()
        
        if closed_trades.empty:
            return {
                'total_orders': len(df),
                'open_orders': len(df[df['action'] == 'OPEN']),
                'close_orders': 0,
                'total_pnl': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }
        
        # Calculate statistics
        total_pnl = closed_trades['pnl'].sum()
        winning_trades = len(closed_trades[closed_trades['pnl'] > 0])
        losing_trades = len(closed_trades[closed_trades['pnl'] < 0])
        total_closed = len(closed_trades)
        
        win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0.0
        
        avg_win = closed_trades[closed_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0.0
        avg_loss = closed_trades[closed_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0.0
        
        # Best and worst trades
        best_trade = closed_trades['pnl'].max() if total_closed > 0 else 0.0
        worst_trade = closed_trades['pnl'].min() if total_closed > 0 else 0.0
        
        # Trading volume
        total_volume = df['value'].sum()
        
        # By strategy
        strategy_stats = closed_trades.groupby('strategy').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(4)
        
        # By symbol
        symbol_stats = closed_trades.groupby('symbol').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(4)
        
        return {
            'total_orders': len(df),
            'open_orders': len(df[df['action'] == 'OPEN']),
            'close_orders': total_closed,
            'total_pnl': round(total_pnl, 4),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 4),
            'avg_loss': round(avg_loss, 4),
            'best_trade': round(best_trade, 4),
            'worst_trade': round(worst_trade, 4),
            'total_volume': round(total_volume, 4),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0.0,
            'strategy_stats': strategy_stats.to_dict() if not strategy_stats.empty else {},
            'symbol_stats': symbol_stats.to_dict() if not symbol_stats.empty else {}
        }
    
    @staticmethod
    def print_trade_summary(trade_history: List[Dict]):
        """
        Print formatted trade summary
        
        Args:
            trade_history: List of trade records
        """
        summary = TradeExporter.get_trade_summary(trade_history)
        
        if not summary:
            print("No trades to summarize")
            return
        
        print("\n" + "="*60)
        print("TRADE SUMMARY")
        print("="*60)
        
        print(f"\nOrders:")
        print(f"  Total Orders:  {summary['total_orders']}")
        print(f"  Open Orders:   {summary['open_orders']}")
        print(f"  Close Orders:  {summary['close_orders']}")
        
        print(f"\nPerformance:")
        print(f"  Total PnL:     ${summary['total_pnl']:,.4f}")
        print(f"  Total Volume:  ${summary['total_volume']:,.4f}")
        
        print(f"\nTrades:")
        print(f"  Winning:       {summary['winning_trades']}")
        print(f"  Losing:        {summary['losing_trades']}")
        print(f"  Win Rate:      {summary['win_rate']:.2f}%")
        
        print(f"\nPnL Stats:")
        print(f"  Avg Win:       ${summary['avg_win']:,.4f}")
        print(f"  Avg Loss:      ${summary['avg_loss']:,.4f}")
        print(f"  Best Trade:    ${summary['best_trade']:,.4f}")
        print(f"  Worst Trade:   ${summary['worst_trade']:,.4f}")
        print(f"  Profit Factor: {summary['profit_factor']:.2f}")
        
        print("="*60 + "\n")
    
    @staticmethod
    def export_detailed_report(trade_history: List[Dict], filepath: str):
        """
        Export detailed trade report with analysis
        
        Args:
            trade_history: List of trade records
            filepath: Output file path (without extension)
        """
        # Export trades CSV
        csv_path = f"{filepath}_trades.csv"
        TradeExporter.export_to_csv(trade_history, csv_path)
        
        # Get summary
        summary = TradeExporter.get_trade_summary(trade_history)
        
        # Export summary as text
        summary_path = f"{filepath}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("TRADE SUMMARY REPORT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Orders:\n")
            f.write(f"  Total Orders:  {summary['total_orders']}\n")
            f.write(f"  Open Orders:   {summary['open_orders']}\n")
            f.write(f"  Close Orders:  {summary['close_orders']}\n\n")
            
            f.write(f"Performance:\n")
            f.write(f"  Total PnL:     ${summary['total_pnl']:,.4f}\n")
            f.write(f"  Total Volume:  ${summary['total_volume']:,.4f}\n\n")
            
            f.write(f"Trades:\n")
            f.write(f"  Winning:       {summary['winning_trades']}\n")
            f.write(f"  Losing:        {summary['losing_trades']}\n")
            f.write(f"  Win Rate:      {summary['win_rate']:.2f}%\n\n")
            
            f.write(f"PnL Stats:\n")
            f.write(f"  Avg Win:       ${summary['avg_win']:,.4f}\n")
            f.write(f"  Avg Loss:      ${summary['avg_loss']:,.4f}\n")
            f.write(f"  Best Trade:    ${summary['best_trade']:,.4f}\n")
            f.write(f"  Worst Trade:   ${summary['worst_trade']:,.4f}\n")
            f.write(f"  Profit Factor: {summary['profit_factor']:.2f}\n\n")
            
            f.write("="*60 + "\n")
        
        print(f"Detailed report exported:")
        print(f"  - Trades: {csv_path}")
        print(f"  - Summary: {summary_path}")

