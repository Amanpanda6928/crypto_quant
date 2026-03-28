#!/usr/bin/env python3
"""
Quick test script to verify the crypto trading system
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.binance_service import get_klines
from backend.config.settings import COINS, TIMEFRAMES

def test_system():
    print("🧪 Testing Crypto Trading System")
    print("=" * 40)
    
    # Test 1: Configuration
    print(f"✅ Config loaded: {len(COINS)} coins, {len(TIMEFRAMES)} timeframes")
    
    # Test 2: Binance API
    print("\n📡 Testing Binance API...")
    try:
        klines = get_klines("BTCUSDT", "1m", 5)
        if klines:
            print(f"✅ API working: Got {len(klines)} candles for BTCUSDT")
            print(f"   Latest price: ${float(klines[-1][4]):.2f}")
        else:
            print("❌ API failed: No data received")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    # Test 3: Model files
    print("\n🤖 Checking trained models...")
    import glob
    model_files = glob.glob("models/*.joblib")
    print(f"✅ Found {len(model_files)} trained models")
    
    if model_files:
        print("   Sample models:")
        for f in model_files[:3]:
            print(f"   - {os.path.basename(f)}")
    
    print("\n🎯 System test complete!")

if __name__ == "__main__":
    test_system()
