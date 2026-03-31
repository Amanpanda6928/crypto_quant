# ==================================================
# 🚀 MULTI-COIN LSTM SYSTEM (30 COINS)
# ==================================================

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import os
import time
from datetime import datetime

class MultiCoinLSTM:
    def __init__(self):
        self.models = {}  # Dictionary to store models for each coin
        self.scalers = {}  # Dictionary to store scalers for each coin
        self.price_history = {}  # Dictionary to store price history for each coin
        self.model_dir = "models"
        
        # Create models directory if it doesn't exist
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        
        # 20 major cryptocurrencies - matching frontend
        self.coins = [
            "BTC", "ETH", "BNB", "SOL", "XRP",
            "ADA", "AVAX", "DOGE", "DOT", "LINK",
            "MATIC", "LTC", "BCH", "UNI", "ATOM",
            "XLM", "ICP", "APT", "ARB", "OP"
        ]
        
        self.load_all_models()
    
    def load_all_models(self):
        """Load all trained models"""
        loaded_count = 0
        for coin in self.coins:
            model_path = f"{self.model_dir}/{coin}_model.pkl"
            scaler_path = f"{self.model_dir}/{coin}_scaler.pkl"
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    self.models[coin] = joblib.load(model_path)
                    self.scalers[coin] = joblib.load(scaler_path)
                    self.price_history[coin] = []
                    loaded_count += 1
                    print(f"✅ {coin} model loaded")
                except:
                    print(f"❌ Failed to load {coin} model")
            else:
                print(f"⚠️ {coin} model not found, will train on demand")
        
        print(f"\n📊 Loaded {loaded_count}/{len(self.coins)} models")
    
    def train_coin_model(self, coin, prices):
        """Train model for a specific coin"""
        if len(prices) < 50:
            print(f"❌ Not enough data for {coin} (need at least 50 prices)")
            return False
        
        print(f"🔄 Training {coin} model...")
        
        scaler = MinMaxScaler()
        data = np.array(prices).reshape(-1, 1)
        scaled = scaler.fit_transform(data)
        
        # Prepare sequences
        X, y = [], []
        for i in range(20, len(scaled)):
            X.append(scaled[i-20:i].flatten())
            y.append(scaled[i][0])
        
        X, y = np.array(X), np.array(y)
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Calculate scores
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        # Save model and scaler
        model_path = f"{self.model_dir}/{coin}_model.pkl"
        scaler_path = f"{self.model_dir}/{coin}_scaler.pkl"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        self.models[coin] = model
        self.scalers[coin] = scaler
        self.price_history[coin] = prices[-100:]  # Keep last 100 prices
        
        print(f"✅ {coin} model trained - Train: {train_score:.3f}, Test: {test_score:.3f}")
        return True
    
    def predict_coin_signal(self, coin):
        """Generate signal for a specific coin"""
        if coin not in self.price_history or len(self.price_history[coin]) < 20:
            return {
                "coin": coin,
                "signal": "HOLD",
                "confidence": 0.5,
                "price": None,
                "reason": "Insufficient data"
            }
        
        if coin not in self.models:
            return {
                "coin": coin,
                "signal": "HOLD",
                "confidence": 0.5,
                "price": self.price_history[coin][-1] if self.price_history[coin] else None,
                "reason": "Model not trained"
            }
        
        try:
            recent_prices = self.price_history[coin][-20:]
            X_pred = self.scalers[coin].transform(np.array(recent_prices).reshape(-1, 1))
            X_pred = X_pred.flatten().reshape(1, -1)
            
            pred_scaled = self.models[coin].predict(X_pred)[0]
            pred_price = self.scalers[coin].inverse_transform([[pred_scaled]])[0][0]
            current_price = self.price_history[coin][-1]
            
            price_change = (pred_price - current_price) / current_price
            
            if price_change > 0.015:  # > 1.5% increase
                signal = "STRONG_BUY"
                confidence = min(0.95, 0.6 + abs(price_change) * 8)
            elif price_change > 0.008:  # > 0.8% increase
                signal = "BUY"
                confidence = min(0.85, 0.5 + abs(price_change) * 6)
            elif price_change < -0.015:  # > 1.5% decrease
                signal = "STRONG_SELL"
                confidence = min(0.95, 0.6 + abs(price_change) * 8)
            elif price_change < -0.008:  # > 0.8% decrease
                signal = "SELL"
                confidence = min(0.85, 0.5 + abs(price_change) * 6)
            else:
                signal = "HOLD"
                confidence = 0.6
            
            return {
                "coin": coin,
                "signal": signal,
                "confidence": round(confidence, 3),
                "price": round(current_price, 6),
                "predicted_price": round(pred_price, 6),
                "price_change": round(price_change * 100, 2),
                "reason": f"Predicted {price_change*100:.2f}% change"
            }
            
        except Exception as e:
            return {
                "coin": coin,
                "signal": "HOLD",
                "confidence": 0.5,
                "price": self.price_history[coin][-1] if self.price_history[coin] else None,
                "reason": f"Prediction error: {str(e)[:50]}"
            }
    
    def update_coin_price(self, coin, price):
        """Update price for a specific coin"""
        if coin not in self.price_history:
            self.price_history[coin] = []
        
        self.price_history[coin].append(price)
        if len(self.price_history[coin]) > 100:
            self.price_history[coin].pop(0)
    
    def get_all_signals(self):
        """Get signals for all coins"""
        signals = {}
        for coin in self.coins:
            signals[coin] = self.predict_coin_signal(coin)
        return signals
    
    def get_top_signals(self, top_n=10):
        """Get top N signals by confidence"""
        all_signals = self.get_all_signals()
        
        # Filter out HOLD signals and sort by confidence
        active_signals = [
            signal for signal in all_signals.values() 
            if signal["signal"] not in ["HOLD"] and signal["confidence"] > 0.6
        ]
        
        active_signals.sort(key=lambda x: x["confidence"], reverse=True)
        return active_signals[:top_n]
    
    def generate_sample_data(self, base_price, volatility=0.03):
        """Generate sample price data for testing"""
        np.random.seed(int(time.time()) % 1000)
        prices = []
        
        for i in range(100):
            change = np.random.normal(0, volatility)
            base_price *= (1 + change)
            prices.append(base_price)
        
        return prices

# Global multi-coin LSTM instance
multi_lstm = MultiCoinLSTM()

def test_all_coins():
    """Test all 20 coins with sample data"""
    print("🚀 MULTI-COIN LSTM SYSTEM - 20 CRYPTOCURRENCIES")
    print("=" * 60)
    
    # Get prices for all 20 coins
    symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT",
        "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
        "XLMUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT", "OPUSDT"
    ]
    
    print("🔄 Training models for all 20 coins...")
    start_time = time.time()
    
    for coin in multi_lstm.coins:
        base_price = base_prices.get(coin, np.random.uniform(0.1, 1000))
        prices = multi_lstm.generate_sample_data(base_price)
        multi_lstm.train_coin_model(coin, prices)
    
    training_time = time.time() - start_time
    print(f"\n⏱️ Training completed in {training_time:.2f} seconds")
    
    print("\n🤖 GENERATING PREDICTIONS FOR ALL 20 COINS...")
    print("=" * 60)
    
    # Get all signals
    all_signals = multi_lstm.get_all_signals()
    
    # Display all signals
    for coin, signal in all_signals.items():
        status_emoji = "🟢" if "BUY" in signal["signal"] else "🔴" if "SELL" in signal["signal"] else "🟡"
        print(f"{status_emoji} {coin:6} | {signal['signal']:12} | {signal['confidence']:.3f} | ${signal['price']:>10.6f} | {signal['price_change']:>6.2f}% | {signal['reason']}")
    
    print("\n🏆 TOP 10 TRADING SIGNALS:")
    print("=" * 60)
    top_signals = multi_lstm.get_top_signals(10)
    
    for i, signal in enumerate(top_signals, 1):
        status_emoji = "🟢" if "BUY" in signal["signal"] else "🔴"
        print(f"{i:2d}. {status_emoji} {signal['coin']:6} | {signal['signal']:12} | {signal['confidence']:.3f} | {signal['price_change']:>+6.2f}% | ${signal['price']:>10.6f}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total Models: {len(multi_lstm.models)}/{len(multi_lstm.coins)}")
    print(f"   Active Signals: {len(top_signals)}")
    print(f"   Average Confidence: {np.mean([s['confidence'] for s in top_signals]):.3f}")
    
    return all_signals, top_signals

def get_real_time_signals():
    """Get real-time signals for current prices"""
    print("\n📡 REAL-TIME SIGNALS:")
    print("=" * 60)
    
    # Simulate current market prices (in real app, these would come from API)
    current_prices = {
        "BTC": 45234.56, "ETH": 3215.78, "BNB": 318.92, "XRP": 0.672, "ADA": 1.235,
        "SOL": 118.45, "DOGE": 0.0867, "DOT": 8.623, "MATIC": 0.948, "SHIB": 0.0000256
    }
    
    for coin, price in current_prices.items():
        multi_lstm.update_coin_price(coin, price)
    
    top_signals = multi_lstm.get_top_signals(5)
    
    for i, signal in enumerate(top_signals, 1):
        status_emoji = "🟢" if "BUY" in signal["signal"] else "🔴"
        print(f"{i}. {status_emoji} {signal['coin']:6} | {signal['signal']:12} | {signal['confidence']:.3f} | {signal['price_change']:>+6.2f}%")
    
    return top_signals

if __name__ == "__main__":
    # Test all coins
    test_all_coins()
    
    # Show real-time signals
    get_real_time_signals()
