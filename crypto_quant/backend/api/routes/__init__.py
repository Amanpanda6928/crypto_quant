"""API routes package"""

from fastapi import APIRouter

from .signals import router as signals_router
from .market import router as market_router
from .performance import router as performance_router
from .orderbook import router as orderbook_router
from .train import router as train_router

router = APIRouter()
router.include_router(signals_router)
router.include_router(market_router)
router.include_router(performance_router)
router.include_router(orderbook_router)
router.include_router(train_router)
