from fastapi import APIRouter, HTTPException
from datetime import datetime

from ...live.live_system import LiveSystem
from ...utils.logger import get_logger

router = APIRouter(prefix="/orderbook", tags=["orderbook"])
logger = get_logger()


@router.get("/{symbol}")
async def get_orderbook(symbol: str):
    """Get current order book snapshot for a symbol."""
    try:
        system = LiveSystem()
        snapshot = system.orderbook.get_snapshot(symbol.upper())
        if not snapshot:
            raise HTTPException(status_code=404, detail="Order book data not found")

        return {
            "symbol": symbol.upper(),
            "snapshot": snapshot,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Orderbook error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{symbol}/history")
async def get_orderbook_history(symbol: str, limit: int = 25):
    """Get recent order book history for symbol."""
    try:
        system = LiveSystem()
        history = system.orderbook.get_history(symbol.upper(), limit=limit)
        if history is None:
            raise HTTPException(status_code=404, detail="Order book history not found")

        return {
            "symbol": symbol.upper(),
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Orderbook history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
