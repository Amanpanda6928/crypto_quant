"""
Daily Risk Limits Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum


class RiskLimitType(Enum):
    DAILY_LOSS = "daily_loss"
    DAILY_VOLUME = "daily_volume"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_POSITIONS = "max_positions"
    SINGLE_TRADE_LOSS = "single_trade_loss"


@dataclass
class RiskLimit:
    """Represents a risk limit configuration."""
    limit_type: RiskLimitType
    value: float
    current: float = 0.0
    breaches: int = 0
    last_breach: Optional[datetime] = None


class DailyRiskLimits:
    """
    Manages daily risk limits for trading operations.

    Tracks various risk metrics and enforces limits to prevent
    excessive losses or over-trading.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize daily risk limits.

        Args:
            config: Dictionary with limit configurations
        """
        self.config = config or self._get_default_config()
        self.limits = self._initialize_limits()
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self._check_daily_reset()

    def _get_default_config(self) -> Dict:
        """Get default risk limit configuration."""
        return {
            'daily_loss_limit': 0.05,  # 5% of capital
            'daily_volume_limit': 1000000,  # $1M daily volume
            'max_drawdown_limit': 0.10,  # 10% max drawdown
            'max_positions_limit': 10,  # Max 10 concurrent positions
            'single_trade_loss_limit': 0.02,  # 2% loss per trade
            'breach_cooldown_hours': 1,  # Hours to wait after breach
        }

    def _initialize_limits(self) -> Dict[RiskLimitType, RiskLimit]:
        """Initialize risk limit objects."""
        limits = {}

        config_map = {
            RiskLimitType.DAILY_LOSS: 'daily_loss_limit',
            RiskLimitType.DAILY_VOLUME: 'daily_volume_limit',
            RiskLimitType.MAX_DRAWDOWN: 'max_drawdown_limit',
            RiskLimitType.MAX_POSITIONS: 'max_positions_limit',
            RiskLimitType.SINGLE_TRADE_LOSS: 'single_trade_loss_limit',
        }

        for limit_type, config_key in config_map.items():
            limits[limit_type] = RiskLimit(
                limit_type=limit_type,
                value=self.config[config_key]
            )

        return limits

    def _check_daily_reset(self):
        """Reset daily limits if it's a new day."""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self._reset_daily_limits()
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def _reset_daily_limits(self):
        """Reset daily accumulative limits."""
        for limit in self.limits.values():
            if limit.limit_type in [RiskLimitType.DAILY_LOSS, RiskLimitType.DAILY_VOLUME]:
                limit.current = 0.0
                limit.breaches = 0
                limit.last_breach = None

    def update_daily_loss(self, loss_amount: float) -> bool:
        """
        Update daily loss accumulator.

        Args:
            loss_amount: Loss amount (positive for losses)

        Returns:
            True if within limits, False if breached
        """
        self._check_daily_reset()
        limit = self.limits[RiskLimitType.DAILY_LOSS]

        if loss_amount > 0:
            limit.current += loss_amount

        return self._check_limit(limit)

    def update_daily_volume(self, volume: float) -> bool:
        """
        Update daily volume accumulator.

        Args:
            volume: Trading volume

        Returns:
            True if within limits, False if breached
        """
        self._check_daily_reset()
        limit = self.limits[RiskLimitType.DAILY_VOLUME]
        limit.current += volume

        return self._check_limit(limit)

    def check_single_trade_loss(self, trade_loss_pct: float) -> bool:
        """
        Check if a single trade loss exceeds limits.

        Args:
            trade_loss_pct: Trade loss as percentage

        Returns:
            True if within limits, False if breached
        """
        limit = self.limits[RiskLimitType.SINGLE_TRADE_LOSS]
        return abs(trade_loss_pct) <= limit.value

    def check_max_positions(self, current_positions: int) -> bool:
        """
        Check if current positions exceed limit.

        Args:
            current_positions: Number of current positions

        Returns:
            True if within limits, False if breached
        """
        limit = self.limits[RiskLimitType.MAX_POSITIONS]
        return current_positions <= limit.value

    def check_max_drawdown(self, current_drawdown_pct: float) -> bool:
        """
        Check if current drawdown exceeds limit.

        Args:
            current_drawdown_pct: Current drawdown as percentage

        Returns:
            True if within limits, False if breached
        """
        limit = self.limits[RiskLimitType.MAX_DRAWDOWN]
        return abs(current_drawdown_pct) <= limit.value

    def _check_limit(self, limit: RiskLimit) -> bool:
        """
        Check if a limit is breached and handle breach logic.

        Args:
            limit: RiskLimit object to check

        Returns:
            True if within limits, False if breached
        """
        if limit.current > limit.value:
            limit.breaches += 1
            limit.last_breach = datetime.now()

            # Check cooldown period
            if limit.last_breach:
                cooldown_hours = self.config.get('breach_cooldown_hours', 1)
                cooldown_end = limit.last_breach + timedelta(hours=cooldown_hours)
                if datetime.now() < cooldown_end:
                    return False

            return False

        return True

    def get_limit_status(self) -> pd.DataFrame:
        """
        Get current status of all risk limits.

        Returns:
            DataFrame with limit status information
        """
        status_data = []

        for limit in self.limits.values():
            status_data.append({
                'limit_type': limit.limit_type.value,
                'limit_value': limit.value,
                'current_value': limit.current,
                'utilization_pct': (limit.current / limit.value * 100) if limit.value > 0 else 0,
                'breaches': limit.breaches,
                'last_breach': limit.last_breach,
                'is_breached': limit.current > limit.value
            })

        return pd.DataFrame(status_data)

    def can_trade(self, trade_params: Dict) -> Tuple[bool, List[str]]:
        """
        Comprehensive check if trading is allowed.

        Args:
            trade_params: Dictionary with trade parameters
                - 'current_positions': int
                - 'current_drawdown_pct': float
                - 'proposed_volume': float
                - 'proposed_loss_pct': float (optional)

        Returns:
            Tuple of (can_trade, reasons_if_not)
        """
        reasons = []

        # Check position limit
        if 'current_positions' in trade_params:
            if not self.check_max_positions(trade_params['current_positions']):
                reasons.append("Maximum positions limit reached")

        # Check drawdown limit
        if 'current_drawdown_pct' in trade_params:
            if not self.check_max_drawdown(trade_params['current_drawdown_pct']):
                reasons.append("Maximum drawdown limit exceeded")

        # Check single trade loss
        if 'proposed_loss_pct' in trade_params:
            if not self.check_single_trade_loss(trade_params['proposed_loss_pct']):
                reasons.append("Single trade loss limit would be exceeded")

        # Check daily volume
        if 'proposed_volume' in trade_params:
            if not self.update_daily_volume(0):  # Check current status
                temp_limit = RiskLimit(
                    limit_type=RiskLimitType.DAILY_VOLUME,
                    value=self.limits[RiskLimitType.DAILY_VOLUME].value,
                    current=self.limits[RiskLimitType.DAILY_VOLUME].current + trade_params['proposed_volume']
                )
                if not self._check_limit(temp_limit):
                    reasons.append("Daily volume limit would be exceeded")

        can_trade = len(reasons) == 0
        return can_trade, reasons

    def get_risk_summary(self) -> Dict:
        """
        Get a summary of current risk status.

        Returns:
            Dictionary with risk summary
        """
        status_df = self.get_limit_status()

        return {
            'overall_risk_level': 'HIGH' if status_df['is_breached'].any() else 'NORMAL',
            'breached_limits': status_df[status_df['is_breached']]['limit_type'].tolist(),
            'highest_utilization': status_df['utilization_pct'].max(),
            'total_breaches_today': status_df['breaches'].sum(),
            'limits_status': status_df.to_dict('records')
        }


if __name__ == "__main__":
    # Example usage
    risk_limits = DailyRiskLimits()

    # Test various checks
    print("Initial status:")
    print(risk_limits.get_limit_status())

    # Test trading permission
    trade_params = {
        'current_positions': 3,
        'current_drawdown_pct': 0.02,
        'proposed_volume': 50000,
        'proposed_loss_pct': 0.015
    }

    can_trade, reasons = risk_limits.can_trade(trade_params)
    print(f"\nCan trade: {can_trade}")
    if not can_trade:
        print(f"Reasons: {reasons}")

    # Test risk summary
    summary = risk_limits.get_risk_summary()
    print(f"\nRisk summary: {summary}")