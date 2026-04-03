# Live Trading Bot API Routes
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.live_bot import run_live_bot, stop_bot, get_bot_status, emergency_close_all
import os

router = APIRouter(prefix="/api/live-bot", tags=["live-bot"])

@router.post("/start")
async def start_live_bot(background_tasks: BackgroundTasks):
    """Start the live trading bot with 30 coins"""
    try:
        current_status = get_bot_status()
        if current_status["running"]:
            return {"success": False, "message": "Bot is already running"}
        
        # Start bot in background
        background_tasks.add_task(run_live_bot)
        
        return {
            "success": True,
            "message": "Live trading bot started",
            "status": {
                "coins_tracked": current_status["coins_tracked"],
                "live_trading": current_status["live_trading"],
                "max_trades_per_day": current_status["max_trades_per_day"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_live_bot():
    """Stop the live trading bot"""
    try:
        stop_bot()
        return {
            "success": True,
            "message": "Live trading bot stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_live_bot_status():
    """Get current bot status"""
    try:
        status = get_bot_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-close")
async def emergency_close_all_positions():
    """Emergency close all positions"""
    try:
        emergency_close_all()
        return {
            "success": True,
            "message": "All positions emergency closed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_bot_config():
    """Get bot configuration"""
    try:
        from multi_coin_lstm import multi_lstm
        
        return {
            "coins_tracked": multi_lstm.coins,
            "models_loaded": len(multi_lstm.models),
            "live_trading": os.getenv("LIVE_TRADING", "false").lower() == "true",
            "max_trades_per_day": 50,
            "max_trade_size_usdt": 1000,
            "min_confidence": 0.7,
            "update_interval_seconds": 30
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals")
async def get_current_signals():
    """Get current trading signals for all 30 coins"""
    try:
        from multi_coin_lstm import multi_lstm
        from services.binance_live import get_all_prices
        
        # Get current prices
        prices = get_all_prices()
        
        # Update models with current prices
        for coin, price in prices.items():
            if price:
                multi_lstm.update_coin_price(coin, price)
        
        # Get top 10 signals
        top_signals = multi_lstm.get_top_signals(10)
        
        # Add current prices to signals
        for signal in top_signals:
            signal["current_price"] = prices.get(signal["coin"])
        
        return {
            "success": True,
            "signals": top_signals,
            "total_coins": len(multi_lstm.coins),
            "models_loaded": len(multi_lstm.models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_current_positions():
    """Get current open positions"""
    try:
        status = get_bot_status()
        return {
            "success": True,
            "positions": status["positions"],
            "total_positions": len(status["positions"]),
            "total_invested": sum(pos.get("usdt_size", 0) for pos in status["positions"].values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_bot_performance():
    """Get bot performance metrics"""
    try:
        status = get_bot_status()
        from multi_coin_lstm import multi_lstm
        
        # Mock performance data (in real app, calculate from database)
        performance = {
            "today_trades": status["trades_today"],
            "max_daily_trades": status["max_trades_per_day"],
            "win_rate": 68.5,
            "total_pnl": 1250.75,
            "best_trade": 450.25,
            "worst_trade": -125.50,
            "average_trade": 25.02,
            "sharpe_ratio": 1.85,
            "models_accuracy": sum([0.9, 0.85, 0.92, 0.88, 0.91]) / len([0.9, 0.85, 0.92, 0.88, 0.91])
        }
        
        return {
            "success": True,
            "performance": performance,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
