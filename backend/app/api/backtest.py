# Backtesting API with Advanced Analytics
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backtesting.strategies import StrategyBacktester
    STRATEGIES_AVAILABLE = True
except ImportError:
    STRATEGIES_AVAILABLE = False

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_balance: float = 10000
    strategy: str = "ai_signals"
    parameters: Optional[dict] = {}

class BacktestResult(BaseModel):
    success: bool
    equity_curve: List[float]
    final_balance: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    average_trade: float
    best_trade: float
    worst_trade: float

@router.post("/")
async def run_backtest(data: dict):
    """Simple backtest endpoint for compatibility"""
    try:
        prices = data.get("prices", [])
        if not prices:
            raise HTTPException(status_code=400, detail="Prices array is required")
        
        balance = 10000
        equity = []
        trades = []
        
        for i, price in enumerate(prices):
            # Simple signal generation
            signal = "BUY" if i % 2 == 0 else "SELL"
            
            if signal == "BUY":
                balance += price * 0.01
                trades.append({"type": "BUY", "price": price, "time": i})
            else:
                balance -= price * 0.005
                trades.append({"type": "SELL", "price": price, "time": i})
            
            equity.append(balance)
        
        return {
            "success": True,
            "equity": equity,
            "final_balance": balance,
            "total_trades": len(trades),
            "trades": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced")
async def run_advanced_backtest(request: BacktestRequest):
    """Advanced backtesting with multiple strategies"""
    try:
        # Generate mock price data for testing
        np.random.seed(int(time.time()))
        days = 100
        base_price = 50000
        prices = []
        
        current_price = base_price
        for i in range(days):
            change = np.random.normal(0, 0.02)  # 2% daily volatility
            current_price *= (1 + change)
            prices.append(current_price)
        
        # Run backtest based on strategy
        if request.strategy == "ai_signals":
            result = run_ai_backtest(prices, request.initial_balance, request.parameters)
        elif request.strategy == "moving_average":
            result = run_ma_backtest(prices, request.initial_balance, request.parameters)
        elif request.strategy == "rsi":
            result = run_rsi_backtest(prices, request.initial_balance, request.parameters)
        else:
            result = run_simple_backtest(prices, request.initial_balance, request.parameters)
        
        return {
            "success": True,
            "symbol": request.symbol,
            "strategy": request.strategy,
            "period": f"{days} days",
            "initial_balance": request.initial_balance,
            "result": result.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_ai_backtest(prices, initial_balance, params):
    """AI signals backtest"""
    balance = initial_balance
    equity = []
    trades = []
    position = None
    
    for i, price in enumerate(prices):
        # Mock AI signal
        signal = "BUY" if i % 7 == 0 else "SELL" if i % 7 == 3 else "HOLD"
        
        if signal == "BUY" and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i
            }
        elif signal == "SELL" and position is not None:
            pnl = (price - position["entry"]) * position["quantity"]
            balance += pnl
            trades.append({
                "entry": position["entry"],
                "exit": price,
                "pnl": pnl,
                "time": position["time"],
                "exit_time": i
            })
            position = None
        
        equity.append(balance)
    
    return calculate_metrics(equity, initial_balance, trades)

def run_ma_backtest(prices, initial_balance, params):
    """Moving average strategy backtest"""
    balance = initial_balance
    equity = []
    trades = []
    position = None
    
    short_window = params.get("short_window", 10)
    long_window = params.get("long_window", 30)
    
    for i in range(long_window, len(prices)):
        short_ma = np.mean(prices[i-short_window:i])
        long_ma = np.mean(prices[i-long_window:i])
        price = prices[i]
        
        if short_ma > long_ma and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i
            }
        elif short_ma < long_ma and position is not None:
            pnl = (price - position["entry"]) * position["quantity"]
            balance += pnl
            trades.append({
                "entry": position["entry"],
                "exit": price,
                "pnl": pnl,
                "time": position["time"],
                "exit_time": i
            })
            position = None
        
        equity.append(balance)
    
    return calculate_metrics(equity, initial_balance, trades)

def run_rsi_backtest(prices, initial_balance, params):
    """RSI strategy backtest"""
    balance = initial_balance
    equity = []
    trades = []
    position = None
    
    rsi_period = params.get("rsi_period", 14)
    rsi_overbought = params.get("rsi_overbought", 70)
    rsi_oversold = params.get("rsi_oversold", 30)
    
    # Calculate RSI
    rsi_values = calculate_rsi(prices, rsi_period)
    
    for i in range(rsi_period, len(prices)):
        price = prices[i]
        rsi = rsi_values[i]
        
        if rsi < rsi_oversold and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i
            }
        elif rsi > rsi_overbought and position is not None:
            pnl = (price - position["entry"]) * position["quantity"]
            balance += pnl
            trades.append({
                "entry": position["entry"],
                "exit": price,
                "pnl": pnl,
                "time": position["time"],
                "exit_time": i
            })
            position = None
        
        equity.append(balance)
    
    return calculate_metrics(equity, initial_balance, trades)

def run_simple_backtest(prices, initial_balance, params):
    """Simple buy/sell backtest"""
    balance = initial_balance
    equity = []
    trades = []
    
    for i, price in enumerate(prices):
        # Simple alternating strategy
        signal = "BUY" if i % 2 == 0 else "SELL"
        
        if signal == "BUY":
            balance += price * 0.01
            trades.append({"type": "BUY", "price": price, "time": i})
        else:
            balance -= price * 0.005
            trades.append({"type": "SELL", "price": price, "time": i})
        
        equity.append(balance)
    
    return calculate_metrics(equity, initial_balance, trades)

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    rsi_values = []
    
    for i in range(period, len(prices)):
        price_slice = prices[i-period+1:i+1]
        gains = []
        losses = []
        
        for j in range(1, len(price_slice)):
            change = price_slice[j] - price_slice[j-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

def calculate_metrics(equity, initial_balance, trades):
    """Calculate backtest performance metrics"""
    if not equity:
        return BacktestResult(
            success=False,
            equity_curve=[],
            final_balance=initial_balance,
            total_return=0,
            sharpe_ratio=0,
            max_drawdown=0,
            win_rate=0,
            total_trades=0,
            profitable_trades=0,
            average_trade=0,
            best_trade=0,
            worst_trade=0
        )
    
    final_balance = equity[-1]
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    # Calculate Sharpe ratio
    returns = np.diff(equity) / equity[:-1]
    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    # Calculate maximum drawdown
    peak = equity[0]
    max_drawdown = 0
    for value in equity:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        max_drawdown = max(max_drawdown, drawdown)
    
    # Calculate trade statistics
    if trades:
        pnl_values = [trade.get("pnl", 0) for trade in trades]
        profitable_trades = len([pnl for pnl in pnl_values if pnl > 0])
        win_rate = profitable_trades / len(trades) * 100
        average_trade = np.mean(pnl_values)
        best_trade = max(pnl_values)
        worst_trade = min(pnl_values)
    else:
        profitable_trades = 0
        win_rate = 0
        average_trade = 0
        best_trade = 0
        worst_trade = 0
    
    return BacktestResult(
        success=True,
        equity_curve=equity,
        final_balance=final_balance,
        total_return=total_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        total_trades=len(trades),
        profitable_trades=profitable_trades,
        average_trade=average_trade,
        best_trade=best_trade,
        worst_trade=worst_trade
    )

@router.get("/strategies")
async def get_backtest_strategies():
    """Get available backtest strategies"""
    return {
        "success": True,
        "strategies": [
            {
                "name": "ai_signals",
                "description": "AI-powered trading signals",
                "parameters": {
                    "confidence_threshold": {"type": "float", "default": 0.7, "min": 0.5, "max": 1.0}
                }
            },
            {
                "name": "moving_average",
                "description": "Moving average crossover strategy",
                "parameters": {
                    "short_window": {"type": "int", "default": 10, "min": 5, "max": 20},
                    "long_window": {"type": "int", "default": 30, "min": 20, "max": 50}
                }
            },
            {
                "name": "rsi",
                "description": "RSI overbought/oversold strategy",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 10, "max": 30},
                    "rsi_overbought": {"type": "int", "default": 70, "min": 60, "max": 80},
                    "rsi_oversold": {"type": "int", "default": 30, "min": 20, "max": 40}
                }
            },
            {
                "name": "simple",
                "description": "Simple alternating buy/sell strategy",
                "parameters": {}
            }
        ]
    }

@router.get("/history")
async def get_backtest_history():
    """Get backtest history (mock data)"""
    return {
        "success": True,
        "history": [
            {
                "id": 1,
                "symbol": "BTCUSDT",
                "strategy": "ai_signals",
                "date": "2024-01-15",
                "initial_balance": 10000,
                "final_balance": 11250,
                "total_return": 12.5,
                "win_rate": 68.5,
                "sharpe_ratio": 1.85
            },
            {
                "id": 2,
                "symbol": "ETHUSDT",
                "strategy": "moving_average",
                "date": "2024-01-14",
                "initial_balance": 10000,
                "final_balance": 9850,
                "total_return": -1.5,
                "win_rate": 45.2,
                "sharpe_ratio": -0.45
            }
        ]
    }
