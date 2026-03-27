"""Utility methods for signal formatting and extras."""

from typing import Dict


def format_signal(symbol: str, signal_value: float) -> Dict[str, float]:
    """Format signal info from raw strategy score."""
    side = "BUY" if signal_value > 0 else "SELL"
    confidence = min(max(abs(signal_value), 0.0), 1.0)

    return {
        "symbol": symbol,
        "signal": side,
        "confidence": round(confidence, 4)
    }
