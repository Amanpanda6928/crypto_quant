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
from app.api import auth, trading, signals, live, admin, bot, analytics, strategies10

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

@app.get("/")
async def root():
    return {"message": "Crypto Quant Trading System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
