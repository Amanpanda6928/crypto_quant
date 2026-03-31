# =========================
# backtesting/strategies.py
# =========================
"""
10 STRATEGY BACKTESTING SYSTEM FOR CRYPTOCURRENCY TRADING
=====================================================
Strategies:
1. Simple Moving Average Crossover (SMA)
2. Exponential Moving Average Crossover (EMA)
3. Relative Strength Index (RSI)
4. MACD (Moving Average Convergence Divergence)
5. Bollinger Bands Mean Reversion
6. Momentum Strategy
7. Volume-Weighted Average Price (VWAP)
8. Stochastic Oscillator
9. Trend Following with ADX
10. Machine Learning (Random Forest) Prediction
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class StrategyBacktester:
    """Backtesting engine for 10 cryptocurrency trading strategies"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.results = {}
        
    # ============================================================================
    # TECHNICAL INDICATORS
    # ============================================================================
    
    @staticmethod
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_12 = StrategyBacktester.calculate_ema(series, 12)
        ema_26 = StrategyBacktester.calculate_ema(series, 26)
        macd = ema_12 - ema_26
        signal = StrategyBacktester.calculate_ema(macd, 9)
        hist = macd - signal
        return macd, signal, hist
    
    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, window: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        middle = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return upper, middle, lower
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=d_period).mean()
        return k, d
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()
        return adx
    
    # ============================================================================
    # STRATEGY 1: SMA CROSSOVER
    # ============================================================================
    
    def strategy_sma_crossover(self, df: pd.DataFrame, 
                               short_window: int = 20, 
                               long_window: int = 50) -> pd.DataFrame:
        """Strategy 1: Simple Moving Average Crossover"""
        df = df.copy()
        df['sma_short'] = self.calculate_sma(df['close'], short_window)
        df['sma_long'] = self.calculate_sma(df['close'], long_window)
        
        df['signal'] = 0
        df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1
        df.loc[df['sma_short'] <= df['sma_long'], 'signal'] = -1
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 2: EMA CROSSOVER
    # ============================================================================
    
    def strategy_ema_crossover(self, df: pd.DataFrame, 
                               short_span: int = 12, 
                               long_span: int = 26) -> pd.DataFrame:
        """Strategy 2: Exponential Moving Average Crossover"""
        df = df.copy()
        df['ema_short'] = self.calculate_ema(df['close'], short_span)
        df['ema_long'] = self.calculate_ema(df['close'], long_span)
        
        df['signal'] = 0
        df.loc[df['ema_short'] > df['ema_long'], 'signal'] = 1
        df.loc[df['ema_short'] <= df['ema_long'], 'signal'] = -1
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 3: RSI MEAN REVERSION
    # ============================================================================
    
    def strategy_rsi(self, df: pd.DataFrame, 
                     period: int = 14, 
                     oversold: int = 30, 
                     overbought: int = 70) -> pd.DataFrame:
        """Strategy 3: RSI Mean Reversion"""
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'], period)
        
        df['signal'] = 0
        df.loc[df['rsi'] < oversold, 'signal'] = 1  # Buy oversold
        df.loc[df['rsi'] > overbought, 'signal'] = -1  # Sell overbought
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 4: MACD
    # ============================================================================
    
    def strategy_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strategy 4: MACD Signal Line Crossover"""
        df = df.copy()
        df['macd'], df['macd_signal'], df['macd_hist'] = self.calculate_macd(df['close'])
        
        df['signal'] = 0
        df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1
        df.loc[df['macd'] <= df['macd_signal'], 'signal'] = -1
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 5: BOLLINGER BANDS MEAN REVERSION
    # ============================================================================
    
    def strategy_bollinger_bands(self, df: pd.DataFrame, 
                                  window: int = 20) -> pd.DataFrame:
        """Strategy 5: Bollinger Bands Mean Reversion"""
        df = df.copy()
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'], window)
        
        df['signal'] = 0
        df.loc[df['close'] < df['bb_lower'], 'signal'] = 1  # Buy when below lower band
        df.loc[df['close'] > df['bb_upper'], 'signal'] = -1  # Sell when above upper band
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 6: MOMENTUM
    # ============================================================================
    
    def strategy_momentum(self, df: pd.DataFrame, 
                          lookback: int = 10, 
                          threshold: float = 0.02) -> pd.DataFrame:
        """Strategy 6: Price Momentum"""
        df = df.copy()
        df['momentum'] = df['close'].pct_change(periods=lookback)
        
        df['signal'] = 0
        df.loc[df['momentum'] > threshold, 'signal'] = 1  # Buy on strong momentum
        df.loc[df['momentum'] < -threshold, 'signal'] = -1  # Sell on weak momentum
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 7: VWAP
    # ============================================================================
    
    def strategy_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strategy 7: Volume-Weighted Average Price"""
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        
        df['signal'] = 0
        df.loc[df['close'] > df['vwap'], 'signal'] = 1  # Buy above VWAP
        df.loc[df['close'] <= df['vwap'], 'signal'] = -1  # Sell below VWAP
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 8: STOCHASTIC OSCILLATOR
    # ============================================================================
    
    def strategy_stochastic(self, df: pd.DataFrame, 
                           k_period: int = 14, 
                           d_period: int = 3) -> pd.DataFrame:
        """Strategy 8: Stochastic Oscillator"""
        df = df.copy()
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(
            df['high'], df['low'], df['close'], k_period, d_period
        )
        
        df['signal'] = 0
        df.loc[(df['stoch_k'] > df['stoch_d']) & (df['stoch_k'] < 20), 'signal'] = 1
        df.loc[(df['stoch_k'] < df['stoch_d']) & (df['stoch_k'] > 80), 'signal'] = -1
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 9: ADX TREND FOLLOWING
    # ============================================================================
    
    def strategy_adx_trend(self, df: pd.DataFrame, 
                          adx_threshold: int = 25) -> pd.DataFrame:
        """Strategy 9: ADX Trend Following"""
        df = df.copy()
        df['adx'] = self.calculate_adx(df['high'], df['low'], df['close'])
        df['ema_20'] = self.calculate_ema(df['close'], 20)
        
        df['signal'] = 0
        strong_trend = df['adx'] > adx_threshold
        df.loc[strong_trend & (df['close'] > df['ema_20']), 'signal'] = 1
        df.loc[strong_trend & (df['close'] <= df['ema_20']), 'signal'] = -1
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # STRATEGY 10: MACHINE LEARNING (RANDOM FOREST)
    # ============================================================================
    
    def strategy_ml_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strategy 10: Machine Learning Price Prediction"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            print("scikit-learn not installed. Skipping ML strategy.")
            return df.copy()
        
        df = df.copy()
        
        # Create features
        df['returns'] = df['close'].pct_change()
        df['sma_10'] = self.calculate_sma(df['close'], 10)
        df['sma_30'] = self.calculate_sma(df['close'], 30)
        df['rsi'] = self.calculate_rsi(df['close'])
        df['volatility'] = df['returns'].rolling(20).std()
        
        for lag in [1, 2, 3, 5]:
            df[f'return_lag_{lag}'] = df['returns'].shift(lag)
        
        # Target: 1 if price goes up next period, -1 if down
        df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, -1)
        
        # Prepare data
        feature_cols = [c for c in df.columns if 'lag' in c or c in ['rsi', 'volatility']]
        df_ml = df.dropna()
        
        if len(df_ml) < 100:
            df['signal'] = 0
            return df
        
        # Train model on first 70% of data
        split_idx = int(len(df_ml) * 0.7)
        train_data = df_ml.iloc[:split_idx]
        test_data = df_ml.iloc[split_idx:]
        
        X_train = train_data[feature_cols]
        y_train = train_data['target']
        X_test = test_data[feature_cols]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        predictions = model.predict(X_test_scaled)
        df.loc[test_data.index, 'signal'] = predictions
        df['signal'] = df['signal'].fillna(0)
        df['position'] = df['signal'].diff().fillna(0)
        
        return df
    
    # ============================================================================
    # BACKTESTING ENGINE
    # ============================================================================
    
    def run_backtest(self, df: pd.DataFrame, strategy_name: str, 
                     commission: float = 0.001, 
                     slippage: float = 0.0005) -> Dict:
        """Run backtest on a strategy"""
        
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        
        # Calculate strategy returns
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # Apply transaction costs when position changes
        df['position_change'] = abs(df['position'])
        df['transaction_cost'] = df['position_change'] * (commission + slippage)
        df['strategy_returns'] -= df['transaction_cost']
        
        # Calculate cumulative returns
        df['cumulative_market'] = (1 + df['returns'].fillna(0)).cumprod()
        df['cumulative_strategy'] = (1 + df['strategy_returns'].fillna(0)).cumprod()
        
        # Calculate metrics
        total_return = df['cumulative_strategy'].iloc[-1] - 1 if len(df) > 0 else 0
        market_return = df['cumulative_market'].iloc[-1] - 1 if len(df) > 0 else 0
        
        # Annualized metrics (assuming hourly data)
        periods_per_year = 365 * 24  # Hourly data
        strategy_volatility = df['strategy_returns'].std() * np.sqrt(periods_per_year)
        sharpe_ratio = (df['strategy_returns'].mean() * periods_per_year) / strategy_volatility if strategy_volatility != 0 else 0
        
        # Maximum Drawdown
        cumulative = df['cumulative_strategy']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
        
        # Win rate
        trades = df[df['position_change'] > 0]
        winning_trades = df[df['strategy_returns'] > 0]
        win_rate = len(winning_trades) / len(df[df['strategy_returns'] != 0]) if len(df[df['strategy_returns'] != 0]) > 0 else 0
        
        # Number of trades
        num_trades = len(df[df['position_change'] > 0])
        
        # Calmar ratio
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'strategy': strategy_name,
            'total_return': total_return,
            'market_return': market_return,
            'excess_return': total_return - market_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'num_trades': num_trades,
            'volatility': strategy_volatility,
            'final_capital': self.initial_capital * (1 + total_return),
            'data': df
        }
    
    def run_all_strategies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run all 10 strategies and compare results"""
        
        strategies = {
            'SMA_Crossover': self.strategy_sma_crossover,
            'EMA_Crossover': self.strategy_ema_crossover,
            'RSI_MeanReversion': self.strategy_rsi,
            'MACD': self.strategy_macd,
            'BollingerBands': self.strategy_bollinger_bands,
            'Momentum': self.strategy_momentum,
            'VWAP': self.strategy_vwap,
            'Stochastic': self.strategy_stochastic,
            'ADX_Trend': self.strategy_adx_trend,
            'ML_Prediction': self.strategy_ml_prediction
        }
        
        results = []
        
        for name, strategy_func in strategies.items():
            try:
                df_strategy = strategy_func(df)
                result = self.run_backtest(df_strategy, name)
                results.append(result)
            except Exception as e:
                print(f"Strategy {name} error: {e}")
        
        # Create comparison DataFrame
        if results:
            comparison = pd.DataFrame([{
                'strategy': r['strategy'],
                'total_return_pct': r['total_return'] * 100,
                'market_return_pct': r['market_return'] * 100,
                'excess_return_pct': r['excess_return'] * 100,
                'sharpe_ratio': r['sharpe_ratio'],
                'max_drawdown_pct': r['max_drawdown'] * 100,
                'calmar_ratio': r['calmar_ratio'],
                'win_rate_pct': r['win_rate'] * 100,
                'num_trades': r['num_trades'],
                'final_capital': r['final_capital']
            } for r in results])
            
            comparison = comparison.sort_values('total_return_pct', ascending=False)
            return comparison
        
        return pd.DataFrame()
    
    def get_best_strategy(self) -> str:
        """Return the best performing strategy"""
        if not self.results:
            return None
        return max(self.results.items(), key=lambda x: x[1]['total_return'])[0]
    
    def get_equity_curve(self, strategy_name: str) -> List[Dict]:
        """Get equity curve data for a strategy"""
        if strategy_name not in self.results:
            return []
        
        data = self.results[strategy_name]['data']
        equity_curve = []
        
        for timestamp, row in data.iterrows():
            equity_curve.append({
                'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                'market': float(row['cumulative_market']) if 'cumulative_market' in row else 1.0,
                'strategy': float(row['cumulative_strategy']) if 'cumulative_strategy' in row else 1.0
            })
        
        return equity_curve
