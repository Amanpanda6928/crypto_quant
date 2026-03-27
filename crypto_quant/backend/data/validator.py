"""
Data validation module for crypto_quant.
Provides validation utilities for financial DataFrames.
"""

import pandas as pd


class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass


class DataValidator:
    """
    Validator class for checking DataFrame integrity and quality.
    
    Performs comprehensive validation checks on OHLCV financial data including:
    - Missing values
    - Negative prices
    - OHLC consistency
    - Duplicate timestamps
    - Time gaps
    - Volume anomalies
    - Price spikes (outliers)
    - Data types
    """
    
    DEFAULT_MIN_ROWS = 100
    
    def __init__(self, min_rows: int = None, strict: bool = True, expected_freq: str = "1min"):
        """
        Initialize validator with configurable thresholds.
        
        Args:
            min_rows: Minimum required rows
            strict: Enable strict validations (outliers, etc.)
            expected_freq: Expected time frequency (e.g., '1min', '5min')
        """
        self.min_rows = min_rows or self.DEFAULT_MIN_ROWS
        self.strict = strict
        self.expected_freq = expected_freq
    
    def validate(self, df: pd.DataFrame) -> bool:
        """
        Run all validation checks on the DataFrame.
        
        Args:
            df: DataFrame containing OHLCV data
            
        Returns:
            True if all validations pass
            
        Raises:
            DataValidationError: If any validation check fails
        """
        if df is None:
            raise DataValidationError("DataFrame is None")
        
        if df.empty:
            raise DataValidationError("DataFrame is empty")
        
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Core checks
        self._check_missing_values(df)
        self._check_negative_prices(df)
        self._check_minimum_rows(df)
        self._check_dtypes(df)
        
        # Time-series checks
        self._check_duplicate_index(df)
        self._check_time_gaps(df)
        
        # Market data checks
        self._check_ohlc_consistency(df)
        self._check_volume(df)
        
        # Strict checks (quant-grade)
        if self.strict:
            self._check_price_spikes(df)
        
        return True
    
    # =========================
    # Core Validations
    # =========================
    
    def _check_missing_values(self, df: pd.DataFrame) -> None:
        missing_count = df.isnull().sum().sum()
        
        if missing_count > 0:
            cols_with_missing = df.columns[df.isnull().any()].tolist()
            raise DataValidationError(
                f"Found {missing_count} missing value(s) in column(s): {cols_with_missing}"
            )
    
    def _check_negative_prices(self, df: pd.DataFrame) -> None:
        price_columns = ['open', 'high', 'low', 'close', 'price', 'vwap']
        
        matching_cols = [col for col in df.columns if col.lower() in price_columns]
        
        for col in matching_cols:
            negative_mask = df[col] < 0
            
            if negative_mask.any():
                indices = df[negative_mask].index[:5].tolist()
                raise DataValidationError(
                    f"Negative values in '{col}' at indices: {indices}"
                )
    
    def _check_minimum_rows(self, df: pd.DataFrame) -> None:
        if len(df) < self.min_rows:
            raise DataValidationError(
                f"Insufficient data: {len(df)} rows found, required: {self.min_rows}"
            )
    
    def _check_dtypes(self, df: pd.DataFrame) -> None:
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) == 0:
            raise DataValidationError("No numeric columns found in dataset")
    
    # =========================
    # Time-Series Validations
    # =========================
    
    def _check_duplicate_index(self, df: pd.DataFrame) -> None:
        if df.index.duplicated().any():
            raise DataValidationError("Duplicate timestamps found in index")
    
    def _check_time_gaps(self, df: pd.DataFrame) -> None:
        if not isinstance(df.index, pd.DatetimeIndex):
            return
        
        expected_range = pd.date_range(
            start=df.index.min(),
            end=df.index.max(),
            freq=self.expected_freq
        )
        
        missing = expected_range.difference(df.index)
        
        if len(missing) > 0:
            raise DataValidationError(
                f"Missing timestamps detected: {len(missing)} gaps"
            )
    
    # =========================
    # Market Data Validations
    # =========================
    
    def _check_ohlc_consistency(self, df: pd.DataFrame) -> None:
        required_cols = ['open', 'high', 'low', 'close']
        
        if not all(col in df.columns for col in required_cols):
            return
        
        invalid_rows = df[
            (df['high'] < df['low']) |
            (df['open'] > df['high']) |
            (df['open'] < df['low']) |
            (df['close'] > df['high']) |
            (df['close'] < df['low'])
        ]
        
        if not invalid_rows.empty:
            raise DataValidationError(
                f"Invalid OHLC relationships at indices: {invalid_rows.index[:5].tolist()}"
            )
    
    def _check_volume(self, df: pd.DataFrame) -> None:
        if 'volume' not in df.columns:
            return
        
        if (df['volume'] < 0).any():
            raise DataValidationError("Negative volume detected")
        
        zero_ratio = (df['volume'] == 0).sum() / len(df)
        
        if zero_ratio > 0.3:
            raise DataValidationError(
                f"Too many zero-volume candles: {zero_ratio:.2%}"
            )
    
    # =========================
    # Advanced (Quant-Level)
    # =========================
    
    def _check_price_spikes(self, df: pd.DataFrame, threshold: float = 0.3) -> None:
        if 'close' not in df.columns:
            return
        
        returns = df['close'].pct_change().abs()
        spikes = returns > threshold
        
        if spikes.sum() > 0:
            raise DataValidationError(
                f"Extreme price spikes detected: {int(spikes.sum())} occurrences"
            )