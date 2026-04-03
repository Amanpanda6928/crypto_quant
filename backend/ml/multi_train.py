import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor

from services.binance_service import get_klines
from config.settings import COINS, TIMEFRAMES, MODEL_SEQUENCE_LENGTH

def build_model():
    """
    Build Random Forest model for price prediction
    """
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    return model

def prepare_data(prices):
    """
    Prepare training data from price series
    """
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(np.array(prices).reshape(-1, 1))
    
    X, y = [], []
    for i in range(MODEL_SEQUENCE_LENGTH, len(scaled)):
        # Use sequence of prices as features
        X.append(scaled[i-MODEL_SEQUENCE_LENGTH:i].flatten())
        y.append(scaled[i][0])
    
    return np.array(X), np.array(y), scaler

def train():
    """
    Train models for all coins and timeframes
    """
    print("🚀 Starting multi-coin training...")
    
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)
    
    for coin in COINS:
        for tf in TIMEFRAMES:
            print(f"Training {coin} {tf}")
            
            # Fetch data
            klines = get_klines(coin, tf, 500)
            if not klines:
                print(f"❌ No data for {coin} {tf}")
                continue
                
            # Extract close prices
            prices = [float(k[4]) for k in klines]
            
            if len(prices) < MODEL_SEQUENCE_LENGTH + 10:
                print(f"❌ Insufficient data for {coin} {tf}")
                continue
            
            # Prepare training data
            X, y, scaler = prepare_data(prices)
            
            # Build and train model
            model = build_model()
            model.fit(X, y)
            
            # Save model and scaler
            model_path = f"models/{coin}_{tf}.joblib"
            scaler_path = f"models/{coin}_{tf}_scaler.save"
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            print(f"✅ Saved {coin} {tf}")

if __name__ == "__main__":
    train()
