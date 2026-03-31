# Portfolio Optimization API
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.backtest_engine import fetch_klines
from app.services.portfolio_engine import (
    run_portfolio, optimize_weights, monte_carlo_optimization, 
    generate_portfolio_report, calculate_portfolio_metrics
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

class PortfolioRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategies: List[str] = ["sma", "ema", "rsi", "bollinger", "macd"]
    weights: Optional[Dict[str, float]] = None
    interval: str = "1h"
    limit: int = 500
    initial_balance: float = 10000

class OptimizationRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategies: List[str] = ["sma", "ema", "rsi", "bollinger", "macd"]
    method: str = "grid"  # "grid" or "monte_carlo"
    iterations: int = 1000
    interval: str = "1h"
    limit: int = 500

@router.get("/backtest")
def portfolio_backtest():
    """Run default portfolio backtest"""
    try:
        # Fetch data
        data = fetch_klines("BTCUSDT", "1h", 500)
        prices = data["prices"]
        
        # Run portfolio with equal weights
        result = run_portfolio(prices)
        metrics = calculate_portfolio_metrics(result["equity"])
        
        return {
            "success": True,
            "symbol": data["symbol"],
            "strategies": result["strategies"],
            "weights": result["weights"],
            "equity": result["equity"],
            "final_balance": result["final_balance"],
            "total_trades": len(result["trades"]),
            "metrics": metrics,
            "data_info": {
                "data_points": data["data_points"],
                "mock_data": data.get("mock", False),
                "interval": data["interval"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
def custom_portfolio_backtest(request: PortfolioRequest):
    """Run custom portfolio backtest"""
    try:
        # Fetch data
        data = fetch_klines(request.symbol, request.interval, request.limit)
        prices = data["prices"]
        
        # Run portfolio
        result = run_portfolio(prices, request.weights, request.strategies)
        metrics = calculate_portfolio_metrics(result["equity"])
        
        return {
            "success": True,
            "request": {
                "symbol": request.symbol,
                "strategies": request.strategies,
                "weights": request.weights,
                "interval": request.interval,
                "limit": request.limit,
                "initial_balance": request.initial_balance
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
                "weights": result["weights"],
                "total_trades": len(result["trades"])
            },
            "metrics": metrics,
            "trades": result["trades"][-10:]  # Last 10 trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
def optimize_portfolio(request: OptimizationRequest):
    """Optimize portfolio weights"""
    try:
        # Fetch data
        data = fetch_klines(request.symbol, request.interval, request.limit)
        prices = data["prices"]
        
        # Run optimization
        if request.method == "grid":
            result = optimize_weights(prices, request.strategies)
        elif request.method == "monte_carlo":
            result = monte_carlo_optimization(prices, request.strategies, request.iterations)
        else:
            raise HTTPException(status_code=400, detail="Invalid optimization method")
        
        return {
            "success": True,
            "optimization_method": request.method,
            "symbol": data["symbol"],
            "strategies": request.strategies,
            "data_info": {
                "data_points": data["data_points"],
                "mock_data": data.get("mock", False),
                "interval": data["interval"]
            },
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
def get_available_strategies():
    """Get available portfolio strategies"""
    try:
        strategies = [
            {
                "name": "sma",
                "display_name": "Simple Moving Average",
                "description": "Classic moving average crossover strategy",
                "type": "trend_following",
                "complexity": "low"
            },
            {
                "name": "ema",
                "display_name": "Exponential Moving Average",
                "description": "Exponential moving average with recent price emphasis",
                "type": "trend_following",
                "complexity": "low"
            },
            {
                "name": "rsi",
                "display_name": "RSI Oscillator",
                "description": "Relative Strength Index for overbought/oversold",
                "type": "oscillator",
                "complexity": "medium"
            },
            {
                "name": "bollinger",
                "display_name": "Bollinger Bands",
                "description": "Volatility-based breakout strategy",
                "type": "volatility",
                "complexity": "medium"
            },
            {
                "name": "macd",
                "display_name": "MACD",
                "description": "Moving Average Convergence Divergence",
                "type": "momentum",
                "complexity": "medium"
            },
            {
                "name": "stochastic",
                "display_name": "Stochastic Oscillator",
                "description": "Momentum oscillator with overbought/oversold",
                "type": "oscillator",
                "complexity": "medium"
            },
            {
                "name": "williams",
                "display_name": "Williams %R",
                "description": "Momentum oscillator measuring overbought/oversold",
                "type": "oscillator",
                "complexity": "medium"
            },
            {
                "name": "atr",
                "display_name": "ATR Trailing Stop",
                "description": "Average True Range for volatility-based stops",
                "type": "volatility",
                "complexity": "high"
            },
            {
                "name": "vwap",
                "display_name": "VWAP",
                "description": "Volume Weighted Average Price",
                "type": "volume",
                "complexity": "high"
            }
        ]
        
        return {
            "success": True,
            "strategies": strategies,
            "total_strategies": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report")
def generate_portfolio_analysis(request: PortfolioRequest):
    """Generate comprehensive portfolio analysis report"""
    try:
        # Fetch data
        data = fetch_klines(request.symbol, request.interval, request.limit)
        prices = data["prices"]
        
        # Generate report
        report = generate_portfolio_report(prices, request.weights, request.strategies)
        
        return {
            "success": True,
            "symbol": request.symbol,
            "report": report,
            "data_info": {
                "data_points": data["data_points"],
                "mock_data": data.get("mock", False),
                "interval": data["interval"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison")
def compare_strategy_performance():
    """Compare all strategy performances individually"""
    try:
        # Fetch data
        data = fetch_klines("BTCUSDT", "1h", 500)
        prices = data["prices"]
        
        # Test each strategy individually
        from app.services.strategies import get_strategy_signals, calculate_strategy_performance
        all_signals = get_strategy_signals(prices)
        
        comparison_results = []
        strategies = ['sma', 'ema', 'rsi', 'bollinger', 'macd', 'stochastic']
        
        for strategy in strategies:
            if strategy in all_signals:
                performance = calculate_strategy_performance(all_signals[strategy], prices)
                
                comparison_results.append({
                    "strategy": strategy,
                    "final_balance": performance["final_balance"],
                    "total_return": (performance["final_balance"] - 10000) / 10000 * 100,
                    "sharpe_ratio": calculate_portfolio_metrics(performance["equity"])["sharpe_ratio"],
                    "max_drawdown": calculate_portfolio_metrics(performance["equity"])["max_drawdown"],
                    "win_rate": performance["win_rate"],
                    "total_trades": performance["total_trades"]
                })
        
        # Sort by Sharpe ratio
        comparison_results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        
        return {
            "success": True,
            "symbol": data["symbol"],
            "data_points": data["data_points"],
            "comparison": comparison_results,
            "best_strategy": comparison_results[0] if comparison_results else None,
            "ranking_by_return": sorted(comparison_results, key=lambda x: x["total_return"], reverse=True),
            "ranking_by_sharpe": sorted(comparison_results, key=lambda x: x["sharpe_ratio"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_portfolio_history():
    """Get portfolio optimization history (mock data)"""
    try:
        history = [
            {
                "id": 1,
                "symbol": "BTCUSDT",
                "strategies": ["sma", "rsi", "bollinger"],
                "optimization_method": "grid",
                "date": "2024-01-15T10:30:00Z",
                "initial_balance": 10000,
                "final_balance": 12500,
                "total_return": 25.0,
                "sharpe_ratio": 1.85,
                "max_drawdown": -8.5,
                "best_weights": {"sma": 0.4, "rsi": 0.3, "bollinger": 0.3}
            },
            {
                "id": 2,
                "symbol": "ETHUSDT",
                "strategies": ["ema", "macd", "stochastic"],
                "optimization_method": "monte_carlo",
                "date": "2024-01-14T15:20:00Z",
                "initial_balance": 10000,
                "final_balance": 11850,
                "total_return": 18.5,
                "sharpe_ratio": 1.65,
                "max_drawdown": -12.3,
                "best_weights": {"ema": 0.5, "macd": 0.3, "stochastic": 0.2}
            },
            {
                "id": 3,
                "symbol": "ADAUSDT",
                "strategies": ["sma", "ema", "rsi", "bollinger", "macd"],
                "optimization_method": "grid",
                "date": "2024-01-13T09:15:00Z",
                "initial_balance": 10000,
                "final_balance": 10890,
                "total_return": 8.9,
                "sharpe_ratio": 1.25,
                "max_drawdown": -6.7,
                "best_weights": {"sma": 0.2, "ema": 0.2, "rsi": 0.3, "bollinger": 0.2, "macd": 0.1}
            }
        ]
        
        return {
            "success": True,
            "history": history,
            "total_optimizations": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
