"""
Time-Weighted Average Price (TWAP) Execution Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
import logging


class TWAPState(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class TWAPOrder:
    """Represents a TWAP order."""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    total_quantity: float
    duration_minutes: int
    start_time: datetime
    end_time: datetime
    interval_seconds: int = 60  # Execute every 60 seconds
    max_slippage_pct: float = 0.005  # 0.5% max slippage per slice
    state: TWAPState = TWAPState.PENDING

    # Execution tracking
    executed_quantity: float = 0.0
    remaining_quantity: float = 0.0
    total_cost: float = 0.0
    total_fees: float = 0.0
    avg_price: float = 0.0
    slices_executed: int = 0
    slices_total: int = 0

    def __post_init__(self):
        self.remaining_quantity = self.total_quantity
        self.slices_total = max(1, int(self.duration_minutes * 60 / self.interval_seconds))


@dataclass
class TWAPSlice:
    """Represents a single slice of a TWAP order."""
    slice_id: str
    order_id: str
    quantity: float
    target_price: float
    executed_price: float = 0.0
    executed_quantity: float = 0.0
    timestamp: datetime = None
    success: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TWAPExecutor:
    """
    Time-Weighted Average Price execution strategy.

    Breaks large orders into smaller slices executed at regular intervals
    to minimize market impact and achieve better average pricing.
    """

    def __init__(self, exchange_api=None, config: Optional[Dict] = None):
        """
        Initialize TWAP executor.

        Args:
            exchange_api: Exchange API client
            config: Configuration dictionary
        """
        self.exchange_api = exchange_api
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)

        # Order tracking
        self.active_orders = {}  # order_id -> TWAPOrder
        self.completed_orders = []
        self.failed_orders = []

    def _get_default_config(self) -> Dict:
        """Get default TWAP configuration."""
        return {
            'min_order_size': 100,      # Minimum order size in USD
            'max_slice_pct': 0.05,      # Max 5% of total order per slice
            'default_interval': 60,     # 60 seconds between slices
            'max_slippage_pct': 0.01,   # 1% max slippage
            'randomize_timing': True,   # Add randomness to execution timing
            'max_concurrent_orders': 5, # Max concurrent TWAP orders
        }

    def submit_twap_order(self, symbol: str, side: str, quantity: float,
                         duration_minutes: int, interval_seconds: Optional[int] = None,
                         max_slippage_pct: Optional[float] = None) -> TWAPOrder:
        """
        Submit a TWAP order.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Total quantity to execute
            duration_minutes: Total execution time in minutes
            interval_seconds: Time between slices (optional)
            max_slippage_pct: Maximum slippage per slice (optional)

        Returns:
            TWAPOrder object
        """
        # Validate inputs
        self._validate_twap_order(symbol, side, quantity, duration_minutes)

        # Check concurrent orders limit
        if len(self.active_orders) >= self.config['max_concurrent_orders']:
            raise ValueError(f"Maximum concurrent TWAP orders ({self.config['max_concurrent_orders']}) reached")

        # Create TWAP order
        order_id = f"twap_{int(time.time() * 1000)}"
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        order = TWAPOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            duration_minutes=duration_minutes,
            start_time=start_time,
            end_time=end_time,
            interval_seconds=interval_seconds or self.config['default_interval'],
            max_slippage_pct=max_slippage_pct or self.config['max_slippage_pct']
        )

        # Start execution
        order.state = TWAPState.EXECUTING
        self.active_orders[order_id] = order

        self.logger.info(f"TWAP order {order_id} started: {quantity} {symbol} over {duration_minutes} minutes")

        return order

    def _validate_twap_order(self, symbol: str, side: str, quantity: float, duration_minutes: int):
        """Validate TWAP order parameters."""
        if side not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if duration_minutes < 1:
            raise ValueError("Duration must be at least 1 minute")

        # Check minimum order size
        estimated_value = quantity * self._get_market_price(symbol)
        if estimated_value < self.config['min_order_size']:
            raise ValueError(f"Order value ${estimated_value:.2f} below minimum ${self.config['min_order_size']}")

    def _get_market_price(self, symbol: str) -> float:
        """Get current market price (simulated)."""
        # In real implementation, this would call exchange API
        base_prices = {
            'BTCUSDT': 50000,
            'ETHUSDT': 3000,
            'ADAUSDT': 2.0,
            'SOLUSDT': 100,
            'DOTUSDT': 20
        }
        return base_prices.get(symbol, 100)

    def execute_twap_slice(self, order: TWAPOrder) -> Optional[TWAPSlice]:
        """
        Execute a single slice of a TWAP order.

        Args:
            order: TWAPOrder to execute slice for

        Returns:
            TWAPSlice result or None if order complete
        """
        if order.remaining_quantity <= 0:
            return None

        # Calculate slice size
        slice_quantity = self._calculate_slice_quantity(order)

        if slice_quantity <= 0:
            return None

        # Get target price
        target_price = self._get_market_price(order.symbol)

        # Execute slice
        slice_result = self._execute_slice(order, slice_quantity, target_price)

        # Update order tracking
        order.slices_executed += 1
        order.executed_quantity += slice_result.executed_quantity
        order.remaining_quantity -= slice_result.executed_quantity
        order.total_cost += slice_result.executed_price * slice_result.executed_quantity

        # Update average price
        if order.executed_quantity > 0:
            order.avg_price = order.total_cost / order.executed_quantity

        # Check if order is complete
        if order.remaining_quantity <= 0.001:  # Allow small tolerance
            order.state = TWAPState.COMPLETED
            order.remaining_quantity = 0
            self._complete_twap_order(order)

        return slice_result

    def _calculate_slice_quantity(self, order: TWAPOrder) -> float:
        """
        Calculate quantity for next slice.

        Args:
            order: TWAPOrder

        Returns:
            Slice quantity
        """
        remaining_slices = order.slices_total - order.slices_executed

        if remaining_slices <= 0:
            return 0

        # Base quantity per slice
        base_slice_quantity = order.total_quantity / order.slices_total

        # Apply maximum slice percentage limit
        max_slice_quantity = order.total_quantity * self.config['max_slice_pct']
        slice_quantity = min(base_slice_quantity, max_slice_quantity)

        # Don't exceed remaining quantity
        slice_quantity = min(slice_quantity, order.remaining_quantity)

        return slice_quantity

    def _execute_slice(self, order: TWAPOrder, quantity: float, target_price: float) -> TWAPSlice:
        """
        Execute a single slice.

        Args:
            order: TWAPOrder
            quantity: Slice quantity
            target_price: Target execution price

        Returns:
            TWAPSlice result
        """
        slice_id = f"{order.order_id}_slice_{order.slices_executed + 1}"

        # Simulate execution with slippage
        slippage = np.random.uniform(-order.max_slippage_pct, order.max_slippage_pct)
        executed_price = target_price * (1 + slippage)

        # Simulate partial fills (small chance)
        if np.random.random() < 0.05:  # 5% chance of partial fill
            executed_quantity = quantity * np.random.uniform(0.5, 0.95)
        else:
            executed_quantity = quantity

        # Calculate fees (0.1%)
        fees = executed_price * executed_quantity * 0.001
        order.total_fees += fees

        slice_result = TWAPSlice(
            slice_id=slice_id,
            order_id=order.order_id,
            quantity=quantity,
            target_price=target_price,
            executed_price=executed_price,
            executed_quantity=executed_quantity,
            success=True
        )

        self.logger.debug(f"TWAP slice executed: {slice_result.executed_quantity:.4f} @ ${executed_price:.4f}")

        return slice_result

    def _complete_twap_order(self, order: TWAPOrder):
        """Handle TWAP order completion."""
        self.logger.info(f"TWAP order {order.order_id} completed: "
                        f"{order.executed_quantity:.4f}/{order.total_quantity:.4f} "
                        f"at avg price ${order.avg_price:.4f}")

        # Move to completed orders
        completed_order = self.active_orders.pop(order.order_id)
        self.completed_orders.append(completed_order)

    def cancel_twap_order(self, order_id: str) -> bool:
        """
        Cancel a TWAP order.

        Args:
            order_id: TWAP order ID

        Returns:
            True if cancelled successfully
        """
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order.state = TWAPState.CANCELLED
            self.logger.info(f"TWAP order {order_id} cancelled")
            return True

        return False

    def get_twap_status(self, order_id: str) -> Optional[TWAPOrder]:
        """
        Get status of a TWAP order.

        Args:
            order_id: TWAP order ID

        Returns:
            TWAPOrder object or None
        """
        return self.active_orders.get(order_id)

    def process_active_orders(self):
        """Process all active TWAP orders (execute due slices)."""
        current_time = datetime.now()

        for order_id, order in list(self.active_orders.items()):
            if order.state != TWAPState.EXECUTING:
                continue

            # Check if order should still be executing
            if current_time > order.end_time:
                # Force complete remaining quantity
                if order.remaining_quantity > 0:
                    self._execute_remaining_quantity(order)
                order.state = TWAPState.COMPLETED
                self._complete_twap_order(order)
                continue

            # Check if it's time for next slice
            time_since_last_slice = current_time - order.start_time
            expected_slices = int(time_since_last_slice.total_seconds() / order.interval_seconds)

            if expected_slices > order.slices_executed:
                # Execute slice(s)
                for _ in range(expected_slices - order.slices_executed):
                    if order.remaining_quantity > 0:
                        self.execute_twap_slice(order)

                        # Add randomization to timing
                        if self.config['randomize_timing']:
                            time.sleep(np.random.uniform(0.5, 1.5))

    def _execute_remaining_quantity(self, order: TWAPOrder):
        """Execute remaining quantity at market."""
        if order.remaining_quantity <= 0:
            return

        target_price = self._get_market_price(order.symbol)
        slice_result = self._execute_slice(order, order.remaining_quantity, target_price)

        # Update final order stats
        order.executed_quantity += slice_result.executed_quantity
        order.remaining_quantity = 0

    def get_twap_stats(self) -> Dict:
        """
        Get TWAP execution statistics.

        Returns:
            Dictionary with TWAP statistics
        """
        if not self.completed_orders:
            return {}

        orders = self.completed_orders

        total_orders = len(orders)
        completed_orders = [o for o in orders if o.state == TWAPState.COMPLETED]
        completion_rate = len(completed_orders) / total_orders if total_orders > 0 else 0

        total_volume = sum(o.total_cost for o in completed_orders)
        total_fees = sum(o.total_fees for o in completed_orders)

        # Calculate slippage vs VWAP
        avg_slippage = []
        for order in completed_orders:
            if order.total_quantity > 0:
                vwap_price = order.total_cost / order.total_quantity
                market_price = self._get_market_price(order.symbol)
                slippage = abs(vwap_price - market_price) / market_price
                avg_slippage.append(slippage)

        avg_slippage_pct = np.mean(avg_slippage) if avg_slippage else 0

        return {
            'total_twap_orders': total_orders,
            'completed_orders': len(completed_orders),
            'completion_rate': completion_rate,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'avg_slippage_pct': avg_slippage_pct,
            'active_orders': len(self.active_orders)
        }


if __name__ == "__main__":
    # Example usage
    twap_executor = TWAPExecutor()

    # Submit a TWAP order
    order = twap_executor.submit_twap_order(
        symbol='BTCUSDT',
        side='buy',
        quantity=1.0,  # 1 BTC
        duration_minutes=10,  # Over 10 minutes
        interval_seconds=60   # Every 60 seconds
    )

    print(f"TWAP order submitted: {order.order_id}")

    # Simulate execution over time
    for i in range(12):  # 12 minutes
        twap_executor.process_active_orders()
        time.sleep(1)  # 1 second = 1 minute in simulation
        print(f"Minute {i+1}: Remaining quantity: {order.remaining_quantity:.4f}")

    # Get final stats
    stats = twap_executor.get_twap_stats()
    print(f"TWAP stats: {stats}")