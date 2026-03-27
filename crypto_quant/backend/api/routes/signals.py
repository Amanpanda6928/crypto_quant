from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.signals_service import signals_service

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/")
async def get_latest_signals(db: Session = Depends(get_db)):
    """
    Get latest trading signals with caching + concurrency safety.
    """

    try:
        return await signals_service.get_signals(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")
