"""
Crypto Quant Trading System - FastAPI Backend
Features: JWT Auth, AI Predictions, Live Trading, Backtesting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, trading, signals, live, admin, bot, analytics, strategies10, export, import_data, predictions, live_predictions
# from app.api import finnhub_predictions  # DISABLED - using live_predictions instead

# Import and start scheduler
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
    from scheduler import start_scheduler_in_background
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ Scheduler not available, skipping...")

# Import live prediction service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.services.live_prediction import start_live_prediction_service

app = FastAPI(
    title="Crypto Quant Trading System",
    description="Advanced cryptocurrency trading system with AI-powered signals",
    version="1.0.0"
)

# CORS - Allow all for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(live.router, prefix="/api/live", tags=["live"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(strategies10.router, tags=["strategies"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(import_data.router, prefix="/api/import", tags=["import"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(live_predictions.router, prefix="/api/live-predictions", tags=["live-predictions"])
# app.include_router(finnhub_predictions.router, prefix="/api/finnhub", tags=["finnhub-predictions"])  # DISABLED

@app.on_event("startup")
async def startup_event():
    """Start scheduler, live prediction service, and auto-update on app startup"""
    # Start scheduler only if available
    if SCHEDULER_AVAILABLE:
        start_scheduler_in_background()
    
    # Start live prediction service
    start_live_prediction_service()
    
    # Start auto-update service - updates prices every 5 minutes
    try:
        from auto_update import start_auto_update
        start_auto_update(interval_minutes=5)
        print("🔄 Auto-update started: Prices refresh every 5 minutes")
    except Exception as e:
        print(f"⚠️  Auto-update failed to start: {e}")

@app.get("/")
async def root():
    return {"message": "Crypto Quant Trading System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
