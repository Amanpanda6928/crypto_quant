"""
Prediction Module - Multi-Asset Ready
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import pickle
import os
import glob

from ..data.api import BinanceDataFetcher
from ..features.pipeline import FeaturePipeline


class Predictor:

    def __init__(self, models_path: str | None = None):
        if models_path is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_path = os.path.join(backend_dir, "models_store")

        self.models_path = models_path
        self.models = {}
        self.feature_pipeline = FeaturePipeline()
        self.fetcher = BinanceDataFetcher()
        self.horizons = ["5m", "10m", "30m", "1h", "4h", "1d"]

    # =====================================================
    # 🔥 COMBINE MULTI-HORIZON PREDICTIONS
    # =====================================================

    def combine_multi_horizon(self, preds):
        # Backward-compatible: if some horizons aren't trained yet, ignore them.
        weights = {
            "5m": 0.25,
            "10m": 0.20,
            "30m": 0.15,
            "1h": 0.15,
            "4h": 0.15,
            "1d": 0.10,
        }

        present = {h: weights[h] for h in weights.keys() if h in preds}
        if not present:
            raise KeyError("No horizons available for combine_multi_horizon")

        total_w = sum(present.values())
        return sum(preds[h][0] * (w / total_w) for h, w in present.items())

    # =====================================================
    # 🔥 LOAD MODELS
    # =====================================================

    def load_latest_models(self):
        for horizon in self.horizons:
            files = glob.glob(f"{self.models_path}/model_{horizon}_*.pkl")

            if not files:
                raise FileNotFoundError(f"No model for {horizon}")

            latest = max(files, key=os.path.getctime)

            with open(latest, "rb") as f:
                self.models[horizon] = pickle.load(f)

        return self.models

    # =====================================================
    # 🔥 PREPARE FEATURES (FIXED)
    # =====================================================

    def prepare_features(self, df: pd.DataFrame, symbol: str):

        df = df.copy()
        df["symbol"] = symbol

        df = self.feature_pipeline.transform(df)

        feature_cols = self.feature_pipeline.select_feature_columns(df)

        X = df[feature_cols + ["symbol"]].iloc[-1:].copy()

        # Encode symbol (same as training)
        X["symbol"] = X["symbol"].astype("category").cat.codes

        return X

    # =====================================================
    # 🔥 PREDICT
    # =====================================================

    def predict(self, X: pd.DataFrame):

        if not self.models:
            self.load_latest_models()

        results = {}

        for horizon, model in self.models.items():

            prob = model.predict_proba(X)[0, 1]

            results[horizon] = (float(prob),)  # Return only probability, no signal

        return results

    # =====================================================
    # 🔥 SINGLE COIN PREDICTION
    # =====================================================

    def predict_single(self, symbol="BTCUSDT"):
        df = self.fetcher.fetch_ohlcv(symbol, limit=300)

        X = self.prepare_features(df, symbol)

        return self.predict(X)

    # =====================================================
    # 🔥 MULTI-COIN PREDICTION (IMPORTANT)
    # =====================================================

    def predict_all(self):

        market_data = self.fetcher.fetch_all_coins(limit=300)

        all_results = {}

        for symbol, df in market_data.items():

            try:
                X = self.prepare_features(df, symbol)
                preds = self.predict(X)
                all_results[symbol] = preds
            except Exception as e:
                # Skip symbols that fail to fetch/prepare/predict
                continue

        return all_results

    # =====================================================
    # 🔥 FORMAT OUTPUT
    # =====================================================

    def format_predictions(self, predictions):

        rows = []

        for horizon, (prob,) in predictions.items():  # Unpack single probability
            rows.append({
                "Horizon": horizon,
                "Prob_Up": round(prob, 4),
                "Confidence": round(abs(prob - 0.5) * 2, 4)
            })

        return pd.DataFrame(rows)


# =====================================================
# 🔥 QUICK FUNCTIONS
# =====================================================

def get_current_prediction(symbol="BTCUSDT"):
    predictor = Predictor()
    preds = predictor.predict_single(symbol)
    return predictor.format_predictions(preds)


def get_all_predictions():
    predictor = Predictor()
    return predictor.predict_all()