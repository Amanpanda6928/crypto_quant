"""
Finnhub Crypto Prediction Service
Real-time AI predictions using Finnhub API with technical analysis
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import threading

# Finnhub API Configuration
FINNHUB_API_KEY = "d7bjpmpr01qgc9t7lpc0d7bjpmpr01qgc9t7lpcg"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# 10 Coins Configuration
COINS = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "BNB": "Binance Coin",
    "SOL": "Solana",
    "XRP": "Ripple",
    "ADA": "Cardano",
    "AVAX": "Avalanche",
    "DOGE": "Dogecoin",
    "DOT": "Polkadot",
    "LINK": "Chainlink",
}

TIMEFRAMES = {
    "15m": {"resolution": "15", "bars": 200, "label": "15 Minute"},
    "30m": {"resolution": "30", "bars": 200, "label": "30 Minute"},
    "1h": {"resolution": "60", "bars": 300, "label": "1 Hour"},
    "4h": {"resolution": "240", "bars": 200, "label": "4 Hour"},
    "1d": {"resolution": "D", "bars": 365, "label": "Daily"},
}


class FinnhubService:
    """
    Real-time crypto prediction service using Finnhub API
    - Technical indicators: EMA, RSI, MACD, Bollinger Bands, StochRSI
    - Multi-factor signal scoring
    - Live backtesting
    """

    def __init__(self):
        self.api_key = FINNHUB_API_KEY
        self.base_url = FINNHUB_BASE_URL
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.last_update = None

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make authenticated request to Finnhub API"""
        params['token'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Finnhub] API Error: {e}")
            return {}

    def fetch_candles(self, symbol: str, resolution: str, bars: int) -> pd.DataFrame:
        """Fetch OHLCV candles from Finnhub"""
        now = int(time.time())
        res_secs = {
            "15": 15*60, "30": 30*60, "60": 3600,
            "240": 4*3600, "D": 86400
        }.get(resolution, 3600)
        from_ts = now - bars * res_secs

        params = {
            'symbol': f'BINANCE:{symbol}USDT',
            'resolution': resolution,
            'from': from_ts,
            'to': now
        }

        data = self._make_request('crypto/candle', params)

        if not data or data.get('s') != 'ok' or not data.get('c'):
            return pd.DataFrame()

        df = pd.DataFrame({
            'timestamp': pd.to_datetime(data['t'], unit='s'),
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v'],
        })
        return df.sort_values('timestamp').reset_index(drop=True)

    def fetch_quote(self, symbol: str) -> Dict:
        """Fetch real-time quote"""
        params = {'symbol': f'BINANCE:{symbol}USDT'}
        return self._make_request('quote', params)

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute technical indicators"""
        if len(df) < 50:
            return df

        c = df['close'].copy()
        h = df['high'].copy()
        l = df['low'].copy()

        # EMAs
        df['ema9'] = c.ewm(span=9, adjust=False).mean()
        df['ema21'] = c.ewm(span=21, adjust=False).mean()
        df['ema50'] = c.ewm(span=50, adjust=False).mean()
        df['ema200'] = c.ewm(span=200, adjust=False).mean()

        # RSI (14)
        delta = c.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_g = gain.ewm(com=13, adjust=False).mean()
        avg_l = loss.ewm(com=13, adjust=False).mean()
        rs = avg_g / avg_l.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        df['bb_mid'] = sma20
        df['bb_upper'] = sma20 + 2 * std20
        df['bb_lower'] = sma20 - 2 * std20
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        df['bb_pct'] = (c - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # ATR (14)
        prev_c = c.shift(1)
        tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
        df['atr'] = tr.ewm(com=13, adjust=False).mean()

        # Stochastic RSI
        rsi_min = df['rsi'].rolling(14).min()
        rsi_max = df['rsi'].rolling(14).max()
        rng = (rsi_max - rsi_min).replace(0, np.nan)
        df['stoch_rsi'] = (df['rsi'] - rsi_min) / rng * 100

        # Volume MA
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma20'].replace(0, np.nan)

        return df

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Multi-factor signal scoring system
        Returns: signal, confidence, score, factors, targets
        """
        if len(df) < 50:
            return {"signal": "HOLD", "confidence": 50, "score": 0, "factors": {}}

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        score = 0
        factors = {}

        # 1. EMA9 vs EMA21
        if last['ema9'] > last['ema21']:
            score += 1
            factors['EMA9>21'] = 'Bullish'
        else:
            score -= 1
            factors['EMA9>21'] = 'Bearish'

        # 2. EMA21 vs EMA50
        if last['ema21'] > last['ema50']:
            score += 1
            factors['EMA21>50'] = 'Bullish'
        else:
            score -= 1
            factors['EMA21>50'] = 'Bearish'

        # 3. Price vs EMA200
        if last['close'] > last['ema200']:
            score += 1
            factors['Price>EMA200'] = 'Bull Trend'
        else:
            score -= 1
            factors['Price>EMA200'] = 'Bear Trend'

        # 4. RSI
        rsi = last['rsi']
        if rsi < 35:
            score += 2
            factors['RSI'] = f'Oversold ({rsi:.1f})'
        elif rsi > 65:
            score -= 2
            factors['RSI'] = f'Overbought ({rsi:.1f})'
        elif 45 <= rsi <= 60:
            score += 1
            factors['RSI'] = f'Bullish Zone ({rsi:.1f})'
        else:
            factors['RSI'] = f'Neutral ({rsi:.1f})'

        # 5. MACD
        if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            score += 2
            factors['MACD'] = 'Bullish Cross'
        elif last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            score -= 2
            factors['MACD'] = 'Bearish Cross'
        elif last['macd_hist'] > 0:
            score += 1
            factors['MACD'] = 'Positive Histogram'
        else:
            score -= 1
            factors['MACD'] = 'Negative Histogram'

        # 6. Bollinger Bands
        bb_pct = last['bb_pct']
        if bb_pct < 0.2:
            score += 2
            factors['Bollinger'] = f'Near Lower Band ({bb_pct:.2f})'
        elif bb_pct > 0.8:
            score -= 2
            factors['Bollinger'] = f'Near Upper Band ({bb_pct:.2f})'
        else:
            factors['Bollinger'] = f'Mid-Band ({bb_pct:.2f})'

        # 7. Stochastic RSI
        srsi = last['stoch_rsi']
        if srsi < 20:
            score += 1
            factors['StochRSI'] = f'Oversold ({srsi:.1f})'
        elif srsi > 80:
            score -= 1
            factors['StochRSI'] = f'Overbought ({srsi:.1f})'
        else:
            factors['StochRSI'] = f'Neutral ({srsi:.1f})'

        # 8. Volume
        if last['vol_ratio'] > 1.5:
            if score > 0:
                score += 1
                factors['Volume'] = f'High Vol Confirms Up (×{last["vol_ratio"]:.1f})'
            elif score < 0:
                score -= 1
                factors['Volume'] = f'High Vol Confirms Down (×{last["vol_ratio"]:.1f})'
            else:
                factors['Volume'] = f'High Volume (×{last["vol_ratio"]:.1f})'
        else:
            factors['Volume'] = f'Normal Volume (×{last["vol_ratio"]:.1f})'

        # Classify signal
        norm = score / 11.0
        if norm >= 0.25:
            signal = "BUY"
            confidence = min(95, int(60 + norm * 35))
        elif norm <= -0.25:
            signal = "SELL"
            confidence = min(95, int(60 + abs(norm) * 35))
        else:
            signal = "HOLD"
            confidence = int(50 + abs(norm) * 20)

        # ATR-based targets
        atr = last['atr']
        price = last['close']
        if signal == "BUY":
            target = round(price + 2.0 * atr, 6)
            stop = round(price - 1.5 * atr, 6)
        elif signal == "SELL":
            target = round(price - 2.0 * atr, 6)
            stop = round(price + 1.5 * atr, 6)
        else:
            target = round(price + 1.0 * atr, 6)
            stop = round(price - 1.0 * atr, 6)

        reward = abs(target - price)
        risk = abs(stop - price)
        rr = round(reward / risk, 2) if risk > 0 else 0

        return {
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "price": round(price, 4),
            "target": target,
            "stop": stop,
            "rr": rr,
            "rsi": round(rsi, 1),
            "macd": round(last['macd'], 4),
            "atr": round(atr, 4),
            "factors": factors,
        }

    def backtest(self, df: pd.DataFrame, symbol: str, tf_label: str) -> Dict:
        """
        Walk-forward backtest using historical data
        """
        if len(df) < 60:
            return {"error": "Insufficient data"}

        df = self.compute_indicators(df.copy()).dropna().reset_index(drop=True)

        trades = []
        in_trade = False
        entry_price = 0.0
        entry_sig = ""
        entry_idx = 0
        tp = sl = 0.0
        equity = 10000.0
        risk_pct = 0.02
        equity_curve = [equity]

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            next_row = df.iloc[i + 1]
            price = row['close']

            # Exit open trade
            if in_trade:
                hit_tp = (entry_sig == "BUY" and next_row['high'] >= tp) or \
                         (entry_sig == "SELL" and next_row['low'] <= tp)
                hit_sl = (entry_sig == "BUY" and next_row['low'] <= sl) or \
                         (entry_sig == "SELL" and next_row['high'] >= sl)

                if hit_tp or hit_sl:
                    exit_price = tp if hit_tp else sl
                    if entry_sig == "BUY":
                        pnl_pct = (exit_price - entry_price) / entry_price
                    else:
                        pnl_pct = (entry_price - exit_price) / entry_price

                    position_size = (equity * risk_pct) / abs(entry_price - sl) * entry_price
                    pnl_dollar = position_size * pnl_pct
                    equity = max(0.01, equity + pnl_dollar)
                    equity_curve.append(equity)

                    trades.append({
                        "entry_idx": entry_idx,
                        "exit_idx": i + 1,
                        "entry_price": round(entry_price, 6),
                        "exit_price": round(exit_price, 6),
                        "signal": entry_sig,
                        "result": "WIN" if hit_tp else "LOSS",
                        "pnl_pct": round(pnl_pct * 100, 3),
                        "pnl_dollar": round(pnl_dollar, 2),
                        "equity": round(equity, 2),
                        "bars_held": i + 1 - entry_idx,
                        "timestamp": str(df.iloc[i]['timestamp'])[:16],
                    })
                    in_trade = False

            # Generate new signal
            if not in_trade:
                sig_data = self.generate_signal(df.iloc[:i+1])
                sig = sig_data['signal']
                if sig in ("BUY", "SELL"):
                    entry_price = next_row['open']
                    atr = row['atr']
                    if sig == "BUY":
                        tp = entry_price + 2.0 * atr
                        sl = entry_price - 1.5 * atr
                    else:
                        tp = entry_price - 2.0 * atr
                        sl = entry_price + 1.5 * atr
                    in_trade = True
                    entry_sig = sig
                    entry_idx = i + 1

        if not trades:
            return {"error": "No trades generated"}

        results = pd.DataFrame(trades)
        wins = results[results['result'] == 'WIN']
        losses = results[results['result'] == 'LOSS']
        total = len(results)
        win_rate = len(wins) / total * 100 if total > 0 else 0
        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0
        profit_factor = (wins['pnl_dollar'].sum() / abs(losses['pnl_dollar'].sum())
                         if losses['pnl_dollar'].sum() != 0 else float('inf'))

        # Max drawdown
        eq = pd.Series(equity_curve)
        peak = eq.cummax()
        dd = (eq - peak) / peak * 100
        max_dd = dd.min()

        # Sharpe ratio
        returns = results['pnl_pct'] / 100
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)
                  if returns.std() != 0 else 0)

        final_equity = equity_curve[-1] if equity_curve else 10000
        total_return = (final_equity - 10000) / 10000 * 100

        return {
            "symbol": symbol,
            "timeframe": tf_label,
            "total_trades": total,
            "win_rate": round(win_rate, 1),
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_dd, 2),
            "sharpe_ratio": round(sharpe, 2),
            "total_return": round(total_return, 2),
            "start_equity": 10000,
            "final_equity": round(final_equity, 2),
            "trades": trades[-10:],
            "equity_curve": equity_curve,
        }

    def get_all_predictions(self) -> Dict[str, Dict[str, Dict]]:
        """Get live predictions for all coins and timeframes"""
        all_signals = {}

        for tf, tf_cfg in TIMEFRAMES.items():
            all_signals[tf] = {}
            for symbol in COINS.keys():
                df = self.fetch_candles(symbol, tf_cfg['resolution'], tf_cfg['bars'])
                if not df.empty:
                    df = self.compute_indicators(df)
                    sig = self.generate_signal(df)
                    sig['name'] = COINS[symbol]
                    all_signals[tf][symbol] = sig
                time.sleep(0.12)  # Rate limiting

        self.last_update = datetime.now()
        return all_signals

    def get_prediction_for_coin(self, symbol: str) -> Dict[str, Dict]:
        """Get predictions for a specific coin across all timeframes"""
        result = {}
        for tf, tf_cfg in TIMEFRAMES.items():
            df = self.fetch_candles(symbol, tf_cfg['resolution'], tf_cfg['bars'])
            if not df.empty:
                df = self.compute_indicators(df)
                sig = self.generate_signal(df)
                sig['name'] = COINS.get(symbol, symbol)
                result[tf] = sig
            time.sleep(0.12)
        return result

    def get_backtest_results(self, symbol: str = None) -> List[Dict]:
        """Get backtest results for all coins or specific coin"""
        results = []
        symbols = [symbol] if symbol else list(COINS.keys())

        for sym in symbols:
            for tf, tf_cfg in TIMEFRAMES.items():
                df = self.fetch_candles(sym, tf_cfg['resolution'], tf_cfg['bars'])
                if not df.empty:
                    df = self.compute_indicators(df)
                    result = self.backtest(df, sym, tf_cfg['label'])
                    if 'error' not in result:
                        results.append(result)
                time.sleep(0.12)

        return results


# Global instance
_finnhub_service = None


def get_finnhub_service() -> FinnhubService:
    """Get or create Finnhub service singleton"""
    global _finnhub_service
    if _finnhub_service is None:
        _finnhub_service = FinnhubService()
    return _finnhub_service
