"""
Test Binance API connection
"""
import os
import sys
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test API connection based on trading mode"""
    mode = os.getenv('TRADING_MODE', 'paper')
    print("="*60)
    print(f"Testing Binance API Connection - {mode.upper()} Mode")
    print("="*60)
    
    if mode == 'backtest':
        print("✓ Backtest mode - No API connection needed")
        print("  Run: python run_backtest.py")
        return True
    
    # Get API credentials based on mode
    if mode == 'testnet':
        api_key = os.getenv('BINANCE_TESTNET_API_KEY')
        api_secret = os.getenv('BINANCE_TESTNET_API_SECRET')
        testnet = True
        print(f"Using Testnet API credentials")
    else:  # paper or mainnet
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        testnet = False
        print(f"Using Mainnet API credentials")
    
    # Check if credentials are set
    if not api_key or not api_secret:
        print("\n✗ API credentials not found!")
        print("\nPlease set the following in your .env file:")
        if mode == 'testnet':
            print("  BINANCE_TESTNET_API_KEY=your_testnet_key")
            print("  BINANCE_TESTNET_API_SECRET=your_testnet_secret")
        else:
            print("  BINANCE_API_KEY=your_api_key")
            print("  BINANCE_API_SECRET=your_api_secret")
        return False
    
    if api_key == 'your_mainnet_api_key_here' or api_key == 'your_testnet_api_key_here':
        print("\n✗ Please replace placeholder API keys with real ones!")
        print("  Edit .env file and add your actual API keys")
        return False
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Secret: {api_secret[:8]}...{api_secret[-4:]}")
    
    # Test connection
    try:
        print("\nConnecting to Binance API...")
        client = Client(api_key, api_secret, testnet=testnet)
        
        # Test 1: Server time
        print("\n1. Testing server time...")
        server_time = client.get_server_time()
        print(f"   ✓ Server time: {server_time['serverTime']}")
        
        # Test 2: Account info
        print("\n2. Testing account access...")
        account = client.get_account()
        print(f"   ✓ Account type: {account['accountType']}")
        print(f"   ✓ Can trade: {account['canTrade']}")
        print(f"   ✓ Can deposit: {account['canDeposit']}")
        print(f"   ✓ Can withdraw: {account['canWithdraw']}")
        
        # Test 3: Balances
        print("\n3. Checking balances...")
        balances = {
            b['asset']: {
                'free': float(b['free']),
                'locked': float(b['locked'])
            }
            for b in account['balances']
            if float(b['free']) > 0 or float(b['locked']) > 0
        }
        
        if balances:
            print(f"   ✓ Found {len(balances)} assets with balance:")
            for asset, balance in list(balances.items())[:5]:  # Show first 5
                total = balance['free'] + balance['locked']
                print(f"     - {asset}: {total:.8f} (Free: {balance['free']:.8f})")
            if len(balances) > 5:
                print(f"     ... and {len(balances)-5} more")
        else:
            print("   ⚠ No balances found")
            if mode == 'testnet':
                print("   Note: Testnet accounts start with 0 balance")
                print("   You may need to request test funds")
        
        # Test 4: Market data
        print("\n4. Testing market data access...")
        ticker = client.get_symbol_ticker(symbol='BTCUSDT')
        print(f"   ✓ BTC/USDT price: ${float(ticker['price']):,.2f}")
        
        # Test 5: Klines
        print("\n5. Testing historical data access...")
        klines = client.get_klines(symbol='BTCUSDT', interval='1h', limit=5)
        print(f"   ✓ Retrieved {len(klines)} candles")
        
        # Summary
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        
        if mode == 'paper':
            print("\nYou're in PAPER mode - trades will be simulated")
            print("To run: python main.py")
        elif mode == 'testnet':
            print("\nYou're in TESTNET mode - safe for testing")
            print("To run: python main.py")
        elif mode == 'mainnet':
            print("\n⚠️  WARNING: You're in MAINNET mode - REAL TRADING!")
            print("Make sure you've tested thoroughly on testnet first")
            print("Start with small amounts!")
            print("To run: python main.py")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ API CONNECTION FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        
        # Common error messages
        error_str = str(e).lower()
        print("\nTroubleshooting:")
        
        if 'invalid api-key' in error_str or 'api-key' in error_str:
            print("  • Check your API key and secret are correct")
            print("  • Make sure there are no extra spaces")
            print("  • Verify you're using the right keys (testnet vs mainnet)")
        
        if 'ip' in error_str:
            print("  • Your IP may not be whitelisted")
            print("  • Check IP restrictions in Binance API settings")
            print("  • Or disable IP whitelist (less secure)")
        
        if 'timestamp' in error_str:
            print("  • Your system time may be out of sync")
            print("  • Sync your system time with NTP server")
        
        if 'permission' in error_str:
            print("  • Check API key permissions on Binance")
            print("  • Make sure 'Spot Trading' is enabled")
        
        return False


if __name__ == '__main__':
    success = test_api_connection()
    sys.exit(0 if success else 1)

