"""
Advanced Backtest Engine with Walk-Forward Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from ..analytics.performance import PerformanceAnalyzer
from ..analytics.portfolio import PortfolioAnalyzer

class AdvancedBacktestEngine:
    """Advanced backtesting with walk-forward analysis and risk management"""

    def __init__(self,
                 initial_capital: float = 10000,
                 commission: float = 0.001,
                 slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        self.performance_analyzer = PerformanceAnalyzer()
        self.portfolio_analyzer = PortfolioAnalyzer()

        self.results = []

    def run_walk_forward(self,
                        data: pd.DataFrame,
                        signals: pd.DataFrame,
                        train_window: int = 2000,
                        test_window: int = 500,
                        step_size: int = 250) -> Dict:
        """Run walk-forward backtest"""

        results = []
        start_idx = 0

        while start_idx + train_window + test_window <= len(data):
            # Define train/test periods
            train_end = start_idx + train_window
            test_end = train_end + test_window

            train_data = data.iloc[start_idx:train_end]
            test_data = data.iloc[train_end:test_end]

            # Get signals for test period
            test_signals = signals[
                (signals['timestamp'] >= test_data.index[0]) &
                (signals['timestamp'] <= test_data.index[-1])
            ]

            # Run backtest on test period
            result = self.run_single_backtest(test_data, test_signals)
            results.append(result)

            start_idx += step_size

        # Aggregate results
        return self._aggregate_results(results)

    def run_single_backtest(self, data: pd.DataFrame, signals: pd.DataFrame) -> Dict:
        """Run single backtest period"""

        capital = self.initial_capital
        positions = {}
        trades = []

        for idx, row in data.iterrows():
            symbol = row['symbol']
            price = row['close']
            timestamp = idx

            # Check for signals
            symbol_signals = signals[
                (signals['symbol'] == symbol) &
                (signals['timestamp'] == timestamp)
            ]

            if not symbol_signals.empty:
                signal = symbol_signals.iloc[0]['signal']
                confidence = symbol_signals.iloc[0]['confidence']

                # Execute trade based on signal
                if signal == 'BUY' and symbol not in positions:
                    # Calculate position size
                    position_size = self._calculate_position_size(capital, price, confidence)

                    if position_size > 0:
                        # Apply slippage and commission
                        execution_price = price * (1 + self.slippage)
                        commission_cost = position_size * execution_price * self.commission

                        if capital >= (position_size * execution_price + commission_cost):
                            # Execute buy
                            positions[symbol] = {
                                'quantity': position_size,
                                'entry_price': execution_price,
                                'entry_time': timestamp
                            }

                            capital -= (position_size * execution_price + commission_cost)

                            trades.append({
                                'symbol': symbol,
                                'side': 'BUY',
                                'quantity': position_size,
                                'price': execution_price,
                                'timestamp': timestamp,
                                'commission': commission_cost
                            })

                elif signal == 'SELL' and symbol in positions:
                    position = positions[symbol]
                    quantity = position['quantity']
                    entry_price = position['entry_price']

                    # Apply slippage and commission
                    execution_price = price * (1 - self.slippage)
                    commission_cost = quantity * execution_price * self.commission

                    # Calculate P&L
                    gross_pnl = (execution_price - entry_price) * quantity
                    net_pnl = gross_pnl - commission_cost

                    capital += (quantity * execution_price - commission_cost)

                    trades.append({
                        'symbol': symbol,
                        'side': 'SELL',
                        'quantity': quantity,
                        'price': execution_price,
                        'pnl': net_pnl,
                        'timestamp': timestamp,
                        'commission': commission_cost
                    })

                    del positions[symbol]

        # Calculate final portfolio value
        final_value = capital
        for symbol, position in positions.items():
            # Assume exit at last price
            last_price = data[data['symbol'] == symbol]['close'].iloc[-1]
            final_value += position['quantity'] * last_price

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital,
            'trades': trades,
            'final_positions': positions
        }

    def _calculate_position_size(self, capital: float, price: float, confidence: float) -> float:
        """Calculate position size based on capital and confidence"""
        # Simple position sizing: risk 1% of capital per trade
        risk_amount = capital * 0.01
        stop_loss_pct = 0.02  # 2% stop loss

        # Adjust position size based on confidence
        confidence_multiplier = confidence

        position_value = risk_amount / stop_loss_pct * confidence_multiplier
        position_size = position_value / price

        return position_size

    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate walk-forward results"""
        if not results:
            return {}

        total_return = np.mean([r['total_return'] for r in results])
        total_trades = sum(len(r['trades']) for r in results)

        # Calculate Sharpe ratio, max drawdown, etc.
        returns_series = pd.Series([r['total_return'] for r in results])

        return {
            'total_periods': len(results),
            'average_return': total_return,
            'total_trades': total_trades,
            'sharpe_ratio': self.performance_analyzer.calculate_sharpe_ratio(returns_series),
            'max_drawdown': self.performance_analyzer.calculate_max_drawdown(pd.Series([1 + r for r in [r['total_return'] for r in results]])),
            'win_rate': self.performance_analyzer.calculate_win_rate(pd.DataFrame([t for r in results for t in r['trades']])),
            'period_results': results
        }