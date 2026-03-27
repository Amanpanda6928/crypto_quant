"""
Run Backtest - Fixed (Multi-Asset + Fast + Consistent)
"""

import pandas as pd
import numpy as np
from typing import Dict

from ..data.build_dataset import DatasetBuilder
from .engine import BacktestEngine


class WalkForwardBacktest:

    def __init__(self, train_size=2000, test_size=500, step_size=500):
        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size
        self.results = []

    def run(self):
        from sklearn.ensemble import GradientBoostingClassifier

        print("Building multi-asset dataset...")

        builder = DatasetBuilder()
        full_df = builder.build_multi_asset(limit=5000)

        X, y, feature_cols, target_cols = builder.get_feature_target_split(full_df)

        # ✅ include symbol (already included in feature_cols)
        # feature_cols = feature_cols + ["symbol"]

        # encode symbol once
        full_df["symbol"] = full_df["symbol"].astype("category").cat.codes

        start = 0
        fold = 0

        while start + self.train_size + self.test_size <= len(full_df):

            fold += 1
            print(f"\nFold {fold}")

            train_df = full_df.iloc[start:start+self.train_size]
            test_df = full_df.iloc[start+self.train_size:start+self.train_size+self.test_size]

            # =========================
            # TRAIN
            # =========================

            models = {}

            for target_col in target_cols:
                horizon = target_col.replace("target_", "")

                X = train_df[feature_cols]
                y = train_df[target_col]

                model = GradientBoostingClassifier(
                    n_estimators=50,
                    max_depth=3,
                    random_state=42
                )

                model.fit(X, y)
                models[horizon] = model

            # =========================
            # PREDICT (FAST)
            # =========================

            pred_rows = []

            X_test = test_df[feature_cols]

            for horizon, model in models.items():

                probs = model.predict_proba(X_test)[:, 1]

                signals = np.where(probs > 0.6, "BUY",
                          np.where(probs < 0.4, "SELL", "HOLD"))

                temp = pd.DataFrame({
                    "open_time": test_df["open_time"].values,
                    "horizon": horizon,
                    "probability": probs,
                    "signal": signals
                })

                pred_rows.append(temp)

            pred_df = pd.concat(pred_rows, ignore_index=True)

            # =========================
            # BACKTEST
            # =========================

            engine = BacktestEngine()
            result = engine.run(test_df, pred_df)

            self.results.append(result)

            print(f"Return: {result['total_return_pct']:.2f}%")

            start += self.step_size

        return self.aggregate()

    # =========================
    # AGGREGATE
    # =========================

    def aggregate(self):

        avg_return = np.mean([r["total_return_pct"] for r in self.results])
        avg_dd = np.mean([r["max_drawdown_pct"] for r in self.results])
        avg_sharpe = np.mean([r["sharpe_ratio"] for r in self.results])

        all_trades = []
        for r in self.results:
            all_trades.extend(r["trades"])

        win_rate = (
            len([t for t in all_trades if t.pnl > 0]) / len(all_trades) * 100
            if all_trades else 0
        )

        print("\n=== FINAL RESULTS ===")
        print(f"Avg Return: {avg_return:.2f}%")
        print(f"Avg Drawdown: {avg_dd:.2f}%")
        print(f"Avg Sharpe: {avg_sharpe:.4f}")
        print(f"Win Rate: {win_rate:.2f}%")

        return {
            "avg_return": avg_return,
            "avg_drawdown": avg_dd,
            "avg_sharpe": avg_sharpe,
            "win_rate": win_rate
        }


# =========================
# SIMPLE RUN
# =========================

def run_simple_backtest():

    bt = WalkForwardBacktest()
    results = bt.run()

    return results