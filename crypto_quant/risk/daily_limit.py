"""
Advanced Daily Risk Limit Module (Quant-Grade)

Adds:
- Intraday peak tracking (trailing drawdown)
- Soft + hard limits
- Lockout system
- Persistent breach state
- Better metrics
"""

from datetime import datetime


class DailyLimitExceeded(Exception):
    pass


class DailyLimit:
    DEFAULT_LIMIT_PCT = 0.05        # Hard stop (5%)
    DEFAULT_WARNING_PCT = 0.03      # Soft warning (3%)

    def __init__(
        self,
        starting_capital: float,
        limit_pct: float = None,
        warning_pct: float = None,
        use_trailing: bool = True
    ):
        if starting_capital <= 0:
            raise ValueError("Starting capital must be positive")

        self.starting_capital = float(starting_capital)
        self.limit_pct = limit_pct or self.DEFAULT_LIMIT_PCT
        self.warning_pct = warning_pct or self.DEFAULT_WARNING_PCT
        self.use_trailing = use_trailing

        self.limit_amount = self.starting_capital * self.limit_pct
        self.warning_amount = self.starting_capital * self.warning_pct

        self._breached = False
        self._locked = False
        self._peak_equity = starting_capital
        self._breach_time = None

    # =========================
    # Core Logic
    # =========================

    def update_peak(self, current_equity: float):
        """Track highest equity for trailing drawdown."""
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity

    def _get_reference_capital(self) -> float:
        """Use peak or starting capital."""
        return self._peak_equity if self.use_trailing else self.starting_capital

    def check(self, current_equity: float) -> bool:
        """
        Hard enforcement check.
        """
        if self._locked:
            raise DailyLimitExceeded("Trading locked for the day")

        self.update_peak(current_equity)

        ref_capital = self._get_reference_capital()
        loss = ref_capital - current_equity

        # Hard breach
        if loss > ref_capital * self.limit_pct:
            self._breached = True
            self._locked = True
            self._breach_time = datetime.utcnow()

            raise DailyLimitExceeded(
                f"DAILY LOSS LIMIT BREACHED\n"
                f"Loss: ${loss:,.2f} ({loss/ref_capital:.2%})\n"
                f"Limit: {self.limit_pct:.2%}\n"
                f"Reference Capital: ${ref_capital:,.2f}"
            )

        return True

    def check_warning(self, current_equity: float) -> bool:
        """
        Soft warning before breach.
        """
        ref_capital = self._get_reference_capital()
        loss = ref_capital - current_equity

        return loss > ref_capital * self.warning_pct

    def can_trade(self, current_equity: float) -> bool:
        if self._locked:
            return False

        try:
            return self.check(current_equity)
        except DailyLimitExceeded:
            return False

    # =========================
    # Status
    # =========================

    def get_status(self, current_equity: float) -> dict:
        ref_capital = self._get_reference_capital()
        loss = ref_capital - current_equity

        return {
            "starting_capital": self.starting_capital,
            "peak_equity": self._peak_equity,
            "current_equity": current_equity,
            "reference_capital": ref_capital,

            "daily_loss": loss,
            "daily_loss_pct": loss / ref_capital if ref_capital > 0 else 0,

            "hard_limit_pct": self.limit_pct,
            "warning_pct": self.warning_pct,

            "breached": self._breached,
            "locked": self._locked,
            "breach_time": self._breach_time,

            "warning_triggered": self.check_warning(current_equity),

            "remaining_buffer": max(0, (ref_capital * self.limit_pct) - loss),
            "can_trade": not self._locked
        }

    # =========================
    # Control
    # =========================

    def force_lock(self):
        """Manually stop trading."""
        self._locked = True
        self._breach_time = datetime.utcnow()

    def reset(self, new_starting_capital: float):
        """Reset for next trading day."""
        self.__init__(
            starting_capital=new_starting_capital,
            limit_pct=self.limit_pct,
            warning_pct=self.warning_pct,
            use_trailing=self.use_trailing
        )