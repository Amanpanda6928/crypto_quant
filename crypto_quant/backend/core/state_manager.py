"""State management for trading system."""

from typing import Dict, Any, List
import asyncio
from datetime import datetime


class StateManager:
    """Manages application state including signals, portfolio, and orders."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            "active": True,
            "signals": {},
            "portfolio": {},
            "orders": [],
            "historical_returns": [],
            "last_updated": None
        }
        self._lock = asyncio.Lock()

    async def get_signals(self) -> Dict[str, Any]:
        """Get current signals."""
        async with self._lock:
            return self._state["signals"].copy()

    def set_signals(self, signals: Dict[str, Any]):
        """Update signals."""
        self._state["signals"] = signals
        self._state["last_updated"] = datetime.utcnow().isoformat()

    def get_active(self) -> Dict[str, Any]:
        """Get full state."""
        return self._state.copy()

    def add_order(self, order: Dict[str, Any]):
        """Add an order."""
        self._state["orders"].append(order)
        self._state["last_updated"] = datetime.utcnow().isoformat()

    def update_portfolio(self, portfolio: Dict[str, Any]):
        """Update portfolio."""
        self._state["portfolio"] = portfolio
        self._state["last_updated"] = datetime.utcnow().isoformat()

    def add_return(self, value: float):
        """Add a return value."""
        self._state["historical_returns"].append(value)
        self._state["last_updated"] = datetime.utcnow().isoformat()