#!/usr/bin/env python3
"""
Fetch Live Market Prices & Generate Predictions
Fetches real-time prices from Binance/CoinGecko and runs AI predictions
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.binance_service import get_binance_service
from backend.app.services.coingecko_service import get_coingecko_service
from backend.app.services.live_prediction_service import LivePredictionService, COINS
import time
from datetime import datetime

def fetch_and_predict():
    """Fetch live prices and generate predictions"""
    print("="*60)
    print("🔮 NEXUS AI - Live Price Fetch & Prediction")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Fetch live prices from Binance
    print("📊 Fetching live prices from Binance...")
    binance = get_binance_service()
    prices = binance.get_all_prices()
    
    if not prices:
        print("⚠️ Binance failed, trying CoinGecko...")
        coingecko = get_coingecko_service()
        prices = coingecko.get_all_prices()
    
    if not prices:
        print("❌ Failed to fetch prices from all sources")
        return
    
    print(f"✅ Fetched {len(prices)} coin prices")
    print()
    print("💰 Current Market Prices:")
    print("-"*40)
    for coin, price in sorted(prices.items()):
        print(f"  {coin:5}: ${price:>12,.2f}")
    print()
    
    # 2. Initialize prediction service
    print("🤖 Initializing AI Prediction Service...")
    predictor = LivePredictionService()
    
    # Update live prices in predictor
    predictor.live_prices = prices
    
    # 3. Generate predictions for each coin
    print("🎯 Generating AI Predictions...")
    print("-"*60)
    
    predictions_data = []
    
    for coin_symbol in sorted(prices.keys()):
        try:
            # Find coin config
            coin_config = None
            for c in COINS:
                if c['symbol'] == coin_symbol:
                    coin_config = c
                    break
            
            if not coin_config:
                continue
            
            # Update current price in config
            coin_config['current_price'] = prices[coin_symbol]
            
            # Generate prediction for 1h timeframe
            prediction = predictor.generate_prediction(coin_config, "1h")
            
            current_price = prediction.get('current_price', prices.get(coin_symbol, 0))
            predicted_price = prediction.get('predicted_price', 0)
            signal = prediction.get('signal', 'HOLD')
            confidence = prediction.get('confidence', 0)
            
            # Calculate change
            change_pct = 0
            if current_price > 0 and predicted_price > 0:
                change_pct = ((predicted_price - current_price) / current_price) * 100
            
            predictions_data.append({
                'coin': coin_symbol,
                'current': current_price,
                'predicted': predicted_price,
                'change_pct': change_pct,
                'signal': signal,
                'confidence': confidence
            })
            
            # Signal emoji
            signal_emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
            
            print(f"{signal_emoji} {coin_symbol:5} | ${current_price:>10,.2f} → ${predicted_price:>10,.2f} | {change_pct:+6.2f}% | {signal:4} | {confidence:.0f}% conf")
            
        except Exception as e:
            print(f"⚠️  {coin_symbol:5} | Error: {e}")
    
    print()
    print("="*60)
    print("📈 Summary:")
    buy_signals = [p for p in predictions_data if p['signal'] == 'BUY']
    sell_signals = [p for p in predictions_data if p['signal'] == 'SELL']
    hold_signals = [p for p in predictions_data if p['signal'] == 'HOLD']
    
    print(f"  🟢 BUY:  {len(buy_signals)} coins")
    print(f"  🔴 SELL: {len(sell_signals)} coins")
    print(f"  ⚪ HOLD: {len(hold_signals)} coins")
    print()
    
    # Top BUY recommendations
    if buy_signals:
        print("🚀 Top BUY Recommendations:")
        top_buys = sorted(buy_signals, key=lambda x: x['confidence'], reverse=True)[:3]
        for i, p in enumerate(top_buys, 1):
            print(f"  {i}. {p['coin']} - Confidence: {p['confidence']:.0f}%, Expected: {p['change_pct']:+.2f}%")
    
    print()
    print("✅ Prediction cycle complete!")
    print("="*60)
    
    return predictions_data

if __name__ == "__main__":
    fetch_and_predict()
