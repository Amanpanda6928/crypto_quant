"""
Feature Engineering Pipeline - Multi-Asset Safe (NO leakage)
"""

import pandas as pd
import numpy as np
from typing import List


class FeaturePipeline:

    def __init__(self):
        self.feature_columns: List[str] = []

    # =====================================================
    # 🔥 TECHNICAL INDICATORS (GROUPED BY SYMBOL)
    # =====================================================

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df = df.sort_values(["symbol", "open_time"])

        # EMA
        df["ema_20"] = df.groupby("symbol")["close"].transform(
            lambda x: x.ewm(span=20, adjust=False).mean()
        )

        df["ema_50"] = df.groupby("symbol")["close"].transform(
            lambda x: x.ewm(span=50, adjust=False).mean()
        )

        # RSI
        def compute_rsi(x):
            delta = x.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df["rsi_14"] = df.groupby("symbol")["close"].transform(compute_rsi)

        # Bollinger Bands
        df["bb_middle"] = df.groupby("symbol")["close"].transform(
            lambda x: x.rolling(20).mean()
        )

        bb_std = df.groupby("symbol")["close"].transform(
            lambda x: x.rolling(20).std()
        )

        df["bb_upper"] = df["bb_middle"] + 2 * bb_std
        df["bb_lower"] = df["bb_middle"] - 2 * bb_std

        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        return df

    # =====================================================
    # 🔥 FEATURE ENGINEERING (GROUPED)
    # =====================================================

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Returns
        df["ret_1"] = df.groupby("symbol")["close"].pct_change(1).fillna(0)
        df["ret_5"] = df.groupby("symbol")["close"].pct_change(5).fillna(0)

        # 🔥 FIX 5: Enhanced Momentum (multiple windows)
        df["momentum_5"] = df.groupby("symbol")["close"].pct_change(5).fillna(0)
        df["momentum_10"] = df.groupby("symbol")["close"].pct_change(10).fillna(0)
        df["momentum_20"] = df.groupby("symbol")["close"].pct_change(20).fillna(0)
        df["momentum_ratio"] = df["momentum_10"] / (df["momentum_5"] + 1e-8)  # Momentum acceleration

        # 🔥 FIX 5: ATR (Average True Range) - True Volatility measure
        # Create TR using vectorized approach without groupby apply
        df = df.sort_values(["symbol", "open_time"])
        df["prev_close"] = df.groupby("symbol")["close"].shift(1)
        
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = (df["high"] - df["prev_close"]).abs()
        df["tr3"] = (df["low"] - df["prev_close"]).abs()
        
        tr_values = pd.concat([df["tr1"], df["tr2"], df["tr3"]], axis=1)
        df["tr"] = tr_values.max(axis=1)
        
        df["atr_14"] = df.groupby("symbol")["tr"].transform(
            lambda x: x.rolling(14).mean()
        )
        
        df["atr_ratio"] = (df["atr_14"] / df["close"]).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        # Clean up intermediate columns
        df = df.drop(["prev_close", "tr1", "tr2", "tr3"], axis=1)

        # 🔥 FIX 5: Enhanced Volatility (multiple windows)
        df["volatility_5"] = df.groupby("symbol")["ret_1"].transform(
            lambda x: x.rolling(5).std()
        )
        
        df["volatility_10"] = df.groupby("symbol")["ret_1"].transform(
            lambda x: x.rolling(10).std()
        )

        df["volatility_30"] = df.groupby("symbol")["ret_1"].transform(
            lambda x: x.rolling(30).std()
        )
        
        df["volatility_ratio"] = (df["volatility_10"] / (df["volatility_5"] + 1e-8))  # Vol spike detection

        # EMA-based
        df["ema_ratio"] = (df["ema_20"] / df["ema_50"]).replace([float('inf'), -float('inf')], 0).fillna(0)
        df["ema_distance"] = ((df["close"] - df["ema_20"]) / df["ema_20"]).replace([float('inf'), -float('inf')], 0).fillna(0)

        # 🔥 FIX 5: Enhanced Volume signals
        df["volume_sma_10"] = df.groupby("symbol")["volume"].transform(
            lambda x: x.rolling(10).mean()
        )
        
        df["volume_sma_20"] = df.groupby("symbol")["volume"].transform(
            lambda x: x.rolling(20).mean()
        )

        # Volume spike detection (current vs 20-bar average)
        df["volume_spike_20"] = (df["volume"] / (df["volume_sma_20"] + 1e-8)).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        # Volume spike detection (current vs 10-bar average) - more sensitive
        df["volume_spike_10"] = (df["volume"] / (df["volume_sma_10"] + 1e-8)).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        df["volume_change"] = df.groupby("symbol")["volume"].pct_change().fillna(0)
        
        # Volume trend
        df["volume_above_avg"] = (df["volume"] > df["volume_sma_20"]).astype(int)

        # Price ratios
        df["high_low_ratio"] = df["high"] / df["low"]
        df["close_open_ratio"] = df["close"] / df["open"]

        # Trend
        df["trend_ema20"] = (df["close"] > df["ema_20"]).astype(int)
        df["trend_ema50"] = (df["close"] > df["ema_50"]).astype(int)

        # Lag features
        for lag in [1, 2, 3, 5]:
            df[f"close_lag_{lag}"] = df.groupby("symbol")["close"].shift(lag)
            df[f"volume_lag_{lag}"] = df.groupby("symbol")["volume"].shift(lag)
            df[f"ret_lag_{lag}"] = df.groupby("symbol")["ret_1"].shift(lag)

        return df

    # =====================================================
    # 🔥 FEATURE SELECTION
    # =====================================================

    def select_feature_columns(self, df: pd.DataFrame) -> List[str]:
        exclude = [
            "open_time", "open", "high", "low", "close", "volume", "symbol",
            "target_5m", "target_10m", "target_30m", "target_1h", "target_4h", "target_1d",
            "future_ret_5m", "future_ret_10m", "future_ret_30m", "future_ret_1h", "future_ret_4h", "future_ret_1d",
            "tr",  # 🔥 Intermediate ATR calculation - exclude from features
            "volume_sma_10", "volume_sma_20"  # Intermediate calculations for spikes
        ]

        return [col for col in df.columns if col not in exclude]

    # =====================================================
    # 🔥 MAIN PIPELINE
    # =====================================================

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.add_technical_indicators(df)
        df = self.add_features(df)

        # Fill NaN values with 0 instead of dropping rows
        df = df.fillna(0)
        
        # Replace inf/-inf with 0
        df = df.replace([float('inf'), -float('inf')], 0)
        
        return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    return FeaturePipeline().transform(df)