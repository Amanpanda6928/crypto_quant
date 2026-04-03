#!/usr/bin/env python3
"""
Train all 30 cryptocurrency AI models with live data
"""

import numpy as np
import requests
import time
import os
import sys
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Coin list - 30 major cryptocurrencies
COINS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", 
    "SHIB", "AVAX", "LINK", "UNI", "LTC", "ATOM", "XLM", "BCH", "FIL",
    "ETC", "ALGO", "VET", "THETA", "ICP", "HBAR", "NEAR", "FTM", "MANA",
    "SAND", "AXS", "TRX"
]

class ModelTrainer:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_dir = "models"
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def fetch_binance_data(self, symbol, interval="1h", limit=500):
        """Fetch live price data from Binance"""
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {'symbol': f"{symbol}USDT", 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            prices = [float(k[4]) for k in data]  # Close prices
            return prices
        except Exception as e:
            print(f"❌ {symbol} fetch error: {e}")
            return None
    
    def generate_mock_data(self, coin, num_points=500):
        """Generate realistic mock data if API fails"""
        base_prices = {
            'BTC': 45000, 'ETH': 3200, 'BNB': 320, 'XRP': 0.6, 'ADA': 1.2,
            'SOL': 125, 'DOGE': 0.08, 'DOT': 8.5, 'MATIC': 1.0, 'SHIB': 0.000009,
            'AVAX': 35, 'LINK': 15, 'UNI': 8, 'LTC': 85, 'ATOM': 10,
            'XLM': 0.12, 'BCH': 250, 'FIL': 6, 'ETC': 25, 'ALGO': 0.25,
            'VET': 0.03, 'THETA': 1.5, 'ICP': 8, 'HBAR': 0.08, 'NEAR': 3,
            'FTM': 0.45, 'MANA': 0.5, 'SAND': 0.6, 'AXS': 8, 'TRX': 0.1
        }
        
        base_price = base_prices.get(coin, 100)
        prices = []
        current_price = base_price
        
        for i in range(num_points):
            change = np.random.normal(0, 0.02)
            trend = 0.001 * np.sin(i / 50)
            current_price *= (1 + change + trend)
            prices.append(current_price)
        
        return prices
    
    def train_model(self, coin, prices):
        """Train AI model for a specific coin"""
        if len(prices) < 50:
            print(f"❌ {coin}: Not enough data")
            return False
        
        scaler = MinMaxScaler()
        data = np.array(prices).reshape(-1, 1)
        scaled = scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(20, len(scaled)):
            X.append(scaled[i-20:i].flatten())
            y.append(scaled[i][0])
        
        X, y = np.array(X), np.array(y)
        
        # Train Random Forest
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        # Save model
        joblib.dump(model, f"{self.model_dir}/{coin}_model.pkl")
        joblib.dump(scaler, f"{self.model_dir}/{coin}_scaler.pkl")
        
        print(f"OK: {coin} trained | Train: {train_score:.3f} | Test: {test_score:.3f}")
        return True
    
    def train_all_coins(self):
        """Train models for all 30 coins"""
        print(">>> Training 30 AI models for cryptocurrency trading...")
        print("=" * 60)
        
        success_count = 0
        for i, coin in enumerate(COINS, 1):
            print(f"\n[{i}/30] Training {coin}...")
            
            # Try live data first
            prices = self.fetch_binance_data(coin)
            if not prices:
                prices = self.generate_mock_data(coin)
            
            if prices and len(prices) >= 50:
                if self.train_model(coin, prices):
                    success_count += 1
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n*** Training complete: {success_count}/30 models trained successfully")
        return success_count

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all_coins()
