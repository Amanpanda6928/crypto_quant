"""
Data Acquisition Module - Fetches OHLCV data from Binance REST API
Includes built-in 30-coin portfolio support
"""

import requests
import pandas as pd
from typing import Optional, List, Dict
import time


class BinanceDataFetcher:
    """Professional-grade data fetcher for Binance cryptocurrency data."""

    BASE_URL = "https://api.binance.com/api/v3/klines"

    # ✅ Built-in 30 coins (high liquidity portfolio)
    DEFAULT_SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "DOGEUSDT", "TRXUSDT", "DOTUSDT", "MATICUSDT",
        "LTCUSDT", "BCHUSDT", "LINKUSDT", "ATOMUSDT", "ETCUSDT",
        "XLMUSDT", "FILUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT",
        "OPUSDT", "NEARUSDT", "ALGOUSDT", "VETUSDT", "SANDUSDT",
        "MANAUSDT", "AXSUSDT", "GALAUSDT", "FTMUSDT", "EGLDUSDT"
    ]

    def __init__(self, rate_limit_delay: float = 0.1):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    def _rate_limit(self):
        """Rate limiting to avoid API bans."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single symbol.

        Binance klines REST caps `limit` to 1000 per request; this method paginates
        (using `endTime`) to support larger limits for long horizons (e.g., 1d on 1m).
        """

        max_per_req = 1000
        remaining = int(limit)
        if remaining <= 0:
            raise ValueError("limit must be > 0")

        all_rows: list[list] = []
        page_end_time = end_time  # ms

        while remaining > 0:
            self._rate_limit()
            req_limit = min(remaining, max_per_req)

            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": req_limit,
            }

            # If caller explicitly provided start_time, respect it on the first page only.
            if start_time and not all_rows:
                params["startTime"] = start_time
            if page_end_time:
                params["endTime"] = page_end_time

            try:
                response = requests.get(self.BASE_URL, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"{symbol} API error: {e}")

            if not data:
                break

            all_rows.extend(data)
            remaining -= len(data)

            # Pagination: move endTime to just before earliest open_time returned.
            earliest_open_time_ms = int(data[0][0])
            page_end_time = earliest_open_time_ms - 1

            # If the API returns fewer rows than requested, we've hit history bounds.
            if len(data) < req_limit:
                break

            # If start_time was used, don't paginate backwards.
            if start_time:
                break

        if not all_rows:
            raise ValueError(f"No data returned for {symbol}")

        df = pd.DataFrame(all_rows, columns=[
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

        # Keep only the most recent `limit` rows (pagination can overshoot slightly).
        if len(df) > limit:
            df = df.iloc[-limit:].reset_index(drop=True)

        return df

    # =========================================
    # 🔥 MULTI-COIN CORE (MAIN FEATURE)
    # =========================================

    def fetch_all_coins(
        self,
        interval: str = "1m",
        limit: int = 500,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all 30 coins (or custom list).
        Returns: {symbol: DataFrame}
        """
        symbols = symbols or self.DEFAULT_SYMBOLS
        market_data = {}

        print(f"\nFetching data for {len(symbols)} coins...\n")

        for symbol in symbols:
            try:
                df = self.fetch_ohlcv(
                    symbol=symbol,
                    interval=interval,
                    limit=limit
                )
                market_data[symbol] = df
                print(f"[OK] {symbol} -> {len(df)} rows")
            except Exception as e:
                print(f"[ERR] {symbol} failed -> {e}")

        return market_data

    # =========================================
    # 🔥 COMBINED DATASET (VERY IMPORTANT)
    # =========================================

    def fetch_combined_dataset(
        self,
        interval: str = "1m",
        limit: int = 500,
        symbols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Returns ONE dataframe for all coins
        Format: [time, symbol, open, high, low, close, volume]
        """
        data = self.fetch_all_coins(interval=interval, limit=limit, symbols=symbols)

        combined = []

        for symbol, df in data.items():
            temp = df.copy()
            temp["symbol"] = symbol
            combined.append(temp)

        final_df = pd.concat(combined, ignore_index=True)
        final_df = final_df.sort_values(["open_time", "symbol"]).reset_index(drop=True)

        return final_df


# =========================================
# SIMPLE ACCESS FUNCTIONS
# =========================================

def fetch_current_data(symbol: str = "BTCUSDT", lookback: int = 500) -> pd.DataFrame:
    fetcher = BinanceDataFetcher()
    return fetcher.fetch_ohlcv(symbol=symbol, interval="1m", limit=lookback)


def fetch_all_market_data(limit: int = 500) -> Dict[str, pd.DataFrame]:
    """Get all 30 coins quickly"""
    fetcher = BinanceDataFetcher()
    return fetcher.fetch_all_coins(limit=limit)


def fetch_full_market_dataset(limit: int = 500) -> pd.DataFrame:
    """Get combined dataset for ML"""
    fetcher = BinanceDataFetcher()
    return fetcher.fetch_combined_dataset(limit=limit)