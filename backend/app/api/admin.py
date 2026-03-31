# =========================
# api/admin.py
# =========================
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.core.security import verify_token
from app.services.trading_engine import trading_engine
from app.services.trading_bot import trading_bot

router = APIRouter()

# Mock user database
users_db = [
    {"id": 1, "username": "admin", "role": "ADMIN", "email": "admin@example.com", "active": True},
    {"id": 2, "username": "user", "role": "USER", "email": "user@example.com", "active": True},
    {"id": 3, "username": "trader1", "role": "USER", "email": "trader1@example.com", "active": True},
    {"id": 4, "username": "superadmin", "role": "SUPERADMIN", "email": "super@example.com", "active": True}
]

def require_admin(token: str):
    """Verify admin access"""
    payload = verify_token(token)
    if not payload or payload.get("role") not in ["ADMIN", "SUPERADMIN"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

@router.get("/users")
async def get_users(token: str = None):
    """Get all users (admin only)"""
    require_admin(token)
    return {"users": users_db}

@router.get("/users/{user_id}")
async def get_user(user_id: int, token: str = None):
    """Get specific user (admin only)"""
    require_admin(token)
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/system/status")
async def get_system_status(token: str = None):
    """Get system status (admin only)"""
    require_admin(token)
    
    try:
        portfolio = trading_engine.get_portfolio_summary()
        bot_status = trading_bot.get_status()
        
        return {
            "system": "healthy",
            "uptime": "72h 15m 30s",
            "version": "1.0.0",
            "portfolio": portfolio,
            "trading_bot": bot_status,
            "active_users": len([u for u in users_db if u["active"]]),
            "total_users": len(users_db)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/metrics")
async def get_system_metrics(token: str = None):
    """Get detailed system metrics (admin only)"""
    require_admin(token)
    
    try:
        portfolio = trading_engine.get_portfolio_summary()
        bot_performance = trading_bot.get_performance_metrics()
        
        return {
            "trading_metrics": {
                "total_trades": portfolio["total_trades"],
                "current_balance": portfolio["balance"],
                "total_equity": portfolio["equity"],
                "open_positions": len(portfolio["positions"])
            },
            "bot_metrics": bot_performance,
            "user_metrics": {
                "total_users": len(users_db),
                "active_users": len([u for u in users_db if u["active"]]),
                "admin_users": len([u for u in users_db if u["role"] == "ADMIN"]),
                "regular_users": len([u for u in users_db if u["role"] == "USER"])
            },
            "system_health": {
                "cpu_usage": "45%",
                "memory_usage": "62%",
                "disk_usage": "38%",
                "network_status": "healthy"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades/all")
async def get_all_trades(token: str = None, limit: int = 100):
    """Get all trades from all users (admin only)"""
    require_admin(token)
    
    try:
        trades = trading_engine.get_trade_history(limit)
        return {"trades": trades, "total": len(trades)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/logs")
async def get_audit_logs(token: str = None, limit: int = 50):
    """Get audit logs (admin only)"""
    require_admin(token)
    
    try:
        # Mock audit logs
        import random
        from datetime import datetime, timedelta
        
        logs = []
        actions = ["LOGIN", "TRADE", "WITHDRAW", "DEPOSIT", "SETTINGS_CHANGE", "API_CALL"]
        
        for i in range(limit):
            log_time = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
            logs.append({
                "id": i + 1,
                "user_id": random.choice([1, 2, 3, 4]),
                "username": random.choice(["admin", "user", "trader1", "superadmin"]),
                "action": random.choice(actions),
                "details": f"User performed {random.choice(actions)} action",
                "ip_address": f"192.168.1.{random.randint(1, 255)}",
                "timestamp": log_time.isoformat()
            })
        
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/toggle")
async def toggle_user_status(user_id: int, token: str = None):
    """Toggle user active status (admin only)"""
    require_admin(token)
    
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["active"] = not user["active"]
    return {
        "user_id": user_id,
        "username": user["username"],
        "active": user["active"],
        "message": f"User {'activated' if user['active'] else 'deactivated'}"
    }

@router.get("/performance/summary")
async def get_performance_summary(token: str = None):
    """Get overall performance summary (admin only)"""
    require_admin(token)
    
    try:
        portfolio = trading_engine.get_portfolio_summary()
        bot_metrics = trading_bot.get_performance_metrics()
        
        return {
            "summary": {
                "total_balance": portfolio["balance"],
                "total_equity": portfolio["equity"],
                "total_trades": portfolio["total_trades"],
                "bot_win_rate": bot_metrics.get("win_rate", 0),
                "daily_trades": bot_metrics.get("daily_trades", 0),
                "system_uptime": "72h 15m 30s",
                "active_positions": len(portfolio["positions"])
            },
            "status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_system_alerts(token: str = None):
    """Get system alerts (admin only)"""
    require_admin(token)
    
    alerts = [
        {
            "id": 1,
            "type": "warning",
            "message": "High CPU usage detected",
            "timestamp": "2024-01-01T10:30:00Z",
            "resolved": False
        },
        {
            "id": 2,
            "type": "info",
            "message": "Bot completed 50 trades today",
            "timestamp": "2024-01-01T09:15:00Z",
            "resolved": True
        },
        {
            "id": 3,
            "type": "error",
            "message": "Failed connection to Binance API",
            "timestamp": "2024-01-01T08:45:00Z",
            "resolved": True
        }
    ]
    
    return {"alerts": alerts, "unresolved": len([a for a in alerts if not a["resolved"]])}
