"""
Download historical data from Binance for backtesting
"""
import argparse
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client
import time


def download_klines(symbol: str, interval: str, start_date: str, end_date: str,
                   output_file: str):
    """
    Download historical klines from Binance
    
    Args:
        symbol: Trading pair symbol
        interval: Kline interval (1m, 5m, 15m, 1h, 1d, etc.)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_file: Output CSV file path
    """
    print(f"Downloading {symbol} {interval} data...")
    print(f"Period: {start_date} to {end_date}")
    
    # Initialize client (no API key needed for public data)
    client = Client()
    
    # Convert dates to timestamps
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
    
    all_klines = []
    current_ts = start_ts
    
    # Download in chunks (max 1000 per request)
    while current_ts < end_ts:
        try:
            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=current_ts,
                limit=1000
            )
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            # Update timestamp for next batch
            current_ts = klines[-1][0] + 1
            
            # Progress
            progress = ((current_ts - start_ts) / (end_ts - start_ts)) * 100
            print(f"Progress: {progress:.1f}%", end='\r')
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\nError: {e}")
            break
    
    print(f"\nDownloaded {len(all_klines)} candles")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # Convert types
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # Set index
    df.set_index('timestamp', inplace=True)
    
    # Keep only OHLCV columns
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    # Save to CSV
    df.to_csv(output_file)
    print(f"Saved to {output_file}")
    
    return df


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Download historical data from Binance')
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT', 'ETHUSDT'],
                       help='Trading symbols')
    parser.add_argument('--interval', type=str, default='15m',
                       help='Kline interval (1m, 5m, 15m, 1h, 4h, 1d)')
    parser.add_argument('--start', type=str, default='2023-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2023-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default='./data',
                       help='Output directory')
    
    args = parser.parse_args()
    
    print("="*60)
    print("BINANCE HISTORICAL DATA DOWNLOADER")
    print("="*60)
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Interval: {args.interval}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Output: {args.output_dir}")
    print("="*60 + "\n")
    
    # Download data for each symbol
    for symbol in args.symbols:
        output_file = f"{args.output_dir}/{symbol}_{args.interval}.csv"
        
        try:
            download_klines(
                symbol=symbol,
                interval=args.interval,
                start_date=args.start,
                end_date=args.end,
                output_file=output_file
            )
            print(f"✓ {symbol} completed\n")
            
        except Exception as e:
            print(f"✗ {symbol} failed: {e}\n")
            continue
    
    print("="*60)
    print("Download completed!")
    print("="*60)


if __name__ == '__main__':
    main()

