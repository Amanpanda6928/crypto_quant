"""
Live Trading System (FINAL)
"""

import numpy as np
from datetime import datetime

from ..model.predict import Predictor
from ..data.api import BinanceDataFetcher
from ..utils.config import get_config
from ..utils.logger import get_logger
from ..utils.alert import get_alert_manager

from ..execution.executor import TradeExecutor
from ..risk.manager import RiskManager
from ..risk.daily_limit import DailyRiskLimits
from ..live.orderbook import OrderBookStream
from ..monitor.health import HealthMonitor


class LiveSystem:

    def __init__(self):

        self.predictor = Predictor()
        self.fetcher = BinanceDataFetcher()

        self.config = get_config()
        self.logger = get_logger()
        self.alert = get_alert_manager()

        self.executor = TradeExecutor(paper_trading=self.config.get('paper_trading'))
        self.risk = RiskManager()
        self.daily_limits = DailyRiskLimits()

        self.health = HealthMonitor()
        self.orderbook = OrderBookStream()

        self.capital = self.config.get("capital")
        self.last_update = None

    def get_signals(self):

        preds = self.predictor.predict_all()
        signals = {}

        for symbol, p in preds.items():

            prob = self.predictor.combine_multi_horizon(p)

            confidence = abs(prob - 0.5) * 2
            score = confidence * prob

            if abs(score) < 0.15:
                continue

            signals[symbol] = score

            try:
                last_price = self.fetcher.fetch_ohlcv(symbol, "1m", limit=1)["close"].iloc[-1]
                self.orderbook.update(symbol, bid=float(last_price) * 0.999, ask=float(last_price) * 1.001)
            except Exception:
                pass

        return signals

    def allocate(self, signals):

        alloc = {}

        for sym, score in signals.items():

            can_trade, _ = self.daily_limits.can_trade({
                "current_positions": len(alloc),
                "current_drawdown_pct": 0.02,
                "proposed_volume": 1000
            })

            if not can_trade:
                continue

            price = self.fetcher.fetch_ohlcv(sym, 1)["close"].iloc[-1]

            size = self.risk.size(self.capital, price, 0.02)

            alloc[sym] = size * np.sign(score)

        return alloc

    def execute(self, alloc):

        for sym, amt in alloc.items():

            price = self.fetcher.fetch_ohlcv(sym, 1)["close"].iloc[-1]

            side = "buy" if amt > 0 else "sell"
            qty = abs(amt)

            self.executor.submit_order(sym, side, qty, price)

            self.logger.log_trade(sym, side, qty, price, reason="live")

            self.alert.trigger_alert(
                title="Trade",
                message=f"{side} {sym}"
            )

    def run_cycle(self):

        print("\n=== NEW CYCLE ===")
        
        # Health check
        self.health.heartbeat("live_system", message="Starting cycle")

        signals = self.get_signals()
        if not signals:
            return {}

        alloc = self.allocate(signals)
        if not alloc:
            return {}

        self.execute(alloc)

        # Health check
        self.health.heartbeat("live_system", message=f"Cycle complete: {len(alloc)} trades")

        self.last_update = datetime.utcnow().isoformat()

        return {
            "allocations": alloc,
            "orderbook": {symbol: self.orderbook.get_snapshot(symbol) for symbol in alloc.keys()},
            "timestamp": self.last_update
        }