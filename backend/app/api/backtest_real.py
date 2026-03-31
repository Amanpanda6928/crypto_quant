# Real Backtesting API with Binance Integration
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.backtest_engine import fetch_klines, run_backtest, calculate_metrics, get_available_strategies

router = APIRouter(prefix="/api/backtest-real", tags=["backtest-real"])

class BacktestRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategy: str = "ma_crossover"
    interval: str = "1h"
    limit: int = 500
    initial_balance: float = 10000
    parameters: Optional[dict] = {}

@router.get("/")
async def run_default_backtest():
    """Run default backtest with BTCUSDT"""
    try:
        # Fetch real data from Binance
        data = fetch_klines("BTCUSDT", "1h", 500)
        
        # Run backtest with default strategy
        result = run_backtest(data["prices"], "ma_crossover", {
            "short_window": 10,
            "long_window": 30
        })
        
        # Calculate performance metrics
        metrics = calculate_metrics(result["equity"])
        
        return {
            "success": True,
            "symbol": data["symbol"],
            "strategy": result["strategy"],
            "data_points": data["data_points"],
            "mock_data": data.get("mock", False),
            "result": {
                "equity": result["equity"],
                "final_balance": result["final_balance"],
                "wins": result["wins"],
                "losses": result["losses"],
                "total_trades": len(result["trades"]),
                "win_rate": (result["wins"] / len(result["trades"]) * 100) if result["trades"] else 0
            },
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def run_custom_backtest(request: BacktestRequest):
    """Run custom backtest with specified parameters"""
    try:
        # Fetch real data from Binance
        data = fetch_klines(request.symbol, request.interval, request.limit)
        
        # Run backtest with specified strategy
        result = run_backtest(data["prices"], request.strategy, request.parameters)
        
        # Calculate performance metrics
        metrics = calculate_metrics(result["equity"], request.initial_balance)
        
        return {
            "success": True,
            "request": {
                "symbol": request.symbol,
                "strategy": request.strategy,
                "interval": request.interval,
                "limit": request.limit,
                "initial_balance": request.initial_balance,
                "parameters": request.parameters
            },
            "data_info": {
                "symbol": data["symbol"],
                "data_points": data["data_points"],
                "mock_data": data.get("mock", False),
                "interval": data["interval"]
            },
            "result": {
                "equity": result["equity"],
                "final_balance": result["final_balance"],
                "wins": result["wins"],
                "losses": result["losses"],
                "total_trades": len(result["trades"]),
                "win_rate": (result["wins"] / len(result["trades"]) * 100) if result["trades"] else 0
            },
            "metrics": metrics,
            "trades": result["trades"][-10:]  # Return last 10 trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_strategies():
    """Get available backtesting strategies"""
    try:
        return get_available_strategies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_available_symbols():
    """Get available symbols for backtesting"""
    try:
        symbols = [
            {"symbol": "BTCUSDT", "name": "Bitcoin", "base_price": 45000},
            {"symbol": "ETHUSDT", "name": "Ethereum", "base_price": 3200},
            {"symbol": "ADAUSDT", "name": "Cardano", "base_price": 1.2},
            {"symbol": "SOLUSDT", "name": "Solana", "base_price": 120},
            {"symbol": "DOGEUSDT", "name": "Dogecoin", "base_price": 0.085},
            {"symbol": "DOTUSDT", "name": "Polkadot", "base_price": 8.5},
            {"symbol": "MATICUSDT", "name": "Polygon", "base_price": 0.95},
            {"symbol": "AVAXUSDT", "name": "Avalanche", "base_price": 38},
            {"symbol": "LINKUSDT", "name": "Chainlink", "base_price": 16},
            {"symbol": "UNIUSDT", "name": "Uniswap", "base_price": 7.5}
        ]
        
        return {
            "success": True,
            "symbols": symbols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intervals")
async def get_available_intervals():
    """Get available time intervals"""
    try:
        intervals = [
            {"interval": "1m", "name": "1 Minute", "duration": "1 minute"},
            {"interval": "5m", "name": "5 Minutes", "duration": "5 minutes"},
            {"interval": "15m", "name": "15 Minutes", "duration": "15 minutes"},
            {"interval": "30m", "name": "30 Minutes", "duration": "30 minutes"},
            {"interval": "1h", "name": "1 Hour", "duration": "1 hour"},
            {"interval": "4h", "name": "4 Hours", "duration": "4 hours"},
            {"interval": "1d", "name": "1 Day", "duration": "1 day"}
        ]
        
        return {
            "success": True,
            "intervals": intervals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_strategies(data: dict):
    """Compare multiple strategies"""
    try:
        symbol = data.get("symbol", "BTCUSDT")
        strategies = data.get("strategies", ["ma_crossover", "rsi"])
        interval = data.get("interval", "1h")
        limit = data.get("limit", 500)
        
        # Fetch data once
        market_data = fetch_klines(symbol, interval, limit)
        prices = market_data["prices"]
        
        # Run backtest for each strategy
        comparison_results = []
        
        for strategy in strategies:
            result = run_backtest(prices, strategy, {})
            metrics = calculate_metrics(result["equity"])
            
            comparison_results.append({
                "strategy": strategy,
                "final_balance": result["final_balance"],
                "total_return": metrics["total_return"],
                "sharpe_ratio": metrics["sharpe"],
                "max_drawdown": metrics["max_drawdown"],
                "win_rate": (result["wins"] / len(result["trades"]) * 100) if result["trades"] else 0,
                "total_trades": len(result["trades"])
            })
        
        # Sort by Sharpe ratio
        comparison_results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        
        return {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "data_points": len(prices),
            "comparison": comparison_results,
            "best_strategy": comparison_results[0] if comparison_results else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_backtest_history():
    """Get backtest history (mock data)"""
    try:
        history = [
            {
                "id": 1,
                "symbol": "BTCUSDT",
                "strategy": "ma_crossover",
                "interval": "1h",
                "date": "2024-01-15T10:30:00Z",
                "initial_balance": 10000,
                "final_balance": 11250,
                "total_return": 12.5,
                "sharpe_ratio": 1.85,
                "max_drawdown": -8.5,
                "win_rate": 68.5,
                "total_trades": 45
            },
            {
                "id": 2,
                "symbol": "ETHUSDT",
                "strategy": "rsi",
                "interval": "1h",
                "date": "2024-01-14T15:20:00Z",
                "initial_balance": 10000,
                "final_balance": 9850,
                "total_return": -1.5,
                "sharpe_ratio": -0.45,
                "max_drawdown": -12.3,
                "win_rate": 45.2,
                "total_trades": 38
            },
            {
                "id": 3,
                "symbol": "ADAUSDT",
                "strategy": "bollinger_bands",
                "interval": "4h",
                "date": "2024-01-13T09:15:00Z",
                "initial_balance": 10000,
                "final_balance": 10890,
                "total_return": 8.9,
                "sharpe_ratio": 1.25,
                "max_drawdown": -6.7,
                "win_rate": 58.3,
                "total_trades": 52
            }
        ]
        
        return {
            "success": True,
            "history": history,
            "total_backtests": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
