# =========================
# services/analytics.py
# =========================
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class AnalyticsEngine:
    def __init__(self):
        self.metrics_cache = {}
    
    def calculate_sharpe_ratio(self, equity_curve: List[float]) -> float:
        """
        Calculate Sharpe ratio from equity curve
        """
        if len(equity_curve) < 2:
            return 0.0
        
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        # Remove any invalid returns
        valid_returns = returns[~np.isnan(returns) & ~np.isinf(returns)]
        
        if len(valid_returns) == 0 or np.std(valid_returns) == 0:
            return 0.0
        
        # Annualized Sharpe ratio (assuming daily returns)
        sharpe = np.mean(valid_returns) / np.std(valid_returns) * np.sqrt(252)
        return sharpe
    
    def calculate_sortino_ratio(self, equity_curve: List[float]) -> float:
        """
        Calculate Sortino ratio (downside risk adjusted return)
        """
        if len(equity_curve) < 2:
            return 0.0
        
        returns = np.diff(equity_curve) / equity_curve[:-1]
        valid_returns = returns[~np.isnan(returns) & ~np.isinf(returns)]
        
        if len(valid_returns) == 0:
            return 0.0
        
        # Only consider negative returns for downside deviation
        negative_returns = valid_returns[valid_returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf') if np.mean(valid_returns) > 0 else 0.0
        
        downside_deviation = np.std(negative_returns)
        if downside_deviation == 0:
            return 0.0
        
        # Annualized Sortino ratio
        sortino = np.mean(valid_returns) / downside_deviation * np.sqrt(252)
        return sortino
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """
        Calculate maximum drawdown and duration
        """
        if not equity_curve:
            return {"max_drawdown": 0.0, "duration": 0}
        
        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_duration = 0
        current_dd_duration = 0
        
        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                current_dd_duration = 0
            else:
                current_dd_duration += 1
                drawdown = (peak - equity) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
                    max_dd_duration = current_dd_duration
        
        return {
            "max_drawdown": max_dd * 100,  # Return as percentage
            "duration": max_dd_duration
        }
    
    def calculate_volatility(self, returns: List[float]) -> float:
        """
        Calculate annualized volatility
        """
        if len(returns) < 2:
            return 0.0
        
        valid_returns = [r for r in returns if not np.isnan(r) and not np.isinf(r)]
        if len(valid_returns) == 0:
            return 0.0
        
        volatility = np.std(valid_returns) * np.sqrt(252)  # Annualized
        return volatility * 100  # Return as percentage
    
    def calculate_calmar_ratio(self, equity_curve: List[float]) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown)
        """
        if len(equity_curve) < 2:
            return 0.0
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        annual_return = total_return * (252 / len(equity_curve))  # Annualized
        
        max_dd_result = self.calculate_max_drawdown(equity_curve)
        max_dd = max_dd_result["max_drawdown"] / 100  # Convert back to decimal
        
        if max_dd == 0:
            return float('inf') if annual_return > 0 else 0.0
        
        return annual_return / max_dd
    
    def calculate_win_rate(self, trades: List[Dict]) -> Dict[str, any]:
        """
        Calculate win rate and related metrics
        """
        if not trades:
            return {"win_rate": 0.0, "total_trades": 0, "winning_trades": 0}
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        
        win_rate = len(winning_trades) / len(trades) * 100
        
        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t["pnl"]) for t in losing_trades]) if losing_trades else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        return {
            "win_rate": round(win_rate, 2),
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2)
        }
    
    def generate_portfolio_metrics(self, portfolio_data: Dict) -> Dict[str, any]:
        """
        Generate comprehensive portfolio analytics
        """
        equity_curve = portfolio_data.get("equity_curve", [])
        trades = portfolio_data.get("trades", [])
        
        if not equity_curve:
            return {"error": "No equity data available"}
        
        # Calculate all metrics
        sharpe = self.calculate_sharpe_ratio(equity_curve)
        sortino = self.calculate_sortino_ratio(equity_curve)
        max_dd = self.calculate_max_drawdown(equity_curve)
        calmar = self.calculate_calmar_ratio(equity_curve)
        win_metrics = self.calculate_win_rate(trades)
        
        # Calculate returns
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] * 100
        
        return {
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "max_drawdown": max_dd,
            "calmar_ratio": round(calmar, 3),
            "current_equity": equity_curve[-1],
            "peak_equity": max(equity_curve),
            "win_metrics": win_metrics,
            "last_updated": datetime.utcnow().isoformat()
        }

# Global analytics engine
analytics_engine = AnalyticsEngine()

def sharpe(equity: List[float]) -> float:
    return analytics_engine.calculate_sharpe_ratio(equity)
