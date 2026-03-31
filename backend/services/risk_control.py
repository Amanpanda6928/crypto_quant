# Risk Management System
def calc_qty(balance_usdt, risk_pct, entry, stop_loss):
    """Calculate position size based on risk management"""
    risk_amount = balance_usdt * (risk_pct / 100.0)
    per_unit_risk = abs(entry - stop_loss)
    if per_unit_risk == 0:
        return 0.0
    qty = risk_amount / per_unit_risk
    return round(qty, 6)

def sl_tp_prices(entry, side, sl_pct=0.02, tp_pct=0.04):
    """Calculate stop loss and take profit prices"""
    if side == "BUY":
        sl = entry * (1 - sl_pct)  # Stop loss below entry for long
        tp = entry * (1 + tp_pct)  # Take profit above entry for long
    else:
        sl = entry * (1 + sl_pct)  # Stop loss above entry for short
        tp = entry * (1 - tp_pct)  # Take profit below entry for short
    return round(sl, 6), round(tp, 6)

def calculate_risk_metrics(positions, current_prices):
    """Calculate portfolio risk metrics"""
    total_value = 0.0
    total_risk = 0.0
    
    for coin, pos in positions.items():
        current_price = current_prices.get(coin, pos["entry"])
        position_value = pos["quantity"] * current_price
        
        # Calculate unrealized PnL
        if pos["side"] == "LONG":
            pnl = (current_price - pos["entry"]) * pos["quantity"]
        else:
            pnl = (pos["entry"] - current_price) * pos["quantity"]
        
        total_value += position_value + pnl
        total_risk += abs(pnl)
    
    return {
        "total_portfolio_value": total_value,
        "total_risk": total_risk,
        "risk_percentage": (total_risk / total_value * 100) if total_value > 0 else 0,
        "positions_count": len(positions)
    }

def validate_trade_risk(balance, trade_size, max_risk_pct=2.0):
    """Validate if trade meets risk criteria"""
    trade_risk_pct = (trade_size / balance) * 100
    return {
        "valid": trade_risk_pct <= max_risk_pct,
        "risk_percentage": trade_risk_pct,
        "max_allowed": max_risk_pct,
        "within_limits": trade_risk_pct <= max_risk_pct
    }

def calculate_position_size_kelly(win_rate, avg_win, avg_loss, balance):
    """Kelly Criterion for optimal position sizing"""
    if avg_loss == 0:
        return 0.0
    
    win_loss_ratio = avg_win / abs(avg_loss)
    kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    
    # Cap Kelly at 25% to avoid over-leveraging
    kelly_pct = min(kelly_pct, 0.25)
    
    return balance * kelly_pct

def get_risk_level(risk_percentage):
    """Categorize risk level"""
    if risk_percentage <= 1.0:
        return "LOW"
    elif risk_percentage <= 2.5:
        return "MEDIUM"
    elif risk_percentage <= 5.0:
        return "HIGH"
    else:
        return "EXTREME"

def portfolio_heatmap(positions, current_prices):
    """Generate portfolio risk heatmap"""
    heatmap_data = []
    
    for coin, pos in positions.items():
        current_price = current_prices.get(coin, pos["entry"])
        
        if pos["side"] == "LONG":
            pnl_pct = ((current_price - pos["entry"]) / pos["entry"]) * 100
        else:
            pnl_pct = ((pos["entry"] - current_price) / pos["entry"]) * 100
        
        # Risk level
        if pnl_pct > 5:
            risk_level = "HIGH_PROFIT"
        elif pnl_pct > 2:
            risk_level = "MODERATE_PROFIT"
        elif pnl_pct > -2:
            risk_level = "SMALL_LOSS"
        else:
            risk_level = "SIGNIFICANT_LOSS"
        
        heatmap_data.append({
            "coin": coin,
            "pnl_percentage": round(pnl_pct, 2),
            "risk_level": risk_level,
            "position_value": round(pos["quantity"] * current_price, 2)
        })
    
    return sorted(heatmap_data, key=lambda x: x["pnl_percentage"], reverse=True)
