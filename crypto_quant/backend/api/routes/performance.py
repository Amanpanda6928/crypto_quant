from fastapi import APIRouter, HTTPException
from ...core.performance_tracker import PerformanceTracker
from ...core.state_manager import StateManager
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/performance", tags=["performance"])

# Singletons
_tracker: PerformanceTracker | None = None
_state_manager: StateManager | None = None

# Cache
_cached_metrics = None
_last_updated: datetime | None = None

# Lock
_lock = asyncio.Lock()

CACHE_TTL = 15  # seconds


def get_tracker() -> PerformanceTracker:
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker


def get_state_manager() -> StateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


@router.get("/")
async def get_performance_metrics():
    """
    Get system performance metrics (cached + safe + structured)
    """

    global _cached_metrics, _last_updated

    async with _lock:
        try:
            now = datetime.utcnow()

            # ✅ Return cached metrics if fresh
            if (
                _cached_metrics is not None
                and _last_updated is not None
                and (now - _last_updated) < timedelta(seconds=CACHE_TTL)
            ):
                return {
                    "status": "cached",
                    "timestamp": _last_updated.isoformat(),
                    "metrics": _cached_metrics
                }

            # ⚡ Load signals (non-blocking)
            state_manager = get_state_manager()
            signals = await asyncio.to_thread(state_manager.get_signals)

            # ⚡ Compute metrics (non-blocking)
            tracker = get_tracker()
            metrics = await asyncio.to_thread(
                tracker.compute_metrics, signals
            )

            # Clean + structured output
            result = {
                "win_rate": metrics.get("win_rate", 0.0),
                "avg_pnl": metrics.get("avg_pnl", 0.0),
                "total_trades": metrics.get("total_trades", 0),
                "profitable_trades": metrics.get("profitable_trades", 0),
                "losing_trades": metrics.get("losing_trades", 0),
                "max_drawdown": metrics.get("max_drawdown", 0.0),
                "sharpe_ratio": metrics.get("sharpe_ratio", None)
            }

            # Save cache
            _cached_metrics = result
            _last_updated = now

            return {
                "status": "fresh",
                "timestamp": now.isoformat(),
                "metrics": result
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Performance calculation failed: {str(e)}"
            )
