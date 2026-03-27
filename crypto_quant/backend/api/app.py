"""
FastAPI Backend for Crypto Quant Trading System
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
from datetime import datetime

from ..live.orderbook import OrderBookStream
from ..utils.config import get_config
from ..utils.logger import get_logger
from .database import init_db
from .background import start_signal_updater
from .routes import router as api_router
from .websocket.manager import ConnectionManager

manager = ConnectionManager()
orderbook_stream = OrderBookStream()

app = FastAPI(
    title="Crypto Quant API",
    description="Real-time cryptocurrency trading system API",
    version="1.0.0"
)

# Register modular API routes
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger()
config = get_config()

@app.on_event("startup")
async def _startup() -> None:
    init_db()
    # Auto-refresh predictions in background (keeps /signals updated).
    await start_signal_updater(interval_seconds=60)

@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Crypto Quant Trading API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.websocket("/ws/orderbook")
async def websocket_orderbook(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            symbol = message.get("symbol")
            if not symbol:
                await websocket.send_json({"error": "symbol is required"})
                continue

            snapshot = orderbook_stream.get_snapshot(symbol.upper())
            await websocket.send_json({
                "symbol": symbol.upper(),
                "orderbook": snapshot,
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)