"""
Binance API Service - Real-time crypto prices
Free, no API key needed for public market data
"""
import requests
import time
from typing import Dict, Optional

# Binance API endpoints
BINANCE_BASE = "https://api.binance.com"

# 10 coins mapping to Binance symbols
COIN_SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
    "AVAX": "AVAXUSDT",
    "DOGE": "DOGEUSDT",
    "DOT": "DOTUSDT",
    "LINK": "LINKUSDT"
}

class BinanceService:
    """Real-time price service using Binance API"""
    
    def __init__(self):
        self.prices = {}
        self.last_update = None
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a coin"""
        binance_symbol = COIN_SYMBOLS.get(symbol)
        if not binance_symbol:
            return None
        
        try:
            url = f"{BINANCE_BASE}/api/v3/ticker/price"
            response = requests.get(url, params={"symbol": binance_symbol}, timeout=5)
            data = response.json()
            price = float(data.get("price", 0))
            self.prices[symbol] = price
            self.last_update = time.time()
            return price
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get prices for all 10 coins"""
        prices = {}
        for coin, binance_sym in COIN_SYMBOLS.items():
            price = self.get_price(coin)
            if price:
                prices[coin] = price
            time.sleep(0.1)  # Rate limit protection
        return prices
    
    def get_24h_stats(self, symbol: str) -> Optional[dict]:
        """Get 24h change stats"""
        binance_symbol = COIN_SYMBOLS.get(symbol)
        if not binance_symbol:
            return None
        
        try:
            url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
            response = requests.get(url, params={"symbol": binance_symbol}, timeout=5)
            data = response.json()
            return {
                "price": float(data.get("lastPrice", 0)),
                "change_24h": float(data.get("priceChangePercent", 0)),
                "high_24h": float(data.get("highPrice", 0)),
                "low_24h": float(data.get("lowPrice", 0)),
                "volume": float(data.get("volume", 0))
            }
        except Exception as e:
            print(f"Error fetching 24h stats for {symbol}: {e}")
            return None

# Singleton instance
_binance_service = None

def get_binance_service() -> BinanceService:
    global _binance_service
    if _binance_service is None:
        _binance_service = BinanceService()
    return _binance_service

if __name__ == "__main__":
    # Test
    service = get_binance_service()
    prices = service.get_all_prices()
    print("Real-time Binance prices:")
    for coin, price in prices.items():
        print(f"  {coin}: ${price:,.2f}")
