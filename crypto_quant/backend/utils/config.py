"""
Configuration Module for Crypto Trading System
"""

import os
from typing import Dict, List, Optional
from pathlib import Path


class Config:
    """
    Centralized configuration management for the trading system.

    Provides default configurations and environment variable overrides.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = self._get_default_config()

        # Load from environment variables
        self._load_from_env()

        # Load from file if provided
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)

    def _get_default_config(self) -> Dict:
        """Get default configuration values."""
        return {
            # Trading parameters
            'capital': 10000.0,
            'max_positions': 10,
            'position_size_pct': 0.20,
            'max_allocation_pct': 0.50,

            # Risk management
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.05,
            'max_drawdown_pct': 0.10,
            'daily_loss_limit_pct': 0.05,

            # Model parameters
            'model_horizons': [5, 10, 30],
            'prediction_threshold_buy': 0.65,
            'prediction_threshold_sell': 0.35,
            'combine_weights': [0.5, 0.3, 0.2],  # 5m, 10m, 30m weights

            # Data parameters
            'symbols': [
                "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                "ADAUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT",
                "TRXUSDT","AVAXUSDT","ATOMUSDT","LINKUSDT","ETCUSDT",
                "XLMUSDT","FILUSDT","APTUSDT","ARBUSDT","OPUSDT",
                "NEARUSDT","ALGOUSDT","VETUSDT","ICPUSDT","SANDUSDT",
                "MANAUSDT","THETAUSDT","EOSUSDT","AAVEUSDT","GALAUSDT"
            ],
            'data_limit': 300,
            'update_interval_minutes': 5,

            # Execution parameters
            'max_slippage_pct': 0.001,
            'fee_pct': 0.001,
            'min_order_size_usd': 10,
            'max_order_size_usd': 100000,
            'paper_trading': True,  # Set to False for real trading

            # Backtest parameters
            'backtest_initial_capital': 1000.0,
            'backtest_start_date': '2024-01-01',
            'backtest_end_date': '2024-12-31',

            # API parameters
            'api_base_url': 'https://api.binance.com',
            'api_timeout': 10,
            'api_rate_limit': 1200,  # requests per minute
            'api_key': os.getenv('BINANCE_API_KEY', ''),
            'api_secret': os.getenv('BINANCE_API_SECRET', ''),

            # File paths
            'data_dir': 'data',
            'models_dir': 'models',
            'logs_dir': 'logs',
            'cache_dir': 'cache',

            # Monitoring
            'health_check_interval': 60,
            'alert_email_enabled': False,
            'alert_webhook_enabled': False,

            # Feature engineering
            'feature_lookback': 50,
            'technical_indicators': [
                'sma_20', 'sma_50', 'ema_12', 'ema_26',
                'rsi', 'macd', 'bb_upper', 'bb_lower',
                'volume_sma', 'price_change'
            ],

            # Logging
            'log_level': 'INFO',
            'log_to_file': True,
            'log_to_console': True,

            # Performance tracking
            'track_performance': True,
            'performance_metrics': [
                'sharpe_ratio', 'max_drawdown', 'win_rate',
                'profit_factor', 'calmar_ratio'
            ]
        }

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'CRYPTO_CAPITAL': ('capital', float),
            'CRYPTO_MAX_POSITIONS': ('max_positions', int),
            'CRYPTO_API_KEY': ('api_key', str),
            'CRYPTO_API_SECRET': ('api_secret', str),
            'CRYPTO_LOG_LEVEL': ('log_level', str),
            'CRYPTO_EMAIL_ENABLED': ('alert_email_enabled', self._str_to_bool),
            'CRYPTO_WEBHOOK_ENABLED': ('alert_webhook_enabled', self._str_to_bool),
        }

        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    self.config[config_key] = converter(value)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid value for {env_var}: {value}")

    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ('true', '1', 'yes', 'on')

    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            import json
            with open(config_file, 'r') as f:
                file_config = json.load(f)

            # Deep merge with default config
            self._deep_merge(self.config, file_config)

        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")

    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default=None):
        """
        Get configuration value.

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value):
        """
        Set configuration value.

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def save_to_file(self, config_file: str):
        """
        Save current configuration to file.

        Args:
            config_file: Path to save configuration
        """
        try:
            import json
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config to {config_file}: {e}")

    def get_symbols(self) -> List[str]:
        """Get list of trading symbols."""
        return self.config['symbols']

    def get_risk_params(self) -> Dict:
        """Get risk management parameters."""
        return {
            'stop_loss_pct': self.config['stop_loss_pct'],
            'take_profit_pct': self.config['take_profit_pct'],
            'max_drawdown_pct': self.config['max_drawdown_pct'],
            'daily_loss_limit_pct': self.config['daily_loss_limit_pct'],
            'max_positions': self.config['max_positions'],
        }

    def get_model_params(self) -> Dict:
        """Get model parameters."""
        return {
            'horizons': self.config['model_horizons'],
            'threshold_buy': self.config['prediction_threshold_buy'],
            'threshold_sell': self.config['prediction_threshold_sell'],
            'combine_weights': self.config['combine_weights'],
        }

    def get_execution_params(self) -> Dict:
        """Get execution parameters."""
        return {
            'max_slippage_pct': self.config['max_slippage_pct'],
            'fee_pct': self.config['fee_pct'],
            'min_order_size_usd': self.config['min_order_size_usd'],
            'max_order_size_usd': self.config['max_order_size_usd'],
        }

    def get_api_params(self) -> Dict:
        """Get API parameters."""
        return {
            'base_url': self.config['api_base_url'],
            'timeout': self.config['api_timeout'],
            'rate_limit': self.config['api_rate_limit'],
        }

    def validate_config(self) -> List[str]:
        """
        Validate configuration values.

        Returns:
            List of validation errors
        """
        errors = []

        # Validate capital
        if self.config['capital'] <= 0:
            errors.append("Capital must be positive")

        # Validate percentages
        pct_fields = ['position_size_pct', 'max_allocation_pct', 'stop_loss_pct',
                     'take_profit_pct', 'max_drawdown_pct', 'daily_loss_limit_pct',
                     'max_slippage_pct', 'fee_pct']

        for field in pct_fields:
            value = self.config.get(field, 0)
            if not 0 <= value <= 1:
                errors.append(f"{field} must be between 0 and 1")

        # Validate position limits
        if self.config['max_positions'] <= 0:
            errors.append("max_positions must be positive")

        # Validate symbols
        if not self.config['symbols']:
            errors.append("At least one symbol must be configured")

        # Validate horizons and weights
        horizons = self.config['model_horizons']
        weights = self.config['combine_weights']

        if len(weights) != len(horizons):
            errors.append("combine_weights length must match model_horizons length")

        if abs(sum(weights) - 1.0) > 0.001:
            errors.append("combine_weights must sum to 1.0")

        return errors

    def print_config(self):
        """Print current configuration."""
        print("=== Trading System Configuration ===")
        print(f"Capital: ${self.config['capital']:,.2f}")
        print(f"Symbols: {', '.join(self.config['symbols'])}")
        print(f"Max Positions: {self.config['max_positions']}")
        print(f"Position Size: {self.config['position_size_pct']:.1%}")
        print(f"Stop Loss: {self.config['stop_loss_pct']:.1%}")
        print(f"Take Profit: {self.config['take_profit_pct']:.1%}")
        print(f"Max Drawdown: {self.config['max_drawdown_pct']:.1%}")
        print(f"Model Horizons: {self.config['model_horizons']}")
        print(f"Log Level: {self.config['log_level']}")
        print("=" * 40)


# Global configuration instance
_default_config = None

def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance.

    Args:
        config_file: Path to configuration file

    Returns:
        Config instance
    """
    global _default_config
    if _default_config is None:
        _default_config = Config(config_file)
    return _default_config


if __name__ == "__main__":
    # Example usage
    config = Config()

    # Print configuration
    config.print_config()

    # Validate configuration
    errors = config.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")

    # Example of getting specific values
    print(f"Capital: ${config.get('capital')}")
    print(f"Symbols: {config.get_symbols()}")
    print(f"Risk params: {config.get_risk_params()}")