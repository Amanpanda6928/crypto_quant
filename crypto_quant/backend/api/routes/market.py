from fastapi import APIRouter, HTTPException, Path
from ...data.binance_fetcher import BinanceDataFetcher
import asyncio
from datetime import datetime, timedelta

router = APIRouter(prefix="/market", tags=["market"])

# Singleton fetcher
_fetcher: BinanceDataFetcher | None = None

# Cache
_cache = {}
CACHE_TTL = 30  # seconds


def get_fetcher() -> BinanceDataFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = BinanceDataFetcher()
    return _fetcher


def is_valid_symbol(symbol: str) -> bool:
    # Basic validation (you can expand this)
    return symbol.endswith("USDT") and len(symbol) >= 6


@router.get("/candles/{symbol}")
async def get_candles(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTCUSDT)")
):
    """
    Get last 200 OHLCV candles (cached + validated + non-blocking)
    """

    symbol = symbol.upper()

    # ✅ Validate symbol
    if not is_valid_symbol(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")

    try:
        now = datetime.utcnow()

        # ✅ Cache key
        cache_key = f"{symbol}_1h"

        # ✅ Serve cached data if fresh
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            if (now - timestamp) < timedelta(seconds=CACHE_TTL):
                return {
                    "status": "cached",
                    "symbol": symbol,
                    "interval": "1h",
                    "data": cached_data
                }

        # ⚡ Non-blocking fetch
        fetcher = get_fetcher()
        df = await asyncio.to_thread(
            fetcher.get_klines,
            symbol=symbol,
            interval="1h",
            limit=200
        )

        data = df.to_dict(orient="records")

        # Save cache
        _cache[cache_key] = (data, now)

        return {
            "status": "fresh",
            "symbol": symbol,
            "interval": "1h",
            "data": data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Market data fetch failed: {str(e)}"
        )
