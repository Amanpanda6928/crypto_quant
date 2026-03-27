"""Simple in-memory order book stream used by live trading and API routes."""

from datetime import datetime
from typing import Dict, List, Optional


class OrderBookStream:
    def __init__(self):
        self.snapshots: Dict[str, Dict] = {}
        self.history: Dict[str, List[Dict]] = {}

    def update(self, symbol: str, bid: float, ask: float, timestamp: Optional[datetime] = None):
        now = timestamp or datetime.utcnow()
        data = {
            "symbol": symbol.upper(),
            "bid": float(bid),
            "ask": float(ask),
            "mid": float((bid + ask) / 2),
            "timestamp": now.isoformat()
        }

        self.snapshots[symbol.upper()] = data
        self.history.setdefault(symbol.upper(), []).append(data)

        # Keep history manageable
        if len(self.history[symbol.upper()]) > 300:
            self.history[symbol.upper()] = self.history[symbol.upper()][-300:]

        return data

    def get_snapshot(self, symbol: str):
        return self.snapshots.get(symbol.upper())

    def get_history(self, symbol: str, limit: int = 50):
        history = self.history.get(symbol.upper(), [])
        return history[-limit:]
