# =========================
# services/backtesting.py
# =========================
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class BacktestEngine:
    def __init__(self):
        self.initial_balance = 10000
        self.balance = self.initial_balance
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, price_data: List[float], signals: List[str], 
                    symbol: str = "BTC/USD") -> Dict[str, any]:
        """
        Run backtest on historical price data with signals
        """
        self.balance = self.initial_balance
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        position_size = 0.1  # 10% of balance per trade
        
        for i, (price, signal) in enumerate(zip(price_data, signals)):
            # Calculate current equity
            current_equity = self.calculate_equity(price)
            self.equity_curve.append(current_equity)
            
            # Execute trades based on signals
            trade_amount = self.balance * position_size
            
            if signal == "BUY" and symbol not in self.positions:
                # Open long position
                quantity = trade_amount / price
                if self.balance >= trade_amount:
                    self.balance -= trade_amount
                    self.positions[symbol] = {
                        "quantity": quantity,
                        "entry_price": price,
                        "entry_time": i
                    }
                    self.trades.append({
                        "time": i,
                        "action": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "balance": self.balance
                    })
            
            elif signal == "SELL" and symbol in self.positions:
                # Close long position
                position = self.positions[symbol]
                pnl = (price - position["entry_price"]) * position["quantity"]
                self.balance += position["quantity"] * price
                
                self.trades.append({
                    "time": i,
                    "action": "SELL",
                    "price": price,
                    "quantity": position["quantity"],
                    "pnl": pnl,
                    "balance": self.balance
                })
                
                del self.positions[symbol]
        
        # Close any remaining positions
        final_price = price_data[-1] if price_data else 0
        for symbol_pos, position in list(self.positions.items()):
            pnl = (final_price - position["entry_price"]) * position["quantity"]
            self.balance += position["quantity"] * final_price
            self.trades.append({
                "time": len(price_data) - 1,
                "action": "SELL",
                "price": final_price,
                "quantity": position["quantity"],
                "pnl": pnl,
                "balance": self.balance
            })
        
        return self.generate_report()
    
    def calculate_equity(self, current_price: float) -> float:
        """Calculate total equity including open positions"""
        equity = self.balance
        for position in self.positions.values():
            equity += position["quantity"] * current_price
        return equity
    
    def generate_report(self) -> Dict[str, any]:
        """Generate backtest performance report"""
        if not self.equity_curve:
            return {"error": "No equity data"}
        
        # Calculate returns
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        
        # Calculate metrics
        total_return = (self.balance - self.initial_balance) / self.initial_balance * 100
        sharpe_ratio = self.calculate_sharpe(returns)
        max_drawdown = self.calculate_max_drawdown()
        win_rate = self.calculate_win_rate()
        
        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "total_return": round(total_return, 2),
            "total_trades": len(self.trades),
            "win_rate": round(win_rate, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "max_drawdown": round(max_drawdown, 2),
            "equity_curve": self.equity_curve,
            "trades": self.trades
        }
    
    def calculate_sharpe(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        return np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100  # Return as percentage
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate"""
        if not self.trades:
            return 0.0
        
        winning_trades = sum(1 for trade in self.trades if trade.get("pnl", 0) > 0)
        return (winning_trades / len(self.trades)) * 100

# Global backtest engine
backtest_engine = BacktestEngine()

def backtest(prices: List[float]) -> Dict[str, any]:
    """Simple backtest function"""
    # Generate random signals for demo
    signals = np.random.choice(["BUY", "SELL", "HOLD"], size=len(prices))
    return backtest_engine.run_backtest(prices, signals)
