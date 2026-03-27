"""
Pydantic Models for FastAPI Backend
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class PredictionResponse(BaseModel):
    """Prediction response model"""
    symbol: str
    horizon: str
    probability: float
    confidence: float
    timestamp: datetime

class SignalResponse(BaseModel):
    """Signal response model"""
    symbol: str
    signal: str
    confidence: float
    timestamp: datetime

class PortfolioResponse(BaseModel):
    """Portfolio response model"""
    total_value: float
    positions: Dict[str, Dict]
    cash: float
    timestamp: datetime

class TradeRequest(BaseModel):
    """Trade request model"""
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    price: Optional[float] = None

class TradeResponse(BaseModel):
    """Trade response model"""
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: datetime