"""
HEDGE FUND LEVEL BACKTESTING STRATEGY
======================================
Professional-grade quantitative trading system with:
- Multi-coin support (BTC, ETH, BNB, SOL, XRP, etc.)
- Multi-timeframe analysis (1h, 4h, 1d, 1w)
- Multi-factor signal generation
- Risk management (VaR, position sizing, stop losses)
- Portfolio optimization across multiple coins
- Regime detection and adaptive strategies
- Realistic execution simulation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import warnings
from scipy import stats
from scipy.optimize import minimize

warnings.filterwarnings('ignore')

# Try to import ccxt for real exchange data
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False


class Regime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOL = "high_volatility"
    LOW_VOL = "low_volatility"


@dataclass
class RiskParameters:
    """Risk management configuration"""
    max_position_size: float = 0.25  # Max 25% in single position
    max_portfolio_heat: float = 0.60  # Max 60% invested at once
    max_drawdown_limit: float = -0.15  # Stop trading at 15% drawdown
    var_limit: float = 0.02  # 2% daily VaR limit
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
    trailing_stop_pct: float = 0.10  # 10% trailing stop
    max_consecutive_losses: int = 5
    risk_per_trade: float = 0.02  # Risk 2% of capital per trade


@dataclass
class ExecutionConfig:
    """Execution and cost configuration"""
    commission_rate: float = 0.001  # 0.1% per trade
    slippage_model: str = "volatility_based"  # fixed, volatility_based, volume_based
    slippage_base: float = 0.0005
    market_impact_factor: float = 0.1
    min_order_size: float = 10.0
    max_order_size_pct_volume: float = 0.01  # Max 1% of volume


@dataclass
class Trade:
    """Trade record"""
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp] = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    position: float = 0.0  # Positive for long, negative for short
    side: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""
    holding_periods: int = 0
    coin: str = ""  # Coin symbol for multi-coin trading


# Top 10 major cryptocurrencies supported
SUPPORTED_COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP",
    "ADA", "AVAX", "DOGE", "DOT", "LINK"
]

# Supported timeframe mappings (15m, 30m, 1h, 4h, 1d)
TIMEFRAMES = {
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}


class MultiCoinDataManager:
    """
    Manages historical and live data for multiple coins across timeframes
    """
    
    def __init__(self, exchange: str = "binance"):
        self.exchange_name = exchange
        self.exchange = None
        self.data_cache: Dict[str, pd.DataFrame] = {}  # key: "COIN_TIMEFRAME"
        
        if CCXT_AVAILABLE:
            try:
                self.exchange = getattr(ccxt, exchange)({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
            except Exception as e:
                print(f"Failed to initialize {exchange}: {e}")
    
    def get_symbol(self, coin: str, quote: str = "USDT") -> str:
        """Convert coin to exchange symbol format"""
        return f"{coin}{quote}"
    
    def fetch_ohlcv(
        self,
        coin: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: int = 500,
        quote: str = "USDT"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a coin
        
        Args:
            coin: Base coin (BTC, ETH, etc.)
            timeframe: Timeframe string (1m, 5m, 1h, 4h, 1d, etc.)
            since: Start timestamp in milliseconds
            limit: Number of candles to fetch
            quote: Quote currency (default USDT)
        """
        cache_key = f"{coin}_{timeframe}"
        
        if self.exchange is None:
            print(f"Exchange not available, generating sample data for {coin}")
            return self._generate_sample_data(coin, timeframe, limit)
        
        try:
            symbol = self.get_symbol(coin, quote)
            
            # Calculate since if not provided (default 30 days)
            if since is None:
                tf_minutes = self._timeframe_to_minutes(timeframe)
                since = int((datetime.now() - timedelta(minutes=limit*tf_minutes)).timestamp() * 1000)
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add coin identifier
            df['coin'] = coin
            df['timeframe'] = timeframe
            
            self.data_cache[cache_key] = df
            return df
            
        except Exception as e:
            print(f"Error fetching data for {coin}: {e}")
            return self._generate_sample_data(coin, timeframe, limit)
    
    def fetch_multi_coin_data(
        self,
        coins: List[str],
        timeframe: str = "1h",
        days: int = 90
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple coins
        
        Args:
            coins: List of coin symbols
            timeframe: Timeframe string
            days: Number of days of history
        """
        data = {}
        limit = self._days_to_candles(days, timeframe)
        
        for coin in coins:
            print(f"Fetching {coin} {timeframe} data...")
            df = self.fetch_ohlcv(coin, timeframe, limit=limit)
            if df is not None and len(df) > 0:
                data[coin] = df
        
        return data
    
    def align_timeframes(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Align multiple coin dataframes to common timestamps"""
        if not data_dict:
            return {}
        
        # Find common date range
        start_times = [df.index.min() for df in data_dict.values()]
        end_times = [df.index.max() for df in data_dict.values()]
        
        common_start = max(start_times)
        common_end = min(end_times)
        
        aligned = {}
        for coin, df in data_dict.items():
            aligned[coin] = df[(df.index >= common_start) & (df.index <= common_end)]
        
        return aligned
    
    def resample_data(
        self,
        df: pd.DataFrame,
        target_timeframe: str,
        source_timeframe: str = "1h"
    ) -> pd.DataFrame:
        """Resample data to different timeframe"""
        if df.empty:
            return df
        
        # Map timeframe strings to pandas resample rules
        tf_map = {
            "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
            "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "8h": "8H", "12h": "12H",
            "1d": "1D", "3d": "3D", "1w": "1W", "1M": "1M"
        }
        
        rule = tf_map.get(target_timeframe, target_timeframe)
        
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        resampled['coin'] = df['coin'].iloc[0] if 'coin' in df.columns else ''
        resampled['timeframe'] = target_timeframe
        
        return resampled.dropna()
    
    def get_cached_data(self, coin: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get data from cache if available"""
        cache_key = f"{coin}_{timeframe}"
        return self.data_cache.get(cache_key)
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe to minutes"""
        units = {"m": 1, "h": 60, "d": 1440, "w": 10080, "M": 43200}
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        return value * units.get(unit, 60)
    
    def _days_to_candles(self, days: int, timeframe: str) -> int:
        """Convert days to number of candles"""
        minutes_per_day = 1440
        tf_minutes = self._timeframe_to_minutes(timeframe)
        return int((days * minutes_per_day) / tf_minutes)
    
    def _generate_sample_data(
        self,
        coin: str,
        timeframe: str,
        limit: int = 500,
        base_price: float = 100.0
    ) -> pd.DataFrame:
        """Generate synthetic OHLCV data for testing"""
        np.random.seed(hash(coin) % 2**32)
        
        # Generate timestamps
        tf_minutes = self._timeframe_to_minutes(timeframe)
        end_time = datetime.now()
        timestamps = [end_time - timedelta(minutes=i*tf_minutes) for i in range(limit)]
        timestamps.reverse()
        
        # Generate price series with trend and volatility
        trend = np.random.uniform(-0.0001, 0.0001)  # Small drift
        volatility = np.random.uniform(0.01, 0.03)  # 1-3% volatility
        
        returns = np.random.normal(trend, volatility, limit)
        
        # Add coin-specific base price adjustment (10 coins only)
        coin_multipliers = {
            "BTC": 45000, "ETH": 3000, "BNB": 300, "SOL": 100, "XRP": 0.5,
            "ADA": 0.4, "AVAX": 30, "DOGE": 0.08, "DOT": 7, "LINK": 15
        }
        base = coin_multipliers.get(coin, base_price)
        
        closes = base * np.exp(np.cumsum(returns))
        
        # Generate OHLC from close
        data = {
            'open': closes * (1 + np.random.normal(0, 0.001, limit)),
            'high': closes * (1 + abs(np.random.normal(0, 0.005, limit))),
            'low': closes * (1 - abs(np.random.normal(0, 0.005, limit))),
            'close': closes,
            'volume': np.random.lognormal(15, 0.5, limit),
            'coin': coin,
            'timeframe': timeframe
        }
        
        df = pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        return df


@dataclass
class PortfolioConfig:
    """Multi-coin portfolio configuration"""
    coins: List[str] = field(default_factory=lambda: ["BTC", "ETH"])
    timeframe: str = "1h"
    lookback_days: int = 90
    max_coins_held: int = 5
    equal_weight: bool = False  # If True, equal weight; if False, use signal strength
    rebalance_frequency: str = "daily"  # hourly, daily, weekly
    correlation_filter: bool = True  # Avoid highly correlated coins


class HedgeFundBacktester:
    """
    Professional hedge fund backtesting engine
    """
    
    def __init__(
        self,
        initial_capital: float = 1000000.0,
        risk_params: Optional[RiskParameters] = None,
        execution_config: Optional[ExecutionConfig] = None
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_params = risk_params or RiskParameters()
        self.execution_config = execution_config or ExecutionConfig()
        
        # State tracking
        self.positions: Dict[str, float] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.signals_history: List[Dict] = []
        self.current_regime: Regime = Regime.SIDEWAYS
        self.consecutive_losses: int = 0
        self.max_equity: float = initial_capital
        self.drawdown: float = 0.0
        self.paused: bool = False
        
        # Performance tracking
        self.returns: List[float] = []
        self.daily_returns: List[float] = []
        self.monthly_returns: List[float] = []
        
    # ============================================================================
    # ADVANCED TECHNICAL INDICATORS
    # ============================================================================
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range for volatility measurement"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def calculate_keltner_channels(
        high: pd.Series, low: pd.Series, close: pd.Series,
        ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Keltner Channels for volatility-based signals"""
        ema = close.ewm(span=ema_period, adjust=False).mean()
        atr = HedgeFundBacktester.calculate_atr(high, low, close, atr_period)
        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)
        return upper, ema, lower
    
    @staticmethod
    def calculate_ichimoku(
        high: pd.Series, low: pd.Series, close: pd.Series
    ) -> Dict[str, pd.Series]:
        """Ichimoku Cloud for trend and support/resistance"""
        tenkan_sen = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun_sen = (high.rolling(26).max() + low.rolling(26).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        senkou_span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou_span = close.shift(-26)
        
        return {
            'tenkan': tenkan_sen,
            'kijun': kijun_sen,
            'senkou_a': senkou_span_a,
            'senkou_b': senkou_span_b,
            'chikou': chikou_span
        }
    
    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
        """Volume profile analysis"""
        price_range = df['close'].max() - df['close'].min()
        bin_size = price_range / bins
        
        df = df.copy()
        df['price_bin'] = ((df['close'] - df['close'].min()) / bin_size).astype(int)
        volume_profile = df.groupby('price_bin')['volume'].sum().reset_index()
        volume_profile.columns = ['bin', 'volume']
        
        return volume_profile
    
    @staticmethod
    def calculate_adaptive_ma(series: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
        """Adaptive moving average based on volatility"""
        volatility = series.pct_change().rolling(20).std()
        regime = pd.cut(volatility, bins=3, labels=['low', 'medium', 'high'])
        
        fast_ma = series.ewm(span=fast, adjust=False).mean()
        slow_ma = series.ewm(span=slow, adjust=False).mean()
        
        # Use faster MA in high vol, slower in low vol
        adaptive = series.copy()
        adaptive[regime == 'high'] = fast_ma[regime == 'high']
        adaptive[regime == 'medium'] = ((fast_ma + slow_ma) / 2)[regime == 'medium']
        adaptive[regime == 'low'] = slow_ma[regime == 'low']
        
        return adaptive
    
    @staticmethod
    def calculate_rsi_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 14) -> pd.Series:
        """Detect RSI divergence signals"""
        price_highs = close.rolling(lookback).max()
        price_lows = close.rolling(lookback).min()
        rsi_highs = rsi.rolling(lookback).max()
        rsi_lows = rsi.rolling(lookback).min()
        
        bullish_div = (close == price_lows) & (rsi > rsi_lows)
        bearish_div = (close == price_highs) & (rsi < rsi_highs)
        
        return pd.Series(np.where(bullish_div, 1, np.where(bearish_div, -1, 0)), index=close.index)
    
    # ============================================================================
    # REGIME DETECTION
    # ============================================================================
    
    def detect_regime(self, df: pd.DataFrame) -> Regime:
        """
        Detect market regime using multiple factors
        """
        if len(df) < 50:
            return Regime.SIDEWAYS
        
        # Trend strength
        returns = df['close'].pct_change().dropna()
        sma_50 = df['close'].rolling(50).mean().iloc[-1]
        sma_200 = df['close'].rolling(200).mean().iloc[-1] if len(df) >= 200 else sma_50
        current_price = df['close'].iloc[-1]
        
        # Volatility regime
        volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(365)
        vol_percentile = returns.rolling(60).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]), raw=False).iloc[-1]
        
        # Trend direction and strength
        trend_direction = 1 if current_price > sma_50 > sma_200 else -1 if current_price < sma_50 < sma_200 else 0
        
        # ADX for trend strength
        adx = self._calculate_adx_simple(df).iloc[-1] if len(df) > 14 else 0
        
        if vol_percentile > 80:
            return Regime.HIGH_VOL
        elif vol_percentile < 20:
            return Regime.LOW_VOL
        elif adx > 25 and trend_direction == 1:
            return Regime.BULL
        elif adx > 25 and trend_direction == -1:
            return Regime.BEAR
        else:
            return Regime.SIDEWAYS
    
    def _calculate_adx_simple(self, df: pd.DataFrame) -> pd.Series:
        """Simplified ADX calculation"""
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        return dx.rolling(14).mean()
    
    # ============================================================================
    # MULTI-FACTOR STRATEGIES
    # ============================================================================
    
    def multi_factor_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Multi-factor momentum strategy with quality filters
        """
        df = df.copy()
        
        # Price momentum factors
        df['mom_1m'] = df['close'].pct_change(30)
        df['mom_3m'] = df['close'].pct_change(90)
        df['mom_6m'] = df['close'].pct_change(180)
        
        # Volatility-adjusted momentum
        volatility = df['close'].pct_change().rolling(30).std()
        df['risk_adj_mom'] = df['mom_1m'] / (volatility * np.sqrt(30))
        
        # Volume confirmation
        volume_sma = df['volume'].rolling(30).mean()
        df['volume_trend'] = df['volume'] / volume_sma
        
        # Trend quality - consistency of returns
        df['trend_quality'] = df['close'].pct_change().rolling(30).apply(
            lambda x: (x > 0).sum() / len(x) if len(x) > 0 else 0.5
        )
        
        # Composite signal
        df['momentum_score'] = (
            0.4 * df['mom_1m'].rolling(5).mean() +
            0.3 * df['mom_3m'].rolling(5).mean() +
            0.2 * df['risk_adj_mom'].rolling(5).mean() +
            0.1 * (df['volume_trend'] - 1) * 0.1
        )
        
        # Signal generation with regime awareness
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        for i in range(len(df)):
            if i < 180:
                continue
            
            score = df['momentum_score'].iloc[i]
            quality = df['trend_quality'].iloc[i]
            volume = df['volume_trend'].iloc[i]
            
            # Strong signal requires quality and volume
            if score > 0.05 and quality > 0.6 and volume > 1.0:
                df.loc[df.index[i], 'signal'] = 1
                df.loc[df.index[i], 'signal_strength'] = min(abs(score) * 10, 1.0)
            elif score < -0.05 and quality < 0.4 and volume > 1.0:
                df.loc[df.index[i], 'signal'] = -1
                df.loc[df.index[i], 'signal_strength'] = min(abs(score) * 10, 1.0)
        
        return df
    
    def statistical_arbitrage(self, df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
        """
        Mean reversion strategy with statistical confidence
        """
        df = df.copy()
        
        # Z-score of price relative to moving average
        ma = df['close'].rolling(lookback).mean()
        std = df['close'].rolling(lookback).std()
        df['z_score'] = (df['close'] - ma) / std
        
        # Bollinger band position
        upper, middle, lower = self._calculate_bollinger(df['close'])
        df['bb_position'] = (df['close'] - lower) / (upper - lower)
        
        # RSI oversold/overbought
        df['rsi'] = self._calculate_rsi_simple(df['close'])
        
        # Mean reversion signal
        df['signal'] = 0
        df['signal_strength'] = 0.0
        df['confidence'] = 0.0
        
        for i in range(lookback, len(df)):
            z = df['z_score'].iloc[i]
            bb_pos = df['bb_position'].iloc[i]
            rsi = df['rsi'].iloc[i]
            
            # Statistical confidence based on z-score
            confidence = 2 * (1 - stats.norm.cdf(abs(z)))
            
            # Mean reversion entry: extreme z-score + RSI confirmation
            if z < -2.0 and bb_pos < 0.1 and rsi < 30 and confidence < 0.05:
                df.loc[df.index[i], 'signal'] = 1
                df.loc[df.index[i], 'signal_strength'] = min(abs(z) / 3, 1.0)
                df.loc[df.index[i], 'confidence'] = 1 - confidence
            elif z > 2.0 and bb_pos > 0.9 and rsi > 70 and confidence < 0.05:
                df.loc[df.index[i], 'signal'] = -1
                df.loc[df.index[i], 'signal_strength'] = min(abs(z) / 3, 1.0)
                df.loc[df.index[i], 'confidence'] = 1 - confidence
        
        return df
    
    def trend_following_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trend following with quality filters and adaptive position sizing
        """
        df = df.copy()
        
        # Multiple timeframe trends
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        
        # ADX for trend strength
        df['adx'] = self._calculate_adx_simple(df)
        
        # Trend alignment score
        df['trend_score'] = 0
        df.loc[df['close'] > df['sma_20'], 'trend_score'] += 1
        df.loc[df['sma_20'] > df['sma_50'], 'trend_score'] += 1
        df.loc[df['sma_50'] > df['sma_200'], 'trend_score'] += 1
        df.loc[df['close'] < df['sma_20'], 'trend_score'] -= 1
        df.loc[df['sma_20'] < df['sma_50'], 'trend_score'] -= 1
        df.loc[df['sma_50'] < df['sma_200'], 'trend_score'] -= 1
        
        # Signal generation
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        for i in range(200, len(df)):
            trend = df['trend_score'].iloc[i]
            adx = df['adx'].iloc[i]
            
            # Only trade strong trends
            if abs(trend) >= 2 and adx > 25:
                df.loc[df.index[i], 'signal'] = 1 if trend > 0 else -1
                df.loc[df.index[i], 'signal_strength'] = min(adx / 50, 1.0)
        
        return df
    
    def volatility_breakout(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Volatility expansion breakout strategy
        """
        df = df.copy()
        
        # ATR for volatility measurement
        df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
        df['atr_pct'] = df['atr'] / df['close']
        
        # Volatility regime
        df['atr_ma'] = df['atr'].rolling(20).mean()
        df['vol_regime'] = df['atr'] / df['atr_ma']
        
        # Donchian channels
        df['donchian_upper'] = df['high'].rolling(20).max()
        df['donchian_lower'] = df['low'].rolling(20).min()
        
        # Breakout detection with volume
        volume_ma = df['volume'].rolling(20).mean()
        
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        for i in range(20, len(df)):
            # Breakout above upper channel
            if (df['close'].iloc[i] > df['donchian_upper'].iloc[i-1] and 
                df['vol_regime'].iloc[i] > 1.2 and
                df['volume'].iloc[i] > volume_ma.iloc[i] * 1.5):
                df.loc[df.index[i], 'signal'] = 1
                df.loc[df.index[i], 'signal_strength'] = min(df['vol_regime'].iloc[i] - 1, 1.0)
            
            # Breakdown below lower channel
            elif (df['close'].iloc[i] < df['donchian_lower'].iloc[i-1] and 
                  df['vol_regime'].iloc[i] > 1.2 and
                  df['volume'].iloc[i] > volume_ma.iloc[i] * 1.5):
                df.loc[df.index[i], 'signal'] = -1
                df.loc[df.index[i], 'signal_strength'] = min(df['vol_regime'].iloc[i] - 1, 1.0)
        
        return df
    
    def _calculate_bollinger(self, series: pd.Series, window: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return upper, middle, lower
    
    def _calculate_rsi_simple(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    # ============================================================================
    # RISK MANAGEMENT
    # ============================================================================
    
    def calculate_position_size(
        self,
        signal_strength: float,
        volatility: float,
        confidence: float = 0.5
    ) -> float:
        """
        Kelly-inspired position sizing with risk constraints
        """
        if volatility == 0:
            return 0
        
        # Risk-adjusted position size
        risk_budget = self.current_capital * self.risk_params.risk_per_trade
        
        # Volatility targeting - lower size in high vol
        vol_scalar = 0.02 / max(volatility, 0.01)  # Target 2% daily vol
        
        # Kelly fraction (simplified)
        win_rate = 0.55  # Assumed based on backtests
        avg_win = 1.5
        avg_loss = 1.0
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly = max(0, min(kelly * 0.25, 0.25))  # Quarter Kelly, max 25%
        
        # Combine factors
        base_size = kelly * vol_scalar * signal_strength * confidence
        
        # Apply constraints
        max_size = self.risk_params.max_position_size * self.current_capital
        position_size = min(base_size * self.current_capital, max_size)
        
        return max(0, position_size)
    
    def check_risk_limits(self, new_position_value: float) -> bool:
        """
        Check if new position violates risk limits
        """
        # Check drawdown limit
        if self.drawdown < self.risk_params.max_drawdown_limit:
            return False
        
        # Check portfolio heat
        total_exposure = sum(abs(v) for v in self.positions.values()) + abs(new_position_value)
        if total_exposure > self.risk_params.max_portfolio_heat * self.current_capital:
            return False
        
        # Check consecutive losses
        if self.consecutive_losses >= self.risk_params.max_consecutive_losses:
            return False
        
        return True
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk
        """
        if len(returns) < 30:
            return 0
        return np.percentile(returns.dropna(), (1 - confidence) * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall)
        """
        if len(returns) < 30:
            return 0
        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()
    
    # ============================================================================
    # EXECUTION SIMULATION
    # ============================================================================
    
    def calculate_slippage(
        self,
        price: float,
        volume: float,
        order_size: float,
        volatility: float
    ) -> float:
        """
        Realistic slippage model based on volatility and market impact
        """
        if self.execution_config.slippage_model == "fixed":
            return self.execution_config.slippage_base
        
        elif self.execution_config.slippage_model == "volatility_based":
            # Higher slippage in high volatility
            vol_factor = 1 + (volatility * 10)
            return self.execution_config.slippage_base * vol_factor
        
        elif self.execution_config.slippage_model == "volume_based":
            # Market impact based on order size relative to volume
            if volume == 0:
                return self.execution_config.slippage_base
            participation = order_size / volume
            impact = self.execution_config.market_impact_factor * participation
            return self.execution_config.slippage_base + impact
        
        return self.execution_config.slippage_base
    
    def simulate_execution(
        self,
        price: float,
        volume: float,
        order_size: float,
        side: str,
        volatility: float
    ) -> Tuple[float, float]:
        """
        Simulate trade execution with costs
        """
        slippage = self.calculate_slippage(price, volume, order_size, volatility)
        
        # Apply slippage
        if side == "buy":
            executed_price = price * (1 + slippage)
        else:
            executed_price = price * (1 - slippage)
        
        # Commission
        commission = executed_price * abs(order_size) * self.execution_config.commission_rate
        
        return executed_price, commission
    
    # ============================================================================
    # BACKTEST ENGINE
    # ============================================================================
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy_func: Callable,
        symbol: str = "CRYPTO"
    ) -> Dict:
        """
        Run professional backtest with full risk management
        """
        df = strategy_func(df)
        
        if 'signal' not in df.columns:
            raise ValueError("Strategy must produce 'signal' column")
        
        # Initialize tracking
        position = 0.0
        entry_price = 0.0
        entry_time = None
        max_price_since_entry = 0.0
        min_price_since_entry = float('inf')
        
        trades = []
        equity_curve = []
        
        for i in range(1, len(df)):
            timestamp = df.index[i]
            current_price = df['close'].iloc[i]
            prev_price = df['close'].iloc[i-1]
            signal = df['signal'].iloc[i-1]  # Use previous signal for next bar execution
            signal_strength = df.get('signal_strength', pd.Series([0.5] * len(df))).iloc[i-1]
            confidence = df.get('confidence', pd.Series([0.5] * len(df))).iloc[i-1]
            volume = df['volume'].iloc[i] if 'volume' in df else 0
            
            # Calculate daily return for equity tracking
            daily_return = (current_price - prev_price) / prev_price if prev_price != 0 else 0
            
            # Update position P&L
            if position != 0:
                position_pnl = position * daily_return
                self.current_capital += position_pnl
                
                # Track max price for trailing stop
                if position > 0:
                    max_price_since_entry = max(max_price_since_entry, current_price)
                    min_price_since_entry = current_price
                else:
                    min_price_since_entry = min(min_price_since_entry, current_price)
                    max_price_since_entry = current_price
            
            # Calculate volatility for position sizing
            if i >= 30:
                volatility = df['close'].iloc[max(0, i-30):i].pct_change().std()
            else:
                volatility = 0.02
            
            # Check stop losses and take profits
            if position != 0 and entry_price != 0:
                pnl_pct = (current_price - entry_price) / entry_price if position > 0 else (entry_price - current_price) / entry_price
                
                # Stop loss
                if pnl_pct < -self.risk_params.stop_loss_pct:
                    exit_price, commission = self.simulate_execution(
                        current_price, volume, abs(position), "sell" if position > 0 else "buy", volatility
                    )
                    pnl = position * (exit_price - entry_price) / entry_price - commission
                    
                    trades.append(Trade(
                        entry_time=entry_time,
                        exit_time=timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position=position,
                        side="long" if position > 0 else "short",
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason="stop_loss",
                        holding_periods=i - df.index.get_loc(entry_time) if entry_time in df.index else 0
                    ))
                    
                    self.current_capital -= commission
                    position = 0
                    self.consecutive_losses += 1
                    continue
                
                # Take profit
                if pnl_pct > self.risk_params.take_profit_pct:
                    exit_price, commission = self.simulate_execution(
                        current_price, volume, abs(position), "sell" if position > 0 else "buy", volatility
                    )
                    pnl = position * (exit_price - entry_price) / entry_price - commission
                    
                    trades.append(Trade(
                        entry_time=entry_time,
                        exit_time=timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position=position,
                        side="long" if position > 0 else "short",
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason="take_profit",
                        holding_periods=i - df.index.get_loc(entry_time) if entry_time in df.index else 0
                    ))
                    
                    self.current_capital -= commission
                    position = 0
                    self.consecutive_losses = 0
                    continue
                
                # Trailing stop
                if position > 0:
                    trail_pct = (max_price_since_entry - current_price) / max_price_since_entry
                else:
                    trail_pct = (current_price - min_price_since_entry) / min_price_since_entry
                
                if trail_pct > self.risk_params.trailing_stop_pct:
                    exit_price, commission = self.simulate_execution(
                        current_price, volume, abs(position), "sell" if position > 0 else "buy", volatility
                    )
                    pnl = position * (exit_price - entry_price) / entry_price - commission
                    
                    trades.append(Trade(
                        entry_time=entry_time,
                        exit_time=timestamp,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position=position,
                        side="long" if position > 0 else "short",
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason="trailing_stop",
                        holding_periods=i - df.index.get_loc(entry_time) if entry_time in df.index else 0
                    ))
                    
                    self.current_capital -= commission
                    position = 0
                    self.consecutive_losses += 1 if pnl < 0 else 0
                    continue
            
            # Signal-based entry/exit
            if signal != 0 and position == 0:
                # Check risk limits
                position_value = self.calculate_position_size(signal_strength, volatility, confidence)
                
                if self.check_risk_limits(position_value):
                    side = "buy" if signal > 0 else "sell"
                    entry_price, commission = self.simulate_execution(
                        current_price, volume, position_value, side, volatility
                    )
                    position = position_value / entry_price if signal > 0 else -position_value / entry_price
                    entry_time = timestamp
                    max_price_since_entry = current_price
                    min_price_since_entry = current_price
                    self.current_capital -= commission
            
            elif signal != 0 and ((position > 0 and signal < 0) or (position < 0 and signal > 0)):
                # Reverse position
                exit_price, commission = self.simulate_execution(
                    current_price, volume, abs(position), "sell" if position > 0 else "buy", volatility
                )
                pnl = position * (exit_price - entry_price) / entry_price - commission
                
                trades.append(Trade(
                    entry_time=entry_time,
                    exit_time=timestamp,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    position=position,
                    side="long" if position > 0 else "short",
                    pnl=pnl,
                    pnl_pct=(exit_price - entry_price) / entry_price if position > 0 else (entry_price - exit_price) / entry_price,
                    exit_reason="signal_reverse",
                    holding_periods=i - df.index.get_loc(entry_time) if entry_time in df.index else 0
                ))
                
                self.current_capital -= commission
                self.consecutive_losses += 1 if pnl < 0 else 0
                
                # Enter new position
                position_value = self.calculate_position_size(signal_strength, volatility, confidence)
                if self.check_risk_limits(position_value):
                    side = "buy" if signal > 0 else "sell"
                    entry_price, commission = self.simulate_execution(
                        current_price, volume, position_value, side, volatility
                    )
                    position = position_value / entry_price if signal > 0 else -position_value / entry_price
                    entry_time = timestamp
                    max_price_since_entry = current_price
                    min_price_since_entry = current_price
                    self.current_capital -= commission
            
            # Update equity curve
            self.returns.append(daily_return)
            equity_curve.append({
                'timestamp': timestamp,
                'equity': self.current_capital,
                'position': position,
                'price': current_price
            })
            
            # Update drawdown
            if self.current_capital > self.max_equity:
                self.max_equity = self.current_capital
            self.drawdown = (self.current_capital - self.max_equity) / self.max_equity
        
        # Close any open position at the end
        if position != 0:
            final_price = df['close'].iloc[-1]
            pnl = position * (final_price - entry_price) / entry_price
            
            trades.append(Trade(
                entry_time=entry_time,
                exit_time=df.index[-1],
                entry_price=entry_price,
                exit_price=final_price,
                position=position,
                side="long" if position > 0 else "short",
                pnl=pnl,
                pnl_pct=(final_price - entry_price) / entry_price if position > 0 else (entry_price - final_price) / entry_price,
                exit_reason="end_of_data",
                holding_periods=len(df) - df.index.get_loc(entry_time) if entry_time in df.index else 0
            ))
        
        self.trades = trades
        self.equity_curve = equity_curve
        
        return self._calculate_performance_metrics(df, trades, equity_curve)
    
    def _calculate_performance_metrics(
        self,
        df: pd.DataFrame,
        trades: List[Trade],
        equity_curve: List[Dict]
    ) -> Dict:
        """
        Calculate comprehensive hedge fund performance metrics
        """
        if not trades or not equity_curve:
            return self._empty_metrics()
        
        # Extract P&L series
        trade_pnls = [t.pnl for t in trades]
        returns_series = pd.Series([e['equity'] for e in equity_curve]).pct_change().dropna()
        
        if len(returns_series) == 0:
            return self._empty_metrics()
        
        # Basic returns
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # Annualized metrics (assuming daily data)
        periods_per_year = 365
        mean_return = returns_series.mean()
        volatility = returns_series.std()
        
        annualized_return = mean_return * periods_per_year
        annualized_vol = volatility * np.sqrt(periods_per_year)
        
        # Sharpe Ratio (assuming 0 risk-free rate for crypto)
        sharpe_ratio = annualized_return / annualized_vol if annualized_vol != 0 else 0
        
        # Sortino Ratio (downside deviation only)
        downside_returns = returns_series[returns_series < 0]
        downside_dev = downside_returns.std() * np.sqrt(periods_per_year) if len(downside_returns) > 0 else 0
        sortino_ratio = annualized_return / downside_dev if downside_dev != 0 else 0
        
        # Maximum Drawdown
        equity_values = [e['equity'] for e in equity_curve]
        peak = equity_values[0]
        max_dd = 0
        for eq in equity_values:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Calmar Ratio
        calmar_ratio = annualized_return / max_dd if max_dd != 0 else 0
        
        # VaR and CVaR
        var_95 = self.calculate_var(returns_series, 0.95)
        var_99 = self.calculate_var(returns_series, 0.99)
        cvar_95 = self.calculate_cvar(returns_series, 0.95)
        cvar_99 = self.calculate_cvar(returns_series, 0.99)
        
        # Trade statistics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        profit_factor = abs(sum(t.pnl for t in winning_trades)) / abs(sum(t.pnl for t in losing_trades)) if losing_trades else float('inf')
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Payoff ratio
        payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
        
        # Maximum consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for t in trades:
            if t.pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # Average holding period
        avg_holding = np.mean([t.holding_periods for t in trades]) if trades else 0
        
        # Skewness and Kurtosis
        skewness = returns_series.skew()
        kurtosis = returns_series.kurtosis()
        
        # Omega Ratio
        threshold = 0  # Risk-free rate
        positive_returns = returns_series[returns_series > threshold].sum()
        negative_returns = abs(returns_series[returns_series < threshold].sum())
        omega_ratio = positive_returns / negative_returns if negative_returns != 0 else float('inf')
        
        return {
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100,
            'annualized_volatility_pct': annualized_vol * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'omega_ratio': omega_ratio,
            'max_drawdown_pct': max_dd * 100,
            'var_95_pct': var_95 * 100,
            'var_99_pct': var_99 * 100,
            'cvar_95_pct': cvar_95 * 100,
            'cvar_99_pct': cvar_99 * 100,
            'skewness': skewness,
            'excess_kurtosis': kurtosis,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': win_rate * 100,
            'profit_factor': profit_factor,
            'payoff_ratio': payoff_ratio,
            'expectancy': expectancy,
            'avg_trade_return': np.mean(trade_pnls) if trade_pnls else 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_holding_periods': avg_holding,
            'final_capital': self.current_capital,
            'equity_curve': equity_curve,
            'trades': trades
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'total_return_pct': 0,
            'annualized_return_pct': 0,
            'annualized_volatility_pct': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0,
            'max_drawdown_pct': 0,
            'total_trades': 0,
            'win_rate_pct': 0,
            'final_capital': self.initial_capital
        }
    
    # ============================================================================
    # STRATEGY COMPARISON
    # ============================================================================
    
    def run_strategy_comparison(
        self,
        df: pd.DataFrame,
        strategies: Optional[Dict[str, Callable]] = None
    ) -> pd.DataFrame:
        """
        Run multiple strategies and compare results
        """
        if strategies is None:
            strategies = {
                'Multi_Factor_Momentum': self.multi_factor_momentum,
                'Statistical_Arbitrage': self.statistical_arbitrage,
                'Trend_Following_Quality': self.trend_following_quality,
                'Volatility_Breakout': self.volatility_breakout
            }
        
        results = []
        
        for name, strategy in strategies.items():
            print(f"Running {name}...")
            try:
                # Reset state for each strategy
                self.current_capital = self.initial_capital
                self.positions = {}
                self.trades = []
                self.equity_curve = []
                self.consecutive_losses = 0
                self.max_equity = self.initial_capital
                self.drawdown = 0
                
                metrics = self.run_backtest(df.copy(), strategy)
                metrics['strategy'] = name
                results.append(metrics)
            except Exception as e:
                print(f"Error in {name}: {e}")
        
        # Create comparison DataFrame
        comparison = pd.DataFrame([{
            'strategy': r['strategy'],
            'total_return_pct': r['total_return_pct'],
            'sharpe_ratio': r['sharpe_ratio'],
            'sortino_ratio': r['sortino_ratio'],
            'calmar_ratio': r['calmar_ratio'],
            'max_drawdown_pct': r['max_drawdown_pct'],
            'win_rate_pct': r['win_rate_pct'],
            'total_trades': r['total_trades'],
            'profit_factor': r.get('profit_factor', 0),
            'expectancy': r.get('expectancy', 0),
            'var_95_pct': r['var_95_pct'],
            'final_capital': r['final_capital']
        } for r in results])
        
        return comparison.sort_values('sharpe_ratio', ascending=False)

    # ============================================================================
    # MULTI-COIN PORTFOLIO BACKTESTING
    # ============================================================================
    
    def run_multi_coin_backtest(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy_func: Callable,
        portfolio_config: Optional[PortfolioConfig] = None
    ) -> Dict:
        """
        Run backtest across multiple coins with portfolio management
        
        Args:
            data_dict: Dictionary of {coin: DataFrame} with OHLCV data
            strategy_func: Strategy function to apply to each coin
            portfolio_config: Portfolio configuration
            
        Returns:
            Dictionary with portfolio results
        """
        if portfolio_config is None:
            portfolio_config = PortfolioConfig(
                coins=list(data_dict.keys()),
                timeframe="1h",
                max_coins_held=min(5, len(data_dict)),
                equal_weight=False
            )
        
        # Run individual coin backtests
        coin_results = {}
        all_trades = []
        
        for coin, df in data_dict.items():
            if len(df) < 50:
                continue
            
            print(f"Running backtest for {coin}...")
            
            # Reset state
            self.current_capital = self.initial_capital / len(data_dict)  # Equal allocation
            self.positions = {}
            self.trades = []
            self.equity_curve = []
            self.consecutive_losses = 0
            self.max_equity = self.current_capital
            self.drawdown = 0
            
            try:
                result = self.run_backtest(df.copy(), strategy_func)
                result['coin'] = coin
                coin_results[coin] = result
                
                # Tag trades with coin
                for trade in result.get('trades', []):
                    trade.coin = coin
                    all_trades.append(trade)
                    
            except Exception as e:
                print(f"Error in {coin}: {e}")
        
        # Calculate portfolio-level metrics
        portfolio_metrics = self._calculate_portfolio_metrics(coin_results, all_trades)
        portfolio_metrics['coin_results'] = coin_results
        portfolio_metrics['trades'] = all_trades
        portfolio_metrics['config'] = portfolio_config
        
        return portfolio_metrics
    
    def run_multi_strategy_multi_coin(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategies: Optional[Dict[str, Callable]] = None
    ) -> pd.DataFrame:
        """
        Run multiple strategies across multiple coins
        
        Returns DataFrame with strategy-coin combinations ranked by Sharpe
        """
        if strategies is None:
            strategies = {
                'Multi_Factor_Momentum': self.multi_factor_momentum,
                'Statistical_Arbitrage': self.statistical_arbitrage,
                'Trend_Following_Quality': self.trend_following_quality,
                'Volatility_Breakout': self.volatility_breakout
            }
        
        results = []
        
        for coin, df in data_dict.items():
            if len(df) < 50:
                continue
            
            for strategy_name, strategy_func in strategies.items():
                try:
                    # Reset state
                    self.current_capital = self.initial_capital
                    self.positions = {}
                    self.trades = []
                    self.equity_curve = []
                    self.consecutive_losses = 0
                    self.max_equity = self.initial_capital
                    self.drawdown = 0
                    
                    result = self.run_backtest(df.copy(), strategy_func)
                    
                    results.append({
                        'coin': coin,
                        'strategy': strategy_name,
                        'total_return_pct': result['total_return_pct'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'sortino_ratio': result['sortino_ratio'],
                        'max_drawdown_pct': result['max_drawdown_pct'],
                        'win_rate_pct': result['win_rate_pct'],
                        'total_trades': result['total_trades'],
                        'profit_factor': result.get('profit_factor', 0),
                        'var_95_pct': result['var_95_pct'],
                        'final_capital': result['final_capital']
                    })
                    
                except Exception as e:
                    print(f"Error in {coin} {strategy_name}: {e}")
        
        if results:
            return pd.DataFrame(results).sort_values('sharpe_ratio', ascending=False)
        return pd.DataFrame()
    
    def _calculate_portfolio_metrics(
        self,
        coin_results: Dict[str, Dict],
        all_trades: List[Trade]
    ) -> Dict:
        """Calculate aggregate portfolio performance metrics"""
        if not coin_results:
            return self._empty_metrics()
        
        # Aggregate returns
        total_pnl = sum(r.get('final_capital', 0) - self.initial_capital / len(coin_results) 
                        for r in coin_results.values())
        total_return = total_pnl / self.initial_capital
        
        # Aggregate trade statistics
        winning_trades = [t for t in all_trades if t.pnl > 0]
        losing_trades = [t for t in all_trades if t.pnl < 0]
        
        total_trades = len(all_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Average metrics across coins
        sharpe_ratios = [r['sharpe_ratio'] for r in coin_results.values()]
        max_drawdowns = [r['max_drawdown_pct'] for r in coin_results.values()]
        
        return {
            'total_return_pct': total_return * 100,
            'total_trades': total_trades,
            'win_rate_pct': win_rate * 100,
            'avg_sharpe_ratio': np.mean(sharpe_ratios),
            'avg_max_drawdown_pct': np.mean(max_drawdowns),
            'best_coin': max(coin_results.items(), key=lambda x: x[1]['total_return_pct'])[0] if coin_results else None,
            'worst_coin': min(coin_results.items(), key=lambda x: x[1]['total_return_pct'])[0] if coin_results else None,
            'num_coins': len(coin_results),
            'total_pnl': total_pnl
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_sample_data(days: int = 365, trend: float = 0.0002, volatility: float = 0.02) -> pd.DataFrame:
    """Generate sample price data for testing"""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days*24, freq='H')
    
    returns = np.random.normal(trend/24, volatility/np.sqrt(24), len(dates))
    prices = 100 * np.exp(np.cumsum(returns))
    
    # Generate OHLC
    df = pd.DataFrame(index=dates)
    df['close'] = prices
    df['open'] = prices * (1 + np.random.normal(0, 0.001, len(dates)))
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + abs(np.random.normal(0, 0.005, len(dates))))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - abs(np.random.normal(0, 0.005, len(dates))))
    df['volume'] = np.random.lognormal(15, 0.5, len(dates))
    
    return df


if __name__ == "__main__":
    # Test the hedge fund backtester
    print("=" * 70)
    print("HEDGE FUND LEVEL BACKTESTING SYSTEM - MULTI-COIN & TIMEFRAME")
    print("=" * 70)
    
    # Initialize data manager
    data_manager = MultiCoinDataManager(exchange="binance")
    
    # Define coins (10 total) and timeframes to test
    coins = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOGE", "DOT", "LINK"]
    timeframe = "1h"  # Options: 15m, 30m, 1h, 4h, 1d
    days = 60  # Lookback period
    
    print(f"\nFetching data for {len(coins)} coins: {coins}")
    print(f"Timeframe: {timeframe}, Lookback: {days} days")
    print("-" * 70)
    
    # Fetch data for all coins
    multi_coin_data = data_manager.fetch_multi_coin_data(coins, timeframe, days)
    
    if not multi_coin_data:
        print("No data fetched, exiting...")
        exit(1)
    
    print(f"\nSuccessfully loaded data for {len(multi_coin_data)} coins")
    for coin, df in multi_coin_data.items():
        print(f"  {coin}: {len(df)} candles | {df.index[0]} to {df.index[-1]}")
    
    # Initialize backtester with professional settings
    risk_params = RiskParameters(
        max_position_size=0.20,
        max_portfolio_heat=0.60,
        max_drawdown_limit=-0.15,
        stop_loss_pct=0.05,
        take_profit_pct=0.15,
        trailing_stop_pct=0.08,
        risk_per_trade=0.02
    )
    
    execution_config = ExecutionConfig(
        commission_rate=0.001,
        slippage_model="volatility_based",
        slippage_base=0.0005
    )
    
    backtester = HedgeFundBacktester(
        initial_capital=100000.0,
        risk_params=risk_params,
        execution_config=execution_config
    )
    
    # Multi-coin backtest with single strategy
    print("\n" + "=" * 70)
    print("MULTI-COIN BACKTEST: Multi-Factor Momentum Strategy")
    print("=" * 70)
    
    portfolio_config = PortfolioConfig(
        coins=coins,
        timeframe=timeframe,
        max_coins_held=3,
        equal_weight=True
    )
    
    portfolio_result = backtester.run_multi_coin_backtest(
        multi_coin_data,
        backtester.multi_factor_momentum,
        portfolio_config
    )
    
    print(f"\nPortfolio Summary:")
    print(f"  Total Return: {portfolio_result['total_return_pct']:.2f}%")
    print(f"  Total Trades: {portfolio_result['total_trades']}")
    print(f"  Win Rate: {portfolio_result['win_rate_pct']:.1f}%")
    print(f"  Avg Sharpe: {portfolio_result['avg_sharpe_ratio']:.3f}")
    print(f"  Avg Max DD: {portfolio_result['avg_max_drawdown_pct']:.2f}%")
    print(f"  Best Coin: {portfolio_result['best_coin']}")
    print(f"  Worst Coin: {portfolio_result['worst_coin']}")
    
    # Multi-strategy, multi-coin comparison
    print("\n" + "=" * 70)
    print("STRATEGY-COIN MATRIX (Top 10 by Sharpe)")
    print("=" * 70)
    
    matrix = backtester.run_multi_strategy_multi_coin(multi_coin_data)
    if not matrix.empty:
        print(matrix.head(10).to_string(index=False))
    
    # Single coin, single timeframe deep analysis
    print("\n" + "=" * 70)
    print("DEEP ANALYSIS: BTC 1H - All Strategies")
    print("=" * 70)
    
    if "BTC" in multi_coin_data:
        btc_comparison = backtester.run_strategy_comparison(multi_coin_data["BTC"])
        print(btc_comparison.to_string(index=False))
        
        best_strategy = btc_comparison.iloc[0]['strategy']
        print(f"\nBest Strategy for BTC: {best_strategy}")
        print(f"  Return: {btc_comparison.iloc[0]['total_return_pct']:.2f}%")
        print(f"  Sharpe: {btc_comparison.iloc[0]['sharpe_ratio']:.3f}")
    
    print("\n" + "=" * 70)
    print("BACKTESTING COMPLETE")
    print("=" * 70)
    print(f"\nSupported Timeframes: {list(TIMEFRAMES.keys())}")
    print(f"Supported Coins: {SUPPORTED_COINS}")
