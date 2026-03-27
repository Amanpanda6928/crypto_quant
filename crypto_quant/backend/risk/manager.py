"""
Risk Manager - Position Sizing
"""

import numpy as np


class RiskManager:

    def __init__(self):
        pass

    def size(self, capital: float, price: float, volatility: float) -> float:
        """
        Calculate position size based on capital, price, and volatility

        Args:
            capital: Available capital
            price: Current asset price
            volatility: Asset volatility (e.g., standard deviation of returns)

        Returns:
            Position size in asset units
        """
        base = (capital * 0.02) / price  # 2% of capital per trade
        scale = max(0.3, min(1.0, 0.02 / (volatility + 1e-6)))  # Scale based on volatility
        return base * scale