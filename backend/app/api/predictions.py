# =========================
# api/predictions.py - Live Prediction API Endpoints
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import json
import time

from app.services.live_prediction import (
    live_prediction_service, 
    get_live_prediction, 
    get_all_live_predictions,
    COINS,
    TIMEFRAMES
)
from app.services.binance_client import binance_client

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        
    async def broadcast(self, message: dict):
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(client_id)
                
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
            
    async def send_to(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                self.disconnect(client_id)

manager = ConnectionManager()


class PredictionResponse(BaseModel):
    coin: str
    signal: str
    confidence: float
    price: Optional[float]
    predicted_price: Optional[float]
    price_change: Optional[float]
    timestamp: str


@router.get("/live/{coin}")
async def get_live_coin_prediction(coin: str):
    """
    Get live AI prediction for a specific coin using LSTM model
    
    - **coin**: Cryptocurrency symbol (BTC, ETH, etc.)
    - Returns: Signal (BUY/SELL/HOLD), confidence, current price, predicted price
    """
    try:
        prediction = get_live_prediction(coin)
        
        # Add timestamp if not present
        if "timestamp" not in prediction:
            prediction["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
        return prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/live")
async def get_all_live_predictions_endpoint():
    """
    Get live AI predictions for all supported coins
    
    Returns: Dictionary of all coin predictions with signals and confidence levels
    """
    try:
        predictions = get_all_live_predictions()
        
        return {
            "predictions": predictions,
            "count": len(predictions),
            "supported_coins": COINS,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/top-signals")
async def get_top_signals(
    min_confidence: float = 0.6, 
    top_n: int = 10,
    signal_type: Optional[str] = None
):
    """
    Get top trading signals sorted by confidence
    
    - **min_confidence**: Minimum confidence threshold (0.0-1.0), default 0.6
    - **top_n**: Number of top signals to return, default 10
    - **signal_type**: Filter by signal type (BUY, SELL, HOLD)
    """
    try:
        signals = live_prediction_service.get_top_signals(
            min_confidence=min_confidence, 
            top_n=top_n * 2  # Get extra to filter by type
        )
        
        # Filter by signal type if specified
        if signal_type and signal_type.upper() in ["BUY", "SELL", "HOLD"]:
            signals = [s for s in signals if s.get("signal") == signal_type.upper()]
            
        return {
            "signals": signals[:top_n],
            "count": len(signals[:top_n]),
            "filters": {
                "min_confidence": min_confidence,
                "signal_type": signal_type
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal error: {str(e)}")


@router.get("/detailed/{coin}")
async def get_detailed_prediction(coin: str):
    """
    Get detailed prediction with market data and technical analysis
    
    - **coin**: Cryptocurrency symbol
    - Returns: Full analysis including LSTM prediction, technical indicators, market data
    """
    try:
        coin = coin.upper().replace("USDT", "")
        
        # Get LSTM prediction
        lstm_pred = get_live_prediction(coin)
        
        # Get market data from Binance
        symbol = f"{coin}USDT"
        
        # Fetch klines for technical analysis
        klines = binance_client.get_klines(symbol, "1h", 50)
        
        if not klines:
            raise HTTPException(status_code=500, detail="Failed to fetch market data")
            
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        
        current_price = closes[-1]
        
        # Technical analysis
        sma_7 = sum(closes[-7:]) / 7 if len(closes) >= 7 else current_price
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sma_7
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
        
        # RSI calculation
        gains = [closes[i] - closes[i-1] for i in range(1, len(closes)) if closes[i] > closes[i-1]]
        losses = [closes[i-1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i-1]]
        avg_gain = sum(gains[-14:]) / 14 if gains else 0
        avg_loss = sum(losses[-14:]) / 14 if losses else 0.001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Price momentum
        momentum_1h = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
        
        # Determine trend
        if sma_7 > sma_20 * 1.005:
            trend = "BULLISH"
        elif sma_7 < sma_20 * 0.995:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
            
        # Combine LSTM prediction with technical analysis
        lstm_signal = lstm_pred.get("signal", "HOLD")
        lstm_confidence = lstm_pred.get("confidence", 0.5)
        
        # Final signal based on both LSTM and technical
        if lstm_signal in ["STRONG_BUY", "BUY"] and trend == "BULLISH":
            final_signal = "BUY"
            final_confidence = min(0.95, lstm_confidence + 0.1)
        elif lstm_signal in ["STRONG_SELL", "SELL"] and trend == "BEARISH":
            final_signal = "SELL"
            final_confidence = min(0.95, lstm_confidence + 0.1)
        else:
            final_signal = "HOLD"
            final_confidence = lstm_confidence
            
        return {
            "coin": coin,
            "current_price": round(current_price, 2),
            "prediction": {
                "signal": final_signal,
                "confidence": round(final_confidence, 3),
                "lstm_signal": lstm_signal,
                "lstm_confidence": lstm_confidence,
                "predicted_price": lstm_pred.get("predicted_price"),
                "price_change_percent": lstm_pred.get("price_change")
            },
            "technical_analysis": {
                "trend": trend,
                "rsi": round(rsi, 1),
                "sma_7": round(sma_7, 2),
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "momentum_1h": round(momentum_1h, 2)
            },
            "market_data": {
                "high_24h": round(max(highs[-24:]), 2) if len(highs) >= 24 else round(max(highs), 2),
                "low_24h": round(min(lows[-24:]), 2) if len(lows) >= 24 else round(min(lows), 2),
                "volume_24h": round(sum(volumes[-24:]), 2) if len(volumes) >= 24 else round(sum(volumes), 2),
                "price_change_24h": round((closes[-1] - closes[0]) / closes[0] * 100, 2) if closes else 0
            },
            "reasoning": lstm_pred.get("reason", "Technical analysis combined with LSTM prediction"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detailed prediction error: {str(e)}")


@router.get("/history/{coin}")
async def get_prediction_history(coin: str, hours: int = 24):
    """
    Get historical price data and prediction history for a coin
    
    - **coin**: Cryptocurrency symbol
    - **hours**: Number of hours of history to retrieve
    """
    try:
        coin = coin.upper().replace("USDT", "")
        symbol = f"{coin}USDT"
        
        # Get price history from service
        price_history = live_prediction_service.get_price_history(coin, limit=hours)
        
        # Get klines from Binance
        klines = binance_client.get_klines(symbol, "1h", hours)
        
        return {
            "coin": coin,
            "price_history": price_history,
            "klines": klines,
            "hours": hours,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


# WebSocket endpoint for real-time predictions
@router.websocket("/ws/predictions")
async def websocket_predictions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time prediction streaming
    
    Connect to ws://<host>/api/predictions/ws/predictions
    Receives real-time updates every 30 seconds
    """
    client_id = f"ws_{id(websocket)}"
    await manager.connect(websocket, client_id)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected to live predictions",
            "supported_coins": COINS,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        # Send current predictions
        predictions = get_all_live_predictions()
        await websocket.send_json({
            "type": "predictions",
            "data": predictions,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        
        # Keep connection alive and send updates
        while True:
            try:
                # Wait for message from client (optional)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client commands
                try:
                    msg = json.loads(data)
                    command = msg.get("command")
                    
                    if command == "subscribe":
                        coin = msg.get("coin", "ALL")
                        await websocket.send_json({
                            "type": "subscribed",
                            "coin": coin,
                            "message": f"Subscribed to {coin} predictions"
                        })
                        
                    elif command == "get_prediction":
                        coin = msg.get("coin")
                        if coin:
                            pred = get_live_prediction(coin)
                            await websocket.send_json({
                                "type": "prediction",
                                "coin": coin,
                                "data": pred
                            })
                            
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send heartbeat/update every 30 seconds
                predictions = get_all_live_predictions()
                await websocket.send_json({
                    "type": "update",
                    "data": predictions,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
        print(f"WebSocket error: {e}")


@router.post("/train/{coin}")
async def train_coin_model(coin: str):
    """
    Manually trigger model training for a specific coin
    
    - **coin**: Cryptocurrency symbol to train
    """
    try:
        coin = coin.upper().replace("USDT", "")
        
        if coin not in COINS:
            raise HTTPException(status_code=400, detail=f"Unsupported coin: {coin}")
            
        # Get price history
        price_history = live_prediction_service.get_price_history(coin, limit=100)
        
        if len(price_history) < 50:
            # Fetch from Binance if not enough history
            symbol = f"{coin}USDT"
            klines = binance_client.get_klines(symbol, "1h", 100)
            
            if klines and len(klines) >= 50:
                price_history = [k["close"] for k in klines]
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient data for {coin}. Need at least 50 price points."
                )
                
        # Train model
        success = live_prediction_service.lstm.train_coin_model(coin, price_history)
        
        if success:
            return {
                "success": True,
                "coin": coin,
                "message": f"Model trained successfully for {coin}",
                "training_samples": len(price_history),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        else:
            raise HTTPException(status_code=500, detail="Model training failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@router.get("/status")
async def get_prediction_service_status():
    """
    Get live prediction service status
    """
    return {
        "service": "live_prediction",
        "running": live_prediction_service.running,
        "supported_coins": COINS,
        "supported_timeframes": TIMEFRAMES,
        "cached_predictions": len(live_prediction_service.prediction_cache),
        "subscribers": len(manager.active_connections),
        "models_loaded": list(live_prediction_service.lstm.models.keys()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
