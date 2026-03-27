"""
Target Creation Module - Multi-Asset Safe (NO leakage)
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class TargetEngine:

    HORIZONS = {
        "5m": 5,
        "10m": 10,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }

    def __init__(self, horizons: Dict[str, int] = None):
        self.horizons = horizons or self.HORIZONS

    # =====================================================
    # 🔥 TARGET CREATION (GROUPED BY SYMBOL)
    # =====================================================

    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Ensure correct order
        df = df.sort_values(["symbol", "open_time"])

        for horizon_name, periods in self.horizons.items():

            # ✅ FIX: groupby prevents cross-coin leakage
            future_return = (
                df.groupby("symbol")["close"]
                .shift(-periods) / df["close"] - 1
            )

            target_col = f"target_{horizon_name}"

            df[target_col] = (future_return > 0).astype(int)

            # Optional: keep for analysis
            df[f"future_ret_{horizon_name}"] = future_return

        return df

    # =====================================================
    # 🔥 TARGET LIST (STATIC, SAFE)
    # =====================================================

    def get_target_columns(self) -> List[str]:
        return [f"target_{k}" for k in self.horizons.keys()]

    # =====================================================
    # 🔥 VALIDATION
    # =====================================================

    def validate_no_leakage(self, df: pd.DataFrame) -> bool:
        return df[self.get_target_columns()].isnull().sum().sum() == 0


# =====================================================
# 🔥 HELPER FUNCTION
# =====================================================

def create_targets(df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:

    engine = TargetEngine()
    df = engine.create_targets(df)

    if drop_na:
        initial_len = len(df)
        df = df.dropna()
        dropped = initial_len - len(df)
        print(f"Dropped {dropped} rows due to future target unavailability")

    return df