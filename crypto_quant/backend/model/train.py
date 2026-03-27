"""
Model Training - LightGBM (FINAL)
"""

import pickle, os, json
from datetime import datetime

from ..data.build_dataset import DatasetBuilder


class MultiHorizonTrainer:

    def __init__(self):
        self.models = {}
        self.metrics = {}

    def train_horizon(self, X_train, X_test, y_train, y_test, horizon):
        from lightgbm import LGBMClassifier
        from sklearn.metrics import roc_auc_score

        model = LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )

        model.fit(X_train, y_train)

        prob = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, prob)

        self.metrics[horizon] = {"auc": auc}
        print(f"{horizon}: AUC={auc:.4f}")

        return model

    def train(self, df, feature_cols, target_cols):

        X = df[feature_cols + ["symbol"]].copy()
        X["symbol"] = X["symbol"].astype("category").cat.codes

        split = int(len(X) * 0.7)

        for target in target_cols:
            horizon = target.replace("target_", "")
            y = df[target]

            model = self.train_horizon(
                X.iloc[:split], X.iloc[split:],
                y.iloc[:split], y.iloc[split:],
                horizon
            )

            self.models[horizon] = model

        return self.models

    def save(self, path="models"):
        os.makedirs(path, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        for h, m in self.models.items():
            with open(f"{path}/model_{h}_{ts}.pkl", "wb") as f:
                pickle.dump(m, f)

        with open(f"{path}/metrics_{ts}.json", "w") as f:
            json.dump(self.metrics, f)


def train_model(limit=1000, models_path: str | None = None):

    builder = DatasetBuilder()
    df = builder.build_multi_asset(limit=limit)

    X, y, features, targets = builder.get_feature_target_split(df)

    trainer = MultiHorizonTrainer()
    trainer.train(df, features, targets)
    if models_path is None:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_path = os.path.join(backend_dir, "models_store")

    trainer.save(path=models_path)

    return trainer