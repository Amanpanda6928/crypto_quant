"""
Feature Store Module
"""

import pandas as pd
import numpy as np
import pickle
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib


class FeatureStore:
    """
    Feature store for caching and retrieving computed features.

    Provides efficient storage and retrieval of features to avoid
    recomputation and enable feature reuse across different models.
    """

    def __init__(self, cache_dir: str = "cache/features"):
        """
        Initialize feature store.

        Args:
            cache_dir: Directory to store cached features
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, symbol: str, start_date: str, end_date: str,
                      features: List[str]) -> str:
        """
        Generate a unique cache key for the given parameters.

        Args:
            symbol: Trading symbol
            start_date: Start date string
            end_date: End date string
            features: List of feature names

        Returns:
            Cache key string
        """
        key_data = f"{symbol}_{start_date}_{end_date}_{'_'.join(sorted(features))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """Get full path for cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def store_features(self, symbol: str, start_date: str, end_date: str,
                      features: List[str], feature_data: pd.DataFrame,
                      metadata: Optional[Dict] = None) -> str:
        """
        Store computed features in cache.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            features: List of feature names
            feature_data: DataFrame with computed features
            metadata: Optional metadata dictionary

        Returns:
            Cache key for stored features
        """
        cache_key = self._get_cache_key(symbol, start_date, end_date, features)
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'features': features,
            'data': feature_data,
            'metadata': metadata or {},
            'created_at': datetime.now(),
            'version': '1.0'
        }

        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)

        return cache_key

    def get_features(self, symbol: str, start_date: str, end_date: str,
                    features: List[str]) -> Optional[pd.DataFrame]:
        """
        Retrieve cached features.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            features: List of feature names

        Returns:
            Cached feature DataFrame or None if not found
        """
        cache_key = self._get_cache_key(symbol, start_date, end_date, features)
        cache_path = self._get_cache_path(cache_key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # Validate cache data
            if (cache_data['symbol'] == symbol and
                cache_data['start_date'] == start_date and
                cache_data['end_date'] == end_date and
                set(cache_data['features']) == set(features)):

                # Check if cache is not too old (optional)
                created_at = cache_data.get('created_at')
                if created_at and (datetime.now() - created_at) > timedelta(days=7):
                    print(f"Warning: Cache for {symbol} is older than 7 days")

                return cache_data['data']

        except Exception as e:
            print(f"Error loading cache for {symbol}: {e}")
            # Remove corrupted cache file
            try:
                os.remove(cache_path)
            except:
                pass

        return None

    def list_cached_features(self) -> pd.DataFrame:
        """
        List all cached features with metadata.

        Returns:
            DataFrame with cache information
        """
        cache_info = []

        if not os.path.exists(self.cache_dir):
            return pd.DataFrame()

        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.pkl'):
                continue

            cache_path = os.path.join(self.cache_dir, filename)
            try:
                with open(cache_path, 'rb') as f:
                    cache_data = pickle.load(f)

                info = {
                    'cache_key': filename.replace('.pkl', ''),
                    'symbol': cache_data.get('symbol', 'unknown'),
                    'start_date': cache_data.get('start_date', 'unknown'),
                    'end_date': cache_data.get('end_date', 'unknown'),
                    'features': cache_data.get('features', []),
                    'num_features': len(cache_data.get('features', [])),
                    'data_shape': cache_data.get('data', pd.DataFrame()).shape,
                    'created_at': cache_data.get('created_at'),
                    'file_size_mb': os.path.getsize(cache_path) / (1024 * 1024)
                }
                cache_info.append(info)

            except Exception as e:
                print(f"Error reading cache file {filename}: {e}")

        return pd.DataFrame(cache_info)

    def clear_cache(self, older_than_days: Optional[int] = None,
                   symbol: Optional[str] = None) -> int:
        """
        Clear cache files.

        Args:
            older_than_days: Remove files older than this many days
            symbol: Remove files for specific symbol only

        Returns:
            Number of files removed
        """
        if not os.path.exists(self.cache_dir):
            return 0

        removed_count = 0

        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.pkl'):
                continue

            cache_path = os.path.join(self.cache_dir, filename)

            # Check symbol filter
            if symbol:
                try:
                    with open(cache_path, 'rb') as f:
                        cache_data = pickle.load(f)
                    if cache_data.get('symbol') != symbol:
                        continue
                except:
                    continue

            # Check age filter
            if older_than_days:
                file_age_days = (datetime.now() - datetime.fromtimestamp(
                    os.path.getctime(cache_path))).days
                if file_age_days < older_than_days:
                    continue

            # Remove file
            try:
                os.remove(cache_path)
                removed_count += 1
            except Exception as e:
                print(f"Error removing {filename}: {e}")

        return removed_count

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cache_df = self.list_cached_features()

        if cache_df.empty:
            return {'total_files': 0, 'total_size_mb': 0, 'symbols': []}

        return {
            'total_files': len(cache_df),
            'total_size_mb': cache_df['file_size_mb'].sum(),
            'symbols': cache_df['symbol'].unique().tolist(),
            'oldest_cache': cache_df['created_at'].min(),
            'newest_cache': cache_df['created_at'].max()
        }


if __name__ == "__main__":
    # Example usage
    store = FeatureStore()

    # Create sample feature data
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
        'sma_20': np.random.randn(100),
        'rsi': np.random.uniform(0, 100, 100),
        'macd': np.random.randn(100)
    })

    # Store features
    cache_key = store.store_features(
        symbol='BTCUSDT',
        start_date='2024-01-01',
        end_date='2024-01-05',
        features=['sma_20', 'rsi', 'macd'],
        feature_data=sample_data
    )

    print(f"Stored features with key: {cache_key}")

    # Retrieve features
    retrieved = store.get_features(
        symbol='BTCUSDT',
        start_date='2024-01-01',
        end_date='2024-01-05',
        features=['sma_20', 'rsi', 'macd']
    )

    print(f"Retrieved data shape: {retrieved.shape if retrieved is not None else 'None'}")

    # Show cache stats
    stats = store.get_cache_stats()
    print(f"Cache stats: {stats}")