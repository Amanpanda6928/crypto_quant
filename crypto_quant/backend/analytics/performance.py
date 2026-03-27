"""
Performance Analytics Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import empyrical as ep

class PerformanceAnalyzer:
    """Advanced performance analytics for trading strategies"""

    def __init__(self):
        self.metrics = {}

    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calculate returns from price series"""
        return prices.pct_change().fillna(0)

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + self.calculate_returns(prices)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """Calculate win rate from trades"""
        if len(trades) == 0:
            return 0.0

        winning_trades = len(trades[trades['pnl'] > 0])
        return winning_trades / len(trades)

    def calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor"""
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]

        total_wins = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
        total_losses = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 1

        return total_wins / total_losses

    def analyze_portfolio(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series = None) -> Dict:
        """Comprehensive portfolio analysis"""
        analysis = {}

        # Basic metrics
        analysis['total_return'] = ep.cum_returns_final(portfolio_returns)
        analysis['annual_return'] = ep.annual_return(portfolio_returns)
        analysis['annual_volatility'] = ep.annual_volatility(portfolio_returns)
        analysis['sharpe_ratio'] = ep.sharpe_ratio(portfolio_returns)
        analysis['max_drawdown'] = ep.max_drawdown(portfolio_returns)
        analysis['calmar_ratio'] = ep.calmar_ratio(portfolio_returns)

        # Risk metrics
        analysis['var_95'] = ep.value_at_risk(portfolio_returns, cutoff=0.05)
        analysis['cvar_95'] = ep.conditional_value_at_risk(portfolio_returns, cutoff=0.05)

        # Benchmark comparison
        if benchmark_returns is not None:
            analysis['alpha'] = ep.alpha(portfolio_returns, benchmark_returns)
            analysis['beta'] = ep.beta(portfolio_returns, benchmark_returns)

        return analysis