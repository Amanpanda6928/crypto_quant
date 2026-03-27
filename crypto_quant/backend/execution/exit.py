"""
Exit Strategy Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging


class ExitReason(Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    SIGNAL_REVERSE = "signal_reverse"
    MAX_HOLD_TIME = "max_hold_time"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"


@dataclass
class ExitRule:
    """Represents an exit rule configuration."""
    rule_type: str
    parameters: Dict
    enabled: bool = True


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    entry_price: float
    entry_time: datetime
    quantity: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    highest_price: float = 0.0  # For trailing stops
    lowest_price: float = float('inf')  # For trailing stops


class ExitStrategy:
    """
    Manages exit strategies for trading positions.

    Implements various exit rules including take profit, stop loss,
    trailing stops, and time-based exits.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize exit strategy manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        self.exit_rules = self._initialize_exit_rules()

    def _get_default_config(self) -> Dict:
        """Get default exit strategy configuration."""
        return {
            'take_profit_pct': 0.05,      # 5% take profit
            'stop_loss_pct': 0.03,        # 3% stop loss
            'trailing_stop_pct': 0.02,    # 2% trailing stop
            'max_hold_hours': 24,         # Max 24 hours hold time
            'time_decay_factor': 0.001,   # Time-based exit factor
            'volatility_adjustment': True, # Adjust exits based on volatility
            'partial_exits': True,        # Allow partial position exits
            'exit_priority': ['stop_loss', 'take_profit', 'trailing_stop', 'time_exit']
        }

    def _initialize_exit_rules(self) -> Dict[str, ExitRule]:
        """Initialize exit rules."""
        rules = {}

        # Take profit rule
        rules['take_profit'] = ExitRule(
            rule_type='take_profit',
            parameters={
                'profit_pct': self.config['take_profit_pct'],
                'partial_exit_pct': 0.5 if self.config['partial_exits'] else 1.0
            }
        )

        # Stop loss rule
        rules['stop_loss'] = ExitRule(
            rule_type='stop_loss',
            parameters={
                'loss_pct': self.config['stop_loss_pct']
            }
        )

        # Trailing stop rule
        rules['trailing_stop'] = ExitRule(
            rule_type='trailing_stop',
            parameters={
                'trail_pct': self.config['trailing_stop_pct'],
                'activation_profit_pct': 0.02  # Activate after 2% profit
            }
        )

        # Time-based exit rule
        rules['time_exit'] = ExitRule(
            rule_type='time_exit',
            parameters={
                'max_hold_hours': self.config['max_hold_hours'],
                'decay_factor': self.config['time_decay_factor']
            }
        )

        # Signal reverse rule
        rules['signal_reverse'] = ExitRule(
            rule_type='signal_reverse',
            parameters={
                'reverse_threshold': 0.1  # Exit if signal reverses by 10%
            }
        )

        return rules

    def should_exit(self, position: Position, current_signal: Optional[float] = None,
                   market_data: Optional[pd.DataFrame] = None) -> Tuple[bool, ExitReason, float]:
        """
        Determine if a position should be exited.

        Args:
            position: Current position
            current_signal: Current trading signal (-1 to 1)
            market_data: Recent market data for analysis

        Returns:
            Tuple of (should_exit, exit_reason, exit_percentage)
        """
        # Check exit rules in priority order
        for rule_name in self.config['exit_priority']:
            if rule_name in self.exit_rules and self.exit_rules[rule_name].enabled:
                should_exit, exit_pct = self._check_rule(
                    self.exit_rules[rule_name], position, current_signal, market_data
                )

                if should_exit:
                    return True, ExitReason(rule_name.upper()), exit_pct

        return False, None, 0.0

    def _check_rule(self, rule: ExitRule, position: Position,
                   current_signal: Optional[float], market_data: Optional[pd.DataFrame]) -> Tuple[bool, float]:
        """
        Check if a specific exit rule is triggered.

        Args:
            rule: Exit rule to check
            position: Current position
            current_signal: Current signal
            market_data: Market data

        Returns:
            Tuple of (rule_triggered, exit_percentage)
        """
        rule_type = rule.rule_type
        params = rule.parameters

        if rule_type == 'take_profit':
            profit_pct = (position.current_price - position.entry_price) / position.entry_price
            if profit_pct >= params['profit_pct']:
                return True, params.get('partial_exit_pct', 1.0)

        elif rule_type == 'stop_loss':
            loss_pct = (position.entry_price - position.current_price) / position.entry_price
            if loss_pct >= params['loss_pct']:
                return True, 1.0  # Full exit on stop loss

        elif rule_type == 'trailing_stop':
            # Update highest/lowest price
            position.highest_price = max(position.highest_price, position.current_price)

            # Check if trailing stop is activated
            activation_profit = (position.highest_price - position.entry_price) / position.entry_price
            if activation_profit >= params['activation_profit_pct']:
                # Calculate trailing stop price
                trail_price = position.highest_price * (1 - params['trail_pct'])
                if position.current_price <= trail_price:
                    return True, 1.0

        elif rule_type == 'time_exit':
            hold_time = datetime.now() - position.entry_time
            hold_hours = hold_time.total_seconds() / 3600

            if hold_hours >= params['max_hold_hours']:
                return True, 1.0

            # Time-based decay (optional)
            if params.get('decay_factor', 0) > 0:
                time_factor = 1 - (hold_hours / params['max_hold_hours']) * params['decay_factor']
                if np.random.random() > time_factor:
                    return True, 0.5  # Partial exit

        elif rule_type == 'signal_reverse':
            if current_signal is not None:
                # Simple signal reversal detection
                # In practice, this would compare to entry signal
                entry_signal = getattr(position, 'entry_signal', 0)
                signal_change = abs(current_signal - entry_signal)
                if signal_change >= params['reverse_threshold']:
                    return True, 1.0

        return False, 0.0

    def calculate_optimal_exit_price(self, position: Position,
                                   exit_reason: ExitReason,
                                   market_data: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate optimal exit price based on exit reason.

        Args:
            position: Position to exit
            exit_reason: Reason for exit
            market_data: Market data for analysis

        Returns:
            Optimal exit price
        """
        current_price = position.current_price

        if exit_reason == ExitReason.TAKE_PROFIT:
            # Take profit at current price
            return current_price

        elif exit_reason == ExitReason.STOP_LOSS:
            # Stop loss at configured percentage
            stop_pct = self.exit_rules['stop_loss'].parameters['loss_pct']
            return position.entry_price * (1 - stop_pct)

        elif exit_reason == ExitReason.TRAILING_STOP:
            # Trailing stop price
            trail_pct = self.exit_rules['trailing_stop'].parameters['trail_pct']
            return position.highest_price * (1 - trail_pct)

        elif exit_reason == ExitReason.TIME_EXIT:
            # Time exit at current price with small discount
            return current_price * 0.998  # 0.2% discount for quick exit

        else:
            # Default to current price
            return current_price

    def update_position(self, position: Position, current_price: float,
                       current_signal: Optional[float] = None):
        """
        Update position with latest market data.

        Args:
            position: Position to update
            current_price: Current market price
            current_signal: Current trading signal
        """
        position.current_price = current_price
        position.unrealized_pnl = (current_price - position.entry_price) * position.quantity

        # Update trailing stop levels
        if 'trailing_stop' in self.exit_rules and self.exit_rules['trailing_stop'].enabled:
            position.highest_price = max(position.highest_price, current_price)
            position.lowest_price = min(position.lowest_price, current_price)

    def get_exit_rules_status(self) -> pd.DataFrame:
        """
        Get status of all exit rules.

        Returns:
            DataFrame with exit rules status
        """
        rules_data = []

        for rule_name, rule in self.exit_rules.items():
            rules_data.append({
                'rule_name': rule_name,
                'enabled': rule.enabled,
                'parameters': str(rule.parameters)
            })

        return pd.DataFrame(rules_data)

    def adjust_rules_for_volatility(self, volatility: float, base_volatility: float = 0.02):
        """
        Adjust exit rules based on current market volatility.

        Args:
            volatility: Current market volatility
            base_volatility: Base volatility level
        """
        if not self.config.get('volatility_adjustment', False):
            return

        # Increase stops in high volatility
        vol_multiplier = volatility / base_volatility

        # Adjust stop loss (wider in high vol)
        if 'stop_loss' in self.exit_rules:
            base_stop = self.config['stop_loss_pct']
            adjusted_stop = base_stop * vol_multiplier
            self.exit_rules['stop_loss'].parameters['loss_pct'] = min(adjusted_stop, base_stop * 2)

        # Adjust take profit (higher in high vol)
        if 'take_profit' in self.exit_rules:
            base_tp = self.config['take_profit_pct']
            adjusted_tp = base_tp * vol_multiplier
            self.exit_rules['take_profit'].parameters['profit_pct'] = max(adjusted_tp, base_tp * 0.5)

        self.logger.info(f"Exit rules adjusted for volatility: {volatility:.4f} (multiplier: {vol_multiplier:.2f})")

    def simulate_exit_scenarios(self, position: Position,
                              price_range: Tuple[float, float],
                              num_scenarios: int = 100) -> pd.DataFrame:
        """
        Simulate different exit scenarios.

        Args:
            position: Position to simulate
            price_range: (min_price, max_price) range
            num_scenarios: Number of scenarios to simulate

        Returns:
            DataFrame with simulation results
        """
        min_price, max_price = price_range
        scenarios = []

        for i in range(num_scenarios):
            # Random exit price
            exit_price = np.random.uniform(min_price, max_price)

            # Update position with exit price
            temp_position = Position(
                symbol=position.symbol,
                entry_price=position.entry_price,
                entry_time=position.entry_time,
                quantity=position.quantity,
                current_price=exit_price
            )

            # Check exit conditions
            should_exit, exit_reason, exit_pct = self.should_exit(temp_position)

            if should_exit:
                pnl = (exit_price - position.entry_price) * position.quantity * exit_pct
                scenarios.append({
                    'scenario_id': i,
                    'exit_price': exit_price,
                    'exit_reason': exit_reason.value if exit_reason else None,
                    'exit_pct': exit_pct,
                    'pnl': pnl,
                    'pnl_pct': pnl / (position.entry_price * position.quantity)
                })

        return pd.DataFrame(scenarios)


if __name__ == "__main__":
    # Example usage
    exit_strategy = ExitStrategy()

    # Create a sample position
    position = Position(
        symbol='BTCUSDT',
        entry_price=50000,
        entry_time=datetime.now() - timedelta(hours=2),
        quantity=0.1,
        current_price=52500,  # 5% profit
        highest_price=53000
    )

    # Check if should exit
    should_exit, reason, exit_pct = exit_strategy.should_exit(position)

    print(f"Should exit: {should_exit}")
    if should_exit:
        print(f"Reason: {reason.value}, Exit %: {exit_pct}")

    # Get exit rules status
    rules_status = exit_strategy.get_exit_rules_status()
    print("\nExit rules status:")
    print(rules_status)

    # Simulate exit scenarios
    scenarios = exit_strategy.simulate_exit_scenarios(
        position, (48000, 54000), num_scenarios=50
    )

    if not scenarios.empty:
        print(f"\nExit scenarios summary:")
        print(f"Average PnL: ${scenarios['pnl'].mean():.2f}")
        print(f"Exit reason distribution:")
        print(scenarios['exit_reason'].value_counts())