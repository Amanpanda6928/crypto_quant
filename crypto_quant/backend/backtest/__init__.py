"""
Backtest module for trading simulation and performance evaluation.

Includes:
- Trade execution engine
- Signal & trade structures
- Performance metrics
- Walk-forward validation
"""

from .engine import BacktestEngine, Signal, Trade
from .metrics import MetricsCalculator
from .run_backtest import WalkForwardBacktest, run_simple_backtest

__all__ = [
    "BacktestEngine",
    "Signal",
    "Trade",
    "MetricsCalculator",
    "WalkForwardBacktest",
    "run_simple_backtest",
]
