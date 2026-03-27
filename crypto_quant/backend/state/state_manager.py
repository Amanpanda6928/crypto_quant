"""State manager for backend trades and portfolio tracking."""

from typing import Dict, Any


class StateManager:
    """Lightweight in-memory state management."""

    def __init__(self):
        self.state: Dict[str, Any] = {
            "active": True,
            "portfolio": {},
            "orders": [],
            "historical_returns": []
        }

    def set_active(self, active: bool):
        self.state["active"] = active

    def get_active(self) -> Dict[str, Any]:
        return self.state

    def add_order(self, order: Dict[str, Any]):
        self.state["orders"].append(order)

    def update_portfolio(self, portfolio_data: Dict[str, Any]):
        self.state["portfolio"] = portfolio_data

    def add_return(self, value: float):
        self.state["historical_returns"].append(value)
