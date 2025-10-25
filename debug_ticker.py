#!/usr/bin/env python3
"""
Debug script to check actual Binance ticker response format
"""
import os
from dotenv import load_dotenv
from binance.client import Client

# Load environment
load_dotenv()

# Get credentials
mode = os.getenv('TRADING_MODE', 'testnet')

if mode == 'testnet':
    api_key = os.getenv('BINANCE_TESTNET_API_KEY')
    api_secret = os.getenv('BINANCE_TESTNET_SECRET_KEY')
    client = Client(api_key, api_secret, testnet=True)
    print("Connected to Binance Testnet")
else:
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    client = Client(api_key, api_secret)
    print("Connected to Binance Mainnet")

# Test symbol
symbol = 'SOLUSDT'

print(f"\nTesting ticker for {symbol}...")
print("="*70)

try:
    # Method 1: get_ticker (24h stats)
    print("\n1. client.get_ticker():")
    ticker1 = client.get_ticker(symbol=symbol)
    print(f"   Keys: {list(ticker1.keys())}")
    print(f"   Response: {ticker1}")
    
except Exception as e:
    print(f"   Error: {e}")

try:
    # Method 2: get_symbol_ticker (just price)
    print("\n2. client.get_symbol_ticker():")
    ticker2 = client.get_symbol_ticker(symbol=symbol)
    print(f"   Keys: {list(ticker2.keys())}")
    print(f"   Response: {ticker2}")
    
except Exception as e:
    print(f"   Error: {e}")

try:
    # Method 3: get_all_tickers
    print("\n3. client.get_all_tickers() (first match):")
    all_tickers = client.get_all_tickers()
    for t in all_tickers:
        if t['symbol'] == symbol:
            print(f"   Keys: {list(t.keys())}")
            print(f"   Response: {t}")
            break
    
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*70)
print("\nRecommendation:")
print("Use the method that works and check which field contains the price.")

