"""
CoinGecko API Service - Real-time crypto prices
Free tier: 10-50 calls/min, no API key needed
"""
import requests
import time
from typing import Dict, Optional

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Coin mapping to CoinGecko IDs
COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink"
}

class CoinGeckoService:
    """Real-time price service using CoinGecko API"""
    
    def __init__(self):
        self.prices = {}
        self.last_update = None
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a coin"""
        coin_id = COIN_IDS.get(symbol)
        if not coin_id:
            return None
        
        try:
            url = f"{COINGECKO_BASE}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            price = data.get(coin_id, {}).get("usd", 0)
            if price:
                self.prices[symbol] = float(price)
                self.last_update = time.time()
                return float(price)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get prices for all 10 coins in one call"""
        try:
            ids = ",".join(COIN_IDS.values())
            url = f"{COINGECKO_BASE}/simple/price"
            params = {
                "ids": ids,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            prices = {}
            for symbol, coin_id in COIN_IDS.items():
                price = data.get(coin_id, {}).get("usd", 0)
                if price:
                    prices[symbol] = float(price)
            
            self.prices = prices
            self.last_update = time.time()
            return prices
        except Exception as e:
            print(f"Error fetching all prices: {e}")
            return {}

# Singleton instance
_coingecko_service = None

def get_coingecko_service() -> CoinGeckoService:
    global _coingecko_service
    if _coingecko_service is None:
        _coingecko_service = CoinGeckoService()
    return _coingecko_service

if __name__ == "__main__":
    service = get_coingecko_service()
    prices = service.get_all_prices()
    print("Real-time CoinGecko prices:")
    for coin, price in prices.items():
        print(f"  {coin}: ${price:,.2f}")
