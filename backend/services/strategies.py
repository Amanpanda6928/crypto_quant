# Multi-Strategy Trading Signals
import numpy as np
import pandas as pd

def sma_strategy(prices, short_window=5, long_window=20):
    """Simple Moving Average Strategy"""
    signals = []
    
    for i in range(long_window, len(prices)):
        short_ma = np.mean(prices[i-short_window:i])
        long_ma = np.mean(prices[i-long_window:i])
        
        if short_ma > long_ma:
            signals.append("BUY")
        elif short_ma < long_ma:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def ema_strategy(prices, short_window=12, long_window=26):
    """Exponential Moving Average Strategy"""
    signals = []
    
    # Calculate EMAs
    ema_short = pd.Series(prices).ewm(span=short_window).mean()
    ema_long = pd.Series(prices).ewm(span=long_window).mean()
    
    for i in range(long_window, len(prices)):
        if ema_short.iloc[i] > ema_long.iloc[i]:
            signals.append("BUY")
        elif ema_short.iloc[i] < ema_long.iloc[i]:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def rsi(prices, period=14):
    """Calculate RSI indicator"""
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def rsi_strategy(prices, period=14, oversold=30, overbought=70):
    """RSI Overbought/Oversold Strategy"""
    signals = []
    
    for i in range(period, len(prices)):
        rsi_val = rsi(prices[i-period:i], period)
        
        if rsi_val < oversold:
            signals.append("BUY")
        elif rsi_val > overbought:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = pd.Series(prices).rolling(window=period).mean()
    std = pd.Series(prices).rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band.values, sma.values, lower_band.values

def bollinger_strategy(prices, period=20, std_dev=2):
    """Bollinger Bands Strategy"""
    signals = []
    upper_band, sma, lower_band = bollinger_bands(prices, period, std_dev)
    
    for i in range(period, len(prices)):
        price = prices[i]
        
        if price <= lower_band[i]:
            signals.append("BUY")
        elif price >= upper_band[i]:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    exp1 = pd.Series(prices).ewm(span=fast).mean()
    exp2 = pd.Series(prices).ewm(span=slow).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal).mean()
    
    return macd_line.values, signal_line.values

def macd_strategy(prices, fast=12, slow=26, signal=9):
    """MACD Crossover Strategy"""
    signals = []
    macd_line, signal_line = macd(prices, fast, slow, signal)
    
    for i in range(slow, len(prices)):
        if macd_line[i] > signal_line[i]:
            signals.append("BUY")
        elif macd_line[i] < signal_line[i]:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def stochastic_oscillator(prices, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator"""
    signals = []
    
    for i in range(k_period, len(prices)):
        window = prices[i-k_period:i]
        high_max = max(window)
        low_min = min(window)
        current_close = prices[i]
        
        k_percent = ((current_close - low_min) / (high_max - low_min)) * 100
        signals.append(k_percent)
    
    # Smooth %K with %D (moving average)
    d_values = pd.Series(signals).rolling(window=d_period).mean().values
    
    return signals[k_period-1:], d_values[d_period-1:]

def stochastic_strategy(prices, k_period=14, d_period=3, oversold=20, overbought=80):
    """Stochastic Oscillator Strategy"""
    signals = []
    k_values, d_values = stochastic_oscillator(prices, k_period, d_period)
    
    for i in range(len(k_values)):
        if k_values[i] < oversold and d_values[i] < oversold:
            signals.append("BUY")
        elif k_values[i] > overbought and d_values[i] > overbought:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def williams_r(prices, period=14):
    """Calculate Williams %R"""
    signals = []
    
    for i in range(period, len(prices)):
        window = prices[i-period:i]
        high_max = max(window)
        low_min = min(window)
        current_close = prices[i]
        
        wr = ((high_max - current_close) / (high_max - low_min)) * -100
        signals.append(wr)
    
    return signals

def williams_strategy(prices, period=14, oversold=-80, overbought=-20):
    """Williams %R Strategy"""
    signals = []
    wr_values = williams_r(prices, period)
    
    for wr in wr_values:
        if wr < oversold:
            signals.append("BUY")
        elif wr > overbought:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def atr(prices, period=14):
    """Calculate Average True Range"""
    tr_values = []
    
    for i in range(1, len(prices)):
        high = prices[i]
        low = prices[i]
        prev_close = prices[i-1]
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr_values.append(max(tr1, tr2, tr3))
    
    return pd.Series(tr_values).rolling(window=period).mean().values

def atr_strategy(prices, period=14, multiplier=2.0):
    """ATR Trailing Stop Strategy"""
    signals = []
    atr_values = atr(prices, period)
    
    for i in range(period, len(prices)):
        price = prices[i]
        atr_val = atr_values[i]
        
        # Generate signals based on ATR
        if price > prices[i-1] + (atr_val * multiplier):
            signals.append("SELL")
        elif price < prices[i-1] - (atr_val * multiplier):
            signals.append("BUY")
        else:
            signals.append("HOLD")
    
    return signals

def vwap(prices, volumes):
    """Calculate Volume Weighted Average Price"""
    signals = []
    
    for i in range(1, len(prices)):
        window_prices = prices[:i+1]
        window_volumes = volumes[:i+1]
        
        vwap = np.sum(window_prices * window_volumes) / np.sum(window_volumes)
        
        if prices[i] > vwap:
            signals.append("BUY")
        elif prices[i] < vwap:
            signals.append("SELL")
        else:
            signals.append("HOLD")
    
    return signals

def get_strategy_signals(prices, volumes=None):
    """Get signals from all strategies"""
    strategies = {}
    
    # Moving Average strategies
    strategies['sma'] = sma_strategy(prices)
    strategies['ema'] = ema_strategy(prices)
    
    # Oscillator strategies
    strategies['rsi'] = rsi_strategy(prices)
    strategies['stochastic'] = stochastic_strategy(prices)
    strategies['williams'] = williams_strategy(prices)
    
    # Volatility strategies
    strategies['bollinger'] = bollinger_strategy(prices)
    strategies['atr'] = atr_strategy(prices)
    
    # Momentum strategies
    strategies['macd'] = macd_strategy(prices)
    
    # Volume-based strategy (if volumes available)
    if volumes:
        strategies['vwap'] = vwap(prices, volumes)
    
    return strategies

def calculate_strategy_performance(signals, prices, initial_balance=10000):
    """Calculate performance metrics for a strategy"""
    balance = initial_balance
    equity = []
    trades = []
    wins = 0
    losses = 0
    position = None
    
    for i, signal in enumerate(signals):
        price = prices[i]
        
        if signal == "BUY" and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        elif signal == "SELL" and position is not None:
            pnl = (price - position["entry"]) * position["quantity"]
            balance += pnl
            
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            
            trades.append({
                "entry": position["entry"],
                "exit": price,
                "pnl": pnl,
                "time": position["time"],
                "exit_time": i,
                "type": position["type"]
            })
            position = None
        
        equity.append(balance)
    
    return {
        "equity": equity,
        "final_balance": balance,
        "wins": wins,
        "losses": losses,
        "total_trades": len(trades),
        "win_rate": (wins / len(trades) * 100) if trades else 0
    }
