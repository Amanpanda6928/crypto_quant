"""
Correlation Risk Management Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sklearn.covariance import LedoitWolf
import warnings


class CorrelationManager:
    """
    Manages correlation risk across multiple assets.

    Provides correlation analysis, clustering, and risk-adjusted
    position sizing based on asset correlations.
    """

    def __init__(self, correlation_window: int = 252, min_periods: int = 30):
        """
        Initialize correlation manager.

        Args:
            correlation_window: Rolling window for correlation calculation
            min_periods: Minimum periods required for correlation
        """
        self.correlation_window = correlation_window
        self.min_periods = min_periods
        self.price_data = {}
        self.correlation_matrix = None
        self.last_update = None

    def update_price_data(self, symbol: str, prices: pd.Series):
        """
        Update price data for a symbol.

        Args:
            symbol: Trading symbol
            prices: Price series (typically close prices)
        """
        self.price_data[symbol] = prices.copy()
        self.last_update = pd.Timestamp.now()

    def update_multi_asset_data(self, price_dict: Dict[str, pd.Series]):
        """
        Update price data for multiple symbols.

        Args:
            price_dict: Dictionary of symbol -> price series
        """
        for symbol, prices in price_dict.items():
            self.update_price_data(symbol, prices)

    def calculate_correlation_matrix(self, method: str = 'pearson') -> pd.DataFrame:
        """
        Calculate correlation matrix for all symbols.

        Args:
            method: Correlation method ('pearson', 'spearman', 'kendall')

        Returns:
            Correlation matrix DataFrame
        """
        if len(self.price_data) < 2:
            raise ValueError("Need at least 2 symbols for correlation analysis")

        # Combine all price series
        price_df = pd.DataFrame(self.price_data)

        # Calculate returns
        returns_df = price_df.pct_change().dropna()

        if len(returns_df) < self.min_periods:
            raise ValueError(f"Insufficient data: need at least {self.min_periods} periods")

        # Calculate correlation matrix
        if method == 'pearson':
            corr_matrix = returns_df.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = returns_df.corr(method='spearman')
        elif method == 'kendall':
            corr_matrix = returns_df.corr(method='kendall')
        else:
            raise ValueError(f"Unknown correlation method: {method}")

        self.correlation_matrix = corr_matrix
        return corr_matrix

    def get_rolling_correlations(self, symbol1: str, symbol2: str) -> pd.Series:
        """
        Calculate rolling correlations between two symbols.

        Args:
            symbol1: First symbol
            symbol2: Second symbol

        Returns:
            Rolling correlation series
        """
        if symbol1 not in self.price_data or symbol2 not in self.price_data:
            raise ValueError(f"Price data not found for symbols: {symbol1}, {symbol2}")

        # Calculate returns
        returns1 = self.price_data[symbol1].pct_change()
        returns2 = self.price_data[symbol2].pct_change()

        # Calculate rolling correlation
        rolling_corr = returns1.rolling(window=self.correlation_window,
                                       min_periods=self.min_periods).corr(returns2)

        return rolling_corr.dropna()

    def find_highly_correlated_pairs(self, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """
        Find pairs of assets with high correlation.

        Args:
            threshold: Correlation threshold

        Returns:
            List of tuples (symbol1, symbol2, correlation)
        """
        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        pairs = []
        symbols = list(self.correlation_matrix.columns)

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                corr = self.correlation_matrix.iloc[i, j]
                if abs(corr) >= threshold:
                    pairs.append((symbols[i], symbols[j], corr))

        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)

    def calculate_portfolio_correlation(self, weights: Dict[str, float]) -> float:
        """
        Calculate portfolio correlation with market.

        Args:
            weights: Dictionary of symbol -> weight

        Returns:
            Portfolio correlation coefficient
        """
        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        # Filter correlation matrix to include only portfolio symbols
        portfolio_symbols = list(weights.keys())
        portfolio_corr = self.correlation_matrix.loc[portfolio_symbols, portfolio_symbols]

        # Calculate portfolio correlation as weighted average
        weights_array = np.array([weights[symbol] for symbol in portfolio_symbols])

        # Vectorized calculation of portfolio correlation
        portfolio_corr_value = np.sum(portfolio_corr.values * np.outer(weights_array, weights_array))

        return portfolio_corr_value

    def get_correlation_clusters(self, threshold: float = 0.6) -> List[List[str]]:
        """
        Group assets into correlation clusters.

        Args:
            threshold: Correlation threshold for clustering

        Returns:
            List of symbol clusters
        """
        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        symbols = list(self.correlation_matrix.columns)
        clusters = []

        # Simple clustering algorithm
        remaining = set(symbols)

        while remaining:
            # Start new cluster with first remaining symbol
            seed = remaining.pop()
            cluster = [seed]

            # Find all symbols correlated with seed
            correlated = []
            for symbol in remaining:
                corr = abs(self.correlation_matrix.loc[seed, symbol])
                if corr >= threshold:
                    correlated.append((symbol, corr))

            # Sort by correlation strength and add to cluster
            correlated.sort(key=lambda x: x[1], reverse=True)

            for symbol, _ in correlated:
                cluster.append(symbol)
                remaining.discard(symbol)

            clusters.append(cluster)

        return clusters

    def calculate_risk_adjusted_weights(self, base_weights: Dict[str, float],
                                       risk_aversion: float = 2.0) -> Dict[str, float]:
        """
        Adjust weights based on correlation risk.

        Args:
            base_weights: Base portfolio weights
            risk_aversion: Risk aversion parameter (higher = more conservative)

        Returns:
            Risk-adjusted weights
        """
        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        symbols = list(base_weights.keys())

        # Extract correlation submatrix
        corr_matrix = self.correlation_matrix.loc[symbols, symbols].values
        weights = np.array([base_weights[s] for s in symbols])

        # Calculate portfolio variance
        portfolio_variance = np.dot(weights.T, np.dot(corr_matrix, weights))

        # Risk parity approach: adjust weights inversely to correlation
        # Higher correlation -> lower weight
        avg_correlations = np.mean(corr_matrix, axis=1)

        # Risk-adjusted weights
        risk_weights = weights * (1 / (1 + risk_aversion * avg_correlations))

        # Normalize
        risk_weights = risk_weights / np.sum(risk_weights)

        return dict(zip(symbols, risk_weights))

    def get_correlation_report(self) -> Dict:
        """
        Generate comprehensive correlation report.

        Returns:
            Dictionary with correlation analysis results
        """
        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        # Basic statistics
        corr_values = self.correlation_matrix.values
        corr_values = corr_values[np.triu_indices_from(corr_values, k=1)]  # Upper triangle

        report = {
            'num_assets': len(self.correlation_matrix),
            'correlation_stats': {
                'mean': np.mean(corr_values),
                'std': np.std(corr_values),
                'min': np.min(corr_values),
                'max': np.max(corr_values),
                'median': np.median(corr_values)
            },
            'highly_correlated_pairs': self.find_highly_correlated_pairs(threshold=0.7),
            'correlation_clusters': self.get_correlation_clusters(threshold=0.6),
            'correlation_matrix': self.correlation_matrix.to_dict()
        }

        return report

    def detect_correlation_breakdown(self, window: int = 20) -> Dict[str, bool]:
        """
        Detect if correlations have broken down recently.

        Args:
            window: Lookback window for breakdown detection

        Returns:
            Dictionary of symbol pairs -> breakdown detected
        """
        breakdowns = {}

        if self.correlation_matrix is None:
            return breakdowns

        symbols = list(self.correlation_matrix.columns)

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]

                try:
                    rolling_corr = self.get_rolling_correlations(symbol1, symbol2)
                    recent_corr = rolling_corr.tail(window).mean()
                    historical_corr = rolling_corr.head(-window).tail(window).mean()

                    # Detect significant change
                    corr_change = abs(recent_corr - historical_corr)
                    breakdowns[f"{symbol1}_{symbol2}"] = corr_change > 0.3  # 30% change threshold

                except:
                    breakdowns[f"{symbol1}_{symbol2}"] = False

        return breakdowns


if __name__ == "__main__":
    # Example usage
    manager = CorrelationManager()

    # Generate sample price data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    # Create correlated price series
    base_returns = np.random.normal(0.001, 0.02, 100)
    btc_returns = base_returns + np.random.normal(0, 0.01, 100)
    eth_returns = base_returns * 0.8 + np.random.normal(0, 0.01, 100)  # Highly correlated
    ada_returns = np.random.normal(0.001, 0.03, 100)  # Less correlated

    btc_prices = 50000 * (1 + btc_returns).cumprod()
    eth_prices = 3000 * (1 + eth_returns).cumprod()
    ada_prices = 2 * (1 + ada_returns).cumprod()

    # Update data
    manager.update_price_data('BTCUSDT', pd.Series(btc_prices, index=dates))
    manager.update_price_data('ETHUSDT', pd.Series(eth_prices, index=dates))
    manager.update_price_data('ADAUSDT', pd.Series(ada_prices, index=dates))

    # Calculate correlations
    corr_matrix = manager.calculate_correlation_matrix()
    print("Correlation Matrix:")
    print(corr_matrix)

    # Find highly correlated pairs
    pairs = manager.find_highly_correlated_pairs(0.5)
    print(f"\nHighly correlated pairs: {pairs}")

    # Get correlation clusters
    clusters = manager.get_correlation_clusters(0.4)
    print(f"\nCorrelation clusters: {clusters}")

    # Risk-adjusted weights example
    base_weights = {'BTCUSDT': 0.5, 'ETHUSDT': 0.3, 'ADAUSDT': 0.2}
    adjusted_weights = manager.calculate_risk_adjusted_weights(base_weights)
    print(f"\nRisk-adjusted weights: {adjusted_weights}")