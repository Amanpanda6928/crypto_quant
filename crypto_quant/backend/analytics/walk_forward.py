"""
Walk-Forward Analysis Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .backtest_engine import AdvancedBacktestEngine

class WalkForwardAnalyzer:
    """Walk-forward analysis for strategy validation"""

    def __init__(self,
                 min_train_periods: int = 1000,
                 test_periods: int = 250,
                 step_size: int = 125,
                 confidence_threshold: float = 0.95):
        self.min_train_periods = min_train_periods
        self.test_periods = test_periods
        self.step_size = step_size
        self.confidence_threshold = confidence_threshold

        self.backtest_engine = AdvancedBacktestEngine()

    def analyze_strategy(self,
                        data: pd.DataFrame,
                        strategy_func,
                        **strategy_params) -> Dict:
        """Run walk-forward analysis on a strategy"""

        results = []
        start_idx = 0

        while start_idx + self.min_train_periods + self.test_periods <= len(data):
            # Training period
            train_end = start_idx + self.min_train_periods
            train_data = data.iloc[start_idx:train_end]

            # Test period
            test_start = train_end
            test_end = test_start + self.test_periods
            test_data = data.iloc[test_start:test_end]

            # Train strategy on training data
            strategy_model = strategy_func(train_data, **strategy_params)

            # Generate signals on test data
            signals = self._generate_signals(strategy_model, test_data)

            # Backtest on test period
            backtest_result = self.backtest_engine.run_single_backtest(test_data, signals)

            # Store results
            results.append({
                'train_period': (start_idx, train_end),
                'test_period': (test_start, test_end),
                'backtest_result': backtest_result,
                'strategy_model': strategy_model
            })

            start_idx += self.step_size

        # Analyze overall results
        return self._analyze_walk_forward_results(results)

    def _generate_signals(self, strategy_model, test_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from strategy model"""
        signals = []

        for idx, row in test_data.iterrows():
            # This would depend on the specific strategy
            # For now, return empty signals
            signal = {
                'timestamp': idx,
                'symbol': row['symbol'],
                'signal': 'HOLD',
                'confidence': 0.5
            }
            signals.append(signal)

        return pd.DataFrame(signals)

    def _analyze_walk_forward_results(self, results: List[Dict]) -> Dict:
        """Analyze walk-forward results for statistical significance"""

        if not results:
            return {}

        # Extract returns
        returns = [r['backtest_result']['total_return'] for r in results]

        # Statistical tests
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        t_stat = mean_return / (std_return / np.sqrt(len(returns))) if std_return > 0 else 0

        # Confidence interval
        confidence_interval = self._calculate_confidence_interval(returns)

        # Probability of positive returns
        prob_positive = np.mean([r > 0 for r in returns])

        # Maximum consecutive losses
        consecutive_losses = self._calculate_max_consecutive_losses(returns)

        return {
            'total_periods': len(results),
            'mean_return': mean_return,
            'std_return': std_return,
            't_statistic': t_stat,
            'p_value': self._calculate_p_value(t_stat, len(results)),
            'confidence_interval': confidence_interval,
            'probability_positive': prob_positive,
            'max_consecutive_losses': consecutive_losses,
            'is_significant': abs(t_stat) > 1.96,  # 95% confidence
            'detailed_results': results
        }

    def _calculate_confidence_interval(self, returns: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for returns"""
        mean = np.mean(returns)
        std = np.std(returns)
        n = len(returns)

        # t-distribution critical value (approximate)
        t_critical = 1.96  # 95% confidence

        margin_error = t_critical * (std / np.sqrt(n))

        return (mean - margin_error, mean + margin_error)

    def _calculate_p_value(self, t_stat: float, n: int) -> float:
        """Calculate approximate p-value"""
        # Simplified calculation
        if abs(t_stat) < 1.96:
            return 0.05  # Not significant
        elif abs(t_stat) < 2.58:
            return 0.01  # Significant at 95%
        else:
            return 0.001  # Highly significant

    def _calculate_max_consecutive_losses(self, returns: List[float]) -> int:
        """Calculate maximum consecutive losses"""
        max_consecutive = 0
        current_consecutive = 0

        for r in returns:
            if r <= 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive