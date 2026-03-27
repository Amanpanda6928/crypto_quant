"""
Logging Utility Module
"""

import logging
import logging.handlers
from typing import Dict, Optional
from datetime import datetime, timedelta
import os
import json
from pathlib import Path


class TradingLogger:
    """
    Enhanced logging system for trading applications.

    Provides structured logging with different levels, file rotation,
    and trade-specific logging methods.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize trading logger.

        Args:
            config: Logging configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger('trading_system')
        self._setup_logger()

    def _get_default_config(self) -> Dict:
        """Get default logging configuration."""
        return {
            'log_level': 'INFO',
            'log_file': 'trades.log',
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'trade_format': '%(timestamp)s|%(symbol)s|%(side)s|%(quantity)s|%(price)s|%(pnl)s|%(reason)s',
            'enable_console': True,
            'enable_file': True,
            'log_directory': 'logs'
        }

    def _setup_logger(self):
        """Setup logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set log level
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(self.config['log_level'], logging.INFO))

        # Create formatters
        formatter = logging.Formatter(self.config['format'])

        # Console handler
        if self.config['enable_console']:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if self.config['enable_file']:
            log_dir = Path(self.config['log_directory'])
            log_dir.mkdir(exist_ok=True)

            log_file = log_dir / self.config['log_file']
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count']
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_trade(self, symbol: str, side: str, quantity: float, price: float,
                  pnl: Optional[float] = None, reason: str = "", **kwargs):
        """
        Log a trade with structured format.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            price: Trade price
            pnl: Profit/loss amount
            reason: Trade reason
            **kwargs: Additional trade data
        """
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'pnl': pnl if pnl is not None else 0.0,
            'reason': reason,
            **kwargs
        }

        # Format trade message
        message = self.config['trade_format'] % trade_data

        # Add extra data as JSON if present
        if kwargs:
            extra_data = {k: v for k, v in kwargs.items() if k not in ['timestamp', 'symbol', 'side', 'quantity', 'price', 'pnl', 'reason']}
            if extra_data:
                message += f" | {json.dumps(extra_data)}"

        self.logger.info(f"TRADE: {message}")

    def log_signal(self, symbol: str, signal_type: str, strength: float,
                   indicators: Optional[Dict] = None):
        """
        Log a trading signal.

        Args:
            symbol: Trading symbol
            signal_type: Type of signal (BUY, SELL, HOLD)
            strength: Signal strength (0-1)
            indicators: Technical indicators used
        """
        message = f"SIGNAL: {symbol} | {signal_type} | strength={strength:.3f}"

        if indicators:
            indicators_str = ", ".join([f"{k}={v:.4f}" for k, v in indicators.items()])
            message += f" | indicators: {indicators_str}"

        self.logger.info(message)

    def log_error(self, error_type: str, message: str, symbol: Optional[str] = None,
                  stack_trace: Optional[str] = None):
        """
        Log an error with context.

        Args:
            error_type: Type of error
            message: Error message
            symbol: Related symbol (if applicable)
            stack_trace: Stack trace (if available)
        """
        error_msg = f"ERROR [{error_type}]: {message}"

        if symbol:
            error_msg += f" | symbol: {symbol}"

        if stack_trace:
            error_msg += f"\nStack trace:\n{stack_trace}"

        self.logger.error(error_msg)

    def log_performance(self, metric_name: str, value: float, unit: str = "",
                       symbol: Optional[str] = None):
        """
        Log performance metrics.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            symbol: Related symbol (if applicable)
        """
        perf_msg = f"PERFORMANCE: {metric_name} = {value:.4f}"

        if unit:
            perf_msg += f" {unit}"

        if symbol:
            perf_msg += f" | symbol: {symbol}"

        self.logger.info(perf_msg)

    def log_system_event(self, event_type: str, message: str, severity: str = "INFO"):
        """
        Log system-level events.

        Args:
            event_type: Type of system event
            message: Event message
            severity: Log severity level
        """
        event_msg = f"SYSTEM [{event_type}]: {message}"

        severity = severity.upper()
        if severity == "DEBUG":
            self.logger.debug(event_msg)
        elif severity == "INFO":
            self.logger.info(event_msg)
        elif severity == "WARNING":
            self.logger.warning(event_msg)
        elif severity == "ERROR":
            self.logger.error(event_msg)
        elif severity == "CRITICAL":
            self.logger.critical(event_msg)

    def log_portfolio_update(self, total_value: float, cash: float,
                           positions: Dict[str, float], pnl: float):
        """
        Log portfolio status update.

        Args:
            total_value: Total portfolio value
            cash: Cash balance
            positions: Position sizes by symbol
            pnl: Unrealized P&L
        """
        positions_str = ", ".join([f"{symbol}: {size:.4f}" for symbol, size in positions.items()])

        portfolio_msg = (f"PORTFOLIO: total_value=${total_value:.2f}, "
                        f"cash=${cash:.2f}, pnl=${pnl:.2f}, "
                        f"positions=[{positions_str}]")

        self.logger.info(portfolio_msg)

    def get_recent_logs(self, lines: int = 100) -> list:
        """
        Get recent log entries.

        Args:
            lines: Number of recent lines to retrieve

        Returns:
            List of recent log lines
        """
        log_file = Path(self.config['log_directory']) / self.config['log_file']

        if not log_file.exists():
            return []

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception:
            return []

    def search_logs(self, keyword: str, hours: int = 24) -> list:
        """
        Search log files for specific keywords.

        Args:
            keyword: Keyword to search for
            hours: Hours of logs to search

        Returns:
            List of matching log lines
        """
        import time

        cutoff_time = time.time() - (hours * 3600)
        matching_lines = []

        # Search main log file
        log_file = Path(self.config['log_directory']) / self.config['log_file']
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if keyword.lower() in line.lower():
                            # Check if line is within time window (rough check)
                            try:
                                # Extract timestamp from log line
                                timestamp_str = line.split(' - ')[0]
                                log_time = datetime.fromisoformat(timestamp_str).timestamp()
                                if log_time > cutoff_time:
                                    matching_lines.append(line.strip())
                            except:
                                matching_lines.append(line.strip())
            except Exception:
                pass

        # Search rotated log files
        for i in range(1, self.config['backup_count'] + 1):
            backup_file = log_file.with_suffix(f".{i}")
            if backup_file.exists():
                try:
                    with open(backup_file, 'r') as f:
                        for line in f:
                            if keyword.lower() in line.lower():
                                matching_lines.append(line.strip())
                except Exception:
                    continue

        return matching_lines

    def export_logs(self, output_file: str, hours: int = 24):
        """
        Export recent logs to a file.

        Args:
            output_file: Output file path
            hours: Hours of logs to export
        """
        recent_logs = self.get_recent_logs(lines=1000)  # Get plenty of lines

        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_logs = []

        for line in recent_logs:
            try:
                timestamp_str = line.split(' - ')[0]
                log_time = datetime.fromisoformat(timestamp_str)
                if log_time > cutoff_time:
                    filtered_logs.append(line)
            except:
                filtered_logs.append(line)

        with open(output_file, 'w') as f:
            f.writelines(filtered_logs)

        self.logger.info(f"Exported {len(filtered_logs)} log lines to {output_file}")


# Global logger instance
_default_logger = None

def get_logger(config: Optional[Dict] = None) -> TradingLogger:
    """
    Get or create the global trading logger instance.

    Args:
        config: Logger configuration

    Returns:
        TradingLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = TradingLogger(config)
    return _default_logger


if __name__ == "__main__":
    # Example usage
    logger = TradingLogger()

    # Log various events
    logger.log_trade(
        symbol='BTCUSDT',
        side='buy',
        quantity=0.1,
        price=50000,
        pnl=None,
        reason='signal_based'
    )

    logger.log_signal(
        symbol='ETHUSDT',
        signal_type='BUY',
        strength=0.85,
        indicators={'rsi': 35.2, 'macd': 0.15}
    )

    logger.log_performance('sharpe_ratio', 1.25, symbol='BTCUSDT')

    logger.log_portfolio_update(
        total_value=125000,
        cash=25000,
        positions={'BTCUSDT': 0.5, 'ETHUSDT': 2.0},
        pnl=1250.50
    )

    # Search logs
    trade_logs = logger.search_logs('TRADE')
    print(f"Found {len(trade_logs)} trade log entries")