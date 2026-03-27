"""
Portfolio Analytics Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class PortfolioAnalyzer:
    """Portfolio-level analytics and risk management"""

    def __init__(self):
        self.positions = {}
        self.history = []

    def update_position(self, symbol: str, quantity: float, price: float, timestamp: datetime = None):
        """Update position for a symbol"""
        if timestamp is None:
            timestamp = datetime.utcnow()

        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0
            }

        position = self.positions[symbol]

        if quantity > 0:  # Buy
            total_quantity = position['quantity'] + quantity
            total_cost = position['total_cost'] + (quantity * price)

            position['quantity'] = total_quantity
            position['avg_price'] = total_cost / total_quantity if total_quantity > 0 else 0
            position['total_cost'] = total_cost

        else:  # Sell
            sell_quantity = abs(quantity)
            sell_value = sell_quantity * price

            # Calculate P&L
            cost_basis = sell_quantity * position['avg_price']
            pnl = sell_value - cost_basis

            position['quantity'] -= sell_quantity
            position['total_cost'] -= cost_basis

            # Record trade
            self.history.append({
                'symbol': symbol,
                'side': 'SELL',
                'quantity': sell_quantity,
                'price': price,
                'pnl': pnl,
                'timestamp': timestamp
            })

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate current portfolio value"""
        total_value = 0
        positions_value = {}

        for symbol, position in self.positions.items():
            if position['quantity'] > 0:
                current_price = current_prices.get(symbol, position['avg_price'])
                value = position['quantity'] * current_price
                positions_value[symbol] = {
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': current_price,
                    'value': value,
                    'pnl': (current_price - position['avg_price']) * position['quantity']
                }
                total_value += value

        return {
            'total_value': total_value,
            'positions': positions_value,
            'cash': 0,  # Would be tracked separately
            'timestamp': datetime.utcnow()
        }

    def get_portfolio_risk(self, returns: pd.DataFrame) -> Dict:
        """Calculate portfolio risk metrics"""
        if returns.empty:
            return {}

        # Portfolio returns (equal weighted for simplicity)
        portfolio_returns = returns.mean(axis=1)

        # Risk metrics
        volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
        var_95 = portfolio_returns.quantile(0.05)
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)

        # Correlation matrix
        correlation = returns.corr()

        return {
            'volatility': volatility,
            'var_95': var_95,
            'max_drawdown': max_drawdown,
            'correlation_matrix': correlation.to_dict(),
            'diversification_ratio': self._calculate_diversification_ratio(correlation)
        }

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_diversification_ratio(self, correlation: pd.DataFrame) -> float:
        """Calculate diversification ratio"""
        n = len(correlation)
        if n <= 1:
            return 1.0

        avg_correlation = correlation.values[np.triu_indices(n, k=1)].mean()
        return 1 / np.sqrt(avg_correlation) if avg_correlation > 0 else 1.0