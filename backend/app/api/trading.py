# =========================
# api/trading.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.trading_engine import trading_engine
from app.services.risk_manager import risk_manager

router = APIRouter()

class TradeRequest(BaseModel):
    symbol: str
    price: float
    quantity: float
    side: str  # BUY or SELL
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class PositionResponse(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float

@router.post("/execute")
async def execute_trade(request: TradeRequest):
    """Execute a trade with risk management"""
    try:
        result = trading_engine.execute_trade(
            symbol=request.symbol,
            price=request.price,
            quantity=request.quantity,
            side=request.side,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Trade failed"))
        
        return {
            "success": True,
            "message": f"Trade executed: {request.side} {request.quantity} {request.symbol}",
            "trade": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    try:
        portfolio = trading_engine.get_portfolio_summary()
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_positions():
    """Get open positions"""
    try:
        positions = trading_engine.positions
        return {"positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_trade_history(limit: int = 100):
    """Get trade history"""
    try:
        history = trading_engine.get_trade_history(limit)
        return {"trades": history, "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-position-size")
async def calculate_position_size(
    balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float
):
    """Calculate optimal position size"""
    try:
        size = risk_manager.calculate_position_size(
            balance, risk_percentage, entry_price, stop_loss
        )
        return {
            "position_size": size,
            "risk_amount": balance * (risk_percentage / 100),
            "max_loss": abs(entry_price - stop_loss) * size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-stop-loss")
async def calculate_stop_loss(entry_price: float, side: str, atr: Optional[float] = None):
    """Calculate stop loss price"""
    try:
        stop_loss = risk_manager.calculate_stop_loss(entry_price, side, atr)
        return {"stop_loss": stop_loss}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-take-profit")
async def calculate_take_profit(entry_price: float, side: str, risk_reward_ratio: float = 2.0):
    """Calculate take profit price"""
    try:
        take_profit = risk_manager.calculate_take_profit(entry_price, side, risk_reward_ratio)
        return {"take_profit": take_profit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/close-position/{symbol}")
async def close_position(symbol: str, current_price: float):
    """Close a position"""
    try:
        position = trading_engine.positions.get(symbol)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        
        result = trading_engine.execute_trade(
            symbol=symbol,
            price=current_price,
            quantity=position["quantity"],
            side="SELL" if position["side"] == "BUY" else "BUY"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail="Failed to close position")
        
        return {
            "success": True,
            "message": f"Position closed for {symbol}",
            "pnl": result.get("pnl", 0)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
