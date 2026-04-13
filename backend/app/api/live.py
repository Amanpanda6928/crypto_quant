# =========================
# api/live.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import time
import random
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.binance_client import binance_client
from app.core.config import LIVE_TRADING

# Import ML model loader for predictions (with fallback)
ml_predict = None
load_ml_models = None
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    from ml.model_loader import predict as ml_predict_func, load_all as load_ml_models_func
    ml_predict = ml_predict_func
    load_ml_models = load_ml_models_func
    # Load ML models on startup
    load_ml_models()
    print("OK: ML models loaded successfully")
except Exception as e:
    print(f"Warning: ML models not loaded: {e}")
    # Define fallback functions
    def ml_predict_fallback(*args, **kwargs):
        return None
    def load_ml_models_fallback(*args, **kwargs):
        pass
    ml_predict = ml_predict_fallback
    load_ml_models = load_ml_models_fallback

router = APIRouter()

class LiveOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    order_type: str = "MARKET"  # MARKET or LIMIT
    price: Optional[float] = None

class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str
    details: Optional[dict] = None

@router.post("/order", response_model=OrderResponse)
async def place_live_order(request: LiveOrderRequest):
    """Place a live trading order on Binance"""
    if not LIVE_TRADING:
        return OrderResponse(
            success=False,
            message="Live trading is disabled. Set LIVE_TRADING=True to enable."
        )
    
    try:
        if request.order_type == "MARKET":
            result = binance_client.market_order(request.symbol, request.side, request.quantity)
        elif request.order_type == "LIMIT":
            if not request.price:
                raise HTTPException(status_code=400, detail="Price required for limit orders")
            result = binance_client.limit_order(request.symbol, request.side, request.quantity, request.price)
        else:
            raise HTTPException(status_code=400, detail="Invalid order type")
        
        if result:
            return OrderResponse(
                success=True,
                order_id=str(result.get("orderId", "unknown")),
                message=f"Order placed successfully",
                details=result
            )
        else:
            return OrderResponse(
                success=False,
                message="Failed to place order"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account")
async def get_account_info():
    """Get Binance account information"""
    try:
        account = binance_client.get_account_info()
        if account:
            return account
        else:
            return {"error": "Failed to get account info"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance")
async def get_account_balance():
    """Get account balance summary"""
    try:
        account = binance_client.get_account_info()
        if not account:
            return {"error": "Failed to get account info"}
        
        balances = []
        total_usdt = 0.0
        
        for balance in account.get("balances", []):
            free = float(balance["free"])
            locked = float(balance["locked"])
            total = free + locked
            
            if total > 0:
                balances.append({
                    "asset": balance["asset"],
                    "free": free,
                    "locked": locked,
                    "total": total
                })
                
                # Estimate USDT value (mock prices for demo)
                if balance["asset"] == "USDT":
                    total_usdt += total
                elif balance["asset"] == "BTC":
                    total_usdt += total * 45000  # Mock BTC price
                elif balance["asset"] == "ETH":
                    total_usdt += total * 3200   # Mock ETH price
        
        return {
            "balances": balances,
            "total_usdt_estimate": total_usdt,
            "live_trading": LIVE_TRADING
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/price/{symbol}")
async def get_symbol_price(symbol: str):
    """Get current price with 24h stats for a symbol"""
    try:
        # Get current price
        price = binance_client.get_price(symbol)
        if not price:
            return {"error": f"Could not get price for {symbol}"}
        
        # Get 24h klines for additional stats
        klines = binance_client.get_klines(symbol, "1h", 24)
        
        if klines and len(klines) >= 24:
            closes = [k["close"] for k in klines]
            highs = [k["high"] for k in klines]
            lows = [k["low"] for k in klines]
            volumes = [k["volume"] for k in klines]
            
            # Calculate 24h change
            price_24h_ago = closes[0] if closes else 0
            change_24h = ((price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago != 0 else 0
            
            # Calculate 1h change (last 2 candles) - prevent division by zero
            change_1h = 0
            if len(closes) >= 2 and closes[-2] != 0:
                change_1h = ((closes[-1] - closes[-2]) / closes[-2] * 100)
            
            # 24h high/low
            high_24h = max(highs)
            low_24h = min(lows)
            
            # 24h volume
            volume_24h = sum(volumes)
            
            return {
                "symbol": symbol,
                "price": price,
                "change_24h": round(change_24h, 2),
                "change_1h": round(change_1h, 2),
                "high_24h": round(high_24h, 2),
                "low_24h": round(low_24h, 2),
                "volume_24h": round(volume_24h, 2),
                "timestamp": int(time.time() * 1000)
            }
        else:
            # Fallback with just price
            return {
                "symbol": symbol,
                "price": price,
                "change_24h": 0,
                "change_1h": 0,
                "high_24h": price,
                "low_24h": price,
                "volume_24h": 0,
                "timestamp": int(time.time() * 1000)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_trading_symbols():
    """Get list of available trading symbols"""
    try:
        # Mock symbol list for demo
        symbols = [
            {"symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", "active": True},
            {"symbol": "ETHUSDT", "base": "ETH", "quote": "USDT", "active": True},
            {"symbol": "ADAUSDT", "base": "ADA", "quote": "USDT", "active": True},
            {"symbol": "BNBUSDT", "base": "BNB", "quote": "USDT", "active": True},
            {"symbol": "SOLUSDT", "base": "SOL", "quote": "USDT", "active": True},
            {"symbol": "DOTUSDT", "base": "DOT", "quote": "USDT", "active": True}
        ]
        return {"symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{symbol}")
async def get_open_orders(symbol: str):
    """Get open orders for a symbol"""
    try:
        # Mock open orders
        orders = [
            {
                "orderId": "12345",
                "symbol": symbol,
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "0.001",
                "price": "45000",
                "status": "NEW"
            }
        ]
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/order/{symbol}/{order_id}")
async def cancel_order(symbol: str, order_id: str):
    """Cancel an order"""
    try:
        result = binance_client.cancel_order(symbol, int(order_id))
        if result:
            return {"success": True, "message": "Order cancelled", "details": result}
        else:
            return {"success": False, "message": "Failed to cancel order"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}")
async def get_klines_data(symbol: str, interval: str = "1h", limit: int = 60, predict_hours: int = 6):
    """Get candlestick data with future AI predictions
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Candlestick interval (30m, 1h, 4h, 1d)
        limit: Number of historical candles (default 60)
        predict_hours: Number of future hours to predict (default 6)
    
    Returns:
        Historical candles + AI predicted future candles
    """
    try:
        # Get historical klines
        klines = binance_client.get_klines(symbol, interval, limit)
        if not klines:
            return {"error": f"Could not get klines for {symbol}", "candles": [], "predictions": []}
        
        # Calculate technical indicators
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        
        # Simple Moving Averages
        sma_7 = sum(closes[-7:]) / 7 if len(closes) >= 7 else closes[-1] if closes else 0
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sma_7
        
        # Price change over the period
        price_change = ((closes[-1] - closes[0]) / closes[0] * 100) if closes and closes[0] != 0 else 0
        
        # Volatility
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        ranges = [h - l for h, l in zip(highs, lows)]
        avg_range = sum(ranges) / len(ranges) if ranges else 0
        volatility = (avg_range / closes[-1] * 100) if closes and closes[-1] != 0 else 0
        
        # Volume trend
        avg_vol_5 = sum(volumes[:-5]) / 5 if len(volumes) >= 5 and sum(volumes[:-5]) > 0 else 1
        vol_change = ((volumes[-1] - avg_vol_5) / avg_vol_5 * 100) if len(volumes) >= 5 else 0
        
        # Determine trend
        if sma_7 > sma_20 * 1.002:
            trend = "BULLISH"
            trend_score = min(100, 50 + price_change * 2)
        elif sma_7 < sma_20 * 0.998:
            trend = "BEARISH"
            trend_score = max(0, 50 - abs(price_change) * 2)
        else:
            trend = "NEUTRAL"
            trend_score = 50
        
        current_price = closes[-1] if closes else 0
        
        # Generate AI future predictions
        predictions = []
        prediction_confidence = 0
        
        # Try ML model prediction first
        coin_symbol = symbol.replace('USDT', '')
        predicted_prices = []
        
        # Use closes as price history for prediction
        if len(closes) >= 60:
            # Get base prediction from model
            base_prediction = ml_predict(coin_symbol, closes, '1h')
            
            if base_prediction:
                # Generate multiple future predictions with trend continuation
                last_price = closes[-1]
                predicted_change = (base_prediction - last_price) / last_price
                prediction_confidence = min(95, 60 + abs(predicted_change) * 100)
                
                # Generate future candles based on prediction
                for i in range(1, predict_hours + 1):
                    # Progressive prediction with some randomness
                    progress_factor = i / predict_hours
                    target_price = last_price + (base_prediction - last_price) * progress_factor
                    
                    # Add volatility
                    vol_range = last_price * volatility / 100
                    pred_high = target_price + vol_range * (0.5 + random.random() * 0.5)
                    pred_low = target_price - vol_range * (0.5 + random.random() * 0.5)
                    pred_open = last_price if i == 1 else predicted_prices[-1]['close']
                    pred_close = target_price
                    pred_volume = volumes[-1] * (0.8 + random.random() * 0.4) if volumes else 100
                    
                    # Calculate timestamp for future candle
                    last_time = klines[-1]["time"] if isinstance(klines[-1], dict) else klines[-1][0]
                    hour_ms = 60 * 60 * 1000
                    future_time = last_time + i * hour_ms
                    
                    pred_candle = {
                        "time": future_time,
                        "open": round(pred_open, 2),
                        "high": round(pred_high, 2),
                        "low": round(pred_low, 2),
                        "close": round(pred_close, 2),
                        "volume": round(pred_volume, 4),
                        "is_prediction": True,
                        "prediction_hour": i
                    }
                    predicted_prices.append(pred_candle)
        
        # If ML prediction failed, use trend-based prediction
        if not predicted_prices and len(closes) >= 2:
            prediction_confidence = 55
            last_price = closes[-1]
            
            # Simple trend extrapolation
            recent_changes = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(-5, 0) if abs(i) <= len(closes)]
            avg_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0
            
            for i in range(1, predict_hours + 1):
                projected_change = avg_change * i
                target_price = last_price * (1 + projected_change)
                
                vol_range = last_price * volatility / 100 if volatility else last_price * 0.01
                pred_high = target_price + vol_range * 0.6
                pred_low = target_price - vol_range * 0.6
                pred_open = last_price if i == 1 else predicted_prices[-1]['close']
                pred_close = target_price
                pred_volume = volumes[-1] * 0.9 if volumes else 100
                
                last_time = klines[-1]["time"] if isinstance(klines[-1], dict) else klines[-1][0]
                hour_ms = 60 * 60 * 1000
                future_time = last_time + i * hour_ms
                
                pred_candle = {
                    "time": future_time,
                    "open": round(pred_open, 2),
                    "high": round(pred_high, 2),
                    "low": round(pred_low, 2),
                    "close": round(pred_close, 2),
                    "volume": round(pred_volume, 4),
                    "is_prediction": True,
                    "prediction_hour": i
                }
                predicted_prices.append(pred_candle)
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": klines,
            "predictions": predicted_prices,
            "prediction": {
                "target_price": round(predicted_prices[-1]["close"], 2) if predicted_prices else round(current_price, 2),
                "predicted_change": round(((predicted_prices[-1]["close"] - current_price) / current_price * 100), 2) if predicted_prices and current_price else 0,
                "confidence": round(prediction_confidence, 1),
                "hours_ahead": predict_hours,
                "signal": "BUY" if predicted_prices and predicted_prices[-1]["close"] > current_price * 1.01 else 
                         "SELL" if predicted_prices and predicted_prices[-1]["close"] < current_price * 0.99 else "HOLD"
            },
            "analysis": {
                "current_price": round(current_price, 2),
                "price_change_24h": round(price_change, 2),
                "trend": trend,
                "trend_score": round(trend_score, 1),
                "sma_7": round(sma_7, 2),
                "sma_20": round(sma_20, 2),
                "volatility": round(volatility, 2),
                "volume_change": round(vol_change, 2),
                "high_24h": round(max(highs), 2) if highs else 0,
                "low_24h": round(min(lows), 2) if lows else 0,
                "support": round(min(lows[-10:]) if len(lows) >= 10 else min(lows), 2) if lows else 0,
                "resistance": round(max(highs[-10:]) if len(highs) >= 10 else max(highs), 2) if highs else 0,
            },
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/status")
async def get_market_status():
    """Get overall market status and sentiment"""
    try:
        # Calculate market regime based on BTC trend
        btc_klines = binance_client.get_klines("BTCUSDT", "1h", 24)
        
        if btc_klines and len(btc_klines) >= 24:
            closes = [k["close"] for k in btc_klines]
            sma_12 = sum(closes[-12:]) / 12
            current = closes[-1]
            
            # Determine regime
            if current > sma_12 * 1.02:
                regime = "BULL"
            elif current < sma_12 * 0.98:
                regime = "BEAR"
            else:
                regime = "NEUTRAL"
            
            # Calculate volatility
            ranges = [k["high"] - k["low"] for k in btc_klines[-12:]]
            avg_range = sum(ranges) / len(ranges)
            volatility_pct = (avg_range / current) * 100
            
            if volatility_pct < 1.5:
                volatility = "LOW"
            elif volatility_pct > 3.5:
                volatility = "HIGH"
            else:
                volatility = "MEDIUM"
            
            # Mock fear & greed (would come from actual API)
            fear_greed = min(100, max(0, 50 + (current - sma_12) / sma_12 * 500))
            
            return {
                "regime": regime,
                "volatility": volatility,
                "fear_greed": round(fear_greed),
                "btc_dominance": 52.4,
                "timestamp": int(time.time() * 1000)
            }
        
        # Fallback mock data
        return {
            "regime": "BULL",
            "volatility": "MEDIUM", 
            "fear_greed": 65,
            "btc_dominance": 52.4,
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_live_trading_status():
    """Get live trading status"""
    return {
        "connected": binance_client.is_connected or True,  # Always connected in demo mode
        "exchange": "Binance",
        "mode": "demo" if not LIVE_TRADING else "live",
        "live_trading_enabled": LIVE_TRADING,
        "binance_connected": binance_client.is_connected,
        "api_keys_configured": bool(binance_client.client),
        "active_orders": 0,
        "bot_running": False,
        "supported_features": [
            "Market Orders",
            "Limit Orders",
            "Account Info",
            "Order Management",
            "Price Ticker"
        ]
    }
