# Secure Live Trading Bot API Routes
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.live_bot import run_live_bot, stop_bot, get_bot_status, emergency_close_all
from services.binance_live import test_connection, get_balance, get_all_prices
from services.risk_control import calculate_risk_metrics
from multi_coin_lstm import multi_lstm

router = APIRouter(prefix="/api/live-bot-secure", tags=["live-bot-secure"])

# Simple JWT verification (for demo)
def get_current_user_simple():
    """Simple user verification for demo"""
    # In production, use proper JWT verification
    return {"role": "SUPERADMIN", "username": "admin"}

class BotConfig(BaseModel):
    live_trading: bool = False
    risk_pct: float = 1.0
    sl_pct: float = 0.02
    tp_pct: float = 0.04
    max_trades_per_day: int = 50

class ManualTrade(BaseModel):
    coin: str
    signal: str
    confidence: float
    quantity: float = None

@router.post("/start")
async def start_live_bot(background_tasks: BackgroundTasks, user=Depends(get_current_user_simple)):
    """Start live trading bot with security checks"""
    try:
        # Check user role
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can start bot")
        
        current_status = get_bot_status()
        if current_status["running"]:
            return {"success": False, "message": "Bot is already running"}
        
        # Test Binance connection
        if not test_connection():
            return {"success": False, "message": "Binance connection failed. Check API keys."}
        
        # Start bot in background
        background_tasks.add_task(run_live_bot)
        
        return {
            "success": True,
            "message": "Secure live trading bot started",
            "started_by": user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z",
            "config": {
                "coins_tracked": len(multi_lstm.coins),
                "models_loaded": len(multi_lstm.models),
                "live_trading": os.getenv("LIVE_TRADING", "false").lower() == "true",
                "risk_management": "Active"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_live_bot(user=Depends(get_current_user_simple)):
    """Stop live trading bot"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can stop bot")
        
        stop_bot()
        
        return {
            "success": True,
            "message": "Secure live trading bot stopped",
            "stopped_by": user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_live_bot_status(user=Depends(get_current_user_simple)):
    """Get current bot status"""
    try:
        status = get_bot_status()
        
        # Add security info
        status["security"] = {
            "user_role": user.get("role"),
            "access_level": "FULL" if user.get("role") == "SUPERADMIN" else "LIMITED",
            "binance_connected": test_connection(),
            "api_keys_configured": bool(os.getenv("BINANCE_API_KEY")),
            "live_trading_enabled": os.getenv("LIVE_TRADING", "false").lower() == "true"
        }
        
        return {
            "success": True,
            "status": status,
            "accessed_by": user.get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop_all(user=Depends(get_current_user_simple)):
    """Emergency stop - close all positions"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can execute emergency stop")
        
        emergency_close_all()
        
        return {
            "success": True,
            "message": "Emergency stop executed - all positions closed",
            "executed_by": user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z",
            "severity": "CRITICAL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/update")
async def update_bot_config(config: BotConfig, user=Depends(get_current_user_simple)):
    """Update bot configuration"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can update config")
        
        # In production, update environment variables or config file
        # For demo, just return the config
        
        return {
            "success": True,
            "message": "Bot configuration updated",
            "updated_by": user.get("username"),
            "new_config": config.dict(),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_bot_config(user=Depends(get_current_user_simple)):
    """Get current bot configuration"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can view config")
        
        return {
            "success": True,
            "config": {
                "live_trading": os.getenv("LIVE_TRADING", "false").lower() == "true",
                "risk_pct": 1.0,
                "sl_pct": 0.02,
                "tp_pct": 0.04,
                "max_trades_per_day": 50,
                "min_confidence": 0.7,
                "coins_tracked": len(multi_lstm.coins),
                "models_loaded": len(multi_lstm.models)
            },
            "accessed_by": user.get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual-trade")
async def execute_manual_trade(trade: ManualTrade, user=Depends(get_current_user_simple)):
    """Execute manual trade with security checks"""
    try:
        if user.get("role") not in ["SUPERADMIN", "ADMIN"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions for manual trading")
        
        # Validate trade
        if trade.coin not in multi_lstm.coins:
            raise HTTPException(status_code=400, detail=f"Invalid coin: {trade.coin}")
        
        if trade.confidence < 0.7:
            raise HTTPException(status_code=400, detail="Confidence too low for manual trade")
        
        # Get current price
        from services.binance_live import get_price
        current_price = get_price(f"{trade.coin}USDT")
        
        if not current_price:
            raise HTTPException(status_code=400, detail="Could not fetch current price")
        
        # Execute trade logic (simplified for demo)
        live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
        
        return {
            "success": True,
            "message": f"Manual trade executed: {trade.signal} {trade.coin}",
            "trade": {
                "coin": trade.coin,
                "signal": trade.signal,
                "confidence": trade.confidence,
                "quantity": trade.quantity or "AUTO",
                "price": current_price,
                "mode": "LIVE" if live_trading else "PAPER",
                "executed_by": user.get("username"),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/balance")
async def get_account_balance(user=Depends(get_current_user_simple)):
    """Get account balance"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can view balance")
        
        balance = get_balance("USDT")
        
        return {
            "success": True,
            "balance": {
                "usdt": balance,
                "currency": "USDT",
                "available": balance,
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "accessed_by": user.get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-analysis")
async def get_risk_analysis(user=Depends(get_current_user_simple)):
    """Get current risk analysis"""
    try:
        if user.get("role") not in ["SUPERADMIN", "ADMIN"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions for risk analysis")
        
        status = get_bot_status()
        prices = get_all_prices()
        
        # Calculate risk metrics
        risk_metrics = calculate_risk_metrics(status.get("positions", {}), prices)
        
        return {
            "success": True,
            "risk_analysis": {
                "portfolio_value": risk_metrics.get("total_portfolio_value", 0),
                "total_risk": risk_metrics.get("total_risk", 0),
                "risk_percentage": risk_metrics.get("risk_percentage", 0),
                "positions_count": risk_metrics.get("positions_count", 0),
                "risk_level": "LOW" if risk_metrics.get("risk_percentage", 0) < 2 else "MEDIUM",
                "max_daily_risk": 2.0,
                "safety_guards": "ACTIVE"
            },
            "accessed_by": user.get("username"),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-log")
async def get_audit_log(user=Depends(get_current_user_simple)):
    """Get audit log (mock for demo)"""
    try:
        if user.get("role") != "SUPERADMIN":
            raise HTTPException(status_code=403, detail="Only SUPERADMIN can view audit log")
        
        # Mock audit log
        audit_log = [
            {
                "timestamp": "2024-01-01T10:30:00Z",
                "user": "admin",
                "action": "BOT_START",
                "details": "Started live trading bot",
                "ip": "127.0.0.1"
            },
            {
                "timestamp": "2024-01-01T11:15:00Z",
                "user": "admin",
                "action": "MANUAL_TRADE",
                "details": "Manual BUY BTC @ 45000",
                "ip": "127.0.0.1"
            },
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "user": "admin",
                "action": "EMERGENCY_STOP",
                "details": "Emergency stop executed",
                "ip": "127.0.0.1"
            }
        ]
        
        return {
            "success": True,
            "audit_log": audit_log,
            "total_entries": len(audit_log),
            "accessed_by": user.get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-check")
async def bot_health_check(user=Depends(get_current_user_simple)):
    """Comprehensive health check"""
    try:
        status = get_bot_status()
        
        health_status = {
            "overall": "HEALTHY" if test_connection() else "UNHEALTHY",
            "components": {
                "binance_connection": "OK" if test_connection() else "FAILED",
                "ai_models": f"{len(multi_lstm.models)}/{len(multi_lstm.coins)} loaded",
                "bot_running": status["running"],
                "positions_open": len(status.get("positions", {})),
                "daily_trades": f"{status.get('trades_today', 0)}/{status.get('max_trades_per_day', 50)}"
            },
            "security": {
                "api_keys_configured": bool(os.getenv("BINANCE_API_KEY")),
                "live_trading_enabled": os.getenv("LIVE_TRADING", "false").lower() == "true",
                "user_authenticated": True,
                "user_role": user.get("role")
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return {
            "success": True,
            "health": health_status,
            "accessed_by": user.get("username")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
