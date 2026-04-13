"""
Live Predictions API
Real-time AI predictions for 17 coins across 4 timeframes
Auto-updates every 30 minutes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.live_prediction_service import get_live_service, start_live_service, COINS, TIMEFRAMES

router = APIRouter()

# Start service on module load
live_service = start_live_service()

class PredictionResponse(BaseModel):
    coin: str
    signal: str
    confidence: float
    confidence_display: str
    current_price: float
    predicted_price: float
    price_change: float
    price_change_display: str
    direction: str
    timeframe: str
    generated_at: str
    # Backtesting metrics
    backtest_strategy: Optional[str] = None
    backtest_return_pct: Optional[float] = None
    backtest_sharpe: Optional[float] = None
    backtest_sortino: Optional[float] = None
    backtest_max_dd_pct: Optional[float] = None
    backtest_win_rate_pct: Optional[float] = None
    backtest_trades: Optional[int] = None
    backtest_profit_factor: Optional[float] = None

class CoinPredictionsResponse(BaseModel):
    coin: str
    predictions: dict
    status: str

@router.get("/status")
async def get_live_status():
    """Get live prediction service status"""
    return live_service.get_status()

@router.get("/all")
async def get_all_live_predictions():
    """Get all predictions for all coins and timeframes"""
    try:
        # Auto-generate if no predictions exist
        predictions = live_service.get_all_predictions()
        if not predictions:
            print(" No predictions found, generating...")
            live_service.generate_all_predictions()
            predictions = live_service.get_all_predictions()
        
        # Format for frontend
        result = {}
        for coin, timeframes in predictions.items():
            result[coin] = {
                "coin": coin,
                "predictions": timeframes,
                "summary": timeframes.get("1h", {})
            }
            
        return {
            "predictions": result,
            "count": len(result),
            "coins_tracked": len(COINS),
            "timeframes": TIMEFRAMES,
            "total_predictions": len(live_service.predictions) * 5 if live_service.predictions else 0,
            "last_updated": live_service.last_update.isoformat() if live_service.last_update else None,
            "next_update": live_service.next_update.isoformat() if live_service.next_update else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coin/{coin}")
async def get_coin_predictions(coin: str):
    """Get all timeframe predictions for a specific coin with backtesting metrics"""
    try:
        predictions = live_service.get_predictions_for_coin(coin)
        
        if not predictions:
            raise HTTPException(status_code=404, detail=f"No predictions found for {coin}")
            
        # Get 1h as primary
        primary = predictions.get("1h", {})
        
        return {
            "coin": coin.upper(),
            "predictions": predictions,
            "primary": primary,
            "signal": primary.get("signal", "HOLD"),
            "confidence": primary.get("confidence", 0),
            "confidence_display": primary.get("confidence_display", "0%"),
            "price_change": primary.get("price_change", 0),
            "price_change_display": primary.get("price_change_display", "0.00%"),
            # Backtesting metrics from primary timeframe
            "backtest_strategy": primary.get("backtest_strategy"),
            "backtest_return_pct": primary.get("backtest_return_pct"),
            "backtest_sharpe": primary.get("backtest_sharpe"),
            "backtest_sortino": primary.get("backtest_sortino"),
            "backtest_max_dd_pct": primary.get("backtest_max_dd_pct"),
            "backtest_win_rate_pct": primary.get("backtest_win_rate_pct"),
            "backtest_trades": primary.get("backtest_trades"),
            "backtest_profit_factor": primary.get("backtest_profit_factor")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeframe/{timeframe}")
async def get_timeframe_predictions(timeframe: str):
    """Get predictions for all coins in a specific timeframe"""
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Use: {TIMEFRAMES}")
    
    try:
        all_preds = live_service.get_all_predictions()
        timeframe_preds = []
        
        for coin, preds in all_preds.items():
            if timeframe in preds:
                timeframe_preds.append(preds[timeframe])
                
        return {
            "timeframe": timeframe,
            "predictions": timeframe_preds,
            "count": len(timeframe_preds)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_predictions(background_tasks: BackgroundTasks):
    """Force refresh all predictions"""
    try:
        predictions = live_service.generate_all_predictions()
        
        # Get summary for response
        buy_count = sum(1 for p in predictions if p["signal"] == "BUY")
        sell_count = sum(1 for p in predictions if p["signal"] == "SELL")
        
        return {
            "success": True,
            "message": f"Generated {len(predictions)} predictions",
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "count": len(predictions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-signals")
async def get_top_signals(min_confidence: float = 60, limit: int = 10):
    """Get top BUY/SELL signals sorted by confidence"""
    try:
        all_preds = live_service.get_all_predictions()
        signals = []
        
        for coin, preds in all_preds.items():
            # Use 1h timeframe as primary
            if "1h" in preds:
                p = preds["1h"]
                if p["confidence"] >= min_confidence and p["signal"] in ["BUY", "SELL"]:
                    signals.append(p)
                    
        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "signals": signals[:limit],
            "count": len(signals[:limit]),
            "min_confidence": min_confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{coin}")
async def get_coin_backtest(coin: str, timeframe: str = "1h", days: int = 14):
    """Get hedge fund backtesting metrics for a specific coin"""
    try:
        metrics = live_service.run_backtest_for_coin(coin.upper(), timeframe, days)
        return {
            "coin": coin.upper(),
            "timeframe": timeframe,
            "days": days,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
