"""
Advanced Exit Manager (Quant-Grade)

Fixes:
- Partial exits (position tracking)
- Position close state
- Trailing activation logic
- Slippage handling
- Proper execution flow
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ExitType(Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"


@dataclass
class ExitSignal:
    exit_type: ExitType
    price: float
    size: float
    level: Optional[float] = None

    def __str__(self):
        return f"{self.exit_type.value} | price={self.price:.4f} | size={self.size:.4f}"


class ExitManager:

    def __init__(
        self,
        entry_price: float,
        position_size: float,
        side: str = "long",
        take_profit_levels: Optional[List[tuple]] = None,
        stop_loss_price: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        trailing_activation_pct: float = 0.01,
        slippage_pct: float = 0.0005
    ):
        if side not in ("long", "short"):
            raise ValueError("side must be 'long' or 'short'")

        self.entry_price = float(entry_price)
        self.initial_size = float(position_size)
        self.remaining_size = float(position_size)

        self.side = side
        self.is_long = side == "long"

        self.tp_levels = take_profit_levels or []
        self.tp_hit = [False] * len(self.tp_levels)

        self.stop_loss_price = stop_loss_price

        # Trailing
        self.trailing_stop_pct = trailing_stop_pct
        self.trailing_activation_pct = trailing_activation_pct
        self.trailing_active = False
        self.trailing_stop_price = None

        self.highest_price = entry_price
        self.lowest_price = entry_price

        # Execution realism
        self.slippage_pct = slippage_pct

        # State
        self.closed = False

    # =========================
    # Core Update
    # =========================

    def update(self, price: float) -> Optional[ExitSignal]:

        if self.closed:
            return None

        self._update_extremes(price)

        # Activate trailing only after profit
        self._maybe_activate_trailing(price)

        # Update trailing
        if self.trailing_active:
            self._update_trailing(price)

        # Priority: SL > TS > TP
        for check in [self._check_stop_loss, self._check_trailing, self._check_tp]:
            signal = check(price)
            if signal:
                return signal

        return None

    # =========================
    # Internal Logic
    # =========================

    def _apply_slippage(self, price: float) -> float:
        if self.is_long:
            return price * (1 - self.slippage_pct)
        return price * (1 + self.slippage_pct)

    def _update_extremes(self, price: float):
        if price > self.highest_price:
            self.highest_price = price
        if price < self.lowest_price:
            self.lowest_price = price

    def _maybe_activate_trailing(self, price: float):
        if not self.trailing_stop_pct or self.trailing_active:
            return

        move = (price - self.entry_price) / self.entry_price
        if not self.is_long:
            move = -move

        if move >= self.trailing_activation_pct:
            self.trailing_active = True
            self._initialize_trailing(price)

    def _initialize_trailing(self, price: float):
        if self.is_long:
            self.trailing_stop_price = price * (1 - self.trailing_stop_pct)
        else:
            self.trailing_stop_price = price * (1 + self.trailing_stop_pct)

    def _update_trailing(self, price: float):
        if self.is_long:
            new_stop = price * (1 - self.trailing_stop_pct)
            if new_stop > self.trailing_stop_price:
                self.trailing_stop_price = new_stop
        else:
            new_stop = price * (1 + self.trailing_stop_pct)
            if new_stop < self.trailing_stop_price:
                self.trailing_stop_price = new_stop

    # =========================
    # Exit Checks
    # =========================

    def _check_stop_loss(self, price: float) -> Optional[ExitSignal]:
        if self.stop_loss_price is None:
            return None

        triggered = (
            self.is_long and price <= self.stop_loss_price
        ) or (
            not self.is_long and price >= self.stop_loss_price
        )

        if triggered:
            exec_price = self._apply_slippage(price)
            size = self.remaining_size
            self.remaining_size = 0
            self.closed = True

            return ExitSignal(ExitType.STOP_LOSS, exec_price, size, self.stop_loss_price)

        return None

    def _check_trailing(self, price: float) -> Optional[ExitSignal]:
        if not self.trailing_active or self.trailing_stop_price is None:
            return None

        triggered = (
            self.is_long and price <= self.trailing_stop_price
        ) or (
            not self.is_long and price >= self.trailing_stop_price
        )

        if triggered:
            exec_price = self._apply_slippage(price)
            size = self.remaining_size
            self.remaining_size = 0
            self.closed = True

            return ExitSignal(ExitType.TRAILING_STOP, exec_price, size, self.trailing_stop_price)

        return None

    def _check_tp(self, price: float) -> Optional[ExitSignal]:
        for i, (tp_price, pct) in enumerate(self.tp_levels):

            if self.tp_hit[i]:
                continue

            triggered = (
                self.is_long and price >= tp_price
            ) or (
                not self.is_long and price <= tp_price
            )

            if triggered:
                size = self.initial_size * pct
                size = min(size, self.remaining_size)

                exec_price = self._apply_slippage(price)

                self.remaining_size -= size
                self.tp_hit[i] = True

                if self.remaining_size <= 0:
                    self.closed = True

                return ExitSignal(ExitType.TAKE_PROFIT, exec_price, size, tp_price)

        return None

    # =========================
    # Status
    # =========================

    def get_status(self):
        return {
            "entry_price": self.entry_price,
            "remaining_size": self.remaining_size,
            "closed": self.closed,
            "trailing_active": self.trailing_active,
            "trailing_price": self.trailing_stop_price,
            "tp_hit": self.tp_hit,
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price
        }