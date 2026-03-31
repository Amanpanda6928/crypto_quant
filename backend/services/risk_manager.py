# Professional Risk Management System
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    CRITICAL = "CRITICAL"

class RiskAction(Enum):
    CONTINUE = "CONTINUE"
    REDUCE_POSITION = "REDUCE_POSITION"
    HALT_NEW = "HALT_NEW"
    CLOSE_ALL = "CLOSE_ALL"
    EMERGENCY_STOP = "EMERGENCY_STOP"

class RiskManager:
    """Professional Risk Management System"""
    
    def __init__(self, 
                 max_drawdown_pct=20.0,
                 max_daily_loss_pct=5.0,
                 max_open_positions=3,
                 max_position_size_pct=10.0,
                 var_confidence=0.95,
                 max_leverage=2.0):
        
        # Risk limits
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_open_positions = max_open_positions
        self.max_position_size_pct = max_position_size_pct
        self.var_confidence = var_confidence
        self.max_leverage = max_leverage
        
        # State tracking
        self.open_positions = {}
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        self.current_drawdown = 0.0
        self.peak_equity = 10000.0
        self.risk_events = []
        
        # Risk metrics
        self.current_var = 0.0
        self.current_sharpe = 0.0
        self.risk_level = RiskLevel.LOW
        
    def check_position_limit(self, symbol: str) -> bool:
        """Check if we can open new position"""
        if len(self.open_positions) >= self.max_open_positions:
            self._log_risk_event("POSITION_LIMIT", f"Max positions ({self.max_open_positions}) reached")
            return False
        
        if symbol in self.open_positions:
            self._log_risk_event("DUPLICATE_POSITION", f"Position already exists for {symbol}")
            return False
        
        return True
    
    def check_position_size(self, symbol: str, proposed_size_usdt: float, account_balance: float) -> bool:
        """Check if position size is within limits"""
        max_size = account_balance * (self.max_position_size_pct / 100.0)
        
        if proposed_size_usdt > max_size:
            self._log_risk_event("POSITION_SIZE_LIMIT", 
                               f"Position size ${proposed_size_usdt:.2f} exceeds max ${max_size:.2f}")
            return False
        
        return True
    
    def update_daily_metrics(self, pnl: float):
        """Update daily PnL and reset if new day"""
        current_date = datetime.now().date()
        
        # Reset daily metrics if new day
        if current_date != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
            self._log_risk_event("DAILY_RESET", f"Daily metrics reset for {current_date}")
        
        self.daily_pnl += pnl
        self.daily_trades += 1
    
    def check_daily_loss_limit(self) -> RiskAction:
        """Check if daily loss limit is breached"""
        daily_loss_pct = (self.daily_pnl / 10000.0) * 100.0  # Assuming 10k initial balance
        
        if daily_loss_pct <= -self.max_daily_loss_pct:
            self._log_risk_event("DAILY_LOSS_LIMIT", 
                               f"Daily loss {daily_loss_pct:.2f}% exceeds limit {-self.max_daily_loss_pct}%")
            self.risk_level = RiskLevel.HIGH
            
            if daily_loss_pct <= -self.max_daily_loss_pct * 1.5:
                return RiskAction.HALT_NEW
            elif daily_loss_pct <= -self.max_daily_loss_pct * 2.0:
                return RiskAction.CLOSE_ALL
        
        return RiskAction.CONTINUE
    
    def check_drawdown_limit(self, current_equity: float) -> RiskAction:
        """Check maximum drawdown limit"""
        # Update peak equity
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Calculate current drawdown
        self.current_drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100.0
        
        if self.current_drawdown >= self.max_drawdown_pct:
            self._log_risk_event("MAX_DRAWDOWN", 
                               f"Drawdown {self.current_drawdown:.2f}% exceeds limit {self.max_drawdown_pct}%")
            self.risk_level = RiskLevel.CRITICAL
            
            if self.current_drawdown >= self.max_drawdown_pct * 1.5:
                return RiskAction.EMERGENCY_STOP
            else:
                return RiskAction.CLOSE_ALL
        
        # Update risk level based on drawdown
        if self.current_drawdown >= self.max_drawdown_pct * 0.8:
            self.risk_level = RiskLevel.HIGH
        elif self.current_drawdown >= self.max_drawdown_pct * 0.5:
            self.risk_level = RiskLevel.MEDIUM
        
        return RiskAction.CONTINUE
    
    def calculate_var(self, returns: List[float]) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) < 30:
            return 0.0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - self.var_confidence) * 100)
        self.current_var = var
        return var
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 30:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe ratio
        sharpe = (mean_return / std_return) * np.sqrt(252)
        self.current_sharpe = sharpe
        return sharpe
    
    def check_correlation_risk(self, portfolio_returns: Dict[str, List[float]]) -> RiskAction:
        """Check portfolio correlation risk"""
        if len(portfolio_returns) < 2:
            return RiskAction.CONTINUE
        
        symbols = list(portfolio_returns.keys())
        correlation_matrix = np.zeros((len(symbols), len(symbols)))
        
        # Calculate correlation matrix
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i != j:
                    returns1 = portfolio_returns[symbol1]
                    returns2 = portfolio_returns[symbol2]
                    
                    if len(returns1) >= 30 and len(returns2) >= 30:
                        correlation = np.corrcoef(returns1, returns2)[0, 1]
                        correlation_matrix[i][j] = correlation
        
        # Check for high correlations
        max_correlation = np.max(np.abs(correlation_matrix))
        avg_correlation = np.mean(np.abs(correlation_matrix[np.triu_indices_from(correlation_matrix.shape)]))
        
        if max_correlation > 0.8:
            self._log_risk_event("HIGH_CORRELATION", 
                               f"Max correlation {max_correlation:.3f} exceeds threshold")
            self.risk_level = RiskLevel.HIGH
            return RiskAction.REDUCE_POSITION
        
        return RiskAction.CONTINUE
    
    def check_leverage_risk(self, total_exposure: float, account_balance: float) -> RiskAction:
        """Check leverage limits"""
        current_leverage = total_exposure / account_balance
        
        if current_leverage > self.max_leverage:
            self._log_risk_event("LEVERAGE_LIMIT", 
                               f"Leverage {current_leverage:.2f}x exceeds max {self.max_leverage}x")
            self.risk_level = RiskLevel.EXTREME
            return RiskAction.CLOSE_ALL
        
        return RiskAction.CONTINUE
    
    def check_volatility_risk(self, recent_returns: List[float]) -> RiskAction:
        """Check volatility-based risk"""
        if len(recent_returns) < 20:
            return RiskAction.CONTINUE
        
        volatility = np.std(recent_returns) * np.sqrt(252)  # Annualized volatility
        
        # Risk levels based on volatility
        if volatility > 0.5:  # 50% annual volatility
            self._log_risk_event("HIGH_VOLATILITY", f"Volatility {volatility:.2f} is extremely high")
            self.risk_level = RiskLevel.EXTREME
            return RiskAction.HALT_NEW
        elif volatility > 0.3:  # 30% annual volatility
            self._log_risk_event("ELEVATED_VOLATILITY", f"Volatility {volatility:.2f} is elevated")
            self.risk_level = RiskLevel.HIGH
            return RiskAction.REDUCE_POSITION
        
        return RiskAction.CONTINUE
    
    def comprehensive_risk_check(self, 
                             current_equity: float,
                             account_balance: float,
                             returns: List[float],
                             portfolio_returns: Optional[Dict[str, List[float]]] = None) -> Dict:
        """Comprehensive risk assessment"""
        risk_actions = []
        
        # Check all risk metrics
        daily_loss_action = self.check_daily_loss_limit()
        drawdown_action = self.check_drawdown_limit(current_equity)
        
        if len(returns) >= 30:
            self.calculate_var(returns)
            self.calculate_sharpe_ratio(returns)
        
        leverage_action = self.check_leverage_risk(
            sum(pos.get('size', 0) for pos in self.open_positions.values()),
            account_balance
        )
        
        volatility_action = self.check_volatility_risk(returns[-20:] if len(returns) >= 20 else returns)
        
        # Add portfolio correlation check if available
        if portfolio_returns:
            correlation_action = self.check_correlation_risk(portfolio_returns)
            risk_actions.append(("CORRELATION", correlation_action))
        
        risk_actions.extend([
            ("DAILY_LOSS", daily_loss_action),
            ("DRAWDOWN", drawdown_action),
            ("LEVERAGE", leverage_action),
            ("VOLATILITY", volatility_action)
        ])
        
        # Determine overall risk action
        overall_action = RiskAction.CONTINUE
        for action_name, action in risk_actions:
            if action.value > overall_action.value:
                overall_action = action
        
        return {
            "overall_action": overall_action,
            "risk_level": self.risk_level,
            "individual_checks": risk_actions,
            "risk_metrics": {
                "daily_pnl": self.daily_pnl,
                "daily_loss_pct": (self.daily_pnl / 10000.0) * 100.0,
                "current_drawdown": self.current_drawdown,
                "peak_equity": self.peak_equity,
                "var_95": self.current_var,
                "sharpe_ratio": self.current_sharpe,
                "open_positions": len(self.open_positions),
                "daily_trades": self.daily_trades
            }
        }
    
    def add_position(self, symbol: str, position_data: Dict):
        """Add new position to risk tracking"""
        self.open_positions[symbol] = {
            **position_data,
            "open_time": datetime.now(),
            "initial_risk_level": self.risk_level
        }
        
        self._log_risk_event("POSITION_OPENED", f"Position opened for {symbol}")
    
    def close_position(self, symbol: str, pnl: float):
        """Close position and update metrics"""
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            position["close_time"] = datetime.now()
            position["pnl"] = pnl
            position["duration"] = (position["close_time"] - position["open_time"]).total_seconds() / 3600  # hours
            
            self.update_daily_metrics(pnl)
            del self.open_positions[symbol]
            
            self._log_risk_event("POSITION_CLOSED", f"Position closed for {symbol}, PnL: ${pnl:.2f}")
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        return {
            "risk_level": self.risk_level,
            "open_positions": len(self.open_positions),
            "max_positions_allowed": self.max_open_positions,
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "current_drawdown": self.current_drawdown,
            "var_95": self.current_var,
            "sharpe_ratio": self.current_sharpe,
            "risk_limits": {
                "max_drawdown_pct": self.max_drawdown_pct,
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_open_positions": self.max_open_positions,
                "max_position_size_pct": self.max_position_size_pct,
                "max_leverage": self.max_leverage
            },
            "recent_events": self.risk_events[-10:] if self.risk_events else []
        }
    
    def _log_risk_event(self, event_type: str, message: str):
        """Log risk events"""
        event = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "message": message,
            "risk_level": self.risk_level,
            "daily_pnl": self.daily_pnl,
            "drawdown": self.current_drawdown
        }
        
        self.risk_events.append(event)
        
        # Keep only last 100 events
        if len(self.risk_events) > 100:
            self.risk_events = self.risk_events[-100:]
        
        print(f"[RISK] {event_type}: {message}")
    
    def emergency_stop_all(self):
        """Emergency stop - close all positions"""
        self._log_risk_event("EMERGENCY_STOP", "Emergency stop triggered - closing all positions")
        
        positions_to_close = list(self.open_positions.keys())
        for symbol in positions_to_close:
            self.close_position(symbol, 0)  # Assume zero PnL for emergency
        
        self.risk_level = RiskLevel.CRITICAL
        return positions_to_close
    
    def reset_daily_limits(self):
        """Reset daily limits (called at start of new day)"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        self._log_risk_event("DAILY_RESET", "Daily limits reset")

# Global risk manager instance
risk_manager = RiskManager()

# Risk management utility functions
def calculate_position_risk(entry_price: float, current_price: float, 
                          position_size: float, stop_loss: float) -> Dict:
    """Calculate risk metrics for a single position"""
    if position_size == 0:
        return {"risk_amount": 0, "risk_pct": 0}
    
    unrealized_pnl = (current_price - entry_price) * position_size
    risk_amount = abs(entry_price - stop_loss) * position_size
    risk_pct = (risk_amount / (entry_price * position_size)) * 100
    
    return {
        "unrealized_pnl": unrealized_pnl,
        "risk_amount": risk_amount,
        "risk_pct": risk_pct,
        "position_return_pct": (unrealized_pnl / (entry_price * position_size)) * 100
    }

def calculate_portfolio_risk(positions: Dict, account_balance: float) -> Dict:
    """Calculate overall portfolio risk"""
    total_exposure = sum(pos.get('size', 0) * pos.get('current_price', 0) for pos in positions.values())
    total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions.values())
    
    leverage = total_exposure / account_balance if account_balance > 0 else 0
    
    return {
        "total_exposure": total_exposure,
        "total_pnl": total_pnl,
        "leverage": leverage,
        "portfolio_return_pct": (total_pnl / account_balance) * 100 if account_balance > 0 else 0,
        "position_count": len(positions)
    }
