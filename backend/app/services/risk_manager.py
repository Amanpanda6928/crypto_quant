# =========================
# services/risk_manager.py
# =========================
from typing import Dict, Optional
from app.core.config import DEFAULT_RISK_PERCENTAGE, MAX_POSITION_SIZE, MAX_DRAWDOWN

class RiskManager:
    def __init__(self):
        self.max_risk_per_trade = DEFAULT_RISK_PERCENTAGE
        self.max_position_size = MAX_POSITION_SIZE
        self.max_drawdown = MAX_DRAWDOWN
    
    def calculate_position_size(self, balance: float, risk_pct: float, entry_price: float, stop_loss: float) -> float:
        """
        Calculate optimal position size based on risk parameters
        """
        if entry_price == stop_loss:
            return 0.0
        
        risk_amount = balance * (risk_pct / 100)
        price_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / price_risk
        
        # Apply maximum position size limit
        max_position_value = balance * self.max_position_size
        max_size_by_value = max_position_value / entry_price
        
        return min(position_size, max_size_by_value)
    
    def validate_trade(self, balance: float, current_drawdown: float, trade_value: float) -> bool:
        """
        Validate if trade meets risk management criteria
        """
        # Check if current drawdown exceeds maximum
        if current_drawdown > self.max_drawdown:
            return False
        
        # Check if trade value is within acceptable range
        if trade_value > balance * self.max_position_size:
            return False
        
        return True
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float = None) -> float:
        """
        Calculate stop loss price based on entry and side
        """
        if side.upper() == "BUY":
            # For long positions, stop loss is below entry
            stop_distance = atr * 2 if atr else entry_price * 0.02  # 2% default
            return entry_price - stop_distance
        else:
            # For short positions, stop loss is above entry
            stop_distance = atr * 2 if atr else entry_price * 0.02
            return entry_price + stop_distance
    
    def calculate_take_profit(self, entry_price: float, side: str, risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit price based on risk/reward ratio
        """
        if side.upper() == "BUY":
            return entry_price * (1 + risk_reward_ratio * 0.02)  # 2% risk * ratio
        else:
            return entry_price * (1 - risk_reward_ratio * 0.02)

# Global risk manager instance
risk_manager = RiskManager()

def position_size(balance: float, risk_pct: float, entry: float, stop: float) -> float:
    return risk_manager.calculate_position_size(balance, risk_pct, entry, stop)
