#!/usr/bin/env python3
"""
Live prediction demo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.binance_service import get_klines
from backend.ml.model_loader import load_all, predict
from backend.config.settings import COINS, TIMEFRAMES

def demo_predictions():
    print("🔮 Live Prediction Demo")
    print("=" * 40)
    
    # Load models
    load_all()
    
    # Test a few coins
    test_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for coin in test_coins:
        print(f"\n📊 {coin}")
        print("-" * 20)
        
        for tf in TIMEFRAMES:
            try:
                # Get recent data
                klines = get_klines(coin, tf, 60)
                prices = [float(k[4]) for k in klines]
                
                if len(prices) >= 60:
                    # Make prediction
                    pred = predict(coin, prices, tf)
                    current = prices[-1]
                    
                    if pred:
                        change = ((pred - current) / current) * 100
                        signal = "📈 BUY" if change > 0.5 else "📉 SELL" if change < -0.5 else "⏸️ HOLD"
                        
                        print(f"  {tf:>3}: ${current:>8.2f} → ${pred:>8.2f} ({change:+.2f}%) {signal}")
                    else:
                        print(f"  {tf:>3}: ❌ No prediction")
                else:
                    print(f"  {tf:>3}: ❌ Insufficient data")
                    
            except Exception as e:
                print(f"  {tf:>3}: ❌ Error: {e}")

if __name__ == "__main__":
    demo_predictions()
