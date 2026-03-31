# =========================
# services/trading_engine.py
# =========================
from typing import Dict, List, Optional
from datetime import datetime
from app.services.risk_manager import risk_manager

class TradingEngine:
    def __init__(self):
        self.portfolio = {"balance": 10000.0, "equity": 10000.0}
        self.positions = {}
        self.trade_history = []
        self.is_live = False
    
    def execute_trade(self, symbol: str, price: float, quantity: float, side: str, 
                     stop_loss: float = None, take_profit: float = None) -> Dict[str, any]:
        """
        Execute a trade with risk management
        """
        trade_value = price * quantity
        
        # Validate trade with risk manager
        if not risk_manager.validate_trade(self.portfolio["balance"], 0, trade_value):
            return {"success": False, "error": "Trade failed risk validation"}
        
        # Calculate position size if not provided
        if stop_loss:
            optimal_quantity = risk_manager.calculate_position_size(
                self.portfolio["balance"], 2.0, price, stop_loss
            )
            quantity = min(quantity, optimal_quantity)
        
        # Execute trade
        if side.upper() == "BUY":
            if self.portfolio["balance"] >= trade_value:
                self.portfolio["balance"] -= trade_value
                self._add_position(symbol, quantity, price, side, stop_loss, take_profit)
                result = {"success": True, "action": "BUY", "value": trade_value}
            else:
                return {"success": False, "error": "Insufficient balance"}
        else:  # SELL
            position = self.positions.get(symbol)
            if position and position["quantity"] >= quantity:
                pnl = (price - position["avg_price"]) * quantity
                self.portfolio["balance"] += trade_value
                self.portfolio["equity"] += pnl
                self._reduce_position(symbol, quantity, price)
                result = {"success": True, "action": "SELL", "value": trade_value, "pnl": pnl}
            else:
                return {"success": False, "error": "Insufficient position"}
        
        # Record trade
        trade_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "value": trade_value,
            "portfolio_balance": self.portfolio["balance"]
        }
        self.trade_history.append(trade_record)
        
        return result
    
    def _add_position(self, symbol: str, quantity: float, price: float, side: str, 
                     stop_loss: float, take_profit: float):
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_quantity = pos["quantity"] + quantity
            pos["avg_price"] = ((pos["avg_price"] * pos["quantity"]) + (price * quantity)) / total_quantity
            pos["quantity"] = total_quantity
        else:
            self.positions[symbol] = {
                "quantity": quantity,
                "avg_price": price,
                "side": side,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "entry_time": datetime.utcnow().isoformat()
            }
    
    def _reduce_position(self, symbol: str, quantity: float, price: float):
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos["quantity"] -= quantity
            if pos["quantity"] <= 0:
                del self.positions[symbol]
    
    def get_portfolio_summary(self) -> Dict[str, any]:
        return {
            "balance": self.portfolio["balance"],
            "equity": self.portfolio["equity"],
            "positions": self.positions,
            "total_trades": len(self.trade_history),
            "last_trade": self.trade_history[-1] if self.trade_history else None
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        return self.trade_history[-limit:]

# Global trading engine instance
trading_engine = TradingEngine()

def execute_trade(symbol: str, price: float, quantity: float, side: str) -> bool:
    result = trading_engine.execute_trade(symbol, price, quantity, side)
    return result.get("success", False)
