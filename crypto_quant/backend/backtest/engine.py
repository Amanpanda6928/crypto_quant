"""
Backtest Engine - Fixed (Accurate PnL + Fast Signal Merge)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    signal: Signal
    position_value: float   # ✅ FIX

    exit_time: pd.Timestamp = None
    exit_price: float = None
    pnl: float = None
    pnl_pct: float = None
    exit_reason: str = None


class BacktestEngine:

    def __init__(
        self,
        initial_capital: float = 1000.0,
        position_size_pct: float = 0.20,
        stop_loss_pct: float = 0.02,      # 🔥 FIX 2: Tighter risk management
        take_profit_pct: float = 0.04,    # 🔥 FIX 2: Lower profit target
        fee_pct: float = 0.001,
        cooldown_bars: int = 3            # 🔥 FIX 4: Prevent overtrading
    ):
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.fee_pct = fee_pct

        self.capital = initial_capital
        self.equity_curve: List[float] = [initial_capital]
        self.trades: List[Trade] = []
        self.position: Trade = None
        self.cooldown_bars = cooldown_bars         # 🔥 FIX 4
        self.bars_since_last_trade = 0             # 🔥 FIX 4

    # ================================
    # POSITION SIZE
    # ================================

    def calculate_position_size(self):
        return self.capital * self.position_size_pct

    # ================================
    # ENTRY
    # ================================

    def execute_entry(self, time, price, signal):
        position_value = self.calculate_position_size()

        fee = position_value * self.fee_pct
        self.capital -= fee

        self.position = Trade(
            entry_time=time,
            entry_price=price,
            signal=signal,
            position_value=position_value  # ✅ FIXED
        )

    # ================================
    # EXIT
    # ================================

    def execute_exit(self, time, price, reason):

        if self.position is None:
            return

        trade = self.position

        trade.exit_time = time
        trade.exit_price = price
        trade.exit_reason = reason

        position_value = trade.position_value  # ✅ FIXED

        if trade.signal == Signal.BUY:
            trade.pnl = (price - trade.entry_price) / trade.entry_price * position_value
        else:
            trade.pnl = (trade.entry_price - price) / trade.entry_price * position_value

        trade.pnl_pct = trade.pnl / position_value

        fee = position_value * self.fee_pct
        trade.pnl -= fee

        self.capital += trade.pnl

        self.trades.append(trade)
        self.position = None

    # ================================
    # EXIT LOGIC
    # ================================

    def check_exit(self, trade, current_price):

        entry = trade.entry_price

        if trade.signal == Signal.BUY:
            if current_price <= entry * (1 - self.stop_loss_pct):
                return True, "STOP_LOSS", entry * (1 - self.stop_loss_pct)
            if current_price >= entry * (1 + self.take_profit_pct):
                return True, "TAKE_PROFIT", entry * (1 + self.take_profit_pct)

        if trade.signal == Signal.SELL:
            if current_price >= entry * (1 + self.stop_loss_pct):
                return True, "STOP_LOSS", entry * (1 + self.stop_loss_pct)
            if current_price <= entry * (1 - self.take_profit_pct):
                return True, "TAKE_PROFIT", entry * (1 - self.take_profit_pct)

        return False, None, None

    # ================================
    # EQUITY UPDATE
    # ================================

    def update_equity(self, price):

        if self.position is None:
            self.equity_curve.append(self.capital)
        else:
            pos = self.position

            if pos.signal == Signal.BUY:
                unrealized = (price - pos.entry_price) / pos.entry_price * pos.position_value
            else:
                unrealized = (pos.entry_price - price) / pos.entry_price * pos.position_value

            self.equity_curve.append(self.capital + unrealized)

    # ================================
    # MAIN BACKTEST
    # ================================

    def run(self, df: pd.DataFrame, predictions: pd.DataFrame):

        print(f"Running backtest on {len(df)} rows...")

        df = df.copy()

        # Group predictions by time and average probabilities
        pred = predictions.groupby("open_time")["probability"].mean().reset_index()

        # Generate signals from averaged probabilities
        pred["signal"] = pred["probability"].apply(
            lambda p: 1 if p > 0.6 else (-1 if p < 0.4 else 0)
        )

        df = df.merge(pred, on="open_time", how="left")

        df["signal"] = df["signal"].fillna(0)

        # ================================
        # LOOP
        # ================================

        for _, row in df.iterrows():

            time = row["open_time"]
            price = row["close"]
            
            # Add slippage to price
            price = price * (1 + 0.001)  # 0.1% slippage
            
            # Handle signals (now numeric: 1=BUY, -1=SELL, 0=HOLD)
            if pd.isna(row["signal"]) or row["signal"] == 0:
                signal = Signal.HOLD
            elif row["signal"] == 1:
                signal = Signal.BUY
            elif row["signal"] == -1:
                signal = Signal.SELL
            else:
                signal = Signal.HOLD

            # EXIT
            if self.position:
                exit_flag, reason, exit_price = self.check_exit(self.position, price)

                if exit_flag:
                    self.execute_exit(time, exit_price, reason)
                    self.bars_since_last_trade = 0  # 🔥 FIX 4: Reset cooldown after exit

                elif signal != Signal.HOLD and signal != self.position.signal:
                    self.execute_exit(time, price, "SIGNAL_REVERSE")
                    self.bars_since_last_trade = 0  # 🔥 FIX 4: Reset cooldown after exit

            # ENTRY
            # 🔥 FIX 4: Check cooldown before entering
            if (self.position is None and signal != Signal.HOLD and 
                self.bars_since_last_trade >= self.cooldown_bars):
                self.execute_entry(time, price, signal)
                self.bars_since_last_trade = 0
            else:
                self.bars_since_last_trade += 1

            # UPDATE
            self.update_equity(price)

        # CLOSE LAST
        if self.position:
            self.execute_exit(df.iloc[-1]["open_time"], df.iloc[-1]["close"], "END")

        return self.get_results()

    # ================================
    # RESULTS
    # ================================

    def get_results(self):

        equity = pd.Series(self.equity_curve)
        returns = equity.pct_change().dropna()

        total_return = (self.capital - self.initial_capital) / self.initial_capital

        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_dd = drawdown.min()

        sharpe = 0
        if len(returns) > 1 and returns.std() != 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 * 60)

        wins = [t for t in self.trades if t.pnl > 0]

        return {
            "final_capital": self.capital,
            "total_return_pct": total_return * 100,
            "max_drawdown_pct": max_dd * 100,
            "sharpe_ratio": sharpe,
            "total_trades": len(self.trades),
            "win_rate": len(wins) / len(self.trades) * 100 if self.trades else 0,
            "equity_curve": self.equity_curve,
            "trades": self.trades
        }