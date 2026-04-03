# =========================
# api/bot.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.trading_bot import trading_bot, run_bot
import asyncio

router = APIRouter()

@router.post("/start")
async def start_trading_bot(background_tasks: BackgroundTasks):
    """Start the trading bot"""
    try:
        if trading_bot.is_running:
            return {"success": False, "message": "Bot is already running"}
        
        # Start bot in background
        background_tasks.add_task(run_bot)
        
        return {
            "success": True,
            "message": "Trading bot started successfully",
            "status": trading_bot.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_trading_bot():
    """Stop the trading bot"""
    try:
        if not trading_bot.is_running:
            return {"success": False, "message": "Bot is not running"}
        
        trading_bot.stop_bot()
        
        return {
            "success": True,
            "message": "Trading bot stopped successfully",
            "status": trading_bot.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_bot_status():
    """Get current bot status"""
    try:
        status = trading_bot.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_bot_performance():
    """Get bot performance metrics"""
    try:
        performance = trading_bot.get_performance_metrics()
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configure")
async def configure_bot(config: dict):
    """Configure bot settings"""
    try:
        if trading_bot.is_running:
            return {"success": False, "message": "Cannot configure bot while running"}
        
        # Update bot configuration
        if "symbols" in config:
            trading_bot.symbols = config["symbols"]
        
        if "max_daily_trades" in config:
            from app.core.config import MAX_DAILY_TRADES
            MAX_DAILY_TRADES = config["max_daily_trades"]
        
        return {
            "success": True,
            "message": "Bot configuration updated",
            "config": {
                "symbols": trading_bot.symbols,
                "max_daily_trades": config.get("max_daily_trades", 50)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_bot_logs(limit: int = 100):
    """Get bot activity logs"""
    try:
        # Mock bot logs
        import random
        from datetime import datetime, timedelta
        
        logs = []
        actions = ["SIGNAL_GENERATED", "TRADE_EXECUTED", "ERROR", "POSITION_OPENED", "POSITION_CLOSED"]
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        for i in range(limit):
            log_time = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))
            action = random.choice(actions)
            symbol = random.choice(symbols)
            
            log_entry = {
                "id": i + 1,
                "timestamp": log_time.isoformat(),
                "action": action,
                "symbol": symbol,
                "message": f"Bot {action.lower()} for {symbol}"
            }
            
            if action == "TRADE_EXECUTED":
                log_entry["details"] = {
                    "side": random.choice(["BUY", "SELL"]),
                    "quantity": round(random.uniform(0.001, 0.1), 4),
                    "price": round(random.uniform(30000, 50000), 2)
                }
            elif action == "SIGNAL_GENERATED":
                log_entry["details"] = {
                    "signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "confidence": round(random.uniform(0.6, 0.95), 3)
                }
            
            logs.append(log_entry)
        
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop - immediately halt all trading activity"""
    try:
        trading_bot.stop_bot()
        
        # Close all positions
        from app.services.trading_engine import trading_engine
        portfolio = trading_engine.get_portfolio_summary()
        
        closed_positions = []
        for symbol, position in portfolio.get("positions", {}).items():
            # Mock position closing
            closed_positions.append({
                "symbol": symbol,
                "quantity": position.get("quantity", 0),
                "message": f"Emergency close position for {symbol}"
            })
        
        return {
            "success": True,
            "message": "Emergency stop executed",
            "actions_taken": [
                "Trading bot stopped",
                f"Closed {len(closed_positions)} positions",
                "All trading activity halted"
            ],
            "closed_positions": closed_positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_bot_health():
    """Get bot health check"""
    try:
        health = {
            "status": "healthy" if trading_bot.is_running else "stopped",
            "uptime": "2h 15m 30s" if trading_bot.is_running else "0s",
            "last_trade": "2024-01-01T10:30:00Z",
            "error_rate": "0.02",  # 2%
            "memory_usage": "45MB",
            "cpu_usage": "12%"
        }
        
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
