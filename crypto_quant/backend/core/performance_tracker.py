"""Performance tracking and metrics computation."""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime


class PerformanceTracker:
    """Tracks and computes trading performance metrics."""

    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.portfolio_history: List[Dict[str, Any]] = []

    def add_trade(self, trade: Dict[str, Any]):
        """Add a completed trade."""
        self.trades.append(trade)

    def compute_metrics(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Compute performance metrics from signals and trade history."""
        if not self.trades:
            return {
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "total_trades": 0,
                "profitable_trades": 0,
                "losing_trades": 0,
                "max_drawdown": 0.0,
                "sharpe_ratio": None
            }

        # Calculate basic metrics
        profitable_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
        total_trades = len(self.trades)

        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0

        pnl_values = [t.get('pnl', 0) for t in self.trades]
        avg_pnl = sum(pnl_values) / len(pnl_values) if pnl_values else 0.0

        # Calculate drawdown
        cumulative_pnl = pd.Series([sum(pnl_values[:i+1]) for i in range(len(pnl_values))])
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0

        # Sharpe ratio (simplified)
        if len(pnl_values) > 1:
            returns = pd.Series(pnl_values)
            sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0.0
        else:
            sharpe_ratio = None

        return {
            "win_rate": round(win_rate, 4),
            "avg_pnl": round(avg_pnl, 4),
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "losing_trades": losing_trades,
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe_ratio, 4) if sharpe_ratio is not None else None
        }