# =========================
# api/analytics.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.analytics import analytics_engine
from app.services.backtesting import backtest_engine
from app.services.trading_engine import trading_engine

router = APIRouter()

class AnalyticsRequest(BaseModel):
    equity_curve: List[float]
    trades: Optional[List[dict]] = None

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_balance: float = 10000

@router.post("/portfolio")
async def analyze_portfolio(request: AnalyticsRequest):
    """Analyze portfolio performance"""
    try:
        portfolio_data = {
            "equity_curve": request.equity_curve,
            "trades": request.trades or []
        }
        
        metrics = analytics_engine.generate_portfolio_metrics(portfolio_data)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtesting on historical data"""
    try:
        # Generate mock historical data
        import numpy as np
        import random
        
        # Generate 100 days of price data
        days = 100
        base_price = 50000 if "BTC" in request.symbol else 3000
        prices = []
        
        current_price = base_price
        for _ in range(days):
            change = np.random.normal(0, 0.02)  # 2% daily volatility
            current_price *= (1 + change)
            prices.append(current_price)
        
        # Generate mock signals
        signals = []
        for i in range(days):
            if i % 7 == 0:  # Weekly signals
                signals.append(random.choice(["BUY", "SELL"]))
            else:
                signals.append("HOLD")
        
        # Run backtest
        result = backtest_engine.run_backtest(prices, signals, request.symbol)
        
        return {
            "symbol": request.symbol,
            "period": f"{days} days",
            "initial_balance": request.initial_balance,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current")
async def get_current_analytics():
    """Get current portfolio analytics"""
    try:
        portfolio = trading_engine.get_portfolio_summary()
        trades = trading_engine.get_trade_history()
        
        # Generate mock equity curve if not available
        equity_curve = []
        current_equity = portfolio.get("equity", 10000)
        
        for i in range(30):  # 30 days
            change = random.uniform(-0.05, 0.05)  # 5% daily change
            current_equity *= (1 + change)
            equity_curve.append(current_equity)
        
        analytics_data = {
            "equity_curve": equity_curve,
            "trades": trades
        }
        
        metrics = analytics_engine.generate_portfolio_metrics(analytics_data)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{period}")
async def get_performance_metrics(period: str = "daily"):
    """Get performance metrics for different periods"""
    try:
        periods = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "yearly": 365
        }
        
        days = periods.get(period, 30)
        
        # Generate mock performance data
        import random
        import numpy as np
        
        # Generate equity curve
        equity_curve = []
        base_equity = 10000
        
        for _ in range(days):
            daily_return = np.random.normal(0.001, 0.02)  # 0.1% daily return, 2% volatility
            base_equity *= (1 + daily_return)
            equity_curve.append(base_equity)
        
        # Calculate metrics
        sharpe = analytics_engine.calculate_sharpe_ratio(equity_curve)
        sortino = analytics_engine.calculate_sortino_ratio(equity_curve)
        max_dd = analytics_engine.calculate_max_drawdown(equity_curve)
        volatility = analytics_engine.calculate_volatility(np.diff(equity_curve) / equity_curve[:-1])
        
        return {
            "period": period,
            "days": days,
            "metrics": {
                "total_return": round((equity_curve[-1] - equity_curve[0]) / equity_curve[0] * 100, 2),
                "sharpe_ratio": round(sharpe, 3),
                "sortino_ratio": round(sortino, 3),
                "max_drawdown": max_dd,
                "volatility": round(volatility, 2),
                "current_equity": equity_curve[-1],
                "peak_equity": max(equity_curve)
            },
            "equity_curve": equity_curve[-100:]  # Return last 100 data points
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-analysis")
async def get_risk_analysis():
    """Get comprehensive risk analysis"""
    try:
        portfolio = trading_engine.get_portfolio_summary()
        
        # Mock risk metrics
        risk_analysis = {
            "portfolio_risk": {
                "var_95": round(portfolio.get("balance", 10000) * 0.05, 2),  # 5% VaR
                "var_99": round(portfolio.get("balance", 10000) * 0.08, 2),  # 8% VaR
                "beta": 1.2,
                "correlation_to_market": 0.75
            },
            "position_risk": {
                "concentration_risk": "Medium",
                "largest_position_pct": 25.5,
                "sector_exposure": {
                    "cryptocurrency": 85.0,
                    "forex": 15.0
                }
            },
            "risk_metrics": {
                "risk_score": 7.2,  # Scale 1-10
                "risk_level": "Medium-High",
                "recommended_actions": [
                    "Consider reducing position sizes",
                    "Diversify across more assets",
                    "Set tighter stop losses"
                ]
            }
        }
        
        return risk_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison")
async def get_strategy_comparison():
    """Compare different trading strategies"""
    try:
        strategies = [
            {
                "name": "AI Momentum",
                "return": 15.2,
                "sharpe": 1.85,
                "max_drawdown": 8.5,
                "win_rate": 68.5,
                "trades": 142
            },
            {
                "name": "Mean Reversion",
                "return": 12.8,
                "sharpe": 1.65,
                "max_drawdown": 11.2,
                "win_rate": 72.1,
                "trades": 98
            },
            {
                "name": "Trend Following",
                "return": 18.5,
                "sharpe": 1.45,
                "max_drawdown": 15.8,
                "win_rate": 58.3,
                "trades": 67
            },
            {
                "name": "Buy & Hold",
                "return": 8.9,
                "sharpe": 0.95,
                "max_drawdown": 22.5,
                "win_rate": 100.0,
                "trades": 1
            }
        ]
        
        return {"strategies": strategies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports")
async def get_analytics_reports():
    """Get available analytics reports"""
    try:
        reports = [
            {
                "id": 1,
                "name": "Daily Performance Report",
                "type": "daily",
                "generated_at": "2024-01-01T00:00:00Z",
                "metrics": {
                    "return": 2.3,
                    "trades": 5,
                    "win_rate": 80.0
                }
            },
            {
                "id": 2,
                "name": "Weekly Risk Analysis",
                "type": "risk",
                "generated_at": "2024-01-01T00:00:00Z",
                "metrics": {
                    "var_95": 500.0,
                    "max_drawdown": 5.2,
                    "risk_score": 6.8
                }
            },
            {
                "id": 3,
                "name": "Monthly Strategy Review",
                "type": "monthly",
                "generated_at": "2024-01-01T00:00:00Z",
                "metrics": {
                    "total_return": 12.5,
                    "sharpe_ratio": 1.85,
                    "best_strategy": "AI Momentum"
                }
            }
        ]
        
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
