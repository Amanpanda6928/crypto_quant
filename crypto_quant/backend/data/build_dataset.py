"""
Dataset Builder - Multi-Asset (30 Coins) Quant Pipeline
"""

import pandas as pd
from typing import Tuple, List

# Add project root to path when run as script
if __name__ == "__main__":
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from crypto_quant.data.api import BinanceDataFetcher
    from crypto_quant.features.pipeline import FeaturePipeline
    from crypto_quant.features.targets import create_targets
else:
    from .api import BinanceDataFetcher
    from ..features.pipeline import FeaturePipeline
    from ..features.targets import create_targets


class DatasetBuilder:
    """
    Multi-asset dataset builder (quant-grade).

    Pipeline:
    1. Fetch multi-coin data
    2. Feature engineering per coin
    3. Target creation per coin
    4. Combine into single dataset
    """

    def __init__(self):
        self.data_fetcher = BinanceDataFetcher()
        self.feature_pipeline = FeaturePipeline()

    # =====================================================
    # 🔥 MAIN BUILD FUNCTION (MULTI-COIN)
    # =====================================================

    def build_multi_asset(
        self,
        interval: str = "1m",
        limit: int = 2000,
        symbols: list[str] | None = None,
        verbose: bool = True
    ) -> pd.DataFrame:
        """Build dataset for specified coins (default: all 30)."""

        if verbose:
            coin_count = len(symbols) if symbols else 30
            print(f"\nFetching multi-coin data for {coin_count} coins...")

        # Step 1: Fetch all coins
        market_data = self.data_fetcher.fetch_all_coins(
            interval=interval,
            limit=limit,
            symbols=symbols
        )

        processed_data = []

        # Step 2–3: Process each coin separately (IMPORTANT)
        for symbol, df in market_data.items():

            if verbose:
                print(f"\nProcessing {symbol}...")

            df = df.copy()
            df["symbol"] = symbol

            # Feature engineering (per coin)
            df = self.feature_pipeline.transform(df)

            # Target creation (per coin)
            df = create_targets(df, drop_na=False)

            # Drop only rows where the training horizons are unavailable.
            df = df.dropna(
                subset=[
                    "future_ret_5m",
                    "future_ret_10m",
                    "future_ret_30m",
                    "future_ret_1h",
                    "future_ret_4h",
                    "future_ret_1d",
                ]
            )

            if df.empty:
                if verbose:
                    print(f"[WARN] {symbol} has no rows after target alignment (increase --candles).")
                continue

            processed_data.append(df)

        if not processed_data:
            raise ValueError(
                "No data processed. Increase candles; for 1d horizon on 1m data use at least ~1600-2500 candles."
            )

        # Step 4: Combine all coins
        final_df = pd.concat(processed_data, ignore_index=True)
        final_df = final_df.sort_values(["open_time", "symbol"]).reset_index(drop=True)

        if verbose:
            print("\nFinal dataset built")
            print(f"Shape: {final_df.shape}")
            print(f"Coins: {final_df['symbol'].nunique()}")

        return final_df

    # =====================================================
    # 🔥 FEATURE / TARGET SPLIT
    # =====================================================

    def get_feature_target_split(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], List[str]]:

        feature_cols = self.feature_pipeline.select_feature_columns(df)
        target_cols = ["target_5m", "target_10m", "target_30m", "target_1h", "target_4h", "target_1d"]

        # Include symbol as categorical feature
        X = df[feature_cols + ["symbol"]].copy()
        y = df[target_cols].copy()

        return X, y, feature_cols, target_cols


# =====================================================
# 🔥 QUICK FUNCTION
# =====================================================

def build_dataset(limit: int = 2000) -> pd.DataFrame:
    builder = DatasetBuilder()
    return builder.build_multi_asset(limit=limit)


if __name__ == "__main__":
    # Run as a script
    df = build_dataset()
    print(f"Built dataset with shape: {df.shape}")
    print(df.head())