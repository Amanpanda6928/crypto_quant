"""Binance data fetcher with get_klines method."""

import pandas as pd
from typing import Optional
import time
import requests


class BinanceDataFetcher:
    """Data fetcher for Binance with get_klines method."""

    BASE_URL = "https://api.binance.com/api/v3/klines"

    def __init__(self, rate_limit_delay: float = 0.1):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    def _rate_limit(self):
        """Rate limiting to avoid API bans."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 200,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """Fetch OHLCV data for a single symbol."""
        self._rate_limit()

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000),
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"{symbol} API error: {e}")

        if not data:
            raise ValueError(f"No data returned for {symbol}")

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])

        df = df[["open_time", "open", "high", "low", "close", "volume"]]

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values("open_time")
        df = df.drop_duplicates(subset=["open_time"])
        df = df.dropna().reset_index(drop=True)

        return df