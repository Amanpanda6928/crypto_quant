# Real Backtesting Engine with Binance Data
import numpy as np
import pandas as pd
from binance.client import Client
import os
from datetime import datetime, timedelta
import time

client = Client(
    os.getenv("BINANCE_API_KEY"),
    os.getenv("BINANCE_SECRET")
)

def fetch_klines(symbol="BTCUSDT", interval="1h", limit=500):
    """Fetch historical kline data from Binance"""
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        prices = [float(k[4]) for k in klines]  # close prices
        volumes = [float(k[5]) for k in klines]  # volumes
        highs = [float(k[2]) for k in klines]  # high prices
        lows = [float(k[3]) for k in klines]  # low prices
        opens = [float(k[1]) for k in klines]  # open prices
        times = [datetime.fromtimestamp(k[0] / 1000) for k in klines]  # timestamps
        
        return {
            "prices": prices,
            "volumes": volumes,
            "highs": highs,
            "lows": lows,
            "opens": opens,
            "times": times,
            "symbol": symbol,
            "interval": interval,
            "data_points": len(prices)
        }
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        # Return mock data for demo
        return generate_mock_data(symbol, limit)

def generate_mock_data(symbol="BTCUSDT", limit=500):
    """Generate mock data for demo purposes"""
    np.random.seed(int(time.time()))
    
    # Base prices for different symbols
    base_prices = {
        "BTCUSDT": 45000,
        "ETHUSDT": 3200,
        "ADAUSDT": 1.2,
        "SOLUSDT": 120,
        "DOGEUSDT": 0.085,
        "DOTUSDT": 8.5,
        "MATICUSDT": 0.95
    }
    
    base_price = base_prices.get(symbol, 100)
    prices = []
    volumes = []
    highs = []
    lows = []
    opens = []
    times = []
    
    current_price = base_price
    for i in range(limit):
        # Generate realistic price movement
        volatility = 0.02  # 2% volatility
        trend = 0.0001 * i  # Slight upward trend
        noise = np.random.normal(0, volatility)
        
        price_change = trend + noise
        current_price *= (1 + price_change)
        
        # Generate OHLC data
        open_price = current_price * (1 + np.random.normal(0, 0.005))
        high_price = current_price * (1 + abs(np.random.normal(0, 0.01)))
        low_price = current_price * (1 - abs(np.random.normal(0, 0.01)))
        volume = np.random.uniform(100, 1000)
        
        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        prices.append(current_price)
        volumes.append(volume)
        times.append(datetime.now() - timedelta(hours=limit-i))
    
    return {
        "prices": prices,
        "volumes": volumes,
        "highs": highs,
        "lows": lows,
        "opens": opens,
        "times": times,
        "symbol": symbol,
        "interval": "1h",
        "data_points": len(prices),
        "mock": True
    }

def run_backtest(prices, strategy="ma_crossover", params=None):
    """Run backtest with different strategies"""
    if params is None:
        params = {}
    
    if strategy == "ma_crossover":
        return run_ma_crossover(prices, params)
    elif strategy == "rsi":
        return run_rsi_strategy(prices, params)
    elif strategy == "bollinger_bands":
        return run_bollinger_bands(prices, params)
    elif strategy == "macd":
        return run_macd_strategy(prices, params)
    else:
        return run_simple_strategy(prices, params)

def run_ma_crossover(prices, params):
    """Moving Average Crossover Strategy"""
    short_window = params.get("short_window", 10)
    long_window = params.get("long_window", 30)
    
    balance = 10000
    equity = []
    position = None
    trades = []
    wins = 0
    losses = 0
    
    for i in range(long_window, len(prices)):
        short_ma = np.mean(prices[i-short_window:i])
        long_ma = np.mean(prices[i-long_window:i])
        price = prices[i]
        
        # ENTRY: Short MA crosses above Long MA
        if short_ma > long_ma and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        
        # EXIT: Short MA crosses below Long MA
        elif short_ma < long_ma and position is not None:
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
        "trades": trades,
        "strategy": "MA Crossover"
    }

def run_rsi_strategy(prices, params):
    """RSI Overbought/Oversold Strategy"""
    rsi_period = params.get("rsi_period", 14)
    rsi_overbought = params.get("rsi_overbought", 70)
    rsi_oversold = params.get("rsi_oversold", 30)
    
    balance = 10000
    equity = []
    position = None
    trades = []
    wins = 0
    losses = 0
    
    # Calculate RSI
    rsi_values = calculate_rsi(prices, rsi_period)
    
    for i in range(rsi_period, len(prices)):
        price = prices[i]
        rsi = rsi_values[i - rsi_period]
        
        # ENTRY: RSI oversold
        if rsi < rsi_oversold and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        
        # EXIT: RSI overbought
        elif rsi > rsi_overbought and position is not None:
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
        "trades": trades,
        "strategy": "RSI"
    }

def run_bollinger_bands(prices, params):
    """Bollinger Bands Strategy"""
    period = params.get("period", 20)
    std_dev = params.get("std_dev", 2)
    
    balance = 10000
    equity = []
    position = None
    trades = []
    wins = 0
    losses = 0
    
    for i in range(period, len(prices)):
        window = prices[i-period:i]
        sma = np.mean(window)
        std = np.std(window)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        price = prices[i]
        
        # ENTRY: Price touches lower band
        if price <= lower_band and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        
        # EXIT: Price touches upper band
        elif price >= upper_band and position is not None:
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
        "trades": trades,
        "strategy": "Bollinger Bands"
    }

def run_macd_strategy(prices, params):
    """MACD Strategy"""
    fast_period = params.get("fast_period", 12)
    slow_period = params.get("slow_period", 26)
    signal_period = params.get("signal_period", 9)
    
    balance = 10000
    equity = []
    position = None
    trades = []
    wins = 0
    losses = 0
    
    # Calculate MACD
    macd_line, signal_line = calculate_macd(prices, fast_period, slow_period, signal_period)
    
    for i in range(slow_period, len(prices)):
        price = prices[i]
        macd = macd_line[i - slow_period]
        signal = signal_line[i - slow_period]
        
        # ENTRY: MACD crosses above signal
        if macd > signal and position is None:
            position = {
                "entry": price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        
        # EXIT: MACD crosses below signal
        elif macd < signal and position is not None:
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
        "trades": trades,
        "strategy": "MACD"
    }

def run_simple_strategy(prices, params):
    """Simple Buy/Sell Strategy"""
    balance = 10000
    equity = []
    position = None
    trades = []
    wins = 0
    losses = 0
    
    for i, price in enumerate(prices):
        # Simple alternating strategy
        signal = "BUY" if i % 10 == 0 else "SELL" if i % 10 == 5 else "HOLD"
        
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
        "trades": trades,
        "strategy": "Simple"
    }

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    rsi_values = []
    
    for i in range(period, len(prices)):
        price_slice = prices[i-period+1:i+1]
        gains = []
        losses = []
        
        for j in range(1, len(price_slice)):
            change = price_slice[j] - price_slice[j-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    exp1 = pd.Series(prices).ewm(span=fast).mean()
    exp2 = pd.Series(prices).ewm(span=slow).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal).mean()
    
    return macd_line.values, signal_line.values

def calculate_metrics(equity, initial_balance=10000):
    """Calculate comprehensive performance metrics"""
    if not equity:
        return {
            "sharpe": 0,
            "max_drawdown": 0,
            "total_return": 0,
            "volatility": 0
        }
    
    final_balance = equity[-1]
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    # Calculate Sharpe ratio
    returns = np.diff(equity) / equity[:-1]
    returns = returns[~np.isnan(returns)]  # Remove NaN values
    
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
    else:
        sharpe = 0
    
    # Calculate Maximum Drawdown
    peak = equity[0]
    drawdown = []
    for value in equity:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        drawdown.append(dd)
    
    max_drawdown = min(drawdown) if drawdown else 0
    
    # Calculate Volatility
    volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 1 else 0
    
    return {
        "sharpe": float(sharpe),
        "max_drawdown": float(max_drawdown),
        "total_return": float(total_return),
        "volatility": float(volatility),
        "final_balance": float(final_balance)
    }

def get_available_strategies():
    """Get list of available backtesting strategies"""
    return {
        "strategies": [
            {
                "name": "ma_crossover",
                "display_name": "Moving Average Crossover",
                "description": "Buy when short MA crosses above long MA",
                "parameters": {
                    "short_window": {"type": "int", "default": 10, "min": 5, "max": 20},
                    "long_window": {"type": "int", "default": 30, "min": 20, "max": 50}
                }
            },
            {
                "name": "rsi",
                "display_name": "RSI Overbought/Oversold",
                "description": "Buy on oversold, sell on overbought",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 10, "max": 30},
                    "rsi_overbought": {"type": "int", "default": 70, "min": 60, "max": 80},
                    "rsi_oversold": {"type": "int", "default": 30, "min": 20, "max": 40}
                }
            },
            {
                "name": "bollinger_bands",
                "display_name": "Bollinger Bands",
                "description": "Buy on lower band, sell on upper band",
                "parameters": {
                    "period": {"type": "int", "default": 20, "min": 10, "max": 50},
                    "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
                }
            },
            {
                "name": "macd",
                "display_name": "MACD",
                "description": "MACD line crossover with signal line",
                "parameters": {
                    "fast_period": {"type": "int", "default": 12, "min": 8, "max": 20},
                    "slow_period": {"type": "int", "default": 26, "min": 20, "max": 40},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
                }
            },
            {
                "name": "simple",
                "display_name": "Simple Strategy",
                "description": "Basic alternating buy/sell pattern",
                "parameters": {}
            }
        ]
    }
