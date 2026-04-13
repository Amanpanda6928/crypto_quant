# =========================
# services/live_prediction.py - Real-time LSTM Prediction Service
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from app.services.binance_client import binance_client
from multi_coin_lstm import MultiCoinLSTM
import numpy as np

# 10 supported coins (matching live_prediction_service.py)
COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT", "LINK"
]

TIMEFRAMES = ["30m", "1h", "4h", "1d"]

class LivePredictionService:
    """
    Real-time prediction service that:
    1. Maintains live price history for all coins
    2. Uses MultiCoinLSTM for predictions
    3. Provides real-time signals via API and WebSocket
    4. Auto-trains models when needed
    """
    
    def __init__(self):
        self.lstm = MultiCoinLSTM()
        self.price_history = defaultdict(list)  # coin -> list of prices
        self.prediction_cache = {}  # coin -> latest prediction
        self.running = False
        self.update_thread = None
        self.lock = threading.Lock()
        
        # WebSocket subscribers
        self.subscribers = set()
        
    def start(self):
        """Start the live prediction service"""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print("🚀 Live Prediction Service started")
        
    def stop(self):
        """Stop the service"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("🛑 Live Prediction Service stopped")
        
    def _update_loop(self):
        """Background loop to fetch prices and generate predictions"""
        while self.running:
            try:
                self._fetch_and_update_prices()
                self._generate_predictions()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                print(f"❌ Error in update loop: {e}")
                time.sleep(5)
                
    def _fetch_and_update_prices(self):
        """Fetch live prices from Binance and update history"""
        for coin in COINS:
            try:
                symbol = f"{coin}USDT"
                price = binance_client.get_price(symbol)
                
                if price and price > 0:
                    with self.lock:
                        self.price_history[coin].append(price)
                        # Keep last 100 prices
                        if len(self.price_history[coin]) > 100:
                            self.price_history[coin].pop(0)
                            
                    # Also update LSTM price history
                    self.lstm.update_coin_price(coin, price)
                    
            except Exception as e:
                print(f"⚠️ Failed to fetch price for {coin}: {e}")
                
    def _generate_predictions(self):
        """Generate predictions for all coins"""
        predictions = {}
        
        for coin in COINS:
            try:
                # Check if we have enough price history
                with self.lock:
                    prices = self.price_history[coin].copy()
                    
                if len(prices) < 20:
                    continue
                    
                # Train model if not exists
                if coin not in self.lstm.models:
                    print(f"🔄 Training model for {coin}...")
                    self.lstm.train_coin_model(coin, prices)
                    
                # Generate signal
                signal = self.lstm.predict_coin_signal(coin)
                predictions[coin] = signal
                
            except Exception as e:
                print(f"⚠️ Prediction error for {coin}: {e}")
                
        # Update cache
        with self.lock:
            self.prediction_cache = predictions
            
        # Notify subscribers
        self._notify_subscribers(predictions)
        
    def _notify_subscribers(self, predictions: Dict[str, Any]):
        """Notify WebSocket subscribers of new predictions"""
        # This will be implemented with WebSocket manager
        pass
        
    def get_prediction(self, coin: str) -> Dict[str, Any]:
        """Get latest prediction for a specific coin"""
        coin = coin.upper().replace("USDT", "")
        
        with self.lock:
            if coin in self.prediction_cache:
                return self.prediction_cache[coin]
                
        # Generate on-demand if not in cache
        if coin in COINS:
            try:
                symbol = f"{coin}USDT"
                price = binance_client.get_price(symbol)
                
                if price:
                    self.lstm.update_coin_price(coin, price)
                    return self.lstm.predict_coin_signal(coin)
                    
            except Exception as e:
                print(f"⚠️ On-demand prediction error for {coin}: {e}")
                
        return {
            "coin": coin,
            "signal": "HOLD",
            "confidence": 0.5,
            "price": None,
            "reason": "No data available"
        }
        
    def get_all_predictions(self) -> Dict[str, Any]:
        """Get all latest predictions"""
        with self.lock:
            return dict(self.prediction_cache)
            
    def get_top_signals(self, min_confidence: float = 0.6, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top signals by confidence"""
        with self.lock:
            all_signals = list(self.prediction_cache.values())
            
        # Filter active signals
        active = [
            s for s in all_signals 
            if s.get("signal") not in ["HOLD"] 
            and s.get("confidence", 0) >= min_confidence
        ]
        
        # Sort by confidence
        active.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return active[:top_n]
        
    def get_price_history(self, coin: str, limit: int = 100) -> List[float]:
        """Get price history for a coin"""
        coin = coin.upper().replace("USDT", "")
        with self.lock:
            history = self.price_history.get(coin, [])
            return history[-limit:] if limit < len(history) else history
            
    def add_subscriber(self, subscriber_id: str):
        """Add a WebSocket subscriber"""
        self.subscribers.add(subscriber_id)
        
    def remove_subscriber(self, subscriber_id: str):
        """Remove a WebSocket subscriber"""
        self.subscribers.discard(subscriber_id)


# Global service instance
live_prediction_service = LivePredictionService()

def start_live_prediction_service():
    """Start the live prediction service in background"""
    live_prediction_service.start()
    
def get_live_prediction(coin: str) -> Dict[str, Any]:
    """Get live prediction for a coin (convenience function)"""
    return live_prediction_service.get_prediction(coin)
    
def get_all_live_predictions() -> Dict[str, Any]:
    """Get all live predictions (convenience function)"""
    return live_prediction_service.get_all_predictions()
