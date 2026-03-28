import joblib
import numpy as np
from config.settings import COINS, TIMEFRAMES

MODELS = {}
SCALERS = {}

def load_all():
    import os
    for coin in COINS:
        MODELS[coin] = {}
        SCALERS[coin] = {}

        for tf in TIMEFRAMES:
            model_path = f"models/{coin}_{tf}.joblib"
            scaler_path = f"models/{coin}_{tf}_scaler.save"
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    MODELS[coin][tf] = joblib.load(model_path)
                    SCALERS[coin][tf] = joblib.load(scaler_path)
                except Exception as e:
                    print(f"Error loading model {coin} {tf}: {e}")
            else:
                # Silently skip missing models
                pass

def predict(symbol, prices, tf):
    if symbol not in MODELS or tf not in MODELS[symbol]:
        # Silently return None for missing models
        return None
    
    if len(prices) < 60:
        # Silently return None for insufficient data
        return None
    
    try:
        model = MODELS[symbol][tf]
        scaler = SCALERS[symbol][tf]
        
        # Prepare data
        data = scaler.transform(np.array(prices).reshape(-1, 1))
        X = np.array([data[-60:].flatten()])
        
        # Make prediction
        pred = model.predict(X)
        return float(scaler.inverse_transform([[pred[0]]])[0][0])
    except Exception as e:
        # Silently return None for prediction errors
        return None
